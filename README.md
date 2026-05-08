# noxus-lab

[![ci](https://github.com/AdvanceWorks/noxus-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/AdvanceWorks/noxus-lab/actions/workflows/ci.yml)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Workflow-as-code for [Noxus AI](https://noxus.ai).** Build in the
UI, edit in your IDE, review in pull requests, run/trace/debug from
the terminal.

## install

    pip install git+https://github.com/AdvanceWorks/noxus-lab.git@v0.9.1
    noxuslab init my-noxus-project
    cd my-noxus-project
    noxuslab doctor

The init wizard prompts for `NOXUS_API_KEY` and writes a chmod-600
`.env`. Get the key at *Noxus UI → Settings → Workspace → API Keys*.

## one cheat sheet

| You want to…                          | Run                                       |
| ------------------------------------- | ----------------------------------------- |
| Pull a workflow from the UI to code   | `noxuslab pull <workflow-id>`             |
| Run it locally + record logs          | `noxuslab run examples/NN_x.py --input k=v` |
| Inspect a past run (logs)             | `noxuslab trace [list \| show <id>]`      |
| Review-before-push (dry-run+diff+log) | `noxuslab check examples/NN_x.py`         |
| See server-vs-local diff              | `noxuslab diff examples/NN_x.py`          |
| Push a code-defined workflow back     | `noxuslab push examples/NN_x.py`          |
| Switch between API-key environments   | `noxuslab env [list \| use <name>]`       |
| Talk to one of your agents            | `noxuslab chat -a <agent-id>`             |
| One-shot question (pipe-friendly)     | `noxuslab ask "..." -a <agent-id>`        |
| List workflows / agents               | `noxuslab list` / `noxuslab agents`       |
| Manage agents as code                 | `noxuslab agents pull/push/diff/delete`   |
| Generate workflow code from a prompt  | `noxuslab gen "..."`                      |
| Auto-push on save                     | `noxuslab watch examples/NN_x.py`         |
| Reformat a workflow file              | `noxuslab fmt examples/*.py`              |
| Open the local read-only dashboard    | `noxuslab portal`                         |
| Diagnose env / network / SDK          | `noxuslab doctor`                         |
| Serve as an MCP tool to your editor   | `noxuslab mcp serve`                      |
| Upgrade the CLI                       | `pip install --upgrade git+https://github.com/AdvanceWorks/noxus-lab.git` |

Full reference: [docs/cli.md](docs/cli.md). Concepts:
[docs/concepts.md](docs/concepts.md). Renderer:
[docs/codegen.md](docs/codegen.md). MCP server:
[docs/mcp.md](docs/mcp.md).

## review loop

When a teammate builds a workflow in the Noxus UI and you want to
review, test, and push back via PR:

    noxuslab pull <workflow-id>             # 1. fetch as examples/NN_x.py
    noxuslab run  examples/NN_x.py --input topic=...   # 2. run + log
    noxuslab trace show <run-id>            # 3. read the logs
    noxuslab check examples/NN_x.py         # 4. dry-run + diff + last-trace
    git switch -c review/<short>            # 5. branch + commit
    git commit -am "review: <workflow-name>"
    git push -u origin HEAD                 # 6. open the PR
    # ... after PR review ...
    noxuslab push examples/NN_x.py          # 7. ship to Noxus

`noxuslab check` is the single "safe-to-commit?" gate: it dry-runs
the file, diffs it against the server (provenance header carries the
id, so no UUID needed), and prints the latest local trace status.
Exit 0 means clean; exit 1 means fix something first.

## why

The Noxus UI is great for sketching. Code is great for diffing,
reviewing, sharing, and version-controlling. `noxuslab pull <id>`
turns a workflow built in the UI into a clean Python file you can
edit and `push` back. Examples under `examples/` are top-level
scripts — read top-to-bottom, no magic.

## philosophy

Three rules:

1. **The reader matters more than the writer.** Examples are read
   100 000 times for every time they're written. Optimise for the
   reader on day one, sitting in front of `01_hello.py`.
2. **Small surface, sharp edges.** The package exports
   `workflow_to_python` and a CLI. Everything else is private
   (`_term`, `_net`, `_secrets`, `_audit`, …). When in doubt about
   adding something, don't.
3. **Standard library first.** Hard deps: `noxus-sdk` and
   `python-dotenv`. Everything else is stdlib.

## contributing

See [docs/contributing.md](docs/contributing.md) and
[AGENTS.md](AGENTS.md). Three commands cover the inner loop:

    pip install -e ".[dev]"
    ruff check . && ruff format .
    pytest

CI mirrors that on Linux, macOS, and Windows. Conventional Commits
required; pre-commit handles ruff + gitleaks; pre-push runs pytest.
