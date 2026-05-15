# AGENTS.md — operating contract for `{project_name}`

This file is the contract every contributor (human or LLM) follows
when touching the repo. Read it once. It is short on purpose.

This repo was scaffolded from the
[`noxus-lab`](https://github.com/AdvanceWorks/noxus-lab) multi-process
template (version `{version}`). For the broader Noxus development
philosophy, read the lab's
[AGENTS.md](https://github.com/AdvanceWorks/noxus-lab/blob/main/AGENTS.md);
this file records only what is specific to `{project_name}`.

## Shape

One top-level folder = one workspace on the Noxus platform = one
end-to-end process. Inside each workspace folder live the labels,
classifier, workflows, agents, knowledge sources, fixtures, and tests
for that one process. Workspaces are independent; they never import
from each other.

Workspaces in this repo:

{workspaces_table}

## Hard rules

- **English only.** Comments, docstrings, identifiers, commit messages.
- **No secrets in git.** `.env` is gitignored; `.env.example` is the
  template. Add new entries to both, with a placeholder value in the
  example. For multi-tenant deploys see
  [docs/environments.md](docs/environments.md).
- **Idempotent pushes.** Every `wf.run`-able script ends with a call
  to `noxuslab.push_workflow(client, wf)` — never
  `client.workflows.save(wf)` directly. The helper updates in place if
  a workflow with the same name exists; the raw SDK call duplicates.
- **Conventional Commits.** `feat:`, `fix:`, `chore:`, `docs:`,
  `refactor:`, `test:`, `ci:`. One topic per commit. Scope by
  workspace where useful, e.g. `feat(pagamentos): …`.
- **Lint and test clean.** `ruff check .` and `pytest` must pass
  locally before every commit. CI enforces both.
- **Coverage gate ≥ 70%.** New code-node templates ship with at least
  one offline test that exercises the `main(inputs)` function via
  `noxuslab.testing.exec_code_node`.
- **Tests follow the workflows.** When you edit a code-node template
  string, edit its test in the same commit. The test imports the same
  string the platform runs, so a stale test means a stale workflow.
- **Don't add a dependency without need.** Justify in the PR. Prefer
  stdlib + the helpers already in `noxuslab` over new packages.

## Testing

Two helpers from `noxuslab.testing` cover the entire offline surface
of a scaffolded repo:

- `make_fake_azure_client(label, probability)` — a `SimpleNamespace`
  shaped like `openai.AzureOpenAI` that replies with one fixed
  (label, logprob) pair. Use it through the `fake_azure_client`
  fixture in the top-level `conftest.py`.

- `exec_code_node(template, inputs)` — exec a `CodeExecutionV3Node`
  template string offline and call its `main(inputs)`. Use this for
  every Python code node in a workflow:

      from noxuslab.testing import exec_code_node
      from <workspace>.workflows.<file> import PARSE_TICKET_CODE

      out = exec_code_node(PARSE_TICKET_CODE, {{"ticket_json": "..."}})
      assert out["..."] == ...

No test ever pushes a workflow, hits OpenAI, or downloads an
attachment. Live runs happen separately via `noxuslab run`.

## Style

- **Code-node templates**: define exactly one `def main(inputs: dict)
  -> dict` at top level. Imports go before `main`. Catch parse / IO
  errors at the boundary and return a structured `{{"...": "...",
  "error": "..."}}` instead of raising — the platform serialises the
  exception otherwise.
- **Workflow files**: use the `mk(node)` helper so two nodes of the
  same type never share a `connector_config`. Name every node with
  `node.name = "..."` so the Noxus UI canvas reads like a sentence.
- **Neutral tone.** Do not pitch ideas by name-dropping famous people
  or with marketing words like "godlike". Describe what the change
  does and why it matters.

## AI assistants — operating procedure

Treat this as a checklist for every non-trivial change:

1. **Plan before touching code.** Read the file before editing. For
   multi-step work, keep a TODO list and update it.
2. **Use subagents** (see
   [.github/agents/](https://github.com/AdvanceWorks/noxus-lab/tree/main/.github/agents)
   in the lab) for delegated read-only research and focused
   refactors. Run independent subagents in parallel.
3. **Edit with intent.** Prefer `multi_replace_string_in_file` for
   batched edits in the same logical step. Always include 3–5 lines
   of context.
4. **Verify before claiming done.** `ruff check .` is green, `pytest`
   is green and coverage ≥ 70%, the commit message follows
   Conventional Commits.
5. **Commit + push.** One commit per topic. Never use `--no-verify`.

## When stuck

Read the SDK source under `.venv/Lib/site-packages/noxus_sdk/` — it
is small and the answer is usually there. For platform-level
questions (which models are enabled? which nodes are allowed via the
API?) check the Noxus workspace settings via the UI and update
`docs/open_questions.md`.
