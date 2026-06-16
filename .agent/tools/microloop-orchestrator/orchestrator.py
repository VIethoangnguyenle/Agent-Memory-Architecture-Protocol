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


def slice_dna(dna, principle_ids):
    """Extract only requested principle entries + always-global thresholds (anti-bloat)."""
    wanted = set(principle_ids)
    return {
        "complexity_thresholds": dna.get("complexity_thresholds", {}),
        "hard_principles": [p for p in dna.get("hard_principles", []) if p["id"] in wanted],
        "style_preferences": [p for p in dna.get("style_preferences", []) if p["id"] in wanted],
    }


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
