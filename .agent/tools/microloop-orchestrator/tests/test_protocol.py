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
    assert gate_ok(files) == "PASS"
    assert gate_bad(files) == "FAIL"
