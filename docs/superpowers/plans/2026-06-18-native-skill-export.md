# Native Skill + Workflow Export — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `amap init`/`update` mirror each skill and workflow into the target platform's native skill/command location (`.claude/skills/`, `.agents/skills/`, `.cursor/commands/`), in addition to the existing `.amap/skills/`/`.amap/workflows/` output, and add a `codex` platform adapter — so AMAP content is discoverable through each tool's own UI, not only through `bootstrap.md` prose.

**Architecture:** A new `BasePlatform.native_skill_export` property (default `None`) declares, per platform, where (if anywhere) it natively discovers skills. A new scaffold pass (`scaffold_native_skill_exports`) reads each already-rendered skill/workflow from the staging dir and writes a second copy to that location — verbatim for Claude Code/Codex/Antigravity, frontmatter-stripped (with `pre_conditions` re-rendered as a checklist) for Cursor. `bootstrap.md` and the manifest are untouched; this is purely an additive output of the existing scaffold pipeline.

**Tech Stack:** Python 3.12, Jinja2, PyYAML, pytest.

**Spec:** `docs/superpowers/specs/2026-06-18-native-skill-export-design.md`

---

## File Structure

**Created:**
- `cli/platforms/codex.py` — new `CodexPlatform` adapter.
- `cli/tests/test_platforms.py` — direct tests for platform adapter properties.

**Modified:**
- `cli/platforms/base.py` — add `native_skill_export` property (default `None`).
- `cli/platforms/claude_code.py`, `cli/platforms/antigravity.py`, `cli/platforms/cursor.py` — override `native_skill_export`; `cursor.py` also gets one more `notes` line.
- `cli/platforms/__init__.py` — register `codex`.
- `cli/scaffold.py` — add `export_as_flat_command()` and `scaffold_native_skill_exports()`.
- `cli/commands/init.py` — call `scaffold_native_skill_exports()` in the staging step.
- `cli/commands/update.py` — call `scaffold_native_skill_exports()` in the staging step; on `--reconfigure`, remove stale native-export directories from the previous platform.
- `cli/tests/test_scaffold.py`, `cli/tests/test_init.py`, `cli/tests/test_update.py` — new tests.

**Test helper convention** (already used in these files):
```python
def _answers(monkeypatch, seq):
    """Feed a fixed sequence to builtins.input()."""
    it = iter(seq)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(it))
```
Prompt order for `run_init`: platform, MCPs, language, confirm. **After this plan, `PLATFORMS` order is:** `1`=antigravity, `2`=claude-code, `3`=cursor, `4`=generic, `5`=codex (codex is appended last so none of the existing indices shift). Language index `3`=python. So claude-code init = `["2", "1,2,3", "3", "y"]`; codex init = `["5", "1,2,3", "3", "y"]`.

**Test runner:** use `/usr/bin/python3 -m pytest`, not bare `python3` — this repo's `.venv/bin/python3` (what `python3` resolves to on `$PATH`) has no `pytest` installed; `/usr/bin/python3` does.

---

## Task 1: `native_skill_export` default property on `BasePlatform`

**Files:**
- Modify: `cli/platforms/base.py:4` (import), `cli/platforms/base.py:55-67` (insert property)
- Test: `cli/tests/test_platforms.py` (create)

- [ ] **Step 1: Write the failing test**

Create `cli/tests/test_platforms.py`:

```python
"""Tests for platform adapter definitions."""

from cli.platforms.generic import GenericPlatform


def test_generic_platform_has_no_native_skill_export():
    assert GenericPlatform().native_skill_export is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest cli/tests/test_platforms.py -v`
Expected: FAIL with `AttributeError: 'GenericPlatform' object has no attribute 'native_skill_export'`.

- [ ] **Step 3: Add the property to `BasePlatform`**

In `cli/platforms/base.py`, line 4 currently reads:

```python
from typing import Dict, List
```

becomes:

```python
from typing import Dict, List, Optional
```

Then, the current `mcp_tool_prefix`/`notes` block (lines 55-67):

```python
    @property
    def mcp_tool_prefix(self) -> str:
        """How this platform prefixes MCP tool names.

        Antigravity: 'mcp_<server>_<tool>'
        Claude Code: 'mcp__<server>__<tool>'
        """
        return ""

    @property
    def notes(self) -> List[str]:
        """Platform-specific notes shown during init."""
        return []
```

becomes:

