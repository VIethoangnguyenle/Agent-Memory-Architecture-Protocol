"""Tests for platform adapter definitions."""

import pytest

from cli.platforms import PLATFORMS, get_platform
from cli.platforms.base import (
    REQUIRED_TOOL_KEYS,
    BasePlatform,
    PlatformToolMappingError,
)
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


def test_all_platforms_define_required_tool_keyset():
    for key, cls in PLATFORMS.items():
        platform = cls()
        missing = REQUIRED_TOOL_KEYS - set(platform.tool_mapping) - platform.unsupported_tools
        extra_unsupported = platform.unsupported_tools - REQUIRED_TOOL_KEYS
        assert missing == set(), f"{key} missing tool mappings: {sorted(missing)}"
        assert extra_unsupported == set(), (
            f"{key} declares unknown unsupported tools: {sorted(extra_unsupported)}"
        )


def test_build_render_context_fails_on_missing_required_tool_mapping():
    class BrokenPlatform(BasePlatform):
        name = "broken"
        display_name = "Broken"
        config_entry_point = "AGENTS.md"
        tool_mapping = {"read_file": "Read"}

    with pytest.raises(PlatformToolMappingError) as exc:
        BrokenPlatform().build_render_context([], "python")

    message = str(exc.value)
    assert "broken" in message
    assert "missing required tool mappings" in message
    assert "write_file" in message


def test_get_tool_fails_for_unknown_required_operation():
    platform = get_platform("generic")

    with pytest.raises(PlatformToolMappingError) as exc:
        platform.get_tool("not_a_real_tool")

    assert "not_a_real_tool" in str(exc.value)
