"""AMAP dashboard registry: which projects the dashboard observes.

Stored as YAML at $AMAP_HOME/projects.yaml (default ~/.amap/projects.yaml):

    projects:
      - /abs/path/to/projectA
      - /abs/path/to/projectB

All functions take the registry file path explicitly so they are pure and
testable; the CLI passes default_registry_file().
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml


def default_registry_file() -> Path:
    home = Path(os.environ.get("AMAP_HOME", Path.home() / ".amap"))
    return home / "projects.yaml"


def load(registry_file: Path) -> list[str]:
    if not registry_file.exists():
        return []
    try:
        data = yaml.safe_load(registry_file.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    if not isinstance(data, dict):
        return []
    projects = data.get("projects", [])
    return [p for p in projects if isinstance(p, str)]


def save(registry_file: Path, projects: list[str]) -> None:
    registry_file.parent.mkdir(parents=True, exist_ok=True)
    registry_file.write_text(
        yaml.safe_dump({"projects": projects}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def register(registry_file: Path, project_path: str) -> bool:
    """Add an absolute project path. Returns True if added, False if already present."""
    abs_path = str(Path(project_path).resolve())
    projects = load(registry_file)
    if abs_path in projects:
        return False
    projects.append(abs_path)
    save(registry_file, projects)
    return True


def unregister(registry_file: Path, project_path: str) -> bool:
    """Remove a project path. Returns True if removed, False if absent."""
    abs_path = str(Path(project_path).resolve())
    projects = load(registry_file)
    if abs_path not in projects:
        return False
    projects.remove(abs_path)
    save(registry_file, projects)
    return True


def prune_missing(registry_file: Path) -> list[str]:
    """Drop entries whose directory no longer exists. Returns the removed paths."""
    projects = load(registry_file)
    keep = [p for p in projects if Path(p).is_dir()]
    removed = [p for p in projects if p not in keep]
    if removed:
        save(registry_file, keep)
    return removed
