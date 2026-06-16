# SP1b — Coding Micro-loop + Extraction Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a portable, filesystem-contract-driven micro-loop orchestrator that rewrites Phase 3 (`/task apply`) into sequential clean-context task execution + extraction review, runnable on any framework (not just Claude).

**Architecture:** A neutral filesystem contract (5 markdown/yaml artifacts) is the core. Pure-logic Python modules (`contract.py`, `orchestrator.py`, `extraction.py`) assemble/parse the contract and run the loop protocol. The orchestrator takes `dispatch_fn` and `gate_fn` via **dependency injection** so it is fully unit-testable with stubs — no Java, no real subagent. Three execution tiers (`subagent`/`fresh-session`/`inline-reload`) implement `dispatch`; `inline-reload` is the lowest-common-denominator that proves no Claude dependency.

**Tech Stack:** Python 3.12, pyyaml, jsonschema, pytest. Follows SP1a tool patterns (`.agent/tools/rule-projector/`): argparse CLI, dict-based data, `sys.path.insert` test imports, fixtures in `tests/fixtures/`.

**Source spec:** [docs/specs/2026-06-17-sp1b-coding-microloop-design.md](../specs/2026-06-17-sp1b-coding-microloop-design.md)

---

## File Structure

```
.agent/tools/microloop-orchestrator/
├── contract.py          # load/dump/validate 5 artifacts (queue, handoff, result, extraction in/out)
├── orchestrator.py      # topo_sort, slice_dna, build_handoff, next_task, apply_result, run_loop
├── extraction.py        # similarity, find_clusters, build_report (HP-10/11 disk-fallback)
├── tiers/
│   ├── __init__.py      # get_dispatch(mode) -> dispatch_fn
│   ├── inline_reload.py # dispatch in same session (LCD)
│   ├── fresh_session.py # write handoff + instruct new session
│   └── subagent.py      # dispatch via Agent tool (Claude)
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   ├── test_contract.py
│   ├── test_toposort.py
│   ├── test_slice.py
│   ├── test_handoff.py
│   ├── test_protocol.py
│   ├── test_degradation.py
│   └── test_extraction.py
├── requirements.txt
└── README.md
.agent/profiles/execution-mode.yaml      # declares active tier
.agent/procedures/executor.md            # executor steps (fresh-session/inline tiers)
.agent/procedures/reviewer.md            # reviewer steps (extraction)
```

Modified (Phase 3 rewrite):
- `docs/workflows/01-task.md` — Phase 3 → orchestrated micro-loop
- `.agent/skills/spec-validator/SKILL.md` §6 — split mechanical vs semantic

---

## Task 1: Scaffold tool directory

**Files:**
- Create: `.agent/tools/microloop-orchestrator/requirements.txt`
- Create: `.agent/tools/microloop-orchestrator/tiers/__init__.py`
- Create: `.agent/tools/microloop-orchestrator/tests/__init__.py`
- Create: `.agent/tools/microloop-orchestrator/tests/fixtures/.gitkeep`

- [ ] **Step 1: Create requirements.txt**

```
pyyaml>=6.0
jsonschema>=4.0
pytest>=7.0
```

- [ ] **Step 2: Create empty package files**

`tiers/__init__.py`: (empty for now, filled in Task 10)
`tests/__init__.py`: (empty)
`tests/fixtures/.gitkeep`: (empty)

- [ ] **Step 3: Commit**

```bash
git add .agent/tools/microloop-orchestrator/
git commit -m "feat(sp1b): scaffold microloop-orchestrator tool + deps"
```

---

## Task 2: contract.py — queue load/dump + validate

**Files:**
- Create: `.agent/tools/microloop-orchestrator/contract.py`
- Test: `.agent/tools/microloop-orchestrator/tests/test_contract.py`

The queue is the durable state. Schema (from spec §5.1): `ticket_id`, `spec_path`, `execution_mode`, `tasks[]` each with `id`, `desc`, `depends_on[]`, `status` (pending|in_progress|done|blocked), `retries`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_contract.py
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import contract  # noqa: E402

def test_queue_roundtrip(tmp_path):
    q = {
        "ticket_id": "ABC-1",
        "spec_path": "openspec/changes/abc-1/",
        "execution_mode": "inline-reload",
        "tasks": [
            {"id": "T1", "desc": "base", "depends_on": [], "status": "pending", "retries": 0},
        ],
    }
    p = tmp_path / "TASK_QUEUE.md"
    contract.dump_queue(q, str(p))
    loaded = contract.load_queue(str(p))
    assert loaded == q

