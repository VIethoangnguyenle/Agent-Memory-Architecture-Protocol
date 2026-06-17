# SP1c — Outcome Loop Design Spec

> **Ngày:** 2026-06-17  
> **Giải:** W6 (Không có outcome loop) từ AMAP-v3-assessment.md  
> **Phụ thuộc:** SP1a (mechanical gate), SP1b (micro-loop orchestrator)  
> **Scope:** ~235 dòng code, 4 file mới + 4 file sửa nhỏ

---

## 1. Bài toán

Assessment W6: *"Có TOKEN_LOG nhưng không có quality log. Không biết rule nào đáng tiền.
Rule chỉ tích lũy, không bao giờ bị prune → rule bloat → context phình → đúng thứ nó đang chống."*

SP1b micro-loop tạo ra dữ liệu gate (PASS/FAIL, retries, blocked) nhưng **vứt hết** sau khi
ticket xong. Không có cơ chế tổng hợp cross-ticket để trả lời:

1. **Rule nào đáng tiền?** — Rule hay bắt lỗi (giữ) vs rule chưa bao giờ trigger (prune candidate).
2. **Micro-loop có cải thiện quality?** — first_pass_rate tăng dần? blocked giảm dần?

---

## 2. Nguyên lý thiết kế

- **Capture tại nguồn, tổng hợp riêng.** Gate enrichment (orchestrator) giữ data; outcome.py
  tổng hợp; stats.py phân tích. Mỗi phần testable độc lập.
- **Append-only log.** outcome-log.yaml chỉ append, không sửa block cũ. Git tracked = diff được.
- **Ghi TRƯỚC archive.** knowledge-curator di chuyển TASK_QUEUE → archive/. Outcome phải ghi
  trước đó, nếu không data mất.
- **Backward-compatible.** Orchestrator vẫn nhận gate_status string cũ (`"PASS"/"FAIL"`).
  Test SP1b không break.

---

## 3. Kiến trúc

```
Pha 3 micro-loop xong
    │
    ▼
spec-validator.post_apply_verify()          ← đã có (SP1b)
    │
    ▼
★ outcome.build_record(queue, report, ir)   ← MỚI (SP1c)
★ outcome.append_to_log(record, log_path)   ← MỚI
    │
    ▼
knowledge-curator.archive()                 ← đã có
    │
    ▼
(optional) stats.print_report()             ← on-demand
```

---

## 4. Thành phần chi tiết

### 4.1 Gate Enrichment — sửa orchestrator.py

**Vấn đề:** `make_gate_fn()` hiện tại vứt linter output, chỉ giữ PASS/FAIL.

**Sửa 1 — `make_gate_fn()` trả dict thay vì string:**

```python
# TRƯỚC (SP1b)
def make_gate_fn(runner):
    def gate_fn(changed_files):
        exit_code, _output = runner(changed_files)
        return "PASS" if exit_code == 0 else "FAIL"
    return gate_fn

# SAU (SP1c)
def make_gate_fn(runner, parse_fn=None):
    def gate_fn(changed_files):
        exit_code, output = runner(changed_files)
        status = "PASS" if exit_code == 0 else "FAIL"
        violations = parse_fn(output) if parse_fn else []
        return {"status": status, "violations": violations}
    return gate_fn
```

`parse_fn` injected — orchestrator không biết format cụ thể (Checkstyle vs ESLint).
Portable: backend khác chỉ cần inject parser khác.

**Sửa 2 — `apply_result()` lưu gate_history:**

```python
def apply_result(queue, task_id, gate_result, max_retries=2):
    # Backward-compatible: nhận string hoặc dict
    if isinstance(gate_result, str):
        gate_status = gate_result
        violations = []
    else:
        gate_status = gate_result["status"]
        violations = gate_result.get("violations", [])

    t = next((t for t in queue["tasks"] if t["id"] == task_id), None)
    if t is None:
        raise ValueError(f"task {task_id} not in queue")

    # Lưu history per-attempt
    t.setdefault("gate_history", []).append({
        "attempt": t.get("retries", 0),
        "status": gate_status,
        "violations": violations,
    })

    if gate_status == "PASS":
        t["status"] = "done"
        return queue
    if t["retries"] >= max_retries:
        t["status"] = "blocked"
    else:
        t["retries"] += 1
        t["status"] = "in_progress"
    return queue
```

**Sửa 3 — `run_loop()` truyền dict thay vì string:**

Không cần sửa — `run_loop` gọi `gate_fn(changed_files)` rồi truyền kết quả vào
`apply_result()`. Kết quả giờ là dict, `apply_result` đã handle.

### 4.2 Outcome Record Schema

**File:** `.knowledge-layer/long-term/outcome-log.yaml`  
**Format:** YAML list, append-only, git tracked.

```yaml
- ticket_id: "PROJ-123"
  date: "2026-06-17"

  # Bài toán #1: Rule nào đáng tiền?
  rules_triggered:
    - rule: "HP-6.max_for_nesting"
      times: 3
      final_resolved: true    # agent sửa được sau retry
    - rule: "threshold.max_method_lines"
      times: 1
      final_resolved: false   # task bị blocked
  rules_silent: ["HP-7.forbid_else", "naming.service_suffix"]

  # Bài toán #2: Quality trend
  micro_loop:
    total_tasks: 5
    first_pass: 3
    retried: 1
    blocked: 1
    first_pass_rate: 0.60

  extraction:
    verdict: "FLAG"
    clusters: 1

  execution_mode: "inline-reload"
  total_gate_calls: 8
```

### 4.3 outcome.py — Aggregation Logic

**File:** `.agent/tools/microloop-orchestrator/outcome.py`

