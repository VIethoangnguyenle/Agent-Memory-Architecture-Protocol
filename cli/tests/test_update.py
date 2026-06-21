"""Tests for maika update."""

from cli.commands.init import run_init
from cli.commands.update import run_update


def _answers(monkeypatch, seq):
    it = iter(seq)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(it))


def test_update_uses_resolved_framework_root(tmp_path, maika_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["1", "1,2,3", "3", "y"])
    run_init(target_dir=str(target), maika_root=str(maika_root))

    skill = target / ".agents" / "skills" / "codebase-explorer" / "SKILL.md"
    skill.write_text("tampered\n", encoding="utf-8")

    run_update(target_dir=str(target), maika_root=str(maika_root))

    assert "tampered" not in skill.read_text(encoding="utf-8")
    assert not (target / ".maika").exists()


def test_update_aborts_when_no_config(tmp_path, maika_root, capsys):
    target = tmp_path / "empty"
    target.mkdir()
    run_update(target_dir=str(target), maika_root=str(maika_root))
    assert "No Maika installation" in capsys.readouterr().out


def test_reconfigure_to_claude_writes_claude_root_and_warns_about_legacy_maika(
    tmp_path, maika_root, monkeypatch, capsys,
):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["3", "1,2,3", "3", "y"])
    run_init(target_dir=str(target), maika_root=str(maika_root))
    assert (target / ".maika").exists()

    _answers(monkeypatch, ["2", "1,2,3", "3"])
    run_update(target_dir=str(target), maika_root=str(maika_root), reconfigure=True)

    assert (target / ".claude" / "resolved-config.yaml").exists()
    assert (target / ".claude" / "skills" / "requirement-analyst" / "SKILL.md").exists()
    assert (target / ".maika").exists()
    assert "legacy .maika" in capsys.readouterr().out
