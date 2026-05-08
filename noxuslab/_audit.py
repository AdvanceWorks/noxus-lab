"""Structured audit log: one JSON line per CLI invocation.

Enable by setting one of:

    NOXUSLAB_AUDIT_LOG=/var/log/noxuslab/audit.log   # append to file
    NOXUSLAB_AUDIT_LOG=https://hooks.slack.com/...   # POST to Slack-style webhook
    NOXUSLAB_AUDIT_LOG=https://example.com/ingest    # POST JSON to any HTTPS URL
    NOXUSLAB_AUDIT=stderr                            # emit to stderr

Each record contains: ts (UTC ISO8601), user, host, cmd, args, rc,
duration_ms, version. Secrets and arbitrary strings (e.g. chat
content) are never logged — only structural metadata.

HTTPS sinks are best-effort and never block the user's command: failures
are swallowed silently. A 1 second timeout is applied. For production
shipping prefer a file sink + filebeat/fluentbit; HTTPS is for
notifications and ad-hoc integrations.
"""

import contextlib
import getpass
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from noxuslab import __version__

# Argv keys that may contain free-form user content. We log their
# presence, not their value.
_REDACT_POSITIONAL_FOR = {"ask", "chat", "gen"}


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


def _is_url(target: str) -> bool:
    return target.startswith(("http://", "https://"))


def _post_webhook(url: str, record: dict) -> None:
    """Best-effort POST. Slack URLs get `{"text": ...}`, others get the raw record."""
    if "hooks.slack.com" in url:
        body = json.dumps({"text": f"`noxuslab` {json.dumps(record)}"}).encode("utf-8")
    else:
        body = json.dumps(record).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310 — explicit user-configured URL
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with (  # noqa: S310 — explicit user-configured URL
        contextlib.suppress(urllib.error.URLError, OSError, TimeoutError),
        urllib.request.urlopen(req, timeout=1.0) as _,  # noqa: S310
    ):
        pass


def _sink():
    path = os.environ.get("NOXUSLAB_AUDIT_LOG")
    if path and not _is_url(path):
        return Path(path).open("a", encoding="utf-8", errors="replace", buffering=1)  # noqa: SIM115 — caller closes
    if os.environ.get("NOXUSLAB_AUDIT") == "stderr":
        return sys.stderr
    return None


def emit(argv: list[str], rc: int, duration_ms: int) -> None:
    """Write one audit record. Silent if logging is not configured."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "user": getpass.getuser(),
        "host": socket.gethostname(),
        "version": __version__,
        "rc": rc,
        "duration_ms": duration_ms,
        **_argv_summary(argv),
    }
    # HTTPS sink (Slack / webhook) takes precedence; file sink runs in addition.
    url = os.environ.get("NOXUSLAB_AUDIT_LOG")
    if url and _is_url(url):
        _post_webhook(url, record)
        return
    sink = _sink()
    if sink is None:
        return
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
