"""`noxuslab env` — switch between `.env.<name>` files.

Convention:
- `.env.dev`, `.env.staging`, `.env.prod` live in the repo root.
- The active one is symlinked (or copied on Windows) to `.env`.
- `.noxuslab/active-env` records the name for `noxuslab env` (no args).
- `.env` is gitignored; the per-environment files SHOULD be too unless
  you explicitly opt in to committing non-secret defaults.

Stdlib only. No mutation of process env at runtime — `load_dotenv()`
calls in the rest of the CLI pick up `.env` on next invocation.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from noxuslab._term import dim, green
from noxuslab.errors import BadFile

STATE_DIR = Path(".noxuslab")
STATE_FILE = STATE_DIR / "active-env"


def _candidates() -> list[str]:
    return sorted(p.name.removeprefix(".env.") for p in Path().glob(".env.*"))


def current() -> str | None:
    if STATE_FILE.is_file():
        return STATE_FILE.read_text(encoding="utf-8").strip() or None
    return None


def cmd_list() -> int:
    names = _candidates()
    if not names:
        print(dim("no .env.<name> files found — create one (e.g. .env.dev) to use envs"))
        return 0
    active = current()
    for n in names:
        marker = green("*") if n == active else " "
        print(f"  {marker} {n}")
    return 0


def cmd_use(name: str) -> int:
    src = Path(f".env.{name}")
    if not src.is_file():
        avail = ", ".join(_candidates()) or "(none)"
        raise BadFile(f"no such env file: {src} (available: {avail})")
    dst = Path(".env")
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    # Copy, not symlink: works on Windows without admin and avoids
    # accidental edits leaking back into the source.
    shutil.copy2(src, dst)
    STATE_DIR.mkdir(exist_ok=True)
    STATE_FILE.write_text(name + "\n", encoding="utf-8")
    print(green(f"using {name} ({src} → .env)"))
    return 0
