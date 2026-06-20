# Dashboard Control Tower Roadmap

> Ngày: 2026-06-19
> Mục tiêu: biến `amap dashboard serve` thành control tower cho agent chính, microloop và subagent.
> P3 branch hiện tại: `dashboard-p3-server`

## Current Baseline

Đã có:

- `amap dashboard serve`
- SSE local server bind `127.0.0.1`
- `/`, `/api/runs`, `/events`
- phase/ticket đọc từ `AGENT_TRANSPARENCY.md`
- progress đọc từ `microloop/TASK_QUEUE.md` nếu có
- subagent prompt đọc từ `TASK_HANDOFF.*.md`
- subagent result đọc từ `microloop/TASK_RESULT.*.md`
- parent brain đọc từ `PARENT_BRAIN.md`
- Antigravity best-effort brain sync qua `amap dashboard sync-brain`
- UI có animation spawn lane, prompt/result drawer, parent brain panel, event timeline

Vấn đề còn lại:

- Progress vẫn phụ thuộc `TASK_QUEUE.md`; Pha 1/Pha 2 không có queue nên đúng là chưa có `x/N`.
- Antigravity brain sync là best-effort vì IDE chỉ ghi text artifacts trong một số tình huống.
- Ảnh chụp/screenshot PR release chưa được đính kèm trong repo.

## Milestone P3.5: Stabilize Current Dashboard

Scope:

- Giữ server SSE hiện tại.
- Giữ UI subagent prompt animation.
- Đảm bảo no-cache/no-store cho static HTML.
- Chốt tests hiện có.

Done criteria:

- `/usr/bin/python3 -m pytest cli/tests/ -q` pass.
- Browser refresh thấy subagent prompt từ `TASK_HANDOFF.*.md`.
- `/events` gửi snapshot đầu tiên ngay khi connect.

Status: done on branch `dashboard-p3-server`.

## Milestone P4: Runtime Contract

Source spec:

- [dashboard-runtime-contract-design](../specs/2026-06-19-dashboard-runtime-contract-design.md)

Scope:

- Chuẩn hóa các artifact dashboard đọc:
  - `AGENT_TRANSPARENCY.md`
  - `microloop/TASK_QUEUE.md`
  - `TASK_HANDOFF.*.md`
  - `microloop/TASK_RESULT.*.md`
  - `microloop/ACTIVITY_LOG.jsonl`
- Mở rộng reader/server snapshot để trả:
  - `subagents[].status`
  - `subagents[].prompt`
  - `subagents[].result`
  - `events[]`
  - lỗi artifact theo dạng degrade an toàn
- Thêm fixture tests cho từng trạng thái.

Implementation tasks:

1. Add pure readers in `cli/dashboard/server.py` or split into `cli/dashboard/runtime.py` if file grows too large.
2. Add tests:
   - handoff-only project;
   - queue with pending/in_progress/done;
   - queue + result files;
   - activity log timeline;
   - malformed queue/log.
3. Keep `registry.py` untouched.
4. Keep `reader.py` backwards-compatible.

Done criteria:

- API snapshot has a stable schema for run, subagents, events.
- Dashboard shows handoff-only state without pretending progress exists.
- Dashboard shows true task progress when queue exists.

Status: done on branch `dashboard-p3-server`.

## Milestone P5: Emit Contract From Framework Workflows

Target:

- `BA-Framework` or any AMAP target project scaffolded with `.agents`.

Scope:

- Update workflow/tool instructions so Pha 3 creates `microloop/TASK_QUEUE.md` before dispatch.
- When subagent handoff files are written, also append `subagent_spawned` events.
- When work starts, append `subagent_started` or `task_started`.
- When a result is written, write `TASK_RESULT.*.md`, update queue status, append `subagent_done` or `task_done`.
- On failure, mark `blocked` and append a blocked event.

Implementation tasks:

1. Patch microloop-orchestrator docs/instructions to emit queue before dispatch.
2. Patch task workflow language so handoff-only state is transitional, not final.
3. Add fixture test in target framework if test harness exists.
4. Run one real Pha 3 task and verify dashboard transitions:
   - `0/2`
   - `1/2`
   - `2/2`

Done criteria:

- A real task shows live progress in the dashboard without manual file edits.
- Subagent nodes show prompt, status, and result.

Status: done on branch `dashboard-p3-server`.

## Milestone P6: UI V2

Scope:

- Turn the current card list into a mission-control view:
  - run header with phase ribbon;
  - progress bar and status badge;
  - animated subagent graph/lane;
  - prompt drawer;
  - result drawer;
  - event timeline;
  - stale/error badge.

Implementation tasks:

1. Refactor inline JS into small functions in `index.html`.
2. Preserve no-build, no-dependency static page.
3. Add DOM markers that tests can assert with plain HTTP fetch.
4. Verify mobile-ish narrow width and desktop width manually.

Done criteria:

- User can answer from the page alone:
  - What phase is this task in?
  - Which subagents were spawned?
  - What prompt did each receive?
  - Which one is running/done/blocked?
  - What result did each produce?

Status: done on branch `dashboard-p3-server`.

## Milestone P7: Reliability

Scope:

- Reconnect behavior.
- Malformed artifact handling.
- Long prompt/result handling.
- Many projects in registry.
- Deleted projects.
- Stale detection.

Implementation tasks:

1. Add stale/error fields per artifact.
2. Add max display height for prompt/result drawers.
3. Add timeline truncation or folding for long logs.
4. Add tests for bad JSONL and bad YAML.

Done criteria:

- One broken project/file never breaks other project cards.
- User sees the file path and short reason for stale/error.

Status: done on branch `dashboard-p3-server`.

## Milestone P8: Packaging And Release

Scope:

- Docs and PR polish.

Implementation tasks:

1. Update README or CLI docs for `amap dashboard serve`.
2. Add troubleshooting:
   - "Why is progress 0%?"
   - "Why do I see subagents but no task queue?"
   - "How do I verify SSE?"
3. Add manual acceptance checklist.
4. Open PR from `dashboard-p3-server`.

Done criteria:

- Fresh user can run the dashboard and understand each state.
- PR has tests, docs, and screenshots or terminal evidence.

Status: docs done on branch `dashboard-p3-server`; PR screenshot/evidence remains a release step.

## Recommended Next Move

Attach PR evidence: terminal output for `/api/runs` and `/events`, plus one browser screenshot
of a project with parent brain, subagent prompt/result, and event timeline.
