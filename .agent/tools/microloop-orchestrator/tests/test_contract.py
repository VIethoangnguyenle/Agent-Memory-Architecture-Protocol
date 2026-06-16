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
