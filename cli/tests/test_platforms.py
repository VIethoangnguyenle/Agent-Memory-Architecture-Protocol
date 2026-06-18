"""Tests for platform adapter definitions."""

from cli.platforms import PLATFORMS, get_platform
from cli.platforms.generic import GenericPlatform


def test_platform_framework_roots():
    assert get_platform("antigravity").framework_root == ".agents"
    assert get_platform("codex").framework_root == ".agents"
    assert get_platform("claude-code").framework_root == ".claude"
    assert get_platform("generic").framework_root == ".amap"


def test_native_root_platforms_do_not_need_skill_mirror():
    assert get_platform("antigravity").native_skill_export is None
    assert get_platform("codex").native_skill_export is None
    assert get_platform("claude-code").native_skill_export is None


def test_render_context_includes_framework_root():
    ctx = get_platform("antigravity").build_render_context(["socraticode"], "python")
    assert ctx["platform"]["framework_root"] == ".agents"


def test_cursor_is_out_of_scope_for_platform_selection():
    assert "cursor" not in PLATFORMS


def test_generic_platform_defaults_to_amap_root():
    assert GenericPlatform().framework_root == ".amap"
    assert GenericPlatform().native_skill_export is None
