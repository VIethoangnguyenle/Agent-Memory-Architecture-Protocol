# Teaching Moment Checkpoint (C-24) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn R-DNA-7 (capture teaching moments in-session) from rule prose into a mechanical pre-archive checkpoint: a `gate-check teaching-moment` validator over `AGENT_TRANSPARENCY.md`, a template seeded in a failing state, and mandated calls in `task.md` + `knowledge-curator`.

**Architecture:** Add a pure `validate_teaching_moment` validator to `gate-check/gates.py` (exposed via CLI), seed a non-passing `## Teaching Moment Check` section into the transparency template, and wire the validator as a mandatory pre-archive check. Per spec, this is "deterministic acknowledgment, not detection" — the validator checks structural invariants only; the call site is honor-code because archive is not intercepted by the PreToolUse write-gate.

**Tech Stack:** Python 3.9+ stdlib (`re`), pytest (`/usr/bin/python3 -m pytest`, import-mode=importlib).

**Spec:** `docs/superpowers/specs/2026-06-20-teaching-moment-checkpoint-design.md`

**Branch:** `teaching-moment-checkpoint` (off `main`, which already has C-22b + C-23; spec + handoff already committed on this branch).

---

## File Structure

- **`.amap/tools/gate-check/gates.py`** (modify) — add `validate_teaching_moment` + `_tm_field` helper + `_TM_VALID`/`_TM_PLACEHOLDERS` constants. Reuse the existing `_SECTION` regex.
- **`.amap/tools/gate-check/cli.py`** (modify) — register `"teaching-moment": "validate_teaching_moment"`.
- **`.amap/tools/gate-check/tests/test_gates.py`** (modify) — validator pass/fail unit tests + the seeded-template forcing-function test.
- **`.amap/knowledge/templates/AGENT_TRANSPARENCY.tpl.md`** (modify) — seed `## Teaching Moment Check` in a non-passing state (blank `status`/`note`).
- **`.amap/workflows/task.md`** (modify) — §0 reset emits the section; Pha 3 post-phase self-check requires it resolved. (prose; verified by inspection)
- **`.amap/skills/knowledge-curator/SKILL.md`** (modify) — `archive_active_context` PRE-CHECK runs the validator and ABORTs on non-zero. (prose; verified by inspection)

---

### Task 1: `validate_teaching_moment` validator + CLI

**Files:**
- Modify: `.amap/tools/gate-check/gates.py`
- Modify: `.amap/tools/gate-check/cli.py`
- Test: `.amap/tools/gate-check/tests/test_gates.py`

- [ ] **Step 1: Write the failing tests**

Open `.amap/tools/gate-check/tests/test_gates.py` and match its existing gates alias (shown here as `g`; `Path`/`importlib` are already imported there from earlier tasks). Append:

