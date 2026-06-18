"""Tests for amap init."""

import pytest

from cli.commands.init import (
    parse_multi_values,
    prompt_multi_checkbox,
    prompt_single_checkbox,
    resolve_init_choices,
    run_init,
)
from cli.scaffold import load_manifest


def _answers(monkeypatch, seq):
    it = iter(seq)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(it))


def test_prompt_single_checkbox_returns_default_on_enter(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")
    assert prompt_single_checkbox("Choose", ["A", "B"], default=1) == "B"


def test_prompt_single_checkbox_accepts_number(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *a, **k: "1")
    assert prompt_single_checkbox("Choose", ["A", "B"], default=1) == "A"


def test_prompt_single_checkbox_requires_choice_when_default_is_none(monkeypatch):
    answers = iter(["", "2"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))

    assert prompt_single_checkbox("Choose", ["A", "B"], default=None) == "B"


def test_prompt_multi_checkbox_returns_empty_on_enter(monkeypatch):
    choices = [{"key": "a", "display": "A"}, {"key": "b", "display": "B"}]
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")
    assert prompt_multi_checkbox("MCPs", choices) == []


def test_prompt_multi_checkbox_accepts_comma_numbers(monkeypatch):
    choices = [{"key": "a", "display": "A"}, {"key": "b", "display": "B"}]
    monkeypatch.setattr("builtins.input", lambda *a, **k: "1,2")
    assert prompt_multi_checkbox("MCPs", choices) == ["a", "b"]


def test_parse_multi_values_accepts_repeated_and_comma_values():
    assert parse_multi_values(["socraticode,confluence", "db-remote"]) == [
        "socraticode",
        "confluence",
        "db-remote",
    ]


def test_resolve_init_choices_accepts_complete_non_interactive_options(amap_root):
    manifest = load_manifest(amap_root)

    platform_key, selected_mcps, language = resolve_init_choices(
        manifest,
        platform_key="generic",
        selected_mcps=["socraticode", "confluence"],
        language="python",
        assume_yes=True,
    )

    assert platform_key == "generic"
    assert selected_mcps == ["socraticode", "confluence"]
    assert language == "python"


def test_resolve_init_choices_rejects_yes_with_missing_required_options(amap_root):
    manifest = load_manifest(amap_root)

    with pytest.raises(ValueError) as exc:
        resolve_init_choices(
            manifest,
            platform_key="generic",
            selected_mcps=[],
            language=None,
            assume_yes=True,
        )

    assert "--yes requires --platform and --language" in str(exc.value)


def test_resolve_init_choices_rejects_invalid_platform(amap_root):
    manifest = load_manifest(amap_root)

    with pytest.raises(ValueError) as exc:
        resolve_init_choices(
            manifest,
            platform_key="unknown",
            selected_mcps=[],
            language="python",
            assume_yes=True,
        )

    assert "Unknown platform" in str(exc.value)


def test_run_init_non_interactive_generic(tmp_path, amap_root):
    target = tmp_path / "proj"

    run_init(
        target_dir=str(target),
        amap_root=str(amap_root),
        platform_key="generic",
        selected_mcps=[],
        language="other",
        assume_yes=True,
    )

    assert (target / ".amap" / "resolved-config.yaml").exists()
    assert (target / "AGENTS.md").exists()


def test_init_antigravity_uses_agents_as_only_framework_root(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["1", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert not (target / ".amap").exists()
    assert (target / ".agents" / "resolved-config.yaml").exists()
    assert (target / ".agents" / "rules" / "RULES.md").exists()
    assert (target / ".agents" / "skills" / "requirement-analyst" / "SKILL.md").exists()
    assert (target / ".agents" / "knowledge" / "long-term" / "author-dna.yaml").exists()
    assert (target / "AGENTS.md").exists()


def test_init_codex_uses_agents_as_only_framework_root(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["4", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert not (target / ".amap").exists()
    assert (target / ".agents" / "resolved-config.yaml").exists()
    assert (target / ".agents" / "skills" / "requirement-analyst" / "SKILL.md").exists()


def test_init_claude_uses_claude_as_only_framework_root(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert not (target / ".amap").exists()
    assert (target / ".claude" / "resolved-config.yaml").exists()
    assert (target / ".claude" / "rules" / "RULES.md").exists()
    assert (target / ".claude" / "skills" / "requirement-analyst" / "SKILL.md").exists()
    assert (target / "CLAUDE.md").exists()


def test_init_generic_keeps_amap_framework_root(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["3", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert (target / ".amap" / "resolved-config.yaml").exists()
    assert (target / ".amap" / "skills" / "requirement-analyst" / "SKILL.md").exists()
    assert not (target / ".agents").exists()
    assert not (target / ".claude" / "skills").exists()


def test_init_aborts_on_unresolved_marker(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"

    def fake_scaffold(plugins, amap, write_root, *a, **k):
        (write_root / "bad.md").write_text("{{ leftover }}\n", encoding="utf-8")
        return {"rendered": 0, "copied": 1, "dirs": 0, "skipped": 0}

    monkeypatch.setattr("cli.commands.init.scaffold_plugins", fake_scaffold)
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert not (target / "CLAUDE.md").exists()
    assert not (target / ".claude").exists()
    assert not (target / ".amap").exists()


def test_init_templatizes_entry_point_references(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    entry = (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert "{{ " not in entry

    rules = (target / ".claude" / "rules" / "RULES.md").read_text(encoding="utf-8")
    assert "CLAUDE.md" in rules
    assert "AGENTS.md" not in rules

    boot = (target / ".claude" / "procedures" / "bootstrap.md").read_text(encoding="utf-8")
    assert "AGENTS.md" not in boot


def test_antigravity_rendered_framework_files_do_not_reference_active_amap_paths(
    tmp_path, amap_root, monkeypatch,
):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["1", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    offenders = []
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".yaml", ".yml", ".txt"} and path.name != "AGENTS.md":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if ".amap/" in text and "legacy .amap" not in text and "source repo" not in text:
            offenders.append(path.relative_to(target).as_posix())
    assert offenders == []


def test_codex_rendered_framework_files_do_not_reference_active_amap_paths(
    tmp_path, amap_root, monkeypatch,
):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["4", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    offenders = []
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".yaml", ".yml", ".txt"} and path.name != "AGENTS.md":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if ".amap/" in text and "legacy .amap" not in text and "source repo" not in text:
            offenders.append(path.relative_to(target).as_posix())
    assert offenders == []


def test_claude_code_rendered_framework_files_do_not_reference_active_amap_paths(
    tmp_path, amap_root, monkeypatch,
):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    offenders = []
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".yaml", ".yml", ".txt"} and path.name != "AGENTS.md":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if ".amap/" in text and "legacy .amap" not in text and "source repo" not in text:
            offenders.append(path.relative_to(target).as_posix())
    assert offenders == []


def test_init_next_steps_use_platform_framework_root(tmp_path, amap_root, monkeypatch, capsys):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["1", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    out = capsys.readouterr().out
    assert "Customize .agents/knowledge/long-term/persona.yaml" in out
    assert ".amap/knowledge/long-term/persona.yaml" not in out


def test_cli_init_forwards_non_interactive_options(monkeypatch, tmp_path):
    from cli import amap

    captured = {}

    def fake_run_init(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("cli.commands.init.run_init", fake_run_init)
    monkeypatch.setattr(
        "sys.argv",
        [
            "amap",
            "init",
            "--target",
            str(tmp_path),
            "--platform",
            "generic",
            "--mcp",
            "socraticode,confluence",
            "--language",
            "python",
            "--yes",
        ],
    )

    amap.main()

    assert captured["target_dir"] == str(tmp_path)
    assert captured["platform_key"] == "generic"
    assert captured["selected_mcps"] == ["socraticode", "confluence"]
    assert captured["language"] == "python"
    assert captured["assume_yes"] is True
