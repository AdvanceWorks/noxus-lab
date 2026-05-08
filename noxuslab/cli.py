"""`noxuslab` CLI: pull workflows from the UI into Python files; push them back.

    noxuslab pull <workflow_id> [--out PATH | -o -] [--force]
    noxuslab push <path/to/file.py> [--dry-run]
    noxuslab list
    noxuslab agents
    noxuslab show <workflow_id>
    noxuslab chat [--agent <id>] [--model <name>]
    noxuslab ask <question> [--agent <id>] [--model <name>]
    noxuslab version
    noxuslab --version | -V

`-` as `--out` means stdout. `--dry-run` parses + validates without saving.
"""

import argparse
import difflib
import os
import re
import runpy
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

from noxuslab import __version__
from noxuslab._net import call as net_call
from noxuslab._term import dim, red
from noxuslab.codegen import _slug, workflow_to_python
from noxuslab.errors import BadFile, NoxusLabError

EXAMPLES_DIR = Path("examples")
_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _client():
    from noxus_sdk.client import Client

    kwargs: dict = {"api_key": os.environ["NOXUS_API_KEY"]}
    url = os.environ.get("NOXUS_BACKEND_URL")
    if url:
        kwargs["base_url"] = url
    return Client(**kwargs)


def _check_id(wid: str) -> None:
    if not _UUID.match(wid.lower()):
        raise NoxusLabError(f"not a uuid: {wid}")


def _next_example_path(name_slug: str) -> Path:
    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    used = [
        int(m.group(1)) for p in EXAMPLES_DIR.glob("*.py") if (m := re.match(r"^(\d{2})_", p.name))
    ]
    nxt = (max(used) + 1) if used else 1
    return EXAMPLES_DIR / f"{nxt:02d}_{name_slug}.py"


def cmd_pull(args: argparse.Namespace) -> int:
    _check_id(args.workflow_id)
    load_dotenv()
    client = _client()
    wf = net_call(lambda: client.workflows.get(workflow_id=args.workflow_id), what="pull workflow")
    code = workflow_to_python(wf, source_id=args.workflow_id)
    if args.out == "-":
        sys.stdout.write(code)
        return 0
    out = Path(args.out) if args.out else _next_example_path(_slug(wf.name))
    if out.exists() and not args.force:
        raise BadFile(f"refusing to overwrite {out} (use --force)")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(code, encoding="utf-8")
    print(out)
    return 0


