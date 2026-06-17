# Micro-loop Orchestrator (SP1b)

Rewrites Phase 3 into sequential clean-context task execution + extraction review.
Portable: a neutral filesystem contract + 3 execution tiers. The orchestrator logic
is platform-agnostic; `dispatch` is the only tier-specific seam.

## Contract artifacts (`.knowledge-layer/active/microloop/`)
- `TASK_QUEUE.md` — topo-sorted tasks + status (durable, resumable)
- `TASK_HANDOFF.md` — per-task input slice
- `TASK_RESULT.md` — per-task output
- `EXTRACTION_INPUT.md` / `EXTRACTION_REPORT.md` — HP-10/11

## Tiers (`.agent/profiles/execution-mode.yaml`)
`subagent` (Claude) · `fresh-session` (Cursor/Antigravity) · `inline-reload` (fallback).

## Run tests
    cd .agent/tools/microloop-orchestrator && python -m pytest tests/ -v
