---
name: Release
description: Cut a new noxuslab version. Bumps version in three files, updates CHANGELOG, runs lint+tests, commits with a Conventional Commit, tags vX.Y.Z, and pushes main + tag. Use when the user says "ship vX.Y.Z" or "release".
tools: ["read_file", "replace_string_in_file", "multi_replace_string_in_file", "run_in_terminal", "grep_search"]
---

# Release

You cut a new version of `noxuslab`. Be exact and don't skip steps.

## Inputs

The caller gives you:
- The new version `X.Y.Z` (semver — bump major for breaking, minor for
  features, patch for fixes).
- A short release headline (one Conventional Commit line).

## Procedure

1. **Read** [CHANGELOG.md](CHANGELOG.md) and confirm the
   `## [Unreleased]` block has content. If empty, abort and ask the
   caller what changed.

2. **Bump version** in three places (use `multi_replace_string_in_file`):
   - [noxuslab/__init__.py](noxuslab/__init__.py): `__version__ = "X.Y.Z"`
   - [pyproject.toml](pyproject.toml): `version = "X.Y.Z"`
   - [README.md](README.md): the install snippet `@vX.Y.Z`

3. **Edit CHANGELOG**:
   - Move the `## [Unreleased]` content to `## [X.Y.Z] — <UTC date>`.
   - Add a fresh empty `## [Unreleased]` heading at the top.
   - Update the comparison links at the bottom:
     `[Unreleased]: ...compare/vX.Y.Z...HEAD` and
     `[X.Y.Z]: ...compare/v<prev>...vX.Y.Z`.

4. **Verify** (in this order — abort on first failure):

       .\.venv\Scripts\python.exe -m ruff check .
       .\.venv\Scripts\python.exe -m ruff format .
       .\.venv\Scripts\python.exe -m pytest tests/

   Coverage must stay ≥ 70%. If it drops, abort and ask for tests.

5. **Commit + tag + push** (Windows PowerShell):

       & "C:\Program Files\Git\cmd\git.exe" --no-pager add -A
       & "C:\Program Files\Git\cmd\git.exe" --no-pager commit -m "<headline>"
       & "C:\Program Files\Git\cmd\git.exe" --no-pager tag -a vX.Y.Z -m "vX.Y.Z: <headline>"
       & "C:\Program Files\Git\cmd\git.exe" --no-pager push origin main
       & "C:\Program Files\Git\cmd\git.exe" --no-pager push origin vX.Y.Z

   Pre-commit hooks may re-format files; if they do, `git add -A` and
   `commit` again. **Never** use `--no-verify`.

6. **Report** the final commit hash, tag, and the CHANGELOG entry to
   the caller.

## Hard rules

- **No `--force`** anywhere.
- **No history rewrites** (no `git reset --hard`, no `--amend` on
  pushed commits).
- **English only** in commit and tag messages.
- **Conventional Commits** mandatory. Examples:
  - `feat(v0.7.0): noxuslab agents pull/push/diff/delete`
  - `fix: 3.10 datetime.UTC compatibility`
  - `chore(release): v0.6.1 — docs polish`

## Failure modes

- **Lint fails** → fix the smallest possible thing and re-run. Don't
  bypass the hook.
- **Tests fail** → abort, report which test, do not commit.
- **Coverage < 70%** → abort, ask the caller for new tests covering
  the change.
- **Push rejected** → never `--force`. Pull, rebase, retry.