def cmd_push(args: argparse.Namespace) -> int:
    """Run a generated file in a fresh namespace; expect `wf` to be defined."""
    load_dotenv()
    path = Path(args.path)
    if not path.is_file():
        raise BadFile(f"not found: {path}")
    src = path.read_text(encoding="utf-8")
    src_no_save = re.sub(r"^\s*print\(c\.workflows\.save\([^)]*\)\.id\)\s*$", "", src, flags=re.M)
    tmp = path.with_suffix(".__noxuslab_push.py")
    tmp.write_text(src_no_save, encoding="utf-8")
    try:
        ns = runpy.run_path(str(tmp), run_name="_noxuslab_pushed")
    finally:
        tmp.unlink(missing_ok=True)
    wf = ns.get("wf")
    if wf is None:
        raise BadFile("the file does not define a `wf` WorkflowDefinition variable")
    if args.dry_run:
        nodes = len(getattr(wf, "nodes", []) or [])
        edges = len(getattr(wf, "edges", []) or [])
        print(f"ok: {nodes} nodes, {edges} edges")
        return 0
    client = _client()
    print(net_call(lambda: client.workflows.save(wf).id, what="push workflow"))
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    load_dotenv()
    client = _client()
    for w in net_call(lambda: list(client.workflows.list()), what="list workflows"):
        print(f"{w.id}  {w.name}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    import json

    _check_id(args.workflow_id)
    load_dotenv()
    client = _client()
    wf = net_call(lambda: client.workflows.get(workflow_id=args.workflow_id), what="show workflow")
    json.dump(wf.to_noxus(), sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


def cmd_version(_args: argparse.Namespace) -> int:
    print(__version__)
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """Scaffold a new project under <dir> by copying examples + .env.example."""
    target = Path(args.dir)
    if target.exists() and any(target.iterdir()):
        raise BadFile(f"refusing to scaffold into non-empty {target}")
    target.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).resolve().parent.parent
    src_examples = here / "examples"
    if src_examples.is_dir():
        shutil.copytree(src_examples, target / "examples", dirs_exist_ok=True)
    env_tpl = here / ".env.example"
    if env_tpl.is_file():
        shutil.copy2(env_tpl, target / ".env.example")
    if args.with_makefile:
        for name in ("Makefile", "bin"):
            src = here / name
            if src.is_file():
                shutil.copy2(src, target / name)
            elif src.is_dir():
                shutil.copytree(src, target / name, dirs_exist_ok=True)
    # Pin the template version so `make template-update` can diff against it.
    (target / ".noxuslab-template-version").write_text(__version__ + "\n", encoding="utf-8")
    (target / "README.md").write_text(
        f"# {target.name}\n\nScaffolded by `noxuslab init` "
        f"(template version `{__version__}`). "
        "Copy `.env.example` to `.env`, set `NOXUS_API_KEY`, then run "
        "`make setup` and `make help`.\n",
        encoding="utf-8",
    )
    print(target)
    return 0


def cmd_agents(_args: argparse.Namespace) -> int:
    load_dotenv()
    client = _client()
    for a in net_call(lambda: list(client.agents.list()), what="list agents"):
        print(f"{a.id}  {a.name}")
    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    from noxuslab.chat import start_chat

    return start_chat(agent_id=args.agent, model=args.model)


def cmd_ask(args: argparse.Namespace) -> int:
    from noxuslab.chat import one_shot

    question = " ".join(args.question) if args.question else sys.stdin.read().strip()
    if not question:
        raise NoxusLabError("no question provided")
    return one_shot(question, agent_id=args.agent, model=args.model)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="noxuslab", description=__doc__)
    p.add_argument("-V", "--version", action="version", version=f"noxuslab {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("pull", help="fetch a workflow and emit a Python file")
    pp.add_argument("workflow_id")
    pp.add_argument("-o", "--out", help="output path; '-' for stdout")
    pp.add_argument("-f", "--force", action="store_true", help="overwrite existing file")
    pp.set_defaults(func=cmd_pull)

    ph = sub.add_parser("push", help="save a workflow defined in a Python file")
    ph.add_argument("path")
    ph.add_argument("--dry-run", action="store_true", help="parse + validate, don't save")
    ph.set_defaults(func=cmd_push)

    sub.add_parser("list", help="list workflows in the workspace").set_defaults(func=cmd_list)

    ps = sub.add_parser("show", help="dump a workflow as JSON")
    ps.add_argument("workflow_id")
    ps.set_defaults(func=cmd_show)

    sub.add_parser("version", help="print noxuslab version").set_defaults(func=cmd_version)

    pi = sub.add_parser("init", help="scaffold a new project from this template")
    pi.add_argument("dir", help="target directory (must be empty or new)")
    pi.add_argument("--with-makefile", action="store_true", help="also copy Makefile + bin/")
    pi.set_defaults(func=cmd_init)

    sub.add_parser("agents", help="list agents in the workspace").set_defaults(func=cmd_agents)

    pc = sub.add_parser("chat", help="interactive conversation with a Noxus agent")
    pc.add_argument("-a", "--agent", help="agent id to attach to")
    pc.add_argument("-m", "--model", help="model name (default: gemini-2.5-flash)")
    pc.set_defaults(func=cmd_chat)

    pa = sub.add_parser("ask", help="one-shot question (pipe-friendly)")
    pa.add_argument("question", nargs="*", help="question text (or pipe via stdin)")
    pa.add_argument("-a", "--agent", help="agent id to attach to")
    pa.add_argument("-m", "--model", help="model name (default: gemini-2.5-flash)")
    pa.set_defaults(func=cmd_ask)

    known = {a.dest for a in sub._choices_actions}  # type: ignore[attr-defined]
    if argv and argv[0] not in known and not argv[0].startswith("-"):
        guess = difflib.get_close_matches(argv[0], known, n=1)
        if guess:
            print(
                red(f"unknown command: {argv[0]}"),
                dim(f"(did you mean '{guess[0]}'?)"),
                file=sys.stderr,
            )

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except NoxusLabError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
