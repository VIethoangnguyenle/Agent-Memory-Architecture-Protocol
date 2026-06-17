# SP3' Review — CLI Scaffolding Migration

> **Date**: 2026-06-17  
> **Author**: Antigravity (thay thế SP3 của Claude Code)  
> **Base**: `b226424` (main HEAD — SP3 adapter layer)  
> **Patch file**: [SP3-CLI-MIGRATION.patch](./SP3-CLI-MIGRATION.patch)

---

## 1. Tổng quan thay đổi

```
23 files changed, 180 insertions(+), 762 deletions(-)
15 new files (cli/ + pyproject.toml) — 1,514 lines
8 files deleted (.agent/adapters/) — 501 lines
```

### Motivation

SP3 (Claude Code) xây **runtime adapter** — agent tự detect provider lúc chạy.  
SP3' (Antigravity) thay bằng **build-time CLI** — dev chạy `amap init`, output có tool names đúng sẵn.

**Lý do thay thế:**
1. Runtime detection phức tạp, agent không phải lúc nào cũng detect đúng
2. Abstract operation names trong skill files khiến agent confuse
3. Build-time resolution = deterministic, testable, zero-ambiguity

---

## 2. Files DELETED (8 files, -501 lines)

Toàn bộ `.agent/adapters/` — runtime adapter layer:

| File | Lines | Mô tả |
|---|---|---|
| `adapters/README.md` | 39 | Adapter docs |
| `adapters/capabilities.yaml` | 116 | 3 abstract capabilities |
| `adapters/registry.yaml` | 59 | Auto-detection rules |
| `adapters/providers/socraticode.yaml` | 66 | Socraticode provider |
| `adapters/providers/kg-mcp.yaml` | 65 | KG MCP provider |
| `adapters/providers/confluence.yaml` | 41 | Confluence provider |
| `adapters/providers/db-remote.yaml` | 57 | DB Remote provider |
| `adapters/providers/grep-fallback.yaml` | 58 | Grep fallback |

---

## 3. Files MODIFIED (15 files)

### 3.1 Core docs

**AGENTS.md** (-19 lines)
- Xoá `adapters/` khỏi directory tree
- Xoá Bước 3b (load adapter registry) trong Bootstrap Protocol
- Cập nhật bootstrap report: `🔌 Adapters: [...]` → `🔌 Platform: <platform> | MCPs: [...]`

**README.md** (-42 lines)
- Quick start: `cp -r` → `pip install -e .` + `amap init`
- Xoá adapter FAQ (provider detection, grep-fallback, auto vs forced)
- Thêm MCP table + re-scaffold guide
- FAQ: "thêm provider custom" → "thêm platform custom"

**rules-tool.md** (-12 lines)
- R-Tool-7: Runtime adapter rules → build-time CLI resolution rules

### 3.2 Templatized files (11 files — 126 tool refs)

Tất cả hardcoded tool names → `{{ tools.X }}` Jinja2 variables:

| File | Refs converted | Example |
|---|---|---|
| `skills/codebase-explorer/SKILL.md` | 32 | `mcp_socraticode_codebase_search` → `{{ tools.search_code }}` |
| `skills/architecture-reviewer/SKILL.md` | 10 | `mcp_socraticode_codebase_impact` → `{{ tools.find_blast_radius }}` |
| `skills/convention-intelligence-builder/SKILL.md` | 8 | |
| `skills/convention-builder/references/*.md` | 9 | |
| `skills/infra-tdd/SKILL.md` | 6 | |
| `skills/infra-tdd/references/socratic-deep-dive.md` | 20 | |
| `skills/author-dna-builder/references/code-evidence-scan.md` | 12 | |
| `workflows/task.md` | 18 | |
| `workflows/index-source.md` | 8 | |
| `procedures/token-tracking.md` | 1 | |

Khi `amap init` chạy, `{{ tools.search_code }}` được render thành:
- **Antigravity**: `mcp_socraticode_codebase_search`
- **Claude Code**: `mcp__socraticode__codebase_search`
- **Cursor**: `mcp_socraticode_codebase_search`

---

## 4. Files NEW (15 files, +1,514 lines)

### 4.1 Package config

