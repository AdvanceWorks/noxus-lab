# Changelog

All notable changes to this project follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Removed
- **`NOXUSLAB_TOKEN` plumbing in the bundled `multi_process` CI
  template.** `noxus-lab` is now a public repository, so consumers can
  resolve `noxuslab @ git+https://...` anonymously. The gated git
  `insteadOf` step and the matching "CI note" paragraph were dropped
  from the template's `.github/workflows/ci.yml` and `README.md.tpl`.
  Repos already scaffolded keep working; the step was already a no-op
  without the secret.

## [0.12.0] - 2026-05-11

### Changed
- **BREAKING — `multi_process` template restructured: workspace = process.**
  The previous two-level `<workspace>/<process>/...` layout is replaced
  by a flat `<workspace>/...`. Each top-level folder is now one
  workspace on the Noxus platform AND one end-to-end automated
  process, owning its own labels, classifier, workflows, agents,
  knowledge sources, fixtures, and tests. This matches the platform's
  governance model (KBs, agents, secrets and audit trails are scoped
  per workspace) and lets each process have its own `CODEOWNERS`.
- **BREAKING — `noxuslab init --multi-process --workspace NAME`** no
  longer accepts the `NAME:PROCESS` syntax. Each `--workspace` flag
  creates one top-level package; the workspace name *is* the process
  name. Default value when `--workspace` is omitted is now
  `example_workspace` (was `agents:example_process`).
- **BREAKING — bundled template skeleton.** The two skeletons
  `_workspace_template/` and `_process_template/` were collapsed into
  one `_workspace_template/`. The `__process__` placeholder is gone;
  only `__workspace__` remains.
- **BREAKING — module import paths in scaffolded repos.** Imports
  changed from `<workspace>.<process>.classifier` to
  `<workspace>.classifier`. Workflow names changed from
  `<workspace>-<process>-classify` to `<workspace>-classify`.

### Added
- **`agents/` and `knowledge/` placeholder folders per workspace** in
  the multi-process template, each with a README explaining the
  intended usage. No code is generated there — the directories are
  reserved for the workspace's Noxus agents and KB source documents.
- **`docs/adding_a_workspace.md`** in the template (replaces
  `docs/adding_a_process.md`) with the new recipe and the build
  wiring checklist (`pyproject.toml`, `pyrightconfig.json`).
- **CLI validation**: `noxuslab init --multi-process --workspace`
  rejects names that are not valid Python identifiers and rejects
  duplicates with a clear error message.

## [0.11.1] - 2026-05-11

### Changed
- **Bundled `multi_process` CI template** rewritten to mirror this
  repo's `ci.yml`: triggers on `push` to `main` and on every
  `pull_request`, runs only `ruff check + ruff format --check + pytest`
  on a 3-job matrix (Linux 3.10, Linux 3.12, Windows 3.12). `pyright`
  is dropped from CI — it stays a local + pre-commit check, matching
  the noxus-lab repo itself.
- The CI template now configures git's `insteadOf` with an optional
  `NOXUSLAB_TOKEN` repo secret so `pip install -e ".[dev]"` can resolve
  the `noxuslab @ git+https://github.com/AdvanceWorks/noxus-lab.git@v...`
  pin while noxus-lab is a private repository. The step is a no-op
  when the secret is absent, so CI keeps working unchanged the day
  noxus-lab goes public.
- `noxus-lab`'s own `ci.yml` switched from `on: [push, pull_request]`
  (any branch) to `push: branches: [main] + pull_request:` for clean
  branch semantics.

## [0.11.0] - 2026-05-11

### Added
- **`noxuslab.classify`** — promoted the Azure OpenAI client wrapper
  and the classification primitive (`TokenScore`, `build_client`,
  `classify`, `ClassificationResult`, `decide`) out of the
  `multi_process` template and into the `noxuslab` package itself.
  Repos scaffolded by `noxuslab init` now `from noxuslab.classify
  import ...` instead of carrying their own `shared/` copy.
