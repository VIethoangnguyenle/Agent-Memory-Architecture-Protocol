"""Tests for outcome.py — build_record + append_to_log."""
from pathlib import Path
import sys, yaml
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import outcome  # noqa: E402


def _enriched_queue():
    """TASK_QUEUE with gate_history (SP1c enrichment)."""
    return {
        "ticket_id": "PROJ-42",
        "spec_path": "spec.md",
        "execution_mode": "inline-reload",
        "tasks": [
            {
                "id": "T1", "desc": "base handler", "depends_on": [],
                "status": "done", "retries": 0,
                "gate_history": [
                    {"attempt": 0, "status": "PASS", "violations": []},
                ],
            },
            {
                "id": "T2", "desc": "validator", "depends_on": ["T1"],
                "status": "done", "retries": 1,
                "gate_history": [
                    {"attempt": 0, "status": "FAIL", "violations": [
                        {"rule": "HP-6.max_for_nesting", "file": "Val.java", "line": 12, "message": "depth 2"},
                        {"rule": "threshold.max_method_lines", "file": "Val.java", "line": 1, "message": "55 > 40"},
                    ]},
                    {"attempt": 1, "status": "PASS", "violations": []},
                ],
            },
            {
                "id": "T3", "desc": "controller", "depends_on": ["T2"],
                "status": "blocked", "retries": 2,
                "gate_history": [
                    {"attempt": 0, "status": "FAIL", "violations": [
                        {"rule": "HP-6.max_for_nesting", "file": "Ctrl.java", "line": 30, "message": "depth 1"},
                    ]},
                    {"attempt": 1, "status": "FAIL", "violations": [
                        {"rule": "HP-6.max_for_nesting", "file": "Ctrl.java", "line": 30, "message": "depth 1"},
                    ]},
                    {"attempt": 2, "status": "FAIL", "violations": [
                        {"rule": "HP-6.max_for_nesting", "file": "Ctrl.java", "line": 30, "message": "depth 1"},
                    ]},
                ],
            },
        ],
    }


def test_build_record_rules_triggered():
    record = outcome.build_record(_enriched_queue())
    triggered = {r["rule"]: r for r in record["rules_triggered"]}
    # HP-6 triggered in T2 (1x) + T3 (3x) = 4 times total
    assert triggered["HP-6.max_for_nesting"]["times"] == 4
    # threshold triggered in T2 only (1x)
    assert triggered["threshold.max_method_lines"]["times"] == 1


def test_build_record_rules_resolved():
    record = outcome.build_record(_enriched_queue())
    triggered = {r["rule"]: r for r in record["rules_triggered"]}
    # HP-6: T2 done (resolved) but T3 blocked → last write wins = False
    assert triggered["HP-6.max_for_nesting"]["final_resolved"] is False
    # threshold: only in T2 which is done → True
    assert triggered["threshold.max_method_lines"]["final_resolved"] is True


def test_build_record_rules_silent_with_ir():
    ir_rules = [
        {"id": "HP-6.max_for_nesting"},
        {"id": "HP-7.forbid_else"},
        {"id": "threshold.max_method_lines"},
        {"id": "naming.service_suffix"},
    ]
    record = outcome.build_record(_enriched_queue(), ir_rules=ir_rules)
    assert "HP-7.forbid_else" in record["rules_silent"]
    assert "naming.service_suffix" in record["rules_silent"]
    assert "HP-6.max_for_nesting" not in record["rules_silent"]


def test_build_record_loop_stats():
    record = outcome.build_record(_enriched_queue())
    ml = record["micro_loop"]
    assert ml["total_tasks"] == 3
    assert ml["first_pass"] == 1   # T1 only
    assert ml["retried"] == 1      # T2
    assert ml["blocked"] == 1      # T3
    assert ml["first_pass_rate"] == round(1/3, 2)


def test_build_record_extraction():
    report = {"verdict": "FLAG", "clusters": [{"files": ["a.java", "b.java"]}]}
    record = outcome.build_record(_enriched_queue(), extraction_report=report)
    assert record["extraction"]["verdict"] == "FLAG"
    assert record["extraction"]["clusters"] == 1


def test_build_record_total_gate_calls():
    record = outcome.build_record(_enriched_queue())
    # T1: 1 call, T2: 2 calls, T3: 3 calls = 6
    assert record["total_gate_calls"] == 6


def test_build_record_no_gate_history():
    """Tasks without gate_history (backward compat) → empty rules."""
    queue = {
        "ticket_id": "OLD-1", "spec_path": "p", "execution_mode": "inline-reload",
        "tasks": [{"id": "T1", "desc": "d", "depends_on": [], "status": "done", "retries": 0}],
    }
    record = outcome.build_record(queue)
    assert record["rules_triggered"] == []
    assert record["micro_loop"]["first_pass"] == 1


def test_append_to_log_creates_and_appends(tmp_path):
    log_path = tmp_path / "outcome-log.yaml"
    record1 = {"ticket_id": "A", "date": "2026-06-17"}
    record2 = {"ticket_id": "B", "date": "2026-06-18"}

    outcome.append_to_log(record1, str(log_path))
    data = yaml.safe_load(log_path.read_text())
    assert len(data) == 1 and data[0]["ticket_id"] == "A"

    outcome.append_to_log(record2, str(log_path))
    data = yaml.safe_load(log_path.read_text())
    assert len(data) == 2 and data[1]["ticket_id"] == "B"
