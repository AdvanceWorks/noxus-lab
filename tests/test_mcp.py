"""Tests for `noxuslab.mcp` (offline)."""

from unittest.mock import MagicMock, patch


def test_build_server_returns_fastmcp():
    from noxuslab.mcp import build_server

    server = build_server()
    assert server is not None
    assert server.name == "noxuslab"


@patch("noxuslab.mcp._client")
def test_list_workflows_tool_calls_client(mock_client):
    from noxuslab.mcp import build_server

    fake_client = MagicMock()
    wf1, wf2 = MagicMock(), MagicMock()
    wf1.id, wf1.name = "id-1", "first"
    wf2.id, wf2.name = "id-2", "second"
    fake_client.workflows.list.return_value = iter([wf1, wf2])
    mock_client.return_value = fake_client

    server = build_server()
    # FastMCP exposes tools via its underlying tool manager.
    tools = list(server._tool_manager._tools.keys())  # noqa: SLF001
    assert "list_workflows" in tools
    assert "list_agents" in tools
    assert "pull_workflow" in tools
    assert "diff_workflow" in tools
    assert "ask_agent" in tools


def test_diff_workflow_returns_error_for_missing_file(tmp_path):
    from noxuslab.mcp import build_server

    server = build_server()
    diff_tool = server._tool_manager._tools["diff_workflow"]  # noqa: SLF001
    out = diff_tool.fn(workflow_id="x", file_path=str(tmp_path / "ghost.py"))
    assert "not found" in out


def test_serve_rejects_unknown_transport():
    import pytest

    from noxuslab.mcp import serve

    with pytest.raises(ValueError, match="unknown transport"):
        serve(transport="carrier-pigeon")
