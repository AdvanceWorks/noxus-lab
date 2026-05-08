# mcp

Two MCP servers are available — pick the one that matches your need:

| Server | Tools | When to use |
|---|---|---|
| `noxus mcp serve` (from noxus-sdk) | ~39 raw SDK tools | Power users / admins who want full SDK access |
| `noxuslab mcp serve` (this repo) | 5 high-level tools (`list_workflows`, `list_agents`, `pull_workflow`, `diff_workflow`, `ask_agent`) | Day-to-day workflow-as-code from any LLM client |

## noxuslab mcp serve

Run noxuslab itself as an MCP server. Configure once in your client and
ask the LLM things like *"list my noxus workflows"*, *"pull workflow
abc-123 to examples/my_flow.py"*, *"show me what would change if I push
this file"*, *"ask my support agent about ticket 42"*.

### Claude Desktop

`%APPDATA%\Claude\claude_desktop_config.json` (Windows) or
`~/Library/Application Support/Claude/claude_desktop_config.json` (Mac):

```json
{
  "mcpServers": {
    "noxuslab": {
      "command": "noxuslab",
      "args": ["mcp", "serve"],
      "env": { "NOXUS_API_KEY": "your_key_here" }
    }
  }
}
```

### Cursor

`.cursor/mcp.json` in your project (same shape).

### VS Code (Copilot)

Config: [.vscode/mcp.json](../.vscode/mcp.json). VS Code prompts for the
API key on first use and stores it in the secret store.

Verify: `> MCP: List Servers`. In Copilot Chat:

    @workspace list my noxus workflows

## noxus mcp serve (full SDK)

The SDK ships its own MCP server with ~39 tools over workflows, agents,
conversations, KBs, runs, files and admin. Use this when the 5 high-level
tools above aren't enough.

Same client config shape — just replace `command: "noxuslab"` with
`command: "noxus"`.

## transports

- `stdio` (default) — local subprocess.
- `sse` — `noxuslab mcp serve --transport sse`.

## backend

Override `NOXUS_BACKEND_URL` for on-prem. Default: `https://backend.noxus.ai`.
