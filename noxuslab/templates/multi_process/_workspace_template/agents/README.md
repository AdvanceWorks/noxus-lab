# Agents for workspace `__workspace__`

One Python file per Noxus agent that belongs to this workspace.
Each agent file builds an `AgentDefinition` (or whatever the SDK
exposes) and pushes it with `noxuslab agents push <file>`.

Empty by default. Add files like `agents/router.py`,
`agents/specialist.py`, etc., as the process grows. The convention is
to name the agent on the platform `__workspace__-<role>` so it is
easy to spot which workspace an agent belongs to.

> Tip: pull an existing agent from the platform with
> `noxuslab agents pull <agent_id>` to bootstrap a new file from
> live state.
