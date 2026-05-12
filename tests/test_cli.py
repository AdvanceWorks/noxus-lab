"""Tests for `noxuslab.cli` (offline)."""

import sys
from pathlib import Path

import pytest

from noxuslab.cli import _check_id, _next_example_path, main
from noxuslab.errors import NoxusLabError


def test_next_example_path_starts_at_01(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert _next_example_path("foo").name == "01_foo.py"


def test_next_example_path_increments(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "examples").mkdir()
    (tmp_path / "examples" / "01_a.py").write_text("")
    (tmp_path / "examples" / "07_b.py").write_text("")
    assert _next_example_path("foo").name == "08_foo.py"


def test_check_id_accepts_uuid():
    _check_id("11111111-2222-3333-4444-555555555555")


def test_check_id_rejects_garbage():
    with pytest.raises(NoxusLabError):
        _check_id("not-a-uuid")


def test_main_version_subcommand(capsys):
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip()


def test_main_global_version_flag(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert "noxuslab" in capsys.readouterr().out


def test_main_requires_subcommand():
    with pytest.raises(SystemExit):
        main([])


def test_pull_rejects_bad_id(capsys):
    rc = main(["pull", "garbage"])
    assert rc == 1
    assert "not a uuid" in capsys.readouterr().err


def test_python_dash_m_works():
    """`python -m noxuslab version` runs via __main__.py."""
    import subprocess

    r = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "noxuslab", "version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert r.stdout.strip()


def test_push_dry_run_validates_without_save(tmp_path: Path, monkeypatch, capsys):
    """`push --dry-run` runs the file but never builds a client."""
    monkeypatch.chdir(tmp_path)
    f = tmp_path / "flow.py"
    f.write_text(
        "class W:\n    nodes = [1, 2, 3]\n    edges = [(1, 2), (2, 3)]\nwf = W()\n",
        encoding="utf-8",
    )
    # Sentinel: if _client is called, raise loudly.
    from noxuslab import cli

    monkeypatch.setattr(cli, "_client", lambda: pytest.fail("must not call _client"))
    rc = main(["push", str(f), "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "3 nodes" in out and "2 edges" in out


def test_push_rejects_file_without_wf(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    f = tmp_path / "no_wf.py"
    f.write_text("x = 1\n", encoding="utf-8")
    rc = main(["push", str(f), "--dry-run"])
    assert rc == 1


def test_push_rejects_missing_file(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = main(["push", str(tmp_path / "ghost.py"), "--dry-run"])
    assert rc == 1


def _push_fixture_file(tmp_path: Path, name: str = "demo") -> Path:
    """Write a minimal flow file whose `wf` carries `name`."""
    f = tmp_path / "flow.py"
    f.write_text(
        f"class W:\n    name = {name!r}\n    nodes = []\n    edges = []\nwf = W()\n",
        encoding="utf-8",
    )
    return f


def test_push_updates_existing_workflow_by_name(tmp_path, monkeypatch, capsys):
    """Re-pushing a file with the same `wf.name` MUST update, not duplicate."""
    monkeypatch.chdir(tmp_path)
    f = _push_fixture_file(tmp_path, name="demo")

    saves: list = []
    updates: list = []

    class FakeWf:
        def __init__(self, wid: str, wname: str):
            self.id = wid
            self.name = wname

    class FakeWorkflows:
        def list(self, page_size: int = 100):  # noqa: ARG002
            return [FakeWf("existing-id", "demo")]

        def save(self, wf):
            saves.append(wf)
            return FakeWf("new-id", wf.name)

        def update(self, wid, wf, force=False):  # noqa: ARG002
            updates.append((wid, wf))
            return FakeWf(wid, wf.name)

    class FakeClient:
        workflows = FakeWorkflows()

    from noxuslab import cli

    monkeypatch.setattr(cli, "_client", lambda: FakeClient())
    rc = main(["push", str(f)])
    assert rc == 0
    assert updates and updates[0][0] == "existing-id", "must call update on existing"
    assert not saves, "must not call save when a workflow with that name exists"
    assert "existing-id" in capsys.readouterr().out


def test_push_creates_when_no_workflow_with_that_name(tmp_path, monkeypatch, capsys):
    """First push of a brand-new workflow falls back to save()."""
    monkeypatch.chdir(tmp_path)
    f = _push_fixture_file(tmp_path, name="brand-new")

    class FakeWf:
        def __init__(self, wid: str, wname: str):
            self.id = wid
            self.name = wname

    saves: list = []

    class FakeWorkflows:
        def list(self, page_size: int = 100):  # noqa: ARG002
            return [FakeWf("other-id", "something-else")]

        def save(self, wf):
            saves.append(wf)
            return FakeWf("created-id", wf.name)

        def update(self, *_args, **_kwargs):  # pragma: no cover - guard
            raise AssertionError("update must not be called when no name match")

    class FakeClient:
        workflows = FakeWorkflows()

    from noxuslab import cli

    monkeypatch.setattr(cli, "_client", lambda: FakeClient())
    rc = main(["push", str(f)])
    assert rc == 0
    assert len(saves) == 1
    assert "created-id" in capsys.readouterr().out


def test_diff_rejects_missing_file(tmp_path: Path):
    rc = main(["diff", "11111111-2222-3333-4444-555555555555", str(tmp_path / "ghost.py")])
    assert rc == 1


def test_diff_rejects_bad_id(tmp_path: Path, capsys):
    f = tmp_path / "x.py"
    f.write_text("# any\n", encoding="utf-8")
    rc = main(["diff", "garbage", str(f)])
    assert rc == 1
    assert "not a uuid" in capsys.readouterr().err


def test_show_rejects_bad_id(capsys):
    rc = main(["show", "garbage"])
    assert rc == 1
    assert "not a uuid" in capsys.readouterr().err


def test_extract_source_id_from_provenance():
    from noxuslab.cli import _extract_source_id

    src = "# generated by `noxuslab pull` from 11111111-2222-3333-4444-555555555555 @ 2026\nx = 1\n"
    assert _extract_source_id(src) == "11111111-2222-3333-4444-555555555555"
    assert _extract_source_id("no header here\n") is None


def test_diff_without_id_and_no_provenance(tmp_path: Path, capsys):
    f = tmp_path / "x.py"
    f.write_text("# any\nwf = None\n", encoding="utf-8")
    rc = main(["diff", str(f)])
    assert rc == 1


# --- pull splice / regen ---------------------------------------------------


def _stub_pull(monkeypatch, wf_dict: dict) -> None:
    """Make `cmd_pull` return `wf_dict` instead of hitting the network."""
    from noxuslab import cli

    class _Ws:
        def get(self, *, workflow_id):  # noqa: ARG002
            return wf_dict

    class _Client:
        workflows = _Ws()

    monkeypatch.setattr(cli, "_client", lambda: _Client())
    # `_format_with_ruff` invokes a subprocess; skip in tests.
    monkeypatch.setattr(cli, "_format_with_ruff", lambda _p: None)


def test_pull_splices_into_existing_file_with_sentinels(
    tmp_path: Path, monkeypatch, sample_workflow_dict
):
    """A re-pull replaces only the sentinel region; user code outside survives."""
    _stub_pull(monkeypatch, sample_workflow_dict)
    out = tmp_path / "flow.py"
    wfid = "11111111-2222-3333-4444-555555555555"
    monkeypatch.chdir(tmp_path)
    assert main(["pull", wfid, "-o", str(out)]) == 0
    # User edits the file, adding a helper above and a comment below.
    text = out.read_text(encoding="utf-8")
    edited = (
        text.replace("import os\n", "import os\n\ndef my_helper():\n    return 'preserved'\n", 1)
        + "\n# user trailing comment\n"
    )
    out.write_text(edited, encoding="utf-8")
    # Re-pull should keep user code.
    assert main(["pull", wfid, "-o", str(out)]) == 0
    after = out.read_text(encoding="utf-8")
    assert "def my_helper():" in after
    assert "# user trailing comment" in after
    assert "WorkflowDefinition(name='test-flow')" in after


def test_pull_refuses_existing_file_without_sentinels(
    tmp_path: Path, monkeypatch, sample_workflow_dict, capsys
):
    _stub_pull(monkeypatch, sample_workflow_dict)
    out = tmp_path / "flow.py"
    out.write_text("# user file with no sentinels\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    rc = main(["pull", "11111111-2222-3333-4444-555555555555", "-o", str(out)])
    assert rc == 1
    assert "refusing to overwrite" in capsys.readouterr().err


def test_pull_regen_overwrites_user_code(tmp_path: Path, monkeypatch, sample_workflow_dict):
    _stub_pull(monkeypatch, sample_workflow_dict)
    out = tmp_path / "flow.py"
    out.write_text("# user file with no sentinels\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main(["pull", "11111111-2222-3333-4444-555555555555", "-o", str(out), "--regen"]) == 0
    assert "WorkflowDefinition(name='test-flow')" in out.read_text(encoding="utf-8")


def test_check_dry_run_passes_offline(tmp_path: Path, monkeypatch, capsys):
    """`check` on a valid file with no provenance: dry-run ok, diff skipped."""
    monkeypatch.chdir(tmp_path)
    f = tmp_path / "flow.py"
    f.write_text(
        "class W:\n    nodes = [1]\n    edges = []\nwf = W()\n",
        encoding="utf-8",
    )
    from noxuslab import cli

    monkeypatch.setattr(cli, "_client", lambda: pytest.fail("must not call _client"))
    rc = main(["check", str(f)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "check ok" in out
    assert "no provenance" in out


def test_check_with_provenance_and_trace(tmp_path: Path, monkeypatch, capsys):
    """`check` with provenance + a matching local trace: diff stub OK, trace shown."""
    import json as _json

    monkeypatch.chdir(tmp_path)
    wid = "11111111-2222-3333-4444-555555555555"
    f = tmp_path / "flow.py"
    f.write_text(
        f"# generated by `noxuslab pull` from {wid} @ 2026\n"
        "class W:\n    nodes = []\n    edges = []\nwf = W()\n",
        encoding="utf-8",
    )
    # Stub cmd_diff to skip the network entirely.
    from noxuslab import cli

    monkeypatch.setattr(cli, "cmd_diff", lambda _a: 0)
    # Lay down a matching trace file.
    tdir = tmp_path / ".noxuslab" / "traces"
    tdir.mkdir(parents=True)
    tp = tdir / "2026-05-08T00-00-00_runX.jsonl"
    tp.write_text(
        _json.dumps({"kind": "header", "ts": "2026-05-08T00:00:00", "workflow_id": wid})
        + "\n"
        + _json.dumps(
            {"kind": "footer", "ts": "2026-05-08T00:00:01", "status": "completed", "elapsed_ms": 42}
        )
        + "\n",
        encoding="utf-8",
    )
    rc = main(["check", str(f)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "check ok" in out
    assert "completed" in out
    assert "42ms" in out


def test_check_rejects_missing_file(tmp_path: Path, capsys):
    rc = main(["check", str(tmp_path / "ghost.py")])
    assert rc == 1
    assert "not found" in capsys.readouterr().err


def test_check_fails_when_dry_run_fails(tmp_path: Path, monkeypatch, capsys):
    """A file without `wf` makes the dry-run fail; check returns non-zero."""
    monkeypatch.chdir(tmp_path)
    f = tmp_path / "no_wf.py"
    f.write_text("x = 1\n", encoding="utf-8")
    rc = main(["check", str(f)])
    assert rc == 1
    err = capsys.readouterr().err
    assert "wf" in err  # cmd_push complains about missing `wf`
