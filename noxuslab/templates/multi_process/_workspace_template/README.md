# `__workspace__`

One workspace on the Noxus platform = one end-to-end automated
process. Replace this README with the real context once the process
owner has been interviewed:

- **What it does**: one sentence in plain language.
- **Trigger**: where the input comes from (Outlook, form, file
  drop, …).
- **Labels**: the set of classifications produced (see [labels.py](labels.py)).
- **Confidence threshold**: when the result is escalated for human
  review (default 0.85).
- **Open questions**: anything blocked on a customer or stakeholder
  decision. Promote them to [../docs/open_questions.md](../docs/open_questions.md)
  when they outgrow this README.

## layout

| Path | What it is |
| ---- | ---------- |
| [labels.py](labels.py) | Label set, review labels, system prompt — single source of truth |
| [classifier.py](classifier.py) | `classify_text(text) -> ClassificationResult`, offline-testable |
| [workflows/](workflows/) | Noxus workflow definitions, push with `noxuslab push` |
| [agents/](agents/) | Noxus agent definitions for this workspace |
| [knowledge/](knowledge/) | Source documents that back this workspace's knowledge bases |
| [test_fixtures/](test_fixtures/) | One `.txt` per actionable label; filename = expected label |
| [tests/](tests/) | Offline tests using the `fake_azure_client` fixture |

## run locally

    python -m __workspace__.classifier test_fixtures/example_a.txt

## push to the platform

    noxuslab push __workspace__/workflows/classify.py
    # add more workflows + agents under workflows/ and agents/ as the process grows