**`pyproject.toml`** (47 lines)
- Entry point: `amap = "cli.amap:main"`
- Dependencies: `jinja2>=3.1`, `pyyaml>=6.0`
- Install: `pip install -e .`

### 4.2 CLI entry point

**`cli/amap.py`** (82 lines)
- Commands: `init`, `status`, `--version`
- Backward compat: `python cli/amap.py` vẫn hoạt động

**`cli/__init__.py`** (2 lines) — version `3.0.0`

### 4.3 Commands

**`cli/commands/init.py`** (297 lines) — Core scaffolding logic:
- Interactive prompt: platform → MCPs → language → confirm
- Plugin processing: copy + auto-detect render + capability gating
- `generate_resolved_config()` → `.agent/resolved-config.yaml`

**`cli/commands/status.py`** (87 lines) — Project diagnostics:
- Platform, MCPs, language from resolved-config
- Skills/workflows listing, knowledge layer state, DNA status

### 4.4 Platforms

**`cli/platforms/base.py`** (90 lines) — Abstract interface:
- `tool_mapping`: abstract → concrete tool names
- `capabilities`: subagent, browser, artifacts...
- `build_render_context()`: Jinja2 context builder

**`cli/platforms/antigravity.py`** (67 lines) — 27 tool mappings:
```python
"search_code": "mcp_socraticode_codebase_search"
"run_command": "run_command"
"read_file":   "view_file"
```

**`cli/platforms/claude_code.py`** (63 lines) — 24 tool mappings:
```python
"search_code": "mcp__socraticode__codebase_search"
"run_command": "Bash"
"read_file":   "Read"
```

**`cli/platforms/cursor.py`** (55 lines) + **`generic.py`** (59 lines)

### 4.5 Renderer

**`cli/renderer.py`** (152 lines):
- `render_string()` — render Jinja2 from string (không cần file)
- `copy_and_render_directory()` — copy dir, auto-detect `{{ ` → render
- Binary-safe (chỉ render `.md`, `.yaml`, `.yml`, `.txt`, `.py`)

### 4.6 Plugin manifest

**`cli/plugin-manifest.yaml`** (329 lines) — 42 plugins:
- `mcp_capabilities`: 3 MCPs với capability mapping
- `plugins[]`: name, source, output, template, copy_dir, requires_capability

### 4.7 Templatize tool

**`cli/tools/templatize.py`** (209 lines):
- Scan files, replace hardcoded tool names → `{{ tools.X }}`
- Dry-run mode, report mode
- Đã chạy 1 lần, convert 126 refs thành công

---

## 5. Test Results

| Test | Result |
|---|---|
| Structure (14 skills, 9 workflows) | ✅ |
| Zero unresolved `{{ ` in output | ✅ |
| Tool names differ per platform | ✅ |
| Capability gating (3 correct skips) | ✅ |
| File integrity (AGENTS.md, templates) | ✅ |
| Cross-platform diff (12 files) | ✅ |
| `amap --version` | ✅ `3.0.0` |
| `amap init` + `amap status` E2E | ✅ |

---

## 6. Review Checklist

- [ ] Có đồng ý xoá `.agent/adapters/` hoàn toàn?
- [ ] Tool mapping cho Antigravity đúng? (27 tools)
- [ ] Tool mapping cho Claude Code đúng? (24 tools)
- [ ] Manifest 42 plugins đủ? Thiếu/thừa gì?
- [ ] Capability gating logic OK? (db_access, code_exploration, doc_search)
- [ ] README quick start flow rõ ràng?
- [ ] AGENTS.md bootstrap report format OK?
- [ ] Có cần thêm platform nào?
- [ ] pyproject.toml metadata đúng?

---

## 7. Lệnh test nhanh

```bash
# Install CLI
pip install -e . --break-system-packages

# Test version
amap --version

# Test scaffold Antigravity (all MCPs)
mkdir /tmp/test && echo -e "1\n1,2,3\n2\ny" | amap init --target /tmp/test

# Check result
amap status --target /tmp/test

# Verify no unresolved Jinja2
grep -rn "{{ " /tmp/test/.agent/ --include="*.md" | wc -l  # expect: 0

# Cleanup
rm -rf /tmp/test
```
