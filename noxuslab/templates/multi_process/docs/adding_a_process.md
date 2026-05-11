# Adding a new process

Each process is one folder under `processes/`. Folder names are plain
Python identifiers (`support_routing`, not `01_support_routing`) so
the `processes.support_routing.classifier` import path is valid.

## the recipe

1. **Copy the example:**

       cp -r processes/support_routing processes/<short_name>

2. **Edit `<short_name>/README.md`:** record the process context, the
   label set, the open questions, and how a new contributor runs it
   locally. This is the entry point for anyone new to the process.

3. **Edit `labels.py`:** replace `LABELS`, `REVIEW_LABELS`, and
   `SYSTEM_PROMPT`. Pick labels whose first token is unique so the
   model's first-token logprob is a clean confidence signal.

4. **Replace `sample_data/`:** one `.txt` file per actionable label.
   The test `test_sample_data_files_exist_for_every_actionable_label`
   will fail if you forget any.

5. **Edit `classifier.py`:** in most cases you only need to update the
   imports (`processes.support_routing.labels` ->
   `processes.<short_name>.labels`) and the default `deployment` /
   `threshold`. The actual call to Azure OpenAI lives in
   `shared/azure_openai.py` — do not duplicate it here.

6. **Edit `workflows/classify_email.py`:** rename the workflow,
   adjust the prompt the in-platform `TextGenerationNode` uses if you
   want a Noxus-side classifier as a fallback.

7. **Add the process to the table** in the top-level
   [README.md](../README.md) with its presentation order.

8. **Run the test suite:**

       pytest processes/<short_name>

   New modules ship with at least one offline test.

## what NOT to do

- Do not import process A from process B. Processes are independent.
  If they share logic, promote it to `shared/`.
- Do not put live Azure / Noxus credentials in tests. The fake-client
  pattern in `test_classifier.py` is the convention.
- Do not skip the local `README.md` — it is the only place a process's
  context, label set, and open questions are recorded.
