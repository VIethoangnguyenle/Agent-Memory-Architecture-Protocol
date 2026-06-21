from pathlib import Path

BOOT = Path(__file__).resolve().parents[3] / "procedures" / "bootstrap.md"


def test_bootstrap_loads_index_not_full_knowledge():
    text = BOOT.read_text(encoding="utf-8")
    assert "knowledge-index.yaml" in text                      # diet loads the index
    assert "đọc TẤT CẢ" not in text and "tất cả entries" not in text  # eager mandate removed
