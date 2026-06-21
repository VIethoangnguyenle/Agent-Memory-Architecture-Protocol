"""Maika dashboard reader: parse a project's contract files into a RunState.

Reads (read-only) from {project}/{framework_root}/knowledge/active/:
  - AGENT_TRANSPARENCY.md    (YAML frontmatter: phase_state, ticket_id)
  - microloop/TASK_QUEUE.md  (pure YAML: tasks[].status)

Token parsing (TOKEN_LOG.md markdown tables) is out of slice scope; `tokens`
stays None. Activity timeline (ACTIVITY_LOG.jsonl) is P5+ and not read here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from cli import CANONICAL_FRAMEWORK_ROOT
from cli.scaffold import load_resolved_config


@dataclass
class RunState:
    project_path: str
    ticket_id: Optional[str] = None
    phase_state: Optional[str] = None
    tasks_total: int = 0
    tasks_done: int = 0
    active_task: Optional[str] = None
    tokens: Optional[dict] = None  # deferred; always None in the slice
    stale: bool = False
    updated_at: Optional[str] = None

    @property
    def progress_pct(self) -> int:
        if self.tasks_total == 0:
            return 0
        return round(100 * self.tasks_done / self.tasks_total)


def _read_frontmatter(path: Path) -> Optional[dict]:
    """Return the YAML frontmatter dict of a `--- ... ---` .md file, else None."""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def active_dir(project_path: str, resolved: Optional[dict] = None) -> Optional[Path]:
    """Resolve {project}/{framework_root}/knowledge/active, or None if not an Maika project.

    Shared by the reader, the SSE server, and the brain sync so config is
    resolved once per project per poll instead of once per consumer.
    """
    if resolved is None:
        resolved = load_resolved_config(Path(project_path))
    if resolved is None:
        return None
    return Path(project_path) / resolved.get("framework_root", CANONICAL_FRAMEWORK_ROOT) / "knowledge" / "active"


def read_run(project_path: str, active: Optional[Path] = None) -> RunState:
    state = RunState(project_path=str(project_path))

    if active is None:
        active = active_dir(project_path)
    if active is None:
        return state  # not an Maika project → idle

    mtimes: list[float] = []

    # AGENT_TRANSPARENCY frontmatter
    at_path = active / "AGENT_TRANSPARENCY.md"
    fm = _read_frontmatter(at_path)
    if fm is not None:
        state.phase_state = fm.get("phase_state")
        state.ticket_id = fm.get("ticket_id")
        mtimes.append(at_path.stat().st_mtime)
    elif at_path.exists():
        state.stale = True  # present but unparseable

    # TASK_QUEUE (the file IS yaml)
    tq_path = active / "microloop" / "TASK_QUEUE.md"
    if tq_path.exists():
        try:
            queue = yaml.safe_load(tq_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            queue = None
            state.stale = True
        if isinstance(queue, dict):
            tasks = queue.get("tasks", [])
            if isinstance(tasks, list):
                state.tasks_total = len(tasks)
                state.tasks_done = sum(1 for t in tasks if isinstance(t, dict) and t.get("status") == "done")
                for t in tasks:
                    if isinstance(t, dict) and t.get("status") == "in_progress":
                        state.active_task = t.get("desc") or t.get("id")
                        break
            if state.ticket_id is None:
                state.ticket_id = queue.get("ticket_id")
            mtimes.append(tq_path.stat().st_mtime)

    if mtimes:
        state.updated_at = datetime.fromtimestamp(max(mtimes), timezone.utc).isoformat()
    return state
