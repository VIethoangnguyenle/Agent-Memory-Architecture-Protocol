# Platform-Aware Entry Point File — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `amap` scaffold the agent entry-point file under the correct per-platform name (`AGENTS.md` / `CLAUDE.md` / `.cursorrules`) and ensure every framework file refers to that resolved name, so AMAP installs cleanly on any supported agent platform.

**Architecture:** The platform adapter layer (`cli/platforms/*.py`) already exposes `config_entry_point` per platform and `build_render_context()` already puts `platform.config_entry_point` into the Jinja context. We wire that through: render the manifest `output` field, templatize the 9 framework files that hardcode `AGENTS.md`, fix `amap status`/`update --reconfigure`/`init` to be platform-aware and safe, and close a marker-scan blind spot for suffixless entry-point files.

**Tech Stack:** Python 3.12, Jinja2, PyYAML, pytest.

**Spec:** `docs/superpowers/specs/2026-06-17-platform-entry-point-design.md`

---

## File Structure

**Modified:**
- `cli/plugin-manifest.yaml` — `agents-md` plugin `output` becomes a Jinja expression.
- `cli/scaffold.py` — render `plugin["output"]` per platform; close `verify_no_unresolved` blind spot.
- `cli/commands/init.py` — stage + verify before writing to target.
- `cli/commands/status.py` — platform-aware install detection with legacy fallback.
- `cli/commands/update.py` — delete stale entry-point file on platform switch.
- `AGENTS.md`, `.agent/procedures/bootstrap.md`, `.agent/rules/rules-flow.md`, `.agent/rules/rules-tool.md`, `.agent/rules/RULES.md`, `.agent/workflows/task.md`, `.agent/procedures/token-tracking.md`, `.knowledge-layer/templates/AGENT_TRANSPARENCY.tpl.md`, `.knowledge-layer/templates/TOKEN_LOG.tpl.md` — replace literal `AGENTS.md` with `{{ platform.config_entry_point }}`.

**Created:**
- `cli/tests/test_init.py` — init filename, templatization, abort-on-marker tests.
- `cli/tests/test_status.py` — status platform-aware + legacy tests.

**Test helper convention** (used by new test files):
```python
def _answers(monkeypatch, seq):
    """Feed a fixed sequence to builtins.input()."""
    it = iter(seq)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(it))
```
Prompt order for `run_init`: platform, MCPs, language, confirm. Platform indices follow `PLATFORMS` order: `1`=antigravity, `2`=claude-code, `3`=cursor, `4`=generic. Language index `3`=python. So claude-code init = `["2", "1,2,3", "3", "y"]`.

---

## Task 1: Dynamic output filename

Render the manifest `output` field through Jinja so the entry-point file is written under the platform's `config_entry_point` name.

**Files:**
- Modify: `cli/plugin-manifest.yaml:50-54`
- Modify: `cli/scaffold.py:157-174` (inside `scaffold_plugins`)
- Test: `cli/tests/test_init.py` (create)

- [ ] **Step 1: Write the failing test**

Create `cli/tests/test_init.py`:

```python
"""Tests for amap init."""

from cli.commands.init import run_init


def _answers(monkeypatch, seq):
    it = iter(seq)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(it))


def test_init_writes_platform_entry_point_filename(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])  # claude-code

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert (target / "CLAUDE.md").exists()
    assert not (target / "AGENTS.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest cli/tests/test_init.py::test_init_writes_platform_entry_point_filename -v`
Expected: FAIL — `AGENTS.md` is written instead of `CLAUDE.md` (assertion on `CLAUDE.md` exists fails).

- [ ] **Step 3: Update the manifest**

In `cli/plugin-manifest.yaml`, change the `agents-md` plugin (lines 50-54):

```yaml
  # ─── META-PROMPT ───
  - name: agents-md
    type: meta-prompt
    source: AGENTS.md
    template: false
    output: "{{ platform.config_entry_point }}"
```

- [ ] **Step 4: Render the output path in scaffold_plugins**

In `cli/scaffold.py`, inside `scaffold_plugins`, replace the `target_path` line and the verbose print so both use a rendered output path. Current code (around lines 157-174):

