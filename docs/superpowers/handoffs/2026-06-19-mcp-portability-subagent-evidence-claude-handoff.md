# Claude Handoff — MCP Portability + Subagent Evidence

**Date:** 2026-06-19
**Branch:** `mcp-portability-subagent-evidence`
**Worktree:** `/home/zane/Desktop/Agent-Memory-Architecture-Protocol/.worktrees/mcp-portability-subagent-evidence`
**Plan:** `docs/superpowers/plans/2026-06-19-mcp-portability-subagent-evidence.md`
**Spec:** `docs/superpowers/specs/2026-06-19-mcp-portability-subagent-evidence-design.md`

## Current State

Implementation was stopped intentionally because context was running low.
All completed work is committed on the branch. The worktree was clean before this handoff file was added.

Baseline before implementation:

- `pytest cli/tests .maika/tools/gate-check/tests .maika/hooks/write-gate/tests -q`
- Result: `121 passed in 2.91s`

## Completed Tasks

### Task 1 — Platform MCP Adapter Contract

Commits:

- `cde7023 feat: add platform mcp adapter contract`

Review:

- Task-scoped review approved.
- Residual note: downstream wiring was out of scope and handled by later tasks.

Tests:

- `pytest cli/tests/test_mcp_adapters.py -v`
- Result: `5 passed`

### Task 2 — MCP Config Parsing And Redaction

Commits:

- `b10d390 feat: load and redact mcp configs`
- `90df922 fix: remove tomli fallback dependency`

Review:

- Initial review found two issues:
  - undeclared `tomli` fallback dependency for older supported Python runtimes,
  - ordinary values under `env` were not redacted.
- Fix review approved.

Tests:

- `pytest cli/tests/test_mcp_config.py -v`
- Result after fix: `6 passed`

### Task 3 — Standalone MCP Bridge Tool

Commits:

- `5d19bb0 Add standalone MCP bridge tool`
- `439c7e7 Fix MCP bridge handshake and legacy SSE fallback`
- `5ad9307 Fix MCP bridge HTTP endpoint resolution`

Review:

- Initial review found protocol issues:
  - missing `notifications/initialized`,
  - narrow HTTP/SSE transport support,
  - stdio missing response could report false success,
  - stdio stderr pipe could deadlock.
- Second review found direct `url` POST regression and missing HTTP sequence test.
- Final review approved.

Tests:

- `pytest cli/tests/test_mcp_bridge.py -v`
- Result after final fix: `8 passed`

### Task 4 — MCP Doctor Report-Only Mode

Commits:

- `4bde571 feat: add mcp doctor report mode`
- `beff217 fix: tighten mcp doctor summary states`

Review:

- Initial review found misleading report states:
  - `native_state` reported `configured` for partial MCP matches,
  - `bridge_state` reported `unavailable` even when no bridge probe ran.
- Fix review approved.

Tests:

- `pytest cli/tests/test_mcp_doctor.py -v`
- Result after fix: `4 passed`
- CLI smoke used `python3 -m cli.maika doctor mcp --help` because `python` was not available in this shell.

## Next Task

Resume at **Task 5: Safe MCP Doctor Fix Mode** in:

`docs/superpowers/plans/2026-06-19-mcp-portability-subagent-evidence.md`

Task 5 expected scope:

- Modify `cli/mcp/doctor.py`
- Modify `cli/commands/doctor.py`
- Modify `cli/tests/test_mcp_doctor.py`
- Implement safe Antigravity config copy/backup fix behavior only under `maika doctor mcp --fix`.
- Keep fix behavior opt-in via `--yes` or interactive confirmation.
- Do not broaden into scaffold, runtime rules, subagent gates, or write-gate work yet.

Recommended first command:

```bash
pytest cli/tests/test_mcp_doctor.py -v
```

Then follow Task 5 from the plan using TDD.

## Remaining Plan Tasks

- Task 5: Safe MCP Doctor Fix Mode
- Task 6: Scaffold MCP Bridge And Init Hint
- Task 7: Subagent Evidence Artifacts And Gate Validators
- Task 8: Runtime Rules For MCP Doctor, Bridge Fallback, And Subagent Review
- Task 9: Antigravity Write-Gate `TargetFile` Support
- Task 10: README And Full Verification

## Important Constraints To Preserve

- Commit as each task or task-fix completes.
- Keep native MCP as preferred path; bridge is diagnostic/fallback only.
- `maika init/update` must not mutate user MCP config.
- Config edits require `maika doctor mcp --fix` plus `--yes` or explicit confirmation.
- Reports must not print secrets, headers, tokens, or raw environment values.
- Subagents must not be the first actor to probe MCP.
- Orchestrator must review subagent output before accepting code.

## Main Checkout Note

The original checkout at `/home/zane/Desktop/Agent-Memory-Architecture-Protocol` had unrelated pre-existing changes when this branch started:

- deleted `TODOS.md`
- deleted `TODOS2.md`
- untracked `maika_setup_mcp_proposal.md`

Those were not touched or staged in this worktree.
