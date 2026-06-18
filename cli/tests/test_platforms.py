"""Tests for platform adapter definitions."""

from cli.platforms.generic import GenericPlatform
from cli.platforms import get_platform


def test_generic_platform_has_no_native_skill_export():
    assert GenericPlatform().native_skill_export is None


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
