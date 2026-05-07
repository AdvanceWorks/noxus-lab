# mcp

The Noxus SDK ships an MCP server with ~39 tools over workflows, agents,
conversations, KBs, runs, files and admin.

## vs code (copilot)

Config: [.vscode/mcp.json](../.vscode/mcp.json). VS Code prompts for the
API key on first use and stores it in the secret store.

Verify: `> MCP: List Servers`. In Copilot Chat:

    @workspace list my noxus workflows

## other clients

Cursor (`.cursor/mcp.json`) and Claude Desktop (`claude_desktop_config.json`)
use the same shape: command `noxus mcp serve` with `NOXUS_API_KEY` in env,
or remote `url` with bearer header. See each client's MCP docs.

## transports

- `stdio` (default) — local subprocess.
- `sse` — `noxus mcp serve --transport sse --port 8888`.
- `streamable http` — `uvicorn noxus_sdk.mcp.asgi:app --port 8000`.
  Stateless; bearer token forwarded per request.

## backend

Override `NOXUS_BACKEND_URL` for on-prem. Default: `https://backend.noxus.ai`.
