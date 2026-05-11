# {project_name}

A multi-workspace automation repository scaffolded by
`noxuslab init --multi-process` (template version `{version}`).

Every "workspace" folder corresponds to one workspace on the Noxus
platform. Inside each workspace, every "process" folder is one
end-to-end automation (a label set, a Python classifier, one or more
Noxus workflow definitions, fixture data, and tests).

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

> **CI note.** While `noxus-lab` is a private repo, the `pip install`
> step in CI needs to clone it. Add a fine-grained PAT with
> `Contents: Read` on `AdvanceWorks/noxus-lab` as a `NOXUSLAB_TOKEN`
> repository secret. Locally nothing is needed — your usual git
> credentials are reused.

`.env` holds these secrets:

| Variable                  | Why                                  |
| ------------------------- | ------------------------------------ |
| `NOXUS_API_KEY`           | Talks to the Noxus platform          |
| `AZURE_OPENAI_API_KEY`    | Calls Azure OpenAI (GPT-4o)          |
| `AZURE_OPENAI_ENDPOINT`   | Your Azure OpenAI resource URL       |

## workspaces

{workspaces_table}

## adding a process to a workspace

See [docs/adding_a_process.md](docs/adding_a_process.md). The short version:

1. `cp -r <workspace>/<existing_process> <workspace>/<new_process>`
2. Replace the labels in `labels.py` and the prompt
3. Replace the fixtures under `test_fixtures/`
4. `pytest <workspace>/<new_process>` — green before commit
5. Add a row in this README

## verify

    ruff check . && ruff format --check .
    pyright
    pytest

CI mirrors the same on every push.
