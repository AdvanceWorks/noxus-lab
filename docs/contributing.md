# Contributing

Thanks for the interest. This is a small repo with strong opinions —
read [AGENTS.md](../AGENTS.md) once before you start.

## Bootstrap

    git clone https://github.com/AdvanceWorks/noxus-lab
    cd noxus-lab
    python -m venv .venv
    . .venv/Scripts/activate     # or `. .venv/bin/activate` on Unix
    pip install -e ".[dev]"
    pre-commit install
    cp .env.example .env         # set NOXUS_API_KEY for live tests

## Loop

    ruff check .                 # lint
    ruff format .                # format
    pytest                       # tests + coverage gate
    pyright                      # type-check (warning-only)

Tests are offline by default. Anything that talks to the live Noxus
backend must be marked `@pytest.mark.smoke` and skipped when
`NOXUS_API_KEY` is unset.

## Regenerating lock files

    pip install pip-tools
    pip-compile --generate-hashes -o requirements.lock pyproject.toml
    pip-compile --generate-hashes --extra=dev -o requirements-dev.lock pyproject.toml

Commit both `.lock` files together with the `pyproject.toml` change.

## PR checklist

- [ ] One topic per PR. Conventional Commit title (`feat:`, `fix:`,
      `chore:`, `docs:`, `refactor:`, `test:`, `ci:`).
- [ ] `ruff check .` and `pytest` clean locally.
- [ ] `CHANGELOG.md` updated under `## [Unreleased]`.
- [ ] Docs/README updated if user-facing.
- [ ] No `.env`, no API keys, no PII in diffs (gitleaks runs in CI).
