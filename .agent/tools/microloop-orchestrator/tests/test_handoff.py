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
