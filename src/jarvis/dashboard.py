"""Read-only local desk view; every activity item comes from persisted event IDs."""

from __future__ import annotations

import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .storage import LocalStorage, StorageError
from .roles import ROLES


def render(home: Path, mode: str = "OFF") -> str:
    try:
        with LocalStorage(home, writer=False) as store:
            events = [row["event"] for row in store.read_events()]
    except (StorageError, OSError) as exc:
        events = []
        error = html.escape(str(exc))
    else:
        error = ""
    by_type = {event["event_type"] for event in events}
    cards = []
    for desk in dict.fromkeys(role.department for role in ROLES):
        roles = [role for role in ROLES if role.department == desk]
        items = ""
        for role in roles:
            observed = bool(by_type.intersection(role.event_types))
            status = "RECORDED" if observed else role.implementation
            items += f"<li title='{html.escape(role.purpose)}'><span class='dot {'active' if observed else ''}'></span>" \
                     f"{html.escape(role.name)} <small>{html.escape(status)}</small></li>"
        cards.append(f"<section><h2>{html.escape(desk)}</h2><ul>{items}</ul></section>")
    timeline = "".join(
        f"<tr><td>{html.escape(e['at'])}</td><td>{html.escape(e['event_type'])}</td>"
        f"<td>{html.escape(str(e.get('asset_id') or '—'))}</td><td><code>{html.escape(e['event_id'])}</code></td>"
        f"<td><details><summary>Trace</summary><pre>{html.escape(json.dumps(e, indent=2))}</pre></details></td></tr>"
        for e in reversed(events[-80:]))
    return f"""<!doctype html><html lang='en'><meta charset='utf-8'><meta http-equiv='refresh' content='5'>
<title>JARVIS Trading Desk</title><style>
body{{font:15px system-ui;background:#0b1423;color:#e9f1f7;margin:0;padding:24px}}
h1{{margin:0}}.tag{{display:inline-block;background:#284668;padding:5px 12px;border-radius:16px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin:24px 0}}
section{{background:#14243a;border:1px solid #33506c;border-radius:12px;padding:16px}}
h2{{font-size:17px}}ul{{list-style:none;padding:0}}li{{padding:5px 0}}small{{float:right;color:#9daec0}}
.dot{{display:inline-block;width:8px;height:8px;border-radius:50%;background:#596879;margin-right:8px}}
.dot.active{{background:#54c59a}}table{{border-collapse:collapse;width:100%}}td,th{{padding:8px;border-bottom:1px solid #33506c;text-align:left}}
code,pre{{font-size:11px;overflow:auto;max-width:650px}}.warn{{color:#ffca76}}
</style><h1>JARVIS Trading Desk <span class='tag'>{html.escape(mode)}</span></h1>
<p>Read-only local view • {len(events)} persisted events • no order controls • no simulated activity shown as live</p>
<p class='warn'>{error}</p><div class='grid'>{''.join(cards)}</div>
<section><h2>Decision and operational event trace</h2><table><thead><tr><th>UTC</th><th>Event</th><th>Asset</th><th>Event ID</th><th>Evidence</th></tr></thead>
<tbody>{timeline}</tbody></table></section></html>"""


def serve(home: Path, host: str = "127.0.0.1", port: int = 8765, mode: str = "OFF") -> None:
    if host not in ("127.0.0.1", "localhost"):
        raise ValueError("dashboard binds to localhost only")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path != "/":
                self.send_error(404)
                return
            body = render(home, mode).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    ThreadingHTTPServer((host, port), Handler).serve_forever()
