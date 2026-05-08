# AGENTS.md — operating contract for AI assistants and contributors

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
- **Lint and test clean.** `make lint` and `make test` must pass
  locally before every commit. CI enforces both on three OSes ×
  three Python versions.
- **Coverage gate ≥ 70%.** `pytest --cov-fail-under=70` is wired into
  the test command. New modules ship with at least one offline test.
- **Don't add a dependency without need.** Justify in the PR. Pin
  exactly one version of `noxus-sdk`. Prefer stdlib over a 50 kB wheel.
- **Update `CHANGELOG.md` on every change.** Append under
  `## [Unreleased]`. Sections: `### Added`, `### Changed`, `### Fixed`,
  `### Removed`. No exceptions for "small" changes.
- **No Docker.** This is a Python CLI; `pip install` and `make setup`
  cover all targets. A Dockerfile would be a DX regression.

## Style

- **Examples**: shebang, 1-line docstring with the invocation, top-level
  script, `print` for output. Target ≤ 80 lines.
- **Package code**: explicit imports, type hints on public APIs,
  validate at boundaries only, no defensive `try/except` for cases that
  cannot happen.
- **Naming**: `snake_case` files, `PascalCase` classes, lowercase
  example prefixes (`NN_short_name.py`).
- **Neutral tone.** Do not pitch ideas by name-dropping famous people
  or with marketing words like "godlike". Describe what the change
  does and why it matters.

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

Three good entry points:

1. **Add an example.** Pick the next free `NN_` prefix under
   `examples/`. Mirror the style of existing scripts. If your idea
   needs a helper that other scripts could share, promote it to
   `noxuslab/`.
2. **Improve the codegen.** `noxuslab.codegen.workflow_to_python`
   produces Python from a `WorkflowDefinition`. Edge cases live in
   `tests/test_codegen.py`. Add a failing test before changing the
   generator.
3. **Add a CLI subcommand.** `noxuslab` lives in `noxuslab/cli.py`.
   New subcommands add one parser branch + one `cmd_<name>` function.
   Keep side-effects out of import time — lazy-import heavy deps
   inside the function.

For deeper changes (new SDK abstraction, new package under
`noxuslab/`), open an issue first.

## AI assistants — operating procedure

Treat this as a checklist for every non-trivial change.

### 1. Plan before touching code

- Read the file you intend to change before editing it.
- For multi-step work, write the plan as a TODO list and update it as
  you go. Single-step edits do not need ceremony.
- Pick the smallest scope that satisfies the request. Out-of-scope
  refactors live in their own commit.

### 2. Use subagents for delegated work

Three subagents live under [.github/agents/](.github/agents/). Each
has a single, narrow job:

- **[Explore](.github/agents/Explore.agent.md)** — read-only research.
  Spawn when you need to read > 5 files or grep widely. Returns one
  scannable message with `[path](path#L12)` citations. Safe in parallel.
- **[Refactor](.github/agents/Refactor.agent.md)** — focused mechanical
  changes (rename, extract, drop dead code). Lists every call site
  before editing. Verifies lint+tests after.
- **[Release](.github/agents/Release.agent.md)** — cut a new version.
  Bumps the three version files, updates the changelog, runs the full
  verify pipeline, commits with Conventional Commits, tags, pushes.

Rules of engagement:

- Each subagent is **stateless** — pass full context in the prompt.
- Run independent subagents **in parallel** when possible.
- Do **not** ask `Explore` to write code; spawn `Refactor` for that.
- Pick thoroughness on purpose for `Explore`: `quick` (one fact,
  ≤5 reads), `medium` (feature audit, ≤20 reads), `thorough` (design
  question, no cap but stay focused).

### 3. Edit with intent

- Prefer `multi_replace_string_in_file` when changing several files
  in the same logical step.
- Always include 3–5 lines of context above and below the edit anchor.
- After editing, run `ruff check . && ruff format . && pytest -q` and
  fix issues immediately. Do not chase a broken build with more edits.

### 4. Verify before claiming done

A change is done only when:

1. `make lint` is green.
2. `make test` is green and coverage ≥ 70%.
3. `make typecheck` (pyright) is green.
4. `CHANGELOG.md` is updated.
5. The Conventional Commit message is written.
6. The user-visible behaviour was exercised at least once
   (`python -m noxuslab <subcommand> --help` for new CLI surface).

### 5. Commit + push

- Run `pre-commit run --all-files` (or trust the git hook).
- One commit per topic. Never use `--no-verify`.
- For releases, bump version in three places:
  `noxuslab/__init__.py`, `pyproject.toml`, the install snippet in
  `README.md`. Add a `[X.Y.Z]` heading + comparison link at the
  bottom of `CHANGELOG.md`. Tag `vX.Y.Z` and push the tag.

### 6. Memory hygiene

- `/memories/` is loaded into context on every turn — keep it terse.
- `/memories/preferences.md` records hard user preferences (what to
  avoid, output style). Read it before generating prose.
- Use `/memories/session/` for one-conversation scratch. Do not
  promote session notes to user memory unless the insight is durable.

### 7. When stuck

Read the SDK source under `.venv/Lib/site-packages/noxus_sdk/` — it is
small and the answer is usually there. If still stuck, leave a `TODO:`
in the code and open an issue. Do not invent API shapes.

## Out of scope

- Re-implementing the SDK or backend.
- Multi-tenant support — one API key per workspace, full stop.
- Auto-publishing or auto-deleting platform resources.
- Translating prose to PT/ES (English-only is a hard rule).
- Replacing the CLI with a GUI as the primary interface.