```python
def _tm(section_body: str) -> str:
    return "# AGENT_TRANSPARENCY\n\n## Teaching Moment Check\n\n" + section_body + "\n"


def test_tm_pass_none_with_note():
    body = "status: none\nnote: no correction-with-principle observed in this session\ntarget_updates:\nwarn:\nreason:"
    assert g.validate_teaching_moment(_tm(body)).ok is True


def test_tm_pass_captured_with_targets():
    body = "status: captured\nnote: user confirmed split\ntarget_updates:\n  - author-dna.yaml: HP-12\n  - conventions.yaml: CP-3\nwarn:\nreason:"
    assert g.validate_teaching_moment(_tm(body)).ok is True


def test_tm_pass_declined_with_warn_and_reason():
    body = "status: declined\nnote:\ntarget_updates:\nwarn: [R-DNA-7] Teaching moment chua capture: prefer composition.\nreason: user declined capture"
    assert g.validate_teaching_moment(_tm(body)).ok is True


def test_tm_pass_pending_with_warn_and_reason():
    body = "status: pending-confirmation\nnote:\ntarget_updates:\nwarn: [R-DNA-7] Teaching moment chua capture: factory boundary.\nreason: awaiting user confirmation"
    assert g.validate_teaching_moment(_tm(body)).ok is True


def test_tm_fail_missing_section():
    result = g.validate_teaching_moment("# AGENT_TRANSPARENCY\n\n## Phase State\n\nphase_state: applying\n")
    assert result.ok is False
    assert "missing" in result.reason.lower()


def test_tm_fail_blank_status():
    body = "status:\nnote:\ntarget_updates:\nwarn:\nreason:"
    result = g.validate_teaching_moment(_tm(body))
    assert result.ok is False
    assert "status must be one of" in result.reason


def test_tm_fail_invalid_status():
    assert g.validate_teaching_moment(_tm("status: maybe\nnote: x")).ok is False


def test_tm_fail_none_without_note():
    result = g.validate_teaching_moment(_tm("status: none\nnote:\ntarget_updates:\nwarn:\nreason:"))
    assert result.ok is False
    assert "active assertion note" in result.reason


def test_tm_fail_none_with_placeholder_note():
    result = g.validate_teaching_moment(_tm("status: none\nnote: fill before archive"))
    assert result.ok is False


def test_tm_fail_captured_without_targets():
    result = g.validate_teaching_moment(_tm("status: captured\nnote: x\ntarget_updates:\nwarn:\nreason:"))
    assert result.ok is False
    assert "target_updates" in result.reason


def test_tm_fail_declined_without_warn():
    result = g.validate_teaching_moment(_tm("status: declined\nnote:\ntarget_updates:\nwarn:\nreason: user declined"))
    assert result.ok is False


def test_tm_fail_declined_without_reason():
    result = g.validate_teaching_moment(_tm("status: declined\nwarn: [R-DNA-7] x\nreason:"))
    assert result.ok is False


def test_tm_fail_pending_without_warn():
    result = g.validate_teaching_moment(_tm("status: pending-confirmation\nreason: awaiting"))
    assert result.ok is False


def test_tm_fail_pending_without_reason():
    result = g.validate_teaching_moment(_tm("status: pending-confirmation\nwarn: [R-DNA-7] x\nreason:"))
    assert result.ok is False


def test_cli_teaching_moment_exit_codes(tmp_path):
    import importlib.util
    cli_mod = Path(__file__).resolve().parents[1] / "cli.py"
    spec = importlib.util.spec_from_file_location("cli", cli_mod)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)

    f = tmp_path / "AGENT_TRANSPARENCY.md"
    f.write_text(_tm("status: none\nnote: nothing to capture this session"), encoding="utf-8")
    assert cli.main(["teaching-moment", str(f)]) == 0
    f.write_text(_tm("status:\nnote:"), encoding="utf-8")
    assert cli.main(["teaching-moment", str(f)]) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -k tm -v`
Expected: FAIL — `module 'gates' has no attribute 'validate_teaching_moment'` + CLI unknown choice.

- [ ] **Step 3: Implement the validator**

In `.amap/tools/gate-check/gates.py`, add after `validate_phase_chain` (the `_SECTION` constant and `re` import already exist further down/up — `_SECTION = r"##\s+{name}[ \t]*\n(.*?)(?=\n##\s|\Z)"` is defined; reuse it):

```python
_TM_VALID = ("none", "captured", "declined", "pending-confirmation")
_TM_PLACEHOLDERS = {"fill before archive"}


def _tm_field(body: str, key: str, multiline: bool = False) -> str:
    if multiline:
        m = re.search(rf"^{key}:[ \t]*(.*(?:\n[ \t]+.*)*)", body, re.MULTILINE)
    else:
        m = re.search(rf"^{key}:[ \t]*(.*)$", body, re.MULTILINE)
    return m.group(1).strip() if m else ""


def validate_teaching_moment(text: str) -> Result:
    """R-DNA-7 pre-archive acknowledgment. Structural invariants only — cannot
    prove a teaching moment actually occurred (honor-code; see spec C-24)."""
    m = re.search(_SECTION.format(name=re.escape("Teaching Moment Check")), text, re.DOTALL | re.IGNORECASE)
    if not m:
        return Result(False, "Teaching Moment Check section missing. Add section before archive.")
    body = m.group(1)
    status = _tm_field(body, "status")
    if status not in _TM_VALID:
        return Result(False, "status must be one of none, captured, declined, pending-confirmation.")
    if status == "none":
        note = _tm_field(body, "note")
        if not note or note.lower() in _TM_PLACEHOLDERS:
            return Result(False, "status none requires a non-empty active assertion note.")
    elif status == "captured":
        if not _tm_field(body, "target_updates", multiline=True):
            return Result(False, "status captured requires non-empty target_updates.")
    elif status in ("declined", "pending-confirmation"):
        if "[R-DNA-7]" not in body:
            return Result(False, f"status {status} requires [R-DNA-7] WARN and reason.")
        if not _tm_field(body, "reason"):
            return Result(False, f"status {status} requires [R-DNA-7] WARN and reason.")
    return Result(True)
```

Note: `_SECTION` is defined lower in the file (used by `_section_has_text`). If `validate_teaching_moment` is placed above the `_SECTION` definition, move the new function below it (after `_section_has_text`) so `_SECTION` is in scope at call time. Module-level functions resolve `_SECTION` at call time, so placement after the assignment is sufficient; verify with the test run.

