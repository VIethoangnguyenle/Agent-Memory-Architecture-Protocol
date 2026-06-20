# Archive-Ready Gate + spec-extract pre_conditions (C-25) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert knowledge-curator's prose "ABORT archive when blocked" into a deterministic `gate-check archive-ready` check, and give spec-extract well-formed `pre_conditions`.

**Architecture:** Add `validate_archive_ready` to `gate-check/gates.py` (mirrors `validate_apply_gate`): it reads `phase_state` from the `## Phase State` section of `AGENT_TRANSPARENCY.md` and fails when blocked. Wire it as a mandated PRE-CHECK call in `knowledge-curator` (honor-code trigger, like C-24). Add file `pre_conditions` to `spec-extract` (R-Guard-1 + skill-lint).

**Tech Stack:** Python 3.9+ stdlib (`re`), pytest (`/usr/bin/python3 -m pytest`, import-mode=importlib).

**Spec:** `docs/superpowers/specs/2026-06-20-archive-ready-gate-design.md`

**Branch:** `archive-ready-gate` (off `main`, which has C-22b/C-23/C-24; spec already committed on this branch).

---

## File Structure

- **`.amap/tools/gate-check/gates.py`** (modify) — add `validate_archive_ready` + `_ARCHIVE_BLOCKED`. Reuse `_SECTION`.
- **`.amap/tools/gate-check/cli.py`** (modify) — register `"archive-ready": "validate_archive_ready"`.
- **`.amap/tools/gate-check/tests/test_gates.py`** (modify) — validator + CLI unit tests.
- **`.amap/skills/spec-extract/SKILL.md`** (modify) — add `pre_conditions` frontmatter.
- **`.amap/skills/knowledge-curator/SKILL.md`** (modify) — PRE-CHECK step 3 becomes the deterministic gate. (prose; verified by inspection + skill-lint)

---

### Task 1: `validate_archive_ready` validator + CLI

**Files:**
- Modify: `.amap/tools/gate-check/gates.py`
- Modify: `.amap/tools/gate-check/cli.py`
- Test: `.amap/tools/gate-check/tests/test_gates.py`

- [ ] **Step 1: Write the failing tests**

Append to `.amap/tools/gate-check/tests/test_gates.py` (match the existing gates alias `g`; `Path`/`importlib` already imported):

```python
def _ps(value: str) -> str:
    return f"# AGENT_TRANSPARENCY\n\n## Phase State\n\n```\nphase_state: {value}\n```\n\n## Next\n\nx\n"


def test_archive_ready_fail_blocked_by_arch():
    result = g.validate_archive_ready(_ps("blocked-by-arch"))
    assert result.ok is False
    assert "blocked-by-arch" in result.reason


def test_archive_ready_fail_blocked_by_data():
    assert g.validate_archive_ready(_ps("blocked-by-data")).ok is False


def test_archive_ready_pass_completed():
    assert g.validate_archive_ready(_ps("completed")).ok is True


def test_archive_ready_pass_applying():
    assert g.validate_archive_ready(_ps("applying")).ok is True


def test_archive_ready_pass_phase2_done():
    assert g.validate_archive_ready(_ps("phase-2-done")).ok is True


def test_archive_ready_pass_when_no_phase_state():
    assert g.validate_archive_ready("# AGENT_TRANSPARENCY\n\nno phase section here\n").ok is True


def test_cli_archive_ready_exit_codes(tmp_path):
    import importlib.util
    cli_mod = Path(__file__).resolve().parents[1] / "cli.py"
    spec = importlib.util.spec_from_file_location("cli", cli_mod)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)

    f = tmp_path / "AGENT_TRANSPARENCY.md"
    f.write_text(_ps("applying"), encoding="utf-8")
    assert cli.main(["archive-ready", str(f)]) == 0
    f.write_text(_ps("blocked-by-arch"), encoding="utf-8")
    assert cli.main(["archive-ready", str(f)]) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -k archive_ready -v`
Expected: FAIL — `module 'gates' has no attribute 'validate_archive_ready'` + CLI invalid choice.

- [ ] **Step 3: Implement the validator**

In `.amap/tools/gate-check/gates.py`, add after `validate_apply_gate` (`_SECTION` and `re` already exist in the module; `_SECTION` is defined lower — module functions resolve it at call time, but to be safe place this function AFTER the `_SECTION = ...` assignment / next to `validate_node_checkpoint`):

