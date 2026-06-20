# Teaching Moment Checkpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lightweight `R-DNA-7` teaching-moment checkpoint that must be structurally resolved before task archive.

**Architecture:** Add a pure `validate_teaching_moment(text) -> Result` validator in `gate-check/gates.py`, expose it through `gate-check teaching-moment`, and seed `AGENT_TRANSPARENCY` with a non-passing checkpoint section. Wire the workflow and `knowledge-curator` prose to require the validator before archive while documenting that semantic truthfulness remains honor-code.

**Tech Stack:** Python 3 standard library, pytest, existing `.amap/tools/gate-check` validator/CLI patterns, Markdown runtime templates and workflow/skill docs.

---

## File Structure

- Modify `.amap/tools/gate-check/gates.py`
  - Add section/body field helpers for the teaching-moment checkpoint.
  - Add `validate_teaching_moment(text: str) -> Result`.
  - Reuse `_SECTION` and the local `Result` type.
- Modify `.amap/tools/gate-check/cli.py`
  - Register the `teaching-moment` subcommand in `VALIDATORS`.
- Modify `.amap/tools/gate-check/tests/test_gates.py`
  - Add pure validator and CLI tests for pass/fail invariants.
- Modify `.amap/tools/gate-check/tests/test_template_roundtrip.py`
  - Add a forcing-function test proving the seeded `AGENT_TRANSPARENCY.tpl.md` does not pass as-is.
- Modify `.amap/knowledge/templates/AGENT_TRANSPARENCY.tpl.md`
  - Seed `## Teaching Moment Check` with blank fields and a comment hint outside field values.
- Modify `.amap/workflows/task.md`
  - Ensure bootstrap/reset instructions seed the teaching-moment section.
  - Add the checkpoint validator to Pha 3 post-phase self-check before archive.
- Modify `.amap/skills/knowledge-curator/SKILL.md`
  - Require running `gate-check teaching-moment` before `archive_active_context`.
  - ABORT archive on non-zero exit.

No scaffold tree snapshots need updates: `cli/tests/snapshots/*.txt` list file paths only, not template contents.

---

### Task 1: Add Failing Teaching-Moment Validator Tests

**Files:**
- Modify: `.amap/tools/gate-check/tests/test_gates.py`
- Test: `.amap/tools/gate-check/tests/test_gates.py`

- [ ] **Step 1: Add test fixtures and pure validator tests**

Append this block after `test_cli_apply_gate_exit_codes` in `.amap/tools/gate-check/tests/test_gates.py`:

```python
def _teaching_moment_section(body: str) -> str:
    return (
        "# AGENT_TRANSPARENCY\n\n"
        "## Teaching Moment Check\n\n"
        f"{body.strip()}\n\n"
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
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run:

```bash
/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -q
```

Expected: FAIL with errors like:

```text
AttributeError: module 'gates' has no attribute 'validate_teaching_moment'
```

- [ ] **Step 3: Commit the failing tests**

```bash
git add .amap/tools/gate-check/tests/test_gates.py
git commit -m "test(gate-check): cover teaching moment checkpoint"
```

---

### Task 2: Implement `gate-check teaching-moment`

**Files:**
- Modify: `.amap/tools/gate-check/gates.py`
- Modify: `.amap/tools/gate-check/cli.py`
- Test: `.amap/tools/gate-check/tests/test_gates.py`

- [ ] **Step 1: Add parser helpers and validator**

In `.amap/tools/gate-check/gates.py`, add this code after `_section_has_text` and before `validate_context_request`:

```python
_TEACHING_MOMENT_STATUSES = {
    "none",
    "captured",
    "declined",
    "pending-confirmation",
}
_PLACEHOLDER_FIELD = re.compile(
    r"^\s*(?:|fill before archive|todo|tbd|n/a|none)\s*$",
    re.IGNORECASE,
)


def _section_body(text: str, name: str):
    pattern = re.compile(_SECTION.format(name=re.escape(name)), re.DOTALL | re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1)


