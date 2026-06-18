import importlib.util
from pathlib import Path

MOD = Path(__file__).resolve().parents[1] / "gates.py"
spec = importlib.util.spec_from_file_location("gates", MOD)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def test_knowledge_checkpoint_needs_ruleid_and_evidence():
    bad = "## Applicable DNA/Conventions\n(nothing)\n"
    ok_graph = "## DNA\nSP-6 staircase\n## Codebase\nnode_id: svc.UserService#42\nblast-radius: 3 nodes\n"
    ok_degrade = "## DNA\nSP-6\n## Codebase\nKG unavailable — grep fallback, MEDIUM\n"
    assert g.validate_knowledge_checkpoint(bad).ok is False
    assert g.validate_knowledge_checkpoint(ok_graph).ok is True
    assert g.validate_knowledge_checkpoint(ok_degrade).ok is True


def test_knowledge_checkpoint_governance_degrade_passes():
    # No approved DNA/conventions yet (fresh project) → proceed at LOW confidence, no rule-id required.
    gov = "## Applicable DNA/Conventions\nno approved DNA/conventions for this artifact-type — generic patterns, LOW confidence\n"
    assert g.validate_knowledge_checkpoint(gov).ok is True


def test_knowledge_checkpoint_still_needs_evidence_when_ruleid_present():
    # Regression: citing a rule-id but no evidence and no degrade still fails.
    bad = "## DNA\nSP-6 staircase\n## Codebase\n(no node_id, no blast-radius)\n"
    assert g.validate_knowledge_checkpoint(bad).ok is False


def test_mcp_status_needs_numbers_or_degrade():
    assert g.validate_mcp_status("MCP: Runtime Ready").ok is False
    assert g.validate_mcp_status("KG: nodes=1240 edges=5530 freshness=2026-06-18").ok is True
    assert g.validate_mcp_status("KG unavailable — grep fallback, MEDIUM").ok is True


def test_phase_chain_requires_ordered_markers():
    done = "Pha 1 DONE\nPha 2 DONE (spec: openspec/changes/x/)\nPha 3 DONE"
    skipped = "Pha 1 DONE\nPha 3 DONE"
    assert g.validate_phase_chain(done).ok is True
    assert g.validate_phase_chain(skipped).ok is False


def test_handoff_slice_requires_applicable_section_with_ruleids():
    empty = "# Handoff\n## Task\ndo X\n"
    filled = "# Handoff\n## Applicable DNA/Conventions\n- SP-6: staircase\n- IW-05: config-driven\n"
    assert g.validate_handoff_slice(empty).ok is False
    assert g.validate_handoff_slice(filled).ok is True


def test_handoff_slice_ignores_ruleids_outside_its_section():
    # rule-id appears only in a LATER, unrelated section → must NOT pass
    leaky = (
        "# Handoff\n"
        "## Applicable DNA/Conventions\n"
        "\n"
        "## Unrelated Section\n"
        "SP-6 is just mentioned here\n"
    )
    assert g.validate_handoff_slice(leaky).ok is False


def test_cli_returns_nonzero_on_invalid(tmp_path):
    import importlib.util
    cli_mod = Path(__file__).resolve().parents[1] / "cli.py"
    spec2 = importlib.util.spec_from_file_location("cli", cli_mod)
    cli = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(cli)
    f = tmp_path / "chk.md"
    f.write_text("nothing useful", encoding="utf-8")
    assert cli.main(["knowledge-checkpoint", str(f)]) == 1


# ─── Regression fixtures: the historical failures these gates exist to catch ───

def test_c10_handoff_without_sp6_slice_blocks_dispatch():
    # C-10: a subagent was dispatched with only a task description (no knowledge
    # slice) → it violated SP-6. The dispatch-gate must refuse such a handoff.
    handoff = "# Handoff\n## Task\nwrite UnlockUserConfirmExecutor\n"
    assert g.validate_handoff_slice(handoff).ok is False


def test_c22_skipped_spec_blocks_completion():
    # C-22: agent jumped Pha 1 → Pha 3, skipping the spec phase. The phase-chain
    # completion gate must reject a non-contiguous marker chain.
    transparency = "Pha 1 DONE\nPha 3 DONE"
    assert g.validate_phase_chain(transparency).ok is False
