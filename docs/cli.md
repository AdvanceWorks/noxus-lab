# noxuslab CLI

Tiny CLI installed by `make setup` (via `pip install -e .`).

    noxuslab --help
    noxuslab version
    noxuslab pull <workflow_id> [--out PATH]
    noxuslab push <file>

`pull` and `push` need `NOXUS_API_KEY` in your environment (loaded
from `.env` automatically). Optional: `NOXUS_BACKEND_URL` for
self-hosted instances.

## pull

    noxuslab pull 1b115224-aaaa-bbbb-cccc-...

Writes `examples/NN_<slug>.py` (next free `NN`). Override with
`--out` if you want a custom path. The generated file is
self-contained: run it with `python examples/NN_<slug>.py` to create a
*new* workflow in your workspace with the same structure.

See [docs/codegen.md](codegen.md) for the rendering details.

## push

    noxuslab push examples/NN_my_flow.py

Executes the file in a fresh namespace, expects a top-level `wf`
variable that is a `WorkflowDefinition`, then calls
`client.workflows.save(wf)` and prints the resulting id. The trailing
`print(c.workflows.save(wf).id)` line in pulled files is stripped
before exec to avoid double-saving.

> Security: `push` runs the file with `exec`. Only push code you wrote
> or reviewed.

## version

    noxuslab version

Prints the installed `noxuslab` version. Handy in bug reports.
