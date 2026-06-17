import sys, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def _gen(tmp_path, dna, conv):
    sys.path.insert(0, str(ROOT))
    import projector
    from backends import checkstyle
    ir = projector.build_ir(str(dna), str(conv))
    (tmp_path / "rules.json").write_text(json.dumps(ir))
    xml = checkstyle.ir_to_checkstyle(ir)
    (tmp_path / "checkstyle.generated.xml").write_text(xml)
    return ir["source_hash"]

def test_sync_check_detects_stale(tmp_path):
    dna = HERE / "fixtures" / "sample-author-dna.yaml"
    conv = HERE / "fixtures" / "sample-conventions.yaml"
    emitted = _gen(tmp_path, dna, conv)
    xml = (tmp_path / "checkstyle.generated.xml").read_text()
    assert f"source_hash={emitted}" in xml
    sys.path.insert(0, str(ROOT))
    import projector
    mutated = tmp_path / "mutated-dna.yaml"
    mutated.write_text(dna.read_text() + "\n# changed\n")
    new_hash = projector.compute_source_hash([str(mutated), str(conv)])
    assert new_hash != emitted
