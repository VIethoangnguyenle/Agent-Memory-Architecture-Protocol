import importlib.util
from pathlib import Path

MOD = Path(__file__).resolve().parents[1] / "complexity.py"
spec = importlib.util.spec_from_file_location("complexity", MOD)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def test_counts_critical_blocks(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("### [CRITICAL] A\nx\n### [CRITICAL] B\ny\n### [REFERENCE] C\n", encoding="utf-8")
    assert c.count_critical_blocks([f]) == 2
