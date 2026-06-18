"""Tests for amap init."""

from cli.commands.init import run_init


def _answers(monkeypatch, seq):
    it = iter(seq)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(it))


def test_init_writes_platform_entry_point_filename(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])  # claude-code

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert (target / "CLAUDE.md").exists()
    assert not (target / "AGENTS.md").exists()


def test_init_aborts_on_unresolved_marker(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"

    def fake_scaffold(plugins, amap, write_root, *a, **k):
        (write_root / "bad.md").write_text("{{ leftover }}\n", encoding="utf-8")
        return {"rendered": 0, "copied": 1, "dirs": 0, "skipped": 0}

    monkeypatch.setattr("cli.commands.init.scaffold_plugins", fake_scaffold)
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])  # claude-code

    run_init(target_dir=str(target), amap_root=str(amap_root))

    # Aborted before syncing — target was never written.
    assert not (target / "CLAUDE.md").exists()
    assert not (target / ".amap").exists()


def test_init_templatizes_entry_point_references(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])  # claude-code

    run_init(target_dir=str(target), amap_root=str(amap_root))

    entry = (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert "CLAUDE.md" in entry
    assert "AGENTS.md" not in entry
    assert "{{ " not in entry

    rules = (target / ".amap" / "rules" / "RULES.md").read_text(encoding="utf-8")
    assert "CLAUDE.md" in rules
    assert "AGENTS.md" not in rules

    boot = (target / ".amap" / "procedures" / "bootstrap.md").read_text(encoding="utf-8")
    assert "AGENTS.md" not in boot


def test_e2e_cursor_platform(tmp_path, amap_root, monkeypatch, capsys):
    from cli.commands.status import run_status
    from cli.commands.update import run_update

    target = tmp_path / "proj"
    _answers(monkeypatch, ["3", "1,2", "2", "y"])  # cursor, socraticode+confluence, typescript

    run_init(target_dir=str(target), amap_root=str(amap_root))

    # 1. Entry-point file is .cursorrules
    assert (target / ".cursorrules").exists()
    assert not (target / "AGENTS.md").exists()
    assert not (target / "CLAUDE.md").exists()

    # 2. Entry-point self-references correctly
    content = (target / ".cursorrules").read_text(encoding="utf-8")
    assert ".cursorrules" in content
    assert "AGENTS.md" not in content
    assert "{{ " not in content

    # 3. Status detects the install
    capsys.readouterr()
    run_status(target_dir=str(target))
    out = capsys.readouterr().out
    assert "No AMAP installation" not in out
    assert "cursor" in out

    # 4. Reconfigure to antigravity cleans up .cursorrules
    answers = iter(["1", "1,2", "2"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))
    run_update(target_dir=str(target), amap_root=str(amap_root), reconfigure=True)

    assert (target / "AGENTS.md").exists()
    assert not (target / ".cursorrules").exists()


def test_init_exports_skills_to_claude_native_path(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])  # claude-code

    run_init(target_dir=str(target), amap_root=str(amap_root))

    native = target / ".claude" / "skills" / "requirement-analyst" / "SKILL.md"
    assert native.exists()
    canonical = target / ".amap" / "skills" / "requirement-analyst" / "SKILL.md"
    assert native.read_text(encoding="utf-8") == canonical.read_text(encoding="utf-8")


def test_init_exports_skills_to_agents_path_for_codex(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["5", "1,2,3", "3", "y"])  # codex

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert (target / "AGENTS.md").exists()
    assert (target / ".agents" / "skills" / "requirement-analyst" / "SKILL.md").exists()


def test_init_exports_skills_to_agents_path_for_antigravity(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["1", "1,2,3", "3", "y"])  # antigravity

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert (target / ".agents" / "skills" / "requirement-analyst" / "SKILL.md").exists()


def test_init_exports_cursor_commands_without_frontmatter(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["3", "1,2,3", "3", "y"])  # cursor

    run_init(target_dir=str(target), amap_root=str(amap_root))

    native = target / ".cursor" / "commands" / "requirement-analyst.md"
    assert native.exists()
    content = native.read_text(encoding="utf-8")
    assert not content.startswith("---")
    assert "ABORT" in content  # pre_conditions on_fail text inlined


def test_init_generic_platform_creates_no_native_export_dirs(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["4", "1,2,3", "3", "y"])  # generic

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert not (target / ".claude").exists()
    assert not (target / ".agents").exists()
    assert not (target / ".cursor").exists()


def test_init_exports_workflow_with_synthesized_name(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])  # claude-code

    run_init(target_dir=str(target), amap_root=str(amap_root))

    native = target / ".claude" / "skills" / "task" / "SKILL.md"
    assert native.exists()
    assert "name: task" in native.read_text(encoding="utf-8")


def test_init_skips_workflow_tdd_native_export_without_frontmatter(
    tmp_path, amap_root, monkeypatch, capsys,
):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])  # claude-code

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert not (target / ".claude" / "skills" / "tdd").exists()
    out = capsys.readouterr().out
    assert "no frontmatter" in out


