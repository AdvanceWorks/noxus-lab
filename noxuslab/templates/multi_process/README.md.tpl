# {project_name}

A multi-process automation repository built on top of
[`noxuslab`](https://github.com/AdvanceWorks/noxus-lab) and the
Noxus AI platform.

Each automation lives as an isolated module under
[processes/](processes/). Cross-cutting helpers live in
[shared/](shared/). One repo, one CI, one place to review.

Scaffolded by `noxuslab init --multi-process` (template version `{version}`).

## install

    python -m venv .venv && .venv\Scripts\activate     # Windows
    pip install -e ".[dev]"
    pip install --upgrade git+https://github.com/AdvanceWorks/noxus-lab.git
    cp .env.example .env                                # then fill it in
    pytest

`noxuslab` is the CLI used to push Noxus workflows from this repo to
the platform; it is installed separately from git so the runtime
dependencies of this project stay independent of the tool's release
cadence.

`.env` holds these secrets:

| Variable                  | Why                                  |
| ------------------------- | ------------------------------------ |
| `NOXUS_API_KEY`           | Talks to the Noxus platform          |
| `AZURE_OPENAI_API_KEY`    | Calls Azure OpenAI (GPT-4o)          |
| `AZURE_OPENAI_ENDPOINT`   | Your Azure OpenAI resource URL       |
| `AZURE_OPENAI_DEPLOYMENT` | The deployment name (model alias)    |

## processes

| Folder                                                        | Order | What it does                                              |
| ------------------------------------------------------------- | ----- | --------------------------------------------------------- |
| [processes/support_routing/](processes/support_routing/)      | 01    | Classify inbound support emails into 5 routing categories |
| _(more to follow)_                                            |       |                                                           |

Folder names are plain Python identifiers (no leading digits) so they
import cleanly. The presentation order lives in the table above.

## shared

| Module                                              | Responsibility                                       |
| --------------------------------------------------- | ---------------------------------------------------- |
| [shared/azure_openai.py](shared/azure_openai.py)    | Thin client wrapper, returns `(label, logprob)`      |
| [shared/classification.py](shared/classification.py) | Threshold logic + label schema dataclasses           |

If a helper appears twice across `processes/`, it gets promoted into
`shared/`. Same rule `noxus-lab` applies between examples and the
package.

## how to add a process

See [docs/adding_a_process.md](docs/adding_a_process.md). The short
version:

1. `cp -r processes/support_routing processes/<short_name>`
2. Edit the local `README.md` with the process context
3. Replace the label set, sample data, and prompt
4. `pytest processes/<short_name>` — green before commit
5. Add a row to the `processes` table above with the order column

## verify

    ruff check . && ruff format --check .
    pyright
    pytest

CI mirrors the same on every push.
