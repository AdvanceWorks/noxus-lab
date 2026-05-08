"""Local read-only dashboard for the workspace.

`noxuslab portal` starts a stdlib HTTP server on localhost. Open the printed
URL in any browser. Three pages:

- `/`           — overview (counts + links)
- `/workflows`  — list of workflows (id, name, copy-id button)
- `/agents`     — list of agents (id, name, copy-id button)

Stdlib only (`http.server`, `socketserver`, `html`). No FastAPI, no React,
no build step. The server is read-only — it never mutates platform state.
By design it binds to `127.0.0.1` only so it cannot be reached from the
network.

Stop with Ctrl+C.
"""

import contextlib
import html
import os
import socketserver
import webbrowser
from http.server import BaseHTTPRequestHandler

from dotenv import load_dotenv

from noxuslab._net import call as net_call
from noxuslab._term import dim, green

_CSS = """\
* { box-sizing: border-box }
body { font: 14px/1.5 -apple-system, system-ui, sans-serif; max-width: 960px;
  margin: 2rem auto; padding: 0 1rem; color: #222; background: #fafafa }
h1 { font-size: 1.4rem; margin-bottom: 0 }
h1 a { color: inherit; text-decoration: none }
nav { margin: .5rem 0 1.5rem; color: #666 }
nav a { color: #06c; margin-right: 1rem; text-decoration: none }
nav a:hover { text-decoration: underline }
table { width: 100%; border-collapse: collapse; background: #fff;
  border: 1px solid #e5e5e5; border-radius: 6px; overflow: hidden }
th, td { padding: .55rem .8rem; text-align: left; border-bottom: 1px solid #f0f0f0 }
th { background: #f6f6f6; font-weight: 600 }
tr:last-child td { border-bottom: none }
code.id { font: 12px ui-monospace, monospace; color: #555 }
button { font: 12px ui-monospace, monospace; padding: .2rem .5rem;
  border: 1px solid #ccc; background: #fff; border-radius: 4px; cursor: pointer }
button:hover { background: #f0f0f0 }
.empty { color: #888; font-style: italic; padding: 1rem }
footer { margin-top: 2rem; color: #888; font-size: 12px }
"""

_JS = """\
function copy(id){navigator.clipboard.writeText(id).then(
 ()=>{event.target.textContent='copied';
 setTimeout(()=>event.target.textContent='copy',1200)})}
"""


def _shell(title: str, body: str) -> bytes:
    page = (
        "<!doctype html><html><head><meta charset=utf-8>"
        f"<title>{html.escape(title)} · noxuslab portal</title>"
        f"<style>{_CSS}</style></head><body>"
        '<h1><a href="/">noxuslab portal</a></h1>'
        '<nav><a href="/">overview</a> <a href="/workflows">workflows</a>'
        ' <a href="/agents">agents</a></nav>'
        f"{body}"
        "<footer>read-only · 127.0.0.1 only · Ctrl+C in terminal to stop</footer>"
        f"<script>{_JS}</script></body></html>"
    )
    return page.encode("utf-8")


def _client():
    from noxus_sdk.client import Client

    from noxuslab._secrets import resolve_api_key

    kwargs: dict = {"api_key": resolve_api_key()}
    url = os.environ.get("NOXUS_BACKEND_URL")
    if url:
        kwargs["base_url"] = url
    return Client(**kwargs)


def _table(rows: list[tuple[str, str]], kind: str) -> str:
    if not rows:
        return f"<div class=empty>no {kind} in this workspace</div>"
    body = ["<table><thead><tr><th>name</th><th>id</th><th></th></tr></thead><tbody>"]
    for rid, name in rows:
        rid_e = html.escape(rid)
        name_e = html.escape(name or "(unnamed)")
        body.append(
            f"<tr><td>{name_e}</td><td><code class=id>{rid_e}</code></td>"
            f'<td><button onclick="copy({rid_e!r})">copy</button></td></tr>'
        )
    body.append("</tbody></table>")
    return "".join(body)


def _overview(n_wf: int, n_ag: int) -> str:
    return (
        f"<p>connected. <b>{n_wf}</b> workflows, <b>{n_ag}</b> agents.</p>"
        '<p>browse <a href="/workflows">workflows</a> or '
        '<a href="/agents">agents</a> to copy ids for the CLI.</p>'
    )


def _make_handler(client):
    """Build a handler class closed over the SDK client (one client per run)."""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):  # silence default access log
            return

        def do_GET(self):  # noqa: N802 — http.server convention
            try:
                if self.path in ("/", "/index.html"):
                    wfs = list(net_call(lambda: client.workflows.list(), what="portal/list-wf"))
                    ags = list(net_call(lambda: client.agents.list(), what="portal/list-ag"))
                    body = _shell("overview", _overview(len(wfs), len(ags)))
                elif self.path == "/workflows":
                    wfs = list(net_call(lambda: client.workflows.list(), what="portal/list-wf"))
                    rows = [(w.id, w.name) for w in wfs]
                    body = _shell("workflows", _table(rows, "workflows"))
                elif self.path == "/agents":
                    ags = list(net_call(lambda: client.agents.list(), what="portal/list-ag"))
                    rows = [(a.id, a.name) for a in ags]
                    body = _shell("agents", _table(rows, "agents"))
                else:
                    self.send_error(404, "not found")
                    return
            except Exception as e:  # noqa: BLE001 — never crash the server loop
                self.send_error(500, f"upstream error: {e}")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def serve(*, host: str = "127.0.0.1", port: int = 7890, open_browser: bool = True) -> int:
    """Block on a tiny HTTP server. Returns 0 on Ctrl+C."""
    if host not in ("127.0.0.1", "localhost"):
        # Refuse to bind publicly — the portal is auth-less by design.
        raise ValueError(f"refusing to bind on non-loopback host {host!r}")
    load_dotenv()
    client = _client()
    handler = _make_handler(client)
    url = f"http://{host}:{port}"
    print(green(f"portal: {url}"), dim("(Ctrl+C to stop)"))
    if open_browser:
        with contextlib.suppress(Exception):
            webbrowser.open(url)
    with socketserver.TCPServer((host, port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print()
    return 0
