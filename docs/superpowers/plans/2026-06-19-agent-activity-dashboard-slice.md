# Agent Activity Dashboard — Slice P0–P2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `amap` a real terminal command and ship a one-shot CLI that prints live progress (phase, x/N tasks, active task) for one or more registered AMAP projects — the de-risking vertical slice before any web server.

**Architecture:** Read-only. A `Registry` (YAML at `~/.amap/projects.yaml`) lists projects to observe. A pure `Reader` parses each project's existing contract files (`AGENT_TRANSPARENCY.md` frontmatter + `microloop/TASK_QUEUE.md` YAML) into a `RunState`. A thin `dashboard` CLI command ties them together. No server, no new runtime dependency.

**Tech Stack:** Python 3.9+, `pyyaml` (already a dep), stdlib `argparse`, `pytest` (run via `/usr/bin/python3 -m pytest`).

**Spec:** [docs/superpowers/specs/2026-06-19-agent-activity-dashboard-design.md](../specs/2026-06-19-agent-activity-dashboard-design.md)

**Branch:** `agent-activity-dashboard`

---

## File Structure

| File | Create/Modify | Responsibility |
|------|---------------|----------------|
| `install.sh` | Modify | P0: editable-install the CLI + symlink `amap` onto PATH |
| `cli/dashboard/__init__.py` | Create | package marker |
| `cli/dashboard/registry.py` | Create | P1: load/save/register/unregister/prune the project registry |
| `cli/dashboard/reader.py` | Create | P2: parse contract files → `RunState` (pure) |
| `cli/commands/dashboard.py` | Create | CLI entry: register/unregister/list + one-shot snapshot |
| `cli/amap.py` | Modify | wire the `dashboard` subcommand |
| `cli/tests/test_dashboard_registry.py` | Create | registry unit tests |
| `cli/tests/test_dashboard_reader.py` | Create | reader unit tests |
| `cli/tests/test_dashboard_command.py` | Create | command/wiring test |

**Reuse (DRY, per eng-review):** `cli.scaffold.load_resolved_config` resolves project → `framework_root`. TASK_QUEUE is "the file IS the yaml" (see [contract.py](../../../.amap/tools/microloop-orchestrator/contract.py) docstring), so the Reader loads it with `yaml.safe_load` directly — `contract.py` lives inside each *target* project's framework root, not on the `cli` import path, so importing it is not viable; loading the YAML is the same operation, not a duplicated parser.

---

## Task 1: P0 — make `amap` a terminal command

**Files:**
- Modify: `install.sh` (insert after the `PY="$VENV/bin/python"` line, before the init/update routing)

- [ ] **Step 1: Read the current install.sh routing block**

Run: `sed -n '30,50p' install.sh`
Expected: see `PY="$VENV/bin/python"` followed by the `if [ -f ... resolved-config.yaml ]` routing.

- [ ] **Step 2: Insert editable install + symlink**

Find this exact line in `install.sh`:

```bash
PY="$VENV/bin/python"
```

Insert immediately after it:

```bash

# Install the amap CLI as an editable package and expose it on PATH.
# pyproject.toml declares the console script: amap = cli.amap:main
"$VENV/bin/pip" install --quiet -e "$AMAP_ROOT"
mkdir -p "$HOME/.local/bin"
ln -sf "$VENV/bin/amap" "$HOME/.local/bin/amap"
echo "→ Installed 'amap' → $HOME/.local/bin/amap"
echo "  (ensure ~/.local/bin is on your PATH: export PATH=\"\$HOME/.local/bin:\$PATH\")"
```

- [ ] **Step 3: Run the installer against this repo and verify the command resolves**

Run: `./install.sh "$(pwd)" && "$HOME/.local/bin/amap" --version`
Expected: prints `amap 3.0.0` (the version from `cli/__init__.py`). No traceback.

- [ ] **Step 4: Commit**

```bash
git add install.sh
git commit -m "feat: install amap CLI as console script via install.sh + symlink"
```

---

## Task 2: P1 — project registry

**Files:**
- Create: `cli/dashboard/__init__.py`
- Create: `cli/dashboard/registry.py`
- Test: `cli/tests/test_dashboard_registry.py`

- [ ] **Step 1: Create the package marker**

Create `cli/dashboard/__init__.py`:

```python
"""AMAP dashboard: read-only observability over AMAP run artifacts."""
```

- [ ] **Step 2: Write the failing tests**

Create `cli/tests/test_dashboard_registry.py`:

```python
"""Tests for the dashboard project registry."""

from cli.dashboard import registry


def test_register_adds_absolute_path(tmp_path):
    reg = tmp_path / "projects.yaml"
    proj = tmp_path / "projA"
    proj.mkdir()

    added = registry.register(reg, str(proj))

    assert added is True
    assert registry.load(reg) == [str(proj.resolve())]


def test_register_is_idempotent(tmp_path):
    reg = tmp_path / "projects.yaml"
    proj = tmp_path / "projA"
    proj.mkdir()

    assert registry.register(reg, str(proj)) is True
    assert registry.register(reg, str(proj)) is False
    assert registry.load(reg) == [str(proj.resolve())]


def test_unregister_removes(tmp_path):
    reg = tmp_path / "projects.yaml"
    proj = tmp_path / "projA"
    proj.mkdir()
    registry.register(reg, str(proj))

    assert registry.unregister(reg, str(proj)) is True
    assert registry.load(reg) == []


def test_unregister_absent_returns_false(tmp_path):
    reg = tmp_path / "projects.yaml"
    assert registry.unregister(reg, str(tmp_path / "nope")) is False


def test_prune_missing_drops_deleted_dirs(tmp_path):
    reg = tmp_path / "projects.yaml"
    gone = tmp_path / "gone"
    gone.mkdir()
    registry.register(reg, str(gone))
    gone.rmdir()

    removed = registry.prune_missing(reg)

    assert removed == [str(gone.resolve())]
    assert registry.load(reg) == []


def test_load_missing_file_returns_empty(tmp_path):
    assert registry.load(tmp_path / "does-not-exist.yaml") == []


def test_load_malformed_returns_empty(tmp_path):
    reg = tmp_path / "projects.yaml"
    reg.write_text("{ not: valid: yaml:", encoding="utf-8")
    assert registry.load(reg) == []
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest cli/tests/test_dashboard_registry.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cli.dashboard.registry'`

- [ ] **Step 4: Implement the registry**

Create `cli/dashboard/registry.py`:

```python
"""AMAP dashboard registry: which projects the dashboard observes.

Stored as YAML at $AMAP_HOME/projects.yaml (default ~/.amap/projects.yaml):

    projects:
      - /abs/path/to/projectA
      - /abs/path/to/projectB

All functions take the registry file path explicitly so they are pure and
testable; the CLI passes default_registry_file().
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml


def default_registry_file() -> Path:
    home = Path(os.environ.get("AMAP_HOME", Path.home() / ".amap"))
    return home / "projects.yaml"


def load(registry_file: Path) -> list[str]:
    if not registry_file.exists():
        return []
    try:
        data = yaml.safe_load(registry_file.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    if not isinstance(data, dict):
        return []
    projects = data.get("projects", [])
    return [p for p in projects if isinstance(p, str)]


def save(registry_file: Path, projects: list[str]) -> None:
    registry_file.parent.mkdir(parents=True, exist_ok=True)
    registry_file.write_text(
        yaml.safe_dump({"projects": projects}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def register(registry_file: Path, project_path: str) -> bool:
    """Add an absolute project path. Returns True if added, False if already present."""
    abs_path = str(Path(project_path).resolve())
    projects = load(registry_file)
    if abs_path in projects:
        return False
    projects.append(abs_path)
    save(registry_file, projects)
    return True


def unregister(registry_file: Path, project_path: str) -> bool:
    """Remove a project path. Returns True if removed, False if absent."""
    abs_path = str(Path(project_path).resolve())
    projects = load(registry_file)
    if abs_path not in projects:
        return False
    projects.remove(abs_path)
    save(registry_file, projects)
    return True


def prune_missing(registry_file: Path) -> list[str]:
    """Drop entries whose directory no longer exists. Returns the removed paths."""
    projects = load(registry_file)
    keep = [p for p in projects if Path(p).is_dir()]
    removed = [p for p in projects if p not in keep]
    if removed:
        save(registry_file, keep)
    return removed
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `/usr/bin/python3 -m pytest cli/tests/test_dashboard_registry.py -v`
Expected: PASS (7 passed)

- [ ] **Step 6: Commit**

```bash
git add cli/dashboard/__init__.py cli/dashboard/registry.py cli/tests/test_dashboard_registry.py
git commit -m "feat: add dashboard project registry"
```

---

## Task 3: P2 — Reader (contract files → RunState)

**Files:**
- Create: `cli/dashboard/reader.py`
- Test: `cli/tests/test_dashboard_reader.py`

- [ ] **Step 1: Write the failing tests**

Create `cli/tests/test_dashboard_reader.py`:

```python
"""Tests for the dashboard reader."""

import textwrap

from cli.dashboard.reader import RunState, read_run


