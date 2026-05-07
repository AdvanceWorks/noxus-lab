"""Pytest fixtures shared across tests."""

import os

import pytest


@pytest.fixture
def has_api_key() -> bool:
    return bool(os.environ.get("NOXUS_API_KEY"))


@pytest.fixture
def sample_workflow_dict() -> dict:
    """The wire shape of a 3-node Input -> TextGen -> Output workflow."""
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "name": "test-flow",
        "type": "flow",
        "definition": {
            "nodes": [
                {
                    "type": "InputNode",
                    "id": "11111111-1111-1111-1111-111111111111",
                    "name": "Input",
                    "display": {"position": {"x": 0, "y": 0}},
                    "node_config": {"type": "str", "label": "topic"},
                    "connector_config": {"inputs": [], "outputs": []},
                    "config_definition": {},
                    "subflow_config": None,
                    "subflow_id": None,
                    "inputs": [],
                    "outputs": [],
                },
                {
                    "type": "TextGenerationNode",
                    "id": "22222222-2222-2222-2222-222222222222",
                    "name": "Gen",
                    "display": {"position": {"x": 200, "y": 0}},
                    "node_config": {
                        "model": ["gemini-2.5-flash-lite"],
                        "template": "Write about ((topic)).",
                    },
                    "connector_config": {"inputs": [], "outputs": []},
                    "config_definition": {},
                    "subflow_config": None,
                    "subflow_id": None,
                    "inputs": [],
                    "outputs": [],
                },
                {
                    "type": "OutputNode",
                    "id": "33333333-3333-3333-3333-333333333333",
                    "name": "Out",
                    "display": {"position": {"x": 400, "y": 0}},
                    "node_config": {},
                    "connector_config": {"inputs": [], "outputs": []},
                    "config_definition": {},
                    "subflow_config": None,
                    "subflow_id": None,
                    "inputs": [],
                    "outputs": [],
                },
            ],
            "edges": [
                {
                    "from_id": {
                        "node_id": "11111111-1111-1111-1111-111111111111",
                        "connector_name": "output",
                        "key": None,
                        "optional": False,
                    },
                    "to_id": {
                        "node_id": "22222222-2222-2222-2222-222222222222",
                        "connector_name": "variables",
                        "key": "topic",
                        "optional": False,
                    },
                    "id": "edge-1",
                },
                {
                    "from_id": {
                        "node_id": "22222222-2222-2222-2222-222222222222",
                        "connector_name": "text_output",
                        "key": None,
                        "optional": False,
                    },
                    "to_id": {
                        "node_id": "33333333-3333-3333-3333-333333333333",
                        "connector_name": "input",
                        "key": None,
                        "optional": False,
                    },
                    "id": "edge-2",
                },
            ],
        },
    }