- **`noxuslab.testing.make_fake_azure_client`** — the test fixture
  factory (an `openai.AzureOpenAI` stand-in) is now also part of the
  package; the template's `conftest.py` is a one-liner that re-exports
  it as a pytest fixture.
- **`noxuslab init --multi-process --workspace NAME[:PROCESS]`** —
  repeatable flag that materialises one workspace folder per value
  (each workspace = one workspace on the Noxus platform). The default
  is `agents:example_process` to keep the zero-flag path working.
- **`noxuslab init` accepts a target dir that already contains
  `.git/` or `.env`** so an existing repo can be initialised in place
  without re-cloning.
- `openai>=1.40.0` is now a runtime dependency of `noxuslab`.

### Changed
- **`noxuslab init --multi-process` template** rewritten end-to-end:
  no `shared/`, no `processes/`. Instead, one folder per workspace
  (`<workspace>/<process>/`), each process imports its primitives
  from `noxuslab.classify`. Repos scaffolded with this command now
  carry **no infrastructure code of their own** — labels, prompts,
  fixtures and Noxus workflow definitions are the only user-written
  files. Generated `pyproject.toml` depends only on `noxuslab` (which
  pulls `noxus-sdk` and `openai` transitively).
- Generated `conftest.py`, `ruff.toml` and `pyrightconfig.json` are
  rewritten to match the new `<workspace>/<process>/` shape and the
  `test_fixtures/` (was `sample_data/`) convention.

### Changed
- **Examples** drop the redundant `base_url=os.environ.get("NOXUS_BACKEND_URL")`
  argument: the SDK `Client` already reads `NOXUS_BACKEND_URL` from the
  environment, so passing it explicitly was both a duplication and a
  type-checker error (`str | None` vs `str`). All eight scripts now
  construct the client with a single line.
- **`examples/04_agent.py`** updated to the current `WorkflowTool` SDK
  signature (`workflow_id=...`); the legacy `workflow={...}, name=...,
  description=...` arguments were removed in a recent SDK release.
- **`examples/08_chat.py`** renders `ChatMessage.parts` (the actual SDK
  shape) instead of a non-existent `.content` attribute.
- **`noxuslab --help`** description shortened and an epilog added so the
  top-level help reads cleanly when run without a subcommand.
- **`_load_agent_file`** now returns `Any` for the settings field instead
  of `object`; the call sites (`agents.update` / `agents.create`) accept
  the live `ConversationSettings` instance produced by the file without
  an explicit cast. Removes two pyright errors.

### Fixed
- **`pyright`**: 22 type errors → 0. The drift between the SDK type
  signatures and the example/CLI surface is fully resolved.
- **`tests/test_fmt_portal.py`** uses `# type: ignore[assignment]` on the
  fake handler's `headers` attribute (the real `BaseHTTPRequestHandler`
  declares it as `Message[str, str]`, which we deliberately bypass).

## [0.10.0] — 2026-05-08

### Added
- **`noxuslab/_workflow.py` — the `LocalWorkflow` primitive.** One
  module owns reading a workflow `.py` file, extracting its provenance
  id, and executing it in a sandboxed namespace with the SDK `Client`
  stubbed. Replaces five hand-rolled copies of the same logic in
  `cli.cmd_push`, `cli.cmd_diff --visual`, `cli._load_agent_file`,
  `fmt.py`, and `runner.py`. New callers (replay, eval, future
  features) are now one line each.
- **`noxuslab replay <run-id>`** — re-runs a workflow using the
  inputs captured in a previous trace. Foundation for upcoming eval /
  regression commands; produces a fresh trace that can be diffed
  against the original. Optional `--target` swaps the workflow but
  keeps the inputs (useful for running a refactored local file against
  the same data the server saw).
- **AGENTS.md “Platform Primitives” rule.** Codifies that new features
  must extract or reuse a primitive in `noxuslab/_*.py` rather than
  ship as a one-off helper.

### Changed
- **`noxuslab fmt`** uses `LocalWorkflow` for parsing + provenance
  extraction — net loss of ~50 lines and the duplicated
  `_StubClient`. Behaviour identical.
