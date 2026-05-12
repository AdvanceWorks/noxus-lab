"""Helpers for workflow push/update logic, shared by CLI and downstream repos.

The Noxus SDK `client.workflows.save(wf)` always creates a new workflow, even if one with the same name already exists. That makes re-running a push script duplicate the workflow on every run, which is never what we want during development.

`push_workflow(client, wf)` looks the workflow up by name first; if found it calls `update(id, wf, force=True)`, otherwise `save(wf)`. Either way it prints the resulting id.

Note: the SDK `client.workflows.list()` hardcodes `type=flow`. Because subflows
use `type="sub_flow"`, we call the raw API endpoint so both types are found.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noxus_sdk.client import Client
    from noxus_sdk.workflows import WorkflowDefinition


def _list_all(client: "Client", page_size: int = 100) -> list:
    """Return all workflows regardless of type (flow + sub_flow)."""
    return client.pget(
        "/v1/workflows",
        params={"page": 1, "page_size": page_size, "type": "flow"},
        page=1,
        page_size=page_size,
    )


def push_workflow(client: "Client", wf: "WorkflowDefinition") -> str:
    """Create or update `wf` on the Noxus platform. Returns the id."""
    existing_data = next((w for w in _list_all(client) if w.get("name") == wf.name), None)
    if existing_data is not None:
        existing_id = existing_data["id"]
        existing_type = existing_data.get("type", "flow")
        if existing_type != wf.type:
            # Cannot PATCH a type change — delete and recreate.
            client.workflows.delete(existing_id)
            client.workflows.save(wf)
            wf_id = wf.id
            action = "recreated"
        else:
            client.workflows.update(existing_id, wf, force=True)
            wf_id = existing_id
            action = "updated"
    else:
        client.workflows.save(wf)
        wf_id = wf.id
        action = "created"
    print(f"{action}: {wf.name}  {wf_id}")
    return wf_id


def find_workflow_id_by_name(client: "Client", name: str) -> str | None:
    """Look up a workflow id by name (flow or sub_flow); None if not found."""
    w = next((w for w in _list_all(client) if w.get("name") == name), None)
    return w["id"] if w else None
