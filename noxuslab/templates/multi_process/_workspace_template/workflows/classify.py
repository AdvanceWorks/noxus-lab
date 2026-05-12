"""Noxus workflow: classify one input for workspace `__workspace__`.

Push (idempotent — updates in place if a workflow with this name exists):

    python -m __workspace__.workflows.classify

Or via the CLI:

    noxuslab push __workspace__/workflows/classify.py

The workflow is a thin in-platform classifier; the detailed Python
pipeline (logprobs, threshold, decision dataclass) lives in
`__workspace__/classifier.py` and is invoked by the orchestrator that
dispatches off this workflow's output.

Add more workflows next to this one as the process grows; each file
in `workflows/` is one workflow on the platform.

Conventions used here (apply them in every new workflow file):

  - `mk(NodeType)` deep-copies the node's `connector_config` so two
    nodes of the same type never share variable-connector dicts. This
    avoids a class of "Invalid workflow" / "value return missing"
    validation errors on the platform.
  - Every node gets a descriptive `node.name = "..."` so the Noxus UI
    canvas reads like a sentence rather than `Text Generation 1/2/3`.
  - Push with `noxuslab.push_workflow` so re-running this script
    updates the existing workflow instead of duplicating it.

The block between the `noxuslab:generated` sentinels is the only part
`noxuslab pull` will overwrite — anything outside is preserved.
"""

from __future__ import annotations

import copy
import os

from dotenv import load_dotenv
from noxus_sdk.client import Client
from noxus_sdk.workflows import NODE_TYPES, WorkflowDefinition
from noxuslab import push_workflow

load_dotenv()


def mk(wf: WorkflowDefinition, node_type: str):
    """Add a node with a fresh, deep-copied `connector_config`.

    The SDK shares one `connector_config` reference across every node of
    the same `node_type` in `NODE_TYPES`. Two `TextGenerationNode`s in
    the same workflow therefore inherit each other's variable connectors,
    which corrupts validation. Cloning the template per-node is the fix.
    """
    node = wf.node(node_type)
    node.connector_config = copy.deepcopy(NODE_TYPES[node_type].connector_config)
    if hasattr(node.connector_config, "variable_connectors"):
        node.connector_config.variable_connectors = {}
    return node


# >>> noxuslab:generated >>>
wf = WorkflowDefinition(name="__workspace__-classify")

# --- read the inbound text (InputNode) ---
n1 = mk(wf, "InputNode").config(label="text", type="str")
n1.name = "inbound text"

# --- ask the model for one label (TextGenerationNode) ---
n2 = mk(wf, "TextGenerationNode").config(
    template=(
        "Classify this input into one label: example_a, example_b, other.\n\n"
        "Reply with one label, lowercase, no punctuation.\n\n"
        "Input:\n((text))"
    ),
    model=["gpt-4o"],
)
n2.name = "classify into one label"

# --- emit the label (OutputNode) ---
n3 = mk(wf, "OutputNode")
n3.name = "label out"

wf.link(n1.output(), n2.input("variables", "text"))
wf.link(n2.output(), n3.input())
# <<< noxuslab:generated <<<


if __name__ == "__main__":
    client = Client(api_key=os.environ["NOXUS_API_KEY"])  # SDK reads NOXUS_BACKEND_URL from env.
    push_workflow(client, wf)
