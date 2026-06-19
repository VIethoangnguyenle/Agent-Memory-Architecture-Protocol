"""Tests for the amap dashboard command + wiring."""

from cli.commands.dashboard import run_dashboard
from cli.dashboard import registry


def test_register_then_list(tmp_path, capsys, monkeypatch):
    reg = tmp_path / "projects.yaml"
    monkeypatch.setattr(registry, "default_registry_file", lambda: reg)
    proj = tmp_path / "projA"
    proj.mkdir()

    run_dashboard(target=str(proj), action="register")
    run_dashboard(action="list")

    out = capsys.readouterr().out
    assert "Registered" in out
    assert str(proj.resolve()) in out


def test_default_snapshot_auto_adds_cwd_and_prints_idle(tmp_path, capsys, monkeypatch):
    reg = tmp_path / "projects.yaml"
    monkeypatch.setattr(registry, "default_registry_file", lambda: reg)
    # a bare dir that is not an AMAP project → idle line, no crash
    run_dashboard(target=str(tmp_path))

    out = capsys.readouterr().out
    assert "AMAP runs" in out
    assert "idle" in out
    assert registry.load(reg) == [str(tmp_path.resolve())]
