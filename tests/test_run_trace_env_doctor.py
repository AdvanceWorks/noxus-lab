"""Offline tests for run/trace/env/doctor.

Network and SDK calls are stubbed via monkeypatch.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from noxuslab import envs, trace_view
from noxuslab._trace import TraceWriter, find_trace, list_traces, read_trace, trace_path
from noxuslab.errors import BadFile
from noxuslab.runner import _parse_input

# --- _trace ------------------------------------------------------------------


def test_trace_writer_jsonl_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = trace_path("abc-123")
    with TraceWriter(p) as tw:
        tw.write("header", workflow_id="wf-1", input={"q": "hi"})
        tw.write("event", type="node_start", data={"node_id": "n1"})
        tw.write("footer", status="completed", elapsed_ms=42)
    entries = read_trace(p)
    assert [e["kind"] for e in entries] == ["header", "event", "footer"]
    assert entries[0]["workflow_id"] == "wf-1"
    assert entries[2]["elapsed_ms"] == 42


def test_trace_writer_redacts_secrets(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = trace_path("r1")
    with TraceWriter(p) as tw:
        tw.write("header", input={"api_key": "leak", "TOKEN": "x", "ok": "fine"})
    entry = read_trace(p)[0]
    assert entry["input"]["api_key"] == "***"
    assert entry["input"]["TOKEN"] == "***"
    assert entry["input"]["ok"] == "fine"


def test_list_and_find_traces(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p1 = trace_path("aaa")
    p1.write_text("{}\n", encoding="utf-8")
    p2 = trace_path("bbb")
    p2.write_text("{}\n", encoding="utf-8")
    files = list_traces()
    assert len(files) == 2
    assert find_trace("aaa") is not None
    assert find_trace("zzz") is None


# --- runner._parse_input -----------------------------------------------------


def test_parse_input_json_and_string():
    out = _parse_input(["n=42", "name=alice", "list=[1,2,3]", "flag=true"])
    assert out == {"n": 42, "name": "alice", "list": [1, 2, 3], "flag": True}


def test_parse_input_at_file(tmp_path: Path):
    f = tmp_path / "blob.json"
    f.write_text('{"x":1}', encoding="utf-8")
    out = _parse_input([f"data=@{f}"])
    assert out == {"data": {"x": 1}}


def test_parse_input_rejects_no_eq():
    with pytest.raises(BadFile, match="key=value"):
        _parse_input(["nope"])


# --- envs --------------------------------------------------------------------


def test_envs_list_and_use(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    Path(".env.dev").write_text("NOXUS_API_KEY=devkey\n", encoding="utf-8")
    Path(".env.prod").write_text("NOXUS_API_KEY=prodkey\n", encoding="utf-8")

    rc = envs.cmd_list()
    assert rc == 0
    out = capsys.readouterr().out
    assert "dev" in out and "prod" in out
    assert envs.current() is None  # nothing chosen yet

    rc = envs.cmd_use("dev")
    assert rc == 0
    assert envs.current() == "dev"
    assert Path(".env").read_text(encoding="utf-8").strip() == "NOXUS_API_KEY=devkey"

    rc = envs.cmd_use("prod")
    assert rc == 0
    assert envs.current() == "prod"
    assert "prodkey" in Path(".env").read_text(encoding="utf-8")


def test_envs_use_unknown_raises(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(BadFile, match="no such env file"):
        envs.cmd_use("ghost")


def test_envs_list_when_empty(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    rc = envs.cmd_list()
    assert rc == 0
    assert "no .env" in capsys.readouterr().out


# --- doctor ------------------------------------------------------------------


def test_doctor_passes_with_env_key(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOXUS_API_KEY", "test-key-12345678")
    monkeypatch.delenv("NOXUSLAB_SECRETS_CMD", raising=False)
    # Force backend reachability check on a guaranteed-closed port to
    # exercise the warn path without depending on the real backend.
    monkeypatch.setenv("NOXUS_BACKEND_URL", "http://127.0.0.1:1")

    from noxuslab.doctor import doctor

    rc = doctor()
    out = capsys.readouterr().out
    assert "noxuslab" in out
    assert "NOXUS_API_KEY resolved" in out
    # Backend warn should not fail the run.
    assert rc == 0


def test_doctor_fails_without_key(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("NOXUS_API_KEY", raising=False)
    monkeypatch.delenv("NOXUSLAB_SECRETS_CMD", raising=False)
    # `load_dotenv()` walks up from cwd; stub it in both modules that call
    # it so the test does not pick up the developer's real .env at the
    # repo root.
    monkeypatch.setattr("noxuslab.doctor.load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr("noxuslab._secrets.load_dotenv", lambda *a, **k: False)

    from noxuslab.doctor import doctor

    rc = doctor()
    out = capsys.readouterr().out
    assert "NOXUS_API_KEY" in out
    assert rc == 1


# --- trace_view --------------------------------------------------------------


def test_trace_view_list_empty(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    rc = trace_view.cmd_list()
    assert rc == 0
    assert "no traces yet" in capsys.readouterr().out


def test_trace_view_show_renders(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    p = trace_path("xyz")
    with TraceWriter(p) as tw:
        tw.write("header", workflow_id="wf-9", workflow_name="my flow", input={"q": "hi"})
        tw.write("event", type="node_start", data={"node_id": "n1", "status": "running"})
        tw.write("footer", status="completed", elapsed_ms=12, output={"answer": "ok"})

    rc = trace_view.cmd_show("xyz")
    assert rc == 0
    out = capsys.readouterr().out
    assert "my flow" in out
    assert "node_start" in out
    assert "completed" in out


def test_trace_view_show_json(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    p = trace_path("jjj")
    with TraceWriter(p) as tw:
        tw.write("header", input={})
        tw.write("footer", status="failed", elapsed_ms=1)

    rc = trace_view.cmd_show("jjj", json_out=True)
    assert rc == 0
    parsed = json.loads(capsys.readouterr().out)
    assert isinstance(parsed, list)
    assert parsed[-1]["status"] == "failed"


def test_trace_view_show_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(BadFile, match="no trace matches"):
        trace_view.cmd_show("nope")


def test_trace_view_list_with_entries(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    p = trace_path("done")
    with TraceWriter(p) as tw:
        tw.write("header", workflow_name="wf-A", input={})
        tw.write("footer", status="completed", elapsed_ms=99)
    p2 = trace_path("fail")
    with TraceWriter(p2) as tw:
        tw.write("header", workflow_name="wf-B", input={})
        tw.write("footer", status="failed", elapsed_ms=10)

    rc = trace_view.cmd_list()
    out = capsys.readouterr().out
    assert rc == 0
    assert "wf-A" in out and "wf-B" in out
    assert "completed" in out and "failed" in out


# --- runner: _load_or_push (offline branches) --------------------------------


def test_load_or_push_rejects_unknown_target(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from noxuslab.runner import _load_or_push

    with pytest.raises(BadFile, match="not a UUID and not a file"):
        _load_or_push(client=object(), target="ghost.py")


def test_load_or_push_uuid_calls_workflows_get(monkeypatch):
    """UUID path should hit `client.workflows.get`."""
    captured = {}

    class _WF:
        def get(self, workflow_id):
            captured["id"] = workflow_id
            return "wf-stub"

    class _Client:
        workflows = _WF()

    from noxuslab.runner import _load_or_push

    out = _load_or_push(_Client(), "11111111-1111-1111-1111-111111111111")
    assert out == "wf-stub"
    assert captured["id"] == "11111111-1111-1111-1111-111111111111"


def test_run_cli_handler_dispatches(monkeypatch):
    """`cmd_run` must call `runner.run` with parsed args (no real network)."""
    import argparse

    from noxuslab import cli

    captured = {}

    def fake_run(target, inputs, *, follow):
        captured["target"] = target
        captured["inputs"] = inputs
        captured["follow"] = follow
        return 0

    monkeypatch.setattr("noxuslab.runner.run", fake_run)
    monkeypatch.setattr(cli, "load_dotenv", lambda *a, **k: None)

    args = argparse.Namespace(target="wf-id", input=["k=1"], detach=False)
    rc = cli.cmd_run(args)
    assert rc == 0
    assert captured == {"target": "wf-id", "inputs": ["k=1"], "follow": True}
