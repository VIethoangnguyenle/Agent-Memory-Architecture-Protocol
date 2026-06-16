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
