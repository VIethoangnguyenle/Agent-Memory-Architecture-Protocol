# Dashboard Runtime Contract Design

> Ngày: 2026-06-19
> Trạng thái: draft đã chốt hướng sau P3 server
> Tiếp nối: [P3 Server + Web UI](2026-06-19-dashboard-p3-server-design.md)
> Roadmap: [dashboard-control-tower-roadmap](../plans/2026-06-19-dashboard-control-tower-roadmap.md)

## 1. Mục tiêu

Dashboard cần chuyển từ "đọc artifact rời rạc và suy luận" sang một runtime contract rõ ràng,
để khi agent chính sinh subagent, chạy task, fail gate, hoặc hoàn tất, UI thấy được ngay:

- phase hiện tại của task chính;
- progress thật `x/N`;
- subagent nào được spawn;
- prompt/handoff subagent nhận;
- trạng thái subagent: pending, running, done, blocked, stale;
- kết quả hoặc lỗi trả về;
- timeline event theo thứ tự thời gian.

Contract này vẫn là filesystem-first, local-only, không thêm dependency runtime mới cho dashboard.

## 2. Nguồn Dữ Liệu Chuẩn

| File | Vai trò | Người ghi | Dashboard đọc |
|------|---------|-----------|----------------|
| `AGENT_TRANSPARENCY.md` | phase, ticket, confidence, cảnh báo | workflow/task runner | có |
| `microloop/TASK_QUEUE.md` | danh sách task, status, active task, progress | microloop orchestrator | có |
| `TASK_HANDOFF.*.md` | prompt/handoff giao cho subagent | orchestrator | có |
| `microloop/TASK_HANDOFF.*.md` | prompt/handoff theo node khi Pha 3 chạy | orchestrator | có |
| `microloop/TASK_RESULT.*.md` | kết quả subagent hoặc node | subagent/orchestrator | có |
| `microloop/ACTIVITY_LOG.jsonl` | event timeline append-only | orchestrator và hooks | có |

Dashboard không ghi các file này.

## 3. Schema: `TASK_QUEUE.md`

`TASK_QUEUE.md` tiếp tục là YAML thuần.

```yaml
ticket_id: SME-TRANSFER-002
spec_path: openspec/changes/sme-transfer-002/tasks.md
execution_mode: subagent
tasks:
  - id: napas-human
    desc: Create human-readable SRS for Napas transfer
    status: in_progress
    depends_on: []
    handoff_path: .agents/knowledge/active/TASK_HANDOFF.napas-human.md
    result_path: .agents/knowledge/active/microloop/TASK_RESULT.napas-human.md
    started_at: "2026-06-19T23:50:00+07:00"
    updated_at: "2026-06-19T23:50:05+07:00"
  - id: napas-agent
    desc: Create agent-readable SRS for Napas transfer
    status: pending
    depends_on: []
    handoff_path: .agents/knowledge/active/TASK_HANDOFF.napas-agent.md
    result_path: .agents/knowledge/active/microloop/TASK_RESULT.napas-agent.md
```

Allowed task statuses:

- `pending`
- `in_progress`
- `done`
- `blocked`
- `stale`

Dashboard progress is:

- `tasks_total = len(tasks)`
- `tasks_done = count(status == "done")`
- `active_task = first in_progress.desc || first in_progress.id`
- `progress_pct = round(100 * tasks_done / tasks_total)`

## 4. Schema: `TASK_HANDOFF.*.md`

Handoff files are Markdown prompts. Dashboard treats the whole file as the prompt body and uses
the file name as the subagent id unless `TASK_QUEUE.md` provides a richer mapping.

Recommended structure:

```markdown
# TASK_HANDOFF.napas-human

## Task Objective
Create human-readable SRS for Napas transfer.

## Scope
- Write `output/srs-napas-transfer/human.md`.

## Constraints
- Follow `srs-checklist.md`.

## Expected Output
- A complete Markdown SRS.

## Verification
- Run checklist and report result.
```

## 5. Schema: `TASK_RESULT.*.md`

Result files are Markdown summaries written when a subagent/node finishes or blocks.

```markdown
# TASK_RESULT.napas-human

status: done
started_at: 2026-06-19T23:50:00+07:00
finished_at: 2026-06-19T23:55:00+07:00

## Summary
Created human-readable SRS.

## Changed Files
- output/srs-napas-transfer/human.md

## Verification
- srs-checklist: pass

## Notes
- No external links used.
```

Dashboard should show result summaries in a drawer beside the prompt drawer.

## 6. Schema: `ACTIVITY_LOG.jsonl`

Append-only JSON Lines. Each line is one event.

Required fields:

```json
{"ts":"2026-06-19T23:50:00+07:00","event":"subagent_spawned","ticket_id":"SME-TRANSFER-002","task_id":"napas-human","label":"Human SRS","path":".agents/knowledge/active/TASK_HANDOFF.napas-human.md"}
```

Event names:

- `phase_changed`
- `task_queue_created`
- `task_started`
- `task_done`
- `task_blocked`
- `subagent_spawned`
- `subagent_started`
- `subagent_done`
- `subagent_blocked`
- `gate_started`
- `gate_passed`
- `gate_failed`
- `result_written`

Dashboard treats unknown event names as generic timeline events and does not crash.

## 7. Reader Behavior

The dashboard reader should build a single project snapshot:

```json
{
  "name": "BA-Framework",
  "ticket_id": "SME-TRANSFER-002",
  "phase_state": "phase-3-in-progress",
  "tasks_total": 2,
  "tasks_done": 1,
  "active_task": "Create agent-readable SRS for Napas transfer",
  "progress_pct": 50,
  "subagents": [
    {
      "id": "napas-human",
      "name": "napas human",
      "status": "done",
      "prompt": "...",
      "result": "...",
      "handoff_path": "...",
      "result_path": "..."
    }
  ],
  "events": []
}
```

Priority rules:

1. If `TASK_QUEUE.md` exists, task/subagent status comes from it.
2. If handoff files exist but no queue exists, show subagents as `spawned` and phase-only progress.
3. If result exists but queue status is missing, infer result presence as `done` only for display, not for progress math.
4. Malformed artifact marks the run `stale` and adds an error badge; one bad file must not break the whole dashboard.

## 8. UI Requirements

P6 UI consumes this contract and displays:

- run card: phase, ticket, progress bar, updated time;
- subagent lane: animated spawn nodes, status badges, prompt drawer, result drawer;
- timeline: event stream from `ACTIVITY_LOG.jsonl`;
- stale/error indicators with file path and short message.

The UI must avoid showing `0/0 (0%)` when no `TASK_QUEUE.md` exists. It should say
`waiting for microloop TASK_QUEUE`.

## 9. Acceptance Criteria

- A fixture project with two `TASK_HANDOFF.*.md` files but no queue shows two spawned subagents and phase-only status.
- A fixture project with `TASK_QUEUE.md` containing two tasks shows `0/2`, then `1/2`, then `2/2` as statuses change.
- A fixture project with `TASK_RESULT.*.md` shows result drawers.
- A fixture project with `ACTIVITY_LOG.jsonl` shows a chronological timeline.
- Malformed queue/log/result files mark the project stale without crashing `/api/runs` or `/events`.

## 10. Out Of Scope

- Remote dashboard or non-local binding.
- Browser-to-agent control commands.
- Auth, multi-user, or WebSocket.
- Exact token accounting.
- Replacing the existing AMAP filesystem contract.
