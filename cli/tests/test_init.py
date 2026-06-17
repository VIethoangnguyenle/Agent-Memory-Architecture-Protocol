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