def test_queue_validate_rejects_bad_status(tmp_path):
    q = {"ticket_id": "X", "spec_path": "p", "execution_mode": "inline-reload",
         "tasks": [{"id": "T1", "desc": "d", "depends_on": [], "status": "nope", "retries": 0}]}
    import pytest
    with pytest.raises(ValueError):
        contract.validate_queue(q)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd .agent/tools/microloop-orchestrator && python -m pytest tests/test_contract.py -v`
Expected: FAIL with "No module named 'contract'"

- [ ] **Step 3: Write minimal implementation**

```python
# contract.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_contract.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add .agent/tools/microloop-orchestrator/contract.py .agent/tools/microloop-orchestrator/tests/test_contract.py
git commit -m "feat(sp1b): contract.py — queue load/dump/validate"
```

---

## Task 3: contract.py — handoff + result load/dump

**Files:**
- Modify: `.agent/tools/microloop-orchestrator/contract.py`
- Test: `.agent/tools/microloop-orchestrator/tests/test_contract.py:append`

Handoff schema (spec §5.2): `task`, `dna_slice`, `spec_slice`, `snapshot_slice`, `written_files[]`, `boundary[]`, `feedback`. Result schema (spec §5.3): `task_id`, `changed_files[]`, `gate_status`, `gate_violations[]`, `self_flagged[]`.

- [ ] **Step 1: Write the failing test (append to test_contract.py)**

```python
def test_handoff_roundtrip(tmp_path):
    h = {
        "task": {"id": "T2", "desc": "XaHandler extends BaseXHandler"},
        "dna_slice": {"hard_principles": ["HP-6"], "complexity_thresholds": {}, "style": []},
        "spec_slice": "implement XaHandler",
        "snapshot_slice": "Validation Chain section",
        "written_files": [{"path": "BaseXHandler.java", "summary": "template method"}],
        "boundary": ["do not touch YyyService"],
        "feedback": None,
    }
    p = tmp_path / "TASK_HANDOFF.md"
    contract.dump_handoff(h, str(p))
    assert contract.load_handoff(str(p)) == h

def test_result_roundtrip(tmp_path):
    r = {
        "task_id": "T2",
        "changed_files": [{"path": "XaHandler.java", "change_type": "NEW", "summary": "extends base"}],
        "gate_status": "PASS",
        "gate_violations": [],
        "self_flagged": [],
    }
    p = tmp_path / "TASK_RESULT.md"
    contract.dump_result(r, str(p))
    assert contract.load_result(str(p)) == r
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_contract.py -k "handoff or result" -v`
Expected: FAIL with "module 'contract' has no attribute 'dump_handoff'"

- [ ] **Step 3: Write minimal implementation (append to contract.py)**

```python
def validate_handoff(h):
    for key in ("task", "dna_slice", "spec_slice", "snapshot_slice", "written_files", "boundary"):
        if key not in h:
            raise ValueError(f"handoff missing key: {key}")
    return h


def load_handoff(path):
    return validate_handoff(_load(path))


def dump_handoff(h, path):
    validate_handoff(h)
    _dump(h, path)


def validate_result(r):
    for key in ("task_id", "changed_files", "gate_status"):
        if key not in r:
            raise ValueError(f"result missing key: {key}")
    return r


def load_result(path):
    return validate_result(_load(path))


def dump_result(r, path):
    validate_result(r)
    _dump(r, path)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_contract.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add .agent/tools/microloop-orchestrator/contract.py .agent/tools/microloop-orchestrator/tests/test_contract.py
git commit -m "feat(sp1b): contract.py — handoff + result load/dump"
```

---

## Task 4: orchestrator.py — topo_sort with cycle detection

**Files:**
- Create: `.agent/tools/microloop-orchestrator/orchestrator.py`
- Test: `.agent/tools/microloop-orchestrator/tests/test_toposort.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_toposort.py
from pathlib import Path
import sys, pytest
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import orchestrator  # noqa: E402

def test_base_before_dependents():
    tasks = [
        {"id": "T2", "depends_on": ["T1"]},
        {"id": "T1", "depends_on": []},
        {"id": "T3", "depends_on": ["T1"]},
    ]
    ordered = [t["id"] for t in orchestrator.topo_sort(tasks)]
    assert ordered.index("T1") < ordered.index("T2")
    assert ordered.index("T1") < ordered.index("T3")

