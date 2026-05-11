# Adding a new workspace (= a new process)

Each workspace is one folder at the repo root. Folder names must be
plain Python identifiers (`hr_requests`, not `01_hr_requests`) so that
`<workspace>.classifier` is a valid import path.

## the recipe

1. **Scaffold or copy:**

       # via the CLI (recommended)
       noxuslab init --multi-process --workspace <new_name> .

       # or copy an existing workspace as a starting point
       cp -r <existing_workspace> <new_name>

2. **Edit `<new_name>/README.md`:** record the process context, the
   label set, the open questions, and how a new contributor runs it
   locally. This is the entry point for anyone new to the process.

3. **Edit `labels.py`:** replace `LABELS`, `REVIEW_LABELS`, and
   `SYSTEM_PROMPT`. Pick labels whose first token is unique so the
   model's first-token logprob is a clean confidence signal.

4. **Replace `test_fixtures/`:** one `.txt` file per actionable label,
   filename = expected label. The test
   `test_test_fixtures_cover_every_actionable_label` will fail if you
   forget any.

5. **Edit `classifier.py`:** update the imports
   (`<existing_workspace>.labels` -> `<new_name>.labels`) and the
   default `deployment` / `threshold`. The actual call to Azure OpenAI
   lives in `noxuslab.classify` \u2014 never duplicate it.

6. **Edit `workflows/*.py`:** rename the workflow on the Noxus side
   (`name="<workspace>-..."` is the convention) and adjust the prompt
   for any in-platform `TextGenerationNode`. Add more workflow files
   as the process grows; one file = one workflow on the platform.

7. **Add agents under `agents/`** as the process needs them. One file
   per agent. Naming convention: `<workspace>-<role>` on the platform.

8. **Drop policy / spec documents under `knowledge/`** so the
   knowledge bases backing this workspace's agents are version-
   controlled.

9. **Wire the workspace into the build:**
   - Add `"<new_name>"` to `pyproject.toml` (`[tool.hatch.build.targets.wheel] packages`,
     `[tool.pytest.ini_options] testpaths`, `[tool.coverage.run] source`,
     and `--cov=<new_name>` under `addopts`).
   - Add `"<new_name>"` to `pyrightconfig.json` (`include`).

10. **Add a row** for the new workspace in the top-level
    [README.md](../README.md).

11. **Run the test suite:**

        pytest <new_name>

    New modules ship with at least one offline test.

## what NOT to do

- Do not import one workspace from another. Workspaces are independent.
  If they share logic, promote it to `noxuslab` upstream and update
  the `noxuslab` dependency in `pyproject.toml`.
- Do not put live Azure / Noxus credentials in tests. The
  `fake_azure_client` fixture from the top-level `conftest.py` is the
  convention.
- Do not skip the local `README.md` \u2014 it is the only place a
  workspace's context, label set, and open questions are recorded.
