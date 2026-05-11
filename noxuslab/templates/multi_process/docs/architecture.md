# Architecture (snapshot)

A two-layer repository on top of two platforms.

```
+-------------------------------------------------------------+
| Inbound channel (Outlook / form / webhook / file drop)      |
|        |                                                    |
|        v                                                    |
| Ingestion         <- repo-specific (Graph API / Power Automate)
|        |                                                    |
|        v                                                    |
| Noxus workflow:  <workspace>/<process>/workflows/...        |
|        |                                                    |
|        v                                                    |
| Python classifier:  <workspace>.<process>.classifier        |
|        |                                                    |
|        v                                                    |
| Shared primitive:   noxuslab.classify.classify (logprobs)   |
|        |                                                    |
|        v                                                    |
| Azure OpenAI (GPT-4o) -> token + logprob                    |
|        |                                                    |
|        v                                                    |
| Threshold decision: noxuslab.classify.decide                |
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

## why this layout

- **Workspace folder** = one workspace on the Noxus platform. All the
  workflows and agents pushed from inside that folder belong to the
  same Noxus workspace.
- **Process folder** = one end-to-end automation inside that workspace
  (a label set, a Python classifier, the Noxus workflow definitions,
  fixture data, and tests).
- **No `shared/` folder.** Cross-cutting code (Azure client wrapper,
  classification primitive, fake test client) lives in the
  `noxuslab` package and is imported. New repos stay tiny.

## why two layers per process

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

## why one repo for many workspaces

- One CI pipeline, one set of dependencies, one place to review.
- The customer reviews **one** repo per quarter, not many.
