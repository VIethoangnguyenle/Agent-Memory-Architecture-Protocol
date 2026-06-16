"""Micro-loop contract: load/dump/validate the 5 filesystem artifacts.

Artifacts are YAML documents embedded as the body of a .md file (front-matter
style is avoided; the file IS the yaml). Keeps SP1a's dict-based simplicity.
"""
import yaml
from pathlib import Path

VALID_STATUS = {"pending", "in_progress", "done", "blocked"}
VALID_MODE = {"subagent", "fresh-session", "inline-reload"}


def _load(path):
    return yaml.safe_load(Path(path).read_text()) or {}


def _dump(doc, path):
    Path(path).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))


def validate_queue(q):
    for key in ("ticket_id", "spec_path", "execution_mode", "tasks"):
        if key not in q:
            raise ValueError(f"queue missing key: {key}")
    if q["execution_mode"] not in VALID_MODE:
        raise ValueError(f"bad execution_mode: {q['execution_mode']}")
    for t in q["tasks"]:
        if t.get("status") not in VALID_STATUS:
            raise ValueError(f"bad task status: {t.get('status')}")
    return q


def load_queue(path):
    return validate_queue(_load(path))


def dump_queue(q, path):
    validate_queue(q)
    _dump(q, path)
