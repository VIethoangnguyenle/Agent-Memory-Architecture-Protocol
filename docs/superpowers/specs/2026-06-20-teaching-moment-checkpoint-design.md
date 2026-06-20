# Teaching Moment Checkpoint - Design

> **Date:** 2026-06-20
> **Status:** Approved (design) - ready for implementation plan
> **Lineage:** enforcement audit 2026-06-20 residual **C-24 / #5**.
> C-22/C-23 made write/apply enforcement mechanical for code writes. This spec addresses
> the remaining R-DNA-7 gap: teaching moments are required by rule prose but have no
> operational trigger before archive/reset.

---

## 1. Context and Problem

`R-DNA-7` in `.amap/rules/rules-guard.md` requires the agent to capture a teaching
moment immediately in the same session.

A teaching moment is a user correction of the agent's code plus a technical principle,
for example:

- "Factory khong duoc chua business logic; validate logic phai nam o processor."
- "Khong dung inheritance o cho nay; dung composition de tranh coupling."
- "Mapper phai pure, dung inject repository vao mapper."

The rule already defines how to split the lesson:

- `author-dna.yaml` for thinking principles and WHY/HOW.
- `conventions.yaml` for naming, structure, and organization rules.
- `knowledge-snapshot.md` for concrete architecture or component facts.

The gap is operational, not conceptual. `task.md` Pha 3 and `knowledge-curator` do not
force a stop before archive/reset to ask whether a teaching moment occurred. If the
agent forgets, archive/reset can erase the live conversational context and the lesson is
lost.

This repeats the broader enforcement audit pattern: rules that exist only as prose are
easy for the agent to skip.

## 2. Design Goal

Add a lightweight but mechanical checkpoint before task archive:

1. Every task's `AGENT_TRANSPARENCY.md` must contain a resolved
   `## Teaching Moment Check` section before archive.
2. A new `gate-check teaching-moment <AGENT_TRANSPARENCY.md>` validator checks the
   section's structural invariants.
3. `knowledge-curator` must run that validator before archive and abort on non-zero exit.
4. The fresh template must seed the section in a failing state so the agent must make an
   explicit assertion before archive.

The goal is not perfect automatic detection. The goal is to make the agent leave an
auditable, deliberate statement: none observed, captured, declined, or awaiting
confirmation.

## 3. Honest Enforcement Boundary

This checkpoint is intentionally weaker than C-22/C-23 apply/write gates.

C-22/C-23 are runtime-hook backed: app-code writes can be denied by the PreToolUse
write-gate. Archive/reset is different. It is a lifecycle action over framework knowledge
files, not an app-code write path, so there is no runtime hook that forces
`knowledge-curator` to run a validator.

Therefore C-24 provides:

- mechanical validation of `AGENT_TRANSPARENCY.md`,
- a mandatory instruction in `task.md` and `knowledge-curator` to call the validator,
- an audit trail in archived transparency logs.

It does not provide a hard runtime block equivalent to `apply-gate`. The call site is
still honor-code. This is stronger than prose-only, but weaker than a write-hook
hard-block.

## 4. Machine-Checked vs Honor-Code Invariants

The validator can check only filesystem-visible structure.

Machine-checked invariants:

- `## Teaching Moment Check` section exists.
- `status` is one of:
  - `none`
  - `captured`
  - `declined`
  - `pending-confirmation`
- `none` has a non-empty active assertion `note`.
- `captured` has non-empty `target_updates`.
- `declined` has a reason and an existing `[R-DNA-7]` warning token.
- `pending-confirmation` has a reason and an existing `[R-DNA-7]` warning token.

Honor-code invariant:

- If the session contained a user correction plus a technical principle, the agent must
  not write `status: none`.

The validator cannot prove from files alone whether the conversation contained a teaching
moment. If an agent dishonestly writes `none`, the validator passes, but the archived
audit trail exposes the false assertion for review.

## 5. Checkpoint Format

The section lives in `{{ platform.framework_root }}/knowledge/active/AGENT_TRANSPARENCY.md`.

### 5.1 Template Seed - Must Fail

`AGENT_TRANSPARENCY.tpl.md` must seed the section in a non-passing state:

```md
## Teaching Moment Check

<!-- Fill this section before archive. Do not pre-fill status: none. -->
status:
note:
target_updates:
warn:
reason:
```

The `note` value must be blank in the template. Do not seed `note: fill before archive`:
if the agent later sets `status: none` and forgets to update the note, a non-empty
placeholder would create a fake active assertion.

### 5.2 Valid Examples

No teaching moment observed:

```md
## Teaching Moment Check

status: none
note: no correction-with-principle observed in this session
target_updates:
warn:
reason:
```

Teaching moment captured:

```md
## Teaching Moment Check

status: captured
note: user confirmed the split and long-term updates were written
target_updates:
  - author-dna.yaml: HP-...
  - conventions.yaml: CP-...
warn:
reason:
```

User declined capture:

```md
## Teaching Moment Check

status: declined
note:
target_updates:
warn: [R-DNA-7] Teaching moment chua capture: prefer composition over inheritance for lifecycle decoupling.
reason: user declined capture
```

Awaiting confirmation:

```md
## Teaching Moment Check

status: pending-confirmation
note:
target_updates:
warn: [R-DNA-7] Teaching moment chua capture: factory boundary excludes business validation logic.
reason: awaiting user confirmation before writing long-term knowledge
```

### 5.3 Captured Means Real Capture

`captured` must not be used merely because the agent noticed a principle. It means the
target updates were written, or at minimum explicitly listed with confirmed user intent.
If the user has not confirmed the split yet, use `pending-confirmation`.

## 6. Data Flow

1. Fresh task bootstrap creates or resets `AGENT_TRANSPARENCY.md`.
2. All creation/reset paths seed `## Teaching Moment Check` in the failing template state.
3. During `/task apply`, if a user correction plus principle happens, the agent follows
   `R-DNA-7`: split the lesson, ask for confirmation, and write the approved target
   updates.
4. Before Pha 3 archive, `task.md` post-phase self-check requires the checkpoint to be
   resolved.
5. `knowledge-curator.archive_active_context(...)` runs:

   ```bash
   python3 {{ platform.framework_root }}/tools/gate-check/cli.py teaching-moment \
     {{ platform.framework_root }}/knowledge/active/AGENT_TRANSPARENCY.md
   ```

6. Exit `0` allows archive to proceed.
7. Non-zero exit aborts archive and tells the agent to resolve the section.
8. Archive preserves the section in `archive/{ticket-id}/AGENT_TRANSPARENCY.md`.

## 7. Reset Paths Must Both Seed the Section

There are two relevant creation/reset paths:

1. `knowledge-curator.reset_active_context()`
   - Uses `knowledge/templates/AGENT_TRANSPARENCY.tpl.md`.
   - Updating the template covers this path.

2. `/task` bootstrap in `.amap/workflows/task.md` section 0
   - Currently describes resetting `AGENT_TRANSPARENCY.md` inline by writing task ID,
     loaded rules, and phase history.
   - C-24 must update this path too, either by explicitly starting from the template or
     by emitting the same non-passing `Teaching Moment Check` section inline.

If only the template changes, the `/task` bootstrap path can create a fresh transparency
log without the section. That would produce a confusing archive failure or require the
agent to remember to add the section manually. Both paths must seed it deterministically.

## 8. Error Handling

Validator failures should be specific and actionable:

- Missing section:
  `FAIL: Teaching Moment Check section missing. Add section before archive.`
- Empty or invalid status:
  `FAIL: status must be one of none, captured, declined, pending-confirmation.`
- `none` without active assertion:
  `FAIL: status none requires a non-empty active assertion note.`
- `captured` without targets:
  `FAIL: status captured requires non-empty target_updates.`
- `declined` without warning or reason:
  `FAIL: status declined requires [R-DNA-7] WARN and reason.`
- `pending-confirmation` without warning or reason:
  `FAIL: status pending-confirmation requires [R-DNA-7] WARN and reason.`

For `declined` and `pending-confirmation`, the validator should look for the existing
`[R-DNA-7]` token defined by `rules-guard.md`. Do not invent a second warning format.

## 9. Implementation Scope

Files expected to change in the implementation plan:

