# AMAP Runtime Style Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean up rationale-heavy and retrospective wording in cloneable `.amap/` runtime files without changing runtime behavior.

**Architecture:** This is a search-driven documentation edit pass. The implementation classifies matching phrases, edits only small local passages, explicitly excludes OpenSpec skills and workflows, then verifies with scans, skill lint, and scaffold/render tests.

**Tech Stack:** Markdown runtime instructions, Python skill lint, pytest CLI tests, ripgrep.

---

## File Structure

Modify:

- `.amap/rules/rules-flow.md` — trim rationale in flow rules while keeping gates and abort conditions.
- `.amap/rules/rules-exec.md` — trim budget/query rationale while keeping log markers and limits.
- `.amap/rules/rules-guard.md` — remove external citations and incident history while keeping guard actions.
- `.amap/rules/rules-knowledge.md` — trim stale-convention rationale while keeping rescan requirements.
- `.amap/rules/rules-tool.md` — trim executor/memory rationale while keeping permission rules.
- `.amap/procedures/bootstrap.md` — remove historical KI rationale and keep operational scan/report actions.
- `.amap/procedures/context-loader.md` — remove historical/diet prose and keep JIT loading rules.
- `.amap/procedures/context-compressor.md` — edit only if retrospective rationale appears in scan.
- `.amap/workflows/task.md` — trim context-dilution rationale while keeping handoff/reload behavior.
- Non-OpenSpec `.amap/skills/*/SKILL.md` and their references/assets — edit only rationale-heavy scan hits.

Do not modify:

- `.amap/skills/openspec-explore/`
- `.amap/skills/openspec-propose/`
- `.amap/skills/openspec-archive-change/`
- `.amap/workflows/opsx-explore.md`
- `.amap/workflows/opsx-propose.md`
- `.amap/workflows/opsx-apply.md`
- `.amap/workflows/opsx-archive.md`

### Task 1: Baseline Scan And Scope Guard

**Files:**
- Read: `.amap/rules/*.md`
- Read: `.amap/procedures/*.md`
- Read: `.amap/workflows/*.md`
- Read: `.amap/skills/*/SKILL.md`

- [x] **Step 1: Generate actionable scan output**

Run:

```bash
rg -n "Incident|incident|trước đây|đã quan sát|sự cố|học được|previous|observed before|learned|Lý do|rationale|false sense|Arthur|Diet" \
  .amap/rules .amap/procedures .amap/workflows .amap/skills \
  -g '!.amap/skills/openspec-explore/**' \
  -g '!.amap/skills/openspec-propose/**' \
  -g '!.amap/skills/openspec-archive-change/**' \
  -g '!.amap/workflows/opsx-*.md'
```

Expected: List of candidates, including operational placeholders that should be kept.

- [x] **Step 2: Confirm OpenSpec exclusions are clean**

Run:

```bash
git diff -- .amap/skills/openspec-explore .amap/skills/openspec-propose .amap/skills/openspec-archive-change .amap/workflows/opsx-explore.md .amap/workflows/opsx-propose.md .amap/workflows/opsx-apply.md .amap/workflows/opsx-archive.md
```

Expected: no output.

### Task 2: Edit Core Rules And Procedures

**Files:**
- Modify: `.amap/rules/rules-flow.md`
- Modify: `.amap/rules/rules-exec.md`
- Modify: `.amap/rules/rules-guard.md`
- Modify: `.amap/rules/rules-knowledge.md`
- Modify: `.amap/rules/rules-tool.md`
- Modify: `.amap/procedures/bootstrap.md`
- Modify: `.amap/procedures/context-loader.md`

- [x] **Step 1: Rewrite only rationale-heavy local passages**

Apply these transformations:

- Remove incident/date/source history from shared rules.
- Replace long "Lý do" paragraphs with concise operational constraints, or delete them when the action already stands alone.
- Keep all rule IDs, severity labels, commands, file paths, markers, and abort/warn/confirm semantics unchanged.

- [x] **Step 2: Review diff for semantics**

Run:

```bash
git diff -- .amap/rules .amap/procedures
```

Expected: wording-only diffs; no deleted rule IDs, commands, markers, or paths.

### Task 3: Edit Non-OpenSpec Workflows And Skills

**Files:**
- Modify: `.amap/workflows/task.md`
- Modify as needed: non-OpenSpec `.amap/skills/*/SKILL.md`
- Modify as needed: non-OpenSpec `.amap/skills/*/references/*.md`
- Modify as needed: non-OpenSpec `.amap/skills/*/assets/*.md`

- [x] **Step 1: Rewrite only scan hits that are runtime rationale**

Keep reason placeholders, ADR/TDD template fields, confidence reasons, and user-facing "lý do" fields when they are artifact content rather than framework rationale.

- [x] **Step 2: Confirm OpenSpec exclusions again**

Run:

```bash
git diff -- .amap/skills/openspec-explore .amap/skills/openspec-propose .amap/skills/openspec-archive-change .amap/workflows/opsx-explore.md .amap/workflows/opsx-propose.md .amap/workflows/opsx-apply.md .amap/workflows/opsx-archive.md
```

Expected: no output.

### Task 4: Verification

**Files:**
- Verify: `.amap/`
- Verify: `cli/tests/`

- [x] **Step 1: Run banned historical framing scan**

Run:

```bash
rg -n "Incident|incident|trước đây|đã quan sát|sự cố|học được|previous|observed before|learned" \
  .amap \
  -g '!.amap/skills/openspec-explore/**' \
  -g '!.amap/skills/openspec-propose/**' \
  -g '!.amap/skills/openspec-archive-change/**' \
  -g '!.amap/workflows/opsx-*.md'
```

Expected: no output, except user-facing examples in templates/references if they are intentionally generic and not framework retrospective.

- [x] **Step 2: Run skill lint**

Run:

```bash
python3 .amap/tools/skill-lint/validate_skills.py
```

Expected: pass.

- [x] **Step 3: Run focused CLI tests**

Run:

```bash
python3 -m pytest cli/tests/test_render.py cli/tests/test_scaffold.py cli/tests/test_snapshots.py
```

Expected: pass, or snapshot-only diffs explained if expected.

- [x] **Step 4: Review final diff**

Run:

```bash
git diff --stat
git diff -- .amap docs/superpowers/plans/2026-06-19-amap-runtime-style-pass.md
```

Expected: wording-only `.amap` changes, plan file added, no OpenSpec changes.

### Task 5: Commit

**Files:**
- Commit: `.amap/`
- Commit: `docs/superpowers/plans/2026-06-19-amap-runtime-style-pass.md`

- [x] **Step 1: Commit style pass**

Run:

```bash
git add .amap docs/superpowers/plans/2026-06-19-amap-runtime-style-pass.md
git commit -m "docs: streamline amap runtime instructions"
```

Expected: commit succeeds.
