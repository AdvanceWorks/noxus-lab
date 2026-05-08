"""Tests for `noxuslab._term` and `noxuslab init`."""

from pathlib import Path

import pytest

from noxuslab._term import _enabled, bold, dim, green, red
from noxuslab.cli import main


def test_term_no_color(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    assert not _enabled()
    assert bold("x") == "x"
    assert red("x") == "x"


def test_term_wraps_when_enabled(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    for fn in (bold, dim, red, green):
        out = fn("hi")
        assert out.endswith("\x1b[0m")
        assert "hi" in out


def test_init_scaffolds(tmp_path: Path):
    target = tmp_path / "newproj"
    rc = main(["init", str(target)])
    assert rc == 0
    assert (target / "README.md").is_file()
    readme = (target / "README.md").read_text(encoding="utf-8")
    assert "noxuslab doctor" in readme
    assert "pip install --upgrade git+https://github.com/AdvanceWorks/noxus-lab.git" in readme
    assert "make setup" not in readme


def test_init_refuses_non_empty(tmp_path: Path, capsys):
    (tmp_path / "x.txt").write_text("hi")
    rc = main(["init", str(tmp_path)])
    assert rc == 1
    assert "refusing" in capsys.readouterr().err


def test_did_you_mean_hint(capsys):
    monkeypatch_argv = ["pul", "abc"]
    with pytest.raises(SystemExit):
        main(monkeypatch_argv)
    err = capsys.readouterr().err
    assert "pul" in err or "did you mean" in err


def test_version_consistent_across_sources():
    """`pyproject.toml`::project.version must equal `noxuslab.__version__`."""
    import sys

    if sys.version_info >= (3, 11):
        import tomllib  # type: ignore[import-not-found]
    else:
        import tomli as tomllib  # type: ignore[import-not-found,no-redef]

    import noxuslab

    toml = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert noxuslab.__version__ == toml["project"]["version"]
