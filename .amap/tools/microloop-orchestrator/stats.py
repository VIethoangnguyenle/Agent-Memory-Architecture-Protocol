"""Outcome stats: rule effectiveness + quality trend + prune candidates.

CLI tool. Reads outcome-log.yaml and prints actionable insights.
Usage: python3 stats.py [path-to-outcome-log.yaml]
No dependencies beyond PyYAML.
"""

import yaml
import sys
from pathlib import Path
from collections import Counter

DEFAULT_LOG = ".amap/knowledge/long-term/outcome-log.yaml"
PRUNE_THRESHOLD = 5  # silent N ticket liên tiếp → candidate prune


def load_log(path):
    """Load outcome-log.yaml → list of records."""
    return yaml.safe_load(Path(path).read_text()) or []


def rule_effectiveness(records):
    """Per-rule: total triggers, % tickets with trigger, resolved rate."""
    trigger_count = Counter()
    ticket_count = Counter()
    resolved_count = Counter()

    for r in records:
        for rt in r.get("rules_triggered", []):
            rule = rt["rule"]
            trigger_count[rule] += rt["times"]
            ticket_count[rule] += 1
            if rt["final_resolved"]:
                resolved_count[rule] += 1

    total_tickets = len(records)
    return [
        {
            "rule": rule,
            "total_triggers": trigger_count[rule],
            "ticket_pct": round(ticket_count[rule] / total_tickets * 100),
            "resolved_pct": round(resolved_count[rule] / ticket_count[rule] * 100),
        }
        for rule in sorted(trigger_count, key=trigger_count.get, reverse=True)
    ]


def prune_candidates(records, threshold=PRUNE_THRESHOLD):
    """Rules silent in the last N consecutive tickets → candidate prune."""
    if len(records) < threshold:
        return []
    recent = records[-threshold:]
    silent_sets = [set(r.get("rules_silent", [])) for r in recent]
    always_silent = silent_sets[0]
    for s in silent_sets[1:]:
        always_silent &= s
    return sorted(always_silent)


def quality_trend(records):
    """first_pass_rate over time — trending up = micro-loop improving quality."""
    return [
        {
            "ticket": r["ticket_id"],
            "date": r["date"],
            "first_pass_rate": r.get("micro_loop", {}).get("first_pass_rate", 0),
            "blocked": r.get("micro_loop", {}).get("blocked", 0),
        }
        for r in records
    ]


def print_report(log_path=DEFAULT_LOG):
    """Print full outcome report to stdout."""
    records = load_log(log_path)
    if not records:
        print("No outcome data yet.")
        return

    print(f"=== Outcome Report ({len(records)} tickets) ===\n")

    # Rule effectiveness
    print("📊 Rule Effectiveness (by trigger count):")
    print(f"  {'Rule':<40} {'Triggers':>8} {'Tickets%':>9} {'Resolved%':>10}")
    for row in rule_effectiveness(records):
        print(f"  {row['rule']:<40} {row['total_triggers']:>8} "
              f"{row['ticket_pct']:>8}% {row['resolved_pct']:>9}%")

    # Prune candidates
    prune = prune_candidates(records)
    if prune:
        print(f"\n🗑️  Prune Candidates (silent {PRUNE_THRESHOLD}+ tickets):")
        for r in prune:
            print(f"  - {r}")
    else:
        print(f"\n✅ No prune candidates (need {PRUNE_THRESHOLD}+ tickets or all rules active)")

    # Quality trend
    print("\n📈 Quality Trend:")
    for p in quality_trend(records):
        bar = "█" * int(p["first_pass_rate"] * 20)
        warn = f" ⚠️{p['blocked']}blk" if p["blocked"] else ""
        print(f"  {p['date']} {p['ticket']:<15} {p['first_pass_rate']:.0%} {bar}{warn}")


if __name__ == "__main__":
    print_report(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOG)
