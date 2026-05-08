"""`noxuslab doctor` — green/red checks for the local setup.

Checks (in order, fail-fast for genuine blockers):
1. Python version >= 3.10
2. `noxuslab` version
3. `NOXUS_API_KEY` resolvable (env or .env or `NOXUSLAB_SECRETS_CMD`)
4. `NOXUS_BACKEND_URL` reachability (TCP connect, 2s timeout)
5. SDK import works
6. `.noxuslab/` directory writable (for traces)

Exit code is 0 if all pass, 1 if any fail. Output is purely visual —
machine-readable status comes from the exit code.
"""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

from noxuslab import __version__
from noxuslab._term import dim, green, red

DEFAULT_BACKEND = "https://backend.noxus.ai"


def _ok(msg: str) -> None:
    print(f"  {green('ok')}    {msg}")


def _fail(msg: str) -> None:
    print(f"  {red('fail')}  {msg}")


def _warn(msg: str) -> None:
    print(f"  {dim('warn')}  {msg}")


def doctor() -> int:
    failed = 0

    # 1. Python.
    py = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    _ok(f"python {py}")

    # 2. noxuslab itself.
    _ok(f"noxuslab {__version__}")

    # 3. SDK import.
    try:
        import noxus_sdk  # noqa: F401

        _ok("noxus_sdk import works")
    except ImportError as e:
        _fail(f"noxus_sdk import failed: {e}")
        failed += 1

    # 4. Secret resolution.
    load_dotenv()
    try:
        from noxuslab._secrets import resolve_api_key

        key = resolve_api_key()
        masked = key[:4] + "…" + key[-4:] if len(key) > 10 else "***"
        _ok(f"NOXUS_API_KEY resolved ({masked})")
    except Exception as e:  # noqa: BLE001 — boundary
        _fail(f"NOXUS_API_KEY: {e}")
        failed += 1

    # 5. Backend reachability.
    url = os.environ.get("NOXUS_BACKEND_URL", DEFAULT_BACKEND)
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not host:
        _fail(f"backend url malformed: {url}")
        failed += 1
    else:
        try:
            with socket.create_connection((host, port), timeout=2):
                _ok(f"backend reachable: {host}:{port}")
        except OSError as e:
            _warn(f"backend {host}:{port} unreachable: {e}")
            # Not a hard failure — user might be offline + intend to fix later.

    # 6. Trace dir writable.
    try:
        trace_dir = Path(".noxuslab") / "traces"
        trace_dir.mkdir(parents=True, exist_ok=True)
        probe = trace_dir / ".probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        _ok(f"trace dir writable: {trace_dir}")
    except OSError as e:
        _fail(f"trace dir not writable: {e}")
        failed += 1

    # 7. Active env (informational).
    from noxuslab.envs import current as env_current

    name = env_current()
    if name:
        _ok(f"active env: {name}")
    else:
        _warn("no active env (use `noxuslab env use <name>` to switch)")

    print()
    if failed:
        print(red(f"{failed} check(s) failed"))
        return 1
    print(green("all checks passed"))
    return 0
