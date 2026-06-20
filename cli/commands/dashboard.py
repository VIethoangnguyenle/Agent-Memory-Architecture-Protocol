"""amap dashboard — register projects and print a one-shot run progress snapshot.

Slice scope (P0-P2): no server. Subcommands:
  amap dashboard register   [--path DIR]   add a project (default: --target)
  amap dashboard unregister [--path DIR]   remove a project
  amap dashboard list                      list registered projects
  amap dashboard                           auto-add cwd, then print progress of all runs
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from cli.dashboard import registry
from cli.dashboard.reader import RunState, read_run


def run_dashboard(
    target: str = ".",
    action: Optional[str] = None,
    path: Optional[str] = None,
    port: int = 7077,
    no_browser: bool = False,
    brain_platform: str = "antigravity",
) -> None:
    if action == "serve":
        from cli.dashboard import server

        server.serve(target=target, port=port, open_browser=not no_browser)
        return

    if action == "sync-brain":
        from cli.dashboard import brain

        result = brain.sync_parent_brain(target, platform=brain_platform)
        if result.written:
            print(
                f"\n  ✓ Synced parent brain: {result.path}"
                f"\n    source: {result.source}"
                f"\n    artifacts: {result.artifact_count}\n"
            )
        else:
            print(f"\n  ⚠️  Parent brain not synced: {result.reason}\n")
        return

    reg = registry.default_registry_file()
    chosen = path or target

    if action == "register":
        added = registry.register(reg, chosen)
        label = "➕ Registered" if added else "✓ Already registered"
        print(f"\n  {label}: {Path(chosen).resolve()}\n")
        return

    if action == "unregister":
        removed = registry.unregister(reg, chosen)
        label = "➖ Unregistered" if removed else "⚠️  Not in registry"
        print(f"\n  {label}: {Path(chosen).resolve()}\n")
        return

    if action == "list":
        projects = registry.load(reg)
        print(f"\n  📋 Registered projects ({len(projects)}):")
        for p in projects:
            print(f"     • {p}")
        print()
        return

    # default: drop deleted projects, auto-add cwd, then snapshot every registered run
    registry.prune_missing(reg)
    registry.register(reg, target)
    projects = registry.load(reg)
    print(f"\n  📊 AMAP runs ({len(projects)} project(s)):\n")
    for p in projects:
        _print_run(read_run(p))
    print()


def _print_run(state: RunState) -> None:
    name = Path(state.project_path).name
    if state.phase_state is None and state.tasks_total == 0:
        print(f"     • {name}: idle (no active run)")
        return
    filled = state.progress_pct // 10
    bar = "█" * filled + "░" * (10 - filled)
    phase = state.phase_state or "?"
    active = f" → {state.active_task}" if state.active_task else ""
    stale = " [stale]" if state.stale else ""
    print(
        f"     • {name}: {bar} {state.tasks_done}/{state.tasks_total} "
        f"({state.progress_pct}%) · {phase}{active}{stale}"
    )
