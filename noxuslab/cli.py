"""`noxuslab` CLI: pull workflows from the UI into Python files; push them back.

noxuslab pull <workflow_id> [--out PATH]
noxuslab push <path/to/file.py>
noxuslab version
"""

import argparse
import importlib.util
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from noxuslab import __version__
from noxuslab.codegen import _slug, workflow_to_python

EXAMPLES_DIR = Path("examples")


def _client():
    from noxus_sdk.client import Client

    return Client(
        api_key=os.environ["NOXUS_API_KEY"],
        base_url=os.environ.get("NOXUS_BACKEND_URL"),
    )


def _next_example_path(name_slug: str) -> Path:
    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    used = []
    for p in EXAMPLES_DIR.glob("*.py"):
        m = re.match(r"^(\d{2})_", p.name)
        if m:
            used.append(int(m.group(1)))
    nxt = (max(used) + 1) if used else 1
    return EXAMPLES_DIR / f"{nxt:02d}_{name_slug}.py"


def cmd_pull(args: argparse.Namespace) -> int:
    load_dotenv()
    c = _client()
    wf = c.workflows.get(workflow_id=args.workflow_id)
    code = workflow_to_python(wf)
    out = Path(args.out) if args.out else _next_example_path(_slug(wf.name))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(code, encoding="utf-8")
    print(out)
    return 0


def cmd_push(args: argparse.Namespace) -> int:
    """Import a generated file (which builds `wf`) and save it via the SDK."""
    load_dotenv()
    path = Path(args.path).resolve()
    if not path.exists():
        print(f"not found: {path}", file=sys.stderr)
        return 2
    spec = importlib.util.spec_from_file_location("_noxuslab_pushed", path)
    if spec is None or spec.loader is None:
        print(f"cannot load: {path}", file=sys.stderr)
        return 2
    # Stop the generated file from saving itself when imported by clearing the
    # NOXUS_API_KEY temporarily — but the canonical flow is to *not* run the
    # `print(c.workflows.save(...).id)` line. So we run the file in a sandbox
    # namespace and call save ourselves.
    src = path.read_text(encoding="utf-8")
    src_no_save = re.sub(r"^\s*print\(c\.workflows\.save\([^)]*\)\.id\)\s*$", "", src, flags=re.M)
    ns: dict = {"__name__": "_noxuslab_pushed", "__file__": str(path)}
    exec(compile(src_no_save, str(path), "exec"), ns)  # noqa: S102
    wf = ns.get("wf")
    if wf is None:
        print("the file does not define a `wf` WorkflowDefinition variable", file=sys.stderr)
        return 2
    c = _client()
    saved = c.workflows.save(wf)
    print(saved.id)
    return 0


def cmd_version(_args: argparse.Namespace) -> int:
    print(__version__)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="noxuslab", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("pull", help="fetch a workflow and emit a Python file")
    pp.add_argument("workflow_id")
    pp.add_argument("--out", help="output path (default: examples/NN_<slug>.py)")
    pp.set_defaults(func=cmd_pull)

    ph = sub.add_parser("push", help="save a workflow defined in a Python file")
    ph.add_argument("path")
    ph.set_defaults(func=cmd_push)

    pv = sub.add_parser("version", help="print noxuslab version")
    pv.set_defaults(func=cmd_version)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
