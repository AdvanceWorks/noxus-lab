"""Tests for `noxuslab._net` (offline)."""

from unittest.mock import MagicMock

import pytest

from noxuslab._net import NetworkError, RateLimited, _delay, _is_retryable, call


def test_call_returns_value_on_success():
    assert call(lambda: 42, what="x") == 42


def test_call_raises_clean_on_terminal_error():
    def boom():
        raise ValueError("nope")

    with pytest.raises(NetworkError) as e:
        call(boom, what="probe")
    assert "probe" in str(e.value)


def test_call_retries_on_timeout(monkeypatch):
    monkeypatch.setattr("noxuslab._net.MAX_RETRIES", 2)
    monkeypatch.setattr("noxuslab._net.time.sleep", lambda _: None)
    monkeypatch.setattr("noxuslab._net._is_retryable", lambda _: True)
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("transient")
        return "ok"

    assert call(flaky, what="probe") == "ok"
    assert calls["n"] == 2


def test_call_429_raises_rate_limited(monkeypatch):
    monkeypatch.setattr("noxuslab._net.MAX_RETRIES", 0)
    resp = MagicMock(status_code=429)
    err = Exception("rate")
    err.response = resp  # type: ignore[attr-defined]

    def boom():
        raise err

    with pytest.raises(RateLimited):
        call(boom, what="x")


def test_is_retryable_status_codes():
    err = Exception("x")
    err.response = MagicMock(status_code=503)  # type: ignore[attr-defined]
    assert _is_retryable(err)
    err.response = MagicMock(status_code=400)  # type: ignore[attr-defined]
    assert not _is_retryable(err)


def test_delay_within_bounds():
    for attempt in range(5):
        d = _delay(attempt)
        assert d > 0
        assert d <= 16  # MAX_DELAY * 2 (jitter ceiling)
