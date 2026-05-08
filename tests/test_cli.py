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
