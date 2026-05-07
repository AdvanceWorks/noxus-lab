# Changelog

All notable changes to this project follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/AdvanceWorks/noxus-lab/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/AdvanceWorks/noxus-lab/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/AdvanceWorks/noxus-lab/releases/tag/v0.1.0
