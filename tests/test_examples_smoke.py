"""Smoke tests: every example file at least compiles cleanly."""

import py_compile
from pathlib import Path

import pytest

EXAMPLES = sorted(Path("examples").glob("*.py"))


@pytest.mark.parametrize("example", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_example_compiles(example: Path, tmp_path: Path):
    py_compile.compile(str(example), cfile=str(tmp_path / (example.stem + ".pyc")), doraise=True)
