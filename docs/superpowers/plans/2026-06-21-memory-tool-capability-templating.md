# Memory Tool Capability Templating (C-27) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** De-hardcode agentmemory's concrete tool names behind a `{{ tools.dynamic_memory_* }}` abstraction layer (mirroring the `db_query`/C-26 precedent), and document the agentmemory-stays-out-of-AMAP boundary as an MCP-only setup recipe.

**Architecture:** Add 7 abstract memory operations to `REQUIRED_TOOL_KEYS` in the platform base, map each to the provider's concrete tool name per platform (respecting each platform's MCP prefix), then replace every literal memory tool name in operational templates (`rules/`, `skills/`, `procedures/`) with the abstract op. A repo-level regression test prevents re-hardcoding. Runtime authority/degrade semantics (spec 2026-06-19) are untouched — this is a representation-layer change only.

**Tech Stack:** Python 3.12, pytest, Jinja2 (`StrictUndefined`), Markdown templates under `.amap/`.

**Spec:** [docs/superpowers/specs/2026-06-21-memory-tool-capability-templating-design.md](../specs/2026-06-21-memory-tool-capability-templating-design.md)

**Conventions for this plan:**
- Run pytest with the system interpreter: **`/usr/bin/python3 -m pytest`** (the repo venv has no pytest).
- All paths are relative to repo root `/home/zane/Desktop/agent-memory-arch-v3`.
- Already on branch `memory-tool-capability-templating`.

---

## File Structure

**Code (CLI):**
- Modify `cli/platforms/base.py` — add 7 `dynamic_memory_*` keys to `REQUIRED_TOOL_KEYS`.
- Modify `cli/platforms/claude_code.py`, `antigravity.py`, `codex.py`, `generic.py`, `cursor.py` — add memory op → concrete tool mappings.
- Modify `cli/tests/test_platforms.py` — add mapping + resolution tests (mirror `db_query` tests).
- Create `cli/tests/test_no_hardcoded_memory_tools.py` — repo-level regression guard.

**Operational templates (the de-hardcode):**
- Modify `.amap/rules/rules-tool.md` (R-Tool-6 permission table, contexts, write-path guard, degrade branch).
- Modify `.amap/rules/rules-exec.md` (memory budget bullets).
- Modify `.amap/skills/knowledge-curator/references/m7-memory-push.md` (Tầng 0/2/3 + save call + remove "native" header).
- Modify `.amap/skills/knowledge-curator/SKILL.md` (M7 summary line).
- Modify `.amap/procedures/bootstrap.md` (memory_health probe).

**Documentation:**
- Create `.amap/profiles/agent-memory-mcp-only-setup.md` — MCP-only setup recipe (framework-internal; not scaffolded).
- Modify `TODOS.md` — mark C-27 done.

**The 7 abstract ops → concrete tool (canonical table):**

| Abstract op | Provider tool | Permission (R-Tool-6) |
|---|---|---|
| `dynamic_memory_search` | `memory_smart_search` | read — counts toward budget |
| `dynamic_memory_recall` | `memory_recall` | read — counts toward budget |
| `dynamic_memory_sessions` | `memory_sessions` | diagnostic — budget-exempt |
| `dynamic_memory_audit` | `memory_audit` | diagnostic — budget-exempt |
| `dynamic_memory_health` | `memory_health` | infra probe — budget-exempt |
| `dynamic_memory_save` | `memory_save` | write — M7 only, 1/Phase 3 |
| `dynamic_memory_forget` | `memory_governance_delete` | admin-only — agent never calls |

**Per-platform concrete form** (prefix only; tool name unchanged):
- claude-code (`mcp__`): `mcp__agent-memory__memory_smart_search`
- antigravity (`mcp_`): `mcp_agent-memory_memory_smart_search`
- codex / generic / cursor (bare): `memory_smart_search`

---

## Task 1: Add abstract memory ops to the platform tool layer

