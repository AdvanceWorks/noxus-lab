# codegen — UI workflow → Python file

`noxuslab pull <workflow_id>` fetches a workflow you built in the UI
and writes a self-contained Python file under `examples/` that
re-creates it. The reverse — `noxuslab push <file>` — saves a
code-defined workflow back to your workspace.

## How it works

1. `client.workflows.get(id)` returns a `WorkflowDefinition`.
2. We call `.to_noxus()` to get the wire dict
   (`{"name", "type", "definition": {"nodes", "edges"}}`).
3. We topologically sort the nodes (Kahn) so the generated file reads
   top-to-bottom: inputs first, leaves last.
4. Each node becomes:
   ```python
   nN = wf.node("<NodeType>").config(<kwargs>)
   ```
   where `<kwargs>` are the keys actually set on the node in the UI
   (defaults are skipped — they live on the server's
   `config_definition`).
5. Each edge becomes:
   ```python
   wf.link(nA.output("<connector>"), nB.input("<connector>"[, "<key>"]))
   ```
   The `key` is only emitted when the destination is a *variables*
   connector (e.g. `("variables", "topic")`).
6. Anything wider than 80 chars when `repr()`'d is hoisted into a
   module-level constant (`_TEMPLATE = "..."`) so the script stays
   readable.
7. The header includes a docstring, `dotenv` load, `Client` setup, and
   a final `print(c.workflows.save(wf).id)`.
8. The whole regenerable region (`WorkflowDefinition` constructor +
   nodes + edges + final `save` line) is wrapped between sentinel
   comments:
   ```python
   # >>> noxuslab:generated >>>
   ...
   # <<< noxuslab:generated <<<
   ```
   On a re-pull the splice replaces only what's between the sentinels;
   any user code outside (extra imports, helper functions, custom
   blocks, comments) is preserved. See
   `noxuslab.codegen.splice_generated` for the splice logic and
   `noxuslab fmt` for the canonicalisation pass.
9. Each node block carries a section comment (`# --- <title>
   (<NodeType>) ---`) and emits `node.name = "<title>"` when a display
   title is set, so re-pushing the file keeps the descriptive names
   visible in the Noxus UI.

## Round-tripping

A pulled file, when run, creates a *new* workflow with the same
structure. It does **not** overwrite the original — that's
intentional, because pulls are read-only by design. Use the new id, or
edit the file and use `make push FILE=...` to send updates.

## Limits and edge cases

- **Non-renderable config keys.** If a config dict has a key that is
  not a valid Python identifier or is a reserved keyword (`if`, `for`,
  `class`...), the generator skips it and emits a comment:
  `# noxuslab: dropped non-renderable config key(s) on n0: 'if'`.
  These keys still round-trip via the wire dict on the server but
  cannot be expressed as Python kwargs.
- **Subflows / agent flows.** `subflow_id` is preserved in the wire
  dict but the SDK does not expose a clean builder API for it yet.
  Workflows that nest agent flows will round-trip but may lose
  internal layout metadata.
- **Unknown node types.** If a workflow uses a node type not present
  in your `client.nodes`, the generated file will still read fine but
  `wf.node("X")` will fail at save-time. Solution: install the plugin
  that ships that node type.
- **Big binary configs.** Configs containing bytes / binary blobs are
  rendered with `repr()` and hoisted; the generated file may end up
  large. Prefer keeping such payloads in separate files referenced by
  path.
- **Display positions.** Layout (`display.position.x/y`) is not
  emitted. The new workflow will be auto-laid out by the UI.
- **Run history / triggers.** Pull is workflow-only. Triggers, runs,
  and KB attachments are not exported.
- **Cycles in the graph.** Topological sort falls back to original
  insertion order when a cycle is detected; the generated file is
  still valid but may not read top-to-bottom.

## Public API

```python
from noxuslab.codegen import workflow_to_python

code: str = workflow_to_python(
    wf,                  # WorkflowDefinition or wire dict
    var="wf",            # name of the WorkflowDefinition variable
    include_imports=True,# emit shebang/docstring/imports/dotenv/Client
    runnable=True,       # append `print(c.workflows.save(wf).id)`
)
```

## See also

- [examples/07_pull_demo.py](../examples/07_pull_demo.py) — print, no write.
- [tests/test_codegen.py](../tests/test_codegen.py) — golden cases.
