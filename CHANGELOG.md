# Changelog

All notable changes to this project follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
  language and name-dropping. `tests/test_godlike.py` renamed to
  `tests/test_features.py`.

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

[Unreleased]: https://github.com/AdvanceWorks/noxus-lab/compare/v0.7.1...HEAD
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
