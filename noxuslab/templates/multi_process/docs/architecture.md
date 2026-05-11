# Architecture (snapshot)

A two-layer repository on top of two platforms.

```
+-------------------------------------------------------------+
| Inbound channel (Outlook / form / webhook / file drop)      |
|        |                                                    |
|        v                                                    |
| Ingestion         <- open question: Graph API vs Power Automate
|        |                                                    |
|        v                                                    |
| Noxus workflow:  processes/<name>/workflows/...             |
|        |                                                    |
|        v                                                    |
| Python classifier:  processes.<name>.classifier             |
|        |                                                    |
|        v                                                    |
| Shared primitive:   shared.azure_openai.classify (logprobs) |
|        |                                                    |
|        v                                                    |
| Azure OpenAI (GPT-4o) -> token + logprob                    |
|        |                                                    |
|        v                                                    |
| Threshold decision: shared.classification.decide            |
|        |                                                    |
|        v                                                    |
| ClassificationResult { label, confidence, needs_review, ... }|
|        |                                                    |
|        v                                                    |
| Downstream Noxus branches                                   |
| +- needs_review=False -> automatic routing                  |
| +- needs_review=True  -> escalate to human review queue     |
+-------------------------------------------------------------+
```

## why two layers

- **Noxus workflow** — visible in the UI, editable by ops, audit
  trail per run, integrates with Outlook/SharePoint via existing
  nodes.
- **Python classifier** — testable offline, version-controlled,
  reproducible. Hosts the parts the platform cannot express cleanly
  today (logprob extraction, threshold, label schema). Imported by
  the Noxus workflow node that needs more than the platform's
  built-in `TextGenerationNode`.

When the platform grows a primitive (e.g. native logprobs in
`TextGenerationNode`), collapse the Python layer.

## why one repo for all processes

- One CI pipeline, one set of dependencies, one place to review.
- Cross-cutting helpers (`shared/`) are extracted from real
  duplication, not invented up front.
- The customer reviews **one** repo per quarter, not many.
