# Open questions

Decisions that affect more than one process. Each entry says who
owns the answer and what is blocked.

## ingestion

- **Inbound path** — Microsoft Graph API (preferred, full metadata
  access) or a Power Automate trigger (faster to approve, loses some
  metadata)?
  - Owner: customer IT
  - Blocks: production deployment. Does not block development — the
    classifier accepts a plain string today.

- **Existing automation** — does the customer already have Power
  Automate / Logic Apps reading the target mailbox? If yes, plug into
  it instead of competing.
  - Owner: customer IT
  - Blocks: nothing — answer changes architecture, not timeline.

## attachments

- **Storage** — do attachments stay attached to the email, or are
  they moved to SharePoint?
  - Owner: customer IT
  - Blocks: how `shared/azure_openai.py` reads them. If SharePoint, we
    need a Graph permission on the relevant site/library.

## scale and routing

- **Volume** — how many messages per day? Drives the choice between
  the standard Azure OpenAI deployment and the Provisioned
  Throughput Unit tier.
  - Owner: business owner
  - Blocks: cost estimate. Does not block the MVP.

- **Review fan-out** — when `needs_review=True`, who receives the
  alert? Single inbox, distribution list, or a ticket-system queue
  (Jira / ServiceNow)?
  - Owner: business owner
  - Blocks: the downstream Noxus branch on the `needs_review` flag.

## Azure / platform

- **Azure project structure** — does the customer have a convention
  for one Azure AI Foundry project per process, or one shared project
  across processes? Affects RBAC, billing tagging, and quota.
  - Owner: customer IT (Azure admin)
  - Blocks: the Foundry project we deploy `gpt-4o` into.

- **Billing** — separate subscription for AI workloads, or charged
  to an existing cost centre?
  - Owner: customer finance / IT
  - Blocks: nothing immediately.

## modelling / future work

- **Confidence calibration** — the MVP uses Azure OpenAI logprobs as
  a confidence signal. Once we have labelled traffic from the live
  pilot, the next iteration is a supervised classifier with
  calibrated probabilities (Platt scaling or isotonic regression).
  Needs: training, validation, model versioning, data-drift
  monitoring — all of which depend on the customer's MLOps stack.
  - Owner: us, after the pilot
  - Blocks: nothing in v1.

- **Monitoring** — does the customer already use Power BI / Azure
  Monitor / Application Insights for process dashboards? Plug into
  the existing stack rather than ship a new one.
  - Owner: customer IT
  - Blocks: dashboard delivery, not the pilot.
