#!/usr/bin/env python3
"""Build a 3-node workflow (Input -> TextGeneration -> Output) and save it.

The saved workflow shows up immediately in the Noxus UI and is editable
there. Prints its id; pass it to 02_run.py.

    python examples/01_hello.py
"""

import os

from dotenv import load_dotenv
from noxus_sdk.client import Client
from noxus_sdk.workflows import WorkflowDefinition

load_dotenv()
c = Client(
    api_key=os.environ["NOXUS_API_KEY"],
    base_url=os.environ.get("NOXUS_BACKEND_URL"),
)

wf = WorkflowDefinition(name="hello-noxus-lab")
inp = wf.node("InputNode").config(label="topic", type="str")
gen = wf.node("TextGenerationNode").config(
    template="Write three crisp bullets about ((topic)).",
    model=["gemini-2.5-flash-lite"],
)
out = wf.node("OutputNode")
wf.link(inp.output(), gen.input("variables", "topic"))
wf.link(gen.output(), out.input())

print(c.workflows.save(wf).id)
