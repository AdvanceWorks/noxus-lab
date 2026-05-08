"""Mermaid graph rendering for workflows.

Emits a `flowchart TD` block with one node per workflow node and edges between
them. Output is plain text (markdown code block) — paste into any Mermaid
renderer (GitHub, VS Code, mermaid.live) for a visual.

Used by `noxuslab diff --visual` to compare server vs local graphs.
"""

from typing import Any


def _node_id(node: Any, idx: int) -> str:
    raw = getattr(node, "id", None) or getattr(node, "name", None) or f"n{idx}"
    return "".join(c if c.isalnum() else "_" for c in str(raw))[:40] or f"n{idx}"


def _node_label(node: Any) -> str:
    label = getattr(node, "name", None) or getattr(node, "type", None) or "?"
    return str(label).replace('"', "'")[:40]


def to_mermaid(wf: Any, *, title: str | None = None) -> str:
    """Render a WorkflowDefinition (or anything with .nodes/.edges) as Mermaid."""
    nodes = list(getattr(wf, "nodes", []) or [])
    edges = list(getattr(wf, "edges", []) or [])
    lines = ["```mermaid", "flowchart TD"]
    if title:
        lines.insert(1, f"%% {title}")
    id_map: dict[str, str] = {}
    for i, n in enumerate(nodes):
        nid = _node_id(n, i)
        id_map[str(getattr(n, "id", "") or i)] = nid
        lines.append(f'    {nid}["{_node_label(n)}"]')
    for e in edges:
        src = getattr(e, "from_node", None) or getattr(e, "source", None) or getattr(e, "src", "")
        dst = getattr(e, "to_node", None) or getattr(e, "target", None) or getattr(e, "dst", "")
        s = id_map.get(str(src), str(src))
        d = id_map.get(str(dst), str(dst))
        lines.append(f"    {s} --> {d}")
    lines.append("```")
    return "\n".join(lines) + "\n"
