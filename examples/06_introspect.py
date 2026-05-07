#!/usr/bin/env python3
"""List the available node types and models exposed by your workspace.

    python examples/06_introspect.py

Useful when you don't know which node type names to feed
`wf.node("...")` or which model strings work in your tier. Prints two
short tables: node types (alphabetical) and active models.
"""

import os

from dotenv import load_dotenv
from noxus_sdk.client import Client

load_dotenv()
c = Client(
    api_key=os.environ["NOXUS_API_KEY"],
    base_url=os.environ.get("NOXUS_BACKEND_URL"),
)

print(f"# {len(c.nodes)} node types")
for n in sorted({nd["name"] for nd in c.nodes if "name" in nd}):
    print("  ", n)

models = c.get_models()
active = [m for m in models if m.get("active") in (True, None)]
print(f"\n# {len(active)} models")
for m in active[:20]:
    print("  ", m.get("name"), "|", m.get("display_name", ""))
if len(active) > 20:
    print(f"  ... and {len(active) - 20} more")
