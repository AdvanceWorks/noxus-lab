"""Structured audit log: one JSON line per CLI invocation.

Enable by setting one of:

    NOXUSLAB_AUDIT_LOG=/var/log/noxuslab/audit.log   # append to file
    NOXUSLAB_AUDIT=stderr                            # emit to stderr

Each record contains: ts (UTC ISO8601), user, host, cmd, args, rc,
duration_ms, version. Secrets and arbitrary strings (e.g. chat
content) are never logged — only structural metadata.

Log lines are append-only and one-per-line, suitable for shipping to
SIEM (Splunk, Datadog, ELK) via filebeat or similar.
"""

import contextlib
import getpass
import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from noxuslab import __version__

# Argv keys that may contain free-form user content. We log their
# presence, not their value.
_REDACT_POSITIONAL_FOR = {"ask", "chat"}


def _argv_summary(argv: list[str]) -> dict:
    if not argv:
        return {}
    cmd = argv[0]
    safe: dict = {"cmd": cmd}
    if cmd in _REDACT_POSITIONAL_FOR:
        # Don't log free-form questions or model strings.
        safe["redacted_positional"] = max(0, len(argv) - 1)
        return safe
    safe["argv"] = argv[1:]
    return safe


def _sink():
    path = os.environ.get("NOXUSLAB_AUDIT_LOG")
    if path:
        return Path(path).open("a", encoding="utf-8", buffering=1)  # noqa: SIM115 — caller closes
    if os.environ.get("NOXUSLAB_AUDIT") == "stderr":
        return sys.stderr
    return None


def emit(argv: list[str], rc: int, duration_ms: int) -> None:
    """Write one audit record. Silent if logging is not configured."""
    sink = _sink()
    if sink is None:
        return
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "user": getpass.getuser(),
        "host": socket.gethostname(),
        "version": __version__,
        "rc": rc,
        "duration_ms": duration_ms,
        **_argv_summary(argv),
    }
    try:
        sink.write(json.dumps(record, separators=(",", ":")) + "\n")
        sink.flush()
    except OSError:
        # Auditing must never crash the user's command.
        pass
    finally:
        if sink not in (sys.stdout, sys.stderr):
            with contextlib.suppress(OSError):
                sink.close()


def time_ms() -> int:
    return int(time.monotonic() * 1000)
