# Canonical resolved-config (derive + unify, P2.3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Python-side resolved-config discovery deterministic by deriving candidate roots from the platform registry, unifying the `framework_root` default into one canonical constant, and enforcing a single-config-on-disk invariant — without moving config out of `framework_root`.

**Architecture:** Add `CANONICAL_FRAMEWORK_ROOT` to `cli/__init__.py`. `resolved_config_candidates` derives its roots from `PLATFORMS` (canonical-first). `generate_resolved_config` sweeps stale AMAP-generated configs from other roots after writing. The two divergent `framework_root` defaults (reader `.amap`, orchestrator `.agents`) collapse onto the constant / become required. Config stays under `framework_root`, so the agent runtime and golden snapshots are untouched.

**Tech Stack:** Python 3.12, pytest, PyYAML. Spec: `docs/superpowers/specs/2026-06-21-canonical-resolved-config-design.md`.

**Test runner:** `/usr/bin/python3 -m pytest` (the `.venv` python has no pytest — see project memory). Use `/usr/bin/grep` for source greps (recursive grep here skips gitignored files).

---

### Task 1: Add `CANONICAL_FRAMEWORK_ROOT` constant

**Files:**
- Modify: `cli/__init__.py`
- Test: `cli/tests/test_scaffold.py`

- [ ] **Step 1: Write the failing test**

Append to `cli/tests/test_scaffold.py`:

```python
def test_canonical_framework_root_matches_generic_platform():
    from cli import CANONICAL_FRAMEWORK_ROOT
    from cli.platforms import get_platform

    # The canonical default must equal the base/generic platform's root so the
    # constant can never drift from the real default.
    assert CANONICAL_FRAMEWORK_ROOT == get_platform("generic").framework_root
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest cli/tests/test_scaffold.py::test_canonical_framework_root_matches_generic_platform -v`
Expected: FAIL with `ImportError: cannot import name 'CANONICAL_FRAMEWORK_ROOT' from 'cli'`.

- [ ] **Step 3: Add the constant**

In `cli/__init__.py`, after the `FRAMEWORK_VERSION` line, add:

```python
# Canonical AMAP framework root — the single default used wherever a
# framework_root cannot be derived from a loaded config. Equals the base/
# generic platform's framework_root (asserted by tests).
CANONICAL_FRAMEWORK_ROOT = ".amap"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/bin/python3 -m pytest cli/tests/test_scaffold.py::test_canonical_framework_root_matches_generic_platform -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cli/__init__.py cli/tests/test_scaffold.py
git commit -m "feat(config): add CANONICAL_FRAMEWORK_ROOT constant (P2.3)"
```

---

### Task 2: Derive candidate roots from the platform registry

**Files:**
- Modify: `cli/scaffold.py:13` (import), `cli/scaffold.py:63-69` (`resolved_config_candidates`), `cli/scaffold.py:121` (`load_resolved_config` fallback)
- Test: `cli/tests/test_scaffold.py:216-222` (replace existing test)

- [ ] **Step 1: Replace the existing candidates test (new red test)**

In `cli/tests/test_scaffold.py`, replace the whole function `test_resolved_config_candidates_include_native_and_legacy_roots` (currently lines 216-222) with:

```python
def test_resolved_config_candidates_derive_from_platform_registry(tmp_path):
    from cli.platforms import PLATFORMS, get_platform

    candidates = [
        p.relative_to(tmp_path).as_posix() for p in resolved_config_candidates(tmp_path)
    ]
    # Every platform's framework_root is represented (derived, not hardcoded).
    expected_roots = {get_platform(k).framework_root for k in PLATFORMS}
    assert {c.split("/")[0] for c in candidates} == expected_roots
    # Canonical root is first → load fallback is deterministic.
    assert candidates[0] == ".amap/resolved-config.yaml"
    # Every entry is a resolved-config.yaml.
    assert all(c.endswith("/resolved-config.yaml") for c in candidates)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest cli/tests/test_scaffold.py::test_resolved_config_candidates_derive_from_platform_registry -v`
