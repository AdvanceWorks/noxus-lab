"""Noxus workflow: classify an inbound support email.

Push to the Noxus platform with `noxuslab push`:

    noxuslab push processes/support_routing/workflows/classify_email.py

The workflow is a thin in-platform classifier. The detailed Python
pipeline (logprobs, threshold, decision dataclass) lives in
`processes/support_routing/classifier.py` and is invoked by the
orchestrator that dispatches off this workflow's output.

Until the email-ingestion path is settled (Microsoft Graph vs Power
Automate), the input is a plain string. Replace with the real
Outlook-trigger node once that decision is made.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from noxus_sdk.client import Client
from noxus_sdk.workflows import WorkflowDefinition

load_dotenv()
c = Client(api_key=os.environ["NOXUS_API_KEY"])  # SDK reads NOXUS_BACKEND_URL from env.

wf = WorkflowDefinition(name="support-routing-classify-email")

email_in = wf.node("InputNode").config(label="email_text", type="str")

classify = wf.node("TextGenerationNode").config(
    template=(
        "Classify this email into one label: billing, technical, sales, "
        "general, other.\n\nReply with one label, lowercase, no "
        "punctuation.\n\nEmail:\n((email_text))"
    ),
    model=["gpt-4o"],
)
out = wf.node("OutputNode")

wf.link(email_in.output(), classify.input("variables", "email_text"))
wf.link(classify.output(), out.input())

print(c.workflows.save(wf).id)
