"""Noxus workflow: classify one input for `__workspace__.__process__`.

Push to the Noxus platform with `noxuslab push`:

    noxuslab push __workspace__/__process__/workflows/classify.py

The workflow is a thin in-platform classifier; the detailed Python
pipeline (logprobs, threshold, decision dataclass) lives in
`__workspace__/__process__/classifier.py` and is invoked by the
orchestrator that dispatches off this workflow's output.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from noxus_sdk.client import Client
from noxus_sdk.workflows import WorkflowDefinition

load_dotenv()
c = Client(api_key=os.environ["NOXUS_API_KEY"])  # SDK reads NOXUS_BACKEND_URL from env.

wf = WorkflowDefinition(name="__workspace__-__process__-classify")

text_in = wf.node("InputNode").config(label="text", type="str")

classify = wf.node("TextGenerationNode").config(
    template=(
        "Classify this input into one label: example_a, example_b, other.\n\n"
        "Reply with one label, lowercase, no punctuation.\n\n"
        "Input:\n((text))"
    ),
    model=["gpt-4o"],
)
out = wf.node("OutputNode")

wf.link(text_in.output(), classify.input("variables", "text"))
wf.link(classify.output(), out.input())

print(c.workflows.save(wf).id)
