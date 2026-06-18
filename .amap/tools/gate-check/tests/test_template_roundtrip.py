import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]   # .amap/
MOD = ROOT / "tools" / "gate-check" / "gates.py"
spec = importlib.util.spec_from_file_location("gates", MOD)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

TPL = ROOT / "knowledge" / "templates" / "KNOWLEDGE_CHECKPOINT.tpl.md"


def test_blank_template_fails_validator():
    # An unfilled checkpoint MUST NOT pass — proves the gate has teeth.
    assert g.validate_knowledge_checkpoint(TPL.read_text(encoding="utf-8")).ok is False


def test_template_has_required_sections():
    text = TPL.read_text(encoding="utf-8")
    assert "Applicable DNA/Conventions" in text
    assert "Codebase evidence" in text
