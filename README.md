# noxus-lab

Sandbox for the [Noxus AI](https://noxus.ai) Python SDK. Build flows,
agents, KBs in code; see them in the UI.

## setup

    make setup        # creates .venv, installs deps, copies .env
    $EDITOR .env      # set NOXUS_API_KEY

Get the key at *Settings → Workspace → API Keys*. Requires `python3` and
GNU `make`. On Windows use Git Bash (ships with Git).

## run

    make hello                    # build a workflow, prints id
    make run ID=<id> TOPIC=...    # run it
    make kb [DOC=path/to.txt]     # ingest a doc, search it
    make help                     # list targets

## dev

    make lint    # ruff check + format --check
    make fmt     # ruff --fix + format
    make clean   # nuke .venv and caches

Pre-commit: `pre-commit install`. CI in
[.github/workflows/ci.yml](.github/workflows/ci.yml). Logic shared with
`make` lives in [bin/](bin/).

## mcp

The SDK ships an MCP server (~39 tools). VS Code config in
[.vscode/mcp.json](.vscode/mcp.json). See [docs/mcp.md](docs/mcp.md).

## layout

    bin/         shared scripts (setup, lint, fmt, clean)
    examples/    one-file, self-contained scripts
    docs/        short notes
    Makefile     interface to the lab
    AGENTS.md    rules for AI assistants

MIT — see [LICENSE](LICENSE).
