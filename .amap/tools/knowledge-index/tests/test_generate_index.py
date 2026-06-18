import importlib.util
from pathlib import Path

MOD = Path(__file__).resolve().parents[1] / "generate_index.py"
spec = importlib.util.spec_from_file_location("generate_index", MOD)
gi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gi)


def test_walk_extracts_entries_with_applies_to():
    tree = {
        "hard_principles": {
            "HP-1": {"name": "SOLID", "applies_to": ["Service"], "mechanically_checkable": False},
        },
        "style_preferences": {
            "SP-6": {"name": "staircase fields", "applies_to": ["Constructor"], "mechanically_checkable": True},
        },
        "noise": {"meta": {"status": "approved"}},  # no applies_to → ignored
    }
    entries = gi.walk_entries(tree, store="author-dna")
    ids = {e["id"]: e for e in entries}
    assert set(ids) == {"HP-1", "SP-6"}
    assert ids["HP-1"] == {
        "id": "HP-1", "store": "author-dna", "title": "SOLID",
        "applies_to": ["Service"], "mechanically_checkable": False,
    }
    assert ids["SP-6"]["mechanically_checkable"] is True


def test_index_snapshot_headings(tmp_path):
    snap = tmp_path / "knowledge-snapshot.md"
    snap.write_text(
        "# Snapshot\n"
        "### User Status Module <!-- applies_to: Handler, Executor -->\n"
        "blah\n"
        "### Untagged Module\n",
        encoding="utf-8",
    )
    entries = gi.index_snapshot(snap)
    assert {"id": "User Status Module", "store": "snapshot",
            "title": "User Status Module", "applies_to": ["Handler", "Executor"],
            "mechanically_checkable": False} in entries
    untagged = [e for e in entries if e["id"] == "Untagged Module"][0]
    assert untagged["applies_to"] == []
