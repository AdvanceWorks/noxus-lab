# {project_name}

A multi-workspace automation repository scaffolded by
`noxuslab init --multi-process` (template version `{version}`).

Each top-level folder is **one workspace on the Noxus platform = one
end-to-end process**. Inside each workspace folder live the labels,
classifier, workflows, agents, knowledge sources, fixtures, and tests
for that one process. Workspaces are independent; they never import
from each other.

The repo carries **no infrastructure code of its own** — the Azure
OpenAI client wrapper, the classification primitive, the test fixture
factory, and every CLI command live in
[`noxuslab`](https://github.com/AdvanceWorks/noxus-lab) and are
imported from there. New repos stay tiny by design.

## install

    python -m venv .venv && .venv\Scripts\activate     # Windows
    pip install -e ".[dev]"
    cp .env.example .env                                # then fill it in
    pytest

`.env` holds these secrets:

| Variable                  | Why                                  |
| ------------------------- | ------------------------------------ |
| `NOXUS_API_KEY`           | Talks to the Noxus platform          |
| `AZURE_OPENAI_API_KEY`    | Calls Azure OpenAI (GPT-4o)          |
| `AZURE_OPENAI_ENDPOINT`   | Your Azure OpenAI resource URL       |

## workspaces (one per process)

{workspaces_table}

## adding a workspace

See [docs/adding_a_workspace.md](docs/adding_a_workspace.md). The short version:

1. `noxuslab init --multi-process --workspace <new_name> .` (or `cp -r <existing> <new_name>`)
2. Replace the labels in `labels.py` and the prompt
3. Replace the fixtures under `test_fixtures/`
4. `pytest <new_name>` — green before commit
5. Add a row in this README, in `pyproject.toml` (`packages`, `--cov`, `testpaths`), and in `pyrightconfig.json` (`include`)

## verify

    ruff check . && ruff format --check .
    pyright
    pytest

CI mirrors the same on every push.