def _strip_markdown_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _field_block(section: str, field: str) -> str:
    pattern = re.compile(
        rf"(?ims)^\s*{re.escape(field)}\s*:\s*(.*?)(?=^[A-Za-z_][A-Za-z0-9_-]*\s*:|\Z)"
    )
    match = pattern.search(section)
    if not match:
        return ""
    return _strip_markdown_comments(match.group(1)).strip()


def _field_has_text(section: str, field: str) -> bool:
    value = _field_block(section, field)
    return bool(value and not _PLACEHOLDER_FIELD.fullmatch(value))


def _field_value(section: str, field: str) -> str:
    pattern = re.compile(rf"(?im)^\s*{re.escape(field)}\s*:\s*(.*)$")
    match = pattern.search(section)
    if not match:
        return ""
    return _strip_markdown_comments(match.group(1)).strip()


def validate_teaching_moment(text: str) -> Result:
    section = _section_body(text, "Teaching Moment Check")
    if section is None:
        return Result(False, "Teaching Moment Check section missing. Add section before archive.")

    status = _field_value(section, "status")
    if status not in _TEACHING_MOMENT_STATUSES:
        return Result(
            False,
            "status must be one of none, captured, declined, pending-confirmation",
        )

    if status == "none":
        if not _field_has_text(section, "note"):
            return Result(False, "status none requires a non-empty active assertion note")
        return Result(True)

    if status == "captured":
        if not _field_has_text(section, "target_updates"):
            return Result(False, "status captured requires non-empty target_updates")
        return Result(True)

    if status in {"declined", "pending-confirmation"}:
        if "[R-DNA-7]" not in _field_block(section, "warn"):
            return Result(False, f"status {status} requires [R-DNA-7] WARN")
        if not _field_has_text(section, "reason"):
            return Result(False, f"status {status} requires reason")
        return Result(True)

    return Result(False, "unreachable teaching-moment status")
```

Notes for the implementer:

- `_field_block` intentionally supports both one-line fields (`warn: ...`) and indented lists under fields (`target_updates:\n  - ...`).
- `_PLACEHOLDER_FIELD` rejects `note: fill before archive`, closing the placeholder-pass hole even though the template will seed `note:` blank.
- `_section_body` reuses `_SECTION` rather than introducing a Markdown parser.

- [ ] **Step 2: Register the CLI subcommand**

In `.amap/tools/gate-check/cli.py`, add the `teaching-moment` entry to `VALIDATORS`:

```python
VALIDATORS = {
    "knowledge-checkpoint": "validate_knowledge_checkpoint",
    "mcp-status": "validate_mcp_status",
    "phase-chain": "validate_phase_chain",
    "handoff-slice": "validate_handoff_slice",
    "context-request": "validate_context_request",
    "node-checkpoint": "validate_node_checkpoint",
    "apply-gate": "validate_apply_gate",
    "teaching-moment": "validate_teaching_moment",
}
```

- [ ] **Step 3: Run the focused tests and verify they pass**

Run:

```bash
/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -q
```

Expected:

```text
.................................... [100%]
```

The exact dot count can differ if nearby tests changed; the important result is all tests in `test_gates.py` pass.

- [ ] **Step 4: Run all gate-check tests**

Run:

```bash
/usr/bin/python3 -m pytest .amap/tools/gate-check/tests -q
```

Expected:

```text
all tests passed
```

- [ ] **Step 5: Commit the validator implementation**

```bash
git add .amap/tools/gate-check/gates.py .amap/tools/gate-check/cli.py
git commit -m "feat(gate-check): add teaching moment validator"
```

---

### Task 3: Seed the Non-Passing Template

**Files:**
- Modify: `.amap/tools/gate-check/tests/test_template_roundtrip.py`
- Modify: `.amap/knowledge/templates/AGENT_TRANSPARENCY.tpl.md`
- Test: `.amap/tools/gate-check/tests/test_template_roundtrip.py`

- [ ] **Step 1: Add the template forcing-function test**

In `.amap/tools/gate-check/tests/test_template_roundtrip.py`, add a second template constant after `TPL`:

```python
AGENT_TRANSPARENCY_TPL = ROOT / "knowledge" / "templates" / "AGENT_TRANSPARENCY.tpl.md"
```

Then append these tests:

```python
def test_agent_transparency_template_has_teaching_moment_section():
    text = AGENT_TRANSPARENCY_TPL.read_text(encoding="utf-8")
    assert "## Teaching Moment Check" in text
    assert "status:" in text
    assert "note:" in text
    assert "target_updates:" in text
    assert "warn:" in text
    assert "reason:" in text


