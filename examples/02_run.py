#!/usr/bin/env python3
"""Execute a saved workflow by id. Blocks until done, prints status + output.

    python examples/02_run.py <workflow_id> [topic]

Default topic is 'octopus cognition'. The workflow's run is
async server-side; .wait() polls every 2s.
"""

import os
import sys

from dotenv import load_dotenv
from noxus_sdk.client import Client

if len(sys.argv) < 2:
    sys.exit("usage: python examples/02_run.py <workflow_id> [topic]")

wid = sys.argv[1]
topic = sys.argv[2] if len(sys.argv) > 2 else "octopus cognition"

load_dotenv()
c = Client(api_key=os.environ["NOXUS_API_KEY"])  # SDK reads NOXUS_BACKEND_URL from env.

run = c.workflows.get(workflow_id=wid).run(body={"topic": topic})
run.wait(interval=2)
print(run.status)
print(run.output)
