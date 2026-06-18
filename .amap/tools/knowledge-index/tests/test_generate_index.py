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


def test_build_index_merges_all_three_stores(tmp_path):
    (tmp_path / "author-dna.yaml").write_text(
        "hard_principles:\n  HP-1:\n    name: SOLID\n    applies_to: [Service]\n",
        encoding="utf-8",
    )
    (tmp_path / "conventions.yaml").write_text(
        "naming:\n  CP-1:\n    name: suffixes\n    applies_to: [Factory]\n    mechanically_checkable: true\n",
        encoding="utf-8",
    )
    (tmp_path / "knowledge-snapshot.md").write_text(
        "### Mod <!-- applies_to: Handler -->\n", encoding="utf-8",
    )
    entries = gi.build_index(
        tmp_path / "author-dna.yaml",
        tmp_path / "conventions.yaml",
        tmp_path / "knowledge-snapshot.md",
    )
    by = {e["id"]: e for e in entries}
    assert by["HP-1"]["store"] == "author-dna"
    assert by["CP-1"]["store"] == "conventions"
    assert by["CP-1"]["mechanically_checkable"] is True
    assert by["Mod"]["store"] == "snapshot"
    assert by["Mod"]["applies_to"] == ["Handler"]


def test_build_index_tolerates_missing_files(tmp_path):
    # Only author-dna present; conventions + snapshot absent → no crash, dna entries only.
    (tmp_path / "author-dna.yaml").write_text(
        "p:\n  HP-1:\n    name: X\n    applies_to: [Service]\n", encoding="utf-8",
    )
    entries = gi.build_index(
        tmp_path / "author-dna.yaml",
        tmp_path / "conventions.yaml",       # does not exist
        tmp_path / "knowledge-snapshot.md",  # does not exist
    )
    assert [e["id"] for e in entries] == ["HP-1"]


def test_main_writes_index_file(tmp_path):
    import yaml
    (tmp_path / "author-dna.yaml").write_text(
        "p:\n  HP-1:\n    name: X\n    applies_to: [Service]\n", encoding="utf-8",
    )
    assert gi.main([str(tmp_path)]) == 0
    out = tmp_path / "knowledge-index.yaml"
    assert out.exists()
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert any(e["id"] == "HP-1" for e in data["entries"])
