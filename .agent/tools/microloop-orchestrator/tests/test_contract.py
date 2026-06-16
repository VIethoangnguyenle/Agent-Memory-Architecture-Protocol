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
