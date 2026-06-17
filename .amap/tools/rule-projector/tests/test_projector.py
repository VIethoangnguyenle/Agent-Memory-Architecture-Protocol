import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import projector  # noqa: E402

DNA = HERE / "fixtures" / "sample-author-dna.yaml"
CONV = HERE / "fixtures" / "sample-conventions.yaml"

def _norm(rules):
    return sorted([json.dumps(r, sort_keys=True) for r in rules])

def test_build_ir_matches_expected_rules():
    ir = projector.build_ir(str(DNA), str(CONV))
    expected = json.loads((HERE / "fixtures" / "expected-ir.json").read_text())
    assert _norm(ir["rules"]) == _norm(expected["rules"])

def test_semantic_principle_excluded():
    ir = projector.build_ir(str(DNA), str(CONV))
    ids = [r["id"] for r in ir["rules"]]
    assert not any("HP-5" in i for i in ids)

def test_bare_dna_still_projects_floor():
    bare = HERE / "fixtures" / "bare-author-dna.yaml"
    ir = projector.build_ir(str(bare), str(CONV))
    irules = {r["ir_rule"] for r in ir["rules"]}
    assert "max_if_nesting" in irules        # from thresholds floor
    assert "max_method_lines" in irules
    assert "naming_regex" in irules
    assert "forbid_else" not in irules

def test_draft_conventions_skipped():
    import tempfile, textwrap
    draft = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
    draft.write(textwrap.dedent('''
        meta:
          status: draft
        naming_patterns:
          - target: TypeName
            pattern: "^X.*$"
    '''))
    draft.close()
    ir = projector.build_ir(str(DNA), draft.name)
    assert not any(r["ir_rule"] == "naming_regex" for r in ir["rules"])
