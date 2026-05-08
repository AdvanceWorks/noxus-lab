"""AI workflow generator.

`noxuslab gen "describe what you want"` asks a Noxus agent for Python code that
defines a `WorkflowDefinition` named `wf`, strips markdown fences, writes it to
`examples/NN_<slug>.py` (or `--out`), then prints the file path. The resulting
file works directly with `noxuslab push <file>`.

Composition over magic — this is a thin wrapper over `chat.one_shot`.
"""

import re
from pathlib import Path

from dotenv import load_dotenv

from noxuslab._net import call as net_call
from noxuslab._term import dim, green
from noxuslab.errors import NoxusLabError

_SYSTEM_PROMPT = """You are a Noxus workflow code generator.

Output ONLY a self-contained Python script that:
  1. imports from `noxus_sdk` and `noxuslab`,
  2. constructs a `WorkflowDefinition` bound to the variable `wf`,
  3. ends with `print(c.workflows.save(wf).id)`.

No prose, no commentary, no markdown fences. Plain Python only.
The script must be ready to feed into `noxuslab push <file>`."""


def _strip_fences(text: str) -> str:
    """Remove ``` fences if the model added them despite instructions."""
    text = text.strip()
    m = re.match(r"^```(?:python|py)?\n(.*?)\n```\s*$", text, flags=re.DOTALL)
    return m.group(1) if m else text


def _slug(s: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return s[:max_len] or "generated"


def _next_example_path(name_slug: str) -> Path:
    examples = Path("examples")
    examples.mkdir(parents=True, exist_ok=True)
    used = [int(m.group(1)) for p in examples.glob("*.py") if (m := re.match(r"^(\d{2})_", p.name))]
    nxt = (max(used) + 1) if used else 1
    return examples / f"{nxt:02d}_{name_slug}.py"


def generate(prompt: str, *, agent_id: str | None, model: str | None, out: str | None) -> int:
    """Generate workflow code from a natural-language prompt. Returns exit code."""
    if not prompt.strip():
        raise NoxusLabError("empty prompt")
    load_dotenv()
    from noxus_sdk.resources.conversations import (
        ConversationSettings,
        MessageRequest,
    )

    from noxuslab.chat import _make_client

    client = _make_client()
    if agent_id:
        conv = net_call(
            lambda: client.conversations.create(name="noxuslab-gen", agent_id=agent_id),
            what="create conversation",
        )
    else:
        settings = ConversationSettings(
            model=[model or "gemini-2.5-flash"],
            temperature=0.3,
            max_tokens=8192,
            tools=[],
        )
        conv = net_call(
            lambda: client.conversations.create(name="noxuslab-gen", settings=settings),
            what="create conversation",
        )
    full_prompt = f"{_SYSTEM_PROMPT}\n\nUser request:\n{prompt}"
    reply = net_call(
        lambda: conv.chat(MessageRequest(content=full_prompt)),
        what="generate workflow",
    )
    code = _strip_fences(getattr(reply, "content", str(reply)))
    if "wf" not in code:
        raise NoxusLabError("model did not produce a `wf` variable; try a more specific prompt")
    path = Path(out) if out else _next_example_path(_slug(prompt))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code + ("\n" if not code.endswith("\n") else ""), encoding="utf-8")
    print(green(f"wrote {path}"), dim(f"({len(code.splitlines())} lines)"))
    print(dim("review the file, then run: ") + f"noxuslab push {path}")
    return 0
