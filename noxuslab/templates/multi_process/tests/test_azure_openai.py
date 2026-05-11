"""Offline tests for `shared/azure_openai.py`."""

import math

import pytest

from shared.azure_openai import TokenScore, _match_label, _required, build_client


def test_token_score_probability_round_trips() -> None:
    s = TokenScore(token="billing", logprob=math.log(0.9))
    assert pytest.approx(s.probability, rel=1e-6) == 0.9


def test_match_label_exact_case_insensitive() -> None:
    assert _match_label("Billing", ["billing", "sales"]) == "billing"


def test_match_label_strips_punctuation() -> None:
    assert _match_label('"billing".', ["billing"]) == "billing"


def test_match_label_falls_back_to_raw_when_unknown() -> None:
    assert _match_label("zzz", ["billing"]) == "zzz"


def test_required_raises_with_helpful_message(monkeypatch) -> None:
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="AZURE_OPENAI_API_KEY"):
        _required("AZURE_OPENAI_API_KEY")


def test_build_client_requires_endpoint(monkeypatch) -> None:
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "x")
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    with pytest.raises(RuntimeError, match="AZURE_OPENAI_ENDPOINT"):
        build_client()
