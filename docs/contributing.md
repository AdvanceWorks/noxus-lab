# Contributing

Thanks for the interest. This is a small repo with strong opinions —
read [AGENTS.md](../AGENTS.md) once before you start.

## Bootstrap

    git clone https://github.com/AdvanceWorks/noxus-lab
    cd noxus-lab
    make setup
    cp .env.example .env && $EDITOR .env   # set NOXUS_API_KEY
    pre-commit install

## Loop

    make lint        # ruff
    make test        # pytest
    make typecheck   # pyright (warning-only)

Tests are offline by default. Anything that talks to the live Noxus
backend must be marked `@pytest.mark.smoke` and skipped when
`NOXUS_API_KEY` is unset.

## PR checklist

- [ ] One topic per PR. Conventional Commit title (`feat:`, `fix:`, etc).
- [ ] `make lint && make test` clean locally.
- [ ] Docs/README updated if user-facing.
- [ ] No `.env`, no API keys, no PII in diffs (gitleaks runs in CI).

## Releases

Tag `vMAJOR.MINOR.PATCH` from `main`. The release workflow
([release.yml](../.github/workflows/release.yml)) builds the wheel and
opens a GitHub release with auto-generated notes. Bump
`pyproject.toml` and `noxuslab/__init__.py` in the same commit.

## Communication

- Bug or unexpected behaviour: open an issue with the *Bug* template.
- Feature idea: open an issue with the *Feature* template before coding.
- Security: email **luis.tunes@advanceworks.ai** — see [security.md](security.md).
