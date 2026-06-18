from pathlib import Path

RULES = Path(__file__).resolve().parents[3] / "rules"


def test_guard2_is_evidence_gate_and_generic():
    text = (RULES / "rules-guard.md").read_text(encoding="utf-8")
    # collapsed to the shared gate, references the checkpoint artifact
    assert "KNOWLEDGE_CHECKPOINT" in text
    assert "decision-gate" in text
    # generic-ised: no hard-coded artifact-type enum in the rule
    assert "Chứa `Factory`" not in text
    assert "Chứa `Service`" not in text


def test_rtool8_dispatch_gate():
    text = (RULES / "rules-tool.md").read_text(encoding="utf-8")
    assert "handoff-slice" in text                     # references the gate validator
    assert "Applicable DNA/Conventions" in text         # required slice section


def test_rflow_phase_gate():
    text = (RULES / "rules-flow.md").read_text(encoding="utf-8")
    assert "phase-chain" in text                         # completion gate validator
    assert "phase_done(spec)" in text or "phase_done: spec" in text
