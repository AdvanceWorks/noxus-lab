"""Tests for `noxuslab.cli` (offline)."""

from pathlib import Path

import pytest

from noxuslab.cli import _next_example_path


def test_next_example_path_starts_at_01(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = _next_example_path("foo")
    assert p.name == "01_foo.py"


def test_next_example_path_increments(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "examples").mkdir()
    (tmp_path / "examples" / "01_a.py").write_text("")
    (tmp_path / "examples" / "07_b.py").write_text("")
    p = _next_example_path("foo")
    assert p.name == "08_foo.py"


def test_main_version(capsys):
    from noxuslab.cli import main

    rc = main(["version"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out  # some version string


def test_main_requires_subcommand():
    from noxuslab.cli import main

    with pytest.raises(SystemExit):
        main([])
