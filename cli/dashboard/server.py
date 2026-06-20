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
from typing import Optional

import yaml

from cli.dashboard import registry
from cli.dashboard.reader import RunState, active_dir, read_run

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
            active = active_dir(p)  # resolve config once; shared by both readers
            run = serialize(read_run(p, active=active))
            reader_stale = run["stale"]  # preserve before update() overwrites it
            runtime = read_runtime(p, active=active)
            run.update(runtime)
            run["stale"] = reader_stale or runtime["stale"]
            runs.append(run)
        except Exception as exc:
            runs.append({"name": Path(p).name, "project_path": p, "error": str(exc)})
    return runs


def read_runtime(project_path: str, active: Optional[Path] = None) -> dict:
    """Read dashboard runtime artifacts beyond the core RunState."""
    if active is None:
        active = active_dir(project_path)
    if active is None:
        return {
            "parent_brain": None,
            "subagents": [],
            "events": [],
            "errors": [],
            "stale": False,
        }
    tasks, queue_errors = _read_queue(active)
    result_paths = _collect_artifacts(active, "TASK_RESULT*.md")
    results = {_result_id(p): p for p in result_paths}
    handoff_paths = _collect_artifacts(active, "TASK_HANDOFF*.md")
    handoffs = {_handoff_id(p): p for p in handoff_paths}
    parent_brain = _read_parent_brain(active)

    subagents = []
    seen = set()
    for task in tasks:
        task_id = str(task.get("id") or task.get("desc") or "task")
        seen.add(task_id)
        handoff_path = _path_from_task(project_path, task.get("handoff_path")) or handoffs.get(task_id)
        result_path = _path_from_task(project_path, task.get("result_path")) or results.get(task_id)
        subagents.append(
            _subagent_record(
                task_id,
                status=task.get("status") or "pending",
                desc=task.get("desc"),
                handoff_path=handoff_path,
                result_path=result_path,
            )
        )

    for task_id, handoff_path in handoffs.items():
        if task_id in seen:
            continue
        seen.add(task_id)
        result_path = results.get(task_id)
        subagents.append(
            _subagent_record(
                task_id,
                status="done" if result_path else "spawned",
                handoff_path=handoff_path,
                result_path=result_path,
            )
        )

    for task_id, result_path in results.items():
        if task_id in seen:
            continue
        subagents.append(
            _subagent_record(task_id, status="done", result_path=result_path)
        )

    events, event_errors = _read_events(active)
    errors = queue_errors + event_errors
    return {
        "parent_brain": parent_brain,
        "subagents": subagents,
        "events": events,
        "errors": errors,
        "stale": bool(errors),
    }


def read_subagents(project_path: str) -> list[dict]:
    """Read generated subagent handoff prompts from active knowledge artifacts."""
    return read_runtime(project_path)["subagents"]


def _read_queue(active: Path) -> tuple[list[dict], list[str]]:
    queue_path = active / "microloop" / "TASK_QUEUE.md"
    if not queue_path.exists():
        return [], []
    try:
        queue = yaml.safe_load(queue_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return [], [f"{queue_path}: {exc}"]
    if not isinstance(queue, dict):
        return [], [f"{queue_path}: expected mapping"]
    tasks = queue.get("tasks", [])
    if not isinstance(tasks, list):
        return [], [f"{queue_path}: tasks must be a list"]
    return [t for t in tasks if isinstance(t, dict)], []


def _read_events(active: Path) -> tuple[list[dict], list[str]]:
    log_path = active / "microloop" / "ACTIVITY_LOG.jsonl"
    if not log_path.exists():
        return [], []
    events = []
    errors = []
    for lineno, line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{log_path}:{lineno}: {exc.msg}")
            continue
        if isinstance(event, dict):
            events.append(event)
        else:
            errors.append(f"{log_path}:{lineno}: expected object")
    return events, errors


def _read_parent_brain(active: Path) -> Optional[dict]:
    for path in (active / "PARENT_BRAIN.md", active / "PARENT_CONVERSATION.md"):
        content = _read_optional_text(path)
        if content:
            return {
                "source": _parent_brain_source(content) or "ide-brain-mirror",
                "path": str(path),
                "content": content,
                "updated_at": _latest_mtime([path]),
            }
    return None


def _parent_brain_source(content: str) -> Optional[str]:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("source:"):
            return stripped.split(":", 1)[1].strip().strip("'\"") or None
    return None


def _collect_artifacts(active: Path, pattern: str) -> list[Path]:
    paths = list(active.glob(pattern))
    microloop = active / "microloop"
    if microloop.exists():
        paths.extend(microloop.glob(pattern))
    return sorted(set(paths), key=lambda p: (p.stat().st_mtime, p.name))


def _subagent_record(
    task_id: str,
    *,
    status: str,
    desc: Optional[str] = None,
    handoff_path: Optional[Path] = None,
    result_path: Optional[Path] = None,
) -> dict:
    prompt = _read_optional_text(handoff_path)
    result = _read_optional_text(result_path)
    updated = _latest_mtime([p for p in (handoff_path, result_path) if p is not None])
    return {
        "id": task_id,
        "name": task_id.replace("-", " "),
        "desc": desc,
        "status": status,
        "path": str(handoff_path) if handoff_path else None,
        "handoff_path": str(handoff_path) if handoff_path else None,
        "result_path": str(result_path) if result_path else None,
        "prompt": prompt,
        "result": result,
        "updated_at": updated,
    }


def _read_optional_text(path: Optional[Path]) -> Optional[str]:
    if path is None or not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _latest_mtime(paths: list[Path]) -> Optional[str]:
    existing = [p.stat().st_mtime for p in paths if p.exists()]
    if not existing:
        return None
    return datetime.fromtimestamp(max(existing), timezone.utc).isoformat()


def _path_from_task(project_path: str, value) -> Optional[Path]:
    if not value:
        return None
    path = Path(str(value))
    if path.is_absolute():
        return path
    return Path(project_path) / path


def _handoff_id(path: Path) -> str:
    stem = path.stem
    if stem == "TASK_HANDOFF":
        return "subagent"
    if stem.startswith("TASK_HANDOFF."):
        return stem.split(".", 1)[1]
    return stem


def _result_id(path: Path) -> str:
    stem = path.stem
    if stem == "TASK_RESULT":
        return "subagent"
    if stem.startswith("TASK_RESULT."):
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