def test_cycle_raises():
    tasks = [
        {"id": "A", "depends_on": ["B"]},
        {"id": "B", "depends_on": ["A"]},
    ]
    with pytest.raises(ValueError, match="cycle"):
        orchestrator.topo_sort(tasks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_toposort.py -v`
Expected: FAIL with "No module named 'orchestrator'"

- [ ] **Step 3: Write minimal implementation**

```python
# orchestrator.py
"""Micro-loop orchestrator: topo-sort, slice assembly, loop protocol.

All functions are pure logic. run_loop() takes dispatch_fn and gate_fn via
dependency injection so the whole protocol is unit-testable with stubs —
no Java, no real subagent.
"""


def topo_sort(tasks):
    """Kahn's algorithm. Returns tasks ordered so deps come first. Raises on cycle."""
    by_id = {t["id"]: t for t in tasks}
    indeg = {t["id"]: 0 for t in tasks}
    for t in tasks:
        for _ in t.get("depends_on", []):
            indeg[t["id"]] += 1
    ready = sorted([tid for tid, d in indeg.items() if d == 0])
    ordered = []
    while ready:
        tid = ready.pop(0)
        ordered.append(by_id[tid])
        for t in tasks:
            if tid in t.get("depends_on", []):
                indeg[t["id"]] -= 1
                if indeg[t["id"]] == 0:
                    ready.append(t["id"])
        ready.sort()
    if len(ordered) != len(tasks):
        raise ValueError("dependency cycle detected in tasks")
    return ordered
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_toposort.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add .agent/tools/microloop-orchestrator/orchestrator.py .agent/tools/microloop-orchestrator/tests/test_toposort.py
git commit -m "feat(sp1b): orchestrator topo_sort + cycle detection"
```

---

## Task 5: orchestrator.py — slice_dna

**Files:**
- Modify: `.agent/tools/microloop-orchestrator/orchestrator.py`
- Test: `.agent/tools/microloop-orchestrator/tests/test_slice.py`

`slice_dna` extracts ONLY the principle entries relevant to a task (anti-bloat — spec §11 handoff assembly). Input: full DNA dict + list of principle ids. Output: dict with matching `hard_principles`/`style_preferences` entries + full `complexity_thresholds` (always included — they are global).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_slice.py
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import orchestrator  # noqa: E402

DNA = {
    "complexity_thresholds": {"max_nesting_depth": 1},
    "hard_principles": [
        {"id": "HP-6", "name": "Zero Nesting"},
        {"id": "HP-7", "name": "No Else"},
        {"id": "HP-1", "name": "Chain of Responsibility"},
    ],
    "style_preferences": [{"id": "SP-1", "prefer": "record"}],
}

def test_slice_includes_only_requested_principles():
    s = orchestrator.slice_dna(DNA, ["HP-6", "SP-1"])
    hp_ids = [p["id"] for p in s["hard_principles"]]
    sp_ids = [p["id"] for p in s["style_preferences"]]
    assert hp_ids == ["HP-6"]
    assert sp_ids == ["SP-1"]
    assert "HP-7" not in hp_ids and "HP-1" not in hp_ids

def test_slice_always_includes_thresholds():
    s = orchestrator.slice_dna(DNA, [])
    assert s["complexity_thresholds"] == {"max_nesting_depth": 1}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_slice.py -v`
Expected: FAIL with "module 'orchestrator' has no attribute 'slice_dna'"

- [ ] **Step 3: Write minimal implementation (append to orchestrator.py)**

```python
def slice_dna(dna, principle_ids):
    """Extract only requested principle entries + always-global thresholds (anti-bloat)."""
    wanted = set(principle_ids)
    return {
        "complexity_thresholds": dna.get("complexity_thresholds", {}),
        "hard_principles": [p for p in dna.get("hard_principles", []) if p["id"] in wanted],
        "style_preferences": [p for p in dna.get("style_preferences", []) if p["id"] in wanted],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_slice.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add .agent/tools/microloop-orchestrator/orchestrator.py .agent/tools/microloop-orchestrator/tests/test_slice.py
git commit -m "feat(sp1b): orchestrator slice_dna — anti-bloat DNA slicing"
```

---

## Task 6: orchestrator.py — build_handoff

**Files:**
- Modify: `.agent/tools/microloop-orchestrator/orchestrator.py`
- Test: `.agent/tools/microloop-orchestrator/tests/test_handoff.py`

`build_handoff` assembles the TASK_HANDOFF dict (spec §5.2) from a task, sliced DNA, spec text, snapshot text, written-files summary, boundary, and optional feedback.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_handoff.py
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import orchestrator  # noqa: E402

def test_build_handoff_shape():
    task = {"id": "T2", "desc": "XaHandler", "depends_on": ["T1"],
            "principle_ids": ["HP-6"]}
    dna = {"complexity_thresholds": {"max_nesting_depth": 1},
           "hard_principles": [{"id": "HP-6", "name": "Zero Nesting"}],
           "style_preferences": []}
    h = orchestrator.build_handoff(
        task=task, dna=dna, spec_slice="impl XaHandler",
        snapshot_slice="chain section",
        written_files=[{"path": "BaseXHandler.java", "summary": "tmpl"}],
        boundary=["no YyyService"], feedback=None)
    assert h["task"] == {"id": "T2", "desc": "XaHandler"}
    assert [p["id"] for p in h["dna_slice"]["hard_principles"]] == ["HP-6"]
    assert h["spec_slice"] == "impl XaHandler"
    assert h["written_files"][0]["path"] == "BaseXHandler.java"
    assert h["feedback"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_handoff.py -v`
Expected: FAIL with "module 'orchestrator' has no attribute 'build_handoff'"

- [ ] **Step 3: Write minimal implementation (append to orchestrator.py)**

```python
def build_handoff(task, dna, spec_slice, snapshot_slice, written_files, boundary, feedback=None):
    """Assemble TASK_HANDOFF dict (spec §5.2). dna_slice is anti-bloat (only task principles)."""
    return {
        "task": {"id": task["id"], "desc": task["desc"]},
        "dna_slice": slice_dna(dna, task.get("principle_ids", [])),
        "spec_slice": spec_slice,
        "snapshot_slice": snapshot_slice,
        "written_files": written_files,
        "boundary": boundary,
        "feedback": feedback,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_handoff.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add .agent/tools/microloop-orchestrator/orchestrator.py .agent/tools/microloop-orchestrator/tests/test_handoff.py
git commit -m "feat(sp1b): orchestrator build_handoff assembly"
```

---

## Task 7: orchestrator.py — next_task + apply_result state machine

**Files:**
- Modify: `.agent/tools/microloop-orchestrator/orchestrator.py`
- Test: `.agent/tools/microloop-orchestrator/tests/test_protocol.py`

State transitions (spec §6): `next_task` picks the next runnable task (resume `in_progress` first, else first `pending` whose `depends_on` are all `done`). `apply_result` mutates queue: gate PASS → `done`; gate FAIL → `retries+1`, stay runnable; FAIL with `retries >= max_retries` → `blocked`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_protocol.py
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import orchestrator  # noqa: E402

def _queue():
    return {"ticket_id": "X", "spec_path": "p", "execution_mode": "inline-reload",
            "tasks": [
                {"id": "T1", "desc": "base", "depends_on": [], "status": "done", "retries": 0},
                {"id": "T2", "desc": "dep", "depends_on": ["T1"], "status": "pending", "retries": 0},
            ]}

def test_next_task_respects_deps():
    q = _queue()
    assert orchestrator.next_task(q)["id"] == "T2"

def test_next_task_resumes_in_progress():
    q = _queue()
    q["tasks"][1]["status"] = "in_progress"
    assert orchestrator.next_task(q)["id"] == "T2"

def test_next_task_none_when_all_done():
    q = _queue()
    q["tasks"][1]["status"] = "done"
    assert orchestrator.next_task(q) is None

def test_apply_result_pass_marks_done():
    q = _queue()
    orchestrator.apply_result(q, "T2", "PASS", max_retries=2)
    t2 = [t for t in q["tasks"] if t["id"] == "T2"][0]
    assert t2["status"] == "done"

def test_apply_result_fail_retries_then_blocks():
    q = _queue()
    orchestrator.apply_result(q, "T2", "FAIL", max_retries=2)  # retries 1
    orchestrator.apply_result(q, "T2", "FAIL", max_retries=2)  # retries 2
    t2 = [t for t in q["tasks"] if t["id"] == "T2"][0]
    assert t2["status"] == "in_progress" and t2["retries"] == 2
    orchestrator.apply_result(q, "T2", "FAIL", max_retries=2)  # exceeds
    assert t2["status"] == "blocked"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_protocol.py -v`
Expected: FAIL with "module 'orchestrator' has no attribute 'next_task'"

- [ ] **Step 3: Write minimal implementation (append to orchestrator.py)**

```python
def next_task(queue):
    """Resume in_progress first; else first pending whose deps are all done."""
    tasks = queue["tasks"]
    done = {t["id"] for t in tasks if t["status"] == "done"}
    for t in tasks:
        if t["status"] == "in_progress":
            return t
    for t in tasks:
        if t["status"] == "pending" and all(d in done for d in t.get("depends_on", [])):
            return t
    return None


def apply_result(queue, task_id, gate_status, max_retries=2):
    """Mutate queue per gate outcome. PASS->done; FAIL->retry; FAIL over budget->blocked."""
    t = next(t for t in queue["tasks"] if t["id"] == task_id)
    if gate_status == "PASS":
        t["status"] = "done"
        return queue
    # FAIL
    if t["retries"] >= max_retries:
        t["status"] = "blocked"
    else:
        t["retries"] += 1
        t["status"] = "in_progress"
    return queue
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_protocol.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add .agent/tools/microloop-orchestrator/orchestrator.py .agent/tools/microloop-orchestrator/tests/test_protocol.py
git commit -m "feat(sp1b): orchestrator next_task + apply_result state machine"
```

---

## Task 8: orchestrator.py — run_loop (injected dispatch + gate, resume)

**Files:**
- Modify: `.agent/tools/microloop-orchestrator/orchestrator.py`
- Test: `.agent/tools/microloop-orchestrator/tests/test_protocol.py:append`

`run_loop` drives the whole loop. Signature: `run_loop(queue, dispatch_fn, gate_fn, max_retries=2)`. Per runnable task: set `in_progress` → `dispatch_fn(task)` (executor writes code, returns changed_files) → `gate_fn(changed_files)` returns "PASS"/"FAIL" → `apply_result`. Stops when no runnable task OR a task becomes `blocked`. Returns the final queue. `set_in_progress` is set before dispatch so a crash leaves a resumable marker.

- [ ] **Step 1: Write the failing test (append to test_protocol.py)**

```python
def test_run_loop_completes_with_stubs():
    q = {"ticket_id": "X", "spec_path": "p", "execution_mode": "inline-reload",
         "tasks": [
             {"id": "T1", "desc": "base", "depends_on": [], "status": "pending", "retries": 0},
             {"id": "T2", "desc": "dep", "depends_on": ["T1"], "status": "pending", "retries": 0},
         ]}
    dispatched = []
    def dispatch_fn(task):
        dispatched.append(task["id"])
        return [{"path": f"{task['id']}.java", "change_type": "NEW", "summary": "ok"}]
    def gate_fn(changed_files):
        return "PASS"
    final = orchestrator.run_loop(q, dispatch_fn, gate_fn)
    assert dispatched == ["T1", "T2"]  # base first
    assert all(t["status"] == "done" for t in final["tasks"])

def test_run_loop_stops_on_blocked():
    q = {"ticket_id": "X", "spec_path": "p", "execution_mode": "inline-reload",
         "tasks": [{"id": "T1", "desc": "base", "depends_on": [], "status": "pending", "retries": 0}]}
    def dispatch_fn(task):
        return [{"path": "T1.java", "change_type": "NEW", "summary": "bad"}]
    def gate_fn(changed_files):
        return "FAIL"
    final = orchestrator.run_loop(q, dispatch_fn, gate_fn, max_retries=2)
    t1 = final["tasks"][0]
    assert t1["status"] == "blocked" and t1["retries"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_protocol.py -k run_loop -v`
Expected: FAIL with "module 'orchestrator' has no attribute 'run_loop'"

- [ ] **Step 3: Write minimal implementation (append to orchestrator.py)**

```python
def run_loop(queue, dispatch_fn, gate_fn, max_retries=2):
    """Drive the micro-loop. dispatch_fn(task)->changed_files; gate_fn(changed_files)->'PASS'|'FAIL'.

    Pure protocol: no knowledge of tiers or the real gate — both injected. This is
    what makes the loop platform-agnostic and unit-testable (portability gate).
    """
    while True:
        t = next_task(queue)
        if t is None:
            return queue
        t["status"] = "in_progress"  # resumable marker before dispatch
        changed_files = dispatch_fn(t)
        gate_status = gate_fn(changed_files)
        apply_result(queue, t["id"], gate_status, max_retries=max_retries)
        if t["status"] == "blocked":
            return queue
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_protocol.py -v`
Expected: PASS (7 passed)

- [ ] **Step 5: Commit**

```bash
git add .agent/tools/microloop-orchestrator/orchestrator.py .agent/tools/microloop-orchestrator/tests/test_protocol.py
git commit -m "feat(sp1b): orchestrator run_loop — injected dispatch+gate"
```

---

## Task 9: extraction.py — similarity, find_clusters, build_report

**Files:**
- Create: `.agent/tools/microloop-orchestrator/extraction.py`
- Test: `.agent/tools/microloop-orchestrator/tests/test_extraction.py`
- Create fixture: `.agent/tools/microloop-orchestrator/tests/fixtures/sample-extraction-input.md`

Disk-fallback HP-10/11 (spec §8): group files by content similarity, flag clusters ≥ threshold, propose Template Method. Similarity = Jaccard over normalized non-trivial lines (strip whitespace, drop lines < 4 chars to ignore braces).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_extraction.py
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import extraction  # noqa: E402

# A and B share 6 method lines, differ only in the last; the class-declaration line
# also differs. Jaccard = 6 / 10 = 0.6 — comfortably above the 0.5 cluster threshold.
A = "public class Xa {\n  validate();\n  enrich();\n  transform();\n  route();\n  persist();\n  log();\n  audit();\n}"
B = "public class Xb {\n  validate();\n  enrich();\n  transform();\n  route();\n  persist();\n  log();\n  notify();\n}"
C = "public class Zz {\n  totallyDifferent();\n  unrelated();\n}"

def test_similarity_high_for_near_duplicates():
    assert extraction.similarity(A, B) >= 0.5

def test_similarity_low_for_unrelated():
    assert extraction.similarity(A, C) < 0.3

def test_find_clusters_groups_duplicates():
    files = [
        {"path": "Xa.java", "content": A},
        {"path": "Xb.java", "content": B},
        {"path": "Zz.java", "content": C},
    ]
    clusters = extraction.find_clusters(files, threshold=0.5)
    paths = sorted([f["path"] for c in clusters for f in c])
    assert "Xa.java" in paths and "Xb.java" in paths
    assert len(clusters) == 1  # only the duplicate pair clusters

def test_build_report_flags_template_method():
    files = [{"path": "Xa.java", "content": A}, {"path": "Xb.java", "content": B}]
    report = extraction.build_report(files, threshold=0.5)
    assert report["verdict"] in ("FLAG", "CLEAN")
    assert report["verdict"] == "FLAG"
    assert "Template Method" in report["clusters"][0]["suggestion"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_extraction.py -v`
Expected: FAIL with "No module named 'extraction'"

- [ ] **Step 3: Write minimal implementation**

```python
# extraction.py
"""Extraction review (HP-10/11) disk-fallback: group new files by content similarity,
flag clusters as Template Method candidates. No UA graph, no vector top-k (spec §8)."""


def _lines(text):
    return {ln.strip() for ln in text.splitlines() if len(ln.strip()) >= 4}


def similarity(a, b):
    la, lb = _lines(a), _lines(b)
    if not la or not lb:
        return 0.0
    return len(la & lb) / len(la | lb)


def find_clusters(files, threshold=0.7):
    """Union near-duplicate files into clusters. Returns list of clusters (each a list of files)."""
    parent = list(range(len(files)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            if similarity(files[i]["content"], files[j]["content"]) >= threshold:
                parent[find(i)] = find(j)
    groups = {}
    for i, f in enumerate(files):
        groups.setdefault(find(i), []).append(f)
    return [g for g in groups.values() if len(g) > 1]


def build_report(files, threshold=0.7):
    clusters = find_clusters(files, threshold)
    return {
        "verdict": "FLAG" if clusters else "CLEAN",
        "clusters": [
            {
                "files": [f["path"] for f in c],
                "suggestion": "Extract Template Method: base class holds shared steps, "
                              "abstract methods for the differing step (HP-10/HP-11).",
            }
            for c in clusters
        ],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_extraction.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Create human-readable fixture for reference**

`tests/fixtures/sample-extraction-input.md`:
```yaml
ticket_id: "ABC-1"
new_files:
  - path: "XaHandler.java"
    content: "public class Xa { validate(); enrich(); transform(); route(); persist(); log(); audit(); }"
  - path: "XbHandler.java"
    content: "public class Xb { validate(); enrich(); transform(); route(); persist(); log(); notify(); }"
  - path: "ZzService.java"
    content: "public class Zz { totallyDifferent(); unrelated(); }"
```

- [ ] **Step 6: Commit**

```bash
git add .agent/tools/microloop-orchestrator/extraction.py .agent/tools/microloop-orchestrator/tests/test_extraction.py .agent/tools/microloop-orchestrator/tests/fixtures/sample-extraction-input.md
git commit -m "feat(sp1b): extraction.py — HP-10/11 disk-fallback clustering"
```

---

## Task 10: tiers/ — dispatch adapters + degradation test

**Files:**
- Create: `.agent/tools/microloop-orchestrator/tiers/inline_reload.py`
- Create: `.agent/tools/microloop-orchestrator/tiers/fresh_session.py`
- Create: `.agent/tools/microloop-orchestrator/tiers/subagent.py`
- Modify: `.agent/tools/microloop-orchestrator/tiers/__init__.py`
- Test: `.agent/tools/microloop-orchestrator/tests/test_degradation.py`

Each tier exposes `dispatch(handoff_path, result_path)`. The agent (any platform) reads the handoff, generates code, writes the result — the Python side only assembles the prompt/instruction and points to the contract files. The degradation test proves `run_loop` completes at the `inline-reload` tier **without importing `subagent.py`** (no Agent-tool dependency).

> **Two-"dispatch" seam (read carefully — they are different layers):**
> - `tier.dispatch(handoff_path, result_path) -> str` returns the **instruction/prompt** the host agent executes. Pure string assembly; no code generation happens in Python.
> - `run_loop`'s injected `dispatch_fn(task) -> changed_files` is the **runtime wrapper** the host builds: it calls `tier.dispatch(...)`, lets the executor (subagent / new session / inline) act and write `TASK_RESULT.md`, then reads `changed_files` back from that result. This wrapper is inherently agent-interactive, so it is NOT unit-tested in the AMAP repo — `run_loop` is tested with a **stub** `dispatch_fn` (Task 8) and the tiers are tested for prompt assembly (this task). Wiring them is a host responsibility documented in `executor.md` (Task 12), not Python code in this repo.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_degradation.py
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import orchestrator  # noqa: E402
from tiers import get_dispatch  # noqa: E402

def test_inline_reload_dispatch_resolves():
    fn = get_dispatch("inline-reload")
    assert callable(fn)

def test_get_dispatch_rejects_unknown():
    import pytest
    with pytest.raises(ValueError):
        get_dispatch("telepathy")

def test_loop_completes_without_subagent_module(monkeypatch):
    # Portability gate: simulate a platform with NO Agent tool by blocking the import.
    monkeypatch.setitem(sys.modules, "tiers.subagent", None)
    q = {"ticket_id": "X", "spec_path": "p", "execution_mode": "inline-reload",
         "tasks": [{"id": "T1", "desc": "base", "depends_on": [], "status": "pending", "retries": 0}]}
    def dispatch_fn(task):
        return [{"path": "T1.java", "change_type": "NEW", "summary": "ok"}]
    def gate_fn(_):
        return "PASS"
    final = orchestrator.run_loop(q, dispatch_fn, gate_fn)
    assert final["tasks"][0]["status"] == "done"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_degradation.py -v`
Expected: FAIL with "cannot import name 'get_dispatch' from 'tiers'"

- [ ] **Step 3: Write the tier modules**

`tiers/inline_reload.py`:
```python
"""inline-reload tier (LCD): executor runs in the SAME session.

dispatch() returns an instruction string telling the agent to reload the handoff
slice (evicting stale exploration context from attention) and generate code for
this one task, then write TASK_RESULT. No Agent tool required."""


def dispatch(handoff_path, result_path):
    return (
        f"RELOAD the slice in {handoff_path} (drop prior exploration from attention). "
        f"Generate code for THIS task only, reading existing files from disk. "
        f"Then write the outcome to {result_path} per the TASK_RESULT schema."
    )
```

`tiers/fresh_session.py`:
```python
"""fresh-session tier (Cursor/Antigravity): executor runs in a NEW session/context.

dispatch() returns an instruction telling the user/host to open a fresh context and
run the executor procedure against the handoff. Clean context via session boundary."""


def dispatch(handoff_path, result_path):
    return (
        f"OPEN A NEW SESSION/CONTEXT and run .agent/procedures/executor.md against "
        f"{handoff_path}. The executor writes its outcome to {result_path}."
    )
```

`tiers/subagent.py`:
```python
"""subagent tier (Claude Code): executor runs as a dispatched Agent-tool subagent.

dispatch() returns the subagent prompt. The host (Claude Code) is responsible for
spawning the Agent with this prompt; full context isolation."""


def dispatch(handoff_path, result_path):
    return (
        f"You are a code-executor subagent. Read {handoff_path}, read existing files "
        f"from disk, generate code for the single task only, respect boundary constraints, "
        f"then write {result_path} per the TASK_RESULT schema."
    )
```

`tiers/__init__.py`:
```python
"""Tier registry: maps execution_mode -> dispatch function.

Importing a tier is lazy so a platform missing one tier's deps never breaks the others
(portability)."""
import importlib

_MODES = {
    "inline-reload": "inline_reload",
    "fresh-session": "fresh_session",
    "subagent": "subagent",
}


def get_dispatch(mode):
    if mode not in _MODES:
        raise ValueError(f"unknown execution_mode: {mode}")
    module = importlib.import_module(f"tiers.{_MODES[mode]}")
    return module.dispatch
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_degradation.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add .agent/tools/microloop-orchestrator/tiers/
git add .agent/tools/microloop-orchestrator/tests/test_degradation.py
git commit -m "feat(sp1b): execution tiers + degradation (portability) test"
```

---

## Task 11: execution-mode profile + gate wiring

**Files:**
- Create: `.agent/profiles/execution-mode.yaml`
- Modify: `.agent/tools/microloop-orchestrator/orchestrator.py` (add `make_gate_fn` adapter to SP1a)
- Test: `.agent/tools/microloop-orchestrator/tests/test_protocol.py:append`

`make_gate_fn` adapts the SP1a mechanical gate into the `gate_fn(changed_files)->'PASS'|'FAIL'` shape `run_loop` expects. In the AMAP repo (no Java/checkstyle), it accepts an injected `runner` so it is testable; the real runner shells out to the SP1a pre-commit/checkstyle path at the target project.

- [ ] **Step 1: Create the profile**

`.agent/profiles/execution-mode.yaml`:
```yaml
# Declares the active micro-loop execution tier for THIS platform.
# The ONLY place platform-specifics live. Change one line to retarget.
#   subagent      → Claude Code (Agent tool, full isolation)
#   fresh-session → Cursor / Antigravity (new session per task)
#   inline-reload → fallback single-session (LCD; always works)
execution_mode: inline-reload
max_retries: 2
gate:
  # Path to the SP1a generated ruleset at the target project.
  checkstyle_xml: ".agent/tools/rule-projector/generated/checkstyle.generated.xml"
  # Command template; {xml} and {files} are substituted. Empty in AMAP repo (no Java).
  command: "checkstyle -c {xml} {files}"
```

- [ ] **Step 2: Write the failing test (append to test_protocol.py)**

```python
def test_make_gate_fn_maps_runner_output():
    # runner returns (exit_code, output); 0 => PASS, nonzero => FAIL
    def ok_runner(changed_files):
        return (0, "")
    def bad_runner(changed_files):
        return (1, "NestedForDepth violation")
    gate_ok = orchestrator.make_gate_fn(ok_runner)
    gate_bad = orchestrator.make_gate_fn(bad_runner)
    files = [{"path": "X.java"}]
    assert gate_ok(files) == "PASS"
    assert gate_bad(files) == "FAIL"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_protocol.py -k make_gate_fn -v`
Expected: FAIL with "module 'orchestrator' has no attribute 'make_gate_fn'"

- [ ] **Step 4: Write minimal implementation (append to orchestrator.py)**

```python
def make_gate_fn(runner):
    """Adapt a (changed_files)->(exit_code, output) runner into gate_fn->'PASS'|'FAIL'.

    The real runner shells out to the SP1a mechanical gate (checkstyle on the generated
    ruleset). Injected so the protocol is testable without Java."""
    def gate_fn(changed_files):
        exit_code, _output = runner(changed_files)
        return "PASS" if exit_code == 0 else "FAIL"
    return gate_fn
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_protocol.py -v`
Expected: PASS (8 passed)

- [ ] **Step 6: Commit**

```bash
git add .agent/profiles/execution-mode.yaml .agent/tools/microloop-orchestrator/orchestrator.py .agent/tools/microloop-orchestrator/tests/test_protocol.py
git commit -m "feat(sp1b): execution-mode profile + SP1a gate adapter"
```

---

## Task 12: Procedures for executor + reviewer

**Files:**
- Create: `.agent/procedures/executor.md`
- Create: `.agent/procedures/reviewer.md`

These are the platform-neutral step lists an agent follows when acting as executor (fresh-session/inline tiers) or reviewer (extraction). No code; markdown procedures consumed by the agent.

- [ ] **Step 1: Write executor.md**

`.agent/procedures/executor.md`:
```markdown
# Procedure: Executor (one micro-loop task)

> Consumed by the agent acting as code-executor. Input: a TASK_HANDOFF.md path.
> Output: TASK_RESULT.md. Platform-neutral — same steps on every tier.

1. Read the TASK_HANDOFF at the given path. Note: task, dna_slice, spec_slice,
   snapshot_slice, written_files, boundary, feedback.
2. Read the actual existing files listed in `written_files` FROM DISK (not just the
   summaries) so inheritance is consistent.
3. Generate code for THIS task ONLY. Obey:
   - dna_slice.hard_principles (REJECT_* = hard) and complexity_thresholds.
   - boundary constraints — do not touch listed files/packages.
   - If `feedback` is present (a retry), fix exactly what it reports.
4. Write changed files to disk.
5. Write TASK_RESULT.md: task_id, changed_files (path/change_type/summary),
   gate_status left as "PENDING" (orchestrator fills it), self_flagged for anything
   you are unsure about.
6. Stop. Do NOT advance to the next task — the orchestrator owns the loop.
```

- [ ] **Step 2: Write reviewer.md**

`.agent/procedures/reviewer.md`:
```markdown
# Procedure: Reviewer (extraction review, once per ticket)

> Consumed by the agent acting as extraction reviewer. Input: EXTRACTION_INPUT.md
> (ALL new/changed files). Output: EXTRACTION_REPORT.md. HP-10/11.

1. Read EXTRACTION_INPUT.md — the COMPLETE set of new files (not a top-k slice).
2. Enumerate sibling classes:
   - If a code-graph capability (UA graph) is available, query it for siblings.
   - Otherwise (disk-fallback), group the files yourself by BUSINESS ESSENCE
     (HP-11 — not by action name).
3. For each group with ≥70% logic overlap, flag a Template Method opportunity
   (HP-10): base class holds shared steps, abstract methods for the differing step.
4. Write EXTRACTION_REPORT.md: verdict (FLAG|CLEAN), clusters (files + suggestion).
5. HP-10/11 are FLAG_AND_WARN — present as recommendation. Do NOT auto-refactor or
   block. The user decides.
```

- [ ] **Step 3: Commit**

```bash
git add .agent/procedures/executor.md .agent/procedures/reviewer.md
git commit -m "feat(sp1b): executor + reviewer procedures (platform-neutral)"
```

---

## Task 13: Rewrite Phase 3 workflow + split spec-validator §6

**Files:**
- Modify: `docs/workflows/01-task.md` (Phase 3 section)
- Modify: `.agent/skills/spec-validator/SKILL.md` (§6)

- [ ] **Step 1: Read current Phase 3 + spec-validator §6**

Run:
```bash
grep -n "Pha 3" docs/workflows/01-task.md
sed -n '190,270p' .agent/skills/spec-validator/SKILL.md
```

- [ ] **Step 2: Rewrite Phase 3 in 01-task.md**

Replace the Phase 3 numbered list (the `## Pha 3 — Apply spec (/task apply)` block) with:

```markdown
## Pha 3 — Apply spec (`/task apply`) — Micro-loop (SP1b)

1. Đọc spec `tasks.md`, tóm tắt files/modules sẽ chạm.
2. **spec-validator** → pre_apply_gate + ac_coverage.
3. Hỏi xác nhận cuối cùng.
4. **Orchestrate micro-loop** (`.agent/tools/microloop-orchestrator/`):
   a. topo-sort tasks (base trước) → `TASK_QUEUE.md`.
   b. Đọc tier từ `.agent/profiles/execution-mode.yaml`.
   c. Loop mỗi task: lắp `TASK_HANDOFF` (DNA slice + spec slice + snapshot slice +
      written-files) → dispatch executor (`.agent/procedures/executor.md`) →
      mechanical gate SP1a → semantic surface-check (spec-validator §6 phần semantic)
      → mark `[x]` task + `TASK_QUEUE` done → task kế.
      Gate FAIL → feedback executor (≤2 vòng) → vẫn FAIL: `blocked`, hỏi user.
5. Hết task → **extraction review** (`.agent/procedures/reviewer.md`) trên TẤT CẢ file
   mới → `EXTRACTION_REPORT` → trình user (HP-10/11 = WARN).
6. **spec-validator** → post_apply_verify.
7. Gọi **knowledge-curator** → archive + update snapshot + reset.

> DNA-RELOAD (cũ, bước 2a) nghỉ hưu: DNA giờ vào context executor qua `dna_slice` trong
> handoff (cấu trúc), không phải nghi thức reload.
```

- [ ] **Step 3: Split spec-validator §6**

In `.agent/skills/spec-validator/SKILL.md` §6, add a note at the top of `post_apply_dna_check`:

```markdown
> **SP1b split:** Rule cơ học (nesting, no-else, max-lines, naming, javadoc) đã chuyển
> sang **mechanical gate deterministic** (SP1a) chạy trong micro-loop — KHÔNG check lại ở
> đây. §6 giờ chỉ giữ phần **semantic** (HP-1/2/3/5/8/9 — pattern judgment), chạy per-task
> trên DIFF của 1 task (surface nhỏ), không phải cuối cả đợt apply.
```

- [ ] **Step 4: Commit**

```bash
git add docs/workflows/01-task.md .agent/skills/spec-validator/SKILL.md
git commit -m "feat(sp1b): rewrite Phase 3 to micro-loop + split spec-validator §6 semantic"
```

---

## Task 14: README + full verification

**Files:**
- Create: `.agent/tools/microloop-orchestrator/README.md`
- Modify: `.agent/tools/README.md` (point to new tool)

- [ ] **Step 1: Write README.md**

`.agent/tools/microloop-orchestrator/README.md`:
```markdown
# Micro-loop Orchestrator (SP1b)

Rewrites Phase 3 into sequential clean-context task execution + extraction review.
Portable: a neutral filesystem contract + 3 execution tiers. The orchestrator logic
is platform-agnostic; `dispatch` is the only tier-specific seam.

## Contract artifacts (`.knowledge-layer/active/microloop/`)
- `TASK_QUEUE.md` — topo-sorted tasks + status (durable, resumable)
- `TASK_HANDOFF.md` — per-task input slice
- `TASK_RESULT.md` — per-task output
- `EXTRACTION_INPUT.md` / `EXTRACTION_REPORT.md` — HP-10/11

## Tiers (`.agent/profiles/execution-mode.yaml`)
`subagent` (Claude) · `fresh-session` (Cursor/Antigravity) · `inline-reload` (fallback).

## Run tests
    cd .agent/tools/microloop-orchestrator && python -m pytest tests/ -v
```

- [ ] **Step 2: Update .agent/tools/README.md**

Add a row/line pointing to `microloop-orchestrator/` alongside `rule-projector/`.

- [ ] **Step 3: Run the full test suite**

Run: `cd .agent/tools/microloop-orchestrator && python -m pytest tests/ -v`
Expected: PASS — all tests across contract, toposort, slice, handoff, protocol, degradation, extraction.

- [ ] **Step 4: Verify portability gate explicitly (spec §12.6)**

Run: `python -m pytest tests/test_degradation.py::test_loop_completes_without_subagent_module -v`
Expected: PASS — loop completes at `inline-reload` with `tiers.subagent` blocked.

- [ ] **Step 5: Commit**

```bash
git add .agent/tools/microloop-orchestrator/README.md .agent/tools/README.md
git commit -m "feat(sp1b): README + tools index + final verify"
```

---

## Verification Checklist (spec §12)

1. `pytest tests/` green across all modules. → Task 14 Step 3
2. Topo-sort: dependents after deps (base first). → Task 4
3. Handoff contains only sliced DNA (anti-bloat). → Task 5, 6
4. Loop protocol: gate FAIL → retry ≤2 → `blocked` (no infinite loop). → Task 7, 8
5. Resume: `in_progress` task continued, `done` not redone. → Task 7 (next_task)
6. **Portability gate:** full protocol completes at `inline-reload` without Agent tool. → Task 10, 14 Step 4
7. Extraction flags >70% duplicate clusters via disk-fallback. → Task 9
8. `task.md` Phase 3 rewritten; spec-validator §6 split; DNA-RELOAD retired to slice. → Task 13
9. SP1a mechanical gate reused (not rewritten) via `make_gate_fn`. → Task 11
