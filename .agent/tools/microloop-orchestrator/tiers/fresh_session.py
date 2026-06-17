"""fresh-session tier (Cursor/Antigravity): executor runs in a NEW session/context.

dispatch() returns an instruction telling the user/host to open a fresh context and
run the executor procedure against the handoff. Clean context via session boundary."""


def dispatch(handoff_path, result_path):
    return (
        f"OPEN A NEW SESSION/CONTEXT and run .agent/procedures/executor.md against "
        f"{handoff_path}. The executor writes its outcome to {result_path}."
    )
