"""Deploy every workflow in this repo to the currently-selected Noxus tenant.

Idempotent: each workflow is updated in place if it already exists on
the platform (matched by name), otherwise created. The tenant is
selected by environment variables — locally via
``noxuslab env use staging|prod``, in CI via the GitHub Environment.

Each workspace folder is one Noxus workspace. Inside, every
``<workspace>/workflows/*.py`` file (excluding underscore-prefixed
modules like ``_common.py``) is one workflow definition.

Two supported workflow-module shapes are auto-detected:

1. ``build() -> WorkflowDefinition`` — preferred. The function is
   called and the returned definition is pushed.
2. Module-level ``wf`` attribute — legacy / template default. The
   attribute is pushed directly.

Run::

    python scripts/deploy.py            # all workspaces
    python scripts/deploy.py pagamentos # one workspace
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
import traceback
from typing import Any

from noxuslab import make_client, push_workflow

# Filled at scaffold time. Add a workspace by appending to this list.
WORKSPACES: list[str] = [{workspace_packages}]

EXCLUDED_PREFIXES = ("_", ".")


def _iter_workflow_modules(workspace: str):
    pkg = importlib.import_module(f"{{workspace}}.workflows")
    for info in pkgutil.iter_modules(pkg.__path__):
        if any(info.name.startswith(p) for p in EXCLUDED_PREFIXES):
            continue
        yield f"{{workspace}}.workflows.{{info.name}}"


def _extract_definition(module: Any):
    """Return a WorkflowDefinition from a workflow module, or None."""
    if callable(getattr(module, "build", None)):
        return module.build()
    return getattr(module, "wf", None)


def main(argv: list[str]) -> int:
    targets = argv[1:] or WORKSPACES
    unknown = [t for t in targets if t not in WORKSPACES]
    if unknown:
        print(f"unknown workspace(s): {{', '.join(unknown)}}", file=sys.stderr)
        print(f"available: {{', '.join(WORKSPACES)}}", file=sys.stderr)
        return 2

    client = make_client()
    failures: list[str] = []
    for ws in targets:
        print(f"\n=== {{ws}} ===")
        for mod_name in _iter_workflow_modules(ws):
            try:
                module = importlib.import_module(mod_name)
                wf = _extract_definition(module)
                if wf is None:
                    print(f"  skip {{mod_name}} (no build()/wf)")
                    continue
                push_workflow(client, wf)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{{mod_name}}: {{exc}}")
                traceback.print_exc()
    if failures:
        print(f"\n{{len(failures)}} workflow(s) failed:", file=sys.stderr)
        for f in failures:
            print(f"  - {{f}}", file=sys.stderr)
        return 1
    print("\nall workflows deployed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
