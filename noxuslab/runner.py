"""`noxuslab run <file> --input k=v` — execute a workflow + record trace.

Two paths:
- File path: load the local workflow file, push it (saving), then run.
- UUID: run a workflow that already exists on the server.

Inputs are parsed as `key=value`. Values are JSON-decoded if they parse;
otherwise treated as plain strings. Use `@file.json` to load a value
from disk (escape hatch for blobs).
"""

from __future__ import annotations

import contextlib
import json
import sys
import time
from pathlib import Path
from typing import Any

from noxuslab._net import call as net_call
from noxuslab._term import dim, green, red
from noxuslab._trace import TraceWriter, trace_path
from noxuslab.errors import BadFile


def _parse_input(pairs: list[str]) -> dict[str, Any]:
    """Parse `k=v` pairs. JSON-decode values when possible. `@file` loads JSON."""
    out: dict[str, Any] = {}
    for raw in pairs or []:
        if "=" not in raw:
            raise BadFile(f"--input must be key=value, got {raw!r}")
        k, v = raw.split("=", 1)
        if v.startswith("@"):
            out[k] = json.loads(Path(v[1:]).read_text(encoding="utf-8"))
            continue
        try:
            out[k] = json.loads(v)
        except (ValueError, json.JSONDecodeError):
            out[k] = v
    return out


def _load_or_push(client: Any, target: str) -> Any:
    """If `target` is a UUID, fetch it; if a file, push it then return the wf."""
    from noxuslab._workflow import LocalWorkflow, is_uuid

    if is_uuid(target):
        return net_call(lambda: client.workflows.get(workflow_id=target), what="fetch workflow")
    wf_local = LocalWorkflow.load(target).execute()
    return net_call(lambda: client.workflows.save(wf_local), what="save workflow")


def run(target: str, inputs: list[str], *, follow: bool = True) -> int:
    """Execute a workflow and stream events to stdout + a JSONL trace.

    Returns 0 on success, 1 on failure. Always writes a trace file even
    on error so the user has something to inspect.
    """
    from noxuslab.cli import _client  # lazy: avoids circular import

    body = _parse_input(inputs)
    client = _client()
    wf = _load_or_push(client, target)

    started = time.time()
    run_obj = net_call(lambda: wf.run(body), what="trigger run")
    tp = trace_path(run_obj.id)
    print(dim(f"trace: {tp}"))
    print(dim(f"run id: {run_obj.id}"))

    rc = 0
    with TraceWriter(tp) as tw:
        tw.write(
            "header",
            workflow_id=str(wf.id),
            workflow_name=getattr(wf, "name", None),
            run_id=run_obj.id,
            input=body,
        )
        if not follow:
            print(run_obj.id)
            tw.write("note", message="follow=false; client detached")
            return 0

        try:
            for ev in run_obj.stream():
                tw.write("event", type=ev.type, data=ev.data)
                _print_event(ev)
                if ev.is_terminal:
                    break
        except KeyboardInterrupt:
            print()
            print(dim("detached — run continues on the server"))
            tw.write("note", message="client detached via KeyboardInterrupt")
            return 0
        except Exception as e:  # noqa: BLE001 — boundary
            tw.write("error", message=str(e))
            print(red(f"stream error: {e}"))
            rc = 1

        # Final refresh + footer.
        with contextlib.suppress(Exception):
            run_obj.refresh()
        elapsed = time.time() - started
        tw.write(
            "footer",
            status=run_obj.status,
            output=run_obj.output,
            elapsed_ms=int(elapsed * 1000),
        )

    if run_obj.status == "completed":
        print(green(f"completed in {elapsed:.2f}s"))
        if run_obj.output:
            json.dump(run_obj.output, sys.stdout, indent=2, default=str)
            sys.stdout.write("\n")
        return rc
    print(red(f"status: {run_obj.status} (after {elapsed:.2f}s)"))
    return 1


def _print_event(ev: Any) -> None:
    """Render one SSE event as a single human line."""
    name = getattr(ev, "type", "event")
    data = getattr(ev, "data", {}) or {}
    node = data.get("node_name") or data.get("node_id") or ""
    short = ""
    for key in ("status", "message", "value", "output", "error"):
        if key in data:
            v = data[key]
            short = v if isinstance(v, str) else json.dumps(v, default=str)[:80]
            break
    line = f"  {name:<22}"
    if node:
        line += f" {dim(node)} "
    if short:
        line += f" {short}"
    print(line)
