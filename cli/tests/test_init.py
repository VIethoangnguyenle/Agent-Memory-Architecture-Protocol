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
    assert not (target / ".agent").exists()


def test_init_templatizes_entry_point_references(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])  # claude-code

    run_init(target_dir=str(target), amap_root=str(amap_root))

    entry = (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert "CLAUDE.md" in entry
    assert "AGENTS.md" not in entry
    assert "{{ " not in entry

    rules = (target / ".agent" / "rules" / "RULES.md").read_text(encoding="utf-8")
    assert "CLAUDE.md" in rules
    assert "AGENTS.md" not in rules

    boot = (target / ".agent" / "procedures" / "bootstrap.md").read_text(encoding="utf-8")
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