def test_agent_transparency_template_teaching_moment_fails_validator():
    text = AGENT_TRANSPARENCY_TPL.read_text(encoding="utf-8")
    assert g.validate_teaching_moment(text).ok is False
```

- [ ] **Step 2: Run the template tests and verify they fail**

Run:

```bash
/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_template_roundtrip.py -q
```

Expected: FAIL because `AGENT_TRANSPARENCY.tpl.md` does not yet contain `## Teaching Moment Check`.

- [ ] **Step 3: Add the non-passing section to the template**

In `.amap/knowledge/templates/AGENT_TRANSPARENCY.tpl.md`, insert this section after `## Cảnh báo / Hạn chế` and before `## Lịch sử pha`:

```md
---

## Teaching Moment Check

<!-- Fill this section before archive. Do not pre-fill status: none. -->
status:
note:
target_updates:
warn:
reason:
```

Keep `note:` blank. Do not write `note: fill before archive`.

- [ ] **Step 4: Run the template tests and verify they pass**

Run:

```bash
/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_template_roundtrip.py -q
```

Expected:

```text
.... [100%]
```

- [ ] **Step 5: Run gate-check tests together**

Run:

```bash
/usr/bin/python3 -m pytest .amap/tools/gate-check/tests -q
```

Expected:

```text
all tests passed
```

- [ ] **Step 6: Commit the template seed**

```bash
git add .amap/tools/gate-check/tests/test_template_roundtrip.py .amap/knowledge/templates/AGENT_TRANSPARENCY.tpl.md
git commit -m "feat(runtime): seed teaching moment checkpoint"
```

---

### Task 4: Wire Workflow and Curator Instructions

**Files:**
- Modify: `.amap/workflows/task.md`
- Modify: `.amap/skills/knowledge-curator/SKILL.md`
- Test: text inspection plus full focused pytest suite

- [ ] **Step 1: Update `/task` bootstrap instructions**

In `.amap/workflows/task.md` section `0. Bootstrap context (bắt buộc)`, replace item `3. Reset ... AGENT_TRANSPARENCY.md` with this text:

```md
3. Reset `{{ platform.framework_root }}/knowledge/active/AGENT_TRANSPARENCY.md` từ
   `{{ platform.framework_root }}/knowledge/templates/AGENT_TRANSPARENCY.tpl.md`
   nếu template tồn tại; nếu không có template, tạo skeleton tối thiểu nhưng **bắt buộc**
   gồm `## Teaching Moment Check` ở trạng thái non-passing:
   ```
   ## Teaching Moment Check

   <!-- Fill this section before archive. Do not pre-fill status: none. -->
   status:
   note:
   target_updates:
   warn:
   reason:
   ```
   Sau đó điền/cập nhật:
   - task/ticket ID hiện tại.
   - `[x] {{ platform.config_entry_point }}` và `[x] {{ platform.framework_root }}/rules/RULES.md` nếu đã đọc.
   - "Lịch sử pha": `Bootstrap | <thời điểm> | Task: <input>`.