- [ ] **Step 4: Register the CLI subcommand**

In `.amap/tools/gate-check/cli.py`, add to the `VALIDATORS` dict:

```python
    "teaching-moment": "validate_teaching_moment",
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -v`
Expected: all PASS (new `tm`/CLI tests + every pre-existing gate test, including `apply_gate`).

- [ ] **Step 6: Commit**

```bash
git add .amap/tools/gate-check/gates.py .amap/tools/gate-check/cli.py .amap/tools/gate-check/tests/test_gates.py
git commit -m "feat(gate-check): add teaching-moment validator (R-DNA-7 acknowledgment)"
```

---

### Task 2: Seed the transparency template in a failing state

**Files:**
- Modify: `.amap/knowledge/templates/AGENT_TRANSPARENCY.tpl.md`
- Test: `.amap/tools/gate-check/tests/test_gates.py`

- [ ] **Step 1: Write the failing forcing-function test**

Append to `.amap/tools/gate-check/tests/test_gates.py`:

```python
def test_seeded_template_fails_teaching_moment_validator():
    tpl = Path(__file__).resolve().parents[3] / "knowledge" / "templates" / "AGENT_TRANSPARENCY.tpl.md"
    content = tpl.read_text(encoding="utf-8")
    assert g.validate_teaching_moment(content).ok is False
```

- [ ] **Step 2: Run it to verify it fails**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py::test_seeded_template_fails_teaching_moment_validator -v`
Expected: FAIL — the template has no `## Teaching Moment Check` section yet, so the validator returns `False` for "missing"… which is actually a PASS for this assertion. To make this a true red→green: this test passes immediately (missing section ⇒ ok is False). That is acceptable — it locks in that the template must never satisfy the validator. After Step 3 adds the section in a *blank-status* state, it must STILL fail (blank status), so the assertion holds. Run again after Step 3 to confirm it remains green for the right reason (blank status, not missing section).

- [ ] **Step 3: Add the seeded section to the template**

In `.amap/knowledge/templates/AGENT_TRANSPARENCY.tpl.md`, add this section just before the final `## Đánh giá Độ tin cậy tổng thể` section (after the `## Violation Log` block):

```md
---

## Teaching Moment Check

<!-- R-DNA-7: Resolve before archive. Do NOT pre-fill status: none.
     status: one of none | captured | declined | pending-confirmation
       none      → requires a real active-assertion note (not a placeholder)
       captured  → requires target_updates (which long-term files got the entry)
       declined / pending-confirmation → require a [R-DNA-7] warn line + reason -->
status:
note:
target_updates:
warn:
reason:
```

- [ ] **Step 4: Confirm the test passes for the right reason**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py::test_seeded_template_fails_teaching_moment_validator -v`
Expected: PASS. Manually confirm the failure reason is the blank status (not missing section):

```bash
/usr/bin/python3 .amap/tools/gate-check/cli.py teaching-moment .amap/knowledge/templates/AGENT_TRANSPARENCY.tpl.md
```
Expected output: `FAIL — status must be one of none, captured, declined, pending-confirmation.`

- [ ] **Step 5: Commit**

```bash
git add .amap/knowledge/templates/AGENT_TRANSPARENCY.tpl.md .amap/tools/gate-check/tests/test_gates.py
git commit -m "feat(template): seed non-passing Teaching Moment Check section"
```

---

### Task 3: Wire the checkpoint into task.md + knowledge-curator (prose)

**Files:**
- Modify: `.amap/workflows/task.md`
- Modify: `.amap/skills/knowledge-curator/SKILL.md`

> These are agent-instruction (prose) changes. There is no Python archive module to unit-test, so verification is text inspection (Step 4), per spec §11.

- [ ] **Step 1: Ensure the bootstrap reset path seeds the section**

In `.amap/workflows/task.md` section `## 0. Bootstrap context`, step 3 ("Reset `…/AGENT_TRANSPARENCY.md`"), append a sub-bullet:

```
   - Bao gồm section `## Teaching Moment Check` ở trạng thái non-passing (status rỗng) — giống template `AGENT_TRANSPARENCY.tpl.md`. KHÔNG pre-fill `status: none`.
```

- [ ] **Step 2: Add the Pha 3 post-phase self-check item**

In `.amap/workflows/task.md`, in the `[POST-PHASE SELF-CHECK — Pha 3]` checklist (the block before calling knowledge-curator archive), add a checkbox line:

```
   - `[ ]` Teaching Moment Check trong AGENT_TRANSPARENCY.md đã resolved — chạy `python3 {{ platform.framework_root }}/tools/gate-check/cli.py teaching-moment {{ platform.framework_root }}/knowledge/active/AGENT_TRANSPARENCY.md` và pass (exit 0) trước khi gọi knowledge-curator.
