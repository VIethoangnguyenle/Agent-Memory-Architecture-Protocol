"""Runtime write gate for AMAP decision-point evidence.

Command-hook contract:
- stdin: JSON payload from the agent runtime hook.
- Claude Code: exit 0 allows; exit 2 blocks with stderr reason.
- Codex: stdout JSON with hookSpecificOutput.permissionDecision allow|deny.
- Antigravity: stdout JSON with decision allow|deny.
"""
import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


_PATCH_FILE_RE = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", re.MULTILINE)


@dataclass
class Decision:
    ok: bool
    reason: str = ""


def _load_gate_check(project_root: Path, framework_root: str):
    candidates = [
        project_root / framework_root / "tools" / "gate-check" / "gates.py",
        Path(__file__).resolve().parents[2] / "tools" / "gate-check" / "gates.py",
    ]
    for mod in candidates:
        if mod.exists():
            spec = importlib.util.spec_from_file_location("gates", mod)
            gates = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gates)
            return gates
    raise FileNotFoundError(f"Cannot locate gate-check/gates.py under {framework_root}")


def _path_from_value(value):
    if isinstance(value, str) and value.strip():
        return Path(value.strip())
    return None


def _paths_from_patch_command(command: str):
    return [Path(match.strip()) for match in _PATCH_FILE_RE.findall(command or "")]


def extract_target_paths(payload: dict):
    tool_input = payload.get("tool_input") or {}
    tool_call = payload.get("toolCall") or {}
    tool_args = tool_call.get("args") or {}

    direct = (
        _path_from_value(tool_input.get("file_path"))
        or _path_from_value(tool_input.get("path"))
        or _path_from_value(tool_args.get("file_path"))
        or _path_from_value(tool_args.get("path"))
        or _path_from_value(tool_args.get("FilePath"))
    )
    if direct:
        return [direct]

    command = tool_input.get("command") or tool_args.get("CommandLine") or ""
    return _paths_from_patch_command(command)


def _is_framework_artifact(path: Path, framework_root: str) -> bool:
    parts = path.as_posix()
    return (
        parts.startswith(f"{framework_root}/")
        or parts.startswith("openspec/")
        or parts.startswith("docs/superpowers/specs/")
        or parts.startswith("docs/superpowers/plans/")
    )


def _load_all_rule_ids(index_path: Path):
    if not index_path.exists():
        return None, True
    data = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
    entries = data.get("entries") or []
    return {entry["id"] for entry in entries if entry.get("id")}, len(entries) == 0


def evaluate_write(project_root: Path, target_path: Path, framework_root: str = ".amap") -> Decision:
    if not target_path.as_posix():
        return Decision(False, "Unable to identify target path for write-gate payload")
    if _is_framework_artifact(target_path, framework_root):
        return Decision(True)

    checkpoint = project_root / framework_root / "knowledge" / "active" / "KNOWLEDGE_CHECKPOINT.md"
    if not checkpoint.exists():
        return Decision(False, f"Missing {checkpoint.relative_to(project_root)} before code write: {target_path}")

    gates = _load_gate_check(project_root, framework_root)
    index_path = project_root / framework_root / "knowledge" / "long-term" / "knowledge-index.yaml"
    valid_rule_ids, index_empty = _load_all_rule_ids(index_path)
    result = gates.validate_knowledge_checkpoint(
        checkpoint.read_text(encoding="utf-8"),
        valid_rule_ids=valid_rule_ids,
        allow_no_knowledge=index_empty,
    )
    if result.ok:
        return Decision(True)
    return Decision(False, f"Invalid KNOWLEDGE_CHECKPOINT before code write: {result.reason}")


def _print_runtime_decision(runtime: str, decision: Decision) -> int:
    if decision.ok:
        if runtime == "codex":
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                }
            }))
        elif runtime == "antigravity":
            print(json.dumps({"decision": "allow"}))
        return 0

    if runtime == "codex":
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": decision.reason,
            }
        }))
        return 0
    if runtime == "antigravity":
        print(json.dumps({"decision": "deny", "reason": decision.reason}))
        return 0
    print(decision.reason, file=sys.stderr)
    return 2


def main(argv=None, stdin_text=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework-root", default=".amap")
    parser.add_argument("--runtime", choices=["claude", "codex", "antigravity"], default="claude")
    args = parser.parse_args(argv)
    raw = stdin_text if stdin_text is not None else sys.stdin.read()
    payload = json.loads(raw or "{}")
    targets = extract_target_paths(payload)
    if not targets:
        decision = Decision(False, "Unable to identify target path for write-gate payload")
    else:
        decisions = [
            evaluate_write(Path.cwd(), target, framework_root=args.framework_root)
            for target in targets
        ]
        decision = next((item for item in decisions if not item.ok), Decision(True))
    return _print_runtime_decision(args.runtime, decision)


if __name__ == "__main__":
    sys.exit(main())
