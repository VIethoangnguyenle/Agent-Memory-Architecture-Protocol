"""amap dashboard serve - local web dashboard (SSE) over registered AMAP runs.

Read-only. Serves one HTML page plus an SSE stream that pushes a JSON snapshot
of every registered project's RunState whenever it changes. Binds 127.0.0.1
only (local single-user). Stdlib only - no new dependencies.
"""
from __future__ import annotations

import json
import time
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from cli.dashboard import registry
from cli.dashboard.reader import RunState, read_run
from cli.scaffold import load_resolved_config

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
    """Serialize every registered project without letting one bad run break all."""
    runs = []
    for p in registry.load(registry_file):
        try:
            run = serialize(read_run(p))
            run["subagents"] = read_subagents(p)
            runs.append(run)
        except Exception:
            runs.append({"name": Path(p).name, "project_path": p, "error": True})
    return runs


def read_subagents(project_path: str) -> list[dict]:
    """Read generated subagent handoff prompts from active knowledge artifacts."""
    active = _active_dir(project_path)
    if active is None:
        return []
    paths = []
    paths.extend(active.glob("TASK_HANDOFF*.md"))
    microloop = active / "microloop"
    if microloop.exists():
        paths.extend(microloop.glob("TASK_HANDOFF*.md"))
    subagents = []
    for path in sorted(set(paths), key=lambda p: (p.stat().st_mtime, p.name)):
        try:
            prompt = path.read_text(encoding="utf-8")
        except OSError:
            continue
        subagents.append(
            {
                "id": _handoff_id(path),
                "name": _handoff_id(path).replace("-", " "),
                "path": str(path),
                "prompt": prompt,
                "updated_at": datetime.fromtimestamp(
                    path.stat().st_mtime, timezone.utc
                ).isoformat(),
            }
        )
    return subagents


def _active_dir(project_path: str) -> Path | None:
    resolved = load_resolved_config(Path(project_path))
    if resolved is None:
        return None
    return (
        Path(project_path)
        / resolved.get("framework_root", ".amap")
        / "knowledge"
        / "active"
    )


def _handoff_id(path: Path) -> str:
    stem = path.stem
    if stem == "TASK_HANDOFF":
        return "subagent"
    if stem.startswith("TASK_HANDOFF."):
        return stem.split(".", 1)[1]
    return stem


def sse_format(json_str: str) -> bytes:
    """Frame a JSON payload as one SSE message."""
    return f"data: {json_str}\n\n".encode("utf-8")


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
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
        self.send_header("Cache-Control", "no-store")
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
    registry.register(reg, target)
    registry.prune_missing(reg)
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", port), DashboardHandler)
    except OSError as exc:
        print(
            f"\n  Cannot bind 127.0.0.1:{port} ({exc}). "
            "Try: amap dashboard serve --port <other>\n"
        )
        return
    httpd.daemon_threads = True
    httpd.registry_file = reg
    url = f"http://127.0.0.1:{port}/"
    print(f"\n  AMAP dashboard live: {url}   (Ctrl+C to stop)\n")
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
