# Rename `amap` → `Maika` (hard cut)

**Date:** 2026-06-21
**Status:** Approved (design), pending implementation plan
**Branch:** `rename/amap-to-maika`

## Why

The project outgrew its name. "AMAP — Agent **Memory** Architecture Protocol"
foregrounds memory, but the scope now spans memory + phase-gated workflow +
rules/guardrails + multi-platform runtime + MCP integration + dashboard control
tower + knowledge lifecycle + worker-fleet orchestration. Repositioned core
identity: **the working OS for AI coding agents.**

## Decisions (locked)

- **New name:** `Maika` — a proper-noun brand, **no acronym**, no backronym.
- **Tagline:** "Maika — hệ điều hành làm việc cho AI coding agent."
- **Hard cut:** erase every `amap` reference. No alias, no compat shim, no
  auto-migration command, **no "formerly AMAP" historical note.**
- **GitHub repo:** rename `Agent-Memory-Architecture-Protocol` → `Maika`
  (GitHub auto-redirects old URLs); update clone URL in docs.
- Drop the "Agent Memory Architecture Protocol" expansion entirely.

## Scope / blast radius

Measured on `main` (tracked files only):

- ~**2305** occurrences of `amap` (case-insensitive) across **136** files.
- `.amap` path references: **1309**.
- `cli.amap` module refs: **38**; `cli/amap` path refs: **27**.

What changes:

1. **Branding / docs** — README (title, prose, tagline, badges), `docs/**`,
   `.amap/DEVELOPMENT_RULES.md`, `docs/examples/**`, any banner asset text.
2. **Code / package** (`pyproject.toml`) — package `amap-cli` → `maika-cli`;
   `description`; console script `amap = "cli.amap:main"` →
   `maika = "cli.maika:main"`. `git mv cli/amap.py cli/maika.py`; update all
   `cli.amap` imports/`-m cli.amap` invocations → `cli.maika`.
3. **Framework root convention** `.amap/` → `.maika/` — the **Generic** platform
   root. Set `framework_root = ".maika"` in `cli/platforms/` (generic platform);
   `git mv .amap .maika`; update all `.amap/` path strings in code, docs,
   templates, hooks.
4. **Tests / hooks / templates** — references in `cli/tests/**`,
   `.amap/hooks/**`, `.amap/knowledge/templates/**`.
5. **This repo's own dogfood** — `CLAUDE.md` (project) references to `.amap/`,
   `cli/`, skill-lint path.
6. **GitHub** — repo rename + README clone URL.

## Replacement rules (case-aware)

Apply in this order, case-aware to avoid breaking identifiers:

- `AMAP` and `Amap` → `Maika`
- `amap` → `maika`
- `.amap` → `.maika`

Guard: confirm `amap` is not a substring of unrelated words (grep shows the
token is project-specific; risk low, but verify in diff). Prose that *describes*
the old acronym (e.g., "Agent Memory Architecture Protocol") must be **rewritten**
to the new positioning, not blind-replaced.

## Execution strategy (dogfood the worker fleet)

- Work on branch `rename/amap-to-maika`.
- **Delegate the heavy mechanical pass to `agy`** (worker, currently READY) with
  a precise task spec + RETURN CONTRACT: agy performs the `git mv`s and the
  case-aware replacements across the tree, then reports SUMMARY/FILES/VERIFY/OPEN.
- **Claude (orchestrator) owns:** the judgment cases (prose rewrites where blind
  replace is wrong), full-diff review, and verification. No compat code is added
  (hard cut).
- Pre-flight `worker-health agy` before delegating; honor circuit breaker.

## Verification / success criteria

- `git grep -i amap` → **0 matches** (zero — hard cut, no exceptions).
- `git ls-files | grep -i amap` → **0** (no amap-named paths; `.maika/` and
  `cli/maika.py` exist).
- `/usr/bin/python3 -m pytest cli/tests` → pass.
- skill-lint passes at the moved path:
  `/usr/bin/python3 .maika/tools/skill-lint/validate_skills.py`.
- `/usr/bin/python3 -m cli.maika status` works; console script `maika` resolves.
- README + any banner show **Maika**; no "AMAP" anywhere.

## Risks / mitigations

- **Case errors / broken identifiers** → case-aware mapping + full-diff review +
  pytest gate.
- **Moved skill-lint path** (`.amap/tools` → `.maika/tools`) → update any
  CI/docs/CLAUDE.md that reference the old path.
- **PR #22 (README banner) is open and unmerged.** It adds an AMAP-text banner +
  README polish on `docs/readme-banner-visual-polish`. This rename is off `main`
  and will conflict on README. **Mitigation / recommendation:** merge PR #22
  first, then rebase this rename on updated `main` so the banner gets renamed in
  the same pass (single source of truth). Alternative: close #22 and fold the
  banner (already renamed) into this branch.
- **GitHub repo rename is external** → performed by the user or via `gh`;
  requires updating the local remote URL and README clone link afterward.

## Out of scope

- No new features; pure rename + repositioning.
- No backward compatibility of any kind.
- Logo/visual redesign beyond swapping the wordmark text AMAP→Maika.