```python
        source_path = resolve_source_path(amap_root, plugin["source"])
        target_path = write_root / plugin["output"]
        if not source_path.exists():
```

becomes:

```python
        source_path = resolve_source_path(amap_root, plugin["source"])
        output_rel = render_string(jinja_env, plugin["output"], context)
        target_path = write_root / output_rel
        if not source_path.exists():
```

and the final verbose print in the same loop:

```python
        if verbose:
            print(f"  ✅ {plugin['output']:35s}")
```

becomes:

```python
        if verbose:
            print(f"  ✅ {output_rel:35s}")
```

(`render_string` is already imported at `cli/scaffold.py:13`. For outputs without `{{ }}` — every other plugin — `render_string` returns the string unchanged, including trailing `/` on directory outputs.)

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest cli/tests/test_init.py::test_init_writes_platform_entry_point_filename -v`
Expected: PASS

- [ ] **Step 6: Run the full suite (no regressions)**

Run: `python3 -m pytest cli/tests/ -q`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add cli/plugin-manifest.yaml cli/scaffold.py cli/tests/test_init.py
git commit -m "$(cat <<'EOF'
feat(cli): render entry-point filename per platform

scaffold now writes the meta-prompt under the platform's
config_entry_point (CLAUDE.md / .cursorrules), not always AGENTS.md.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Close `verify_no_unresolved` blind spot for suffixless entry points

`.cursorrules` has an empty `Path.suffix`, so the marker-scan safety gate never inspects it. Make the gate always scan known entry-point filenames regardless of suffix.

**Files:**
- Modify: `cli/scaffold.py:178-195` (`verify_no_unresolved`)
- Test: `cli/tests/test_scaffold.py`

- [ ] **Step 1: Write the failing test**

Append to `cli/tests/test_scaffold.py`:

```python
def test_verify_no_unresolved_flags_suffixless_entry_point(tmp_path):
    # .cursorrules has an empty suffix and would escape a suffix-only
    # scan — but it is a real platform entry point and must be checked.
    offending = tmp_path / ".cursorrules"
    offending.write_text("rules {{ platform.config_entry_point }}\n", encoding="utf-8")

    offenders = verify_no_unresolved(tmp_path)

    assert offending in offenders
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest cli/tests/test_scaffold.py::test_verify_no_unresolved_flags_suffixless_entry_point -v`
Expected: FAIL — `.cursorrules` is skipped by the suffix filter, so `offenders` is empty.

- [ ] **Step 3: Update `verify_no_unresolved`**

In `cli/scaffold.py`, replace the whole function body (lines 178-195) with:

```python
def verify_no_unresolved(root: Path) -> List[Path]:
    """Return text files under root that still contain an unresolved '{{ ' marker.

    Scans every extension the renderer actually renders (cli.renderer's
    _TEXT_EXTENSIONS), plus every known platform entry-point filename
    regardless of suffix — `.cursorrules` has an empty suffix and would
    otherwise escape the suffix-only filter, leaving the riskiest file
    (the one this scaffold renames dynamically) unchecked.
    """
    from cli.platforms import PLATFORMS, get_platform

    entry_points = {get_platform(k).config_entry_point for k in PLATFORMS}
    offenders = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _RENDERED_SUFFIXES and path.name not in entry_points:
            continue
        try:
            if "{{ " in path.read_text(encoding="utf-8"):
                offenders.append(path)
        except UnicodeDecodeError:
            continue
    return offenders
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest cli/tests/test_scaffold.py::test_verify_no_unresolved_flags_suffixless_entry_point -v`
Expected: PASS

- [ ] **Step 5: Run the full suite (the existing `.py` blind-spot test must still pass)**

Run: `python3 -m pytest cli/tests/ -q`
Expected: all pass (including `test_verify_no_unresolved_flags_offending_py_file`).

- [ ] **Step 6: Commit**

```bash
git add cli/scaffold.py cli/tests/test_scaffold.py
git commit -m "$(cat <<'EOF'
fix(cli): scan suffixless entry-point files for unresolved markers

verify_no_unresolved now always checks known platform entry points
(e.g. .cursorrules) regardless of suffix, closing a marker-scan gap.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Harden `amap init` with staging + verify

