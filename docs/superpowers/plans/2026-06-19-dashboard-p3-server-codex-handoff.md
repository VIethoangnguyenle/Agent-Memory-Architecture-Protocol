# P3 Dashboard Server — Codex Implementation Handoff

> Self-contained. Implement task-by-task with TDD. All code is final — paste it, run the
> verify command, commit. Do NOT redesign; if something seems off, note it but follow the plan.

## Context (what already exists)

Repo: `/home/zane/Desktop/agent-memory-arch-v3` (Python CLI package under `cli/`).
The P0–P2 slice already shipped (PR #9) and provides everything you build on:

- `cli/dashboard/registry.py` — `load(registry_file)`, `register(registry_file, path)`, `unregister`, `prune_missing`, `default_registry_file()`. A YAML registry of project paths. **Do not modify.**
- `cli/dashboard/reader.py` — `read_run(project_path: str) -> RunState`. `RunState` fields: `project_path, ticket_id, phase_state, tasks_total, tasks_done, active_task, tokens, stale, updated_at` + property `progress_pct` (0 when no tasks). Pure, defensive. **Do not modify.**
- `cli/commands/dashboard.py` — `run_dashboard(target=".", action=None, path=None)`; actions `register|unregister|list` + default one-shot snapshot. **You will extend this.**
- `cli/amap.py` — argparse entry; the `dashboard` subparser has positional `action` (choices `register|unregister|list`) + `--target` + `--path`, and a dispatch `elif args.command == "dashboard": run_dashboard(...)`. **You will extend this.**

Design spec: `docs/superpowers/specs/2026-06-19-dashboard-p3-server-design.md`.

## Goal

Add `amap dashboard serve` — a local web dashboard that shows every registered project's
`RunState` and updates in realtime via **SSE**. Stdlib only (no new dependencies).

## Hard constraints

- **Test runner:** `/usr/bin/python3 -m pytest` — NOT the repo's `.venv` python (it has no pytest).
- **No new dependencies.** Stdlib `http.server` only. `pyproject.toml` stays jinja2+pyyaml.
- **Bind `127.0.0.1` only** (local single-user; never `0.0.0.0`).
- **Python 3.9+** — every new module starts with `from __future__ import annotations`.
- **Do not modify** `reader.py` or `registry.py`. Reuse them.
- Work on a branch: `git checkout -b dashboard-p3-server` (from current `agent-activity-dashboard`). Commit after each task. Do NOT run `git checkout <sha>` / `reset` / `merge` mid-task.
- Constants: `DEFAULT_PORT = 7077`, `POLL_SECONDS = 1.0`.

---

## Task 1 — server core (pure functions, TDD)

**Files:** create `cli/dashboard/server.py`; test `cli/tests/test_dashboard_server.py`.

### Step 1.1 — write failing tests

Create `cli/tests/test_dashboard_server.py`:

```python
"""Tests for the dashboard SSE server."""
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from cli.dashboard import registry, server
from cli.dashboard.reader import RunState


def test_serialize_includes_name_and_progress():
    s = RunState(project_path="/tmp/projX", phase_state="phase-3-in-progress",
                 tasks_total=4, tasks_done=2, active_task="wire DI")
    d = server.serialize(s)
    assert d["name"] == "projX"
    assert d["progress_pct"] == 50
    assert d["phase_state"] == "phase-3-in-progress"
    assert d["active_task"] == "wire DI"
    assert d["project_path"] == "/tmp/projX"


def test_sse_format_framing():
    assert server.sse_format('{"a":1}') == b'data: {"a":1}\n\n'


def test_snapshot_empty_registry(tmp_path):
    assert server.snapshot(tmp_path / "none.yaml") == []


def test_snapshot_non_amap_project_is_idle(tmp_path):
    reg = tmp_path / "projects.yaml"
    proj = tmp_path / "p"
    proj.mkdir()
    registry.register(reg, str(proj))
    runs = server.snapshot(reg)
    assert len(runs) == 1
    assert runs[0]["name"] == "p"
    assert runs[0]["phase_state"] is None
    assert runs[0]["tasks_total"] == 0


@pytest.fixture
def running_server(tmp_path):
    reg = tmp_path / "projects.yaml"
    proj = tmp_path / "p"
    proj.mkdir()
    registry.register(reg, str(proj))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.DashboardHandler)
    httpd.daemon_threads = True
    httpd.registry_file = reg
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()
    httpd.server_close()


def test_index_served(running_server):
    with urllib.request.urlopen(running_server + "/", timeout=5) as r:
        body = r.read().decode()
        assert r.status == 200
        assert "AMAP" in body


def test_api_runs_json(running_server):
    with urllib.request.urlopen(running_server + "/api/runs", timeout=5) as r:
        assert r.status == 200
        data = json.loads(r.read())
        assert isinstance(data, list)
        assert data[0]["name"] == "p"


def test_unknown_path_404(running_server):
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(running_server + "/nope", timeout=5)
    assert exc.value.code == 404


def test_events_first_message_is_snapshot(running_server):
    req = urllib.request.urlopen(running_server + "/events", timeout=5)
    line = req.readline()  # b"data: [...]\n"
    req.close()
    assert line.startswith(b"data: ")
    payload = json.loads(line[len(b"data: "):].decode())
    assert isinstance(payload, list)
```

### Step 1.2 — run, expect fail

`/usr/bin/python3 -m pytest cli/tests/test_dashboard_server.py -v`
Expected: collection error / `ModuleNotFoundError: No module named 'cli.dashboard.server'`.

### Step 1.3 — implement

Create `cli/dashboard/server.py`:

```python
"""amap dashboard serve — local web dashboard (SSE) over registered AMAP runs.

Read-only. Serves one HTML page plus an SSE stream that pushes a JSON snapshot
of every registered project's RunState whenever it changes. Binds 127.0.0.1
only (local single-user). Stdlib only — no new dependencies.
"""
from __future__ import annotations

import json
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from cli.dashboard import registry
from cli.dashboard.reader import RunState, read_run

DEFAULT_PORT = 7077
POLL_SECONDS = 1.0
_STATIC = Path(__file__).parent / "static" / "index.html"


def serialize(state: RunState) -> dict:
    """RunState -> JSON-able dict (adds name + computed progress_pct)."""
    return {
        "name": Path(state.project_path).name,
        "project_path": state.project_path,
        "ticket_id": state.ticket_id,
        "phase_state": state.phase_state,
        "tasks_total": state.tasks_total,
        "tasks_done": state.tasks_done,
        "active_task": state.active_task,
        "stale": state.stale,
        "updated_at": state.updated_at,
        "progress_pct": state.progress_pct,
    }


def snapshot(registry_file: Path) -> list[dict]:
    """Serialize every registered project's RunState. One bad project never
    breaks the whole snapshot."""
    runs = []
    for p in registry.load(registry_file):
        try:
            runs.append(serialize(read_run(p)))
        except Exception:
            runs.append({"name": Path(p).name, "project_path": p, "error": True})
    return runs


def sse_format(json_str: str) -> bytes:
    """Frame a JSON payload as one SSE message."""
    return f"data: {json_str}\n\n".encode("utf-8")


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silence default request logging
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send_static()
        elif self.path == "/api/runs":
            self._send_json(snapshot(self.server.registry_file))
        elif self.path == "/events":
            self._send_sse()
        else:
            self.send_error(404)

    def _send_static(self):
        try:
            body = _STATIC.read_bytes()
        except OSError:
            self.send_error(500, "index.html missing")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        last = None
        try:
            while True:
                cur = json.dumps(snapshot(self.server.registry_file), ensure_ascii=False)
                if cur != last:
                    self.wfile.write(sse_format(cur))
                    self.wfile.flush()
                    last = cur
                time.sleep(POLL_SECONDS)
        except (BrokenPipeError, ConnectionResetError):
            return


def serve(target: str = ".", port: int = DEFAULT_PORT, open_browser: bool = True) -> None:
    reg = registry.default_registry_file()
    registry.register(reg, target)   # auto-add cwd, like the snapshot command
    registry.prune_missing(reg)
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", port), DashboardHandler)
    except OSError as exc:
        print(f"\n  ❌ Cannot bind 127.0.0.1:{port} ({exc}). "
              f"Try: amap dashboard serve --port <other>\n")
        return
    httpd.daemon_threads = True
    httpd.registry_file = reg
    url = f"http://127.0.0.1:{port}/"
    print(f"\n  📊 AMAP dashboard live: {url}   (Ctrl+C to stop)\n")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped")
    finally:
        httpd.server_close()
```

### Step 1.4 — create the static page

Create `cli/dashboard/static/index.html`:

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>AMAP Dashboard</title>
<style>
  body{font-family:ui-monospace,Menlo,Consolas,monospace;background:#0f1115;color:#e6e6e6;margin:0;padding:24px}
  h1{font-size:14px;font-weight:600;color:#9ac7ff;margin:0 0 16px}
  #status{color:#778}
  .runs{display:flex;flex-direction:column;gap:12px;max-width:560px}
  .card{background:#1a1d24;border:1px solid #2a2f3a;border-radius:8px;padding:12px 14px}
  .name{font-weight:600;margin-bottom:6px}
  .bar{height:8px;background:#2a2f3a;border-radius:4px;overflow:hidden;margin:6px 0}
  .fill{height:100%;background:#4aa3ff;width:0;transition:width .3s}
  .meta{font-size:12px;color:#9aa3b2}
  .phase{color:#d9c98a}.active{color:#88cc88}.stale{color:#dd7777}.idle,.empty{color:#778}
</style>
</head>
<body>
  <h1>AMAP runs &middot; <span id="status">connecting&hellip;</span></h1>
  <div class="runs" id="runs"></div>
<script>
const runsEl=document.getElementById('runs'),statusEl=document.getElementById('status');
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function render(runs){
  if(!runs.length){runsEl.innerHTML='<div class="empty">no projects registered &mdash; run: amap dashboard register</div>';return;}
  runsEl.innerHTML=runs.map(r=>{
    const idle=(r.phase_state===null&&r.tasks_total===0);
    if(idle)return `<div class="card"><div class="name">${esc(r.name)} <span class="idle">&middot; idle</span></div><div class="meta">${esc(r.phase_state||'bootstrapped')}</div></div>`;
    const pct=r.progress_pct||0;
    return `<div class="card">
      <div class="name">${esc(r.name)}${r.stale?' <span class="stale">[stale]</span>':''}</div>
      <div class="bar"><div class="fill" style="width:${pct}%"></div></div>
      <div class="meta">${r.tasks_done}/${r.tasks_total} (${pct}%) &middot; <span class="phase">${esc(r.phase_state||'?')}</span></div>
      ${r.active_task?`<div class="meta active">&#9654; ${esc(r.active_task)}</div>`:''}
      ${r.updated_at?`<div class="meta">updated ${esc(r.updated_at)}</div>`:''}
    </div>`;
  }).join('');
}
const es=new EventSource('/events');
es.onopen=()=>statusEl.textContent='live · SSE';
es.onmessage=e=>{statusEl.textContent='live · SSE';render(JSON.parse(e.data));};
es.onerror=()=>statusEl.textContent='reconnecting…';
</script>
</body>
</html>
```

### Step 1.5 — run tests, expect pass

`/usr/bin/python3 -m pytest cli/tests/test_dashboard_server.py -v`
Expected: 8 passed. If `test_events_first_message_is_snapshot` is flaky under load, re-run once; it reads one line then closes.

### Step 1.6 — commit

```bash
git add cli/dashboard/server.py cli/dashboard/static/index.html cli/tests/test_dashboard_server.py
git commit -m "feat: dashboard SSE server + static UI"
```

---

## Task 2 — wire `serve` into the command + CLI

**Files:** modify `cli/commands/dashboard.py`, `cli/amap.py`; test add to `cli/tests/test_dashboard_command.py`.

### Step 2.1 — extend `run_dashboard`

In `cli/commands/dashboard.py`, change the signature of `run_dashboard` from:

```python
def run_dashboard(target: str = ".", action: Optional[str] = None, path: Optional[str] = None) -> None:
    reg = registry.default_registry_file()
    chosen = path or target
```

to:

```python
def run_dashboard(target: str = ".", action: Optional[str] = None, path: Optional[str] = None,
                  port: int = 7077, no_browser: bool = False) -> None:
    if action == "serve":
        from cli.dashboard import server
        server.serve(target=target, port=port, open_browser=not no_browser)
        return
    reg = registry.default_registry_file()
    chosen = path or target
```

(Leave the rest of the function unchanged. `server` is imported lazily so the snapshot/register paths don't load it.)

### Step 2.2 — add an argparse test (this is the regression-safe check; `serve` itself is covered by Task 1's server tests)

Append to `cli/tests/test_dashboard_command.py`:

```python
def test_serve_action_dispatches(monkeypatch):
    calls = {}

    def fake_serve(target=".", port=7077, open_browser=True):
        calls.update(target=target, port=port, open_browser=open_browser)

    import cli.dashboard.server as server_mod
    monkeypatch.setattr(server_mod, "serve", fake_serve)

    run_dashboard(target="/tmp/x", action="serve", port=9000, no_browser=True)

    assert calls == {"target": "/tmp/x", "port": 9000, "open_browser": False}
```

### Step 2.3 — run, expect fail then pass

`/usr/bin/python3 -m pytest cli/tests/test_dashboard_command.py::test_serve_action_dispatches -v`
First run (before Step 2.1 applied) fails; after Step 2.1 it passes.

### Step 2.4 — wire argparse in `cli/amap.py`

Find the `dashboard` subparser block (the `action` argument with `choices=["register", "unregister", "list"]`). Make two edits:

1. Add `"serve"` to the choices and update the help:

```python
    dashboard_parser.add_argument(
        "action",
        nargs="?",
        choices=["register", "unregister", "list", "serve"],
        default=None,
        help="register/unregister/list/serve; omit to print a progress snapshot",
    )
```

2. Immediately after the existing `--path` argument of the dashboard subparser, add:

```python
    dashboard_parser.add_argument(
        "--port", type=int, default=7077, help="Port for `serve` (default: 7077)",
    )
    dashboard_parser.add_argument(
        "--no-browser", action="store_true", help="Do not auto-open the browser on `serve`",
    )
```

3. Update the dispatch. Find:

```python
    elif args.command == "dashboard":
        from cli.commands.dashboard import run_dashboard
        run_dashboard(target=args.target, action=args.action, path=args.path)
```

Replace with:

```python
    elif args.command == "dashboard":
        from cli.commands.dashboard import run_dashboard
        run_dashboard(target=args.target, action=args.action, path=args.path,
                      port=args.port, no_browser=args.no_browser)
```

### Step 2.5 — verify end-to-end (manual, time-boxed)

```bash
# argparse accepts the new flags without launching a blocking server:
/usr/bin/python3 -m cli.amap dashboard --help | grep -- "--port"
# smoke the server for 2 seconds without opening a browser:
timeout 2 /usr/bin/python3 -m cli.amap dashboard serve --no-browser --port 7077 || true
# in another shell while it runs you could: curl -s localhost:7077/api/runs
```
Expected: `--help` shows `--port`; the `serve` smoke prints the "AMAP dashboard live" line and exits on the 2s timeout with no traceback.

### Step 2.6 — full suite + commit

```bash
/usr/bin/python3 -m pytest cli/tests/ -q   # expect all pass (134 from slice + new server/command tests)
git add cli/commands/dashboard.py cli/amap.py cli/tests/test_dashboard_command.py
git commit -m "feat: wire amap dashboard serve (SSE web dashboard)"
```

---

## Task 3 — manual acceptance (human)

1. `amap dashboard serve` → browser opens `http://127.0.0.1:7077/`.
2. Register a real project: `amap dashboard register --path /home/zane/Desktop/BA-Framework`.
3. Run an AMAP task in that project (Antigravity). Watch the card's phase/progress update live in the browser within ~1s, no manual refresh (this is the P2.5 task-level confirmation the slice deferred).
4. `Ctrl+C` stops the server cleanly.

---

## Done criteria

- `cli/dashboard/server.py` + `static/index.html` exist; `amap dashboard serve` launches a 127.0.0.1 SSE dashboard.
- `amap dashboard` (snapshot), `register/unregister/list` unchanged.
- `/usr/bin/python3 -m pytest cli/tests/` all green.
- No new dependency in `pyproject.toml`.
- Browser shows multi-project cards updating in realtime.

## Out of scope (do NOT build)

Token display, tool-call timeline / activity hook (P5–P6), WebSocket, auth, non-local binding,
OS-level file watching. Keep the poll-and-diff SSE loop as specified.
