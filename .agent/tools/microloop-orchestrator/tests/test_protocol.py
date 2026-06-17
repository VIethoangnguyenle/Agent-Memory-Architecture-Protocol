from pathlib import Path
import sys, pytest
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

def test_apply_result_unknown_task_raises():
    q = {"ticket_id": "X", "spec_path": "p", "execution_mode": "inline-reload",
         "tasks": [{"id": "T1", "desc": "d", "depends_on": [], "status": "pending", "retries": 0}]}
    with pytest.raises(ValueError, match="not in queue"):
        orchestrator.apply_result(q, "NOPE", "PASS")

def test_make_gate_fn_maps_runner_output():
    # runner returns (exit_code, output); 0 => PASS, nonzero => FAIL
    def ok_runner(changed_files):
        return (0, "")
    def bad_runner(changed_files):
        return (1, "NestedForDepth violation")
    gate_ok = orchestrator.make_gate_fn(ok_runner)
    gate_bad = orchestrator.make_gate_fn(bad_runner)
    files = [{"path": "X.java"}]
    # SP1c: make_gate_fn returns dict with status + violations
    assert gate_ok(files) == {"status": "PASS", "violations": []}
    assert gate_bad(files) == {"status": "FAIL", "violations": []}


def test_make_gate_fn_with_parse_fn():
    """SP1c: parse_fn extracts violations from linter output."""
    def runner(changed_files):
        return (1, "HP-6:Val.java:12:depth 2")
    def parser(raw):
        parts = raw.split(":")
        return [{"rule": parts[0], "file": parts[1], "line": int(parts[2]), "message": parts[3]}]
    gate = orchestrator.make_gate_fn(runner, parse_fn=parser)
    result = gate([{"path": "Val.java"}])
    assert result["status"] == "FAIL"
    assert len(result["violations"]) == 1
    assert result["violations"][0]["rule"] == "HP-6"


def test_apply_result_stores_gate_history():
    """SP1c: apply_result records gate_history per-attempt."""
    q = {"ticket_id": "X", "spec_path": "p", "execution_mode": "inline-reload",
         "tasks": [{"id": "T1", "desc": "d", "depends_on": [], "status": "pending", "retries": 0}]}
    # First call: FAIL with violations (dict format)
    orchestrator.apply_result(q, "T1", {"status": "FAIL", "violations": [
        {"rule": "HP-6", "file": "A.java", "line": 1, "message": "bad"}
    ]}, max_retries=2)
    t1 = q["tasks"][0]
    assert len(t1["gate_history"]) == 1
    assert t1["gate_history"][0]["violations"][0]["rule"] == "HP-6"
    # Second call: PASS (string format — backward compat)
    orchestrator.apply_result(q, "T1", "PASS", max_retries=2)
    assert len(t1["gate_history"]) == 2
    assert t1["gate_history"][1]["status"] == "PASS"
    assert t1["gate_history"][1]["violations"] == []
    assert t1["status"] == "done"


def test_topo_sort_nodes_orders_contract_before_leaf():
    nodes = [
        {"id": "L1", "type": "leaf", "desc": "child", "depends_on": ["C1"], "reads": [], "writes": ["Child.java"], "status": "pending"},
        {"id": "C1", "type": "contract", "desc": "base", "depends_on": [], "reads": [], "writes": ["Base.java"], "status": "pending"},
    ]
    ordered = orchestrator.topo_sort_nodes(nodes)
    assert [node["id"] for node in ordered] == ["C1", "L1"]


def test_find_write_conflicts_groups_by_path():
    nodes = [
        {"id": "L1", "type": "leaf", "writes": ["Registry.java"]},
        {"id": "L2", "type": "leaf", "writes": ["Registry.java"]},
        {"id": "L3", "type": "leaf", "writes": ["Other.java"]},
    ]
    assert orchestrator.find_write_conflicts(nodes) == {"Registry.java": ["L1", "L2"]}


def test_plan_parallel_batches_keeps_conflicting_writes_separate():
    nodes = [
        {"id": "L1", "type": "leaf", "depends_on": [], "writes": ["Registry.java"], "status": "pending"},
        {"id": "L2", "type": "leaf", "depends_on": [], "writes": ["Registry.java"], "status": "pending"},
        {"id": "L3", "type": "leaf", "depends_on": [], "writes": ["Other.java"], "status": "pending"},
    ]
    batches = orchestrator.plan_parallel_batches(nodes)
    flattened = [node["id"] for batch in batches for node in batch]
    assert flattened == ["L1", "L3", "L2"]
    assert [node["id"] for node in batches[0]] == ["L1", "L3"]
    assert [node["id"] for node in batches[1]] == ["L2"]


def test_invalidate_contract_dependents_marks_stale():
    dag = {
        "nodes": [
            {"id": "C1", "type": "contract", "status": "done", "contract_version": "v2", "depends_on": [], "reads": [], "writes": []},
            {"id": "L1", "type": "leaf", "status": "done", "depends_on": ["C1"], "reads": [], "writes": [], "contract_ref": {"node_id": "C1", "version": "v1"}},
            {"id": "L2", "type": "leaf", "status": "done", "depends_on": ["C1"], "reads": [], "writes": [], "contract_ref": {"node_id": "C1", "version": "v2"}},
        ]
    }
    updated = orchestrator.invalidate_contract_dependents(dag, "C1", "v2")
    statuses = {node["id"]: node["status"] for node in updated["nodes"]}
    assert statuses["L1"] == "stale"
    assert statuses["L2"] == "done"


def test_knowledge_gate_blocks_complex_without_graph():
    kp = {
        "confidence": {"overall": "CAO", "code_graph": "THAP", "database": "CAO", "memory": "CAO"},
        "ua_kg": {"graph_status": "unavailable"},
        "database": {"required": False, "evidence": []},
    }
    result = orchestrator.check_knowledge_gate(kp, complexity="complex", user_override=False)
    assert result["status"] == "BLOCK"
    assert "KG graph unavailable" in result["issues"][0]


def test_build_contract_handoff_includes_dna_convention_and_snapshot():
    task = {"id": "L1", "desc": "Create child", "contract_ref": {"node_id": "C1", "version": "v1"}}
    handoff = orchestrator.build_contract_handoff(
        task=task,
        knowledge_pack={"dna": {"hard_principles": ["HP-1"]}, "conventions": {"relevant_sections": ["naming"]}},
        spec_slice="Implement child",
        snapshot_slice="Payment module",
        contract_snapshot={"node_id": "C1", "contract_version": "v1"},
        written_files=[],
        boundary=["Do not edit BasePaymentProcessor"],
        feedback=None,
    )
    assert handoff["task"]["id"] == "L1"
    assert handoff["dna_slice"]["hard_principles"] == ["HP-1"]
    assert handoff["convention_slice"]["relevant_sections"] == ["naming"]
    assert handoff["contract_snapshot"]["contract_version"] == "v1"
