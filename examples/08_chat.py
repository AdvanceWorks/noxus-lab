#!/usr/bin/env python3
"""Start a conversation with a Noxus agent and send one message.

    python examples/08_chat.py [agent_id]

Without an agent_id, creates an ephemeral conversation with the default
model. With an agent_id, inherits the agent's tools, persona, and KB access.
"""

import os
import sys

from dotenv import load_dotenv
from noxus_sdk.client import Client
from noxus_sdk.resources.conversations import MessageRequest

load_dotenv()
c = Client(
    api_key=os.environ["NOXUS_API_KEY"],
    base_url=os.environ.get("NOXUS_BACKEND_URL"),
)

agent_id = sys.argv[1] if len(sys.argv) > 1 else None

if agent_id:
    conv = c.conversations.create(name="demo-chat", agent_id=agent_id)
else:
    from noxus_sdk.resources.conversations import ConversationSettings

    settings = ConversationSettings(
        model=["gemini-2.5-flash"], temperature=0.7, max_tokens=4096, tools=[]
    )
    conv = c.conversations.create(name="demo-chat", settings=settings)

reply = conv.chat(MessageRequest(content="Hello! What can you help me with?"))
print(reply.content)
