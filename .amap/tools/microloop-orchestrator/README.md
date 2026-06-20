# Micro-loop Orchestrator (SP1b)

Rewrites Phase 3 into sequential clean-context task execution + extraction review.
Portable: a neutral filesystem contract + 3 execution tiers. The orchestrator logic
is platform-agnostic; `dispatch` is the only tier-specific seam.

## Contract artifacts (`{{ platform.framework_root }}/knowledge/active/microloop/`)
- `TASK_QUEUE.md` — topo-sorted tasks + status (durable, resumable)
- `TASK_HANDOFF.md` — per-task input slice
- `TASK_RESULT.md` — per-task output
- `PARENT_BRAIN.md` — dashboard-visible mirror of the parent IDE brain/conversation
- `EXTRACTION_INPUT.md` / `EXTRACTION_REPORT.md` — HP-10/11
- `ACTIVITY_LOG.jsonl` — append-only dashboard timeline (`task_queue_created`,
  `subagent_spawned`, `subagent_started`, `result_written`, `subagent_done`,
  `subagent_blocked`, plus parent-agent events such as `phase_changed`,
  `parent_note`, `parent_brain_updated`, `archive_started`)

## Dashboard runtime helpers
Use these helpers from `orchestrator.py` when running Phase 3 so
`amap dashboard serve` can show live progress:

- `initialize_runtime_queue(active_dir, ticket_id, spec_path, tasks, framework_root="{{ platform.framework_root }}")`
- `write_task_handoff(active_dir, task_id, prompt, label=None)`
- `update_task_status(active_dir, task_id, status, event=None)`
- `write_task_result(active_dir, task_id, body, status="done")`
- `append_activity_event(active_dir, event, **fields)`
- `record_parent_event(active_dir, event, phase=None, summary=None, **fields)`
- `write_parent_brain(active_dir, body, source="ide-brain-mirror", append=False, **fields)`

## Tiers (`{{ platform.framework_root }}/profiles/execution-mode.yaml`)
`subagent` (Claude) · `fresh-session` (Cursor/Antigravity) · `inline-reload` (fallback).

## Run tests
    cd {{ platform.framework_root }}/tools/microloop-orchestrator && python -m pytest tests/ -v
