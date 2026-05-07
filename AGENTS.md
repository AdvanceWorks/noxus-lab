# AGENTS.md

Rules for AI coding assistants in this repo.

## Mission

Learning sandbox for the Noxus AI platform. Small, readable, runnable.
One concept per example. No abstractions, no framework.

## House rules

- **English only** in code, comments, docs, commits.
- **Minimal deps.** Justify every line in `requirements.txt`. Dev-only
  tools go in `requirements-dev.txt`.
- **One concept per example.** New file under `examples/NN_short_name.py`,
  numbered. Self-contained. No shared utility module.
- **Top-level scripts.** No `def main()`, no `if __name__ == "__main__"`,
  no `from __future__ import annotations`. Type hints only where they aid
  the reader.
- **Read source first.** The `noxus-sdk` README is the source of truth; do
  not invent APIs. If unsure: `python -c "from noxus_sdk import *; help(...)"`.
- **No secrets.** Never commit `.env`, API keys, workspace IDs. Load via
  `os.environ` after `dotenv.load_dotenv()`.
- **Idempotent.** Scripts safe to re-run; check existence or accept dups
  and print clear IDs.
- **Print, don't log.** This is a lab.
- **Small commits.** One change. Imperative subject (`add kb example`).

## Build & CI

- `make` is the single user interface.
- All non-trivial logic lives in `bin/` so CI runs the exact same code.
  Never duplicate logic between the Makefile and CI — add a script in
  `bin/` and call it from both.
- Lint with `ruff` (config in `ruff.toml`). Pre-commit enforces it.
- CI: [.github/workflows/ci.yml](.github/workflows/ci.yml) runs
  `bin/setup`, `bin/lint`, then `compileall examples`.

## Style

- Python 3.10+, standard library first.
- `ruff` formatter is canonical.
- Plain, terse, UNIX.

## When asked to add an example

1. Pick the next free number under `examples/`.
2. Shebang + one-line docstring with the invocation.
3. Load env, build, run, print. Done.
4. Add a `make` target only if the script takes parameters worth naming.
5. Append a one-line entry to the *run* section of the README.

## When asked about MCP

Point to [docs/mcp.md](docs/mcp.md) and [.vscode/mcp.json](.vscode/mcp.json).
The Noxus SDK ships `noxus mcp serve`. Do not reimplement it.

## Out of scope

- Production deployment.
- Wrapping the SDK in custom abstractions.
- Anything that turns this into a framework.
