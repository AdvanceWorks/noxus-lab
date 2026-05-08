# Contributing

See [docs/contributing.md](../docs/contributing.md) for the full
guide: setup, branching, commit style, lint/test workflow, and PR
checklist.

TL;DR:

```sh
make setup
make lint && make test
git switch -c feat/<short>
# ...code...
git commit -m "feat(scope): one-line summary"
git push -u origin HEAD
# open PR
```

Conventional Commits required. CHANGELOG must be updated for every
behaviour change. See [AGENTS.md](../AGENTS.md) for the full contract.