def _make_project(tmp_path, *, transparency=None, queue=None):
    """Build a minimal AMAP project under tmp_path with framework_root '.amap'."""
    root = tmp_path / ".amap"
    active = root / "knowledge" / "active"
    active.mkdir(parents=True)
    (root / "resolved-config.yaml").write_text(
        "resolved:\n"
        "  platform: antigravity\n"
        "  framework_root: .amap\n"
        "  language: python\n"
        "  framework_version: '3.0'\n",
        encoding="utf-8",
    )
    (tmp_path / "AGENTS.md").write_text("# agents\n", encoding="utf-8")
    if transparency is not None:
        (active / "AGENT_TRANSPARENCY.md").write_text(transparency, encoding="utf-8")
    if queue is not None:
        (active / "microloop").mkdir(parents=True)
        (active / "microloop" / "TASK_QUEUE.md").write_text(queue, encoding="utf-8")
    return tmp_path


TRANSPARENCY = textwrap.dedent(
    """\
    ---
    schema: agent-transparency/v1
    ticket_id: AUTH-feature
    phase_state: phase-3-in-progress
    ---
    # body
    """
)

QUEUE = textwrap.dedent(
    """\
    ticket_id: AUTH-feature
    spec_path: docs/spec.md
    execution_mode: subagent
    tasks:
      - id: T1
        desc: build login
        status: done
      - id: T2
        desc: wire DI
        status: in_progress
      - id: T3
        desc: tests
        status: pending
    """
)


def test_full_state(tmp_path):
    proj = _make_project(tmp_path, transparency=TRANSPARENCY, queue=QUEUE)
    state = read_run(str(proj))
    assert state.ticket_id == "AUTH-feature"
    assert state.phase_state == "phase-3-in-progress"
    assert state.tasks_total == 3
    assert state.tasks_done == 1
    assert state.active_task == "wire DI"
    assert state.progress_pct == 33
    assert state.stale is False


def test_missing_task_queue(tmp_path):
    proj = _make_project(tmp_path, transparency=TRANSPARENCY)
    state = read_run(str(proj))
    assert state.phase_state == "phase-3-in-progress"
    assert state.tasks_total == 0
    assert state.progress_pct == 0


def test_missing_transparency(tmp_path):
    proj = _make_project(tmp_path, queue=QUEUE)
    state = read_run(str(proj))
    assert state.phase_state is None
    assert state.tasks_total == 3
    # ticket falls back to the queue's ticket_id
    assert state.ticket_id == "AUTH-feature"


def test_no_active_run_is_idle(tmp_path):
    proj = _make_project(tmp_path)
    state = read_run(str(proj))
    assert state.phase_state is None
    assert state.tasks_total == 0
    assert state.progress_pct == 0


def test_malformed_queue_sets_stale(tmp_path):
    proj = _make_project(tmp_path, transparency=TRANSPARENCY, queue="tasks: [oops: : :")
    state = read_run(str(proj))
    assert state.stale is True
    assert state.tasks_total == 0


def test_zero_tasks_progress_is_zero(tmp_path):
    empty_queue = "ticket_id: X\nspec_path: s\nexecution_mode: subagent\ntasks: []\n"
    proj = _make_project(tmp_path, queue=empty_queue)
    state = read_run(str(proj))
    assert state.tasks_total == 0
    assert state.progress_pct == 0  # no ZeroDivisionError


def test_not_an_amap_project_is_idle(tmp_path):
    state = read_run(str(tmp_path))  # no resolved-config.yaml
    assert isinstance(state, RunState)
    assert state.phase_state is None
    assert state.tasks_total == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest cli/tests/test_dashboard_reader.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cli.dashboard.reader'`

- [ ] **Step 3: Implement the reader**

Create `cli/dashboard/reader.py`:

```python
"""AMAP dashboard reader: parse a project's contract files into a RunState.

Reads (read-only) from {project}/{framework_root}/knowledge/active/:
  - AGENT_TRANSPARENCY.md    (YAML frontmatter: phase_state, ticket_id)
  - microloop/TASK_QUEUE.md  (pure YAML: tasks[].status)

Token parsing (TOKEN_LOG.md markdown tables) is out of slice scope; `tokens`
stays None. Activity timeline (ACTIVITY_LOG.jsonl) is P5+ and not read here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from cli.scaffold import load_resolved_config


@dataclass
class RunState:
    project_path: str
    ticket_id: Optional[str] = None
    phase_state: Optional[str] = None
    tasks_total: int = 0
    tasks_done: int = 0
    active_task: Optional[str] = None
    tokens: Optional[dict] = None  # deferred; always None in the slice
    stale: bool = False
    updated_at: Optional[str] = None

    @property
    def progress_pct(self) -> int:
        if self.tasks_total == 0:
            return 0
        return round(100 * self.tasks_done / self.tasks_total)


def _read_frontmatter(path: Path) -> Optional[dict]:
    """Return the YAML frontmatter dict of a `--- ... ---` .md file, else None."""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def read_run(project_path: str) -> RunState:
    state = RunState(project_path=str(project_path))

    resolved = load_resolved_config(Path(project_path))
    if resolved is None:
        return state  # not an AMAP project → idle

    root = Path(project_path) / resolved.get("framework_root", ".amap")
    active = root / "knowledge" / "active"
    mtimes: list[float] = []

    # AGENT_TRANSPARENCY frontmatter
    at_path = active / "AGENT_TRANSPARENCY.md"
    fm = _read_frontmatter(at_path)
    if fm is not None:
        state.phase_state = fm.get("phase_state")
        state.ticket_id = fm.get("ticket_id")
        mtimes.append(at_path.stat().st_mtime)
    elif at_path.exists():
        state.stale = True  # present but unparseable

    # TASK_QUEUE (the file IS yaml)
    tq_path = active / "microloop" / "TASK_QUEUE.md"
    if tq_path.exists():
        try:
            queue = yaml.safe_load(tq_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            queue = None
            state.stale = True
        if isinstance(queue, dict):
            tasks = queue.get("tasks", [])
            if isinstance(tasks, list):
                state.tasks_total = len(tasks)
                state.tasks_done = sum(1 for t in tasks if isinstance(t, dict) and t.get("status") == "done")
                for t in tasks:
                    if isinstance(t, dict) and t.get("status") == "in_progress":
                        state.active_task = t.get("desc") or t.get("id")
                        break
            if state.ticket_id is None:
                state.ticket_id = queue.get("ticket_id")
            mtimes.append(tq_path.stat().st_mtime)

    if mtimes:
        state.updated_at = datetime.fromtimestamp(max(mtimes), timezone.utc).isoformat()
    return state
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `/usr/bin/python3 -m pytest cli/tests/test_dashboard_reader.py -v`
Expected: PASS (7 passed)

- [ ] **Step 5: Commit**

```bash
git add cli/dashboard/reader.py cli/tests/test_dashboard_reader.py
git commit -m "feat: add dashboard reader (contract files -> RunState)"
```

---

## Task 4: CLI command + wiring

**Files:**
- Create: `cli/commands/dashboard.py`
- Modify: `cli/amap.py` (add subparser near the `doctor` block; add dispatch near the `status` dispatch)
- Test: `cli/tests/test_dashboard_command.py`

- [ ] **Step 1: Write the failing test**

Create `cli/tests/test_dashboard_command.py`:

```python
"""Tests for the amap dashboard command + wiring."""

from cli.commands.dashboard import run_dashboard
from cli.dashboard import registry


def test_register_then_list(tmp_path, capsys, monkeypatch):
    reg = tmp_path / "projects.yaml"
    monkeypatch.setattr(registry, "default_registry_file", lambda: reg)
    proj = tmp_path / "projA"
    proj.mkdir()

    run_dashboard(target=str(proj), action="register")
    run_dashboard(action="list")

    out = capsys.readouterr().out
    assert "Registered" in out
    assert str(proj.resolve()) in out


def test_default_snapshot_auto_adds_cwd_and_prints_idle(tmp_path, capsys, monkeypatch):
    reg = tmp_path / "projects.yaml"
    monkeypatch.setattr(registry, "default_registry_file", lambda: reg)
    # a bare dir that is not an AMAP project → idle line, no crash
    run_dashboard(target=str(tmp_path))

    out = capsys.readouterr().out
    assert "AMAP runs" in out
    assert "idle" in out
    assert registry.load(reg) == [str(tmp_path.resolve())]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest cli/tests/test_dashboard_command.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cli.commands.dashboard'`

- [ ] **Step 3: Implement the command**

Create `cli/commands/dashboard.py`:

```python
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


def run_dashboard(target: str = ".", action: Optional[str] = None, path: Optional[str] = None) -> None:
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

    # default: auto-add cwd, then snapshot every registered run
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/bin/python3 -m pytest cli/tests/test_dashboard_command.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Wire the subcommand into the parser**

In `cli/amap.py`, find the `# ─── doctor ───` block and insert this block immediately **before** it:

```python
    # ─── dashboard ───
    dashboard_parser = subparsers.add_parser(
        "dashboard",
        help="Register projects and print AMAP run progress (one-shot CLI)",
    )
    dashboard_parser.add_argument(
        "action",
        nargs="?",
        choices=["register", "unregister", "list"],
        default=None,
        help="register/unregister/list; omit to print a progress snapshot",
    )
    dashboard_parser.add_argument(
        "--target", default=".", help="Project directory (default: current directory)",
    )
    dashboard_parser.add_argument(
        "--path", default=None, help="Path for register/unregister (default: --target)",
    )

```

- [ ] **Step 6: Wire the dispatch**

In `cli/amap.py`, find this exact block:

```python
    elif args.command == "doctor" and args.doctor_command == "mcp":
        from cli.commands.doctor import run_doctor_mcp
        run_doctor_mcp(target_dir=args.target, fix=args.fix, assume_yes=args.yes)
```

Insert immediately **before** it:

```python
    elif args.command == "dashboard":
        from cli.commands.dashboard import run_dashboard
        run_dashboard(target=args.target, action=args.action, path=args.path)
```

- [ ] **Step 7: Verify the wiring end-to-end**

Run: `/usr/bin/python3 -m cli.amap dashboard list`
Expected: prints `📋 Registered projects (N):` with no traceback (N may be 0).

- [ ] **Step 8: Run the full suite**

Run: `/usr/bin/python3 -m pytest cli/tests/ -q`
Expected: all pass (no regressions in existing tests).

- [ ] **Step 9: Commit**

```bash
git add cli/commands/dashboard.py cli/amap.py cli/tests/test_dashboard_command.py
git commit -m "feat: wire amap dashboard subcommand (register/list + snapshot)"
```

---

## Task 5: P2.5 — validation gate (manual, blocking before any server work)

This task has no code. It verifies the load-bearing assumption from the spec §5/§7 before we invest in the web server (P3+). **Do not start P3 until this passes or is explicitly waived.**

- [ ] **Step 1: Register this repo and start a real Antigravity task**

Run: `amap dashboard register --path "$(pwd)"`
Then kick off a real Antigravity run that uses the microloop (one that spawns a background subagent).

- [ ] **Step 2: Watch the contract files for live updates (signal A)**

Run (repeat a few times during the run):
`ls -l --time-style=full-iso .amap/knowledge/active/AGENT_TRANSPARENCY.md .amap/knowledge/active/microloop/TASK_QUEUE.md 2>/dev/null`
Record: do the mtimes change *during* the run (not only at the end)?

- [ ] **Step 3: Watch the snapshot reflect progress**

Run (a few times): `amap dashboard`
Record: does `phase`/`x/N`/`active task` change as the run progresses?

- [ ] **Step 4: Record the verdict in the spec**

Edit `docs/superpowers/specs/2026-06-19-agent-activity-dashboard-design.md`, under §7, append a short "P2.5 result" note: one of
- **PASS (A live):** contract files update mid-run → proceed to P3 (server) on the neutral path.
- **PARTIAL:** files update only at phase boundaries → P3 viable but realtime granularity is per-phase; revisit whether the activity hook (P5, signal B) should come *before* the server.
- **FAIL:** no mid-run updates → STOP; the realtime story for Antigravity needs rethinking (see §6/§9 tier C) before any server work.

- [ ] **Step 5: Commit the verdict**

```bash
git add docs/superpowers/specs/2026-06-19-agent-activity-dashboard-design.md
git commit -m "docs: record P2.5 validation-gate result"
```

---

## Self-Review

**Spec coverage:**
- P0 install → Task 1 ✓
- P1 registry (register/unregister/list, auto-add cwd, dedup, remove-missing) → Task 2 (functions) + Task 4 (auto-add cwd via default snapshot) ✓
- P2 Reader reusing `load_resolved_config`, nullable tokens, graceful missing/malformed → Task 3 ✓
- P2.5 validation gate (both signals; STOP branch) → Task 5 ✓
- Test diagram's 11 paths (register add/dedup/auto-cwd, unregister, list-empty, reader full/missing-queue/missing-transparency/idle/malformed-stale/zero-task-progress) → covered across Tasks 2–4 ✓
- Token table parsing — explicitly deferred (`tokens` stays None) ✓
- Server/UI/hook (P3–P6), SSE-vs-WS, tier C — NOT in this plan, per spec §9 ✓

**Placeholder scan:** No TBD/TODO; every code/test step shows complete content; every command has expected output. ✓

**Type consistency:** `RunState` fields and `progress_pct` are defined once (Task 3) and used identically in Task 4. Registry function names (`register`/`unregister`/`load`/`prune_missing`/`default_registry_file`) match between Tasks 2 and 4. `read_run(project_path: str) -> RunState` used consistently. ✓
