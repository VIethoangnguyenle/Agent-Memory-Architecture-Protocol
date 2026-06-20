# DB-query templating + orphan document-writer (C-26) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the hard-coded `db-remote` MCP name from skill source by adding a `db_query` abstract-op (mapped per-platform, default `db-remote`) and templatizing the skills; document `document-writer` as intentionally manual-only.

**Architecture:** `db_query` joins the platform tool contract (`REQUIRED_TOOL_KEYS`) and every platform's `tool_mapping` maps it to the `db_access` MCP reference `"db-remote"` (server-level, matching how db-explorer uses it). The two skills reference `{{ tools.db_query }}` instead of the literal. No capability-resolution rework (P2.1 deferred).

**Tech Stack:** Python 3.9+ stdlib, pytest (`/usr/bin/python3 -m pytest`), Jinja2 scaffold render context.

**Spec:** `docs/superpowers/specs/2026-06-21-db-query-templating-design.md`

**Branch:** `db-query-templating` (off `main`; spec already committed on this branch).

---

## File Structure

- **`cli/platforms/base.py`** (modify) — add `"db_query"` to `REQUIRED_TOOL_KEYS`.
- **`cli/platforms/{claude_code,codex,cursor,generic,antigravity}.py`** (modify) — add `"db_query": "db-remote"` to each `tool_mapping`.
- **`cli/tests/test_platforms.py`** (modify) — assert every platform maps `db_query`.
- **`.amap/skills/db-explorer/SKILL.md`** (modify) — replace `db-remote` literals (frontmatter description, `pre_conditions`, body) with `{{ tools.db_query }}`.
- **`.amap/skills/codebase-explorer/SKILL.md`** (modify) — replace `db-remote` body literals with `{{ tools.db_query }}`.
- **`.amap/skills/skill-index.yaml`** (regenerated) — via `generate_index.py`.
- **`.amap/skills/document-writer/SKILL.md`** (modify) — manual-only note (#6b).
- **`cli/tests/snapshots/*`** (maybe) — refresh only if a rendered `db_query` value lands in a snapshot.

---

### Task 1: Add `db_query` to the tool contract + all platform mappings

**Files:**
- Modify: `cli/platforms/base.py`, `cli/platforms/claude_code.py`, `cli/platforms/codex.py`, `cli/platforms/cursor.py`, `cli/platforms/generic.py`, `cli/platforms/antigravity.py`
- Test: `cli/tests/test_platforms.py`

- [ ] **Step 1: Write the failing test**

Append to `cli/tests/test_platforms.py` (it already imports `PLATFORMS`, `get_platform`, and `REQUIRED_TOOL_KEYS`):

```python
def test_all_platforms_map_db_query():
    for key, cls in PLATFORMS.items():
        assert "db_query" in cls().tool_mapping, f"{key} missing db_query mapping"


def test_db_query_resolves_in_render_context():
    ctx = get_platform("claude-code").build_render_context(["db-remote"], "python")
    assert ctx["tools"]["db_query"] == "db-remote"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest cli/tests/test_platforms.py -k "db_query" -v`
Expected: FAIL — no platform maps `db_query` yet (KeyError/assert).

- [ ] **Step 3: Add `db_query` to the required keyset**

In `cli/platforms/base.py`, add `"db_query",` to the `REQUIRED_TOOL_KEYS` frozenset (e.g. right after `"get_space_pages",` in the document group, or anywhere in the set):

```python
    "get_space_pages",
    "db_query",
    "search_web",
```

- [ ] **Step 4: Map `db_query` in every platform's tool_mapping**

In EACH of `cli/platforms/claude_code.py`, `codex.py`, `cursor.py`, `generic.py`, `antigravity.py`, add this entry to the `tool_mapping` dict (place it near the code-exploration / document group). Use the **same value `"db-remote"` for all platforms** — it is a server-level reference to the `db_access` MCP (db-explorer uses the MCP, not a specific tool name), so it is intentionally NOT `mcp__…`-prefixed:

```python
        # ── Database (db_access MCP — server-level reference) ──
        "db_query":          "db-remote",
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `/usr/bin/python3 -m pytest cli/tests/test_platforms.py -v`
Expected: all PASS — the two new `db_query` tests AND the pre-existing `test_all_platforms_define_required_tool_keyset` (which now requires `db_query` and finds it in every platform).

- [ ] **Step 6: Commit**

```bash
git add cli/platforms/base.py cli/platforms/claude_code.py cli/platforms/codex.py cli/platforms/cursor.py cli/platforms/generic.py cli/platforms/antigravity.py cli/tests/test_platforms.py
git commit -m "feat(platforms): add db_query abstract-op mapped to db_access MCP"
```

---

### Task 2: Templatize `db-remote` in the skills + regenerate index

**Files:**
- Modify: `.amap/skills/db-explorer/SKILL.md`, `.amap/skills/codebase-explorer/SKILL.md`
- Regenerate: `.amap/skills/skill-index.yaml`

> Skill bodies are rendered through Jinja at `amap init` (same as `{{ platform.framework_root }}`), so `{{ tools.db_query }}` resolves there. skill-lint runs on the unrendered source; a `{{ … }}` string value is valid.

- [ ] **Step 1: Find every `db-remote` literal in the two skills**

Run: `/usr/bin/grep -n "db-remote" .amap/skills/db-explorer/SKILL.md .amap/skills/codebase-explorer/SKILL.md`
Note each occurrence: db-explorer has it in the frontmatter `description`, in `pre_conditions` (`- tool: db-remote`), and in several body lines; codebase-explorer has it in body lines.

- [ ] **Step 2: Replace all literals with the template var**

In both files, replace every literal `db-remote` with `{{ tools.db_query }}`. Two forms:
- Prose / description / body: `MCP db-remote` → `MCP {{ tools.db_query }}`.
- `pre_conditions` entry in db-explorer:
  ```yaml
    - tool: db-remote
  ```
  becomes:
  ```yaml
    - tool: "{{ tools.db_query }}"
  ```
  (quote it — a bare `{{ … }}` is not valid YAML.)

Do not change surrounding wording, only the token.

- [ ] **Step 3: Regenerate the skill index**

Run: `/usr/bin/python3 .amap/tools/skill-index/generate_index.py`
(The header of `skill-index.yaml` says it is auto-generated — do not hand-edit it.)

- [ ] **Step 4: Verify no literal remains + lint passes**

Run:
```bash
/usr/bin/grep -c "db-remote" .amap/skills/db-explorer/SKILL.md .amap/skills/codebase-explorer/SKILL.md
/usr/bin/grep -n "tools.db_query" .amap/skills/db-explorer/SKILL.md | head
/usr/bin/grep -c "db-remote" .amap/skills/skill-index.yaml
/usr/bin/python3 .amap/tools/skill-lint/validate_skills.py | tail -1
```
Expected: `db-remote` count is `0` in both skill bodies and in `skill-index.yaml`; `{{ tools.db_query }}` present; skill-lint `14/14 skills PASS`.

- [ ] **Step 5: Commit**

```bash
git add .amap/skills/db-explorer/SKILL.md .amap/skills/codebase-explorer/SKILL.md .amap/skills/skill-index.yaml
git commit -m "refactor(skills): reference db_access MCP via {{ tools.db_query }} not literal"
```

---

### Task 3: Mark document-writer manual-only (#6b)

**Files:**
- Modify: `.amap/skills/document-writer/SKILL.md`

> Prose-only. Resolves the "orphan skill" observation by documenting it as intentional.

- [ ] **Step 1: Add the manual-only note**

In `.amap/skills/document-writer/SKILL.md`, in the `## Khi nào sử dụng` section, add a note line:

```
> **Manual-only:** skill này được gọi trực tiếp (manual) — không `/task` workflow nào auto-route tới nó. Orphan status là có chủ đích, không phải thiếu sót.
```

- [ ] **Step 2: Verify lint still passes**

Run: `/usr/bin/python3 .amap/tools/skill-lint/validate_skills.py | tail -1`
Expected: `14/14 skills PASS`.

- [ ] **Step 3: Commit**

```bash
git add .amap/skills/document-writer/SKILL.md
git commit -m "docs(document-writer): document intentional manual-only (no workflow entry)"
```

---

### Task 4: Full verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full affected suite**

Run: `/usr/bin/python3 -m pytest cli/tests .amap/tools .amap/hooks -q`
Expected: all PASS.

- [ ] **Step 2: Snapshot check (refresh only if needed)**

Run: `/usr/bin/python3 -m pytest cli/tests/test_snapshots.py -q`
Expected: PASS. If it fails because a rendered `db_query` value now appears in a captured scaffold output, refresh snapshots with the project-local method:

```bash
/usr/bin/python3 - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from cli.commands.init import run_init
from cli.tests.test_snapshots import PLATFORM_OPTIONS, _snapshot_tree

root = Path.cwd()
snap_dir = root / "cli" / "tests" / "snapshots"
for platform_key in sorted(PLATFORM_OPTIONS):
    with TemporaryDirectory() as td:
        target = Path(td) / "proj"
        options = PLATFORM_OPTIONS[platform_key]
        run_init(target_dir=str(target), amap_root=str(root), platform_key=platform_key,
                 selected_mcps=options["mcps"], language=options["language"], assume_yes=True)
        (snap_dir / f"{platform_key}.txt").write_text(_snapshot_tree(target), encoding="utf-8")
PY
```
(Snapshots capture the file TREE, so a tool-value change usually does NOT affect them — expect no refresh needed.)

- [ ] **Step 3: Render smoke — db_query resolves, no literal in rendered skill**

```bash
/usr/bin/python3 -c "from cli.platforms import get_platform; print(get_platform('claude-code').build_render_context(['db-remote'],'python')['tools']['db_query'])"
```
Expected: `db-remote`.

- [ ] **Step 4: Commit any snapshot refresh (only if Step 2 required it)**

```bash
git status
# commit only if snapshots were intentionally refreshed
git add cli/tests/snapshots/ && git commit -m "test(snapshots): refresh for db_query render value"
```

---

## Self-Review

**Spec coverage:**
- §3.1 add `db_query` to REQUIRED_TOOL_KEYS → Task 1 Step 3.
- §3.2 per-platform mapping (default `db-remote`, server-level) → Task 1 Step 4 (all 5 platforms).
- §3.3 templatize db-explorer (description + pre_conditions + body) + codebase-explorer (body) → Task 2 Step 2.
- §3.4 regenerate skill-index → Task 2 Step 3.
- §4 document-writer manual-only (#6b) → Task 3.
- §6 acceptance: validate_tool_mapping passes (existing keyset test, Task 1 Step 5); render resolves (Task 1 Step 1 + Task 4 Step 3); no literal `db-remote` in the two skills + index (Task 2 Step 4); skill-lint 14/14 (Tasks 2-3); exit condition (rendered skill has resolved ref) → Task 4 Step 3.
- §7 non-goals: no P2.1 rework, single `db_query` op only, no workflow for document-writer — nothing in the plan violates these.

**Placeholder scan:** No TBD/TODO. Snapshot refresh in Task 4 is conditional with an explicit "only if" guard.

**Type/name consistency:** abstract-op key is `db_query` everywhere (REQUIRED_TOOL_KEYS, all tool_mappings, tests, skill template var `{{ tools.db_query }}`). Value `"db-remote"` consistent across platforms. `PLATFORMS`/`get_platform`/`REQUIRED_TOOL_KEYS` match the existing `test_platforms.py` imports.
