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
