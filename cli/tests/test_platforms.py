"""Tests for platform adapter definitions."""

import pytest

from cli.platforms import PLATFORMS, get_platform
from cli.platforms.base import (
    OPTIONAL_TOOL_KEYS,
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


def test_write_gate_hook_capability_matrix():
    assert get_platform("claude-code").capabilities["write_gate_hook"] is True
    assert get_platform("codex").capabilities["write_gate_hook"] is True
    assert get_platform("antigravity").capabilities["write_gate_hook"] is True
    assert get_platform("generic").capabilities["write_gate_hook"] is False


def test_cursor_is_out_of_scope_for_platform_selection():
    assert "cursor" not in PLATFORMS


def test_generic_platform_defaults_to_amap_root():
    assert GenericPlatform().framework_root == ".amap"
    assert GenericPlatform().native_skill_export is None


def test_all_platforms_define_required_tool_keyset():
    for key, cls in PLATFORMS.items():
        platform = cls()
        missing = REQUIRED_TOOL_KEYS - set(platform.tool_mapping) - platform.unsupported_tools
        extra = set(platform.tool_mapping) - REQUIRED_TOOL_KEYS - OPTIONAL_TOOL_KEYS
        extra_unsupported = platform.unsupported_tools - REQUIRED_TOOL_KEYS
        assert missing == set(), f"{key} missing tool mappings: {sorted(missing)}"
        assert extra == set(), f"{key} declares unknown tool mappings: {sorted(extra)}"
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


def test_build_render_context_allows_declared_optional_tool_mappings():
    class OptionalToolPlatform(BasePlatform):
        name = "optional-tools"
        display_name = "Optional Tools"
        config_entry_point = "AGENTS.md"
        tool_mapping = {
            **{key: key.upper() for key in REQUIRED_TOOL_KEYS},
            **{key: key.upper() for key in OPTIONAL_TOOL_KEYS},
        }

    context = OptionalToolPlatform().build_render_context([], "python")

    assert context["tools"]["browser_agent"] == "BROWSER_AGENT"
    assert context["tools"]["generate_image"] == "GENERATE_IMAGE"


def test_build_render_context_fails_on_unknown_extra_tool_mapping():
    class ExtraToolPlatform(BasePlatform):
        name = "extra-tools"
        display_name = "Extra Tools"
        config_entry_point = "AGENTS.md"
        tool_mapping = {
            **{key: key.upper() for key in REQUIRED_TOOL_KEYS},
            "surprise_tool": "SURPRISE_TOOL",
        }

    with pytest.raises(PlatformToolMappingError) as exc:
        ExtraToolPlatform().build_render_context([], "python")

    message = str(exc.value)
    assert "extra-tools" in message
    assert "unknown tool mappings" in message
    assert "surprise_tool" in message


def test_get_tool_fails_for_unknown_required_operation():
    platform = get_platform("generic")

    with pytest.raises(PlatformToolMappingError) as exc:
        platform.get_tool("not_a_real_tool")

    assert "not_a_real_tool" in str(exc.value)


def test_all_platforms_map_db_query():
    for key, cls in PLATFORMS.items():
        assert "db_query" in cls().tool_mapping, f"{key} missing db_query mapping"


def test_db_query_resolves_in_render_context():
    ctx = get_platform("claude-code").build_render_context(["db-remote"], "python")
    assert ctx["tools"]["db_query"] == "db-remote"