Expected: FAIL on `candidates[0] == ".amap/resolved-config.yaml"` (current order is `.agents` first).

- [ ] **Step 3: Update the import**

In `cli/scaffold.py`, change line 13 from:

```python
from cli import FRAMEWORK_VERSION
```

to:

```python
from cli import FRAMEWORK_VERSION, CANONICAL_FRAMEWORK_ROOT
```

- [ ] **Step 4: Rewrite `resolved_config_candidates`**

Replace the function body (lines 63-69) with:

```python
def resolved_config_candidates(target: Path) -> List[Path]:
    """Return supported resolved-config locations in preference order.

    Roots are derived from the platform registry, so a new platform with a
    new framework_root is covered automatically. The canonical root sorts
    first → the fallback in load_resolved_config is deterministic.
    """
    from cli.platforms import PLATFORMS, get_platform

    roots = {get_platform(k).framework_root for k in PLATFORMS}
    ordered = [CANONICAL_FRAMEWORK_ROOT, *sorted(roots - {CANONICAL_FRAMEWORK_ROOT})]
    return [target / root / "resolved-config.yaml" for root in ordered]
```

- [ ] **Step 5: DRY the load fallback**

In `load_resolved_config`, change line 121 from:

```python
            expected_root = ".amap"
```

to:

```python
            expected_root = CANONICAL_FRAMEWORK_ROOT
```

- [ ] **Step 6: Run the full scaffold test module**

Run: `/usr/bin/python3 -m pytest cli/tests/test_scaffold.py -v`
Expected: PASS — the new candidates test passes AND all existing `load_resolved_config` tests still pass (each only writes one config, so ordering does not affect them).

- [ ] **Step 7: Commit**

```bash
git add cli/scaffold.py cli/tests/test_scaffold.py
git commit -m "refactor(config): derive resolved-config candidates from PLATFORMS (P2.3)"
```

---

### Task 3: Enforce single-config invariant (sweep-on-write)

**Files:**
- Modify: `cli/scaffold.py` (`generate_resolved_config` + new `_sweep_stale_configs`; harden `_read_resolved_config`)
- Test: `cli/tests/test_scaffold.py`

- [ ] **Step 1: Write the failing sweep test + a hardening test**

Append to `cli/tests/test_scaffold.py`:

```python
def test_read_resolved_config_returns_none_for_top_level_scalar(tmp_path):
    # A stray same-named file whose YAML is a bare scalar must not crash.
    from cli.scaffold import _read_resolved_config

    p = tmp_path / "resolved-config.yaml"
    p.write_text("just a bare string\n", encoding="utf-8")
    assert _read_resolved_config(p) is None


def test_generate_resolved_config_sweeps_stale_amap_config(tmp_path):
    from cli.platforms import get_platform

    # Stale AMAP-generated config left from a previous (generic) install.
    stale = tmp_path / ".amap" / "resolved-config.yaml"
    stale.parent.mkdir(parents=True)
    stale.write_text(
        "resolved:\n  platform: generic\n  framework_root: .amap\n",
        encoding="utf-8",
    )
    # An unrelated file that merely shares the name must be preserved.
    bystander = tmp_path / ".claude" / "resolved-config.yaml"
    bystander.parent.mkdir(parents=True)
    bystander.write_text("other: value\n", encoding="utf-8")

    generate_resolved_config(tmp_path, get_platform("antigravity"), ["socraticode"], "python")

    assert (tmp_path / ".agents" / "resolved-config.yaml").exists()   # active written
    assert not stale.exists()                                         # stale swept
    assert bystander.read_text(encoding="utf-8") == "other: value\n"  # bystander kept
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest cli/tests/test_scaffold.py::test_generate_resolved_config_sweeps_stale_amap_config cli/tests/test_scaffold.py::test_read_resolved_config_returns_none_for_top_level_scalar -v`
Expected: `test_generate_..._sweeps_stale_amap_config` FAILS (`stale.exists()` still True — no sweep yet). `test_read_..._top_level_scalar` may FAIL with `AttributeError: 'str' object has no attribute 'get'` (current `_read_resolved_config` crashes on a scalar).