- **`noxuslab run` / `runner._load_or_push`** uses `LocalWorkflow` and
  `_workflow.is_uuid`. The error message for a missing target file
  changed from `not a UUID and not a file: <x>` to `not found: <x>`
  (still raises `BadFile`).
- **`noxuslab.cli`** drops its private `_UUID` regex and inline
  `_extract_source_id` in favour of `_workflow.check_uuid` /
  `extract_source_id`. Public CLI surface unchanged.

## [0.9.1] — 2026-05-08

### Added
- **`noxuslab check <file>`** — pre-commit / pre-PR review gate.
  Bundles three local checks (dry-run push, diff vs server, last
  local trace summary) into one command. Exit 0 means safe to
  commit/push. The workflow id is auto-extracted from the file's
  provenance header — no UUID needed at the command line.
- **README "review loop"** section documenting the recommended
  pull → run → trace → check → commit → PR → push workflow.

### Changed
- **`noxuslab diff`** now accepts the file alone when it has a
  provenance header (`# generated by noxuslab pull from <id> @ ...`).
  Explicit `noxuslab diff <id> <file>` continues to work.

## [0.9.0] — 2026-05-08

### Removed
- **`Makefile` and `bin/` wrappers** at the repo root. The `noxuslab`
  CLI is now the single, canonical interface — every former `make`
  target maps directly to a `noxuslab` subcommand. See the cheat
  sheet in [README](README.md).
- **`noxuslab init --with-makefile`** flag (and its `Makefile`/`bin/`
  copies). New scaffolds are CLI-only, matching the published
  philosophy.
- **`docs/quickstart.md`, `docs/for-users.md`, `docs/for-builders.md`,
  `docs/philosophy.md`, `docs/publish.md`, `docs/security.md`** —
  collapsed into [README.md](README.md), [docs/cli.md](docs/cli.md),
  [docs/contributing.md](docs/contributing.md), and root
  [SECURITY.md](SECURITY.md). One page per concept, no overlap.

### Changed
- **README** is now ~80 lines and tells one story: install, init, one
  cheat-sheet table, links to deeper docs.
- **`docs/cli.md`** is the canonical command reference (init, doctor,
  pull/push/diff, run/trace/env, list/show, agents, chat/ask, gen,
  watch, fmt, portal, mcp, version) — each command in one place,
  no duplication with the README.
- **`docs/contributing.md`** describes the inner loop in three plain
  commands (`pip install -e ".[dev]"`, `ruff check .`,
  `pytest`) and includes the lock-file regeneration recipe inline.
- **`AGENTS.md`** updated: hard rule is now "`ruff check .` and
  `pytest` must pass"; the workflow snippet uses the CLI directly
  instead of `make`. New rule: "No Docker, no Make."
- **`.pre-commit-config.yaml`** drops the pre-push pytest hook (it
  relied on `sh bin/test`); contributors run `pytest` before pushing
  and CI is the source of truth.
- **`.editorconfig`** drops the `[Makefile]` indent override.

## [0.8.1] — 2026-05-08

### Changed
- **`noxuslab init` is now the canonical new-project path** in the docs.
  The GitHub repo is framed as the source for the CLI/examples rather
  than the default app scaffold for end users.

### Fixed
- **Scaffold README now matches the scaffold mode** — plain `noxuslab
  init` no longer tells users to run `make setup`/`make help` when
  those files were not copied. `--with-makefile` keeps the Make-based
  instructions. The generated README also documents how to upgrade the
  installed CLI later with `pip install --upgrade ...`.

## [0.8.0] — 2026-05-08

### Added
- **`noxuslab run <target> --input k=v`** — execute a workflow and
  stream live events. `<target>` is either a server-side workflow UUID
  or a local Python file (auto-saved before run). Inputs are
  JSON-decoded when possible; prefix a value with `@` to load JSON
  from a file. `--detach` triggers and exits.
- **JSONL trace recorder** (`noxuslab._trace`) — every `run` writes
  one JSONL file under `.noxuslab/traces/<utc>_<run_id>.jsonl`.
  Header + per-event lines + footer; flushed per line so it is
  tail-able from another terminal. Secret-shaped keys (`api_key`,
  `token`, `password`, ...) are redacted before being written.
