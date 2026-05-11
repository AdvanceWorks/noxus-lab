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
import contextlib
import difflib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from noxuslab import __version__
from noxuslab._net import call as net_call
from noxuslab._term import dim, green, red
from noxuslab._workflow import (
    LocalWorkflow,
)
from noxuslab._workflow import (
    check_uuid as _check_id,
)
from noxuslab._workflow import (
    extract_source_id as _extract_source_id,
)
from noxuslab.codegen import _slug, workflow_to_python
from noxuslab.errors import BadFile, NoxusLabError

EXAMPLES_DIR = Path("examples")


def _client():
    from noxus_sdk.client import Client

    from noxuslab._secrets import resolve_api_key

    kwargs: dict = {"api_key": resolve_api_key()}
    url = os.environ.get("NOXUS_BACKEND_URL")
    if url:
        kwargs["base_url"] = url
    return Client(**kwargs)


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
    wf = LocalWorkflow.load(args.path).execute()
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


def _scaffold_readme(project_name: str) -> str:
    return (
        f"# {project_name}\n\n"
        f"Scaffolded by `noxuslab init` (template version `{__version__}`).\n\n"
        "This is a CLI-first Noxus project. The installed `noxuslab` package "
        "provides the commands; this repo holds your `examples/`, `.env`, and local state.\n\n"
        "Set `NOXUS_API_KEY` in `.env` (or rerun `noxuslab init --interactive`), "
        "then run `noxuslab doctor` and start from a file in `examples/` or `noxuslab pull <workflow_id>`.\n\n"
        "Upgrade the CLI later with:\n\n"
        "    pip install --upgrade git+https://github.com/AdvanceWorks/noxus-lab.git\n"
    )


def cmd_init(args: argparse.Namespace) -> int:
    """Scaffold a new project under <dir> by copying examples + .env.example.

    With `--multi-process`, scaffolds the multi-process repo layout
    (shared/ + processes/<name>/) instead of the single-workflow one.

    With `--interactive` (or when stdin is a TTY), runs a short wizard that
    asks for the API key and writes a ready-to-use `.env`.
    """
    target = Path(args.dir)
    if target.exists() and any(target.iterdir()):
        raise BadFile(f"refusing to scaffold into non-empty {target}")
    target.mkdir(parents=True, exist_ok=True)

    if getattr(args, "multi_process", False):
        _scaffold_multi_process(target)
    else:
        _scaffold_single(target)

    interactive = args.interactive or (
        args.interactive is None and sys.stdin.isatty() and sys.stdout.isatty()
    )
    if interactive:
        _run_init_wizard(target)

    print(target)
    return 0


def _scaffold_single(target: Path) -> None:
    """Original single-workflow layout: examples/ + .env.example + README."""
    here = Path(__file__).resolve().parent.parent
    src_examples = here / "examples"
    if src_examples.is_dir():
        shutil.copytree(src_examples, target / "examples", dirs_exist_ok=True)
    env_tpl = here / ".env.example"
    if env_tpl.is_file():
        shutil.copy2(env_tpl, target / ".env.example")
    # Pin the template version so future tooling can diff against it.
    (target / ".noxuslab-template-version").write_text(__version__ + "\n", encoding="utf-8")
    (target / "README.md").write_text(_scaffold_readme(target.name), encoding="utf-8")


def _scaffold_multi_process(target: Path) -> None:
    """Multi-process layout: shared/ + processes/<name>/ + tests + docs.

    Copies the bundled template tree, then renders any `*.tpl` file by
    formatting it with `{project_name}` and `{version}` and removing
    the `.tpl` suffix. Same template-version marker as the single layout.
    """
    src = Path(__file__).resolve().parent / "templates" / "multi_process"
    if not src.is_dir():
        raise BadFile(
            f"multi-process template missing at {src}. Reinstall noxuslab from a complete checkout."
        )
    shutil.copytree(src, target, dirs_exist_ok=True)

    project_name = target.name
    for tpl in list(target.rglob("*.tpl")):
        rendered = tpl.read_text(encoding="utf-8").format(
            project_name=project_name,
            version=__version__,
        )
        tpl.with_suffix("").write_text(rendered, encoding="utf-8")
        tpl.unlink()

    (target / ".noxuslab-template-version").write_text(__version__ + "\n", encoding="utf-8")


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
        print(dim("wizard skipped — edit .env manually, then run `noxuslab doctor`"))
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


