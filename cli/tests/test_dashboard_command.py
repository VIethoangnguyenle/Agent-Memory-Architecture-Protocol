"""Tests for the maika dashboard command + wiring."""

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
    # a bare dir that is not an Maika project → idle line, no crash
    run_dashboard(target=str(tmp_path))

    out = capsys.readouterr().out
    assert "Maika runs" in out
    assert "idle" in out
    assert registry.load(reg) == [str(tmp_path.resolve())]


def test_print_run_renders_active_and_stale(capsys):
    from cli.commands.dashboard import _print_run
    from cli.dashboard.reader import RunState

    state = RunState(
        project_path="/tmp/projX",
        phase_state="phase-3-in-progress",
        tasks_total=4,
        tasks_done=2,
        active_task="wire DI",
        stale=True,
    )
    _print_run(state)

    out = capsys.readouterr().out
    assert "projX" in out
    assert "2/4" in out
    assert "(50%)" in out
    assert "→ wire DI" in out
    assert "[stale]" in out
    assert "█████░░░░░" in out  # filled = 50 // 10 = 5


def test_register_dedup_message(tmp_path, capsys, monkeypatch):
    reg = tmp_path / "projects.yaml"
    monkeypatch.setattr(registry, "default_registry_file", lambda: reg)
    proj = tmp_path / "projA"
    proj.mkdir()

    run_dashboard(target=str(proj), action="register")
    capsys.readouterr()  # clear first registration output
    run_dashboard(target=str(proj), action="register")

    assert "Already registered" in capsys.readouterr().out


def test_unregister_messages(tmp_path, capsys, monkeypatch):
    reg = tmp_path / "projects.yaml"
    monkeypatch.setattr(registry, "default_registry_file", lambda: reg)
    proj = tmp_path / "projA"
    proj.mkdir()

    run_dashboard(target=str(proj), action="register")
    capsys.readouterr()
    run_dashboard(target=str(proj), action="unregister")
    assert "Unregistered" in capsys.readouterr().out

    run_dashboard(target=str(proj), action="unregister")
    assert "Not in registry" in capsys.readouterr().out


def test_default_snapshot_prunes_deleted_projects(tmp_path, capsys, monkeypatch):
    reg = tmp_path / "projects.yaml"
    monkeypatch.setattr(registry, "default_registry_file", lambda: reg)
    gone = tmp_path / "gone"
    gone.mkdir()
    run_dashboard(target=str(gone), action="register")
    gone.rmdir()
    capsys.readouterr()  # clear

    here = tmp_path / "here"
    here.mkdir()
    run_dashboard(target=str(here))  # default snapshot from an existing dir

    projects = registry.load(reg)
    assert str(gone.resolve()) not in projects
    assert str(here.resolve()) in projects


def test_serve_action_dispatches(monkeypatch):
    calls = {}

    def fake_serve(target=".", port=7077, open_browser=True):
        calls.update(target=target, port=port, open_browser=open_browser)

    import cli.dashboard.server as server_mod

    monkeypatch.setattr(server_mod, "serve", fake_serve)

    run_dashboard(target="/tmp/x", action="serve", port=9000, no_browser=True)

    assert calls == {"target": "/tmp/x", "port": 9000, "open_browser": False}


def test_sync_brain_action_dispatches(monkeypatch, capsys):
    calls = {}

    class Result:
        written = True
        reason = "ok"
        path = "/tmp/x/.agents/knowledge/active/PARENT_BRAIN.md"
        source = "antigravity-brain"
        artifact_count = 2

    def fake_sync_parent_brain(target, platform="antigravity"):
        calls.update(target=target, platform=platform)
        return Result()

    import cli.dashboard.brain as brain_mod

    monkeypatch.setattr(brain_mod, "sync_parent_brain", fake_sync_parent_brain)

    run_dashboard(target="/tmp/x", action="sync-brain", brain_platform="antigravity")

    out = capsys.readouterr().out
    assert calls == {"target": "/tmp/x", "platform": "antigravity"}
    assert "Synced parent brain" in out
    assert "antigravity-brain" in out
