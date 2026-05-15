"""noxuslab: a terse sandbox and CLI for the Noxus AI SDK.

The package itself is intentionally tiny. Public surface:

- `noxuslab.codegen.workflow_to_python(wf, var="wf")` — render a
  `WorkflowDefinition` as a self-contained Python script.
- `noxuslab.cli.main()` — the `noxuslab` CLI (`pull`, `push`, `diff`,
  `chat`, `ask`, `list`, `agents`, `show`, `init`, `version`).
- `noxuslab.helpers.push_workflow(wf)` — push a workflow to the Noxus AI
  server.
- `noxuslab.helpers.find_workflow_id_by_name(name)` — find a workflow
  by name.

Everything pedagogical lives under `examples/` at the repo root and is
deliberately kept terse and free of `noxuslab` imports.
"""

__version__ = "0.15.0"

from .helpers.client import make_client
from .helpers.workflow import find_workflow_id_by_name, push_workflow

__all__ = [
    "find_workflow_id_by_name",
    "make_client",
    "push_workflow",
]