- [ ] **Step 3: Harden `_read_resolved_config`**

In `cli/scaffold.py`, in `_read_resolved_config`, change:

```python
    resolved = (data or {}).get("resolved")
```

to:

```python
    resolved = data.get("resolved") if isinstance(data, dict) else None
```

- [ ] **Step 4: Add the sweep and call it from `generate_resolved_config`**

In `generate_resolved_config`, after the `with open(config_path, "w", ...)` block that writes the file, add a final line:

```python
    _sweep_stale_configs(target_dir, keep=config_path)
```

Then add this new function immediately after `generate_resolved_config`:

```python
def _sweep_stale_configs(target_dir: Path, keep: Path) -> None:
    """Remove AMAP-generated resolved-config.yaml under candidate roots != keep.

    Enforces the single-config invariant after a write (e.g. clears the old
    config when a project switches platforms). Only deletes a file that parses
    as an AMAP resolved config (has a ``resolved:`` mapping) — never an
    unrelated same-named file. Best-effort: missing/unreadable files are skipped.
    """
    for candidate in resolved_config_candidates(target_dir):
        if candidate == keep or not candidate.exists():
            continue
        if _read_resolved_config(candidate) is None:
            continue
        candidate.unlink()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `/usr/bin/python3 -m pytest cli/tests/test_scaffold.py -v`
Expected: PASS — both new tests pass; `test_generate_resolved_config_uses_platform_framework_root` still passes (no `.amap` config exists in that test, so the sweep is a no-op and never creates `.amap/`).

- [ ] **Step 6: Commit**

```bash
git add cli/scaffold.py cli/tests/test_scaffold.py
git commit -m "feat(config): sweep stale configs on write for single-config invariant (P2.3)"
```

---

### Task 4: Unify the two divergent `framework_root` defaults

**Files:**
- Modify: `cli/dashboard/reader.py` (import + line 68 default)
- Modify: `.amap/tools/microloop-orchestrator/orchestrator.py:103` (make `framework_root` keyword-only required)
- Test: `.amap/tools/microloop-orchestrator/tests/test_runtime_contract.py`

- [ ] **Step 1: Write the failing orchestrator test**

Append to `.amap/tools/microloop-orchestrator/tests/test_runtime_contract.py` (match the file's try/except style — it does not import pytest):

```python
def test_initialize_runtime_queue_requires_framework_root(tmp_path):
    active = tmp_path / ".agents" / "knowledge" / "active"
    active.mkdir(parents=True)
    try:
        orchestrator.initialize_runtime_queue(
            active,
            ticket_id="X",
            spec_path="p",
            tasks=[{"id": "T1", "desc": "one", "depends_on": []}],
        )
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError when framework_root is omitted")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest .amap/tools/microloop-orchestrator/tests/test_runtime_contract.py::test_initialize_runtime_queue_requires_framework_root -v`
Expected: FAIL with `AssertionError: expected TypeError when framework_root is omitted` (the current `.agents` default means no error is raised).

- [ ] **Step 3: Make `framework_root` keyword-only required**

In `.amap/tools/microloop-orchestrator/orchestrator.py`, change the signature at line 103 from:

```python
def initialize_runtime_queue(active_dir, ticket_id, spec_path, tasks,
                             execution_mode="subagent", framework_root=".agents"):
```

to (insert `*,` so `framework_root` is keyword-only and has no default — do NOT reorder positionals):

```python
def initialize_runtime_queue(active_dir, ticket_id, spec_path, tasks,
                             execution_mode="subagent", *, framework_root):
```

- [ ] **Step 4: Fix the existing caller that omitted `framework_root`**

In the same test file, in `test_update_task_status_rejects_unknown_task` (around lines 78-83), add the `framework_root` argument to the `initialize_runtime_queue(...)` call:

```python
    orchestrator.initialize_runtime_queue(
        active,
        ticket_id="X",
        spec_path="p",
        tasks=[{"id": "T1", "desc": "one", "depends_on": []}],
        framework_root=".agents",
    )
```