**Files:**
- Modify: `cli/platforms/base.py` (`REQUIRED_TOOL_KEYS`, currently ends at the `read_url` entry ~line 35)
- Modify: `cli/platforms/claude_code.py`, `cli/platforms/antigravity.py`, `cli/platforms/codex.py`, `cli/platforms/generic.py`, `cli/platforms/cursor.py`
- Test: `cli/tests/test_platforms.py`

- [ ] **Step 1: Write the failing tests**

Append to `cli/tests/test_platforms.py`:

```python
DYNAMIC_MEMORY_OPS = {
    "dynamic_memory_search",
    "dynamic_memory_recall",
    "dynamic_memory_sessions",
    "dynamic_memory_audit",
    "dynamic_memory_health",
    "dynamic_memory_save",
    "dynamic_memory_forget",
}


def test_all_platforms_map_dynamic_memory_ops():
    for key, cls in PLATFORMS.items():
        mapping = cls().tool_mapping
        for op in DYNAMIC_MEMORY_OPS:
            assert op in mapping, f"{key} missing {op} mapping"


def test_dynamic_memory_ops_are_required_keys():
    assert DYNAMIC_MEMORY_OPS <= REQUIRED_TOOL_KEYS


def test_dynamic_memory_resolves_in_render_context_claude():
    ctx = get_platform("claude-code").build_render_context(["agent-memory"], "python")
    assert ctx["tools"]["dynamic_memory_save"] == "mcp__agent-memory__memory_save"
    assert ctx["tools"]["dynamic_memory_search"] == "mcp__agent-memory__memory_smart_search"
    assert ctx["tools"]["dynamic_memory_forget"] == "mcp__agent-memory__memory_governance_delete"


def test_dynamic_memory_resolves_even_when_agent_memory_not_selected():
    # REQUIRED => the op is always in the `tools` namespace; runtime degrade
    # (R-Tool-6 / M7) handles the provider being absent, NOT template rendering.
    ctx = get_platform("generic").build_render_context([], "other")
    assert ctx["tools"]["dynamic_memory_save"] == "memory_save"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `/usr/bin/python3 -m pytest cli/tests/test_platforms.py -k dynamic_memory -v`
Expected: FAIL — `test_dynamic_memory_ops_are_required_keys` fails (ops not in `REQUIRED_TOOL_KEYS`), and `test_all_platforms_map_dynamic_memory_ops` fails (KeyErrors / missing keys).

- [ ] **Step 3: Add the 7 ops to `REQUIRED_TOOL_KEYS` in `cli/platforms/base.py`**

In the `REQUIRED_TOOL_KEYS = frozenset({ ... })` block, after the `"read_url",` line and before the closing `})`, insert:

```python
    # ── Dynamic (episodic/advisory) memory — provider-mapped, runtime-optional ──
    "dynamic_memory_search",
    "dynamic_memory_recall",
    "dynamic_memory_sessions",
    "dynamic_memory_audit",
    "dynamic_memory_health",
    "dynamic_memory_save",
    "dynamic_memory_forget",
```

- [ ] **Step 4: Map the ops in `cli/platforms/claude_code.py`**

In `tool_mapping`, after the `"read_url":        "WebFetch",` line (before the closing `}`), insert:

```python

        # ── Dynamic Memory (agent-memory MCP — tool-level; optional at runtime) ──
        "dynamic_memory_search":   "mcp__agent-memory__memory_smart_search",
        "dynamic_memory_recall":   "mcp__agent-memory__memory_recall",
        "dynamic_memory_sessions": "mcp__agent-memory__memory_sessions",
        "dynamic_memory_audit":    "mcp__agent-memory__memory_audit",
        "dynamic_memory_health":   "mcp__agent-memory__memory_health",
        "dynamic_memory_save":     "mcp__agent-memory__memory_save",
        "dynamic_memory_forget":   "mcp__agent-memory__memory_governance_delete",
