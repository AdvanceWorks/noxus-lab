# AGENTS.md — rules for AI assistants and contributors

This file is the contract every contributor (human or LLM) follows when
touching the repo. Read it once. It is short on purpose.

## North star

A **terse, modern, learn-by-reading** sandbox for the Noxus AI Python
SDK. Two layers, sharply separated:

1. **`examples/`** — one concept per script. Top-level code, no `def
   main`, no `__future__`, no abstractions. Optimise for *the reader on
   their first day*.
2. **`noxuslab/`** — small reusable package. Real docstrings, type
   hints, tests. Optimise for *the reader writing their tenth script*.

If a piece of logic appears twice in `examples/`, it is a candidate for
`noxuslab/`. If it appears once, it stays inline.

## Hard rules

- **English only.** Comments, docstrings, identifiers, commit messages.
- **No secrets in git.** `.env` is gitignored; `.env.example` is the
  template. `gitleaks` runs on every commit.
- **Idempotent-ish examples.** Running an example must not destroy
  workflows or KBs that already exist on the platform. Create new
  resources; let the user clean up via the UI or `make`.
- **Conventional Commits.** `feat:`, `fix:`, `chore:`, `docs:`,
  `refactor:`, `test:`, `ci:`. One topic per commit.
- **Lint clean.** `make lint` must pass. `make test` must pass. CI
  enforces both on three OSes and three Python versions.
- **Don't add a dependency without need.** Justify in the PR. Pin
  exactly one version of `noxus-sdk`.
- **Update CHANGELOG on every change.** Every commit that ships
  user-visible behaviour appends a bullet under `## [Unreleased]` in
  `CHANGELOG.md`. Sections: `### Added`, `### Changed`, `### Fixed`,
  `### Removed`. AI assistants must do this automatically — no
  exceptions for "small" changes.
- **No Docker.** This is a Python CLI; `pip install` and `make setup`
  cover all targets. Adding a Dockerfile is a regression in DX.

## Style

- **Examples**: shebang, 1-line docstring with the invocation, top-level
  script, `print` for output. Target ≤ 80 lines.
- **Package code**: explicit imports, type hints on public APIs, no
  exceptions for "just in case". Validate at boundaries only.
- **Naming**: `snake_case` files, `PascalCase` classes, lowercase
  example prefixes (`NN_short_name.py`).

## Workflow

    make setup
    make lint && make test
    git switch -c feat/<short>
    # ...code...
    pre-commit run --all-files
    git commit -m "feat(scope): one-line summary"
    git push -u origin HEAD
    # open PR

Branch names follow `<type>/<short-kebab>`. PR titles follow
Conventional Commits. PRs require a green CI before merge.

## Extending noxus-lab

You have three good entry points:

1. **Add an example.** Pick the next free `NN_` prefix under
   `examples/`. Mirror the style of existing ones. If your idea needs a
   helper that other scripts could share, propose it for `noxuslab/`.
2. **Improve the codegen.** `noxuslab.codegen.workflow_to_python`
   produces Python from a `WorkflowDefinition`. Edge cases live in
   `tests/test_codegen.py`. Add a failing test before changing the
   generator.
3. **Add a CLI subcommand.** `noxuslab` lives in `noxuslab/cli.py`. New
   subcommands subclass nothing — just add a parser branch. Keep
   side-effects out of import time.

For deeper changes (new SDK abstraction, a new package under
`noxuslab/`), open an issue first.

## Out of scope

- Re-implementing the SDK or backend.
- A web UI for this lab.
- Multi-tenant support — one API key per workspace, full stop.
- Translating prose to PT/ES.
- Auto-publishing or auto-deleting platform resources.

## When the agent is stuck

Read the SDK source under `.venv/Lib/site-packages/noxus_sdk/`. It is
small and the answer is usually there. If still stuck, leave a TODO and
open an issue using the template — do not invent API shapes.
