"""Tests for the dashboard reader."""

import textwrap

from cli.dashboard.reader import RunState, read_run


def _make_project(tmp_path, *, transparency=None, queue=None):
    """Build a minimal Maika project under tmp_path with framework_root '.maika'."""
    root = tmp_path / ".maika"
    active = root / "knowledge" / "active"
    active.mkdir(parents=True)
    (root / "resolved-config.yaml").write_text(
        "resolved:\n"
        "  platform: antigravity\n"
        "  framework_root: .maika\n"
        "  language: python\n"
        "  framework_version: '3.0'\n",
        encoding="utf-8",
    )
    (tmp_path / "AGENTS.md").write_text("# agents\n", encoding="utf-8")
    if transparency is not None:
        (active / "AGENT_TRANSPARENCY.md").write_text(transparency, encoding="utf-8")
    if queue is not None:
        (active / "microloop").mkdir(parents=True)
        (active / "microloop" / "TASK_QUEUE.md").write_text(queue, encoding="utf-8")
    return tmp_path


TRANSPARENCY = textwrap.dedent(
    """\
    ---
    schema: agent-transparency/v1
    ticket_id: AUTH-feature
    phase_state: phase-3-in-progress
    ---
    # body
    """
)

QUEUE = textwrap.dedent(
    """\
    ticket_id: AUTH-feature
    spec_path: docs/spec.md
    execution_mode: subagent
    tasks:
      - id: T1
        desc: build login
        status: done
      - id: T2
        desc: wire DI
        status: in_progress
      - id: T3
        desc: tests
        status: pending
    """
)


def test_full_state(tmp_path):
    proj = _make_project(tmp_path, transparency=TRANSPARENCY, queue=QUEUE)
    state = read_run(str(proj))
    assert state.ticket_id == "AUTH-feature"
    assert state.phase_state == "phase-3-in-progress"
    assert state.tasks_total == 3
    assert state.tasks_done == 1
    assert state.active_task == "wire DI"
    assert state.progress_pct == 33
    assert state.stale is False


def test_missing_task_queue(tmp_path):
    proj = _make_project(tmp_path, transparency=TRANSPARENCY)
    state = read_run(str(proj))
    assert state.phase_state == "phase-3-in-progress"
    assert state.tasks_total == 0
    assert state.progress_pct == 0


def test_missing_transparency(tmp_path):
    proj = _make_project(tmp_path, queue=QUEUE)
    state = read_run(str(proj))
    assert state.phase_state is None
    assert state.tasks_total == 3
    # ticket falls back to the queue's ticket_id
    assert state.ticket_id == "AUTH-feature"


def test_no_active_run_is_idle(tmp_path):
    proj = _make_project(tmp_path)
    state = read_run(str(proj))
    assert state.phase_state is None
    assert state.tasks_total == 0
    assert state.progress_pct == 0


def test_malformed_queue_sets_stale(tmp_path):
    proj = _make_project(tmp_path, transparency=TRANSPARENCY, queue="tasks: [oops: : :")
    state = read_run(str(proj))
    assert state.stale is True
    assert state.tasks_total == 0


def test_zero_tasks_progress_is_zero(tmp_path):
    empty_queue = "ticket_id: X\nspec_path: s\nexecution_mode: subagent\ntasks: []\n"
    proj = _make_project(tmp_path, queue=empty_queue)
    state = read_run(str(proj))
    assert state.tasks_total == 0
    assert state.progress_pct == 0  # no ZeroDivisionError


def test_not_an_maika_project_is_idle(tmp_path):
    state = read_run(str(tmp_path))  # no resolved-config.yaml
    assert isinstance(state, RunState)
    assert state.phase_state is None
    assert state.tasks_total == 0
