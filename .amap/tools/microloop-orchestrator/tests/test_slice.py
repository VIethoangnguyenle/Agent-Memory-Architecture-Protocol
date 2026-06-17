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
