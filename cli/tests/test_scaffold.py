"""Tests for the shared scaffolding core."""

import pytest
from jinja2 import TemplateSyntaxError

from cli.scaffold import (
    load_manifest,
    has_capability,
    get_ownership,
    resolve_source_path,
    scaffold_plugin,
)


def test_get_ownership_defaults_to_framework():
    assert get_ownership({"name": "x"}) == "framework"
    assert get_ownership({"name": "x", "ownership": "user"}) == "user"


def test_load_manifest_has_plugins(amap_root):
    manifest = load_manifest(amap_root)
    assert len(manifest["plugins"]) > 0
    assert "mcp_capabilities" in manifest


def test_has_capability(amap_root):
    manifest = load_manifest(amap_root)
    caps = manifest["mcp_capabilities"]
    assert has_capability(["socraticode"], caps, "code_exploration") is True
    assert has_capability([], caps, "code_exploration") is False


def test_resolve_source_path_maps_skills(amap_root):
    p = resolve_source_path(amap_root, "skills/codebase-explorer/")
    assert p == amap_root / ".agent/skills/codebase-explorer/"


def test_scaffold_plugin_renders_template_source(tmp_path, jinja_env, claude_context):
    source_path = tmp_path / "x.md"
    source_path.write_text("use {{ tools.read_file }}", encoding="utf-8")
    target_path = tmp_path / "out" / "x.md"
    plugin = {"name": "x", "source": "x.md", "output": "x.md"}

    result = scaffold_plugin(plugin, source_path, target_path, claude_context, jinja_env)

    assert result["action"] == "rendered"
    assert target_path.exists()
    content = target_path.read_text(encoding="utf-8")
    assert "Read" in content
    assert "{{" not in content
    assert "}}" not in content


def test_scaffold_plugin_malformed_template_raises_not_swallowed(
    tmp_path, jinja_env, claude_context
):
    source_path = tmp_path / "x.md"
    source_path.write_text("broken {{ tools.read_file ", encoding="utf-8")
    target_path = tmp_path / "out" / "x.md"
    plugin = {"name": "x", "source": "x.md", "output": "x.md"}

    with pytest.raises(TemplateSyntaxError):
        scaffold_plugin(plugin, source_path, target_path, claude_context, jinja_env)