Mirror `amap update`'s safety model: render into a temp dir, abort cleanly if any unresolved marker survives, only then sync into the target. This protects the target before Task 4 introduces ~25 new Jinja markers.

**Files:**
- Modify: `cli/commands/init.py` (imports + `run_init` body around lines 1-12 and 95-108)
- Test: `cli/tests/test_init.py`

- [ ] **Step 1: Write the failing test**

Append to `cli/tests/test_init.py`:

```python
def test_init_aborts_on_unresolved_marker(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"

    def fake_scaffold(plugins, amap, write_root, *a, **k):
        (write_root / "bad.md").write_text("{{ leftover }}\n", encoding="utf-8")
        return {"rendered": 0, "copied": 1, "dirs": 0, "skipped": 0}

    monkeypatch.setattr("cli.commands.init.scaffold_plugins", fake_scaffold)
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])  # claude-code

    run_init(target_dir=str(target), amap_root=str(amap_root))

    # Aborted before syncing — target was never written.
    assert not (target / "CLAUDE.md").exists()
    assert not (target / ".agent").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest cli/tests/test_init.py::test_init_aborts_on_unresolved_marker -v`
Expected: FAIL — current `run_init` writes directly to target, so the marker file (and partial tree) lands in the target; the abort never happens.

- [ ] **Step 3: Add imports to init.py**

At the top of `cli/commands/init.py`, the current imports are:

```python
from pathlib import Path
from typing import List, Optional, Tuple

from cli.platforms import PLATFORMS, get_platform
from cli.renderer import create_renderer
from cli.scaffold import (
    load_manifest,
    scaffold_plugins,
    generate_resolved_config,
)
```

Replace with:

```python
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from cli.platforms import PLATFORMS, get_platform
from cli.renderer import create_renderer
from cli.scaffold import (
    load_manifest,
    scaffold_plugins,
    generate_resolved_config,
    verify_no_unresolved,
    sync_tree,
)
```

- [ ] **Step 4: Stage, verify, then sync in run_init**

In `cli/commands/init.py`, the current block (lines 95-102) is:

```python
    context = platform.build_render_context(selected_mcps, language)
    jinja_env = create_renderer(str(amap))
    print("\nScaffolding AMAP framework...\n")
    stats = scaffold_plugins(
        manifest.get("plugins", []), amap, target, context, jinja_env,
        manifest.get("mcp_capabilities", {}), selected_mcps,
    )
    generate_resolved_config(target, platform_key, selected_mcps, language)
```

Replace with:

```python
    context = platform.build_render_context(selected_mcps, language)
    jinja_env = create_renderer(str(amap))
    print("\nScaffolding AMAP framework...\n")

    staging = Path(tempfile.mkdtemp(prefix="amap-init-"))
    try:
        stats = scaffold_plugins(
            manifest.get("plugins", []), amap, staging, context, jinja_env,
            manifest.get("mcp_capabilities", {}), selected_mcps,
        )
        offenders = verify_no_unresolved(staging)
        if offenders:
            print("\n  ❌ Init aborted — unresolved template markers in:")
            for p in offenders:
                print(f"     • {p.relative_to(staging)}")
            print("  Target was NOT modified.")
            return
        sync_tree(staging, target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    generate_resolved_config(target, platform_key, selected_mcps, language)
```

(`stats` is still consumed by the summary print at the end of `run_init` — leave that unchanged.)

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest cli/tests/test_init.py::test_init_aborts_on_unresolved_marker -v`
Expected: PASS

- [ ] **Step 6: Run the full suite**

Run: `python3 -m pytest cli/tests/ -q`
Expected: all pass (Task 1's filename test still passes — it now goes through staging).

- [ ] **Step 7: Commit**

```bash
git add cli/commands/init.py cli/tests/test_init.py
git commit -m "$(cat <<'EOF'
fix(cli): stage and verify amap init before writing to target

init now renders into a temp dir, aborts on any unresolved marker, and
only syncs on success — matching amap update's safety model.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Templatize entry-point references in framework files

Replace every literal `AGENTS.md` in the 9 scaffolded framework files with `{{ platform.config_entry_point }}` so the installed docs name the correct file for each platform.

