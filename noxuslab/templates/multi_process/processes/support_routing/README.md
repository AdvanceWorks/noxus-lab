# 01 — support email routing (example process)

The example that ships with `noxuslab init --multi-process`. It is a
realistic, generic B2B scenario: an inbound support mailbox is read,
each email is classified into one of five routing categories, and
low-confidence cases are escalated for human review.

Treat it as a working starting point — keep the structure, replace the
labels, prompt and sample data for your own process.

## what is in this folder

| File / folder                                                 | Purpose                                                   |
| ------------------------------------------------------------- | --------------------------------------------------------- |
| [README.md](README.md)                                        | This file: context, decisions, open questions             |
| [labels.py](labels.py)                                        | The label set + `LABELS`, `REVIEW_LABELS`, `SYSTEM_PROMPT` |
| [classifier.py](classifier.py)                                | Pure function: `classify_email(text) -> ClassificationResult` |
| [workflows/classify_email.py](workflows/classify_email.py)    | Noxus workflow definition (push with `noxuslab push`)     |
| [sample_data/](sample_data/)                                  | One example email per actionable label, used in tests     |
| [tests/test_classifier.py](tests/test_classifier.py)          | Offline tests using a mocked Azure OpenAI client          |

## the labels

Each label starts with a unique first token so the model's first-token
logprob is a clean confidence signal.

| Label       | Example trigger                                            |
| ----------- | ---------------------------------------------------------- |
| `billing`   | "Invoice is wrong / charge appeared / refund needed"       |
| `technical` | "Bug, error, login fails, integration broken"              |
| `sales`     | "Pricing question, demo request, contract upgrade"         |
| `general`   | "How do I do X, where is the documentation"                |
| `other`     | _Anything that does not clearly fit — always reviewed_     |

## confidence threshold

Default: **0.85**. Below the threshold, or when the model picks
`other`, the result has `needs_review=True` and the downstream Noxus
workflow routes the email to the support team's review queue instead
of acting on the label automatically.

The threshold is a single keyword argument to `classify_email`, so a
later experiment can tune it per label without touching this file's
logic.

## open questions

These typically wait on the customer's tech-lead reply (record yours
in [docs/open_questions.md](../../docs/open_questions.md)):

1. **Email ingestion** — Microsoft Graph API or Power Automate trigger?
2. **Attachment storage** — in the email or moved to SharePoint?
3. **Volume** — daily message count drives the choice between the
   real-time Azure OpenAI deployment and a batch-friendly tier.
4. **Review fan-out** — single inbox, distribution list, or a
   ticket-system queue?

Until those are answered, the workflow accepts the email content as a
plain string (no Outlook bindings yet) so the rest is testable in
isolation.

## how to run locally

    pytest processes/support_routing        # offline, ~1s

To exercise the live Azure OpenAI path:

    cp .env.example .env                    # fill AZURE_OPENAI_*
    python -m processes.support_routing.classifier processes/support_routing/sample_data/billing.txt
