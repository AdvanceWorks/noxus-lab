#!/usr/bin/env python3
"""Create an Agent (Co-worker) bound to a workflow tool, then chat with it.

    python examples/04_agent.py <workflow_id>

The agent gets a `WorkflowTool` pointing to the workflow id you pass in
(use the one printed by `01_hello.py`). We then start a Conversation
with `agent_id=...` and send one message that asks the agent to invoke
the tool. Settings come from the agent automatically.
"""

import os
import sys

from dotenv import load_dotenv
from noxus_sdk.client import Client
from noxus_sdk.resources.conversations import (
    ConversationSettings,
    MessageRequest,
    WorkflowTool,
)

if len(sys.argv) < 2:
    sys.exit("usage: python examples/04_agent.py <workflow_id>")

wid = sys.argv[1]

load_dotenv()
c = Client(
    api_key=os.environ["NOXUS_API_KEY"],
    base_url=os.environ.get("NOXUS_BACKEND_URL"),
)

agent = c.agents.create(
    name="noxus-lab-agent",
    settings=ConversationSettings(
        model=["gemini-2.5-flash-lite"],
        temperature=0.2,
        max_tokens=300,
        tools=[
            WorkflowTool(
                enabled=True,
                workflow={"id": wid, "name": "hello", "description": "Bullets generator."},
                name="hello",
                description="Generate three bullets about a topic.",
            )
        ],
        extra_instructions="When asked for bullets on a topic, call the hello tool.",
    ),
)
print("agent:", agent.id)

conv = c.conversations.create(name="agent-chat", agent_id=agent.id)
print("conv:", conv.id)

resp = conv.add_message(MessageRequest(content="Use the hello tool. Topic: octopus cognition."))
for part in resp.message_parts:
    print("-", part.get("type"), "::", str(part.get("content"))[:200])
