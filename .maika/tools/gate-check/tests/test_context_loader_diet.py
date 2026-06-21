from pathlib import Path

CL = Path(__file__).resolve().parents[3] / "procedures" / "context-loader.md"


def test_context_loader_uses_index_not_eager_full_load():
    text = CL.read_text(encoding="utf-8")
    # references the index (diet)
    assert "knowledge-index.yaml" in text
    # points to JIT pull at the gate rather than eager full-body load
    assert "decision-gate" in text
