"""Helpers for workflow push/update logic, shared by CLI and downstream repos.

The Noxus SDK `client.workflows.save(wf)` always creates a new workflow, even if one with the same name already exists. That makes re-running a push script duplicate the workflow on every run, which is never what we want during development.

`push_workflow(client, wf)` looks the workflow up by name first; if found it calls `update(id, wf, force=True)`, otherwise `save(wf)`. Either way it prints the resulting id.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noxus_sdk.client import Client
    from noxus_sdk.workflows import WorkflowDefinition


def push_workflow(client: "Client", wf: "WorkflowDefinition") -> str:
    """Create or update `wf` on the Noxus platform. Returns the id."""
    existing = next((w for w in client.workflows.list(page_size=100) if w.name == wf.name), None)
    if existing is not None:
        client.workflows.update(existing.id, wf, force=True)
        wf_id = existing.id
        action = "updated"
    else:
        client.workflows.save(wf)
        wf_id = wf.id
        action = "created"
    print(f"{action}: {wf.name}  {wf_id}")
    return wf_id


def find_workflow_id_by_name(client: "Client", name: str) -> str | None:
    """Look up a workflow id by name; None if it doesn't exist yet."""
    w = next((w for w in client.workflows.list(page_size=100) if w.name == name), None)
    return w.id if w else None
