#!/usr/bin/env python3
"""Pull a workflow from Noxus and print the generated Python (no write).

    python examples/07_pull_demo.py <workflow_id>

A minimal demo of `noxuslab.codegen.workflow_to_python`. Use the
`noxuslab pull` CLI to write the result to a file under `examples/`.
"""

import os
import sys

from dotenv import load_dotenv
from noxus_sdk.client import Client

from noxuslab.codegen import workflow_to_python

if len(sys.argv) < 2:
    sys.exit("usage: python examples/07_pull_demo.py <workflow_id>")

load_dotenv()
c = Client(
    api_key=os.environ["NOXUS_API_KEY"],
    base_url=os.environ.get("NOXUS_BACKEND_URL"),
)
wf = c.workflows.get(workflow_id=sys.argv[1])
print(workflow_to_python(wf))
