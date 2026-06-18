"""Tests for the shared scaffolding core."""

import pytest
from jinja2 import TemplateSyntaxError

from cli.scaffold import (
    generate_resolved_config,
    load_manifest,
    load_resolved_config,
    resolved_config_candidates,
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
    assert p == amap_root / ".amap/skills/codebase-explorer/"


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
    config_path = target / ".amap" / "resolved-config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(content, encoding="utf-8")


def test_resolved_config_candidates_include_native_and_legacy_roots(tmp_path):
    candidates = [p.relative_to(tmp_path).as_posix() for p in resolved_config_candidates(tmp_path)]
    assert candidates == [
        ".agents/resolved-config.yaml",
        ".claude/resolved-config.yaml",
        ".amap/resolved-config.yaml",
    ]


def test_generate_resolved_config_uses_platform_framework_root(tmp_path):
    from cli.platforms import get_platform

    platform = get_platform("antigravity")
    generate_resolved_config(tmp_path, platform, ["socraticode"], "python")

    config = tmp_path / ".agents" / "resolved-config.yaml"
    assert config.exists()
    assert not (tmp_path / ".amap").exists()
    body = config.read_text(encoding="utf-8")
    assert "platform: antigravity" in body
    assert "framework_root: .agents" in body


def test_load_resolved_config_reads_agents_config(tmp_path):
    config = tmp_path / ".agents" / "resolved-config.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(
        "resolved:\n"
        "  platform: antigravity\n"
        "  framework_root: .agents\n"
        "  mcps: [socraticode]\n"
        "  language: python\n",
        encoding="utf-8",
    )

    resolved = load_resolved_config(tmp_path)
    assert resolved["platform"] == "antigravity"
    assert resolved["framework_root"] == ".agents"


def test_load_resolved_config_returns_dict_when_valid(tmp_path):
    _write_resolved_config(
        tmp_path,
        "resolved:\n  platform: claude-code\n  mcps: []\n  language: python\n",
    )
    resolved = load_resolved_config(tmp_path)
    assert resolved["platform"] == "claude-code"
    assert resolved["mcps"] == []
    assert resolved["language"] == "python"
    assert resolved["framework_root"] == ".claude"


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


def test_load_resolved_config_reads_legacy_amap_config(tmp_path):
    _write_resolved_config(
        tmp_path,
        "resolved:\n  platform: generic\n  mcps: []\n  language: python\n",
    )

    resolved = load_resolved_config(tmp_path)
    assert resolved["platform"] == "generic"
    assert resolved["framework_root"] == ".amap"


def test_verify_no_unresolved_flags_offending_py_file(tmp_path):
    # .py is not in scaffold's single-file render allowlist, but the
    # renderer's copy_and_render_directory does render .py files — so the
    # safety gate must scan it too, or an unresolved marker in a rendered
    # .py file would slip past verify_no_unresolved undetected.
    offending = tmp_path / "hook.py"
    offending.write_text("value = {{ tools.read_file }}\n", encoding="utf-8")

    offenders = verify_no_unresolved(tmp_path)

    assert offending in offenders


def test_verify_no_unresolved_flags_platform_entry_point(tmp_path):
    offending = tmp_path / "AGENTS.md"
    offending.write_text("rules {{ platform.config_entry_point }}\n", encoding="utf-8")

    offenders = verify_no_unresolved(tmp_path)

    assert offending in offenders


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
