"""Live sync: watch a workflow Python file and push on every save.

Polls the file's mtime in a stdlib loop (no `watchdog` dependency). When a
change is detected, runs the same code path as `noxuslab push`. Designed for
sub-second feedback during iterative workflow editing.

Press Ctrl+C to stop.
"""

import os
import re
import runpy
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from noxuslab._net import call as net_call
from noxuslab._term import dim, green, red
from noxuslab.errors import BadFile, NoxusLabError


def _client():
    from noxus_sdk.client import Client

    from noxuslab._secrets import resolve_api_key

    kwargs: dict = {"api_key": resolve_api_key()}
    url = os.environ.get("NOXUS_BACKEND_URL")
    if url:
        kwargs["base_url"] = url
    return Client(**kwargs)


def _push_once(path: Path, client) -> str:
    """Execute the file, extract `wf`, save, return new workflow id."""
    src = path.read_text(encoding="utf-8")
    src_no_save = re.sub(r"^\s*print\(c\.workflows\.save\([^)]*\)\.id\)\s*$", "", src, flags=re.M)
    tmp = path.with_suffix(".__noxuslab_watch.py")
    tmp.write_text(src_no_save, encoding="utf-8")
    try:
        ns = runpy.run_path(str(tmp), run_name="_noxuslab_watched")
    finally:
        tmp.unlink(missing_ok=True)
    wf = ns.get("wf")
    if wf is None:
        raise BadFile("the file does not define a `wf` WorkflowDefinition variable")
    return net_call(lambda: client.workflows.save(wf).id, what="watch push")


def watch(file: str, *, interval: float = 0.5) -> int:
    """Block, polling `file`'s mtime; push on change. Returns 0 on Ctrl+C."""
    path = Path(file)
    if not path.is_file():
        raise BadFile(f"not found: {path}")
    load_dotenv()
    client = _client()
    last_mtime = path.stat().st_mtime
    print(green(f"watching {path}"), dim(f"(every {interval}s; Ctrl+C to stop)"))
    try:
        # First push so the user sees current state on the server.
        wid = _push_once(path, client)
        print(dim(time.strftime("%H:%M:%S")), green("pushed"), wid)
        while True:
            time.sleep(interval)
            try:
                mt = path.stat().st_mtime
            except FileNotFoundError:
                continue
            if mt == last_mtime:
                continue
            last_mtime = mt
            t0 = time.monotonic()
            try:
                wid = _push_once(path, client)
            except (NoxusLabError, BadFile) as e:
                print(dim(time.strftime("%H:%M:%S")), red("error:"), e, file=sys.stderr)
                continue
            elapsed = int((time.monotonic() - t0) * 1000)
            print(dim(time.strftime("%H:%M:%S")), green("pushed"), wid, dim(f"({elapsed}ms)"))
    except KeyboardInterrupt:
        print()
        return 0
