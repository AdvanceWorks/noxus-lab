# noxus-lab

[![ci](https://github.com/AdvanceWorks/noxus-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/AdvanceWorks/noxus-lab/actions/workflows/ci.yml)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Workflow-as-code for [Noxus AI](https://noxus.ai).** Build in the UI,
edit in your IDE, review in pull requests. Chat with your AI agents from
the terminal. Two artifacts, one idea:

- **This template repo** — clone-and-go starter with examples, docs,
  pre-commit, CI. *Use this template* on the GitHub page.
- **The `noxuslab` CLI** — install directly from git for users who
  already have a repo. Powers the UI ↔ code round-trip + agent chat.

## quick start

Two paths, same repo:

| You are a... | Do this |
|---|---|
| **Builder** (writes code) | `make setup` → `make hello` → `make pull ID=<id>` → edit → PR → `make push FILE=examples/NN_<slug>.py` |
| **User** (talks to AI) | `make setup` → `make chat AGENT=<id>` — ask questions, get answers |

See [docs/quickstart.md](docs/quickstart.md) for a zero-assumption setup guide (no coding background needed).
See [docs/for-builders.md](docs/for-builders.md) or
[docs/for-users.md](docs/for-users.md) for the full guide.

## why

The Noxus UI is great for sketching. Code is great for diffing,
reviewing, sharing, and version-controlling. `noxuslab pull <id>`
turns a workflow you built in the UI into a clean Python file you can
edit and `push` back. The package stays small on purpose — see
[docs/philosophy.md](docs/philosophy.md).

## install

    # CLI only, drop into any existing project:
    pip install git+https://github.com/AdvanceWorks/noxus-lab.git@v0.3.2

    # or, full template:
    # click 'Use this template' on github.com/AdvanceWorks/noxus-lab

## what you get

- `examples/` — one self-contained script per concept. Read top-down.
- `noxuslab/` — small package with a CLI: `noxuslab pull <id>` turns a
  workflow built in the UI into an editable Python file under
  `examples/`. `noxuslab push <file>` does the reverse.
- A real CI pipeline: ruff + pytest on every push.
- A `noxuslab` console script (also `python -m noxuslab`).

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
    make chat [AGENT=<id>]        # interactive agent conversation
    make ask Q="..." [AGENT=<id>] # one-shot question (pipe-friendly)
    make list                     # show workflows
    make agents                   # show agents
    make pull ID=<id> [OUT=...]   # workflow id -> examples/NN_<slug>.py
    make push FILE=examples/...   # send a code-defined workflow back
    make help                     # list all targets

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
    08_chat.py         start a conversation with an agent

## mcp

The SDK ships an MCP server (~39 tools across workflows, agents, KBs).
VS Code config in [.vscode/mcp.json](.vscode/mcp.json). See
[docs/mcp.md](docs/mcp.md).

## docs

- [docs/for-users.md](docs/for-users.md) — non-technical guide (chat with agents)
- [docs/for-builders.md](docs/for-builders.md) — developer workflow guide
- [docs/philosophy.md](docs/philosophy.md) — three rules
- [docs/concepts.md](docs/concepts.md) — primitives in 3 minutes
- [docs/cli.md](docs/cli.md) — full CLI reference
- [docs/codegen.md](docs/codegen.md) — how `noxuslab pull` works, limits
- [docs/mcp.md](docs/mcp.md) — MCP server quick start
- [docs/publish.md](docs/publish.md) — git workflow for this repo
- [docs/security.md](docs/security.md) — vulnerability reporting
- [docs/contributing.md](docs/contributing.md) — dev loop, PR checklist
- [CHANGELOG.md](CHANGELOG.md) — release notes
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