- **`noxuslab trace [list|show]`** — inspect recorded runs. `list`
  shows newest first with status + elapsed. `show <id>` renders a
  timeline (relative timestamps, node names, status footer). `--json`
  emits the raw JSONL entries.
- **`noxuslab env [list|use]`** — switch between `.env.dev`,
  `.env.staging`, `.env.prod`, etc. The chosen file is copied to
  `.env` (works on Windows without admin); active name recorded in
  `.noxuslab/active-env`.
- **`noxuslab doctor`** — green/red checks for Python version,
  `noxuslab`/`noxus_sdk` install, `NOXUS_API_KEY` resolution, backend
  reachability, trace dir writability, and active env. Exit code 0
  on full pass, 1 on any hard failure.
- New modules: `noxuslab.runner`, `noxuslab._trace`,
  `noxuslab.trace_view`, `noxuslab.envs`, `noxuslab.doctor`.
- Tests: `tests/test_run_trace_env_doctor.py` covers trace I/O and
  redaction, input parsing (`k=v`, JSON, `@file`), env switching,
  doctor pass/fail, runner UUID dispatch, and CLI handler wiring.

## [0.7.1] — 2026-05-08

### Fixed
- **Python 3.10 CI** — `agent_codegen` used `from datetime import UTC`,
  which is 3.11+. Switched to `timezone.utc` to match the rest of the
  codebase.

### Changed
- **CI matrix trimmed** from 9 jobs to 4: ubuntu × {3.10, 3.12},
  macos × 3.12, windows × 3.12. Covers every supported OS plus the
  min/max Python boundary; mid-version (3.11) is dropped because the
  syntax/semantics range is bracketed by 3.10 and 3.12. Add it back if
  a 3.11-only bug appears.
- **Subagents split into dedicated files** under
  [.github/agents/](.github/agents/): `Explore.agent.md` (read-only
  research), `Refactor.agent.md` (mechanical changes), and
  `Release.agent.md` (version bump + tag + push). AGENTS.md now points
  to them with one-line summaries instead of inlining the full
  procedure.

## [0.7.0] — 2026-05-08

### Added
- **`noxuslab agents pull|push|diff|delete`** — full CRUD for Noxus
  agents, mirroring the workflow toolkit:
  - `agents pull <id>` writes a self-contained Python file under
    `agents/NN_<slug>.py` (override with `-o`, `-` for stdout). The
    file carries a provenance header and serialises
    `ConversationSettings` as JSON for diff-friendly round-tripping.
  - `agents push <file>` runs the file with the SDK `Client` stubbed
    (no network), reads `agent_name` / `agent_settings` /
    optional `agent_id`, and calls update or create accordingly.
    `--dry-run` validates without saving.
  - `agents diff <id> <file>` exit 0 if identical, 1 otherwise.
  - `agents delete <id> --yes` (refuses without `--yes` — destructive).
- New module `noxuslab.agent_codegen` with `agent_to_python(agent,
  source_id=...)`.
- Tests: `tests/test_agents.py` covers codegen, round-trip load,
  guard rails (missing `agent_name`/`agent_settings`/path),
  default-path pull, and delete confirmation.

### Changed
- Bare `noxuslab agents` keeps its original meaning (list agents) but
  is now a parser group exposing `list`, `pull`, `push`, `diff`,
  `delete`.

## [0.6.0] — 2026-05-08

### Added
- **`noxuslab fmt <file>...`** — format-in-place for workflow files.
  Same renderer as `pull`, but loads each file with the SDK `Client`
  stubbed (no network), regenerates the canonical Python, and rewrites
  the file. Flags: `--check` (exit 1 if any file would change) and
  `--diff` (preview without writing). The workflow analogue of
  `ruff format`.
- **`noxuslab portal`** — read-only HTML dashboard at
  `http://127.0.0.1:7890`. Lists workflows and agents with one-click
  copy-to-clipboard for ids. Built on the stdlib `http.server`, no
  extra dependency. Refuses to bind on non-loopback hosts. Auto-opens
  the default browser unless `--no-open`.
