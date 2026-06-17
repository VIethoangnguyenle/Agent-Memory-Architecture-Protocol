"""Tests for amap update."""

from pathlib import Path

import pytest

from cli.commands.init import run_init
from cli.commands.update import run_update


def _init_claude(target, amap_root, monkeypatch):
    # Feed prompts: platform=2 (claude-code), MCPs=1,2,3, language=3, confirm=y
    answers = iter(["2", "1,2,3", "3", "y"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))
    run_init(target_dir=str(target), amap_root=str(amap_root))


def test_update_preserves_user_file_rerenders_framework(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _init_claude(target, amap_root, monkeypatch)

    # User edits a user-owned file and a framework file.
    persona = target / ".knowledge-layer" / "long-term" / "persona.yaml"
    persona.write_text("MY CUSTOM PERSONA\n", encoding="utf-8")
    skill = target / ".agent" / "skills" / "codebase-explorer" / "SKILL.md"
    skill.write_text("user tampered\n", encoding="utf-8")

    run_update(target_dir=str(target), amap_root=str(amap_root))

    # User file untouched.
    assert persona.read_text(encoding="utf-8") == "MY CUSTOM PERSONA\n"
    # Framework file re-rendered (overwritten) with real tool names, no markers.
    body = skill.read_text(encoding="utf-8")
    assert "user tampered" not in body
    assert "mcp__socraticode__codebase_search" in body
    assert "{{ " not in body


def test_update_aborts_when_no_config(tmp_path, amap_root, capsys):
    target = tmp_path / "empty"
    target.mkdir()
    run_update(target_dir=str(target), amap_root=str(amap_root))
    assert "No AMAP installation" in capsys.readouterr().out


def test_reconfigure_switches_platform_keeps_user_files(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _init_claude(target, amap_root, monkeypatch)

    persona = target / ".knowledge-layer" / "long-term" / "persona.yaml"
    persona.write_text("KEEP ME\n", encoding="utf-8")

    skill = target / ".agent" / "skills" / "codebase-explorer" / "SKILL.md"
    assert "mcp__socraticode__codebase_search" in skill.read_text(encoding="utf-8")

    # Reconfigure to antigravity (platform=1), MCPs=1,2,3, language=3.
    answers = iter(["1", "1,2,3", "3"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))
    run_update(target_dir=str(target), amap_root=str(amap_root), reconfigure=True)

    body = skill.read_text(encoding="utf-8")
    # Antigravity uses single-underscore MCP prefix.
    assert "mcp_socraticode_codebase_search" in body
    assert "mcp__socraticode__codebase_search" not in body
    assert persona.read_text(encoding="utf-8") == "KEEP ME\n"

    # resolved-config now records antigravity.
    cfg = (target / ".agent" / "resolved-config.yaml").read_text(encoding="utf-8")
    assert "antigravity" in cfg
