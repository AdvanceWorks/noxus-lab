"""MCP server exposing noxuslab as tools to MCP clients.

Configure in Claude Desktop, Cursor, or VS Code:

    {
      "mcpServers": {
        "noxuslab": {
          "command": "noxuslab",
          "args": ["mcp", "serve"],
          "env": {"NOXUS_API_KEY": "..."}
        }
      }
    }

Then ask the LLM things like:

    list my noxus workflows
    pull workflow abc-123 to examples/my_flow.py
    show me what would change if I push examples/my_flow.py

The tools wrap the same code paths as the CLI, so they go through the
retry/audit/secrets layers.
"""

from __future__ import annotations

import difflib
import os
from pathlib import Path

from dotenv import load_dotenv

from noxuslab._net import call as net_call


def _client():
    """Build a Noxus client. Imported here to avoid hard SDK dependency at import time."""
    from noxus_sdk.client import Client

    from noxuslab._secrets import resolve_api_key

    kwargs: dict = {"api_key": resolve_api_key()}
    url = os.environ.get("NOXUS_BACKEND_URL")
    if url:
        kwargs["base_url"] = url
    return Client(**kwargs)


def build_server():
    """Construct and return the FastMCP server with noxuslab tools registered."""
    from mcp.server.fastmcp import FastMCP

    from noxuslab.codegen import workflow_to_python

    mcp = FastMCP(name="noxuslab")

    @mcp.tool()
    def list_workflows() -> list[dict]:
        """List all workflows in the Noxus workspace.

        Returns a list of {id, name} entries.
        """
        load_dotenv()
        client = _client()
        wfs = net_call(lambda: list(client.workflows.list()), what="list workflows")
        return [{"id": w.id, "name": w.name} for w in wfs]

    @mcp.tool()
    def list_agents() -> list[dict]:
        """List all agents in the Noxus workspace.

        Returns a list of {id, name} entries. Use the id with `chat` or `ask`.
        """
        load_dotenv()
        client = _client()
        agents = net_call(lambda: list(client.agents.list()), what="list agents")
        return [{"id": a.id, "name": a.name} for a in agents]

    @mcp.tool()
    def pull_workflow(workflow_id: str) -> str:
        """Pull a workflow from Noxus and return it as Python code.

        Args:
            workflow_id: UUID of the workflow to pull.

        Returns the canonical Python source — a self-contained script that
        re-creates the workflow when executed.
        """
        load_dotenv()
        client = _client()
        wf = net_call(
            lambda: client.workflows.get(workflow_id=workflow_id),
            what="pull workflow",
        )
        return workflow_to_python(wf, source_id=workflow_id)

    @mcp.tool()
    def diff_workflow(workflow_id: str, file_path: str) -> str:
        """Compare a local Python file against the current server workflow.

        Args:
            workflow_id: UUID of the workflow on the server.
            file_path: path to the local Python file.

        Returns a unified diff (empty string if identical).
        """
        path = Path(file_path)
        if not path.is_file():
            return f"error: file not found: {file_path}"
        load_dotenv()
        client = _client()
        wf = net_call(
            lambda: client.workflows.get(workflow_id=workflow_id),
            what="diff workflow",
        )
        server_code = workflow_to_python(wf, source_id=workflow_id)
        local_code = path.read_text(encoding="utf-8")
        diff = list(
            difflib.unified_diff(
                server_code.splitlines(keepends=True),
                local_code.splitlines(keepends=True),
                fromfile=f"server:{workflow_id}",
                tofile=f"local:{path}",
                n=3,
            )
        )
        return "".join(diff) if diff else ""

    @mcp.tool()
    def ask_agent(question: str, agent_id: str | None = None) -> str:
        """Ask a Noxus agent a one-shot question and return the reply text.

        Args:
            question: the question to ask, in plain language.
            agent_id: optional agent UUID. If omitted, uses the default model.

        Returns the assistant's full reply as a string.
        """
        from noxus_sdk.resources.conversations import (
            ConversationSettings,
            MessageRequest,
        )

        load_dotenv()
        client = _client()
        if agent_id:
            conv = net_call(
                lambda: client.conversations.create(name="noxuslab-mcp", agent_id=agent_id),
                what="create conversation",
            )
        else:
            settings = ConversationSettings(
                model=["gemini-2.5-flash"],
                temperature=0.7,
                max_tokens=4096,
                tools=[],
            )
            conv = net_call(
                lambda: client.conversations.create(name="noxuslab-mcp", settings=settings),
                what="create conversation",
            )
        reply = net_call(
            lambda: conv.chat(MessageRequest(content=question)),
            what="ask agent",
        )
        return getattr(reply, "content", str(reply))

    return mcp


def serve(transport: str = "stdio") -> None:
    """Run the MCP server. transport: 'stdio' (default) or 'sse'."""
    server = build_server()
    if transport == "stdio":
        server.run("stdio")
    elif transport == "sse":
        server.run("sse")
    else:
        raise ValueError(f"unknown transport: {transport!r}")