- Tests: `tests/test_fmt_portal.py` covers fmt idempotence/check/diff
  and portal HTML rendering, handler routing, and loopback rejection.

### Changed
- **AGENTS.md rewritten** as an operating contract for both humans and
  AI assistants. New sections: hard rules, neutral-tone clause in
  style, AI assistants operating procedure (plan → subagents →
  edit → verify → commit → memory hygiene → when stuck).
- Documentation, tests, and changelog scrubbed of motivational
  language and name-dropping. The legacy showcase test module was
  renamed to `tests/test_features.py`.

## [0.5.0] — 2026-05-08

### Added
- **`noxuslab watch <file>`** — hot-push on every save. Polls the
  file's mtime in a stdlib loop (no `watchdog` dep). First push happens
  immediately; subsequent saves push in <1s with a timestamp +
  elapsed-ms confirmation. Ctrl+C to stop.
- **`noxuslab gen "<prompt>"`** — generate a workflow Python file from
  a natural-language description. Wraps a Noxus conversation with a
  strict system prompt, strips markdown fences, writes to
  `examples/NN_<slug>.py` (or `--out`). Output is ready for
  `noxuslab push <file>`.
- **`noxuslab init --interactive`** — first-run wizard. Auto-detects
  TTY; prompts for API key (hidden via `getpass`) and optional backend
  URL; writes `.env` with `chmod 600`. Use `--no-interactive` for
  unattended scaffolding.
- **`noxuslab diff --visual`** — side-by-side Mermaid graphs for
  server vs local workflow. Paste into any Mermaid renderer (GitHub,
  mermaid.live, VS Code) for a visual review. New module
  `noxuslab.graph` with `to_mermaid()` helper.
- **HTTPS audit sinks** — `NOXUSLAB_AUDIT_LOG` now accepts `https://`
  URLs. Slack-style hooks (`hooks.slack.com`) get a `{"text": ...}`
  wrapper; other URLs receive the raw JSON record. Best-effort, 1s
  timeout, silent on failure. File sinks unchanged.
- `noxuslab gen` is added to the audit redaction set (free-form prompts
  never logged).
- Tests: `tests/test_features.py` covers `gen`, `graph`, audit sinks,
  and `watch` boundary conditions. Coverage 71%.

## [0.4.0] — 2026-05-08

### Added
- **`noxuslab mcp serve`** — run noxuslab as an MCP server. Plug into
  Claude Desktop, Cursor, or VS Code Copilot and ask the LLM
  *"list my noxus workflows"*, *"pull workflow abc-123 to a file"*,
  *"diff this file against the server"*, *"ask my agent about X"*.
  Five high-level tools: `list_workflows`, `list_agents`,
  `pull_workflow`, `diff_workflow`, `ask_agent`. All go through the
  same retry / audit / secrets layers as the CLI.
- `noxuslab/mcp.py` module + `tests/test_mcp.py` (4 offline tests).
- `docs/mcp.md` rewritten to compare `noxuslab mcp serve` (5 high-level
  tools, day-to-day) vs `noxus mcp serve` (~39 raw SDK tools, power
  users), with Claude / Cursor / VS Code config snippets.
- `mcp>=1.0` added to `[dev]` extras so tests can import it.

## [0.3.2] — 2026-05-08

### Added
- `SECURITY.md` and `.github/CONTRIBUTING.md` so GitHub auto-surfaces
  the security policy and contributing guide.
- Python 3.11 in the CI matrix (now ubuntu/macos/windows × 3.10/3.11/3.12 = 9 jobs).
- Optional production env vars documented in `.env.example`:
  `NOXUSLAB_SECRETS_CMD`, `NOXUSLAB_AUDIT_LOG`, `NOXUSLAB_AUDIT`,
  `NOXUSLAB_MAX_RETRIES`, `NOXUSLAB_BASE_DELAY`, `NOXUSLAB_MAX_DELAY`.