```python
    @property
    def mcp_tool_prefix(self) -> str:
        """How this platform prefixes MCP tool names.

        Antigravity: 'mcp_<server>_<tool>'
        Claude Code: 'mcp__<server>__<tool>'
        """
        return ""

    @property
    def native_skill_export(self) -> Optional[dict]:
        """Where (if anywhere) this platform natively auto-discovers skills.

        None = no native discovery; skills/workflows are reachable only via
        bootstrap.md's manual PHASE 1 self-registration (works on every
        platform, including this one).

        dir: root directory; the skill/workflow name is appended automatically.
        strip_frontmatter: True means export as a flat <name>.md with YAML
          frontmatter removed — pre_conditions (if any) are re-rendered into
          the body as a checklist instead of being silently dropped (see
          export_as_flat_command in cli/scaffold.py).
        flatten: True means output is <dir>/<name>.md (no subfolder); False
          means <dir>/<name>/SKILL.md.
        """
        return None

    @property
    def notes(self) -> List[str]:
        """Platform-specific notes shown during init."""
        return []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/bin/python3 -m pytest cli/tests/test_platforms.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cli/platforms/base.py cli/tests/test_platforms.py
git commit -m "$(cat <<'EOF'
feat(cli): add native_skill_export property to BasePlatform

Default None — platforms opt in to declaring where they natively
discover skills/workflows. No behavior change yet.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Override `native_skill_export` for claude-code, antigravity, cursor

**Files:**
- Modify: `cli/platforms/claude_code.py:57-59`
- Modify: `cli/platforms/antigravity.py:61-63`
- Modify: `cli/platforms/cursor.py:49-55`
- Test: `cli/tests/test_platforms.py`

- [ ] **Step 1: Write the failing tests**

Append to `cli/tests/test_platforms.py`:

```python
from cli.platforms import get_platform


def test_claude_code_native_skill_export():
    export = get_platform("claude-code").native_skill_export
    assert export == {"dir": ".claude/skills", "strip_frontmatter": False, "flatten": False}


def test_antigravity_native_skill_export():
    export = get_platform("antigravity").native_skill_export
    assert export == {"dir": ".agents/skills", "strip_frontmatter": False, "flatten": False}


def test_cursor_native_skill_export():
    export = get_platform("cursor").native_skill_export
    assert export == {"dir": ".cursor/commands", "strip_frontmatter": True, "flatten": True}


