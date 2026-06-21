"""Best-effort IDE brain sync for dashboard parent context.

The dashboard remains read-only while serving. This module provides explicit
commands that mirror runtime-specific IDE conversation/brain files into Maika's
stable `PARENT_BRAIN.md` contract.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cli.dashboard.reader import active_dir

TEXT_SUFFIXES = {".md", ".txt", ".jsonl", ".json", ".resolved"}
MAX_ARTIFACTS = 6
MAX_FILE_CHARS = 4000
MAX_TOTAL_CHARS = 14000


@dataclass
class BrainSyncResult:
    written: bool
    reason: str
    path: Optional[str] = None
    source: Optional[str] = None
    conversation_id: Optional[str] = None
    artifact_count: int = 0


def sync_parent_brain(
    project_path: str | Path,
    *,
    platform: str = "antigravity",
    home: Optional[Path] = None,
) -> BrainSyncResult:
    """Sync a platform IDE brain into `PARENT_BRAIN.md`."""
    if platform != "antigravity":
        return BrainSyncResult(False, f"unsupported brain platform: {platform}")
    return sync_antigravity_parent_brain(project_path, home=home)


def sync_antigravity_parent_brain(
    project_path: str | Path,
    *,
    home: Optional[Path] = None,
) -> BrainSyncResult:
    """Mirror recent Antigravity brain text artifacts into PARENT_BRAIN.md."""
    project = Path(project_path).resolve()
    active = active_dir(str(project))
    if active is None:
        return BrainSyncResult(False, "target is not an Maika project")

    home = Path(home).expanduser() if home is not None else Path.home()
    conversation_id = _antigravity_conversation_id(project, home)
    if not conversation_id:
        return BrainSyncResult(False, "no Antigravity conversation mapping found")

    brain_root = home / ".gemini" / "antigravity" / "brain" / conversation_id
    artifacts = _recent_text_artifacts(brain_root)
    if not artifacts:
        return BrainSyncResult(
            False,
            f"no text brain artifacts found for conversation {conversation_id}",
            conversation_id=conversation_id,
        )

    content = _build_parent_brain(project, conversation_id, brain_root, artifacts)
    out_path = active / "PARENT_BRAIN.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    _append_activity_event(
        active,
        "parent_brain_updated",
        actor="parent",
        source="antigravity-brain",
        conversation_id=conversation_id,
        artifact_count=len(artifacts),
        path=str(out_path),
        summary="Synced parent brain from Antigravity artifacts.",
    )
    return BrainSyncResult(
        True,
        "synced Antigravity parent brain",
        path=str(out_path),
        source="antigravity-brain",
        conversation_id=conversation_id,
        artifact_count=len(artifacts),
    )


def _antigravity_conversation_id(project: Path, home: Path) -> Optional[str]:
    cache_path = home / ".gemini" / "antigravity-cli" / "cache" / "last_conversations.json"
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None

    project_resolved = str(project.resolve())
    for raw_path, conversation_id in data.items():
        if not isinstance(raw_path, str) or not isinstance(conversation_id, str):
            continue
        if raw_path == project_resolved:
            return conversation_id
        try:
            if str(Path(raw_path).expanduser().resolve()) == project_resolved:
                return conversation_id
        except OSError:
            continue
    return None


def _recent_text_artifacts(brain_root: Path) -> list[Path]:
    if not brain_root.exists():
        return []
    paths = []
    for path in brain_root.rglob("*"):
        if not path.is_file():
            continue
        if path.name.endswith(".metadata.json"):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            paths.append(path)
    return sorted(paths, key=lambda p: (p.stat().st_mtime, p.name), reverse=True)[:MAX_ARTIFACTS]


def _build_parent_brain(project: Path, conversation_id: str, brain_root: Path, artifacts: list[Path]) -> str:
    updated_at = datetime.now(timezone.utc).isoformat()
    parts = [
        "# PARENT_BRAIN",
        "",
        "source: antigravity-brain",
        f"conversation_id: {conversation_id}",
        f"project_path: {project}",
        f"updated_at: {updated_at}",
        "",
        "## Antigravity Brain Mirror",
        "",
        "Best-effort mirror of recent text artifacts from the Antigravity IDE brain.",
        "The IDE conversation/brain remains the source of truth; this file is the dashboard contract.",
        "",
        "## Recent Text Artifacts",
    ]
    total = 0
    for path in artifacts:
        rel = _relative_to(path, brain_root)
        text = _read_artifact_excerpt(path)
        if total + len(text) > MAX_TOTAL_CHARS:
            text = text[: max(0, MAX_TOTAL_CHARS - total)].rstrip()
        if not text:
            continue
        total += len(text)
        mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
        parts.extend([
            "",
            f"### {rel}",
            "",
            f"mtime: {mtime}",
            "",
            "```text",
            text,
            "```",
        ])
        if total >= MAX_TOTAL_CHARS:
            break
    return "\n".join(parts).rstrip() + "\n"


def _read_artifact_excerpt(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
    text = text.strip()
    if len(text) > MAX_FILE_CHARS:
        return text[:MAX_FILE_CHARS].rstrip() + "\n\n[truncated]"
    return text


def _append_activity_event(active: Path, event: str, **fields) -> None:
    record = {"ts": datetime.now(timezone.utc).isoformat(), "event": event}
    record.update({k: v for k, v in fields.items() if v is not None})
    path = active / "microloop" / "ACTIVITY_LOG.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _relative_to(path: Path, parent: Path) -> str:
    try:
        return str(path.relative_to(parent))
    except ValueError:
        return str(path)
