import importlib.util
from pathlib import Path
from textwrap import dedent

MOD = Path(__file__).resolve().parents[1] / "gates.py"
spec = importlib.util.spec_from_file_location("gates", MOD)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def test_context_request_requires_request_type_and_missing_evidence():
    empty = "node_id: L1\nrequest_type: context\nmissing: []\nsuggested_tools: []\nblocked_reason: \"\"\n"
    filled = (
        "node_id: L1\n"
        "request_type: context\n"
        "missing:\n  - AD_USER column metadata\n"
        "suggested_tools:\n  - db-remote\n"
        "blocked_reason: cannot choose the correct repository method\n"
    )
    assert g.validate_context_request(empty).ok is False
    assert g.validate_context_request(filled).ok is True


def test_context_request_rejects_wrong_request_type():
    wrong = (
        "node_id: L1\n"
        "request_type: integration\n"
        "missing:\n  - something\n"
        "suggested_tools: []\n"
        "blocked_reason: blocked\n"
    )
    assert g.validate_context_request(wrong).ok is False


def test_node_checkpoint_requires_files_evidence_and_verification():
    empty = "# Node Checkpoint\n## Files Changed\n\n"
    filled = (
        "# Node Checkpoint\n"
        "## Files Changed\n- src/App.java\n"
        "## Requirement Satisfied\n- Implements TASK-1\n"
        "## Evidence Used\n- SP-6 from TASK_HANDOFF.node-1.md\n"
        "## Verification\n- pytest cli/tests/test_init.py -v: PASS\n"
    )
    assert g.validate_node_checkpoint(empty).ok is False
    assert g.validate_node_checkpoint(filled).ok is True


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


def test_knowledge_checkpoint_rejects_ruleid_not_in_valid_set():
    text = (
        "## DNA\nISO-9001 mentioned here\n"
        "## Codebase\nnode_id: svc.UserService#42\nblast-radius: 3 nodes\n"
    )
    result = g.validate_knowledge_checkpoint(text, valid_rule_ids={"SP-6"})
    assert result.ok is False
    assert "valid rule-id" in result.reason


def test_knowledge_checkpoint_accepts_ruleid_from_valid_set():
    text = (
        "## DNA\nSP-6 staircase\n"
        "## Codebase\nnode_id: svc.UserService#42\nblast-radius: 3 nodes\n"
    )
    assert g.validate_knowledge_checkpoint(text, valid_rule_ids={"SP-6"}).ok is True


def test_governance_degrade_requires_no_knowledge_allowed():
    gov = "## Applicable DNA/Conventions\nno approved DNA/conventions for this artifact-type — generic patterns, LOW confidence\n"
    assert g.validate_knowledge_checkpoint(gov, allow_no_knowledge=False).ok is False
    assert g.validate_knowledge_checkpoint(gov, allow_no_knowledge=True).ok is True


def test_knowledge_checkpoint_still_needs_evidence_when_ruleid_present():
    # Regression: citing a rule-id but no evidence and no degrade still fails.
    bad = "## DNA\nSP-6 staircase\n## Codebase\n(no node_id, no blast-radius)\n"
    assert g.validate_knowledge_checkpoint(bad).ok is False


def test_mcp_status_needs_numbers_or_degrade():
    assert g.validate_mcp_status("MCP: Runtime Ready").ok is False
    assert g.validate_mcp_status("KG: nodes=1240 edges=5530 freshness=2026-06-18").ok is True
    assert g.validate_mcp_status("KG unavailable — grep fallback, MEDIUM").ok is True


def test_degrade_line_must_be_compact_not_rambling():
    # P1(a): rambling prose that merely contains both anchors far apart must NOT
    # satisfy the degrade path; the canonical compact line still does.
    rambling = ("KG unavailable, but actually the architecture quality is only "
                "MEDIUM for entirely unrelated documentation reasons")
    assert g.validate_mcp_status(rambling).ok is False
    assert g.validate_mcp_status("KG unavailable — grep fallback, MEDIUM").ok is True


