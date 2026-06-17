"""Micro-loop orchestrator: topo-sort, slice assembly, loop protocol.

All functions are pure logic. run_loop() takes dispatch_fn and gate_fn via
dependency injection so the whole protocol is unit-testable with stubs —
no Java, no real subagent.
"""


def topo_sort(tasks):
    """Kahn's algorithm. Returns tasks ordered so deps come first. Raises on cycle."""
    by_id = {t["id"]: t for t in tasks}
    for t in tasks:
        for dep_id in t.get("depends_on", []):
            if dep_id not in by_id:
                raise ValueError(f"task {t['id']} depends on non-existent task {dep_id}")
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


def apply_result(queue, task_id, gate_result, max_retries=2):
    """Mutate queue per gate outcome. PASS->done; FAIL->retry; FAIL over budget->blocked.

    gate_result: str ('PASS'/'FAIL') for backward compat, or dict
    {'status': 'PASS'|'FAIL', 'violations': [...]} from enriched gate (SP1c).
    Stores gate_history per-attempt for outcome loop."""
    t = next((t for t in queue["tasks"] if t["id"] == task_id), None)
    if t is None:
        raise ValueError(f"task {task_id} not in queue")

    # Backward-compatible: accept string or dict
    if isinstance(gate_result, str):
        gate_status = gate_result
        violations = []
    else:
        gate_status = gate_result["status"]
        violations = gate_result.get("violations", [])

    # Record gate history per-attempt (SP1c outcome loop)
    t.setdefault("gate_history", []).append({
        "attempt": t.get("retries", 0),
        "status": gate_status,
        "violations": violations,
    })

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


def make_gate_fn(runner, parse_fn=None):
    """Adapt a (changed_files)->(exit_code, output) runner into enriched gate_fn.

    Returns dict {'status': 'PASS'|'FAIL', 'violations': [...]}.
    parse_fn: optional (raw_output) -> list[{rule, file, line, message}].
    If None, violations is always []. Injected so backend-specific parsing
    (Checkstyle, ESLint, Ruff) is decoupled from the protocol."""
    def gate_fn(changed_files):
        exit_code, output = runner(changed_files)
        status = "PASS" if exit_code == 0 else "FAIL"
        violations = parse_fn(output) if parse_fn else []
        return {"status": status, "violations": violations}
    return gate_fn


def run_loop(queue, dispatch_fn, gate_fn, max_retries=2):
    """Drive the micro-loop. dispatch_fn(task)->changed_files;
    gate_fn(changed_files)->dict{'status','violations'} or str 'PASS'|'FAIL'.

    Pure protocol: no knowledge of tiers or the real gate — both injected. This is
    what makes the loop platform-agnostic and unit-testable (portability gate).
    gate_history is accumulated in each task for SP1c outcome loop.
    """
    while True:
        t = next_task(queue)
        if t is None:
            return queue
        t["status"] = "in_progress"  # resumable marker before dispatch
        changed_files = dispatch_fn(t)
        gate_result = gate_fn(changed_files)
        apply_result(queue, t["id"], gate_result, max_retries=max_retries)
        if t["status"] == "blocked":
            return queue


def topo_sort_nodes(nodes):
    """Topo-sort Contract DAG nodes by depends_on, preserving deterministic id order."""
    by_id = {node["id"]: node for node in nodes}
    for node in nodes:
        for dep_id in node.get("depends_on", []):
            if dep_id not in by_id:
                raise ValueError(f"node {node['id']} depends on non-existent node {dep_id}")
    indeg = {node["id"]: len(node.get("depends_on", [])) for node in nodes}
    ready = sorted([node_id for node_id, degree in indeg.items() if degree == 0])
    ordered = []
    while ready:
        node_id = ready.pop(0)
        ordered.append(by_id[node_id])
        for node in nodes:
            if node_id in node.get("depends_on", []):
                indeg[node["id"]] -= 1
                if indeg[node["id"]] == 0:
                    ready.append(node["id"])
        ready.sort()
    if len(ordered) != len(nodes):
        raise ValueError("dependency cycle detected in contract dag")
    return ordered


def find_write_conflicts(nodes):
    """Return paths written by more than one node: {path: [node_id, ...]}."""
    writers = {}
    for node in nodes:
        for path in node.get("writes", []):
            writers.setdefault(path, []).append(node["id"])
    return {path: ids for path, ids in writers.items() if len(ids) > 1}


def plan_parallel_batches(nodes):
    """Plan deterministic batches where no nodes in the same batch write the same file."""
    pending = topo_sort_nodes(nodes)
    batches = []
    while pending:
        batch = []
        used_writes = set()
        remaining = []
        for node in pending:
            writes = set(node.get("writes", []))
            if used_writes.isdisjoint(writes):
                batch.append(node)
                used_writes.update(writes)
            else:
                remaining.append(node)
        batches.append(batch)
        pending = remaining
    return batches


def invalidate_contract_dependents(dag, contract_node_id, new_version):
    """Mark downstream nodes stale when their contract_ref version is older than new_version."""
    for node in dag.get("nodes", []):
        ref = node.get("contract_ref")
        if ref and ref.get("node_id") == contract_node_id and ref.get("version") != new_version:
            node["status"] = "stale"
    return dag


def check_knowledge_gate(knowledge_pack, complexity="standard", user_override=False):
    """Return PASS/BLOCK for Phase 3 knowledge readiness."""
    issues = []
    graph_status = knowledge_pack.get("ua_kg", {}).get("graph_status")
    if complexity == "complex" and graph_status != "available":
        issues.append("KG graph unavailable for complex task")
    database = knowledge_pack.get("database", {})
    if database.get("required") and not database.get("evidence"):
        issues.append("DB evidence missing for data-touching task")
    if issues and not user_override:
        return {"status": "BLOCK", "issues": issues}
    if issues:
        return {"status": "WARN", "issues": issues}
    return {"status": "PASS", "issues": []}


def build_contract_handoff(task, knowledge_pack, spec_slice, snapshot_slice, contract_snapshot,
                           written_files, boundary, feedback=None):
    """Build role-aware TASK_HANDOFF content for Hybrid Contract DAG nodes."""
    return {
        "task": {"id": task["id"], "desc": task["desc"]},
        "dna_slice": knowledge_pack.get("dna", {}),
        "convention_slice": knowledge_pack.get("conventions", {}),
        "spec_slice": spec_slice,
        "snapshot_slice": snapshot_slice,
        "contract_snapshot": contract_snapshot,
        "written_files": written_files,
        "boundary": boundary,
        "feedback": feedback,
    }
