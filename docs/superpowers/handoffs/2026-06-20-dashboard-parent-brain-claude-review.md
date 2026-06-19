# Dashboard Parent Brain - Claude Review Handoff

Date: 2026-06-20
Branch: `dashboard-p3-server`
Primary commit: `ac8cab6 feat: surface parent brain in dashboard`

## Goal

Make the dashboard show the parent agent's own working context, not only subagent
handoffs/results. The intended source of truth is the IDE brain/conversation with
the human. AMAP now exposes a dashboard-readable mirror file so runtime-specific
IDE adapters can sync into one stable contract.

## What Changed

- Added dashboard reader support for `PARENT_BRAIN.md` and fallback
  `PARENT_CONVERSATION.md`.
- Added `parent_brain` to `/api/runs` snapshots with:
  - `source`
  - `path`
  - `content`
  - `updated_at`
- Added a UI panel named `parent brain`, separate from:
  - subagent prompt/result drawers
  - event timeline
- Added orchestrator helper:
  - `write_parent_brain(active_dir, body, source="ide-brain-mirror", append=False, **fields)`
- Added `parent_brain_updated` activity event emitted as `actor: parent`.
- Updated Phase 3 workflow instructions so parent context is mirrored from IDE
  brain/conversation at apply start and after important parent decisions.
- Updated runtime contract documentation.

## Files To Review

- `cli/dashboard/server.py`
  - `_read_parent_brain`
  - `_parent_brain_source`
  - `read_runtime` response shape
- `cli/dashboard/static/index.html`
  - `parentBrain(r)` rendering
  - placement inside idle, phase-only, and task-progress cards
- `.amap/tools/microloop-orchestrator/orchestrator.py`
  - `write_parent_brain`
  - event emission behavior
- `.amap/workflows/task.md`
  - new Phase 3 parent brain mirror requirement
- `cli/tests/test_dashboard_server.py`
  - `test_snapshot_includes_parent_brain_mirror`
  - static UI marker assertion
- `.amap/tools/microloop-orchestrator/tests/test_runtime_contract.py`
  - helper/event contract assertion
- `docs/superpowers/specs/2026-06-19-dashboard-runtime-contract-design.md`
  - source-of-truth language and API schema

## Verification Run

Passed:

```bash
/usr/bin/python3 -m pytest cli/tests/ -q
# 148 passed

cd .amap/tools/microloop-orchestrator
/usr/bin/python3 -m pytest tests/ -q
# 61 passed
```

Runtime smoke:

```bash
/usr/bin/python3 -m cli.amap dashboard serve --port 7077 --target /home/zane/Desktop/BA-Framework
```

`/api/runs` confirmed for `BA-Framework`:

- progress: `2/2 100%`
- `parent_brain`: `true`
- source: `antigravity-brain-mirror`
- tail event includes: `parent_brain_updated`

Dashboard URL used during smoke test:

```text
http://127.0.0.1:7077/
```

## BA-Framework Runtime Note

The framework update was synced into `/home/zane/Desktop/BA-Framework` with:

```bash
/usr/bin/python3 -m cli.amap update --target /home/zane/Desktop/BA-Framework --source /home/zane/Desktop/agent-memory-arch-v3
```

User-owned active/long-term knowledge was preserved. A runtime mirror was written
to:

```text
/home/zane/Desktop/BA-Framework/.agents/knowledge/active/PARENT_BRAIN.md
```

This file is runtime state in the target project, not part of this repo commit.

## Review Questions

- Is `PARENT_BRAIN.md` the right stable mirror name, or should the contract prefer
  `PARENT_CONVERSATION.md` as the canonical name?
- Should dashboard parse additional frontmatter/metadata later, or is the current
  `source:` line enough for the P6 UI?
- Should `write_parent_brain(..., append=True)` preserve/update metadata on append,
  or should append remain a raw continuation for now?
- Should future Antigravity/Codex/Claude adapters live in a new dashboard adapter
  module, or inside the microloop orchestrator helper layer?

## Suggested Next Step

Implement an Antigravity best-effort sync adapter that reads a stable local
conversation/brain source when available and writes the task-relevant summary into
`PARENT_BRAIN.md`. The dashboard contract and UI are already ready for that.
