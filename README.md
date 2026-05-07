# noxus-lab

[![ci](https://github.com/AdvanceWorks/noxus-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/AdvanceWorks/noxus-lab/actions/workflows/ci.yml)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Sandbox + tiny CLI for the [Noxus AI](https://noxus.ai) Python SDK.
Build flows in the UI, pull them into clean Python files, push them
back. Or write the flow in code from scratch — your call.

> Use this repo as a **GitHub template** to bootstrap your own Noxus
> project. Click *Use this template* on the repo page.

## what you get

- `examples/` — one self-contained script per concept. Read top-down.
- `noxuslab/` — small package with a CLI: `noxuslab pull <id>` turns a
  workflow built in the UI into an editable Python file under
  `examples/`. `noxuslab push <file>` does the reverse.
- A real CI pipeline: ruff + pytest on Linux/macOS/Windows × Py 3.10/11/12.

## setup

    make setup        # creates .venv, installs deps, copies .env
    $EDITOR .env      # set NOXUS_API_KEY

Get the key at *Settings → Workspace → API Keys*. Requires `python3` and
GNU `make`. On Windows, install Git for Windows (provides `sh`) and
GnuWin32 `make`.

## run

    make hello                    # build a workflow, prints id
    make run ID=<id> TOPIC=...    # run it
    make kb [DOC=path/to.txt]     # ingest a doc, search it
    make pull ID=<id> [OUT=...]   # workflow id -> examples/NN_<slug>.py
    make push FILE=examples/...   # send a code-defined workflow back
    make help                     # list targets

## dev

    make lint        # ruff check + format --check
    make fmt         # ruff --fix + format
    make test        # pytest
    make typecheck   # pyright (warning-only)
    make clean       # nuke .venv and caches

`pre-commit install` once. Hooks cover ruff, gitleaks, line endings.
CI mirrors all of this — see [.github/workflows/ci.yml](.github/workflows/ci.yml).

## examples

    01_hello.py        build a 3-node workflow
    02_run.py          run a saved workflow
    03_kb.py           create + ingest + search a knowledge base
    04_agent.py        agent with a workflow tool, then chat
    05_async.py        parallel KB ops via asyncio
    06_introspect.py   list available node types and models
    07_pull_demo.py    print generated python for a workflow id

## mcp

The SDK ships an MCP server (~39 tools across workflows, agents, KBs).
VS Code config in [.vscode/mcp.json](.vscode/mcp.json). See
[docs/mcp.md](docs/mcp.md).

## docs

- [docs/concepts.md](docs/concepts.md) — primitives in 3 minutes
- [docs/codegen.md](docs/codegen.md) — how `noxuslab pull` works, limits
- [docs/mcp.md](docs/mcp.md) — MCP server quick start
- [docs/publish.md](docs/publish.md) — git workflow for this repo
- [docs/security.md](docs/security.md) — vulnerability reporting
- [docs/contributing.md](docs/contributing.md) — dev loop, PR checklist
- [AGENTS.md](AGENTS.md) — rules for AI assistants and contributors

## layout

    bin/         shared scripts (setup, lint, fmt, clean, test, typecheck)
    examples/    one-file, self-contained scripts
    noxuslab/    pull/push CLI + codegen
    tests/       pytest suite (offline)
    docs/        short notes
    Makefile     interface to the lab
    AGENTS.md    rules for AI assistants

MIT — see [LICENSE](LICENSE).