**Files (all Modify):**
- `AGENTS.md` (6 occurrences: lines 1, 18, 105, 164, 291, 317)
- `.agent/procedures/bootstrap.md` (5: lines 11, 13, 165, 189, 200)
- `.agent/rules/rules-flow.md` (2: lines 33, 86)
- `.agent/rules/rules-tool.md` (1: line 80)
- `.agent/rules/RULES.md` (1: line 14)
- `.agent/workflows/task.md` (1: line 32)
- `.agent/procedures/token-tracking.md` (1: line 54)
- `.knowledge-layer/templates/AGENT_TRANSPARENCY.tpl.md` (2: lines 45, 53)
- `.knowledge-layer/templates/TOKEN_LOG.tpl.md` (1: line 28)
- Test: `cli/tests/test_init.py`

- [ ] **Step 1: Write the failing test**

Append to `cli/tests/test_init.py`:

```python
def test_init_templatizes_entry_point_references(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])  # claude-code

    run_init(target_dir=str(target), amap_root=str(amap_root))

    entry = (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert "CLAUDE.md" in entry
    assert "AGENTS.md" not in entry
    assert "{{ " not in entry

    rules = (target / ".agent" / "rules" / "RULES.md").read_text(encoding="utf-8")
    assert "CLAUDE.md" in rules
    assert "AGENTS.md" not in rules

    boot = (target / ".agent" / "procedures" / "bootstrap.md").read_text(encoding="utf-8")
    assert "AGENTS.md" not in boot
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest cli/tests/test_init.py::test_init_templatizes_entry_point_references -v`
Expected: FAIL — the rendered `CLAUDE.md` still contains literal `AGENTS.md` self-references.

- [ ] **Step 3: Replace literals across all 9 files**

Run this from the repo root. The `#` sed delimiter avoids clashing with `/` in paths, and the replacement contains no `#`:

```bash
for f in \
  AGENTS.md \
  .agent/procedures/bootstrap.md \
  .agent/rules/rules-flow.md \
  .agent/rules/rules-tool.md \
  .agent/rules/RULES.md \
  .agent/workflows/task.md \
  .agent/procedures/token-tracking.md \
  .knowledge-layer/templates/AGENT_TRANSPARENCY.tpl.md \
  .knowledge-layer/templates/TOKEN_LOG.tpl.md ; do
  sed -i 's#AGENTS\.md#{{ platform.config_entry_point }}#g' "$f"
done
```

- [ ] **Step 4: Verify no literal survives in the 9 source files**

Run:

```bash
grep -rn "AGENTS\.md" \
  AGENTS.md .agent/procedures/bootstrap.md .agent/rules/rules-flow.md \
  .agent/rules/rules-tool.md .agent/rules/RULES.md .agent/workflows/task.md \
  .agent/procedures/token-tracking.md \
  .knowledge-layer/templates/AGENT_TRANSPARENCY.tpl.md \
  .knowledge-layer/templates/TOKEN_LOG.tpl.md
```

Expected: no output (every literal replaced). The single-brace placeholders (`{n}`, `{ticket-id}`) in the `.tpl.md` files are untouched — Jinja only parses double-brace `{{ }}`.

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest cli/tests/test_init.py::test_init_templatizes_entry_point_references -v`
Expected: PASS

- [ ] **Step 6: Run the full suite**

Run: `python3 -m pytest cli/tests/ -q`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add AGENTS.md .agent/ .knowledge-layer/templates/ cli/tests/test_init.py
git commit -m "$(cat <<'EOF'
feat(cli): templatize entry-point references in framework files

Replace literal AGENTS.md with {{ platform.config_entry_point }} across
bootstrap, rules, workflow, token-tracking and knowledge templates so
installed docs name the correct file per platform.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Platform-aware `amap status` with legacy fallback

Detect installation by the resolved platform's entry-point file; fall back to `AGENTS.md` for pre-resolved-config (legacy) installs.

**Files:**
- Modify: `cli/commands/status.py:7-22`
- Test: `cli/tests/test_status.py` (create)

- [ ] **Step 1: Write the failing tests**

Create `cli/tests/test_status.py`:

```python
"""Tests for amap status."""

