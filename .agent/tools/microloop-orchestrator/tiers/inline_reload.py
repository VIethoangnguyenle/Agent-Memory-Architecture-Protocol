"""inline-reload tier (LCD): executor runs in the SAME session.

dispatch() returns an instruction string telling the agent to reload the handoff
slice (evicting stale exploration context from attention) and generate code for
this one task, then write TASK_RESULT. No Agent tool required."""


def dispatch(handoff_path, result_path):
    return (
        f"RELOAD the slice in {handoff_path} (drop prior exploration from attention). "
        f"Generate code for THIS task only, reading existing files from disk. "
        f"Then write the outcome to {result_path} per the TASK_RESULT schema."
    )