def test_mcp_status_accepts_agent_memory_probe_and_degrade():
    assert g.validate_mcp_status("agent-memory: healthy").ok is True
    assert g.validate_mcp_status(
        "agent-memory unavailable — skip recall/save"
    ).ok is True
    # A bare label with no health word or degrade is still invalid.
    assert g.validate_mcp_status("agent-memory").ok is False
    # Hardening: negated/stale prose must NOT count as a healthy probe.
    assert g.validate_mcp_status("agent-memory is not healthy").ok is False
    # Hardening: rambling prose must NOT satisfy the degrade line.
    assert g.validate_mcp_status(
        "agent-memory unavailable, we decided to skip the recall step but later "
        "did save anyway after extensive debugging"
    ).ok is False


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


def test_cli_uses_index_to_reject_unknown_ruleid(tmp_path):
    import importlib.util
    cli_mod = Path(__file__).resolve().parents[1] / "cli.py"
    spec2 = importlib.util.spec_from_file_location("cli", cli_mod)
    cli = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(cli)

    checkpoint = tmp_path / "KNOWLEDGE_CHECKPOINT.md"
    checkpoint.write_text(
        "## DNA\nISO-9001\n"
        "## Codebase\nnode_id: svc.UserService#42\nblast-radius: 3 nodes\n",
        encoding="utf-8",
    )
    index = tmp_path / "knowledge-index.yaml"
    index.write_text(
        "entries:\n"
        "  - id: SP-6\n"
        "    store: author-dna\n"
        "    title: staircase\n"
        "    applies_to: [Constructor]\n",
        encoding="utf-8",
    )

    assert cli.main([
        "knowledge-checkpoint", str(checkpoint),
        "--index", str(index),
        "--artifact-type", "Constructor",
    ]) == 1


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


def test_apply_gate_passes_with_pha2_and_no_blocker():
    assert g.validate_apply_gate("Pha 1 DONE\nPha 2 DONE\n").ok is True


def test_apply_gate_fails_without_pha2():
    result = g.validate_apply_gate("Pha 1 DONE\n")
    assert result.ok is False
    assert "Pha 2 DONE" in result.reason


def test_apply_gate_fails_with_open_blocker():
    text = "Pha 1 DONE\nPha 2 DONE\n[BLOCKER-ARCH] coupling risk\n"
    assert g.validate_apply_gate(text).ok is False


def test_apply_gate_passes_when_blocker_resolved():
    text = (
        "Pha 1 DONE\nPha 2 DONE\n"
        "[BLOCKER-ARCH] coupling risk\n"
        "[BLOCKER-ARCH RESOLVED] 2026-06-20 user approved approach\n"
    )
    assert g.validate_apply_gate(text).ok is True


def test_cli_apply_gate_exit_codes(tmp_path):
    import importlib.util
    cli_mod = Path(__file__).resolve().parents[1] / "cli.py"
    spec = importlib.util.spec_from_file_location("cli", cli_mod)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)

    f = tmp_path / "AGENT_TRANSPARENCY.md"
    f.write_text("Pha 1 DONE\nPha 2 DONE\n", encoding="utf-8")
    assert cli.main(["apply-gate", str(f)]) == 0
    f.write_text("Pha 1 DONE\n", encoding="utf-8")
    assert cli.main(["apply-gate", str(f)]) == 1


def _teaching_moment_section(body: str) -> str:
    return (
        "# AGENT_TRANSPARENCY\n\n"
        "## Teaching Moment Check\n\n"
        f"{dedent(body).strip()}\n\n"
        "## Violation Log\n\n"
    )


def test_teaching_moment_passes_none_with_active_assertion():
    text = _teaching_moment_section(
        """
        status: none
        note: no correction-with-principle observed in this session
        target_updates:
        warn:
        reason:
        """
    )
    assert g.validate_teaching_moment(text).ok is True


def test_teaching_moment_passes_captured_with_targets():
    text = _teaching_moment_section(
        """
        status: captured
        note: user confirmed the split and long-term updates were written
        target_updates:
          - author-dna.yaml: HP-12 prefer composition for lifecycle decoupling
          - conventions.yaml: CP-08 mapper stays pure
        warn:
        reason:
        """
    )
    assert g.validate_teaching_moment(text).ok is True