```python
_ARCHIVE_BLOCKED = {"blocked-by-arch", "blocked-by-data"}


def validate_archive_ready(text: str) -> Result:
    """Pre-archive guard: refuse to archive/reset while the task is blocked.
    Reads phase_state from the '## Phase State' section. Deterministic check;
    honor-code trigger (archive is not hook-intercepted)."""
    m = re.search(_SECTION.format(name=re.escape("Phase State")), text, re.DOTALL | re.IGNORECASE)
    section = m.group(1) if m else ""
    ps = re.search(r"phase_state:\s*(\S+)", section)
    phase_state = ps.group(1).strip() if ps else ""
    if phase_state in _ARCHIVE_BLOCKED:
        return Result(False, f"archive blocked: phase_state={phase_state} — resolve the blocker first")
    return Result(True)
```

- [ ] **Step 4: Register the CLI subcommand**

In `.amap/tools/gate-check/cli.py`, add to the `VALIDATORS` dict:

```python
    "archive-ready": "validate_archive_ready",
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -v`
Expected: all PASS (new archive_ready/CLI tests + every pre-existing gate test incl. apply_gate, teaching_moment).

- [ ] **Step 6: Commit**

```bash
git add .amap/tools/gate-check/gates.py .amap/tools/gate-check/cli.py .amap/tools/gate-check/tests/test_gates.py
git commit -m "feat(gate-check): add archive-ready validator (phase_state not blocked)"
```

---

### Task 2: spec-extract `pre_conditions`

**Files:**
- Modify: `.amap/skills/spec-extract/SKILL.md`

> Verified by `skill-lint` (it validates `pre_conditions` structure, check F4). No new pytest needed beyond the lint run.

- [ ] **Step 1: Confirm spec-extract currently lints PASS without pre_conditions**

Run: `/usr/bin/python3 .amap/tools/skill-lint/validate_skills.py`
Expected: `14/14 skills PASS`. Note spec-extract's `F4` column shows `--` (no pre_conditions).

- [ ] **Step 2: Add the `pre_conditions` block to the frontmatter**

In `.amap/skills/spec-extract/SKILL.md`, the frontmatter currently ends after the `description:` block, before the closing `---`. Add a `pre_conditions:` key (same indentation level as `name`/`version`/`description`), so the frontmatter becomes:

```yaml
---
name: spec-extract
version: '1.0'
description: >
  Trích xuất spec có cấu trúc từ tài liệu (wiki/Confluence/PRD) vào REQUIREMENT.md, kèm đánh giá độ tin cậy.
  Dùng khi đầu vào là tài liệu dài, wiki nhiều trang, hoặc PRD cần parse.
  KHÔNG dùng cho: ticket có sẵn đã rõ scope (→ requirement-analyst),
  ideation/brainstorm (→ openspec-explore), khám phá DB schema (→ db-explorer).
pre_conditions:
  - file: "{{ platform.framework_root }}/knowledge/active/AGENT_TRANSPARENCY.md"
    condition: exists
    on_fail: "ABORT — bootstrap chưa chạy, gọi `/task` trước"
  - input: doc_url_or_text
    condition: not_empty
    on_fail: "ABORT — thiếu tài liệu nguồn để extract"
---
```

(Keep the rest of the body unchanged. Do not alter `name`/`version`/`description`.)

- [ ] **Step 3: Verify skill-lint still PASS (now with F4 for spec-extract)**

Run: `/usr/bin/python3 .amap/tools/skill-lint/validate_skills.py`
Expected: `14/14 skills PASS`; spec-extract's `F4` column now shows `✅` (valid pre_conditions structure) instead of `--`.

Also run the skill-lint test suite to confirm no regression:
Run: `/usr/bin/python3 -m pytest .amap/tools/skill-lint -q`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add .amap/skills/spec-extract/SKILL.md
git commit -m "feat(spec-extract): declare pre_conditions (bootstrap + non-empty input)"
```

---

### Task 3: Wire archive-ready into knowledge-curator PRE-CHECK (prose)

**Files:**
- Modify: `.amap/skills/knowledge-curator/SKILL.md`

> Prose (agent-instruction) change. knowledge-curator is a SKILL, not a Python module — verified by inspection (Step 2), not pytest, per the C-24 precedent.

- [ ] **Step 1: Replace PRE-CHECK step 3 with the deterministic gate**

In `.amap/skills/knowledge-curator/SKILL.md`, in `### 3.1 archive_active_context(...)` `PRE-CHECK (theo R-Guard-1):`, step 3 currently reads:

