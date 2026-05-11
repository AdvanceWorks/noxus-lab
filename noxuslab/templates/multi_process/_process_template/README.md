# `__workspace__/__process__`

One end-to-end automation. Replace this README with the real context:

- **What it does**: one sentence, in plain language.
- **Trigger**: where the input comes from (Outlook, form, file drop, …).
- **Labels**: the set of classifications this process produces (see
  [labels.py](labels.py)).
- **Confidence threshold**: when the result is escalated for human
  review (default 0.85).
- **Open questions**: anything blocked on a customer or stakeholder
  decision. Migrate them to [../../docs/open_questions.md](../../docs/open_questions.md)
  when they outgrow this README.

## files

| File | What it is |
| ---- | ---------- |
| [labels.py](labels.py) | The label set, the review labels, the system prompt |
| [classifier.py](classifier.py) | `classify(text) -> ClassificationResult`, offline-testable |
| [workflows/](workflows/) | Noxus workflow definitions, push with `noxuslab push` |
| [test_fixtures/](test_fixtures/) | One `.txt` per actionable label; filename = expected label |
| [tests/](tests/) | Offline tests using the `fake_azure_client` fixture |

## run locally

    python -m __workspace__.__process__.classifier test_fixtures/example.txt