- `.amap/tools/gate-check/gates.py`
  - Add a `teaching-moment` validator.
  - Reuse existing section parsing helpers/patterns such as `_SECTION` and
    `_section_has_text`; do not introduce a new Markdown parser.
- `.amap/tools/gate-check/cli.py`
  - Add `teaching-moment <AGENT_TRANSPARENCY.md>` command routing.
- `.amap/tools/gate-check/tests/test_gates.py` or a focused new test file
  - Add pass/fail coverage for all invariants.
- `.amap/knowledge/templates/AGENT_TRANSPARENCY.tpl.md`
  - Seed the non-passing checkpoint section with blank field values.
- `.amap/workflows/task.md`
  - Add the checkpoint to Pha 3 post-phase self-check.
  - Update section 0 bootstrap/reset instructions so all fresh transparency logs seed
    the section.
- `.amap/skills/knowledge-curator/SKILL.md`
  - Require `gate-check teaching-moment` before archive.
  - ABORT archive on non-zero exit.

Coordination note: enforcement #4 also touches `knowledge-curator` pre-archive guards by
adding machine-readable `pre_conditions`. It is preferable to implement #4 first, then
wire C-24 into the same pre-archive guard area to avoid conflicting edits. This is a
coordination preference, not a hard technical dependency.

## 10. Non-Goals

- No heuristic conversation detection in C-24.
- No parsing of raw chat transcripts.
- No attempt to prove that `status: none` is semantically truthful.
- No new `TEACHING_MOMENTS.md` artifact yet; keep the checkpoint in
  `AGENT_TRANSPARENCY.md` for B-lite scope.
- No runtime write-hook enforcement for archive/reset.
- No coverage for teaching moments outside `/task apply` archive flow, including manual
  edits to framework files under `.amap/`.

## 11. Test Plan

Mechanical tests cover only executable validator behavior.

Pass fixtures:

- `none` with a non-empty active assertion note.
- `captured` with non-empty `target_updates`.
- `declined` with `[R-DNA-7]` warning and reason.
- `pending-confirmation` with `[R-DNA-7]` warning and reason.

Fail fixtures:

- Missing `## Teaching Moment Check` section.
- Seeded template with blank `status`.
- Invalid `status`.
- `none` without `note`.
- `none` with blank `note`.
- If implementation recognizes placeholder tokens defensively: `none` with placeholder
  text such as `fill before archive`.
- `captured` without `target_updates`.
- `declined` without `[R-DNA-7]` warning.
- `declined` without reason.
- `pending-confirmation` without `[R-DNA-7]` warning.
- `pending-confirmation` without reason.

Template forcing-function test:

- A fixture matching the seeded template section must fail the validator as-is.

`knowledge-curator` caveat:

- `knowledge-curator` is skill prose, not a Python archive module. Do not promise pytest
  coverage for "archive aborts." The implementation can be verified by review/text
  inspection: the skill must instruct the agent to run the validator and ABORT on
  non-zero exit.

## 12. Acceptance Criteria

- `gate-check teaching-moment <AGENT_TRANSPARENCY.md>` exists and returns non-zero for
  unresolved or malformed checkpoint sections.
- A freshly seeded `AGENT_TRANSPARENCY` checkpoint does not pass by default.
- `status: none` requires a real active assertion note, not a pre-filled placeholder.
- `status: captured` requires non-empty `target_updates`.
- `status: declined` and `status: pending-confirmation` require both reason and
  `[R-DNA-7]` warning token.
- Both `AGENT_TRANSPARENCY.tpl.md` and `/task` bootstrap/reset instructions seed the
  checkpoint in a non-passing state.
- `task.md` Pha 3 requires the checkpoint before archive.
- `knowledge-curator` requires running the validator before archive and aborting on
  non-zero exit.
- Tests cover validator pass/fail cases and the seeded-template failure case.

## 13. Residual Risk

- Dishonest or inattentive `status: none` remains possible. This is the unavoidable
  honor-code portion because the validator cannot inspect the full human conversation.
- Archive/reset enforcement remains weaker than write-gate enforcement because no runtime
  hook forces the archive path to call `gate-check`.
- Teaching moments outside the `/task apply` archive flow are not covered in this slice.
