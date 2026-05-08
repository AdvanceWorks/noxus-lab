"""Local trace store for workflow runs.

Design:
- One JSONL file per run under `.noxuslab/traces/<utc-ts>_<run_id>.jsonl`.
- First line is the run header (workflow id, input, started_at).
- One line per `RunEvent` from the SDK SSE stream.
- Last line is a footer with status, output, and total wall time.

Stdlib only. No daemon. No background thread. Each line is a flush so
the file is tail-able from another terminal in real time.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TRACE_DIR = Path(".noxuslab") / "traces"

# Keys whose values must be redacted before writing to disk.
_REDACT = re.compile(r"(?i)(api[_-]?key|secret|token|password|authorization)")


def _redact(value: Any) -> Any:
    """Recursively redact secret-shaped values. Stdlib only."""
    if isinstance(value, dict):
        return {k: ("***" if _REDACT.search(k) else _redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")


def trace_path(run_id: str) -> Path:
    """Return the canonical path for a new trace file."""
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    return TRACE_DIR / f"{_ts()}_{run_id}.jsonl"


class TraceWriter:
    """Append-only JSONL writer. One line = one trace entry."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._fh = path.open("w", encoding="utf-8")

    def write(self, kind: str, **payload: Any) -> None:
        entry = {"kind": kind, "ts": datetime.now(timezone.utc).isoformat(), **_redact(payload)}
        self._fh.write(json.dumps(entry, default=str) + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> TraceWriter:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def list_traces(limit: int = 20) -> list[Path]:
    """Return the most recent trace files (newest first)."""
    if not TRACE_DIR.is_dir():
        return []
    return sorted(TRACE_DIR.glob("*.jsonl"), key=os.path.getmtime, reverse=True)[:limit]


def find_trace(needle: str) -> Path | None:
    """Resolve a trace by id, prefix, or full filename."""
    p = Path(needle)
    if p.is_file():
        return p
    if not TRACE_DIR.is_dir():
        return None
    for cand in TRACE_DIR.glob(f"*{needle}*"):
        return cand
    return None


def read_trace(path: Path) -> list[dict[str, Any]]:
    """Parse a JSONL trace into a list of entries."""
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
