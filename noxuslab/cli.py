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
from noxuslab._term import dim, green, red
from noxuslab.codegen import _slug, workflow_to_python
from noxuslab.errors import BadFile, NoxusLabError

EXAMPLES_DIR = Path("examples")
_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _client():
    from noxus_sdk.client import Client

    from noxuslab._secrets import resolve_api_key

    kwargs: dict = {"api_key": resolve_api_key()}
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
    """Scaffold a new project under <dir> by copying examples + .env.example.

    With `--interactive` (or when stdin is a TTY), runs a short wizard that
    asks for the API key and writes a ready-to-use `.env`.
    """
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

    interactive = args.interactive or (
        args.interactive is None and sys.stdin.isatty() and sys.stdout.isatty()
    )
    if interactive:
        _run_init_wizard(target)

    print(target)
    return 0


def _run_init_wizard(target: Path) -> None:
    """First-run wizard: prompt for API key + backend URL, write `.env`.

    Stdlib only. Skips silently on EOF / KeyboardInterrupt — scaffold is
    already on disk; the user can re-run setup later.
    """
    import getpass

    print()
    print(dim(f"setting up {target.name}..."))
    print(dim("press Enter to skip a question; Ctrl+C to abort the wizard"))
    try:
        key = getpass.getpass("noxus api key (hidden): ").strip()
        url = input("backend url [https://backend.noxus.ai]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        print(dim("wizard skipped — edit .env manually before `make setup`"))
        return

    lines = []
    if key:
        lines.append(f"NOXUS_API_KEY={key}")
    if url:
        lines.append(f"NOXUS_BACKEND_URL={url}")
    if lines:
        env = target / ".env"
        env.write_text("\n".join(lines) + "\n", encoding="utf-8")
        import contextlib

        with contextlib.suppress(OSError):
            env.chmod(0o600)  # Windows / FS without chmod silently ignored
        print(green(f"wrote {env} (chmod 600)"))
    else:
        print(dim("no values entered — .env not created"))


def cmd_agents(_args: argparse.Namespace) -> int:
    load_dotenv()
    client = _client()
    for a in net_call(lambda: list(client.agents.list()), what="list agents"):
        print(f"{a.id}  {a.name}")
    return 0


def _next_agent_path(name_slug: str) -> Path:
    """Mirror `_next_example_path` for agents under `agents/`."""
    out_dir = Path("agents")
    out_dir.mkdir(parents=True, exist_ok=True)
    used = [int(m.group(1)) for p in out_dir.glob("*.py") if (m := re.match(r"^(\d{2})_", p.name))]
    nxt = (max(used) + 1) if used else 1
    return out_dir / f"{nxt:02d}_{name_slug}.py"


def cmd_agents_list(_args: argparse.Namespace) -> int:
    return cmd_agents(_args)


def cmd_agents_pull(args: argparse.Namespace) -> int:
    """Fetch one agent and emit a self-contained Python file."""
    from noxuslab.agent_codegen import agent_to_python

    load_dotenv()
    client = _client()
    agent = net_call(lambda: client.agents.get(args.agent_id), what="pull agent")
    code = agent_to_python(agent, source_id=args.agent_id)
    if args.out == "-":
        sys.stdout.write(code)
        return 0
    out = Path(args.out) if args.out else _next_agent_path(_slug(agent.name))
    if out.exists() and not args.force:
        raise BadFile(f"refusing to overwrite {out} (use --force)")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(code, encoding="utf-8")
    print(out)
    return 0


def _load_agent_file(path: Path) -> tuple[str, object, str | None]:
    """Run an agent file with `Client` stubbed; return (name, settings, id?).

    Stubbing means we never make an HTTP call during the load — only the
    three module-level variables matter.
    """
    if not path.is_file():
        raise BadFile(f"not found: {path}")

    import noxus_sdk.client as _sdk_client

    real_client = _sdk_client.Client

    class _StubClient:
        def __init__(self, *_a, **_k) -> None:
            self.nodes = []
            self.agents = self
            self.workflows = self

        def __getattr__(self, _name):
            return lambda *a, **k: None

    _sdk_client.Client = _StubClient  # type: ignore[assignment]
    try:
        ns = runpy.run_path(str(path), run_name="_noxuslab_agent_push")
    finally:
        _sdk_client.Client = real_client  # type: ignore[assignment]

    name = ns.get("agent_name")
    settings = ns.get("agent_settings")
    agent_id = ns.get("agent_id") or None
    if not isinstance(name, str) or not name:
        raise BadFile(f"{path}: missing or empty `agent_name`")
    if settings is None:
        raise BadFile(f"{path}: missing `agent_settings` (ConversationSettings instance)")
    return name, settings, agent_id


def cmd_agents_push(args: argparse.Namespace) -> int:
    """Create or update an agent from a Python file."""
    load_dotenv()
    path = Path(args.path)
    name, settings, agent_id = _load_agent_file(path)
    if args.dry_run:
        n_tools = len(getattr(settings, "tools", []) or [])
        kind = "update" if agent_id else "create"
        print(f"ok: would {kind} '{name}' with {n_tools} tool(s)")
        return 0
    client = _client()
    if agent_id:
        result_id = net_call(
            lambda: client.agents.update(agent_id, name=name, settings=settings).id,
            what="update agent",
        )
    else:
        result_id = net_call(
            lambda: client.agents.create(name, settings).id,
            what="create agent",
        )
    print(result_id)
    return 0


def cmd_agents_diff(args: argparse.Namespace) -> int:
    """Diff a local agent file against the server state. Exit 1 on diff."""
    from noxuslab.agent_codegen import agent_to_python

    path = Path(args.file)
    if not path.is_file():
        raise BadFile(f"not found: {path}")
    _check_id(args.agent_id)
    load_dotenv()
    client = _client()
    agent = net_call(lambda: client.agents.get(args.agent_id), what="diff agent")
    server_code = agent_to_python(agent, source_id=args.agent_id)
    local_code = path.read_text(encoding="utf-8")
    diff = list(
        difflib.unified_diff(
            server_code.splitlines(keepends=True),
            local_code.splitlines(keepends=True),
            fromfile=f"server:{args.agent_id}",
            tofile=f"local:{path}",
            n=3,
        )
    )
    if not diff:
        print("identical")
        return 0
    sys.stdout.writelines(diff)
    return 1


def cmd_agents_delete(args: argparse.Namespace) -> int:
    """Delete an agent on the server. Requires `--yes` (destructive)."""
    _check_id(args.agent_id)
    if not args.yes:
        raise BadFile("refusing to delete without --yes (this is destructive)")
    load_dotenv()
    client = _client()
    net_call(lambda: client.agents.delete(args.agent_id), what="delete agent")
    print(f"deleted {args.agent_id}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    """Show what `noxuslab push <file>` would change on the server.

    Pulls the current server state for the workflow, generates the
    canonical Python form, and unified-diffs it against `<file>`.
    Exits 0 if no differences, 1 if differences exist.

    With `--visual`, emits two side-by-side Mermaid graphs (server vs
    local) instead of a unified text diff.
    """
    path = Path(args.file)
    if not path.is_file():
        raise BadFile(f"not found: {path}")
    _check_id(args.workflow_id)
    load_dotenv()
    client = _client()
    wf = net_call(
        lambda: client.workflows.get(workflow_id=args.workflow_id),
        what="diff workflow",
    )
    if args.visual:
        from noxuslab.graph import to_mermaid

        local_ns = runpy.run_path(str(path), run_name="_noxuslab_visual")
        local_wf = local_ns.get("wf")
        print("## server")
        print(to_mermaid(wf, title=f"server:{args.workflow_id}"))
        print("## local")
        print(
            to_mermaid(local_wf, title=f"local:{path}")
            if local_wf is not None
            else "(no `wf` defined in local file)"
        )
        return 0
    server_code = workflow_to_python(wf, source_id=args.workflow_id)
    local_code = path.read_text(encoding="utf-8")
    diff = list(
        difflib.unified_diff(
            server_code.splitlines(keepends=True),
            local_code.splitlines(keepends=True),
            fromfile=f"server:{args.workflow_id}",
            tofile=f"local:{path}",
            n=3,
        )
    )
    if not diff:
        print("identical")
        return 0
    sys.stdout.writelines(diff)
    return 1


def cmd_chat(args: argparse.Namespace) -> int:
    from noxuslab.chat import start_chat

    return start_chat(agent_id=args.agent, model=args.model)


def cmd_ask(args: argparse.Namespace) -> int:
    from noxuslab.chat import one_shot

    question = " ".join(args.question) if args.question else sys.stdin.read().strip()
    if not question:
        raise NoxusLabError("no question provided")
    return one_shot(question, agent_id=args.agent, model=args.model)


def cmd_mcp_serve(args: argparse.Namespace) -> int:
    """Run the noxuslab MCP server. Blocks forever (stdio loop)."""
    try:
        from noxuslab.mcp import serve
    except ImportError as e:
        raise NoxusLabError("mcp extras not installed. Run: pip install 'noxuslab[mcp]'") from e
    serve(transport=args.transport)
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    from noxuslab.watch import watch

    return watch(args.file, interval=args.interval)


def cmd_gen(args: argparse.Namespace) -> int:
    from noxuslab.gen import generate

    prompt = " ".join(args.prompt) if args.prompt else sys.stdin.read().strip()
    return generate(prompt, agent_id=args.agent, model=args.model, out=args.out)


def cmd_fmt(args: argparse.Namespace) -> int:
    from noxuslab.fmt import fmt

    return fmt(args.files, check=args.check, show_diff=args.diff)


def cmd_portal(args: argparse.Namespace) -> int:
    from noxuslab.portal import serve as portal_serve

    return portal_serve(host=args.host, port=args.port, open_browser=not args.no_open)


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
    pi.add_argument(
        "--interactive",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="force/disable wizard; default = on when stdin is a TTY",
    )
    pi.set_defaults(func=cmd_init)

    pag = sub.add_parser(
        "agents",
        help="manage Noxus agents (list / pull / push / diff / delete)",
    )
    pag.set_defaults(func=cmd_agents)  # bare `noxuslab agents` = list
    pag_sub = pag.add_subparsers(dest="agents_cmd", required=False)

    pag_sub.add_parser("list", help="list agents in the workspace").set_defaults(
        func=cmd_agents_list
    )

    pag_pull = pag_sub.add_parser("pull", help="fetch an agent and emit a Python file")
    pag_pull.add_argument("agent_id")
    pag_pull.add_argument("-o", "--out", help="output path; '-' for stdout")
    pag_pull.add_argument("-f", "--force", action="store_true", help="overwrite existing file")
    pag_pull.set_defaults(func=cmd_agents_pull)

    pag_push = pag_sub.add_parser("push", help="create or update an agent from a Python file")
    pag_push.add_argument("path")
    pag_push.add_argument("--dry-run", action="store_true", help="parse + validate, don't save")
    pag_push.set_defaults(func=cmd_agents_push)

    pag_diff = pag_sub.add_parser("diff", help="diff a local agent file vs the server")
    pag_diff.add_argument("agent_id")
    pag_diff.add_argument("file")
    pag_diff.set_defaults(func=cmd_agents_diff)

    pag_del = pag_sub.add_parser("delete", help="delete an agent on the server")
    pag_del.add_argument("agent_id")
    pag_del.add_argument("--yes", action="store_true", help="confirm destructive delete")
    pag_del.set_defaults(func=cmd_agents_delete)

    pd = sub.add_parser("diff", help="show what `push <file>` would change")
    pd.add_argument("workflow_id")
    pd.add_argument("file")
    pd.add_argument(
        "--visual",
        action="store_true",
        help="emit Mermaid graphs (server + local) instead of a text diff",
    )
    pd.set_defaults(func=cmd_diff)

    pc = sub.add_parser("chat", help="interactive conversation with a Noxus agent")
    pc.add_argument("-a", "--agent", help="agent id to attach to")
    pc.add_argument("-m", "--model", help="model name (default: gemini-2.5-flash)")
    pc.set_defaults(func=cmd_chat)

    pa = sub.add_parser("ask", help="one-shot question (pipe-friendly)")
    pa.add_argument("question", nargs="*", help="question text (or pipe via stdin)")
    pa.add_argument("-a", "--agent", help="agent id to attach to")
    pa.add_argument("-m", "--model", help="model name (default: gemini-2.5-flash)")
    pa.set_defaults(func=cmd_ask)

    pm = sub.add_parser(
        "mcp", help="run noxuslab as an MCP server (Claude Desktop, Cursor, VS Code)"
    )
    pm_sub = pm.add_subparsers(dest="mcp_cmd", required=True)
    pm_serve = pm_sub.add_parser("serve", help="start the MCP server")
    pm_serve.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "sse"],
        help="transport (default: stdio)",
    )
    pm_serve.set_defaults(func=cmd_mcp_serve)

    pw = sub.add_parser("watch", help="hot-push a workflow file on every save")
    pw.add_argument("file", help="path to a workflow .py file")
    pw.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="poll interval in seconds (default 0.5)",
    )
    pw.set_defaults(func=cmd_watch)

    pg = sub.add_parser("gen", help="generate a workflow Python file from a prompt")
    pg.add_argument("prompt", nargs="*", help="natural-language description (or pipe via stdin)")
    pg.add_argument("-a", "--agent", help="agent id (use a workflow-aware agent for best results)")
    pg.add_argument("-m", "--model", help="model name (default: gemini-2.5-flash)")
    pg.add_argument("-o", "--out", help="output path (default: examples/NN_<slug>.py)")
    pg.set_defaults(func=cmd_gen)

    pf = sub.add_parser("fmt", help="canonicalise a workflow file (round-trip through codegen)")
    pf.add_argument("files", nargs="+", help="one or more .py files")
    pf.add_argument("--check", action="store_true", help="exit 1 if any file would be reformatted")
    pf.add_argument("--diff", action="store_true", help="print unified diff, do not write")
    pf.set_defaults(func=cmd_fmt)

    pp_portal = sub.add_parser("portal", help="start a local read-only HTML dashboard on 127.0.0.1")
    pp_portal.add_argument("--host", default="127.0.0.1", help="loopback address (127.0.0.1 only)")
    pp_portal.add_argument("--port", type=int, default=7890, help="TCP port (default 7890)")
    pp_portal.add_argument("--no-open", action="store_true", help="don't auto-open the browser")
    pp_portal.set_defaults(func=cmd_portal)

    known = {a.dest for a in sub._choices_actions}  # type: ignore[attr-defined]
    if argv and argv[0] not in known and not argv[0].startswith("-"):
        guess = difflib.get_close_matches(argv[0], known, n=1)
        if guess:
            print(
                red(f"unknown command: {argv[0]}"),
                dim(f"(did you mean '{guess[0]}'?)"),
                file=sys.stderr,
            )
            sys.exit(2)

    args = p.parse_args(argv)
    from noxuslab._audit import emit, time_ms

    started = time_ms()
    rc = 1
    try:
        rc = args.func(args)
        return rc  # noqa: RET504 — rc captured for the finally audit emit
    except NoxusLabError as e:
        print(f"error: {e}", file=sys.stderr)
        rc = 1
        return rc  # noqa: RET504 — rc captured for the finally audit emit
    finally:
        emit(argv or sys.argv[1:], rc, time_ms() - started)


if __name__ == "__main__":
    raise SystemExit(main())
