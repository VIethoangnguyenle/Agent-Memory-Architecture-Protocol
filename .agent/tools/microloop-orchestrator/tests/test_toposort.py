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

def test_dangling_dependency_raises_distinct_error():
    tasks = [
        {"id": "T1", "depends_on": ["T99"]},  # T99 does not exist
    ]
    with pytest.raises(ValueError, match="non-existent"):
        orchestrator.topo_sort(tasks)