```

- [ ] **Step 5: Map the ops in `cli/platforms/antigravity.py`**

In `tool_mapping`, after `"generate_image":    "generate_image",` (before the closing `}`), insert:

```python

        # ── Dynamic Memory (agent-memory MCP — tool-level; optional at runtime) ──
        "dynamic_memory_search":   "mcp_agent-memory_memory_smart_search",
        "dynamic_memory_recall":   "mcp_agent-memory_memory_recall",
        "dynamic_memory_sessions": "mcp_agent-memory_memory_sessions",
        "dynamic_memory_audit":    "mcp_agent-memory_memory_audit",
        "dynamic_memory_health":   "mcp_agent-memory_memory_health",
        "dynamic_memory_save":     "mcp_agent-memory_memory_save",
        "dynamic_memory_forget":   "mcp_agent-memory_memory_governance_delete",
```

- [ ] **Step 6: Map the ops in `cli/platforms/codex.py`, `generic.py`, and `cursor.py` (bare names)**

In each of the three files' `tool_mapping`, after the `"read_url":` entry (before the closing `}`), insert the SAME bare-name block:

```python

        # ── Dynamic Memory (agent-memory MCP — tool-level; optional at runtime) ──
        "dynamic_memory_search":   "memory_smart_search",
        "dynamic_memory_recall":   "memory_recall",
        "dynamic_memory_sessions": "memory_sessions",
        "dynamic_memory_audit":    "memory_audit",
        "dynamic_memory_health":   "memory_health",
        "dynamic_memory_save":     "memory_save",
        "dynamic_memory_forget":   "memory_governance_delete",
```

> Note: `cursor.py` is not in the selectable `PLATFORMS` registry (dormant), but it already carries `db_query`; map memory there too for consistency. Tests iterate `PLATFORMS` (4 platforms), so cursor is not asserted.

- [ ] **Step 7: Run the platform tests to verify they pass**

Run: `/usr/bin/python3 -m pytest cli/tests/test_platforms.py -v`
Expected: PASS — including `test_all_platforms_define_required_tool_keyset` (all 4 platforms now map every required key) and the 4 new `dynamic_memory` tests.

- [ ] **Step 8: Commit**

```bash
git add cli/platforms/base.py cli/platforms/claude_code.py cli/platforms/antigravity.py cli/platforms/codex.py cli/platforms/generic.py cli/platforms/cursor.py cli/tests/test_platforms.py
git commit -m "feat(platforms): add dynamic_memory_* abstract ops mapped to agent-memory MCP (C-27)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Refactor `rules-tool.md` to use abstract memory ops

**Files:**
- Modify: `.amap/rules/rules-tool.md` (R-Tool-6 section, ~lines 65–113)

- [ ] **Step 1: Replace the permission table tool names**

Edit the table rows (keep backticks and the rest of each row intact):

| Old cell | New cell |
|---|---|
| `` `memory_smart_search` `` | `` `{{ tools.dynamic_memory_search }}` `` |
| `` `memory_recall` `` | `` `{{ tools.dynamic_memory_recall }}` `` |
| `` `memory_sessions` `` | `` `{{ tools.dynamic_memory_sessions }}` `` |
| `` `memory_audit` `` | `` `{{ tools.dynamic_memory_audit }}` `` |
| `` `memory_health` `` | `` `{{ tools.dynamic_memory_health }}` `` |
| `` `memory_save` `` | `` `{{ tools.dynamic_memory_save }}` `` |
| `` `memory_governance_delete` `` | `` `{{ tools.dynamic_memory_forget }}` `` |

- [ ] **Step 2: Replace remaining inline references in the same section**

Apply these exact replacements (each is a unique occurrence):

- The diagnostic-exempt sentence:
  - Old: `` `memory_sessions`, `memory_audit`, và `memory_health` là diagnostic tools — không ảnh hưởng reasoning, miễn khỏi memory budget. ``
  - New: `` `{{ tools.dynamic_memory_sessions }}`, `{{ tools.dynamic_memory_audit }}`, và `{{ tools.dynamic_memory_health }}` là diagnostic tools — không ảnh hưởng reasoning, miễn khỏi memory budget. ``
- Pha 1 context:
  - Old: `đề xuất `memory_smart_search` trước khi thực thi`
  - New: `đề xuất `{{ tools.dynamic_memory_search }}` trước khi thực thi`
