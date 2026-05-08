"""noxuslab: a terse sandbox and CLI for the Noxus AI SDK.

The package itself is intentionally tiny. Public surface:

- `noxuslab.codegen.workflow_to_python(wf, var="wf")` — render a
  `WorkflowDefinition` as a self-contained Python script.
- `noxuslab.cli.main()` — the `noxuslab` CLI (`pull`, `push`, `diff`,
  `chat`, `ask`, `list`, `agents`, `show`, `init`, `version`).

Everything pedagogical lives under `examples/` at the repo root and is
deliberately kept terse and free of `noxuslab` imports.
"""

__version__ = "0.6.0"