- Tests for `cmd_diff`, `cmd_show`, `cmd_push --dry-run`,
  `cmd_init --with-makefile`, audit-to-stderr, `time_ms`, and
  version consistency between `pyproject.toml` and `__init__.py`.
  Coverage 73% → **81%**.
- `docs/cli.md` complete reference for `chat`, `ask`, `agents`,
  `diff`, and the `init --with-makefile` flag.

### Changed
- `.env.example` now seeds `NOXUS_API_KEY=your_key_here` (was empty)
  to match the quickstart guide.
- `examples/03_kb.py` sample text replaced with a generic fictional
  company (was internal CTT operational content).
- `docs/security.md`: corrected statement about `noxuslab push` —
  uses `runpy.run_path`, not `exec`.
- `docs/philosophy.md` and `noxuslab/__init__.py` docstring updated
  to list all current CLI commands (was stale "four-command CLI").
- README builder quickstart row now shows `make push FILE=...`.
- `_audit.py` log file open uses `errors="replace"` so encoding edge
  cases degrade gracefully instead of raising.

### Removed
- `NoxusLabError.NotFound` — was defined but never raised anywhere.
- `noxuslab._term.yellow` — was defined but never used outside its
  own test.

### Fixed
- Unknown subcommand no longer prints two error messages — the
  "did you mean" hint exits with code 2 directly, suppressing
  argparse's generic "invalid choice" follow-up.
- Removed duplicate `import difflib` in `cmd_diff`.

## [0.3.1] — 2026-05-08

### Added
- `docs/quickstart.md` — zero-assumption setup guide for non-technical
  users (Windows + Mac). Covers tool install, template setup, API key,
  and when to use `make` vs the `noxuslab` CLI directly.

### Changed
- README: dropped broken PyPI badge; install instructions now use
  `pip install git+https://...@v0.3.1` until the project is registered
  on PyPI.
- `release.yml`: GitHub-release-only (no PyPI step). Removed the
  duplicate `publish.yml` workflow.

## [0.3.0] — 2026-05-08

### Added
- Structured audit log — set `NOXUSLAB_AUDIT_LOG=/path/to/audit.log`
  (or `NOXUSLAB_AUDIT=stderr`) and every CLI invocation emits a JSON
  line with ts, user, host, cmd, rc, duration_ms. Free-form arguments
  to `chat` and `ask` are redacted (count only, never content). Ready
  for SIEM ingestion (Splunk / Datadog / ELK).
- `NOXUSLAB_SECRETS_CMD` — pluggable secret resolver. Set it to a
  shell command (e.g. `aws secretsmanager get-secret-value --query
  SecretString --output text --secret-id ...`) and `noxuslab` will
  fetch the API key on demand. Production deployments need not write
  the key to disk.
- `noxuslab._secrets.resolve_api_key()` — env > .env > command, with
  typed errors. Used by both `cli.py` and `chat.py`.
- `noxuslab diff <workflow_id> <file>` — unified diff between the
  server's current canonical Python and a local file. Exit 0 on
  identical, exit 1 on differences. `make diff ID=... FILE=...` wraps
  it. Useful before `push` to see exactly what would change.
- `requirements.lock` and `requirements-dev.lock` — fully pinned with
  hashes, generated by `pip-compile --generate-hashes`. Use
  `LOCKED=1 sh bin/setup` (or in CI) to install hash-verified versions
  for reproducible builds.
- `bin/lock` and `make lock` — regenerate locks after editing
  dependencies in `pyproject.toml`.
- `noxuslab._net.call()` wrapper around all Noxus API calls: retries
  transient failures (5xx, 429, timeouts) with exponential backoff +
  jitter. Tunable via `NOXUSLAB_MAX_RETRIES`, `NOXUSLAB_BASE_DELAY`,
  `NOXUSLAB_MAX_DELAY` env vars.
- `NetworkError` and `RateLimited` typed exceptions.
- `noxuslab chat [--agent <id>] [--model <name>]` — interactive
  conversation REPL with SSE-streamed responses. `/exit`, `/clear`
  built-ins.