- Pre-spec context:
  - Old: `` **Trước spec (Pre-spec)**: `memory_recall` để tra cứu quyết định kiến trúc trước đó. ``
  - New: `` **Trước spec (Pre-spec)**: `{{ tools.dynamic_memory_recall }}` để tra cứu quyết định kiến trúc trước đó. ``
- Post-task context:
  - Old: `` **Sau task (Pha 3)**: `memory_save` chỉ qua `knowledge-curator` post-task hook. ``
  - New: `` **Sau task (Pha 3)**: `{{ tools.dynamic_memory_save }}` chỉ qua `knowledge-curator` post-task hook. ``
- Degrade branch (read tools):
  - Old: `- Mọi `memory_smart_search` / `memory_recall` bị **bỏ qua** — KHÔNG gọi, KHÔNG bịa kết quả.`
  - New: `- Mọi `{{ tools.dynamic_memory_search }}` / `{{ tools.dynamic_memory_recall }}` bị **bỏ qua** — KHÔNG gọi, KHÔNG bịa kết quả.`
- Write-path guard:
  - Old: `Gọi `memory_save` hoặc `memory_governance_delete` ngoài `knowledge-curator` post-task hook là **CẤM**.`
  - New: `Gọi `{{ tools.dynamic_memory_save }}` hoặc `{{ tools.dynamic_memory_forget }}` ngoài `knowledge-curator` post-task hook là **CẤM**.`

> **Do NOT change** the fixed degrade log string `agent-memory unavailable — skip recall/save` (it contains no `memory_*` tool name; it is a status string the gate-check whitelists).

- [ ] **Step 3: Verify no literal memory tool name remains in this file**

Run: `/usr/bin/grep -nE '\bmemory_(smart_search|recall|sessions|audit|health|save|governance_delete)\b' .amap/rules/rules-tool.md`
Expected: no output (exit 1). The `\b` word boundary means `{{ tools.dynamic_memory_save }}` etc. are NOT matched (preceded by `_`).

- [ ] **Step 4: Verify the template still renders (no StrictUndefined)**

Run: `/usr/bin/python3 -m pytest cli/tests/test_snapshots.py -v`
Expected: PASS — `run_init` renders every template (including `rules-tool.md`) for all 4 platforms under `StrictUndefined`; an unmapped `{{ tools.* }}` would raise here.

- [ ] **Step 5: Commit**

