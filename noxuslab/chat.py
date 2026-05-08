"""Interactive chat REPL and one-shot ask backed by Noxus Conversations."""

import os
import sys

from dotenv import load_dotenv

from noxuslab._term import bold, dim, green
from noxuslab.errors import AuthMissing


def _make_client():
    from noxus_sdk.client import Client

    key = os.environ.get("NOXUS_API_KEY")
    if not key:
        raise AuthMissing("NOXUS_API_KEY not set (check .env)")
    kwargs: dict = {"api_key": key}
    url = os.environ.get("NOXUS_BACKEND_URL")
    if url:
        kwargs["base_url"] = url
    return Client(**kwargs)


def _create_conversation(client, *, agent_id: str | None, model: str | None):
    """Create a fresh conversation, optionally tied to an agent."""
    from noxus_sdk.resources.conversations import ConversationSettings

    if agent_id:
        return client.conversations.create(name="noxuslab-chat", agent_id=agent_id)
    settings = ConversationSettings(
        model=[model or "gemini-2.5-flash"],
        temperature=0.7,
        max_tokens=4096,
        tools=[],
    )
    return client.conversations.create(name="noxuslab-chat", settings=settings)


def _stream_reply(conversation) -> str:
    """Stream assistant reply events, print tokens live, return full text."""
    full = []
    for event in conversation.iter_messages():
        if event.type == "conversation_end":
            break
        if event.content:
            sys.stdout.write(event.content)
            sys.stdout.flush()
            full.append(event.content)
    sys.stdout.write("\n")
    return "".join(full)


def _send_blocking(conversation, text: str) -> str:
    """Send a message and stream the response."""
    from noxus_sdk.resources.conversations import MessageRequest

    conversation.chat(MessageRequest(content=text))
    return _stream_reply(conversation)


def start_chat(*, agent_id: str | None = None, model: str | None = None) -> int:
    """Enter interactive chat loop. Returns exit code."""
    load_dotenv()
    client = _make_client()
    conv = _create_conversation(client, agent_id=agent_id, model=model)

    label = "agent" if agent_id else (model or "gemini-2.5-flash")
    print(green(f"connected to {label}"), dim("(/exit to quit)"))
    print()

    try:
        while True:
            try:
                line = input(bold("you> "))
            except EOFError:
                break
            line = line.strip()
            if not line:
                continue
            if line.lower() in ("/exit", "/quit", "/q"):
                break
            if line.lower() == "/clear":
                conv = _create_conversation(client, agent_id=agent_id, model=model)
                print(dim("(conversation cleared)"))
                continue
            sys.stdout.write(dim("ai>") + " ")
            _send_blocking(conv, line)
    except KeyboardInterrupt:
        print()
    return 0


def one_shot(question: str, *, agent_id: str | None = None, model: str | None = None) -> int:
    """Ask a single question, print the answer, exit."""
    load_dotenv()
    client = _make_client()
    conv = _create_conversation(client, agent_id=agent_id, model=model)
    _send_blocking(conv, question)
    return 0
