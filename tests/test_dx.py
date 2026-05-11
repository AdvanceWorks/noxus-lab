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


def test_init_multi_process_scaffolds(tmp_path: Path):
    target = tmp_path / "acme_processes"
    rc = main(["init", "--multi-process", "--no-interactive", str(target)])
    assert rc == 0
    # Default workspace = one folder named `example_workspace`, no nesting.
    assert (target / "example_workspace" / "__init__.py").is_file()
    assert (target / "example_workspace" / "classifier.py").is_file()
    assert (target / "example_workspace" / "labels.py").is_file()
    assert (target / "example_workspace" / "tests" / "test_classifier.py").is_file()
    assert (target / "example_workspace" / "test_fixtures" / "README.md").is_file()
    assert (target / "example_workspace" / "agents" / "README.md").is_file()
    assert (target / "example_workspace" / "knowledge" / "README.md").is_file()
    assert (target / "example_workspace" / "workflows" / "classify.py").is_file()
    assert (target / "conftest.py").is_file()
    assert (target / "docs" / "architecture.md").is_file()
    assert (target / "docs" / "adding_a_workspace.md").is_file()
    assert (target / ".github" / "workflows" / "ci.yml").is_file()
    assert (target / ".env.example").is_file()
    assert (target / ".noxuslab-template-version").is_file()
    # No infrastructure code copied locally
    assert not (target / "shared").exists()
    assert not (target / "processes").exists()
    # Templates rendered + originals removed
    assert (target / "README.md").is_file()
    assert not (target / "README.md.tpl").exists()
    assert (target / "pyproject.toml").is_file()
    assert not (target / "pyproject.toml.tpl").exists()
    # The classifier imports the primitive from noxuslab, not a local copy
    classifier = (target / "example_workspace" / "classifier.py").read_text(encoding="utf-8")
    assert "from noxuslab.classify import" in classifier
    assert "from example_workspace.labels" in classifier


def test_init_multi_process_renders_template_vars(tmp_path: Path):
    target = tmp_path / "acme_processes"
    rc = main(["init", "--multi-process", "--no-interactive", str(target)])
    assert rc == 0
    pyproj = (target / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "acme_processes"' in pyproj
    assert '"example_workspace"' in pyproj
    readme = (target / "README.md").read_text(encoding="utf-8")
    assert "# acme_processes" in readme
    assert "{project_name}" not in readme
    assert "{version}" not in readme


def test_init_multi_process_with_custom_workspaces(tmp_path: Path):
    target = tmp_path / "demo"
    rc = main(
        [
            "init",
            "--multi-process",
            "--no-interactive",
            "--workspace",
            "hr_requests",
            "--workspace",
            "cf_orders",
            str(target),
        ]
    )
    assert rc == 0
    assert (target / "hr_requests" / "classifier.py").is_file()
    assert (target / "cf_orders" / "classifier.py").is_file()
    # Placeholders substituted in identifiers and module paths
    classifier = (target / "hr_requests" / "classifier.py").read_text(encoding="utf-8")
    assert "from hr_requests.labels" in classifier
    assert "__workspace__" not in classifier
    pyproj = (target / "pyproject.toml").read_text(encoding="utf-8")
    assert '"hr_requests"' in pyproj and '"cf_orders"' in pyproj
    assert '"--cov=hr_requests"' in pyproj
    assert '"--cov=cf_orders"' in pyproj


def test_init_multi_process_into_git_only_dir(tmp_path: Path):
    target = tmp_path / "existing"
    target.mkdir()
    (target / ".git").mkdir()
    (target / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    rc = main(["init", "--multi-process", "--no-interactive", str(target)])
    assert rc == 0
    assert (target / "example_workspace" / "classifier.py").is_file()


def test_init_multi_process_rejects_invalid_workspace_name(tmp_path: Path, capsys):
    target = tmp_path / "demo"
    rc = main(
        [
            "init",
            "--multi-process",
            "--no-interactive",
            "--workspace",
            "not-an-identifier",
            str(target),
        ]
    )
    assert rc == 1
    assert "not a valid Python identifier" in capsys.readouterr().err


def test_init_multi_process_rejects_duplicate_workspaces(tmp_path: Path, capsys):
    target = tmp_path / "demo"
    rc = main(
        [
            "init",
            "--multi-process",
            "--no-interactive",
            "--workspace",
            "hr_requests",
            "--workspace",
            "hr_requests",
            str(target),
        ]
    )
    assert rc == 1
    assert "unique" in capsys.readouterr().err


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