```

- [ ] **Step 3: Mandate the validator in knowledge-curator pre-archive**

In `.amap/skills/knowledge-curator/SKILL.md`, in `archive_active_context` `PRE-CHECK (theo R-Guard-1)` (after the TOKEN_LOG step), add:

```
  5. Teaching Moment gate (R-DNA-7): chạy
     `python3 {{ platform.framework_root }}/tools/gate-check/cli.py teaching-moment {{ platform.framework_root }}/knowledge/active/AGENT_TRANSPARENCY.md`
     → Exit 0: tiếp tục archive.
     → Exit ≠ 0: ABORT archive, in lỗi cụ thể từ validator, yêu cầu agent resolve section
       `## Teaching Moment Check` (đặt status hợp lệ + bằng chứng) rồi chạy lại.
     Giới hạn: validator chỉ kiểm cấu trúc, không chứng minh được có teaching moment thật.
     Việc gọi gate này là honor-code (archive không bị PreToolUse write-gate chặn).
```

- [ ] **Step 4: Verify by inspection**

Run:
```bash
/usr/bin/grep -n "teaching-moment\|Teaching Moment" .amap/workflows/task.md .amap/skills/knowledge-curator/SKILL.md .amap/knowledge/templates/AGENT_TRANSPARENCY.tpl.md
```
Expected: the reset-seed bullet, the Pha 3 self-check line, the knowledge-curator PRE-CHECK step, and the template section all present.

- [ ] **Step 5: Commit**

```bash
git add .amap/workflows/task.md .amap/skills/knowledge-curator/SKILL.md
git commit -m "docs(flow): mandate teaching-moment checkpoint before archive (R-DNA-7)"
```

---

### Task 4: Full verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full affected suite**

Run: `/usr/bin/python3 -m pytest .amap/tools .amap/hooks cli/tests -q`
Expected: all PASS (the new teaching-moment tests compose with existing apply-gate/write-gate tests).

- [ ] **Step 2: Smoke — resolved checkpoint passes, blank fails**

```bash
T=$(mktemp); printf '## Teaching Moment Check\n\nstatus: none\nnote: nothing to capture\n' > "$T"
/usr/bin/python3 .amap/tools/gate-check/cli.py teaching-moment "$T"; echo "resolved exit=$?"
printf '## Teaching Moment Check\n\nstatus:\nnote:\n' > "$T"
/usr/bin/python3 .amap/tools/gate-check/cli.py teaching-moment "$T"; echo "blank exit=$?"
rm -f "$T"
```
Expected: `resolved exit=0`, then `FAIL — status must be one of …` with `blank exit=1`.

---

## Self-Review

**Spec coverage:**
- §4/§8 machine-checked invariants + error messages → Task 1 validator + unit tests (every invariant has a pass and fail test).
- §2.2 CLI validator → Task 1 (`teaching-moment` in VALIDATORS + CLI test).
- §5.1 template seed must fail → Task 2 (seeded section + forcing-function test).
- §6/§7 data flow + both reset paths seed the section → Task 3 Step 1 (task.md §0) + the template (Task 2) covers knowledge-curator's reset-from-template path.
- §6 Pha 3 self-check before archive → Task 3 Step 2.
- §2.3/§6 knowledge-curator runs validator + ABORT on non-zero → Task 3 Step 3.
- §3 honor-code boundary → encoded in the validator docstring + the knowledge-curator note (Task 1 + Task 3 Step 3).
- §11 test plan (validator-only; no pytest for "archive aborts") → Tasks 1–2 cover the testable surface; Task 3 verified by inspection (Step 4), explicitly not pytest.
- §10 non-goals → nothing in the plan adds heuristic detection, a new artifact, or a runtime hook.

**Placeholder scan:** No TBD/TODO. Task 2 Step 2's note about red/green nuance is an explicit explanation, not a deferred action.

**Type/name consistency:** `validate_teaching_moment(text) -> Result` defined in Task 1, used as `g.validate_teaching_moment(...)` in tests and `"teaching-moment": "validate_teaching_moment"` in cli. `_tm_field`, `_TM_VALID`, `_TM_PLACEHOLDERS` consistent. `_SECTION` reused (not redefined). The `[R-DNA-7]` token matches the format in `rules-guard.md`. Status enum `none|captured|declined|pending-confirmation` consistent across validator, tests, template, and prose.
