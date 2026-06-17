"""Tests for stats.py — rule_effectiveness, prune_candidates, quality_trend."""
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import stats  # noqa: E402


def _sample_log():
    """5 ticket outcome log for testing."""
    return [
        {
            "ticket_id": "P-1", "date": "2026-06-01",
            "rules_triggered": [
                {"rule": "HP-6.max_for_nesting", "times": 2, "final_resolved": True},
            ],
            "rules_silent": ["HP-7.forbid_else", "naming.service_suffix"],
            "micro_loop": {"total_tasks": 3, "first_pass": 1, "retried": 1, "blocked": 1, "first_pass_rate": 0.33},
        },
        {
            "ticket_id": "P-2", "date": "2026-06-02",
            "rules_triggered": [
                {"rule": "HP-6.max_for_nesting", "times": 1, "final_resolved": True},
                {"rule": "threshold.max_method_lines", "times": 1, "final_resolved": True},
            ],
            "rules_silent": ["HP-7.forbid_else", "naming.service_suffix"],
            "micro_loop": {"total_tasks": 2, "first_pass": 1, "retried": 1, "blocked": 0, "first_pass_rate": 0.50},
        },
        {
            "ticket_id": "P-3", "date": "2026-06-03",
            "rules_triggered": [
                {"rule": "HP-6.max_for_nesting", "times": 3, "final_resolved": False},
            ],
            "rules_silent": ["HP-7.forbid_else", "naming.service_suffix"],
            "micro_loop": {"total_tasks": 4, "first_pass": 2, "retried": 1, "blocked": 1, "first_pass_rate": 0.50},
        },
        {
            "ticket_id": "P-4", "date": "2026-06-04",
            "rules_triggered": [],
            "rules_silent": ["HP-6.max_for_nesting", "HP-7.forbid_else", "naming.service_suffix"],
            "micro_loop": {"total_tasks": 2, "first_pass": 2, "retried": 0, "blocked": 0, "first_pass_rate": 1.0},
        },
        {
            "ticket_id": "P-5", "date": "2026-06-05",
            "rules_triggered": [
                {"rule": "HP-6.max_for_nesting", "times": 1, "final_resolved": True},
            ],
            "rules_silent": ["HP-7.forbid_else", "naming.service_suffix"],
            "micro_loop": {"total_tasks": 3, "first_pass": 2, "retried": 1, "blocked": 0, "first_pass_rate": 0.67},
        },
    ]


def test_rule_effectiveness_sorted_by_triggers():
    rows = stats.rule_effectiveness(_sample_log())
    assert rows[0]["rule"] == "HP-6.max_for_nesting"
    assert rows[0]["total_triggers"] == 7  # 2+1+3+1
    assert rows[0]["ticket_pct"] == 80     # 4/5 tickets


def test_rule_effectiveness_resolved_rate():
    rows = stats.rule_effectiveness(_sample_log())
    hp6 = next(r for r in rows if r["rule"] == "HP-6.max_for_nesting")
    # P-1 resolved, P-2 resolved, P-3 NOT resolved, P-5 resolved → 3/4 = 75%
    assert hp6["resolved_pct"] == 75


def test_prune_candidates_finds_always_silent():
    candidates = stats.prune_candidates(_sample_log(), threshold=5)
    # HP-7 and naming silent in ALL 5 tickets
    assert "HP-7.forbid_else" in candidates
    assert "naming.service_suffix" in candidates
    # HP-6 was silent in P-4 but triggered in P-1,2,3,5 — not always silent
    assert "HP-6.max_for_nesting" not in candidates


def test_prune_candidates_not_enough_data():
    candidates = stats.prune_candidates(_sample_log()[:3], threshold=5)
    assert candidates == []  # only 3 tickets < threshold 5


def test_quality_trend_shape():
    trend = stats.quality_trend(_sample_log())
    assert len(trend) == 5
    assert trend[0]["first_pass_rate"] == 0.33
    assert trend[4]["first_pass_rate"] == 0.67
    assert trend[0]["blocked"] == 1
    assert trend[4]["blocked"] == 0


def test_quality_trend_improving():
    """first_pass_rate should generally trend upward in sample data."""
    trend = stats.quality_trend(_sample_log())
    rates = [p["first_pass_rate"] for p in trend]
    # Last rate should be higher than first rate
    assert rates[-1] > rates[0]
