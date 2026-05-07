"""Property-based tests for the codegen.

The contract: any wire dict with valid node ids and edges renders to a
parseable Python module. We don't assert behaviour, only structural
soundness.
"""

import ast

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from noxuslab.codegen import workflow_to_python

_id = st.text(
    alphabet="abcdef0123456789",
    min_size=8,
    max_size=8,
).map(lambda s: f"{s}-1111-1111-1111-111111111111")

_node_type = st.sampled_from(["InputNode", "OutputNode", "TextGenerationNode"])

_scalar = st.one_of(
    st.text(max_size=20),
    st.integers(min_value=-1000, max_value=1000),
    st.booleans(),
    st.none(),
)

_node = st.builds(
    lambda nid, t, cfg: {"id": nid, "type": t, "node_config": cfg},
    _id,
    _node_type,
    st.dictionaries(st.text(min_size=1, max_size=10), _scalar, max_size=4),
)


@given(nodes=st.lists(_node, min_size=1, max_size=5, unique_by=lambda n: n["id"]))
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_codegen_emits_valid_python(nodes):
    wire = {"name": "fuzz", "definition": {"nodes": nodes, "edges": []}}
    code = workflow_to_python(wire)
    ast.parse(code)
