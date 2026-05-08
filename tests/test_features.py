"""Offline tests for v0.5+ features (gen, watch, graph, audit sinks, init wizard)."""

from __future__ import annotations

import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from noxuslab._audit import _is_url, emit
from noxuslab.gen import _slug, _strip_fences
from noxuslab.graph import to_mermaid

# --- gen ---------------------------------------------------------------------


def test_strip_fences_plain():
    assert _strip_fences("import x\nwf = 1\n") == "import x\nwf = 1"


def test_strip_fences_python_block():
    text = "```python\nimport x\nwf = 1\n```"
    assert _strip_fences(text) == "import x\nwf = 1"


def test_strip_fences_no_lang():
    assert _strip_fences("```\nfoo\n```") == "foo"


def test_slug_normalises():
    assert _slug("Hello, World!  Build a Bot") == "hello_world_build_a_bot"


def test_slug_empty_falls_back():
    assert _slug("!!!") == "generated"


def test_generate_rejects_empty_prompt():
    from noxuslab.errors import NoxusLabError
    from noxuslab.gen import generate

    with pytest.raises(NoxusLabError, match="empty prompt"):
        generate("   ", agent_id=None, model=None, out=None)


def test_generate_rejects_reply_without_wf(tmp_path, monkeypatch):
    from noxuslab.errors import NoxusLabError
    from noxuslab.gen import generate

    monkeypatch.chdir(tmp_path)
    fake_conv = MagicMock()
    fake_conv.chat.return_value = SimpleNamespace(content="print('no workflow here')")
    fake_client = MagicMock()
    fake_client.conversations.create.return_value = fake_conv
    with (
        patch("noxuslab.chat._make_client", return_value=fake_client),
        pytest.raises(NoxusLabError, match="`wf`"),
    ):
        generate("make a thing", agent_id=None, model=None, out=None)


def test_generate_writes_file(tmp_path, monkeypatch, capsys):
    from noxuslab.gen import generate

    monkeypatch.chdir(tmp_path)
    code = "from noxus_sdk import x\nwf = x.WorkflowDefinition()\nprint(c.workflows.save(wf).id)"
    fake_conv = MagicMock()
    fake_conv.chat.return_value = SimpleNamespace(content=code)
    fake_client = MagicMock()
    fake_client.conversations.create.return_value = fake_conv
    out = tmp_path / "out.py"
    with patch("noxuslab.chat._make_client", return_value=fake_client):
        rc = generate("make a thing", agent_id=None, model=None, out=str(out))
    assert rc == 0
    assert out.read_text(encoding="utf-8").startswith("from noxus_sdk")


# --- graph (mermaid) ---------------------------------------------------------


def test_to_mermaid_minimal():
    wf = SimpleNamespace(nodes=[], edges=[])
    out = to_mermaid(wf)
    assert out.startswith("```mermaid\nflowchart TD")
    assert out.endswith("```\n")


def test_to_mermaid_nodes_and_edges():
    n1 = SimpleNamespace(id="a", name="Input")
    n2 = SimpleNamespace(id="b", name="LLM Call")
    e = SimpleNamespace(from_node="a", to_node="b")
    wf = SimpleNamespace(nodes=[n1, n2], edges=[e])
    out = to_mermaid(wf, title="server:test")
    assert "%% server:test" in out
    assert '"Input"' in out
    assert '"LLM Call"' in out
    assert "-->" in out


def test_to_mermaid_handles_missing_attrs():
    n = SimpleNamespace()
    wf = SimpleNamespace(nodes=[n], edges=[])
    out = to_mermaid(wf)
    assert "n0" in out  # falls back to index


# --- audit sinks -------------------------------------------------------------


def test_is_url_true():
    assert _is_url("https://hooks.slack.com/services/x")
    assert _is_url("http://localhost:8080/x")


def test_is_url_false():
    assert not _is_url("/var/log/audit.log")
    assert not _is_url("audit.log")


def test_emit_to_https_calls_urlopen(monkeypatch):
    monkeypatch.setenv("NOXUSLAB_AUDIT_LOG", "https://example.com/ingest")
    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["data"] = req.data
        return io.BytesIO(b"")

    with patch("noxuslab._audit.urllib.request.urlopen", side_effect=fake_urlopen):
        emit(["pull", "abc"], 0, 5)
    assert captured["url"] == "https://example.com/ingest"
    import json

    body = json.loads(captured["data"])
    assert body["cmd"] == "pull"
    assert body["rc"] == 0


def test_emit_to_slack_wraps_in_text_field(monkeypatch):
    monkeypatch.setenv("NOXUSLAB_AUDIT_LOG", "https://hooks.slack.com/services/x/y/z")
    captured = {}

    def fake_urlopen(req, timeout):
        captured["data"] = req.data
        return io.BytesIO(b"")

    with patch("noxuslab._audit.urllib.request.urlopen", side_effect=fake_urlopen):
        emit(["push", "f.py"], 1, 100)
    import json

    body = json.loads(captured["data"])
    assert "text" in body  # Slack format


def test_emit_https_failure_is_silent(monkeypatch):
    monkeypatch.setenv("NOXUSLAB_AUDIT_LOG", "https://example.com/ingest")
    import urllib.error

    with patch(
        "noxuslab._audit.urllib.request.urlopen",
        side_effect=urllib.error.URLError("boom"),
    ):
        emit(["pull", "abc"], 0, 5)  # must not raise


def test_emit_redacts_gen_prompt(monkeypatch, tmp_path: Path):
    log = tmp_path / "audit.log"
    monkeypatch.setenv("NOXUSLAB_AUDIT_LOG", str(log))
    emit(["gen", "summarise PDFs and email weekly"], 0, 1)
    line = log.read_text(encoding="utf-8")
    assert "summarise" not in line
    assert "redacted_positional" in line


# --- watch -------------------------------------------------------------------


def test_watch_rejects_missing_file(tmp_path):
    from noxuslab.errors import BadFile
    from noxuslab.watch import watch

    with pytest.raises(BadFile, match="not found"):
        watch(str(tmp_path / "nope.py"))
