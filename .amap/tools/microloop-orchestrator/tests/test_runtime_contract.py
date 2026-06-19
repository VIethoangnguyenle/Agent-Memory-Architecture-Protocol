from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import orchestrator  # noqa: E402


def test_runtime_contract_emits_queue_handoff_result_and_events(tmp_path):
    active = tmp_path / ".agents" / "knowledge" / "active"
    active.mkdir(parents=True)
    tasks = [
        {"id": "napas-agent", "desc": "Create agent SRS", "depends_on": ["napas-human"]},
        {"id": "napas-human", "desc": "Create human SRS", "depends_on": []},
    ]

    queue = orchestrator.initialize_runtime_queue(
        active,
        ticket_id="SME-TRANSFER-002",
        spec_path="openspec/changes/sme-transfer-002/tasks.md",
        tasks=tasks,
        framework_root=".agents",
    )
    orchestrator.record_parent_event(
        active,
        "phase_changed",
        phase="phase-3-in-progress",
        summary="Parent entered apply phase.",
        ticket_id="SME-TRANSFER-002",
    )
    orchestrator.write_task_handoff(active, "napas-human", "# TASK_HANDOFF.napas-human\n")
    orchestrator.write_task_handoff(active, "napas-agent", "# TASK_HANDOFF.napas-agent\n")
    orchestrator.update_task_status(active, "napas-human", "in_progress", event="subagent_started")
    orchestrator.write_task_result(active, "napas-human", "# TASK_RESULT.napas-human\n\nstatus: done\n")

    loaded = orchestrator.load_runtime_queue(active)
    statuses = {task["id"]: task["status"] for task in loaded["tasks"]}
    events = [
        json.loads(line)
        for line in (active / "microloop" / "ACTIVITY_LOG.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert [task["id"] for task in queue["tasks"]] == ["napas-human", "napas-agent"]
    assert statuses == {"napas-human": "done", "napas-agent": "pending"}
    assert (active / "TASK_HANDOFF.napas-human.md").exists()
    assert (active / "microloop" / "TASK_RESULT.napas-human.md").exists()
    assert loaded["tasks"][0]["handoff_path"] == ".agents/knowledge/active/TASK_HANDOFF.napas-human.md"
    assert loaded["tasks"][0]["result_path"] == ".agents/knowledge/active/microloop/TASK_RESULT.napas-human.md"
    assert [event["event"] for event in events] == [
        "task_queue_created",
        "phase_changed",
        "subagent_spawned",
        "subagent_spawned",
        "subagent_started",
        "result_written",
        "subagent_done",
    ]
    assert events[0]["actor"] == "parent"
    assert events[1]["actor"] == "parent"
    assert events[2]["actor"] == "subagent"


def test_update_task_status_rejects_unknown_task(tmp_path):
    active = tmp_path / ".agents" / "knowledge" / "active"
    active.mkdir(parents=True)
    orchestrator.initialize_runtime_queue(
        active,
        ticket_id="X",
        spec_path="p",
        tasks=[{"id": "T1", "desc": "one", "depends_on": []}],
    )

    try:
        orchestrator.update_task_status(active, "NOPE", "done")
    except ValueError as exc:
        assert "not in queue" in str(exc)
    else:
        raise AssertionError("expected ValueError")
