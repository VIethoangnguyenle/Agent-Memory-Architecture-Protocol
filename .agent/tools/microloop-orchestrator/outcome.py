"""Outcome aggregator: enriched TASK_QUEUE → outcome record → append log.

Reads gate_history from enriched TASK_QUEUE (SP1c), builds a per-ticket
outcome record, and appends it to outcome-log.yaml. Pure functions except
append_to_log (single side-effect, isolated for test mocking).
"""

import yaml
from pathlib import Path
from datetime import date
from collections import Counter


def _collect_rules(tasks, ir_rules=None):
    """Scan gate_history across all tasks → rules_triggered + rules_silent."""
    triggered = Counter()   # rule_id → total trigger count
    resolved = {}           # rule_id → True if every task that hit it eventually passed

    for t in tasks:
        for attempt in t.get("gate_history", []):
            for v in attempt.get("violations", []):
                rule = v["rule"]
                triggered[rule] += 1
                resolved[rule] = t["status"] == "done"

    rules_triggered = [
        {"rule": r, "times": triggered[r], "final_resolved": resolved.get(r, False)}
        for r in sorted(triggered)
    ]

    if ir_rules:
        all_ids = {r["id"] for r in ir_rules}
        triggered_ids = {r["rule"] for r in rules_triggered}
        rules_silent = sorted(all_ids - triggered_ids)
    else:
        rules_silent = []

    return rules_triggered, rules_silent


def _loop_stats(tasks):
    """Compute first_pass / retried / blocked counts."""
    first_pass = sum(1 for t in tasks if t["status"] == "done" and t.get("retries", 0) == 0)
    retried = sum(1 for t in tasks if t["status"] == "done" and t.get("retries", 0) > 0)
    blocked = sum(1 for t in tasks if t["status"] == "blocked")
    total = len(tasks)
    return {
        "total_tasks": total,
        "first_pass": first_pass,
        "retried": retried,
        "blocked": blocked,
        "first_pass_rate": round(first_pass / total, 2) if total else 0,
    }


def build_record(queue, extraction_report=None, ir_rules=None):
    """Build one outcome record from enriched TASK_QUEUE.

    Args:
        queue: TASK_QUEUE dict with gate_history in each task.
        extraction_report: optional EXTRACTION_REPORT dict (verdict + clusters).
        ir_rules: optional list of rule dicts from rules.json IR (for rules_silent).
    Returns:
        dict ready to append to outcome-log.yaml.
    """
    tasks = queue["tasks"]
    rules_triggered, rules_silent = _collect_rules(tasks, ir_rules)
    total_gate_calls = sum(len(t.get("gate_history", [])) for t in tasks)

    return {
        "ticket_id": queue.get("ticket_id", "unknown"),
        "date": str(date.today()),
        "rules_triggered": rules_triggered,
        "rules_silent": rules_silent,
        "micro_loop": _loop_stats(tasks),
        "extraction": {
            "verdict": (extraction_report or {}).get("verdict", "N/A"),
            "clusters": len((extraction_report or {}).get("clusters", [])),
        },
        "execution_mode": queue.get("execution_mode", "unknown"),
        "total_gate_calls": total_gate_calls,
    }


def append_to_log(record, log_path):
    """Append one record to outcome-log.yaml (create if missing)."""
    path = Path(log_path)
    existing = yaml.safe_load(path.read_text()) if path.exists() else []
    existing = existing or []
    existing.append(record)
    path.write_text(yaml.safe_dump(existing, sort_keys=False, allow_unicode=True))
