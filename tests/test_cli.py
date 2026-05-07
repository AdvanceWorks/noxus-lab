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
