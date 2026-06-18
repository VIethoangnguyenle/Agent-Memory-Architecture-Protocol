# Meta-Prompt Template Relocation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the downstream meta-prompt template from repo root `AGENTS.md` to `.amap/meta-prompt.md` so Codex/Antigravity stop auto-loading it during framework development, with zero change to downstream `amap init` output.

**Architecture:** The template's body is already platform-neutral (`{{ platform.config_entry_point }}` only). Relocation is purely a *source path* change: update the plugin manifest `source` and the scaffolder `SOURCE_MAP`, then `git mv` the file. Render path (`output: {{ platform.config_entry_point }}`) is unchanged, so all three platform entry points render exactly as before.

**Tech Stack:** Python 3.8+, PyYAML, Jinja2, pytest. Test runner: `/usr/bin/python3 -m pytest` (the repo `.venv` has no pytest).

---

## File Structure

Modify:
- `cli/scaffold.py` — `SOURCE_MAP`: replace the `AGENTS.md` source entry with `meta-prompt.md → .amap/meta-prompt.md`.
- `cli/plugin-manifest.yaml` — `agents-md` plugin `source: AGENTS.md` → `source: meta-prompt.md`.
- `cli/tests/test_scaffold.py` — add a unit test for the new source mapping.
- `docs/amap-file-ownership-policy.md` — one-line note that the meta-prompt source now lives at `.amap/meta-prompt.md`.

Move:
- `AGENTS.md` → `.amap/meta-prompt.md` (via `git mv`, body unchanged).

Do not modify:
- The template body (no hardcoded `"AGENTS.md"`; uses `{{ platform.config_entry_point }}`).
- README.md (describes the *downstream* project tree, still correct).
- Platform adapters / `config_entry_point` mapping.
- `install.sh` (does not reference root `AGENTS.md`).

---

## Task 1: Add failing test for the new source mapping

**Files:**
- Test: `cli/tests/test_scaffold.py`

- [ ] **Step 1: Write the failing test**

Add this test directly after `test_resolve_source_path_maps_skills` (around line 39) in `cli/tests/test_scaffold.py`:

```python
def test_resolve_source_path_maps_meta_prompt(amap_root):
    p = resolve_source_path(amap_root, "meta-prompt.md")
    assert p == amap_root / ".amap/meta-prompt.md"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `/usr/bin/python3 -m pytest cli/tests/test_scaffold.py::test_resolve_source_path_maps_meta_prompt -v`

Expected: FAIL. With the current `SOURCE_MAP`, `"meta-prompt.md"` matches no prefix, so `resolve_source_path` falls through to `amap_root / "meta-prompt.md"` — the assertion against `.amap/meta-prompt.md` fails.

- [ ] **Step 3: Commit the failing test**

```bash
git add cli/tests/test_scaffold.py
git commit -m "test(scaffold): expect meta-prompt source under .amap/"
```

---

## Task 2: Relocate the template and repoint the scaffolder

**Files:**
- Move: `AGENTS.md` → `.amap/meta-prompt.md`
- Modify: `cli/scaffold.py:27`
- Modify: `cli/plugin-manifest.yaml:52`

- [ ] **Step 1: Move the file (preserve git history)**

```bash
git mv AGENTS.md .amap/meta-prompt.md
```

- [ ] **Step 2: Update `SOURCE_MAP` in `cli/scaffold.py`**

In `cli/scaffold.py`, replace the final `SOURCE_MAP` entry (line 27):

```python
    "AGENTS.md":            "AGENTS.md",
```

with:

```python
    "meta-prompt.md":       ".amap/meta-prompt.md",
```

- [ ] **Step 3: Update the plugin manifest source**

In `cli/plugin-manifest.yaml`, the `agents-md` plugin (line 52), change:

```yaml
    source: AGENTS.md
```

to:

```yaml
    source: meta-prompt.md
```

Leave `template: false` and `output: "{{ platform.config_entry_point }}"` unchanged.

- [ ] **Step 4: Run the new unit test to verify it passes**

Run: `/usr/bin/python3 -m pytest cli/tests/test_scaffold.py::test_resolve_source_path_maps_meta_prompt -v`

Expected: PASS. `resolve_source_path` now maps `"meta-prompt.md"` → `amap_root / ".amap/meta-prompt.md"`.

- [ ] **Step 5: Run the full CLI test suite**

Run: `/usr/bin/python3 -m pytest cli/tests/ -q`

Expected: all pass. In particular `test_init.py` (e.g. `test_init_antigravity_uses_agents_as_only_framework_root`, `test_init_codex_uses_agents_as_only_framework_root`) still renders the entry point to the target — this is end-to-end proof the relocated source resolves and renders.

- [ ] **Step 6: Commit**

```bash
git add AGENTS.md .amap/meta-prompt.md cli/scaffold.py cli/plugin-manifest.yaml
git commit -m "refactor(cli): relocate meta-prompt template to .amap/meta-prompt.md"
```

---

## Task 3: Doc note and final verification

**Files:**
- Modify: `docs/amap-file-ownership-policy.md:11`

- [ ] **Step 1: Add a source-location note to the ownership policy**

Open `docs/amap-file-ownership-policy.md`. Read line 11 (the Framework-owned row) and add a short clause noting the meta-prompt *source* now lives at `.amap/meta-prompt.md` while the rendered downstream entry-point file remains framework-owned as before. Keep it to one clause — do not restructure the table. Example clause to append inside that row's last cell:

```text
(nguồn meta-prompt: `.amap/meta-prompt.md` → render ra entry-point downstream)
```

- [ ] **Step 2: Smoke-test `amap init` for all three platforms**

Run:

```bash
/usr/bin/python3 - <<'PY'
import tempfile, pathlib
from cli.commands.init import run_init

amap_root = pathlib.Path.cwd()
# answers: platform, mcps, language, confirm  (see test_init.py _answers ordering)
cases = {
    "claude-code": ["2", "1,2,3", "3", "y"],
    "codex":       ["4", "1,2,3", "3", "y"],
    "generic":     ["3", "1,2,3", "3", "y"],
}
for name, answers in cases.items():
    d = tempfile.mkdtemp(prefix=f"amap-{name}-")
    it = iter(answers)
    import builtins
    builtins.input = lambda *a, **k: next(it)
    run_init(target_dir=d, amap_root=str(amap_root))
    root = pathlib.Path(d)
    entries = [p.name for p in root.iterdir()]
    print(name, "->", sorted(entries))
PY
```

Expected: each target contains a rendered entry point (`CLAUDE.md` for claude-code, `AGENTS.md` for codex/generic). If the platform-number answers do not match (the prompt order changed), confirm the indices against `cli/commands/init.py` and re-run. Verify visually that the entry-point file contains no literal `{{ ` (it has been rendered).

> Note: if a platform answer index is wrong, the smoke script will still complete but write to the wrong framework root. Cross-check against the platform prompt in `cli/commands/init.py` before trusting output.

- [ ] **Step 3: Confirm root no longer holds `AGENTS.md` and tree is clean**

```bash
test ! -e AGENTS.md && echo "root AGENTS.md gone: OK"
test -e .amap/meta-prompt.md && echo "meta-prompt relocated: OK"
git diff --check
```

Expected: both `OK` lines print; `git diff --check` produces no output.

- [ ] **Step 4: Final full-suite gate**

Run: `/usr/bin/python3 -m pytest cli/tests/ -q`

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add docs/amap-file-ownership-policy.md
git commit -m "docs(ownership): note relocated meta-prompt source path"
```
