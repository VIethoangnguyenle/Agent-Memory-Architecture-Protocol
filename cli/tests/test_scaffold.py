"""Tests for the shared scaffolding core."""

import pytest
from jinja2 import TemplateSyntaxError

from cli.scaffold import (
    load_manifest,
    load_resolved_config,
    has_capability,
    get_ownership,
    resolve_source_path,
    scaffold_plugin,
    verify_no_unresolved,
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


def test_knowledge_dirs_are_user_owned(amap_root):
    manifest = load_manifest(amap_root)
    by_name = {p["name"]: p for p in manifest["plugins"]}
    assert get_ownership(by_name["knowledge-active-skeleton"]) == "user"
    assert get_ownership(by_name["knowledge-long-term"]) == "user"
    # Templates remain framework-managed.
    assert get_ownership(by_name["knowledge-templates"]) == "framework"


def _write_resolved_config(target, content):
    config_path = target / ".agent" / "resolved-config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(content, encoding="utf-8")


def test_load_resolved_config_returns_dict_when_valid(tmp_path):
    _write_resolved_config(
        tmp_path,
        "resolved:\n  platform: claude-code\n  mcps: []\n  language: python\n",
    )
    resolved = load_resolved_config(tmp_path)
    assert resolved == {"platform": "claude-code", "mcps": [], "language": "python"}


def test_load_resolved_config_returns_none_when_missing(tmp_path):
    assert load_resolved_config(tmp_path) is None


def test_load_resolved_config_returns_none_when_empty(tmp_path):
    _write_resolved_config(tmp_path, "")
    assert load_resolved_config(tmp_path) is None


def test_load_resolved_config_returns_none_when_only_comment(tmp_path):
    _write_resolved_config(tmp_path, "# just a comment\n")
    assert load_resolved_config(tmp_path) is None


def test_load_resolved_config_returns_none_when_resolved_not_dict(tmp_path):
    _write_resolved_config(tmp_path, "resolved: 3\n")
    assert load_resolved_config(tmp_path) is None


def test_load_resolved_config_returns_none_when_malformed_yaml(tmp_path):
    _write_resolved_config(tmp_path, "resolved:\n  - [unterminated\n")
    assert load_resolved_config(tmp_path) is None


def test_verify_no_unresolved_flags_offending_py_file(tmp_path):
    # .py is not in scaffold's single-file render allowlist, but the
    # renderer's copy_and_render_directory does render .py files — so the
    # safety gate must scan it too, or an unresolved marker in a rendered
    # .py file would slip past verify_no_unresolved undetected.
    offending = tmp_path / "hook.py"
    offending.write_text("value = {{ tools.read_file }}\n", encoding="utf-8")

    offenders = verify_no_unresolved(tmp_path)

    assert offending in offenders
