# Handoff → Codex: Enforcement follow-ups #4–#6 (audit 2026-06-20)

> **Audience:** Codex (cold start — assume no prior context).
> **Author:** Claude, 2026-06-20.
> **Scope:** Implement the remaining three gaps (#4, #5, #6) from the 2026-06-20
> enforcement audit of AMAP's RULES/SKILLS/WORKFLOWS layer. #1–#3 are already shipped.

---

## 0. Context you need first

AMAP is an agent framework whose source lives under `.amap/` (rules, skills, workflows,
procedures, tools, hooks). The CLI that scaffolds it into a target project lives under `cli/`.

**Central finding of the audit:** enforcement is two-tiered. Only the runtime **write-gate
hook** (`.amap/hooks/write-gate/write_gate.py`, a PreToolUse hook) enforces anything
mechanically. Everything else (`gate-check` CLI, `pre_conditions:` frontmatter, R-DNA-7,
etc.) depends on the agent voluntarily complying — "on paper".

**What was already fixed this session (do NOT redo):**
- **#1 Bash-write bypass** → branch `bash-write-gate`, PR #12. The hook now also gates
  `Bash` shell writes (`parse_shell_writes` heuristic) across all 3 runtime matchers.
- **#2 `/opsx:apply` back door** + **#3 gates-not-wired** → branch `apply-gate`, PR #13
  (stacked on #12). Added `validate_apply_gate` (requires `Pha 2 DONE` + no unresolved
  `[BLOCKER-ARCH]`) and wired it into `evaluate_write`, so any app-code write requires the
  spec phase to be complete — workflow-agnostic, closing the back door.

Read these for patterns to mirror:
- `docs/superpowers/specs/2026-06-20-bash-write-gate-design.md`
- `docs/superpowers/specs/2026-06-20-apply-gate-design.md` (+ matching plans in `plans/`)

**Process expectation:** AMAP work goes brainstorm → spec (`docs/superpowers/specs/`) →
plan (`docs/superpowers/plans/`) → TDD implementation → PR. #4 and #6a are mechanical
enough to spec lightly; **#5 needs a real brainstorm** (it's behavioral, not just code).

**Test runner:** `/usr/bin/python3 -m pytest` (the repo `.venv` python lacks pytest).
`grep -r` silently skips gitignored files here — use `/usr/bin/grep`.

---

## #4 — Destructive skills lack machine-readable `pre_conditions:`

**Problem.** `R-Guard-1` ([.amap/rules/rules-guard.md](../../../.amap/rules/rules-guard.md))
says: before running any skill that declares `pre_conditions:` in frontmatter, the agent
must check each condition (`not_empty`/`not_skeleton`/`exists`/`phase_done`) and run
`on_fail`. But the guard only fires for skills that *declare* `pre_conditions:`. The most
dangerous skills don't:
- **knowledge-curator** ([.amap/skills/knowledge-curator/SKILL.md](../../../.amap/skills/knowledge-curator/SKILL.md))
  resets `knowledge/active/` and mutates the snapshot, yet its guard is **prose** ("PRE-CHECK
  (theo R-Guard-1)" in the body, ~§3.1), not a machine-readable `pre_conditions:` block.
- **spec-extract** writes `REQUIREMENT.md` with no `pre_conditions` (no bootstrap check).
- Overall: 8/14 skills have no `pre_conditions`; **0/14 declare `outputs:`** even though
  `R-Path-1` ([.amap/rules/rules-knowledge.md](../../../.amap/rules/rules-knowledge.md) §12)
  has a full "who writes what" table.

**Verify current state:** `/usr/bin/grep -rL "pre_conditions" .amap/skills/*/SKILL.md`.
Schema + lint live in `.amap/tools/skill-lint/validate_skills.py` (frontmatter `F4`
validates `pre_conditions` structure if present; `F5` validates `outputs` if present —
both optional today).

**Proposed approach.**
1. Add a `pre_conditions:` block to **knowledge-curator** that encodes its existing prose
   pre-check in the 4 supported condition types. The tricky part: its prose has WARN-vs-ABORT
   branching on `phase_state` (blocked-by-arch → ABORT; not-completed → WARN). Map what fits
   the existing `condition`/`on_fail` schema; keep the rest as documented prose with a note.
   Confirm `skill-lint` still passes (`/usr/bin/python3 .amap/tools/skill-lint/validate_skills.py`).
2. Add `pre_conditions:` to **spec-extract** (at minimum a bootstrap/AGENT_TRANSPARENCY
   `exists` check, mirroring requirement-analyst).
3. (Optional, decide during spec) Add `outputs:` declarations to skills so the R-Path-1
   table becomes machine-checkable; consider a `skill-lint` rule that warns when a skill
   writes a path not declared in `outputs`. This may be its own follow-up — don't over-scope.

**Design question to resolve first:** the 4 condition types (`not_empty`/`not_skeleton`/
`exists`/`phase_done`) may not express knowledge-curator's `phase_state ∈ {blocked-*}` →
ABORT logic. Either (a) extend the condition vocabulary (and the R-Guard-1 checker), or
(b) accept that the machine block covers the common cases and the nuanced branch stays prose.
Pick one explicitly in the spec.

**Acceptance.** knowledge-curator + spec-extract have `pre_conditions:`; `skill-lint` PASS;
R-Guard-1's deterministic check now covers the destructive reset. Add/extend tests under
`.amap/tools/skill-lint/tests/` if you change the schema.

**Effort:** ~1 spec + small impl. Mechanical-ish once the design question is settled.

---

## #5 — R-DNA-7 teaching-moment has no hook  (needs brainstorm)

**Problem.** `R-DNA-7` ([.amap/rules/rules-guard.md](../../../.amap/rules/rules-guard.md))
requires capturing a "teaching moment" (user corrects the agent's code and explains a
principle) **in-session**, splitting it across author-dna / conventions / knowledge-snapshot.
But this only lives in the rule text + the author-dna-builder skill. The **apply phase**
(`task.md` Pha 3) and **knowledge-curator** post-task have **no step** that prompts capture.
So it depends entirely on the agent remembering R-DNA-7 → it will be missed.

Verify: `/usr/bin/grep -rln "teaching moment\|R-DNA-7" .amap/skills .amap/workflows .amap/procedures`
(today: only `author-dna-builder/SKILL.md`).

**Why brainstorm, not just code.** A teaching moment is detected behaviorally (user says
"không được…", "phải dùng…", "sai rồi…", or edits agent code with a rationale). You can't
make that a deterministic file-evidence gate the way #1–#3 were. Options to weigh:
- A post-task **prompt step** in knowledge-curator / `task.md` Pha 3 ("did a teaching moment
  occur this session? if so capture before archive") — cheap, but still agent-trust.
- A lightweight **checkpoint artifact** (e.g. `TEACHING_LOG.md`) the agent must touch, gated
  by a `gate-check` validator before archive — more deterministic, more ceremony.
- Detection heuristics on the conversation (out of scope for a file hook).
Lead with a recommendation; this is genuinely a design tradeoff (determinism vs. ceremony
vs. false-positives).

**Acceptance.** Define in the spec. At minimum: an explicit capture step wired into the
post-apply / archive path so the obligation has an operational trigger, not just rule prose.

**Effort:** brainstorm first → spec → small impl.

---

## #6 — `db-remote` hard-coded + orphan `document-writer`

**6a — DB tool not routed through the capability/adapter layer.**
KG tools are templated via the render context (`{{ tools.* }}`) so they resolve per-platform
at `amap init` (see `R-Adapter-1` in [.amap/rules/rules-tool.md](../../../.amap/rules/rules-tool.md)
§R-Tool-7, and usages in `task.md`). But the DB tool is hard-coded as the literal `db-remote`:
- [.amap/skills/db-explorer/SKILL.md](../../../.amap/skills/db-explorer/SKILL.md) (e.g. lines ~5, ~72, ~80, ~149, ~311)
- [.amap/skills/codebase-explorer/SKILL.md](../../../.amap/skills/codebase-explorer/SKILL.md) (~226, ~232)
Verify: `/usr/bin/grep -rn "db-remote" .amap/skills`.

Proposed: introduce a `{{ tools.db_query }}` (name TBD) abstract-op in the render context,
populated like the KG tools per platform/MCP, and replace the literal `db-remote` references.
Check how `{{ tools.* }}` is built (`cli/scaffold.py` + `cli/platforms/*.py` `tool_mapping`)
and whether a DB capability already exists in the manifest `provides`. **Note overlap with
roadmap P2.1/UP2** (capability-based portability) — coordinate so this isn't done twice; it
may be cleanest as the first concrete slice of P2.1. Keep AMAP generic: no project-specific
DB names hard-coded (see memory: "AMAP framework generic boundary").

**6b — orphan skill `document-writer`.**
`document-writer` lints PASS but **no workflow references it**. Verify:
`/usr/bin/grep -rn "document-writer" .amap/workflows` (expect nothing).
Decide: either give it an entry point (a `/document` workflow or a step in an existing flow),
or mark it explicitly as manual-invoke-only in its SKILL.md so the orphan status is intentional.
Small decision — fold into the #6 spec.

**Acceptance.** No literal `db-remote` in skills (all via the adapter layer); snapshot/lint
tests pass; document-writer either wired or documented as manual-only.

**Effort:** 6a small-medium (touches scaffold render context — read P2.1 notes in TODOS.md
first); 6b tiny.

---

## Suggested order

1. **#4** — most self-contained, highest safety value (guards a destructive reset).
2. **#6** — mechanical-ish; coordinate 6a with roadmap P2.1 so portability isn't done twice.
3. **#5** — last; needs a brainstorm before any code.

Each should land as its own spec → plan → PR (mirror the C-22b / C-23 cadence). Update the
"Enforcement hardening" section in `TODOS.md` as you complete each.