def test_teaching_moment_passes_declined_with_warn_and_reason():
    text = _teaching_moment_section(
        """
        status: declined
        note:
        target_updates:
        warn: [R-DNA-7] Teaching moment chua capture: mapper must stay pure.
        reason: user declined capture
        """
    )
    assert g.validate_teaching_moment(text).ok is True


def test_teaching_moment_passes_pending_confirmation_with_warn_and_reason():
    text = _teaching_moment_section(
        """
        status: pending-confirmation
        note:
        target_updates:
        warn: [R-DNA-7] Teaching moment chua capture: factory boundary excludes validation logic.
        reason: awaiting user confirmation
        """
    )
    assert g.validate_teaching_moment(text).ok is True


def test_teaching_moment_rejects_missing_section():
    result = g.validate_teaching_moment("# AGENT_TRANSPARENCY\n\n## Phase State\n\n")
    assert result.ok is False
    assert "section missing" in result.reason


def test_teaching_moment_rejects_seeded_blank_status():
    text = _teaching_moment_section(
        """
        <!-- Fill this section before archive. Do not pre-fill status: none. -->
        status:
        note:
        target_updates:
        warn:
        reason:
        """
    )
    result = g.validate_teaching_moment(text)
    assert result.ok is False
    assert "status must be one of" in result.reason


def test_teaching_moment_rejects_invalid_status():
    text = _teaching_moment_section(
        """
        status: maybe
        note: checked
        target_updates:
        warn:
        reason:
        """
    )
    result = g.validate_teaching_moment(text)
    assert result.ok is False
    assert "status must be one of" in result.reason


def test_teaching_moment_rejects_none_without_real_note():
    blank = _teaching_moment_section(
        """
        status: none
        note:
        target_updates:
        warn:
        reason:
        """
    )
    placeholder = _teaching_moment_section(
        """
        status: none
        note: fill before archive
        target_updates:
        warn:
        reason:
        """
    )
    assert g.validate_teaching_moment(blank).ok is False
    assert g.validate_teaching_moment(placeholder).ok is False


def test_teaching_moment_rejects_captured_without_target_updates():
    text = _teaching_moment_section(
        """
        status: captured
        note: user confirmed the split
        target_updates:
        warn:
        reason:
        """
    )
    result = g.validate_teaching_moment(text)
    assert result.ok is False
    assert "target_updates" in result.reason


def test_teaching_moment_rejects_declined_without_warn_or_reason():
    missing_warn = _teaching_moment_section(
        """
        status: declined
        note:
        target_updates:
        warn:
        reason: user declined capture
        """
    )
    missing_reason = _teaching_moment_section(
        """
        status: declined
        note:
        target_updates:
        warn: [R-DNA-7] Teaching moment chua capture: mapper must stay pure.
        reason:
        """
    )
    assert g.validate_teaching_moment(missing_warn).ok is False
    assert g.validate_teaching_moment(missing_reason).ok is False


def test_teaching_moment_rejects_pending_without_warn_or_reason():
    missing_warn = _teaching_moment_section(
        """
        status: pending-confirmation
        note:
        target_updates:
        warn:
        reason: awaiting user confirmation
        """
    )
    missing_reason = _teaching_moment_section(
        """
        status: pending-confirmation
        note:
        target_updates:
        warn: [R-DNA-7] Teaching moment chua capture: factory boundary excludes validation logic.
        reason:
        """
    )
    assert g.validate_teaching_moment(missing_warn).ok is False
    assert g.validate_teaching_moment(missing_reason).ok is False


def test_cli_teaching_moment_exit_codes(tmp_path):
    import importlib.util
    cli_mod = Path(__file__).resolve().parents[1] / "cli.py"
    spec = importlib.util.spec_from_file_location("cli", cli_mod)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)

    f = tmp_path / "AGENT_TRANSPARENCY.md"
    f.write_text(
        _teaching_moment_section(
            """
            status: none
            note: no correction-with-principle observed in this session
            target_updates:
            warn:
            reason:
            """
        ),
        encoding="utf-8",
    )
    assert cli.main(["teaching-moment", str(f)]) == 0

    f.write_text(_teaching_moment_section("status:\nnote:\n"), encoding="utf-8")
    assert cli.main(["teaching-moment", str(f)]) == 1