```bash
git add .amap/rules/rules-tool.md
git commit -m "refactor(rules-tool): memory tools via {{ tools.dynamic_memory_* }} (C-27)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Refactor `rules-exec.md` memory budget

**Files:**
- Modify: `.amap/rules/rules-exec.md` (memory budget bullets, ~lines 75–79)

- [ ] **Step 1: Replace tool names in the budget bullets**

- Memory budget header bullet:
  - Old: `- **Memory budget** — áp dụng cho `memory_smart_search` + `memory_recall` (chỉ khi`
  - New: `- **Memory budget** — áp dụng cho `{{ tools.dynamic_memory_search }}` + `{{ tools.dynamic_memory_recall }}` (chỉ khi`
- Phase 3 bullet:
  - Old: ``**Pha 3** (`/task apply`): **0 memory read calls**; **1 `memory_save` call** qua `knowledge-curator` post-task hook only.``
  - New: ``**Pha 3** (`/task apply`): **0 memory read calls**; **1 `{{ tools.dynamic_memory_save }}` call** qua `knowledge-curator` post-task hook only.``
- Exempt bullet:
  - Old: `- `memory_sessions`, `memory_audit`, `memory_health` là **exempt** — không tính vào budget.`
  - New: `- `{{ tools.dynamic_memory_sessions }}`, `{{ tools.dynamic_memory_audit }}`, `{{ tools.dynamic_memory_health }}` là **exempt** — không tính vào budget.`

- [ ] **Step 2: Verify no literal remains**

Run: `/usr/bin/grep -nE '\bmemory_(smart_search|recall|sessions|audit|health|save|governance_delete)\b' .amap/rules/rules-exec.md`
Expected: no output (exit 1).

- [ ] **Step 3: Verify render**

Run: `/usr/bin/python3 -m pytest cli/tests/test_snapshots.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add .amap/rules/rules-exec.md
git commit -m "refactor(rules-exec): memory budget via {{ tools.dynamic_memory_* }} (C-27)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Refactor `m7-memory-push.md` (+ remove the "native" header)

**Files:**
- Modify: `.amap/skills/knowledge-curator/references/m7-memory-push.md`

- [ ] **Step 1: Replace tool names and the "native" header**

- Intro line (~line 12):
  - Old: `Trước khi gọi `memory_save`, curator PHẢI đi qua 3 tầng:`
  - New: `Trước khi gọi `{{ tools.dynamic_memory_save }}`, curator PHẢI đi qua 3 tầng:`
- Tầng 0 (~line 18):
  - Old: `→ KHÔNG gọi `memory_smart_search` hay `memory_save`.`
  - New: `→ KHÔNG gọi `{{ tools.dynamic_memory_search }}` hay `{{ tools.dynamic_memory_save }}`.`
- Tầng 2 call (~line 36):
  - Old: `CALL: memory_smart_search(topic_summary, project_id=<project>, limit=3)`
  - New: `CALL: {{ tools.dynamic_memory_search }}(topic_summary, project_id=<project>, limit=3)`
- Save-call header (~line 54) — **remove the "native" claim**:
  - Old: `## Gọi `memory_save` (native — không cần mapping)`
  - New: `## Gọi `{{ tools.dynamic_memory_save }}``
- Save-call code block (~line 57):
  - Old: `memory_save(`
  - New: `{{ tools.dynamic_memory_save }}(`

- [ ] **Step 2: Verify no literal remains**

Run: `/usr/bin/grep -nE '\bmemory_(smart_search|recall|sessions|audit|health|save|governance_delete)\b' .amap/skills/knowledge-curator/references/m7-memory-push.md`
Expected: no output (exit 1).

- [ ] **Step 3: Verify render**

Run: `/usr/bin/python3 -m pytest cli/tests/test_snapshots.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add .amap/skills/knowledge-curator/references/m7-memory-push.md
git commit -m "refactor(m7): memory save/search via abstract op; drop 'native' claim (C-27)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Refactor `knowledge-curator/SKILL.md`

**Files:**
- Modify: `.amap/skills/knowledge-curator/SKILL.md` (~line 300)

- [ ] **Step 1: Replace the M7 summary reference**

- Old: `Bao gồm 3 tầng lọc chất lượng (Gate → Dedup → Quota), `memory_save` call, kind selection guide,`
- New: `Bao gồm 3 tầng lọc chất lượng (Gate → Dedup → Quota), `{{ tools.dynamic_memory_save }}` call, kind selection guide,`

- [ ] **Step 2: Verify no literal remains in the file**

Run: `/usr/bin/grep -nE '\bmemory_(smart_search|recall|sessions|audit|health|save|governance_delete)\b' .amap/skills/knowledge-curator/SKILL.md`
Expected: no output (exit 1).

- [ ] **Step 3: Verify render**

Run: `/usr/bin/python3 -m pytest cli/tests/test_snapshots.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add .amap/skills/knowledge-curator/SKILL.md
git commit -m "refactor(knowledge-curator): M7 summary uses abstract memory op (C-27)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Refactor `bootstrap.md` memory_health probe

**Files:**
- Modify: `.amap/procedures/bootstrap.md` (~line 173)

- [ ] **Step 1: Replace the probe tool name**

- Old: `>   Nếu `resolved-config.yaml` khai báo `agent-memory` → probe `memory_health` và ghi`
- New: `>   Nếu `resolved-config.yaml` khai báo `agent-memory` → probe `{{ tools.dynamic_memory_health }}` và ghi`

> Keep the surrounding lines (the `🔌 MCP: agent-memory: healthy` status line and the `agent-memory unavailable — skip recall/save` degrade line) unchanged — they are status strings, not tool calls.

- [ ] **Step 2: Verify no literal remains in the file**

Run: `/usr/bin/grep -nE '\bmemory_(smart_search|recall|sessions|audit|health|save|governance_delete)\b' .amap/procedures/bootstrap.md`
Expected: no output (exit 1).

- [ ] **Step 3: Verify render**

Run: `/usr/bin/python3 -m pytest cli/tests/test_snapshots.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add .amap/procedures/bootstrap.md
git commit -m "refactor(bootstrap): memory_health probe via abstract op (C-27)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Add the regression guard test (no re-hardcoding)

**Files:**
- Create: `cli/tests/test_no_hardcoded_memory_tools.py`

- [ ] **Step 1: Write the guard test**

```python
"""Guard: operational AMAP templates must not hardcode provider memory tool names.

Concrete memory tool names belong ONLY in cli/platforms/ mappings, the provider
setup recipe, fixed degrade/status strings, and historical docs (see C-27 spec
§5 Phần 5). Operational rules/skills/procedures/workflows must reference memory
via {{ tools.dynamic_memory_* }} so the provider stays swappable.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AMAP = REPO_ROOT / ".amap"
OPERATIONAL_DIRS = ("rules", "skills", "procedures", "workflows")

# \b word-boundary => the abstract op `dynamic_memory_save` (preceded by `_`)
# is NOT matched; only standalone provider tool names are.
LITERAL = re.compile(
    r"\bmemory_(?:smart_search|recall|sessions|audit|health|save|governance_delete)\b"
)


def test_no_hardcoded_memory_tool_names_in_operational_templates():
    offenders = []
    for sub in OPERATIONAL_DIRS:
        base = AMAP / sub
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if LITERAL.search(line):
                    rel = path.relative_to(REPO_ROOT)
                    offenders.append(f"{rel}:{lineno}: {line.strip()}")
    assert offenders == [], (
        "Hardcoded provider memory tool names found in operational templates "
        "(use {{ tools.dynamic_memory_* }} instead):\n" + "\n".join(offenders)
    )
```

- [ ] **Step 2: Run the guard test to verify it passes**

Run: `/usr/bin/python3 -m pytest cli/tests/test_no_hardcoded_memory_tools.py -v`
Expected: PASS (Tasks 2–6 removed every literal). If it FAILS, the offender list points to the exact `file:line` still holding a literal — fix that file the same way before continuing.

- [ ] **Step 3: Sanity-check the regex excludes the abstract op**

Run: `/usr/bin/python3 -c "import re; p=re.compile(r'\bmemory_(?:smart_search|recall|sessions|audit|health|save|governance_delete)\b'); print(bool(p.search('{{ tools.dynamic_memory_save }}')), bool(p.search('\`memory_save\`')))"`
Expected: `False True` (abstract op not flagged; bare literal flagged).

- [ ] **Step 4: Commit**

```bash
git add cli/tests/test_no_hardcoded_memory_tools.py
git commit -m "test: guard against re-hardcoding memory tool names in templates (C-27)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Add the MCP-only setup recipe

**Files:**
- Create: `.amap/profiles/agent-memory-mcp-only-setup.md`

> This file is framework-internal documentation (the `.amap/profiles/` dir is NOT in `cli/plugin-manifest.yaml`, so it is not scaffolded into target projects and does not affect snapshots). It documents the §4 boundary decision.

- [ ] **Step 1: Verify the upstream package/command before writing (spec §5 Phần 4)**

Check the current `rohitg00/agentmemory` README for the exact MCP-only install command and `mcpServers` block. If you cannot confirm the package name (`@agentmemory/mcp`) or command at implementation time, write them as **examples** with a link to the upstream README rather than as normative commands.

- [ ] **Step 2: Write the recipe**

```markdown
# Agent Memory — MCP-only setup (provider boundary)

> Framework-internal guidance. AMAP does **not** bundle, vendor, auto-install, or
> auto-run `agentmemory`. This recipe is for the **end project** that opts into
> the `memory` capability at `amap init`. Source of truth: design spec
> `docs/superpowers/specs/2026-06-21-memory-tool-capability-templating-design.md` §4.

## Why MCP-only (hooks OFF)

`agentmemory connect <agent>` installs **12 auto-capture hooks** that record memory
on every tool use with no gating. That directly conflicts with AMAP's memory
governance (R-Tool-6, M7: one save per task, 3 quality filters, no-PII, top-K
recall, source-of-truth priority). AMAP must own memory governance, so the end
project wires **only the MCP tool surface** and leaves auto-capture off.

## Setup (verify against upstream before use — example)

> Confirm the package name and command at the upstream repo:
> https://github.com/rohitg00/agentmemory

1. Run the standalone MCP shim (no hooks):

   ```
   npx -y @agentmemory/mcp
   ```

2. Or register the MCP server manually in your platform config (example shape):

   ```json
   {
     "mcpServers": {
       "agent-memory": { "command": "npx", "args": ["-y", "@agentmemory/mcp"] }
     }
   }
   ```

## Do NOT

- Do **not** run `agentmemory connect --with-hooks` (installs the 12 auto-capture hooks).
- Do **not** install agentmemory's bundled skills (they overlap `knowledge-curator` / bootstrap).
- Do **not** commit `~/.agentmemory/` state into the repo (it is user-machine-scoped).

## Result

AMAP's `dynamic_memory_*` abstract ops resolve to this server's tools
(`mcp__agent-memory__memory_*` on Claude Code). When `agent-memory` is not selected
at init, all recall/save are skipped per R-Tool-6 degrade and M7 Tầng 0 — AMAP
still works on repo-based knowledge alone.
```

- [ ] **Step 3: Verify nothing scaffolds it (snapshots unchanged)**

Run: `/usr/bin/python3 -m pytest cli/tests/test_snapshots.py -v`
Expected: PASS (the new file is under `.amap/profiles/`, which is not a scaffolded plugin source).

- [ ] **Step 4: Commit**

```bash
git add .amap/profiles/agent-memory-mcp-only-setup.md
git commit -m "docs(profiles): MCP-only agent-memory setup recipe (C-27 §4 boundary)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 9: Full suite, TODOS update, wrap-up

**Files:**
- Modify: `TODOS.md` (mark C-27 done — match the existing C-26 / enforcement entry style)

- [ ] **Step 1: Run the full test suite**

Run: `/usr/bin/python3 -m pytest cli/ -q`
Expected: PASS (all tests green, including the new platform tests, the guard, and unchanged snapshot/render/init/scaffold tests).

- [ ] **Step 2: Final whole-repo de-hardcode check across operational templates**

Run: `/usr/bin/grep -rnE '\bmemory_(smart_search|recall|sessions|audit|health|save|governance_delete)\b' .amap/rules .amap/skills .amap/procedures .amap/workflows`
Expected: no output (exit 1). Any hit is a missed literal — fix it before finishing.

- [ ] **Step 3: Update `TODOS.md`**

Add a C-27 entry mirroring the format of the existing C-26 (db-query templating) line, marking it DONE: memory-tool capability templating + agentmemory MCP-only boundary; 7 `dynamic_memory_*` ops; provider not bundled.

- [ ] **Step 4: Commit**

```bash
git add TODOS.md
git commit -m "docs(todos): mark C-27 done (memory-tool capability templating)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 5: Confirm the branch is ready for PR**

Run: `git log --oneline main..HEAD`
Expected: the spec commits plus the 9-task implementation commits, all on `memory-tool-capability-templating`.

---

## Acceptance (from spec §9)

- Operational templates (`.amap/rules|skills|procedures|workflows`) contain **0** literal provider memory tool names; all reference `{{ tools.dynamic_memory_* }}`.
- `cli/platforms/` is the single place deciding concrete tool names.
- `amap init` renders successfully **with and without** `agent-memory` selected.
- No new runtime dependency; agentmemory not bundled/vendored/auto-installed/auto-run; no auto-capture hooks enabled by AMAP.
- Semantics of R-Tool-6, rules-exec, M7, R-KL-3 unchanged.
- Promote-to-knowledge remains AMAP core governance (no provider op).
