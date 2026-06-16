"""subagent tier (Claude Code): executor runs as a dispatched Agent-tool subagent.

dispatch() returns the subagent prompt. The host (Claude Code) is responsible for
spawning the Agent with this prompt; full context isolation."""


def dispatch(handoff_path, result_path):
    return (
        f"You are a code-executor subagent. Read {handoff_path}, read existing files "
        f"from disk, generate code for the single task only, respect boundary constraints, "
        f"then write {result_path} per the TASK_RESULT schema."
    )