- `noxuslab ask <question> [--agent <id>]` — one-shot, pipe-friendly.
- `noxuslab agents` — list agents in the workspace.
- `noxuslab init --with-makefile` — full project scaffold including
  Makefile, `bin/`, and a `.noxuslab-template-version` marker.
- `make chat`, `make ask`, `make list`, `make agents`, `make new`,
  `make template-update` targets. `make help` is now grouped by
  audience (use / browse / sync / dev).
- `examples/08_chat.py` — programmatic conversation creation.
- `docs/for-users.md` and `docs/for-builders.md` — dual-audience guides.
- `.github/workflows/dependabot-automerge.yml` — auto-approve + squash
  grouped dependabot PRs after CI passes.
- `tests/test_chat.py` — 6 tests covering chat REPL behaviour (mocked).

### Changed
- CI matrix: install from pyproject.toml (not lockfile) so all Python
  versions resolve their own backport deps. Lock stays for local dev
  reproducibility. Fixes 3.10 CI failures.
- CI matrix expanded from 2 jobs (Ubuntu × Py 3.10/3.12) to 6
  (Ubuntu + macOS + Windows × Py 3.10/3.12).
- README: dual-audience quickstart table + chat/ask in the run section.
- AGENTS.md: hard rule that every behaviour change updates CHANGELOG;
  Docker explicitly out of scope.
- Codegen now emits a `# noxuslab: dropped <N> non-renderable config
  key(s): ...` comment instead of silently skipping invalid kwargs.

### Fixed
- Codegen: Python keywords (`if`, `for`, etc.) used as config keys are
  no longer rendered as invalid kwargs (`SyntaxError`). They are
  reported in the dropped-keys comment.

## [0.2.0] — 2026-05-07

### Added
- `noxuslab init <dir>` scaffolds a new project from this template.
- `noxuslab list` and `noxuslab show <id>` for workspace introspection.
- `noxuslab pull -o -` writes generated code to stdout (pipe-friendly).
- `noxuslab pull --force` overwrites existing files.
- `noxuslab push --dry-run` validates without saving.
- Global `--version` / `-V` flag.
- `python -m noxuslab` works as an alternative to the console script.
- "Did you mean" suggestion on unknown subcommand.
- `noxuslab._term` ANSI helper (NO_COLOR-aware, stdlib only).
- `noxuslab.errors` module with typed exceptions.
- Codegen emits provenance header (source id + UTC stamp).
- Codegen output is now deterministic (sorted edges).
- Hypothesis property tests for codegen.
- pytest coverage gate (≥ 70%).

### Changed
- `cmd_push` uses `runpy.run_path` instead of `exec(compile(...))`.
- CI trimmed from 11 jobs to 2 (Ubuntu × Py 3.10/3.12).
- Single source of dependencies in `pyproject.toml`
  (`requirements.txt` and `requirements-dev.txt` removed).
- `SECURITY.md` and `CONTRIBUTING.md` moved under `docs/`.

### Fixed
- Codegen no longer emits invalid Python for non-identifier config keys.

## [0.1.0] — 2026-05-06

### Added
- Initial `noxuslab` package: `codegen` and `cli` (pull / push / version).
- Examples 01–07 covering build, run, KB, agent, async, introspect, pull demo.
- CI, pre-commit, ruff strict, pyright config.

[Unreleased]: https://github.com/AdvanceWorks/noxus-lab/compare/v0.8.1...HEAD
[0.8.1]: https://github.com/AdvanceWorks/noxus-lab/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/AdvanceWorks/noxus-lab/compare/v0.7.1...v0.8.0
[0.7.1]: https://github.com/AdvanceWorks/noxus-lab/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/AdvanceWorks/noxus-lab/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/AdvanceWorks/noxus-lab/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/AdvanceWorks/noxus-lab/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/AdvanceWorks/noxus-lab/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/AdvanceWorks/noxus-lab/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/AdvanceWorks/noxus-lab/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/AdvanceWorks/noxus-lab/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/AdvanceWorks/noxus-lab/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/AdvanceWorks/noxus-lab/releases/tag/v0.1.0
