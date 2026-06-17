# Procedure: Executor (one micro-loop task)

> Consumed by the agent acting as code-executor. Input: a TASK_HANDOFF.md path.
> Output: TASK_RESULT.md. Platform-neutral — same steps on every tier.

1. Read the TASK_HANDOFF at the given path. Note: task, dna_slice, spec_slice,
   snapshot_slice, written_files, boundary, feedback.
2. Read the actual existing files listed in `written_files` FROM DISK (not just the
   summaries) so inheritance is consistent.
3. Generate code for THIS task ONLY. Obey:
   - dna_slice.hard_principles (REJECT_* = hard) and complexity_thresholds.
   - boundary constraints — do not touch listed files/packages.
   - If `feedback` is present (a retry), fix exactly what it reports.
4. Write changed files to disk.
5. Write TASK_RESULT.md: task_id, changed_files (path/change_type/summary),
   gate_status left as "PENDING" (orchestrator fills it), self_flagged for anything
   you are unsure about.
6. Stop. Do NOT advance to the next task — the orchestrator owns the loop.