```python
"""Outcome aggregator: enriched TASK_QUEUE → outcome record → append log."""

import yaml
from pathlib import Path
from datetime import date
from collections import Counter


def _collect_rules(tasks, ir_rules=None):
    """Scan gate_history → rules_triggered + rules_silent."""
    triggered = Counter()
    resolved = {}

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
    """first_pass / retried / blocked counts."""
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
    """Build one outcome record from enriched TASK_QUEUE."""
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
    """Append one record to outcome-log.yaml."""
    path = Path(log_path)
    existing = yaml.safe_load(path.read_text()) if path.exists() else []
    existing = existing or []
    existing.append(record)
    path.write_text(yaml.safe_dump(existing, sort_keys=False, allow_unicode=True))
```

### 4.4 stats.py — CLI Analysis Tool

**File:** `.agent/tools/microloop-orchestrator/stats.py`

```python
"""Outcome stats: rule effectiveness + quality trend + prune candidates.
CLI tool. Usage: python3 stats.py [path-to-outcome-log.yaml]"""

import yaml, sys
from pathlib import Path
from collections import Counter

DEFAULT_LOG = ".knowledge-layer/long-term/outcome-log.yaml"
PRUNE_THRESHOLD = 5


def load_log(path):
    return yaml.safe_load(Path(path).read_text()) or []


def rule_effectiveness(records):
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
    if len(records) < threshold:
        return []
    recent = records[-threshold:]
    silent_sets = [set(r.get("rules_silent", [])) for r in recent]
    always_silent = silent_sets[0]
    for s in silent_sets[1:]:
        always_silent &= s
    return sorted(always_silent)


def quality_trend(records):
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
    records = load_log(log_path)
    if not records:
        print("No outcome data yet.")
        return

    print(f"=== Outcome Report ({len(records)} tickets) ===\n")

    print("📊 Rule Effectiveness (by trigger count):")
    print(f"  {'Rule':<40} {'Triggers':>8} {'Tickets%':>9} {'Resolved%':>10}")
    for row in rule_effectiveness(records):
        print(f"  {row['rule']:<40} {row['total_triggers']:>8} "
              f"{row['ticket_pct']:>8}% {row['resolved_pct']:>9}%")

    prune = prune_candidates(records)
    if prune:
        print(f"\n🗑️  Prune Candidates (silent {PRUNE_THRESHOLD}+ tickets):")
        for r in prune:
            print(f"  - {r}")
    else:
        print(f"\n✅ No prune candidates (need {PRUNE_THRESHOLD}+ tickets)")

    print("\n📈 Quality Trend:")
    for p in quality_trend(records):
        bar = "█" * int(p["first_pass_rate"] * 20)
        warn = f" ⚠️{p['blocked']}blk" if p["blocked"] else ""
        print(f"  {p['date']} {p['ticket']:<15} {p['first_pass_rate']:.0%} {bar}{warn}")


if __name__ == "__main__":
    print_report(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOG)
```

---

## 5. Integration Points

### 5.1 task.md Pha 3 bước 6 — thêm outcome step

```markdown
6. Sau khi micro-loop xong:
   - Chạy `spec-validator.post_apply_verify(...)`.
   - **[SP1c] Ghi outcome record:** đọc TASK_QUEUE (có `gate_history`) +
     EXTRACTION_REPORT → `outcome.build_record()` → `outcome.append_to_log()`
     vào `.knowledge-layer/long-term/outcome-log.yaml`. PHẢI chạy TRƯỚC archive.
```

### 5.2 knowledge-curator/SKILL.md — precondition

```markdown
PRE-CONDITION (SP1c): outcome-log.yaml đã được append TRƯỚC khi archive.
Nếu outcome chưa ghi → WARN vào AGENT_TRANSPARENCY, vẫn archive.
```

### 5.3 outcome-log.yaml — git tracked

File `.knowledge-layer/long-term/outcome-log.yaml` là source-of-truth sống,
PHẢI track trong git (giống knowledge-snapshot.md). KHÔNG gitignore.

---

## 6. Blast Radius

| File | Thay đổi | Dòng |
|---|---|---|
| `orchestrator.py` | Sửa `make_gate_fn` + `apply_result` (gate_history) | ~15 |
| `contract.py` | Validate `gate_history` (optional field) | ~5 |
| `outcome.py` | **Mới** — aggregation logic | ~60 |
| `stats.py` | **Mới** — CLI analysis tool | ~70 |
| `test_outcome.py` | **Mới** | ~40 |
| `test_stats.py` | **Mới** | ~40 |
| `task.md` | Thêm outcome step ở bước 6 | 3 |
| `knowledge-curator SKILL.md` | Thêm precondition | 3 |
| **Tổng** | 4 file mới + 4 file sửa nhỏ | **~236** |

---

## 7. Verification

- Unit test `test_outcome.py`: build_record với fixture TASK_QUEUE có gate_history
  → assert schema đúng, rules_triggered count đúng, rules_silent đúng.
- Unit test `test_stats.py`: rule_effectiveness + prune_candidates + quality_trend
  trên fixture outcome-log nhiều ticket.
- Backward-compat: chạy lại test SP1b hiện có → PASS (apply_result nhận string vẫn OK).
- Integration: chạy full pipeline trên fixture → outcome-log.yaml có đúng 1 record mới.

---

## 8. Không thuộc scope SP1c

- Auto-prune (tự xoá rule) — user quyết dựa trên stats output.
- Multi-language parser (ESLint, Ruff) — SP1c chỉ cung cấp `parse_fn` interface;
  backend cụ thể thuộc SP3.
- Dashboard UI — stats.py là CLI, đủ cho giai đoạn này.