from cli.commands.init import run_init
from cli.commands.status import run_status


def _answers(monkeypatch, seq):
    it = iter(seq)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(it))


def test_status_detects_claude_code_install(tmp_path, amap_root, monkeypatch, capsys):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])  # claude-code
    run_init(target_dir=str(target), amap_root=str(amap_root))
    capsys.readouterr()  # drop init output

    run_status(target_dir=str(target))

    out = capsys.readouterr().out
    assert "No AMAP installation" not in out
    assert "claude-code" in out


def test_status_detects_legacy_install(tmp_path, capsys):
    # Legacy install: AGENTS.md present, no resolved-config.yaml.
    target = tmp_path / "legacy"
    target.mkdir()
    (target / "AGENTS.md").write_text("# legacy\n", encoding="utf-8")

    run_status(target_dir=str(target))

    out = capsys.readouterr().out
    assert "No AMAP installation" not in out
    assert "legacy installation" in out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest cli/tests/test_status.py -v`
Expected: `test_status_detects_claude_code_install` FAILS — the hardcoded `AGENTS.md` existence gate reports "No AMAP installation" for a claude-code install. (`test_status_detects_legacy_install` may already pass — keep it as a guard.)

- [ ] **Step 3: Update run_status**

In `cli/commands/status.py`, the current header + gate (lines 7-22):

```python
from pathlib import Path

from cli.scaffold import load_resolved_config


def run_status(target_dir: str) -> None:
    """Show AMAP status for a target project."""
    target = Path(target_dir).resolve()

    # ─── Check for AMAP installation ───
    agents_md = target / "AGENTS.md"

    if not agents_md.exists():
        print(f"\n  ❌ No AMAP installation found in {target}")
        print(f"     Run: amap init --target {target}")
        return
```

Replace with:

```python
from pathlib import Path

from cli.platforms import get_platform
from cli.scaffold import load_resolved_config


def run_status(target_dir: str) -> None:
    """Show AMAP status for a target project."""
    target = Path(target_dir).resolve()

    # ─── Check for AMAP installation ───
    # Resolve the entry-point file from the recorded platform; fall back to
    # AGENTS.md for legacy installs predating resolved-config.yaml.
    resolved = load_resolved_config(target)
    if resolved is not None:
        try:
            entry = get_platform(resolved.get("platform", "generic")).config_entry_point
        except ValueError:
            entry = "AGENTS.md"
    else:
        entry = "AGENTS.md"

    if not (target / entry).exists():
        print(f"\n  ❌ No AMAP installation found in {target}")
        print(f"     Run: amap init --target {target}")
        return
```

(The existing body below already calls `load_resolved_config(target)` again at line ~29 to print platform/MCPs/language — that second call is cheap; leave it, or reuse `resolved`. The `else` branch there still prints the "legacy installation" message when `resolved is None`.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest cli/tests/test_status.py -v`
Expected: both PASS.

- [ ] **Step 5: Run the full suite**