def _load_agent_file(path: Path) -> tuple[str, Any, str | None]:
    """Load an agent file in a stubbed namespace; return (name, settings, id?).

    The three module-level variables (`agent_name`, `agent_id`,
    `agent_settings`) are the entire contract. `settings` is typed `Any`
    because the file produces a live `ConversationSettings` instance from
    the SDK; importing the type here would make the CLI eager-import the
    SDK on every `--help`.
    """
    ns = LocalWorkflow.load(path).execute_namespace()
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

    `workflow_id` is optional when the file carries a provenance
    header (`# generated by noxuslab pull from <id> @ ...`).
    """
    path = Path(args.file)
    if not path.is_file():
        raise BadFile(f"not found: {path}")
    local_code = path.read_text(encoding="utf-8")
    workflow_id = args.workflow_id or _extract_source_id(local_code)
    if not workflow_id:
        raise BadFile(
            f"no workflow id given and no provenance header in {path}; "
            "pass <workflow_id> explicitly"
        )
    _check_id(workflow_id)
    load_dotenv()
    client = _client()
    wf = net_call(
        lambda: client.workflows.get(workflow_id=workflow_id),
        what="diff workflow",
    )
    if args.visual:
        from noxuslab.graph import to_mermaid

        local_wf = None
        with contextlib.suppress(BadFile):
            local_wf = LocalWorkflow.load(path).execute()
        print("## server")
        print(to_mermaid(wf, title=f"server:{workflow_id}"))
        print("## local")
        print(
            to_mermaid(local_wf, title=f"local:{path}")
            if local_wf is not None
            else "(no `wf` defined in local file)"
        )
        return 0
    server_code = workflow_to_python(wf, source_id=workflow_id)
    diff = list(
        difflib.unified_diff(
            server_code.splitlines(keepends=True),
            local_code.splitlines(keepends=True),
            fromfile=f"server:{workflow_id}",
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


def cmd_run(args: argparse.Namespace) -> int:
    from noxuslab.runner import run as runner_run

    load_dotenv()
    return runner_run(args.target, args.input or [], follow=not args.detach)


def cmd_replay(args: argparse.Namespace) -> int:
    """Re-run a workflow using the inputs captured in a previous trace.

    Reads the `header` line of the matching trace file, extracts
    `workflow_id` and `input`, and calls the same code path as
    `noxuslab run`. The replay produces a fresh trace; comparing the
    two traces is a one-liner with `diff` once outputs are stable.

    This is the foundation for the eval / regression-test primitives:
    once a run is replayable from its trace, every other batch behaviour
    (run N times, vary one input, compare outputs) is a script over
    `_trace.list_traces`.
    """
    from noxuslab._trace import find_trace, read_trace
    from noxuslab.runner import run as runner_run

    p = find_trace(args.run_id)
    if p is None:
        raise BadFile(f"no trace matches: {args.run_id}")
    entries = read_trace(p)
    header = next((e for e in entries if e.get("kind") == "header"), None)
    if header is None:
        raise BadFile(f"trace {p.name} has no header line")
    target = args.target or header.get("workflow_id")
    if not target:
        raise BadFile(f"trace {p.name} has no workflow_id; pass --target explicitly")
    inputs = header.get("input") or {}
    pairs = [f"{k}={json.dumps(v)}" for k, v in inputs.items()]
    print(dim(f"replay: {target}  ({len(pairs)} input(s) from {p.name})"))
    load_dotenv()
    return runner_run(target, pairs, follow=not args.detach)


def cmd_check(args: argparse.Namespace) -> int:
    """Pre-commit/PR review for a workflow file.

    Three local checks, no writes:
      1. dry-run push  (parses + validates the file; no network)
      2. diff vs server (only if file has a provenance header)
      3. last local trace summary (status, elapsed_ms) for that workflow

    Exit 0 when steps 1+2 are both clean. Exit 1 if dry-run fails or the
    server differs. Step 3 is informational and never affects exit code.
    """
    from noxuslab._trace import list_traces, read_trace

    path = Path(args.file)
    if not path.is_file():
        raise BadFile(f"not found: {path}")

    # 1. dry-run
    dry_args = argparse.Namespace(path=str(path), dry_run=True)
    print(dim("[1/3] dry-run..."))
    rc1 = cmd_push(dry_args)
    rc = rc1

    # 2. diff vs server (best-effort; only if provenance present)
    src_id = _extract_source_id(path.read_text(encoding="utf-8"))
    print(dim(f"[2/3] diff vs server ({src_id or 'no provenance — skipped'})..."))
    if src_id:
        diff_args = argparse.Namespace(workflow_id=src_id, file=str(path), visual=False)
        rc2 = cmd_diff(diff_args)
        if rc2 != 0:
            rc = 1

    # 3. last local trace summary (informational)
    print(dim("[3/3] last trace..."))
    matched = None
    for tp in list_traces(50):
        try:
            entries = read_trace(tp)
        except (OSError, ValueError):
            continue
        header = next((e for e in entries if e["kind"] == "header"), {})
        if src_id and header.get("workflow_id") != src_id:
            continue
        footer = next((e for e in entries if e["kind"] == "footer"), {})
        matched = (tp, header, footer)
        break
    if matched is None:
        print(dim("  (no local traces — run `noxuslab run` first)"))
    else:
        tp, header, footer = matched
        status = footer.get("status", "incomplete")
        elapsed = footer.get("elapsed_ms", "?")
        tag = green(status) if status == "completed" else red(status)
        print(f"  {tp.name}  {tag}  ({elapsed}ms)")

    if rc == 0:
        print(green("check ok — safe to commit / push"))
    else:
        print(red("check failed — fix the issues above before pushing"))
    return rc


def cmd_trace(args: argparse.Namespace) -> int:
    from noxuslab import trace_view

    if args.trace_cmd in (None, "list"):
        return trace_view.cmd_list(limit=args.limit if hasattr(args, "limit") else 20)
    if args.trace_cmd == "show":
        return trace_view.cmd_show(args.id, json_out=args.json)
    raise BadFile(f"unknown trace subcommand: {args.trace_cmd}")


def cmd_env(args: argparse.Namespace) -> int:
    from noxuslab import envs

    if args.env_cmd in (None, "list"):
        return envs.cmd_list()
    if args.env_cmd == "use":
        return envs.cmd_use(args.name)
    raise BadFile(f"unknown env subcommand: {args.env_cmd}")


def cmd_doctor(_args: argparse.Namespace) -> int:
    from noxuslab.doctor import doctor

    return doctor()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="noxuslab",
        description="Workflow-as-code for Noxus AI: pull from the UI, edit, run, trace, push back.",
        epilog="Run `noxuslab <command> --help` for details on each command.",
    )
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
    pi.add_argument(
        "--multi-process",
        action="store_true",
        help="scaffold a multi-process repo (shared/ + processes/<name>/) "
        "instead of the single-workflow layout",
    )
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
    pd.add_argument(
        "workflow_id",
        nargs="?",
        help="workflow UUID; optional if <file> has a provenance header",
    )
    pd.add_argument("file")
    pd.add_argument(
        "--visual",
        action="store_true",
        help="emit Mermaid graphs (server + local) instead of a text diff",
    )
    pd.set_defaults(func=cmd_diff)

    pck = sub.add_parser("check", help="safe-to-commit check: dry-run + diff + last-trace summary")
    pck.add_argument("file", help="workflow .py file (uses provenance header for diff)")
    pck.set_defaults(func=cmd_check)

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

    pr = sub.add_parser("run", help="execute a workflow (UUID or local file) with live trace")
    pr.add_argument("target", help="workflow UUID or path to a workflow .py file")
    pr.add_argument(
        "--input",
        action="append",
        metavar="K=V",
        help="input key=value (repeatable). Values are JSON-decoded; use @file for blobs",
    )
    pr.add_argument(
        "--detach",
        action="store_true",
        help="trigger and exit; don't follow events (prints run id and quits)",
    )
    pr.set_defaults(func=cmd_run)

    prp = sub.add_parser("replay", help="re-run a workflow with inputs captured in a past trace")
    prp.add_argument("run_id", help="trace id, prefix, or filename to replay")
    prp.add_argument(
        "--target",
        help="override the workflow id/file (default: same as the original run)",
    )
    prp.add_argument(
        "--detach",
        action="store_true",
        help="trigger and exit; don't follow events",
    )
    prp.set_defaults(func=cmd_replay)

    ptr = sub.add_parser("trace", help="list or inspect recorded run traces (~/.noxuslab/traces)")
    ptr_sub = ptr.add_subparsers(dest="trace_cmd", required=False)
    ptr.set_defaults(func=cmd_trace)
    ptr_list = ptr_sub.add_parser("list", help="list recent traces (newest first)")
    ptr_list.add_argument("--limit", type=int, default=20, help="max rows to show")
    ptr_list.set_defaults(func=cmd_trace)
    ptr_show = ptr_sub.add_parser("show", help="render a trace as a timeline")
    ptr_show.add_argument("id", help="run id, prefix, or full filename")
    ptr_show.add_argument("--json", action="store_true", help="emit raw JSONL entries instead")
    ptr_show.set_defaults(func=cmd_trace)

    pe = sub.add_parser("env", help="list or switch active environment (.env.<name>)")
    pe_sub = pe.add_subparsers(dest="env_cmd", required=False)
    pe.set_defaults(func=cmd_env)
    pe_sub.add_parser("list", help="list available envs (active marked with *)").set_defaults(
        func=cmd_env
    )
    pe_use = pe_sub.add_parser("use", help="switch the active env (copies .env.<name> to .env)")
    pe_use.add_argument("name", help="env name (e.g. dev, staging, prod)")
    pe_use.set_defaults(func=cmd_env)

    pdoc = sub.add_parser("doctor", help="run sanity checks on the local setup")
    pdoc.set_defaults(func=cmd_doctor)

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