```

This covers the inline bootstrap path from the spec. It does not require implementing code because `task.md` is runtime prose.

- [ ] **Step 2: Add the Pha 3 post-phase self-check item**

In `.amap/workflows/task.md` section `8. **[POST-PHASE SELF-CHECK — Pha 3]**`, add this checklist item before `Nếu bất kỳ ô nào chưa tick`:

```md
   - `[ ]` Teaching Moment Check đã được resolve và gate cơ học PASS:
     `python3 {{ platform.framework_root }}/tools/gate-check/cli.py teaching-moment {{ platform.framework_root }}/knowledge/active/AGENT_TRANSPARENCY.md`.
     Lưu ý: gate chỉ kiểm cấu trúc/audit trail; nếu session có correction+kèm principle thì agent honor-code **không được** ghi `status: none`.
```

- [ ] **Step 3: Update `knowledge-curator` pre-check instructions**

In `.amap/skills/knowledge-curator/SKILL.md` section `3.1 archive_active_context`, inside the `PRE-CHECK` list, add this item after the blocked-state check and before the `TOKEN_LOG.md` check:

```md
  4. Chạy Teaching Moment gate trước archive:
     `python3 {{ platform.framework_root }}/tools/gate-check/cli.py teaching-moment {{ platform.framework_root }}/knowledge/active/AGENT_TRANSPARENCY.md`
     → Nếu exit != 0:
        ABORT: "Teaching Moment Check chưa resolve. Cập nhật `## Teaching Moment Check`
        trong AGENT_TRANSPARENCY.md thành một trong `none|captured|declined|pending-confirmation`
        trước khi archive."
     → Nếu PASS: tiếp tục archive.

     Giới hạn trung thực: gate này kiểm được section/status/target_updates/WARN/reason,
     nhưng không thể tự phát hiện conversation thật sự có teaching moment hay không. Nếu
     user đã correction+kèm principle thì agent honor-code **không được** ghi `status: none`.
```

Then renumber the existing `TOKEN_LOG.md` item from `4.` to `5.` and fix its indentation so the list is consistent:

```md
  5. Kiểm tra `{{ platform.framework_root }}/knowledge/active/TOKEN_LOG.md` tồn tại và có nội dung (không chỉ template):
