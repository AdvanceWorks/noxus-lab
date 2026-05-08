# Contributing

See [docs/contributing.md](../docs/contributing.md) for the full
guide. TL;DR:

```sh
pip install -e ".[dev]"
ruff check . && ruff format .
pytest
git switch -c feat/<short>
# ...code...
git commit -m "feat(scope): one-line summary"
git push -u origin HEAD
# open PR
```
