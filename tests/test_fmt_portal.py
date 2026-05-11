"""Offline tests for `noxuslab fmt` and `noxuslab portal`."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from noxuslab.errors import BadFile
from noxuslab.fmt import fmt, fmt_one
from noxuslab.portal import _make_handler, _overview, _shell, _table, serve

# A minimal but valid workflow file. Mirrors what `noxuslab pull` emits.
_WF_FILE = '''\
#!/usr/bin/env python3
"""recreate test workflow."""

import os

from dotenv import load_dotenv
from noxus_sdk.client import Client
from noxus_sdk.workflows import WorkflowDefinition

load_dotenv()
c = Client(api_key=os.environ.get("NOXUS_API_KEY", "x"), base_url=None)

wf = WorkflowDefinition(name="test")

print(c.workflows.save(wf).id)
'''


# --- fmt ---------------------------------------------------------------------


def test_fmt_rejects_missing_file(tmp_path):
    with pytest.raises(BadFile, match="not found"):
        fmt_one(tmp_path / "nope.py", check=False, show_diff=False)


def test_fmt_rejects_no_paths():
    with pytest.raises(BadFile, match="no files"):
        fmt([])


def test_fmt_rejects_file_without_wf(tmp_path: Path):
    f = tmp_path / "no_wf.py"
    f.write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(BadFile, match="`wf`"):
        fmt_one(f, check=False, show_diff=False)


def test_fmt_idempotent_on_canonical(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setenv("NOXUS_API_KEY", "test")
    f = tmp_path / "wf.py"
    f.write_text(_WF_FILE, encoding="utf-8")
    # First pass writes canonical form (likely changes whitespace).
    fmt_one(f, check=False, show_diff=False)
    # Second pass must be a no-op.
    rc = fmt_one(f, check=False, show_diff=False)
    assert rc == 0


def test_fmt_check_returns_1_when_changes_pending(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setenv("NOXUS_API_KEY", "test")
    f = tmp_path / "wf.py"
    # Inject extra blank lines that the canonical form will collapse.
    f.write_text(
        _WF_FILE.replace("wf = WorkflowDefinition", "\n\nwf = WorkflowDefinition"), encoding="utf-8"
    )
    rc = fmt_one(f, check=True, show_diff=False)
    out = capsys.readouterr().out
    assert rc == 1
    assert "would reformat" in out


def test_fmt_diff_does_not_write(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setenv("NOXUS_API_KEY", "test")
    f = tmp_path / "wf.py"
    original = _WF_FILE + "\n# trailing junk\n"
    f.write_text(original, encoding="utf-8")
    rc = fmt_one(f, check=False, show_diff=True)
    out = capsys.readouterr().out
    assert rc == 1
    assert "---" in out and "+++" in out
    assert f.read_text(encoding="utf-8") == original  # untouched


# --- portal ------------------------------------------------------------------


def test_serve_rejects_non_loopback():
    with pytest.raises(ValueError, match="loopback"):
        serve(host="0.0.0.0", port=7890)  # noqa: S104 — testing the rejection


def test_shell_wraps_body():
    out = _shell("ttl", "<p>hi</p>").decode("utf-8")
    assert "<title>ttl" in out
    assert "<p>hi</p>" in out
    assert "<nav>" in out
    assert "127.0.0.1" in out  # footer hint


def test_table_empty_kind():
    assert "no widgets" in _table([], "widgets")


def test_table_renders_rows_and_escapes():
    rows = [("abc", "<script>")]
    out = _table(rows, "workflows")
    assert "&lt;script&gt;" in out
    assert "abc" in out


def test_overview_counts():
    out = _overview(3, 5)
    assert "<b>3</b>" in out
    assert "<b>5</b>" in out


def test_make_handler_returns_class():
    fake_client = MagicMock()
    H = _make_handler(fake_client)
    assert hasattr(H, "do_GET")
    # log_message is silenced
    inst = H.__new__(H)
    assert inst.log_message("anything") is None


def test_handler_routes_overview(monkeypatch):
    """Drive the handler in-memory: build a fake request, capture the response."""
    import io

    fake_client = MagicMock()
    fake_client.workflows.list.return_value = [type("W", (), {"id": "w1", "name": "Flow A"})()]
    fake_client.agents.list.return_value = [type("A", (), {"id": "a1", "name": "Bot"})()]

    H = _make_handler(fake_client)
    # Subclass to short-circuit network init.
    captured = {}

    class TestHandler(H):
        def __init__(self):
            self.path = "/"
            self.wfile = io.BytesIO()
            self.rfile = io.BytesIO()
            self.headers = {}  # type: ignore[assignment]

        def send_response(self, code):
            captured["code"] = code

        def send_header(self, *a, **k):
            pass

        def end_headers(self):
            pass

    with patch("noxuslab.portal.net_call", side_effect=lambda f, what: f()):
        TestHandler().do_GET()
    assert captured["code"] == 200


def test_handler_404_for_unknown_path():
    import io

    fake_client = MagicMock()
    H = _make_handler(fake_client)
    captured = {}

    class TestHandler(H):
        def __init__(self):
            self.path = "/nope"
            self.wfile = io.BytesIO()
            self.rfile = io.BytesIO()
            self.headers = {}  # type: ignore[assignment]

        def send_error(self, code, msg=None):
            captured["code"] = code

        def send_response(self, code):
            captured["code"] = code

        def send_header(self, *a, **k):
            pass

        def end_headers(self):
            pass

    TestHandler().do_GET()
    assert captured["code"] == 404