```

- [ ] **Step 4: Run text inspection commands**

Run:

```bash
rg -n "Teaching Moment Check|gate-check/cli.py teaching-moment|honor-code|status: none" .amap/workflows/task.md .amap/skills/knowledge-curator/SKILL.md .amap/knowledge/templates/AGENT_TRANSPARENCY.tpl.md
```

Expected:

```text
.amap/workflows/task.md:... Teaching Moment Check ...
.amap/workflows/task.md:... gate-check/cli.py teaching-moment ...
.amap/workflows/task.md:... honor-code ...
.amap/skills/knowledge-curator/SKILL.md:... Teaching Moment gate ...
.amap/skills/knowledge-curator/SKILL.md:... gate-check/cli.py teaching-moment ...
.amap/skills/knowledge-curator/SKILL.md:... honor-code ...
.amap/knowledge/templates/AGENT_TRANSPARENCY.tpl.md:... Teaching Moment Check ...
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
/usr/bin/python3 -m pytest .amap/tools/gate-check/tests -q
```

Expected:

```text
all tests passed
```

- [ ] **Step 6: Commit the workflow and curator wiring**

```bash
git add .amap/workflows/task.md .amap/skills/knowledge-curator/SKILL.md
git commit -m "docs(runtime): require teaching moment checkpoint before archive"
```

---

### Task 5: Final Verification and Scope Check

**Files:**
- Verify: `.amap/tools/gate-check/*`
- Verify: `.amap/knowledge/templates/AGENT_TRANSPARENCY.tpl.md`
- Verify: `.amap/workflows/task.md`
- Verify: `.amap/skills/knowledge-curator/SKILL.md`

- [ ] **Step 1: Run full relevant pytest coverage**

Run:

```bash
/usr/bin/python3 -m pytest .amap/tools/gate-check/tests .amap/hooks/write-gate/tests cli/tests/test_snapshots.py -q
```

Expected:

```text
all tests passed
```

Rationale:

- `gate-check/tests` covers the new validator and template forcing function.
- `write-gate/tests` protects C-22/C-23 behavior after adding a new validator sibling.
- `cli/tests/test_snapshots.py` confirms scaffold file trees did not unexpectedly change.

- [ ] **Step 2: Smoke-test the CLI manually**

Run:

```bash
tmp="$(mktemp -d)"
cat > "$tmp/AGENT_TRANSPARENCY.md" <<'EOF'
# AGENT_TRANSPARENCY

## Teaching Moment Check

status: none
note: no correction-with-principle observed in this session
target_updates:
warn:
reason:
EOF
/usr/bin/python3 .amap/tools/gate-check/cli.py teaching-moment "$tmp/AGENT_TRANSPARENCY.md"
```

Expected:

```text
PASS
```

Run:

```bash
tmp="$(mktemp -d)"
cat > "$tmp/AGENT_TRANSPARENCY.md" <<'EOF'
# AGENT_TRANSPARENCY

## Teaching Moment Check

<!-- Fill this section before archive. Do not pre-fill status: none. -->
status:
note:
target_updates:
warn:
reason:
EOF
/usr/bin/python3 .amap/tools/gate-check/cli.py teaching-moment "$tmp/AGENT_TRANSPARENCY.md"; echo "exit=$?"
```

Expected:

```text
FAIL — status must be one of none, captured, declined, pending-confirmation
exit=1
```

- [ ] **Step 3: Verify no impossible integration-test promise was added**

Run:

```bash
rg -n "pytest.*archive|integration test.*archive|archive abort" docs/superpowers/specs/2026-06-20-teaching-moment-checkpoint-design.md docs/superpowers/plans/2026-06-20-teaching-moment-checkpoint.md .amap/skills/knowledge-curator/SKILL.md
```

Expected:

```text
docs/superpowers/specs/2026-06-20-teaching-moment-checkpoint-design.md:... Do not promise pytest coverage for "archive aborts." ...
```

No runtime doc should claim there is a Python `knowledge-curator.archive_active_context()` implementation test.

- [ ] **Step 4: Check the final diff**

Run:

```bash
git diff --stat HEAD~3..HEAD
git diff --check HEAD~3..HEAD
```

Expected:

```text
no whitespace errors
```

The diff should include only:

- `.amap/tools/gate-check/gates.py`
- `.amap/tools/gate-check/cli.py`
- `.amap/tools/gate-check/tests/test_gates.py`
- `.amap/tools/gate-check/tests/test_template_roundtrip.py`
- `.amap/knowledge/templates/AGENT_TRANSPARENCY.tpl.md`
- `.amap/workflows/task.md`
- `.amap/skills/knowledge-curator/SKILL.md`

- [ ] **Step 5: Commit verification note if needed**

If verification required a small correction, commit it:

```bash
git add <corrected-files>
git commit -m "fix: align teaching moment checkpoint verification"
```

If no correction was needed, do not create an empty commit.

---

## Self-Review Checklist

- Spec coverage:
  - Validator exists and checks all machine-checkable invariants.
  - `none` requires an active assertion note and rejects `fill before archive`.
  - `captured` requires non-empty `target_updates`.
  - `declined` and `pending-confirmation` require `[R-DNA-7]` and reason.
  - Template seed is non-passing.
  - Both reset paths are covered: template reset and `/task` bootstrap prose.
  - `knowledge-curator` calls the validator and aborts on non-zero exit in prose.
  - Honor-code limitation is explicitly preserved.
- Placeholder scan:
  - No `TBD`, `TODO`, "implement later", or "similar to Task N" instructions.
  - Template comments may say "Fill this section before archive"; field values remain blank.
- Type/name consistency:
  - Function name is `validate_teaching_moment`.
  - CLI subcommand is `teaching-moment`.
  - Section name is exactly `Teaching Moment Check`.
  - Field names are exactly `status`, `note`, `target_updates`, `warn`, `reason`.
