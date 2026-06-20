# Archive-Ready Gate + spec-extract pre_conditions (C-25) — Design

> **Date:** 2026-06-20
> **Status:** Approved (design) — ready for implementation plan
> **Branch:** `archive-ready-gate` (off `main`, which has C-22b/C-23/C-24).
> **Lineage:** enforcement audit 2026-06-20 item **#4** (destructive skills lack
> machine-readable guards). Reuses the C-24 pattern (gate-check validator + mandated
> PRE-CHECK call).

---

## 1. Context & problem

Audit item #4: the most destructive skill — `knowledge-curator`, which resets
`knowledge/active/` and mutates the long-term snapshot — guards itself with **prose**
(`archive_active_context` PRE-CHECK: "nếu phase_state = blocked-by-arch | blocked-by-data
→ ABORT"). spec-extract (writes `REQUIREMENT.md`) has no `pre_conditions` at all.

Two findings shape the fix:

- **`pre_conditions` has no runtime evaluator.** The condition keywords
  (`not_empty`/`not_skeleton`/`exists`/`phase_done`) appear only in `skill-lint`
  (validates the *structure* of a `pre_conditions` block if present) — nothing reads a
  skill's `pre_conditions` and checks them against real context files. So R-Guard-1 is
  agent-prose (honor-code), not mechanical.
- **knowledge-curator's real guard is a `phase_state` *value* check, not file-existence.**
  It doesn't fit the file/tool-oriented `pre_conditions` vocab. Bolting file
  `pre_conditions` onto it would be the wrong shape; what it needs is a deterministic
  `phase_state` guard.

Decision (see Non-Goals for rejected alternatives): **targeted** — give knowledge-curator
a deterministic `phase_state` gate (the proven C-24 pattern), and give spec-extract the
file `pre_conditions` that genuinely fit it. Do not build a general `pre_conditions`
evaluator, and do not bulk-add `pre_conditions` to non-destructive skills.

## 2. Goal & non-goals

- **Goal:** convert knowledge-curator's prose "ABORT when blocked" into a deterministic
  pre-archive check, and give spec-extract a well-formed `pre_conditions` guard.
- **Non-goals (YAGNI, recorded):**
  - No general `gate-check pre-conditions` evaluator that reads any skill's frontmatter
    (heavy; marginal risk for non-destructive skills; trigger stays agent-driven anyway).
  - No bulk `pre_conditions` on the other 6 skills lacking them (mostly non-destructive,
    no real guard → cargo-cult).
  - No `outputs:` declarations / R-Path-1 lint cross-check (orthogonal; separate follow-up).

## 3. Mechanism

### 3.1 `validate_archive_ready` — `gates.py`
`validate_archive_ready(text) -> Result`:
- Extract `phase_state` value from the `## Phase State` section of `AGENT_TRANSPARENCY.md`
  (reuse the `_SECTION` regex; read `phase_state:\s*(\S+)` inside that section).
- **FAIL** if `phase_state ∈ {blocked-by-arch, blocked-by-data}` — reason names the blocked
  state and says to resolve the blocker first.
- **PASS** otherwise (including when phase_state is absent — fail-open here is acceptable;
  the C-24 teaching-moment gate + Pha 3 self-check cover the rest of archive-readiness).
- Mirrors the shape of `validate_apply_gate`.

Register `"archive-ready": "validate_archive_ready"` in `cli.py` VALIDATORS.

### 3.2 Wire into knowledge-curator PRE-CHECK
In `knowledge-curator/SKILL.md` `archive_active_context` PRE-CHECK, replace/augment the
prose "phase_state blocked → ABORT" step with a mandated deterministic call:
```
python3 {{ platform.framework_root }}/tools/gate-check/cli.py archive-ready \
  {{ platform.framework_root }}/knowledge/active/AGENT_TRANSPARENCY.md
```
Exit 0 → continue; exit ≠ 0 → ABORT archive, print the validator reason. Keep the existing
prose `phase_state ∉ {completed,cancelled}` WARN (that is advisory, not a hard block).

### 3.3 spec-extract `pre_conditions`
Add to `spec-extract/SKILL.md` frontmatter (mirroring requirement-analyst):
```yaml
pre_conditions:
  - file: "{{ platform.framework_root }}/knowledge/active/AGENT_TRANSPARENCY.md"
    condition: exists
    on_fail: "ABORT — bootstrap chưa chạy, gọi `/task` trước"
  - input: doc_url_or_text
    condition: not_empty
    on_fail: "ABORT — thiếu tài liệu nguồn để extract"
```
This guard is enforced by R-Guard-1 (agent-check) + structure-validated by skill-lint —
honor-code, acceptable for a non-destructive write skill.

## 4. Honest enforcement boundary

`archive-ready` is a **deterministic check with an honor-code trigger** — archive/reset is
not intercepted by the PreToolUse write-gate, so knowledge-curator calling the validator is
agent-mandated, not runtime-forced. Same class as C-24: stronger than prose, weaker than the
C-22/C-23 write/apply gates. spec-extract `pre_conditions` are fully honor-code (no evaluator).

## 5. Files

- `.amap/tools/gate-check/gates.py` — add `validate_archive_ready`.
- `.amap/tools/gate-check/cli.py` — register `archive-ready`.
- `.amap/tools/gate-check/tests/test_gates.py` — validator unit tests.
- `.amap/skills/spec-extract/SKILL.md` — add `pre_conditions` frontmatter.
- `.amap/skills/knowledge-curator/SKILL.md` — mandate `gate-check archive-ready` in PRE-CHECK.

## 6. Test plan / acceptance

**`validate_archive_ready` (unit):**
- `## Phase State` with `phase_state: blocked-by-arch` → FAIL (reason names the state).
- `phase_state: blocked-by-data` → FAIL.
- `phase_state: completed` → PASS; `phase_state: applying` → PASS; `phase_state: phase-2-done` → PASS.
- no `## Phase State` / no phase_state → PASS (fail-open, documented).

**CLI:** `gate-check archive-ready <file>` exit 0 (pass) / 1 (blocked).

**spec-extract:** `skill-lint` PASS with the new `pre_conditions` (structure valid); `14/14`
skills still lint-PASS.

**Wiring (prose):** knowledge-curator PRE-CHECK references `gate-check archive-ready` with
ABORT-on-non-zero — verified by inspection (knowledge-curator is SKILL prose, not a Python
module; no pytest for "archive aborts", per the C-24 precedent).

**Exit condition:** a fixture `AGENT_TRANSPARENCY.md` with `phase_state: blocked-by-arch`
makes `gate-check archive-ready` exit non-zero, demonstrating the destructive reset is
deterministically blocked while a blocker is open.

## 7. Residual

- Trigger remains honor-code (archive not hook-intercepted).
- spec-extract `pre_conditions` are agent-checked (no evaluator) — structural lint only.
- General `pre_conditions` evaluator + `outputs:` machine-check remain unbuilt (Non-Goals);
  audit #6 (db-remote templating + orphan document-writer) is separate.
