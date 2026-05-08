"""Tests for `noxuslab._audit` (offline)."""

import json
from pathlib import Path

from noxuslab._audit import _argv_summary, emit


def test_argv_summary_empty():
    assert _argv_summary([]) == {}


def test_argv_summary_normal_cmd():
    s = _argv_summary(["pull", "abc-def"])
    assert s == {"cmd": "pull", "argv": ["abc-def"]}


def test_argv_summary_redacts_chat():
    s = _argv_summary(["chat", "--agent", "secret-id"])
    assert s["cmd"] == "chat"
    assert "argv" not in s
    assert s["redacted_positional"] == 2


def test_argv_summary_redacts_ask():
    s = _argv_summary(["ask", "what is the meaning of life"])
    assert s["cmd"] == "ask"
    assert "argv" not in s
    assert s["redacted_positional"] >= 1


def test_emit_silent_when_unset(monkeypatch, tmp_path):
    monkeypatch.delenv("NOXUSLAB_AUDIT_LOG", raising=False)
    monkeypatch.delenv("NOXUSLAB_AUDIT", raising=False)
    emit(["pull", "x"], 0, 1)  # must not raise


def test_emit_appends_jsonl_to_file(monkeypatch, tmp_path: Path):
    log = tmp_path / "audit.log"
    monkeypatch.setenv("NOXUSLAB_AUDIT_LOG", str(log))
    emit(["pull", "abc-def"], 0, 42)
    emit(["push", "x.py"], 1, 99)
    lines = log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    rec0 = json.loads(lines[0])
    assert rec0["cmd"] == "pull"
    assert rec0["rc"] == 0
    assert rec0["duration_ms"] == 42
    assert "user" in rec0
    assert "host" in rec0
    assert "version" in rec0
    rec1 = json.loads(lines[1])
    assert rec1["cmd"] == "push"
    assert rec1["rc"] == 1


def test_emit_to_stderr(monkeypatch, capsys):
    monkeypatch.delenv("NOXUSLAB_AUDIT_LOG", raising=False)
    monkeypatch.setenv("NOXUSLAB_AUDIT", "stderr")
    emit(["list"], 0, 5)
    err = capsys.readouterr().err
    assert '"cmd":"list"' in err
    assert '"rc":0' in err


def test_time_ms_is_monotonic_positive():
    from noxuslab._audit import time_ms

    a = time_ms()
    b = time_ms()
    assert a > 0
    assert b >= a