Run: `python3 -m pytest cli/tests/ -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add cli/commands/status.py cli/tests/test_status.py
git commit -m "$(cat <<'EOF'
fix(cli): make amap status platform-aware with legacy fallback

Detect installs by the resolved platform's entry-point file (CLAUDE.md,
.cursorrules); fall back to AGENTS.md when no resolved-config exists.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: `amap update --reconfigure` removes stale entry-point file

When reconfiguring to a platform with a different entry-point name, delete the old one so the target doesn't keep a dangling `AGENTS.md` beside the new `CLAUDE.md`.

**Files:**
- Modify: `cli/commands/update.py` (capture old entry around line 30, delete after sync around lines 66-71)
- Test: `cli/tests/test_update.py`

- [ ] **Step 1: Write the failing test**

Append to `cli/tests/test_update.py` (the `_init_claude` helper already exists in this file):

```python
def test_reconfigure_removes_old_entry_point(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _init_claude(target, amap_root, monkeypatch)
    assert (target / "CLAUDE.md").exists()

    # Reconfigure to antigravity (platform=1).
    answers = iter(["1", "1,2,3", "3"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))
    run_update(target_dir=str(target), amap_root=str(amap_root), reconfigure=True)

    assert (target / "AGENTS.md").exists()
    assert not (target / "CLAUDE.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest cli/tests/test_update.py::test_reconfigure_removes_old_entry_point -v`
Expected: FAIL — after reconfigure, both `CLAUDE.md` (stale) and `AGENTS.md` (new) exist; the `not CLAUDE.md` assertion fails.

- [ ] **Step 3: Capture the old entry point before reconfigure**

In `cli/commands/update.py`, just after the `resolved is None` guard (current lines 30-34), add the old-entry capture:

```python
    resolved = load_resolved_config(target)
    if resolved is None:
        print(f"\n  ❌ No AMAP installation found in {target}")
        print(f"     Run: amap init --target {target}")
        return

    try:
        old_entry = get_platform(resolved.get("platform", "generic")).config_entry_point
    except ValueError:
        old_entry = "AGENTS.md"
```

(`get_platform` is already imported at `cli/commands/update.py:13`.)

- [ ] **Step 4: Delete the stale entry point after sync**

In `cli/commands/update.py`, the current tail (lines 66-73):

```python
        count = sync_tree(staging, target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    if reconfigure:
        generate_resolved_config(target, platform_key, selected_mcps, language)

    print(f"\n  ✅ Updated {count} framework files. User files preserved.\n")
```

becomes:

```python
        count = sync_tree(staging, target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    if reconfigure and old_entry != platform.config_entry_point:
        old_path = target / old_entry
        if old_path.exists():
            old_path.unlink()

    if reconfigure:
        generate_resolved_config(target, platform_key, selected_mcps, language)

    print(f"\n  ✅ Updated {count} framework files. User files preserved.\n")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest cli/tests/test_update.py::test_reconfigure_removes_old_entry_point -v`
Expected: PASS

- [ ] **Step 6: Run the full suite**

Run: `python3 -m pytest cli/tests/ -q`
Expected: all pass (including the existing `test_reconfigure_switches_platform_keeps_user_files`).

- [ ] **Step 7: Commit**

```bash
git add cli/commands/update.py cli/tests/test_update.py
git commit -m "$(cat <<'EOF'
fix(cli): drop stale entry-point file on amap update --reconfigure

Switching platforms now deletes the previous entry point (e.g. CLAUDE.md)
so the target keeps a single correct agent config file.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: End-to-end Cursor install verification

A focused integration test proving the whole chain works for the suffixless-entry-point platform.

**Files:**
- Test: `cli/tests/test_init.py`

- [ ] **Step 1: Write the test**

Append to `cli/tests/test_init.py`:

```python
def test_init_cursor_produces_clean_cursorrules(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["3", "1,2,3", "3", "y"])  # cursor

    run_init(target_dir=str(target), amap_root=str(amap_root))

    entry = target / ".cursorrules"
    assert entry.exists()
    body = entry.read_text(encoding="utf-8")
    assert ".cursorrules" in body          # self-reference resolved
    assert "AGENTS.md" not in body
    assert "{{ " not in body               # nothing left unrendered
    assert not (target / "AGENTS.md").exists()
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python3 -m pytest cli/tests/test_init.py::test_init_cursor_produces_clean_cursorrules -v`
Expected: PASS (all machinery is in place after Tasks 1-4). If it fails on a leftover marker, that is the Task 2 blind-spot guard doing its job — fix the offending source file.

- [ ] **Step 3: Run the full suite**

Run: `python3 -m pytest cli/tests/ -q`
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add cli/tests/test_init.py
git commit -m "$(cat <<'EOF'
test(cli): verify cursor init renders a clean .cursorrules entry point

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Final verification

- [ ] Run the complete suite once more: `python3 -m pytest cli/tests/ -q` — expect all green.
- [ ] Manual smoke test (optional):
  ```bash
  tmp=$(mktemp -d)
  printf '2\n1,2,3\n3\ny\n' | python3 cli/amap.py init --target "$tmp" --source .
  ls "$tmp"/CLAUDE.md && ! ls "$tmp"/AGENTS.md 2>/dev/null
  python3 cli/amap.py status --target "$tmp"
  rm -rf "$tmp"
  ```
  Expect: `CLAUDE.md` present, no `AGENTS.md`, status reports `claude-code`.
