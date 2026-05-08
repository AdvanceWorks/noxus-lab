"""`noxuslab trace` — list / show / replay trace files."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from noxuslab._term import dim, green, red
from noxuslab._trace import find_trace, list_traces, read_trace
from noxuslab.errors import BadFile


def cmd_list(limit: int = 20) -> int:
    rows = list_traces(limit)
    if not rows:
        print(dim("no traces yet — run `noxuslab run <file>` to record one"))
        return 0
    for p in rows:
        try:
            entries = read_trace(p)
        except (OSError, json.JSONDecodeError):
            print(f"  {p.name}  (unreadable)")
            continue
        header = next((e for e in entries if e["kind"] == "header"), {})
        footer = next((e for e in entries if e["kind"] == "footer"), {})
        status = footer.get("status", "incomplete")
        elapsed = footer.get("elapsed_ms")
        wf = header.get("workflow_name") or header.get("workflow_id") or "?"
        tag = green(status) if status == "completed" else red(status)
        ms = f"{elapsed}ms" if elapsed is not None else "—"
        print(f"  {p.name}  {tag:<24}  {wf}  ({ms})")
    return 0


def cmd_show(needle: str, *, json_out: bool = False) -> int:
    p = find_trace(needle)
    if p is None:
        raise BadFile(f"no trace matches: {needle}")
    entries = read_trace(p)
    if json_out:
        json.dump(entries, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        return 0
    _render_timeline(p, entries)
    return 0


def _fmt_ts(ts: str) -> str:
    try:
        return datetime.fromisoformat(ts).strftime("%H:%M:%S.%f")[:-3]
    except ValueError:
        return ts


def _render_timeline(path: Path, entries: list[dict[str, Any]]) -> None:
    print(dim(f"# {path}"))
    print(dim("-" * 60))
    t0: float | None = None
    for e in entries:
        kind = e.get("kind", "?")
        ts = e.get("ts", "")
        try:
            t = datetime.fromisoformat(ts).timestamp()
        except ValueError:
            t = 0.0
        if t0 is None:
            t0 = t
        delta = f"+{(t - t0) * 1000:>7.1f}ms"

        if kind == "header":
            print(f"  {_fmt_ts(ts)} {dim('header')}  {e.get('workflow_name', '?')}")
            print(f"  {' ' * 12} {dim('input ')}  {json.dumps(e.get('input', {}))[:120]}")
        elif kind == "event":
            t_name = e.get("type", "")
            data = e.get("data", {}) or {}
            node = data.get("node_name") or data.get("node_id") or ""
            short = _short(data)
            print(f"  {delta}  {t_name:<22} {dim(node):<24} {short}")
        elif kind == "footer":
            tag = (
                green(e.get("status", ""))
                if e.get("status") == "completed"
                else red(e.get("status", ""))
            )
            print(dim("-" * 60))
            print(f"  {tag}  in {e.get('elapsed_ms', '?')}ms")
            if e.get("output"):
                print(f"  output: {json.dumps(e['output'], default=str)[:200]}")
        elif kind == "error":
            print(f"  {delta}  {red('error')}  {e.get('message', '')}")
        else:
            print(f"  {delta}  {kind}  {json.dumps(e, default=str)[:120]}")


def _short(data: dict[str, Any]) -> str:
    for k in ("message", "status", "value", "output", "error"):
        if k in data:
            v = data[k]
            return v if isinstance(v, str) else json.dumps(v, default=str)[:80]
    return ""
