"""Tests for amap status."""

from cli.commands.init import run_init
from cli.commands.status import run_status


def _answers(monkeypatch, seq):
    it = iter(seq)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(it))


def test_status_detects_claude_code_install(tmp_path, amap_root, monkeypatch, capsys):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])  # claude-code
    run_init(target_dir=str(target), amap_root=str(amap_root))
    capsys.readouterr()  # drop init output

    run_status(target_dir=str(target))

    out = capsys.readouterr().out
    assert "No AMAP installation" not in out
    assert "claude-code" in out


def test_status_detects_legacy_install(tmp_path, capsys):
    # Legacy install: AGENTS.md present, no resolved-config.yaml.
    target = tmp_path / "legacy"
    target.mkdir()
    (target / "AGENTS.md").write_text("# legacy\n", encoding="utf-8")

    run_status(target_dir=str(target))

    out = capsys.readouterr().out
    assert "No AMAP installation" not in out
    assert "legacy installation" in out
