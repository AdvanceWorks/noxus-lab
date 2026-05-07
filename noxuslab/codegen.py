"""Render a `WorkflowDefinition` as a self-contained Python script.

    from noxuslab.codegen import workflow_to_python
    code = workflow_to_python(workflow)

Output is a top-level script (no `def main`, no `__future__`) that
re-creates the workflow with the SDK and prints the new id. Non-trivial
node configs over a length threshold are hoisted into module-level vars.
The header records provenance: the source workflow id and a UTC stamp
so the file is traceable back to its origin.
"""

import json
import re
from datetime import datetime, timezone
from typing import Any

CONFIG_INLINE_LIMIT = 80
"""Above this many chars (repr length) a config value is hoisted to a top var."""


def _slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return s or "workflow"


def _py(value: Any) -> str:
    return repr(value)


def _topo_order(node_ids: list[str], edges: list[dict]) -> list[str]:
    """Kahn topological sort. Ids in topo order; original order on cycle."""
    indeg = dict.fromkeys(node_ids, 0)
    succ: dict[str, list[str]] = {nid: [] for nid in node_ids}
    for e in edges:
        src = e["from_id"]["node_id"]
        dst = e["to_id"]["node_id"]
        if src in indeg and dst in indeg:
            indeg[dst] += 1
            succ[src].append(dst)
    queue = [nid for nid, d in indeg.items() if d == 0]
    out: list[str] = []
    while queue:
        nid = queue.pop(0)
        out.append(nid)
        for s in succ[nid]:
            indeg[s] -= 1
            if indeg[s] == 0:
                queue.append(s)
    if len(out) != len(node_ids):
        return list(node_ids)
    return out


def _config_kwargs(cfg: dict, hoisted: dict[str, str]) -> str:
    parts: list[str] = []
    for key in sorted(cfg):
        if not key.isidentifier():
            # Skip keys we can't render as Python kwargs; they round-trip
            # via the wire dict but never appear in real workflows.
            continue
        rendered = _py(cfg[key])
        if len(rendered) > CONFIG_INLINE_LIMIT:
            var_name = f"_{key.upper()}"
            i = 1
            while var_name in hoisted and hoisted[var_name] != rendered:
                i += 1
                var_name = f"_{key.upper()}_{i}"
            hoisted.setdefault(var_name, rendered)
            parts.append(f"{key}={var_name}")
        else:
            parts.append(f"{key}={rendered}")
    return ", ".join(parts)


def _to_wire(wf: Any) -> dict:
    """Coerce a WorkflowDefinition or wire dict into the wire dict shape."""
    if isinstance(wf, dict):
        return wf
    if hasattr(wf, "to_noxus"):
        return wf.to_noxus()
    raise TypeError(f"unsupported workflow type: {type(wf)!r}")


def _edge_key(name_of: dict[str, str], e: dict) -> tuple:
    """Stable sort key so codegen output is deterministic."""
    return (
        name_of.get(e["from_id"]["node_id"], "~"),
        name_of.get(e["to_id"]["node_id"], "~"),
        e["from_id"].get("connector_name", ""),
        e["to_id"].get("connector_name", ""),
        str(e["to_id"].get("key") or ""),
    )


def workflow_to_python(
    wf: Any,
    *,
    var: str = "wf",
    include_imports: bool = True,
    runnable: bool = True,
    source_id: str | None = None,
) -> str:
    """Render `wf` as a self-contained Python script string.

    `wf` may be a `WorkflowDefinition` instance or a wire dict. If
    `source_id` is given, a provenance header is emitted.
    """
    raw = _to_wire(wf)
    name = raw["name"]
    nodes_raw: list[dict] = raw["definition"]["nodes"]
    edges_raw: list[dict] = raw["definition"]["edges"]

    by_id = {n["id"]: n for n in nodes_raw}
    order = _topo_order(list(by_id), edges_raw)
    name_of = {nid: f"n{i}" for i, nid in enumerate(order)}
    edges_sorted = sorted(edges_raw, key=lambda e: _edge_key(name_of, e))

    hoisted: dict[str, str] = {}
    body: list[str] = []

    for nid in order:
        n = by_id[nid]
        kwargs = _config_kwargs(n.get("node_config", {}), hoisted)
        if kwargs:
            body.append(f'{name_of[nid]} = {var}.node("{n["type"]}").config({kwargs})')
        else:
            body.append(f'{name_of[nid]} = {var}.node("{n["type"]}")')

    body.append("")

    for e in edges_sorted:
        src = e["from_id"]
        dst = e["to_id"]
        if src["node_id"] not in name_of or dst["node_id"] not in name_of:
            body.append(f"# skipped edge: {json.dumps(e)}")
            continue
        out_args = [_py(src["connector_name"])]
        in_args = [_py(dst["connector_name"])]
        if dst.get("key") is not None:
            in_args.append(_py(dst["key"]))
        body.append(
            f"{var}.link("
            f"{name_of[src['node_id']]}.output({', '.join(out_args)}), "
            f"{name_of[dst['node_id']]}.input({', '.join(in_args)})"
            ")"
        )

    pieces: list[str] = []
    slug = _slug(name)
    if include_imports:
        prov = ""
        if source_id:
            stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
            prov = f"# generated by `noxuslab pull` from {source_id} @ {stamp}\n"
        pieces.append(
            "#!/usr/bin/env python3\n"
            f"{prov}"
            f'"""Recreate the `{name}` workflow on Noxus.\n\n'
            f"    python examples/{slug}.py\n\n"
            "Generated by `noxuslab pull`. Edit freely.\n"
            '"""\n\n'
            "import os\n\n"
            "from dotenv import load_dotenv\n"
            "from noxus_sdk.client import Client\n"
            "from noxus_sdk.workflows import WorkflowDefinition\n\n"
            "load_dotenv()\n"
            "c = Client(\n"
            '    api_key=os.environ["NOXUS_API_KEY"],\n'
            '    base_url=os.environ.get("NOXUS_BACKEND_URL"),\n'
            ")\n"
        )

    if hoisted:
        pieces.append("\n".join(f"{k} = {v}" for k, v in hoisted.items()) + "\n")

    pieces.append(f"{var} = WorkflowDefinition(name={_py(name)})\n")
    pieces.append("\n".join(body))

    if runnable:
        pieces.append(f"\nprint(c.workflows.save({var}).id)\n")

    text = "\n".join(p.rstrip() for p in pieces if p) + "\n"
    return re.sub(r"\n{3,}", "\n\n", text)