def test_cursor_notes_mention_manual_invocation():
    notes = " ".join(get_platform("cursor").notes).lower()
    assert "auto-trigger" in notes or "manual" in notes
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest cli/tests/test_platforms.py -v`
Expected: the 4 new tests FAIL — `native_skill_export` is still `None` (inherited default) for all three platforms.

- [ ] **Step 3: Override in `claude_code.py`**

Current (lines 57-59):

```python
    mcp_tool_prefix = "mcp__"

    notes = [
```

becomes:

```python
    mcp_tool_prefix = "mcp__"

    native_skill_export = {"dir": ".claude/skills", "strip_frontmatter": False, "flatten": False}

    notes = [
```

- [ ] **Step 4: Override in `antigravity.py`**

Current (lines 61-63):

```python
    mcp_tool_prefix = "mcp_"

    notes = [
```

becomes:

```python
    mcp_tool_prefix = "mcp_"

    native_skill_export = {"dir": ".agents/skills", "strip_frontmatter": False, "flatten": False}

    notes = [
```

- [ ] **Step 5: Override in `cursor.py`**

Current (lines 49-55):

```python
    }

    notes = [
        ".cursorrules is the config entry point",
        "Cursor has limited MCP support — check version",
        "No subagent capability — workflows degrade to sequential",
    ]
```

becomes:

```python
    }

    native_skill_export = {"dir": ".cursor/commands", "strip_frontmatter": True, "flatten": True}

    notes = [
        ".cursorrules is the config entry point",
        "Cursor has limited MCP support — check version",
        "No subagent capability — workflows degrade to sequential",
        "Skills/workflows export to .cursor/commands/ as manual commands — Cursor does "
        "not auto-trigger them from a description the way a real skill picker would",
    ]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `/usr/bin/python3 -m pytest cli/tests/test_platforms.py -v`
Expected: all PASS

- [ ] **Step 7: Run the full suite**

Run: `/usr/bin/python3 -m pytest cli/ -q`
Expected: all pass (28 pre-existing + new ones).

- [ ] **Step 8: Commit**

```bash
git add cli/platforms/claude_code.py cli/platforms/antigravity.py cli/platforms/cursor.py cli/tests/test_platforms.py
git commit -m "$(cat <<'EOF'
feat(cli): declare native_skill_export for claude-code, antigravity, cursor

claude-code and antigravity point at their real skill-discovery folders
(.claude/skills/, .agents/skills/ — the latter shared with Codex per the
open agent-skills standard). Cursor points at .cursor/commands/ with
strip_frontmatter+flatten, since Cursor commands forbid frontmatter and
are flat files, not folders.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: New `codex` platform adapter

**Files:**
- Create: `cli/platforms/codex.py`
- Modify: `cli/platforms/__init__.py`
- Test: `cli/tests/test_platforms.py`

- [ ] **Step 1: Write the failing tests**

Append to `cli/tests/test_platforms.py`:

```python
from cli.platforms import PLATFORMS


def test_codex_platform_registered():
    assert "codex" in PLATFORMS
    codex = get_platform("codex")
    assert codex.config_entry_point == "AGENTS.md"
    assert codex.native_skill_export == {
        "dir": ".agents/skills", "strip_frontmatter": False, "flatten": False,
    }


def test_codex_tool_mapping_is_abstract_passthrough():
    codex = get_platform("codex")
    assert codex.tool_mapping["read_file"] == "read_file"
    assert codex.tool_mapping["run_command"] == "run_command"


def test_platforms_dict_order_unchanged_for_existing_platforms():
    # Existing tests hardcode numeric prompt indices for these 4 platforms —
    # codex must be appended, never inserted, or those indices break.
    keys = list(PLATFORMS.keys())
    assert keys[:4] == ["antigravity", "claude-code", "cursor", "generic"]
    assert keys[4] == "codex"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest cli/tests/test_platforms.py -v`
Expected: FAIL — `cli.platforms.codex` does not exist yet; `"codex" in PLATFORMS` is `False`.

- [ ] **Step 3: Create `cli/platforms/codex.py`**

```python
"""Codex Platform — OpenAI Codex CLI agent."""

from .base import BasePlatform


class CodexPlatform(BasePlatform):

    name = "codex"
    display_name = "OpenAI Codex CLI"
    config_entry_point = "AGENTS.md"

    native_skill_export = {"dir": ".agents/skills", "strip_frontmatter": False, "flatten": False}

    tool_mapping = {
        # Codex CLI does not publicly document its internal tool names the
        # way Claude Code/Antigravity do — keep abstract passthrough (same
        # approach as GenericPlatform) rather than inventing concrete names.
        "read_file":         "read_file",
        "write_file":        "write_file",
        "edit_file":         "edit_file",
        "multi_edit_file":   "multi_edit_file",
        "search_text":       "search_text",
        "list_directory":    "list_directory",
        "run_command":       "run_command",
        "command_status":    "command_status",
        "send_input":        "send_input",
        "search_code":       "search_code",
        "index_code":        "index_code",
        "code_status":       "code_status",
        "get_dependencies":  "get_dependencies",
        "trace_flow":        "trace_flow",
        "find_blast_radius": "find_blast_radius",
        "get_symbol":        "get_symbol",
        "list_symbols":      "list_symbols",
        "graph_stats":       "graph_stats",
        "graph_build":       "graph_build",
        "search_docs":       "search_docs",
        "get_page":          "get_page",
        "list_spaces":       "list_spaces",
        "search_web":        "search_web",
        "read_url":          "read_url",
    }

    notes = [
        "AGENTS.md is the config entry point (developers.openai.com/codex/guides/agents-md)",
        "tool_mapping is abstract passthrough — Codex CLI's internal tool names are not "
        "publicly documented; map manually if your AMAP skills need concrete tool calls",
        "Skills/workflows export to .agents/skills/ — the open agent-skills standard, "
        "shared with Antigravity",
    ]
```

- [ ] **Step 4: Register it in `cli/platforms/__init__.py`**

Current full content:

```python
"""Platform registry — discover and load platform definitions."""

from .antigravity import AntigravityPlatform
from .claude_code import ClaudeCodePlatform
from .cursor import CursorPlatform
from .generic import GenericPlatform

PLATFORMS = {
    "antigravity": AntigravityPlatform,
    "claude-code": ClaudeCodePlatform,
    "cursor": CursorPlatform,
    "generic": GenericPlatform,
}


def get_platform(name: str):
    """Get platform class by name."""
    cls = PLATFORMS.get(name)
    if not cls:
        raise ValueError(f"Unknown platform: {name}. Available: {list(PLATFORMS.keys())}")
    return cls()
```

becomes:

```python
"""Platform registry — discover and load platform definitions."""

from .antigravity import AntigravityPlatform
from .claude_code import ClaudeCodePlatform
from .codex import CodexPlatform
from .cursor import CursorPlatform
from .generic import GenericPlatform

PLATFORMS = {
    "antigravity": AntigravityPlatform,
    "claude-code": ClaudeCodePlatform,
    "cursor": CursorPlatform,
    "generic": GenericPlatform,
    "codex": CodexPlatform,
}


def get_platform(name: str):
    """Get platform class by name."""
    cls = PLATFORMS.get(name)
    if not cls:
        raise ValueError(f"Unknown platform: {name}. Available: {list(PLATFORMS.keys())}")
    return cls()
```

(`codex` is appended **after** `generic` in the dict, not inserted earlier — this keeps `antigravity`/`claude-code`/`cursor`/`generic` at indices 1-4, matching every existing test's hardcoded prompt answers. It becomes index `5`.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `/usr/bin/python3 -m pytest cli/tests/test_platforms.py -v`
Expected: all PASS

- [ ] **Step 6: Run the full suite**

Run: `/usr/bin/python3 -m pytest cli/ -q`
Expected: all pass — no existing test's numeric platform index broke.

- [ ] **Step 7: Commit**

```bash
git add cli/platforms/codex.py cli/platforms/__init__.py cli/tests/test_platforms.py
git commit -m "$(cat <<'EOF'
feat(cli): add Codex CLI platform adapter

config_entry_point=AGENTS.md and native_skill_export=.agents/skills/
are verified against developers.openai.com/codex docs. tool_mapping is
left as abstract passthrough since Codex CLI doesn't publicly document
concrete internal tool names. Appended last in PLATFORMS so existing
numeric platform indices in tests are unaffected.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: `export_as_flat_command()` — frontmatter-stripping transform

**Files:**
- Modify: `cli/scaffold.py` (new function, placed after `scaffold_plugins`, before `verify_no_unresolved`)
- Test: `cli/tests/test_scaffold.py`

- [ ] **Step 1: Write the failing tests**

Append to `cli/tests/test_scaffold.py`:

```python
from cli.scaffold import export_as_flat_command


def test_export_as_flat_command_strips_frontmatter_and_inlines_pre_conditions():
    skill_md = (
        "---\n"
        "name: requirement-analyst\n"
        "description: Standardize tickets into REQUIREMENT.md.\n"
        "pre_conditions:\n"
        "  - file: .amap/knowledge/active/AGENT_TRANSPARENCY.md\n"
        "    condition: exists\n"
        "    on_fail: \"ABORT - bootstrap hasn't run\"\n"
        "---\n"
        "\n"
        "# Requirement Analyst\n"
        "\n"
        "Body content here.\n"
    )

    output = export_as_flat_command(skill_md)

    assert not output.startswith("---")
    assert "name:" not in output
    assert "# requirement-analyst" in output
    assert "Standardize tickets into REQUIREMENT.md." in output
    assert "ABORT - bootstrap hasn't run" in output
    assert "Body content here." in output


def test_export_as_flat_command_without_pre_conditions_omits_checklist():
    skill_md = (
        "---\n"
        "description: Approve and commit.\n"
        "---\n"
        "\n"
        "# /approve-conventions\n"
        "\n"
        "Body.\n"
    )

    output = export_as_flat_command(skill_md)

    assert "Pre-conditions" not in output
    assert "Approve and commit." in output
    assert "Body." in output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest cli/tests/test_scaffold.py -v -k export_as_flat_command`
Expected: FAIL with `ImportError: cannot import name 'export_as_flat_command'`.

- [ ] **Step 3: Implement `export_as_flat_command`**

In `cli/scaffold.py`, insert this new function right after `scaffold_plugins` (which currently ends at line 176, just before `def verify_no_unresolved`):

```python
def export_as_flat_command(skill_md_text: str) -> str:
    """Render a SKILL.md/workflow file as a frontmatter-free flat command.

    For platforms whose native command format forbids YAML frontmatter
    (e.g. Cursor's .cursor/commands/*.md). pre_conditions are re-rendered
    as a plain markdown checklist so the gates they encode (e.g.
    "ABORT - bootstrap hasn't run") aren't silently dropped.
    """
    _, frontmatter_text, body = skill_md_text.split("---", 2)
    meta = yaml.safe_load(frontmatter_text) or {}
    name = meta.get("name", "")
    description = (meta.get("description") or "").strip()

    header_lines = [f"# {name}", "", f"> {description}"]

    pre_conditions = meta.get("pre_conditions") or []
    if pre_conditions:
        header_lines.append("")
        header_lines.append("## Pre-conditions")
        for cond in pre_conditions:
            target = cond.get("file") or cond.get("input") or ""
            condition = cond.get("condition", "")
            on_fail = cond.get("on_fail", "")
            header_lines.append(f"- `{target}` {condition} -> if not met: {on_fail}")

    return "\n".join(header_lines) + "\n" + body.lstrip("\n")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `/usr/bin/python3 -m pytest cli/tests/test_scaffold.py -v -k export_as_flat_command`
Expected: both PASS

- [ ] **Step 5: Run the full suite**

Run: `/usr/bin/python3 -m pytest cli/ -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add cli/scaffold.py cli/tests/test_scaffold.py
git commit -m "$(cat <<'EOF'
feat(cli): add export_as_flat_command for frontmatter-free platforms

Strips YAML frontmatter and re-renders pre_conditions as a markdown
checklist in the body, so platforms that forbid frontmatter (Cursor)
don't silently lose the gates pre_conditions encode.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: `scaffold_native_skill_exports()` — the new scaffold pass

**Files:**
- Modify: `cli/scaffold.py` (new function, placed after `export_as_flat_command`)
- Test: `cli/tests/test_scaffold.py`

- [ ] **Step 1: Write the failing tests**

Append to `cli/tests/test_scaffold.py`:

```python
from cli.scaffold import scaffold_native_skill_exports


class _FakePlatform:
    def __init__(self, native_skill_export):
        self.native_skill_export = native_skill_export


def test_scaffold_native_skill_exports_noop_when_unsupported(tmp_path):
    plugins = [{"name": "requirement-analyst", "type": "skill", "copy_dir": True,
                "output": ".amap/skills/requirement-analyst/"}]
    platform = _FakePlatform(None)

    stats = scaffold_native_skill_exports(plugins, tmp_path, platform, verbose=False)

    assert stats == {"exported": 0, "skipped": 0}


def test_scaffold_native_skill_exports_mirrors_skill_verbatim(tmp_path):
    skill_dir = tmp_path / ".amap" / "skills" / "requirement-analyst"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: requirement-analyst\ndescription: Standardize tickets.\n---\n\nBody.\n",
        encoding="utf-8",
    )
    plugins = [{"name": "requirement-analyst", "type": "skill", "copy_dir": True,
                "output": ".amap/skills/requirement-analyst/"}]
    platform = _FakePlatform({"dir": ".claude/skills", "strip_frontmatter": False, "flatten": False})

    stats = scaffold_native_skill_exports(plugins, tmp_path, platform, verbose=False)

    target = tmp_path / ".claude" / "skills" / "requirement-analyst" / "SKILL.md"
    assert target.exists()
    assert target.read_text(encoding="utf-8") == (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    assert stats == {"exported": 1, "skipped": 0}


def test_scaffold_native_skill_exports_inserts_name_for_workflow(tmp_path):
    workflow_path = tmp_path / ".amap" / "workflows" / "task.md"
    workflow_path.parent.mkdir(parents=True)
    workflow_path.write_text(
        "---\ndescription: Main task orchestrator.\n---\n\n# /task\n",
        encoding="utf-8",
    )
    plugins = [{"name": "workflow-task", "type": "workflow", "output": ".amap/workflows/task.md"}]
    platform = _FakePlatform({"dir": ".claude/skills", "strip_frontmatter": False, "flatten": False})

    scaffold_native_skill_exports(plugins, tmp_path, platform, verbose=False)

    target = tmp_path / ".claude" / "skills" / "task" / "SKILL.md"
    content = target.read_text(encoding="utf-8")
    assert "name: task" in content
    assert "description: Main task orchestrator." in content


def test_scaffold_native_skill_exports_flattens_and_strips_for_cursor(tmp_path):
    skill_dir = tmp_path / ".amap" / "skills" / "requirement-analyst"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: requirement-analyst\ndescription: Standardize tickets.\n---\n\nBody.\n",
        encoding="utf-8",
    )
    plugins = [{"name": "requirement-analyst", "type": "skill", "copy_dir": True,
                "output": ".amap/skills/requirement-analyst/"}]
    platform = _FakePlatform({"dir": ".cursor/commands", "strip_frontmatter": True, "flatten": True})

    scaffold_native_skill_exports(plugins, tmp_path, platform, verbose=False)

    target = tmp_path / ".cursor" / "commands" / "requirement-analyst.md"
    content = target.read_text(encoding="utf-8")
    assert not content.startswith("---")
    assert "Standardize tickets." in content
    assert "Body." in content


def test_scaffold_native_skill_exports_skips_missing_frontmatter(tmp_path):
    workflow_path = tmp_path / ".amap" / "workflows" / "tdd.md"
    workflow_path.parent.mkdir(parents=True)
    workflow_path.write_text("# /tdd\n\nNo frontmatter here.\n", encoding="utf-8")
    plugins = [{"name": "workflow-tdd", "type": "workflow", "output": ".amap/workflows/tdd.md"}]
    platform = _FakePlatform({"dir": ".claude/skills", "strip_frontmatter": False, "flatten": False})

    stats = scaffold_native_skill_exports(plugins, tmp_path, platform, verbose=False)

    assert stats == {"exported": 0, "skipped": 1}
    assert not (tmp_path / ".claude" / "skills" / "tdd").exists()


def test_scaffold_native_skill_exports_ignores_non_skill_workflow_plugins(tmp_path):
    plugins = [{"name": "rules-manifest", "type": "rule", "output": ".amap/rules/RULES.md"}]
    platform = _FakePlatform({"dir": ".claude/skills", "strip_frontmatter": False, "flatten": False})

    stats = scaffold_native_skill_exports(plugins, tmp_path, platform, verbose=False)

    assert stats == {"exported": 0, "skipped": 0}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest cli/tests/test_scaffold.py -v -k native_skill_exports`
Expected: FAIL with `ImportError: cannot import name 'scaffold_native_skill_exports'`.

- [ ] **Step 3: Implement `scaffold_native_skill_exports`**

In `cli/scaffold.py`, insert this new function right after `export_as_flat_command` (added in Task 4):

```python
def scaffold_native_skill_exports(
    plugins: List[dict], write_root: Path, platform, verbose: bool = True,
) -> dict:
    """Mirror skill/workflow plugins into the platform's native skill/command
    location (if it has one), in addition to their .amap/ output.

    Reads from write_root / plugin["output"] — already Jinja-rendered for
    this platform by scaffold_plugins() — rather than from the AMAP repo
    source, so the native export always matches the rendered content
    exactly. No-op if platform.native_skill_export is None.
    """
    stats = {"exported": 0, "skipped": 0}
    export = platform.native_skill_export
    if export is None:
        return stats

    for plugin in plugins:
        if plugin.get("type") not in ("skill", "workflow"):
            continue

        output_path = write_root / plugin["output"]
        source_file = output_path / "SKILL.md" if plugin.get("copy_dir") else output_path
        if not source_file.exists():
            stats["skipped"] += 1
            continue

        text = source_file.read_text(encoding="utf-8")
        if not text.startswith("---"):
            if verbose:
                print(f"  ⏭️  native export skip: {plugin['name']} (no frontmatter)")
            stats["skipped"] += 1
            continue

        name = plugin["name"].removeprefix("workflow-")
        _, frontmatter_text, body = text.split("---", 2)
        meta = yaml.safe_load(frontmatter_text) or {}
        if "name" not in meta:
            meta = {"name": name, **meta}
            frontmatter_text = yaml.dump(meta, default_flow_style=False, allow_unicode=True)
            text = f"---\n{frontmatter_text}---{body}"

        content = export_as_flat_command(text) if export["strip_frontmatter"] else text

        if export["flatten"]:
            target = write_root / export["dir"] / f"{name}.md"
        else:
            target = write_root / export["dir"] / name / "SKILL.md"

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        stats["exported"] += 1
        if verbose:
            print(f"  ✅ native export: {target.relative_to(write_root)}")

    return stats
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `/usr/bin/python3 -m pytest cli/tests/test_scaffold.py -v -k native_skill_exports`
Expected: all PASS

- [ ] **Step 5: Run the full suite**

Run: `/usr/bin/python3 -m pytest cli/ -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add cli/scaffold.py cli/tests/test_scaffold.py
git commit -m "$(cat <<'EOF'
feat(cli): add scaffold_native_skill_exports pass

Mirrors skill/workflow plugins into a platform's native_skill_export
location, synthesizing a name: frontmatter key for workflows (which
only declare description:). No-op for platforms without native
discovery. Not yet wired into init/update — next commits do that.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Wire into `amap init`

**Files:**
- Modify: `cli/commands/init.py:10-16` (import), `cli/commands/init.py:103-118` (call)
- Test: `cli/tests/test_init.py`

- [ ] **Step 1: Write the failing tests**

Append to `cli/tests/test_init.py`:

```python
def test_init_exports_skills_to_claude_native_path(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])  # claude-code

    run_init(target_dir=str(target), amap_root=str(amap_root))

    native = target / ".claude" / "skills" / "requirement-analyst" / "SKILL.md"
    assert native.exists()
    canonical = target / ".amap" / "skills" / "requirement-analyst" / "SKILL.md"
    assert native.read_text(encoding="utf-8") == canonical.read_text(encoding="utf-8")


def test_init_exports_skills_to_agents_path_for_codex(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["5", "1,2,3", "3", "y"])  # codex

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert (target / "AGENTS.md").exists()
    assert (target / ".agents" / "skills" / "requirement-analyst" / "SKILL.md").exists()


def test_init_exports_skills_to_agents_path_for_antigravity(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["1", "1,2,3", "3", "y"])  # antigravity

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert (target / ".agents" / "skills" / "requirement-analyst" / "SKILL.md").exists()


def test_init_exports_cursor_commands_without_frontmatter(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["3", "1,2,3", "3", "y"])  # cursor

    run_init(target_dir=str(target), amap_root=str(amap_root))

    native = target / ".cursor" / "commands" / "requirement-analyst.md"
    assert native.exists()
    content = native.read_text(encoding="utf-8")
    assert not content.startswith("---")
    assert "ABORT" in content  # pre_conditions on_fail text inlined


def test_init_generic_platform_creates_no_native_export_dirs(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["4", "1,2,3", "3", "y"])  # generic

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert not (target / ".claude").exists()
    assert not (target / ".agents").exists()
    assert not (target / ".cursor").exists()


def test_init_exports_workflow_with_synthesized_name(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])  # claude-code

    run_init(target_dir=str(target), amap_root=str(amap_root))

    native = target / ".claude" / "skills" / "task" / "SKILL.md"
    assert native.exists()
    assert "name: task" in native.read_text(encoding="utf-8")


def test_init_skips_workflow_tdd_native_export_without_frontmatter(
    tmp_path, amap_root, monkeypatch, capsys,
):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])  # claude-code

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert not (target / ".claude" / "skills" / "tdd").exists()
    out = capsys.readouterr().out
    assert "no frontmatter" in out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest cli/tests/test_init.py -v -k "native or codex or cursor_commands or generic_platform_creates or synthesized_name or skips_workflow_tdd"`
Expected: FAIL — `run_init` doesn't call `scaffold_native_skill_exports` yet, so none of the native paths exist; also `"5"` is not yet a valid platform index until Task 3's `codex` registration (already done by this point in the plan, so that part should work — only the export-call wiring is missing).

- [ ] **Step 3: Import in `init.py`**

Current (lines 10-16):

```python
from cli.scaffold import (
    load_manifest,
    scaffold_plugins,
    generate_resolved_config,
    verify_no_unresolved,
    sync_tree,
)
```

becomes:

```python
from cli.scaffold import (
    load_manifest,
    scaffold_plugins,
    scaffold_native_skill_exports,
    generate_resolved_config,
    verify_no_unresolved,
    sync_tree,
)
```

- [ ] **Step 4: Call it in `run_init`**

Current (lines 103-118):

```python
    staging = Path(tempfile.mkdtemp(prefix="amap-init-"))
    try:
        stats = scaffold_plugins(
            manifest.get("plugins", []), amap, staging, context, jinja_env,
            manifest.get("mcp_capabilities", {}), selected_mcps,
        )
        offenders = verify_no_unresolved(staging)
        if offenders:
            print("\n  ❌ Init aborted — unresolved template markers in:")
            for p in offenders:
                print(f"     • {p.relative_to(staging)}")
            print("  Target was NOT modified.")
            return
        sync_tree(staging, target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
```

becomes:

```python
    staging = Path(tempfile.mkdtemp(prefix="amap-init-"))
    try:
        stats = scaffold_plugins(
            manifest.get("plugins", []), amap, staging, context, jinja_env,
            manifest.get("mcp_capabilities", {}), selected_mcps,
        )
        scaffold_native_skill_exports(manifest.get("plugins", []), staging, platform)
        offenders = verify_no_unresolved(staging)
        if offenders:
            print("\n  ❌ Init aborted — unresolved template markers in:")
            for p in offenders:
                print(f"     • {p.relative_to(staging)}")
            print("  Target was NOT modified.")
            return
        sync_tree(staging, target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
```

(Runs against `staging`, before `verify_no_unresolved` — so native-exported files get the same unresolved-marker safety check as everything else, and an abort never touches `target`.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `/usr/bin/python3 -m pytest cli/tests/test_init.py -v`
Expected: all PASS (the full file, including pre-existing tests).

- [ ] **Step 6: Run the full suite**

Run: `/usr/bin/python3 -m pytest cli/ -q`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add cli/commands/init.py cli/tests/test_init.py
git commit -m "$(cat <<'EOF'
feat(cli): export native skills/commands during amap init

claude-code/codex/antigravity get verbatim mirrors at their native
skill folder; cursor gets frontmatter-stripped flat commands; generic
is unaffected. Runs inside the existing staging+verify safety net.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Wire into `amap update`, clean up stale native-export dirs on reconfigure

**Files:**
- Modify: `cli/commands/update.py:15-22` (import), `:52-58` (call), `:70-82` (reconfigure cleanup)
- Test: `cli/tests/test_update.py`

- [ ] **Step 1: Write the failing tests**

Append to `cli/tests/test_update.py`:

```python
def test_update_keeps_native_export_in_sync(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _init_claude(target, amap_root, monkeypatch)

    native = target / ".claude" / "skills" / "codebase-explorer" / "SKILL.md"
    native.write_text("tampered\n", encoding="utf-8")

    run_update(target_dir=str(target), amap_root=str(amap_root))

    assert "tampered" not in native.read_text(encoding="utf-8")


def test_reconfigure_removes_stale_native_export_dir(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _init_claude(target, amap_root, monkeypatch)
    assert (target / ".claude" / "skills" / "requirement-analyst" / "SKILL.md").exists()

    # Reconfigure to antigravity (platform=1).
    answers = iter(["1", "1,2,3", "3"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))
    run_update(target_dir=str(target), amap_root=str(amap_root), reconfigure=True)

    assert not (target / ".claude" / "skills").exists()
    assert (target / ".agents" / "skills" / "requirement-analyst" / "SKILL.md").exists()


def test_reconfigure_to_generic_removes_native_export_dir_without_creating_a_new_one(
    tmp_path, amap_root, monkeypatch,
):
    target = tmp_path / "proj"
    _init_claude(target, amap_root, monkeypatch)

    # Reconfigure to generic (platform=4).
    answers = iter(["4", "1,2,3", "3"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))
    run_update(target_dir=str(target), amap_root=str(amap_root), reconfigure=True)

    assert not (target / ".claude" / "skills").exists()
    assert not (target / ".agents").exists()
    assert not (target / ".cursor").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest cli/tests/test_update.py -v -k "native_export"`
Expected: FAIL — `run_update` doesn't call `scaffold_native_skill_exports`, so the first test's `native` file is never re-rendered (`"tampered"` survives); the reconfigure tests still find the stale `.claude/skills/` directory present.

- [ ] **Step 3: Import in `update.py`**

Current (lines 15-22):

```python
from cli.scaffold import (
    load_manifest,
    load_resolved_config,
    scaffold_plugins,
    verify_no_unresolved,
    sync_tree,
    generate_resolved_config,
)
```

becomes:

```python
from cli.scaffold import (
    load_manifest,
    load_resolved_config,
    scaffold_plugins,
    scaffold_native_skill_exports,
    verify_no_unresolved,
    sync_tree,
    generate_resolved_config,
)
```

- [ ] **Step 4: Call it in `run_update`**

Current (lines 52-58):

```python
    staging = Path(tempfile.mkdtemp(prefix="amap-update-"))
    try:
        scaffold_plugins(
            manifest.get("plugins", []), amap, staging, context, jinja_env,
            manifest.get("mcp_capabilities", {}), selected_mcps,
            only_framework=True,
        )
        offenders = verify_no_unresolved(staging)
```

becomes:

```python
    staging = Path(tempfile.mkdtemp(prefix="amap-update-"))
    try:
        scaffold_plugins(
            manifest.get("plugins", []), amap, staging, context, jinja_env,
            manifest.get("mcp_capabilities", {}), selected_mcps,
            only_framework=True,
        )
        scaffold_native_skill_exports(manifest.get("plugins", []), staging, platform)
        offenders = verify_no_unresolved(staging)
```

- [ ] **Step 5: Clean up stale native-export dirs on reconfigure**

Current tail (lines 70-82):

```python
    if reconfigure:
        generate_resolved_config(target, platform_key, selected_mcps, language)
        # Remove stale entry-point files left by the previous platform.
        current_entry = platform.config_entry_point
        for key in PLATFORMS:
            other_entry = get_platform(key).config_entry_point
            if other_entry != current_entry:
                stale = target / other_entry
                if stale.exists():
                    stale.unlink()
                    print(f"  🗑️  Removed stale entry point: {other_entry}")

    print(f"\n  ✅ Updated {count} framework files. User files preserved.\n")
```

becomes:

```python
    if reconfigure:
        generate_resolved_config(target, platform_key, selected_mcps, language)
        # Remove stale entry-point files left by the previous platform.
        current_entry = platform.config_entry_point
        for key in PLATFORMS:
            other_entry = get_platform(key).config_entry_point
            if other_entry != current_entry:
                stale = target / other_entry
                if stale.exists():
                    stale.unlink()
                    print(f"  🗑️  Removed stale entry point: {other_entry}")
        # Remove stale native skill/workflow export dirs left by the previous
        # platform. Scoped to exactly other_export["dir"] (e.g. ".claude/skills"),
        # never the parent dotdir (".claude/"), which may hold unrelated user
        # content (this repo's own .claude/settings.local.json, for example).
        current_export = platform.native_skill_export
        for key in PLATFORMS:
            other_export = get_platform(key).native_skill_export
            if other_export and other_export != current_export:
                stale_dir = target / other_export["dir"]
                if stale_dir.exists():
                    shutil.rmtree(stale_dir)
                    print(f"  🗑️  Removed stale native export dir: {other_export['dir']}")

    print(f"\n  ✅ Updated {count} framework files. User files preserved.\n")
```

(`shutil` is already imported at the top of `update.py`; `PLATFORMS`/`get_platform` are already imported.)

- [ ] **Step 6: Run tests to verify they pass**

Run: `/usr/bin/python3 -m pytest cli/tests/test_update.py -v`
Expected: all PASS (full file).

- [ ] **Step 7: Run the full suite**

Run: `/usr/bin/python3 -m pytest cli/ -q`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add cli/commands/update.py cli/tests/test_update.py
git commit -m "$(cat <<'EOF'
feat(cli): sync native skill exports on amap update, clean up on reconfigure

update now re-renders native exports the same way it re-renders
.amap/ framework files. Reconfigure additionally removes the previous
platform's native export directory (scoped to exactly that subdir,
never the parent dotdir, to avoid touching unrelated user content).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Final verification

- [ ] Run the complete suite once more: `/usr/bin/python3 -m pytest cli/ -q` — expect all green (28 pre-existing + 26 new = 54 tests).
- [ ] `git diff main -- .amap/procedures/bootstrap.md` shows no changes — confirms the spec's neutrality boundary (§3) held: nothing in this plan touched `bootstrap.md`.
- [ ] `grep -rn "native_skill_export" cli/platforms/` shows it defined in `base.py` and overridden in exactly `claude_code.py`, `antigravity.py`, `cursor.py`, `codex.py` — `generic.py` should NOT appear (per spec §7 item 5).
- [ ] Manual smoke test (optional):
  ```bash
  tmp=$(mktemp -d)
  printf '2\n1,2,3\n3\ny\n' | /usr/bin/python3 -c "from cli.commands.init import run_init; run_init('$tmp')"
  ls "$tmp/.claude/skills/requirement-analyst/SKILL.md"
  ls "$tmp/.claude/skills/task/SKILL.md"
  rm -rf "$tmp"
  ```
  Expect: both files exist.
- [ ] **Manual, before merge (per spec §6 risk 1 — cannot be automated in pytest):** run `amap init` for `claude-code` against a real scratch project, open it in an actual Claude Code session, and confirm the exported skills (e.g. `requirement-analyst`) appear in Claude Code's own skill list despite the extra `pre_conditions`/`version` frontmatter fields AMAP adds beyond `name`/`description`. If Claude Code's parser rejects or ignores skills with unexpected frontmatter keys, that invalidates the verbatim-mirror assumption in Task 6 and needs a follow-up fix before this ships.
