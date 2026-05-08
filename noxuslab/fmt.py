"""Workflow file formatter.

`noxuslab fmt <file>` runs the file in an isolated namespace, extracts its
`wf` variable, and rewrites the file with the canonical Python form produced
by `workflow_to_python`. This eliminates spurious diffs caused by node order,
edge order, kwarg order, or hand-edited whitespace.

It is the workflow analogue of `ruff format` for `noxuslab` files. Pure
local — no network calls. Sandbox + provenance handling is delegated to
the `LocalWorkflow` primitive in `_workflow.py`.

Modes:
- default: rewrite file in place (no-op if already canonical)
- `--check`: exit 1 if file would be rewritten, 0 otherwise (CI-friendly)
- `--diff`: print unified diff to stdout, do not write

Multiple files can be passed; exit code is the OR of per-file outcomes.
"""

import difflib
import sys
from pathlib import Path

from noxuslab._workflow import LocalWorkflow
from noxuslab.codegen import workflow_to_python
from noxuslab.errors import BadFile


def _canonical(path: Path) -> tuple[str, str]:
    """Return (current_source, canonical_source) for the file."""
    lw = LocalWorkflow.load(path)
    wf = lw.execute()
    canonical = workflow_to_python(wf, source_id=lw.provenance_id)
    return lw.text, canonical


def fmt_one(path: Path, *, check: bool, show_diff: bool) -> int:
    """Format a single file. Returns 0 if unchanged, 1 if changed (or would change)."""
    if not path.is_file():
        raise BadFile(f"not found: {path}")
    src, canonical = _canonical(path)
    if src == canonical:
        return 0
    if show_diff:
        diff = difflib.unified_diff(
            src.splitlines(keepends=True),
            canonical.splitlines(keepends=True),
            fromfile=str(path),
            tofile=f"{path} (canonical)",
            n=3,
        )
        sys.stdout.writelines(diff)
        return 1
    if check:
        print(f"would reformat: {path}")
        return 1
    path.write_text(canonical, encoding="utf-8")
    print(f"reformatted: {path}")
    return 1


def fmt(paths: list[str], *, check: bool = False, show_diff: bool = False) -> int:
    """Format every path. Exit code is 1 if any file was (or would be) reformatted."""
    if not paths:
        raise BadFile("no files provided")
    rc = 0
    for p in paths:
        rc |= fmt_one(Path(p), check=check, show_diff=show_diff)
    return rc