(The other call, in `test_runtime_contract_emits_queue_handoff_result_and_events`, already passes `framework_root=".agents"` — leave it.)

- [ ] **Step 5: Run the orchestrator test module to verify it passes**

Run: `/usr/bin/python3 -m pytest .amap/tools/microloop-orchestrator/tests/test_runtime_contract.py -v`
Expected: PASS (all three tests, including the new TypeError test).

- [ ] **Step 6: Point the reader default at the constant**

In `cli/dashboard/reader.py`, add an import near the existing `from cli.scaffold import load_resolved_config` (line 19):

```python
from cli import CANONICAL_FRAMEWORK_ROOT
```

Then change the `active_dir` return line (line 68) from:

```python
    return Path(project_path) / resolved.get("framework_root", ".amap") / "knowledge" / "active"
```

to:

```python
    return Path(project_path) / resolved.get("framework_root", CANONICAL_FRAMEWORK_ROOT) / "knowledge" / "active"
```

- [ ] **Step 7: Run the reader tests to verify no regression**

Run: `/usr/bin/python3 -m pytest cli/tests/test_dashboard_reader.py -v`
Expected: PASS (behavior unchanged — `.amap` and `CANONICAL_FRAMEWORK_ROOT` are the same value; this is a DRY/anti-drift change).

- [ ] **Step 8: Commit**

```bash
git add cli/dashboard/reader.py .amap/tools/microloop-orchestrator/orchestrator.py .amap/tools/microloop-orchestrator/tests/test_runtime_contract.py
git commit -m "refactor(config): unify framework_root defaults; orchestrator fail-loud (P2.3 / S2)"
```

---

### Task 5: Full-suite + golden-snapshot verification

**Files:** none (verification gate).

- [ ] **Step 1: Run the full CLI test suite**

Run: `/usr/bin/python3 -m pytest cli/tests/ -v`
Expected: PASS, no regressions.

- [ ] **Step 2: Confirm golden snapshots are unchanged**

Run: `/usr/bin/python3 -m pytest cli/tests/test_snapshots.py -v`
Expected: PASS — config still renders under `framework_root`, so scaffold output is byte-identical (UP3 guard).

- [ ] **Step 3: Run the orchestrator test suite**

Run: `/usr/bin/python3 -m pytest .amap/tools/microloop-orchestrator/tests/ -v`
Expected: PASS.

- [ ] **Step 4: Confirm no divergent `framework_root` literal default remains**

Run each; both must print nothing (exit 1):

```bash
/usr/bin/grep -n 'framework_root=".agents"' .amap/tools/microloop-orchestrator/orchestrator.py
/usr/bin/grep -n '"framework_root", ".amap"' cli/dashboard/reader.py
```

Expected: no output from either — the orchestrator default is gone (keyword-only required) and the reader default is the constant. A hit means a divergent literal default leaked back in.

- [ ] **Step 5: Final commit (if any verification fixups were needed)**

```bash
git add -A
git commit -m "test(config): verify canonical resolved-config end-to-end (P2.3)"
```

(If steps 1-4 were all green with no fixups, skip this commit.)

---

## Spec coverage map

- Spec §3.1 (constant + invariant) → Task 1.
- Spec §3.2 (derive candidates, canonical-first, fallback DRY) → Task 2.
- Spec §3.3 (diet divergence: reader constant, orchestrator fail-loud keyword-only) → Task 4.
- Spec §3.4 (sweep-on-write + verify-AMAP-generated guard) → Task 3.
- Spec §3.5 (deterministic load, no mtime) → Task 2 (canonical-first ordering) + existing load logic retained.
- Spec §5 (test plan incl. snapshot/regression/divergence guard) → Tasks 1-5.
- Spec §6 (error handling: best-effort sweep, orchestrator fail-loud) → Task 3 Step 4, Task 4.
- Spec §8 non-goals (no file move, no pointer, no mtime, no capability rework) → respected; nothing in any task touches agent templates, `meta-prompt.md`, or `tool_mapping`.