```
  3. Nếu phase_state = `blocked-by-arch` | `blocked-by-data`:
     → ABORT: "Task đang bị BLOCK — không thể archive cho đến khi block được resolve"
```

Replace it with:

```
  3. Archive-ready gate (deterministic, R-DNA / R-Guard): chạy
     `python3 {{ platform.framework_root }}/tools/gate-check/cli.py archive-ready {{ platform.framework_root }}/knowledge/active/AGENT_TRANSPARENCY.md`
     → Exit ≠ 0 (phase_state = blocked-by-arch | blocked-by-data): ABORT archive, in lý do
       cụ thể từ validator — không thể archive cho đến khi block được resolve.
     → Exit 0: tiếp tục.
     Giới hạn: check deterministic, nhưng việc gọi gate là honor-code (archive không bị
     PreToolUse write-gate chặn).
```

(Leave step 2 — the `phase_state ∉ {completed, cancelled}` WARN — and steps 4–5 — TOKEN_LOG, teaching-moment gate — unchanged.)

- [ ] **Step 2: Verify by inspection**

Run:
```bash
/usr/bin/grep -n "archive-ready" .amap/skills/knowledge-curator/SKILL.md
```
Expected: shows the `gate-check archive-ready` call inside the PRE-CHECK block (step 3).

- [ ] **Step 3: Commit**

```bash
git add .amap/skills/knowledge-curator/SKILL.md
git commit -m "docs(knowledge-curator): gate archive on deterministic phase_state check"
```

---

### Task 4: Full verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full affected suite**

Run: `/usr/bin/python3 -m pytest .amap/tools .amap/hooks cli/tests -q`
Expected: all PASS.

- [ ] **Step 2: Smoke — blocked phase_state blocks archive-ready, applying passes**

```bash
T=$(mktemp); printf '## Phase State\n\n```\nphase_state: blocked-by-arch\n```\n' > "$T"
/usr/bin/python3 .amap/tools/gate-check/cli.py archive-ready "$T"; echo "blocked exit=$?"
printf '## Phase State\n\n```\nphase_state: applying\n```\n' > "$T"
/usr/bin/python3 .amap/tools/gate-check/cli.py archive-ready "$T"; echo "applying exit=$?"
rm -f "$T"
```
Expected: `archive blocked: phase_state=blocked-by-arch …` with `blocked exit=1`; then `applying exit=0`.

- [ ] **Step 3: Confirm skill-lint clean**

Run: `/usr/bin/python3 .amap/tools/skill-lint/validate_skills.py`
Expected: `14/14 skills PASS`.

---

## Self-Review

**Spec coverage:**
- §3.1 `validate_archive_ready` (phase_state ∈ blocked → FAIL, else PASS, fail-open on missing) → Task 1 + unit tests (blocked-by-arch/data fail; completed/applying/phase-2-done/missing pass).
- §3.1 CLI `archive-ready` → Task 1 (VALIDATORS + CLI exit-code test).
- §3.2 knowledge-curator mandated call + ABORT → Task 3.
- §3.3 spec-extract `pre_conditions` → Task 2 (+ skill-lint F4 verification).
- §4 honor-code boundary → encoded in validator docstring + knowledge-curator "Giới hạn" note.
- §6 acceptance (incl. exit condition: blocked-by-arch fixture → non-zero) → Task 1 tests + Task 4 smoke.
- §2 non-goals → nothing in the plan builds a general evaluator, bulk pre_conditions, or outputs declarations.

**Placeholder scan:** No TBD/TODO. The `_SECTION` placement note in Task 1 Step 3 is a concrete guidance, not deferred work.

**Type/name consistency:** `validate_archive_ready(text) -> Result` defined in Task 1, used as `g.validate_archive_ready` in tests and `"archive-ready": "validate_archive_ready"` in cli. `_ARCHIVE_BLOCKED`, `_SECTION`, `Result` consistent. `phase_state` values (`blocked-by-arch`, `blocked-by-data`, `applying`, `completed`, `phase-2-done`) match the template's documented enum. spec-extract `pre_conditions` keys (`file`/`input`/`condition`/`on_fail`) match the skill-lint F4 schema and the db-explorer/requirement-analyst precedent.
