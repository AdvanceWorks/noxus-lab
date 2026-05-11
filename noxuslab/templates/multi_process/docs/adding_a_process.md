# Adding a new process to a workspace

Each process is one folder under `<workspace>/`. Folder names are
plain Python identifiers (`hr_requests`, not `01_hr_requests`) so the
`<workspace>.<process>.classifier` import path is valid.

## the recipe

1. **Copy an existing process:**

       cp -r <workspace>/<existing_process> <workspace>/<new_process>

2. **Edit `<new_process>/README.md`:** record the process context, the
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
   (`<workspace>.<existing_process>.labels` ->
   `<workspace>.<new_process>.labels`) and the default `deployment` /
   `threshold`. The actual call to Azure OpenAI lives in
   `noxuslab.classify` — never duplicate it.

6. **Edit `workflows/*.py`:** rename the workflow on the Noxus side
   (`name="<workspace>-<process>-..."` is the convention) and adjust
   the prompt for any in-platform `TextGenerationNode`.

7. **Add the process to the table** in the top-level
   [README.md](../README.md).

8. **Run the test suite:**

       pytest <workspace>/<new_process>

   New modules ship with at least one offline test.

## what NOT to do

- Do not import one process from another. Processes are independent.
  If they share logic, promote it to `noxuslab` upstream and update
  the `noxuslab` dependency in `pyproject.toml`.
- Do not put live Azure / Noxus credentials in tests. The
  `fake_azure_client` fixture from the top-level `conftest.py` is the
  convention.
- Do not skip the local `README.md` — it is the only place a process's
  context, label set, and open questions are recorded.
