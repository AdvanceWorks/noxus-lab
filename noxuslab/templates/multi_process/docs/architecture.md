# Architecture (snapshot)

A two-layer repository on top of two platforms.

```
+-------------------------------------------------------------+
| Inbound channel (Outlook / form / webhook / file drop)      |
|        |                                                    |
|        v                                                    |
| Ingestion          <- repo-specific (Graph API / Power Automate)
|        |                                                    |
|        v                                                    |
| Noxus workflow:   <workspace>/workflows/...                 |
|        |                                                    |
|        v                                                    |
| Python classifier:  <workspace>.classifier                  |
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
| ClassificationResult { label, confidence, needs_review, ...}|
|        |                                                    |
|        v                                                    |
| Downstream Noxus branches (workflows + agents)              |
| +- needs_review=False -> automatic routing                  |
| +- needs_review=True  -> escalate to human review queue     |
+-------------------------------------------------------------+
```

## why this layout

- **One workspace = one process.** A workspace folder corresponds 1-to-1
  to a workspace on the Noxus platform AND to one end-to-end business
  process. It owns its own labels, classifier, workflows, agents,
  knowledge bases, fixtures, tests, and (eventually) its own
  CODEOWNERS line.
- **No `shared/` folder.** Cross-cutting code (Azure client wrapper,
  classification primitive, fake test client, every CLI command) lives
  in the `noxuslab` package and is imported. New repos and new
  workspaces stay tiny.
- **Workspaces never import from each other.** If two workspaces need
  the same helper, promote it to `noxuslab` upstream.

## why two layers per workspace (Python + Noxus)

- **Noxus workflow / agent** \u2014 visible in the UI, editable by ops,
  audit trail per run, integrates with Outlook / SharePoint via existing
  nodes.
- **Python classifier** \u2014 testable offline, version-controlled,
  reproducible. Hosts the parts the platform cannot express cleanly
  today (logprob extraction, threshold, label schema). Imported by the
  Noxus nodes that need more than the platform's built-in primitives.

When the platform grows a primitive (e.g. native logprobs in
`TextGenerationNode`), collapse the Python layer.

## why one repo for many workspaces

- One CI pipeline, one set of dependencies, one place to review.
- The customer reviews **one** repo per quarter, not many.
- Per-workspace ownership is expressed via `CODEOWNERS`, not via
  separate repositories.
