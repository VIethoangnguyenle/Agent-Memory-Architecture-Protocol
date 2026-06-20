# DB-query templating + orphan document-writer (C-26) — Design

> **Date:** 2026-06-21
> **Status:** Approved (design) — ready for implementation plan
> **Branch:** `db-query-templating` (off `main`).
> **Lineage:** enforcement audit 2026-06-20 item **#6** (#6a db-remote templating, #6b orphan
> document-writer). **Minimal scope** — full capability-resolution (roadmap P2.1/UP2) is
> explicitly deferred (see §2).

---

## 1. Context & problem

- **#6a:** `db-explorer` and `codebase-explorer` hard-code the MCP server name `db-remote`
  in skill source, while KG and doc tools are templated `{{ tools.* }}` (resolved at
  `amap init`). The tool contract ([cli/platforms/base.py](../../../cli/platforms/base.py)
  `REQUIRED_TOOL_KEYS`) has **no DB abstract-op at all** — that is why db-explorer falls back
  to a literal. Hard-coding a project-ish MCP name in framework skill source violates the
  "framework-generic-boundary" principle.
- **#6b:** `document-writer` is a defined skill that lints PASS but **no workflow references
  it** — its "orphan" status is undocumented (bug or intentional?).

Note (manifest already models DB as a capability): `plugin-manifest.yaml` declares
`db-remote: { provides: db_access }`. So a `db_access` capability exists; it is used today
only for plugin gating (`requires_capability`), not for tool resolution.

## 2. Scope decision — minimal, defer P2.1

`tool_mapping` currently maps each abstract-op to **one hard-coded MCP** (`search_code →
mcp__socraticode__…`, `search_docs → mcp__confluence__…`). Making resolution
capability-driven (abstract-op → capability → *selected* MCP) is roadmap **P2.1/UP2**, which
TODOS gates on **P1.1** ("validate trước khi đổ công vào portability" — P1.1 not done).

This spec does **not** do that rework. It adds `db_query` as a first-class abstract-op
mapped the same hard-coded way as `search_code`/`search_docs`, so the **skill source becomes
generic** (no project MCP name) while the default MCP reference lives in the adapter — exactly
the existing pattern. P2.1 will later change *how all abstract-ops resolve*, `db_query`
included, for free.

**Honest boundary:** after this, `db_query` is still tied to one MCP (`db-remote`) just like
`search_code` is tied to socraticode. The win is skill-level genericity, not full
cross-MCP portability. Full portability = P2.1 (deferred).

## 3. Mechanism — #6a

`db-explorer` references `db-remote` at the **server level** ("dùng MCP db-remote để
SELECT/find"), not via specific tool names. So `db_query` is a **reference to the db_access
MCP** (default `db-remote`), not an invented tool-name.

1. **Tool contract:** add `db_query` to `REQUIRED_TOOL_KEYS` in
   [cli/platforms/base.py](../../../cli/platforms/base.py) — so `{{ tools.db_query }}` always
   renders (runtime degrades if the MCP is absent, per R-Tool-5; same as KG/docs tools).
2. **Per-platform mapping:** add `db_query` to every platform's `tool_mapping`
   (`claude_code`, `codex`, `antigravity`, and any others), valued as the `db_access` MCP
   (`db-remote`) reference. Exact string confirmed in planning (it reads in prose as the MCP
   name, e.g. `db-remote`; per-platform mcp prefix applied only if the skill text needs a
   tool-call form).
3. **Skills:** replace literal `db-remote` with `{{ tools.db_query }}` in:
   - [db-explorer/SKILL.md](../../../.amap/skills/db-explorer/SKILL.md) — body references AND
     the `pre_conditions` entry `- tool: db-remote` → `tool: "{{ tools.db_query }}"`.
   - [codebase-explorer/SKILL.md](../../../.amap/skills/codebase-explorer/SKILL.md) — body references.
4. **Regenerate** `skills/skill-index.yaml` (auto-generated; the db-remote ref there comes
   from db-explorer's `pre_conditions`) via `generate_index.py`.

## 4. Mechanism — #6b (orphan document-writer)

`document-writer` has no workflow entry point. Decision: **mark it manual-only** (intentional),
not wire a workflow. Add a short note in
[document-writer/SKILL.md](../../../.amap/skills/document-writer/SKILL.md) "Khi nào sử dụng"
stating it is invoked directly by the user/agent (no `/task` workflow auto-routes to it), so
its orphan status is documented as intentional rather than a gap. No code change.

## 5. Files

- `cli/platforms/base.py` — add `db_query` to `REQUIRED_TOOL_KEYS`.
- `cli/platforms/*.py` — add `db_query` to each `tool_mapping`.
- `.amap/skills/db-explorer/SKILL.md` — literal `db-remote` → `{{ tools.db_query }}` (body + pre_conditions).
- `.amap/skills/codebase-explorer/SKILL.md` — literal `db-remote` → `{{ tools.db_query }}`.
- `.amap/skills/skill-index.yaml` — regenerated.
- `.amap/skills/document-writer/SKILL.md` — manual-only note (#6b).
- `cli/tests/*` — tool-mapping validation + snapshot updates as needed.

## 6. Test plan / acceptance

- **Platform contract:** each platform's `validate_tool_mapping()` PASSES with the new
  required `db_query` key (add/extend a platforms test asserting `db_query` present in every
  platform's `tool_mapping`).
- **Render:** `build_render_context(...)["tools"]["db_query"]` resolves to a non-empty value
  per platform.
- **Skills:** no literal `db-remote` remains in `db-explorer`/`codebase-explorer`
  (`grep -c "db-remote"` → 0 in those two skill bodies); `{{ tools.db_query }}` present.
  skill-lint 14/14 PASS; skill-index regenerated (no stale `db-remote`).
- **Snapshots:** `cli/tests/snapshots` refresh only if the rendered tool value appears in
  captured output.
- **#6b:** document-writer SKILL.md states manual-only; skill-lint still PASS.
- **Exit condition:** a rendered db-explorer (post-`amap init`) contains the resolved DB MCP
  reference, not a hard-coded literal in the skill source.

## 7. Non-goals / residual

- **No P2.1 capability-resolution rework** (abstract-op → capability → selected MCP). Deferred
  until after P1.1; recorded as a follow-up in TODOS. `db_query` (and `search_code`,
  `search_docs`) remain tied to one default MCP until then.
- No new DB abstract-ops beyond a single `db_query` reference (YAGNI — db-explorer uses
  db-remote at server level; one reference suffices). Add more only if a platform's DB MCP
  genuinely needs tool-level granularity.
- No workflow entry point for document-writer (intentional manual-only).
