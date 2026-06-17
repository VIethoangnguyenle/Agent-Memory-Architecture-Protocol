# AMAP Installer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn this repo into an OpenSpec-style installer — `./install.sh /path/to/project` scaffolds AMAP into a target project for a chosen IDE, and re-running safely updates the framework without destroying user customizations.

**Architecture:** A thin `install.sh` bootstraps a venv and routes to the existing Python CLI (`amap init` vs new `amap update`). Per-plugin `ownership` (framework|user) in the manifest decides what `update` re-renders vs preserves. `update` renders to a temp staging dir, verifies zero unresolved `{{ ` markers, then atomically syncs framework files over the target. Template errors are no longer silently swallowed.

**Tech Stack:** Python 3.8+, Jinja2, PyYAML, pytest, Bash.

**Spec:** [docs/superpowers/specs/2026-06-17-amap-installer-design.md](../specs/2026-06-17-amap-installer-design.md)

---

## File Structure

- `cli/scaffold.py` — **new.** Shared, non-interactive scaffolding core: manifest loading, source-path resolution, capability gating, per-plugin copy/render, ownership lookup, staging verification, tree sync, resolved-config generation. Imported by both `init` and `update`.
- `cli/commands/init.py` — **modified.** Keeps interactive prompts (`prompt_choice`, `prompt_multi`, new `gather_choices`); delegates the actual file work to `cli/scaffold.py`. Moved helpers are deleted here.
- `cli/commands/update.py` — **new.** `run_update(target, amap_root, reconfigure)`.
- `cli/amap.py` — **modified.** Adds the `update` subcommand with `--reconfigure`.
- `cli/renderer.py` — **modified.** Stop swallowing Jinja `TemplateError` in `copy_and_render_directory`.
- `cli/plugin-manifest.yaml` — **modified.** Add `ownership: user` to the two knowledge-layer plugins.
- `install.sh` — **new.** Repo-root shell wrapper.
- `cli/tests/` — **new.** `conftest.py`, `test_render.py`, `test_scaffold.py`, `test_update.py`.

Tests run with the repo itself as the AMAP source root and `tmp_path` as the target.

---

## Task 1: Fail-loud rendering + test scaffolding

**Files:**
- Create: `cli/tests/__init__.py`
- Create: `cli/tests/conftest.py`
- Create: `cli/tests/test_render.py`
- Modify: `cli/renderer.py:133-146`

- [ ] **Step 1: Create the test package marker**

Create `cli/tests/__init__.py` (empty file):

```python
```

- [ ] **Step 2: Create shared fixtures**

Create `cli/tests/conftest.py`:

```python
"""Shared fixtures for AMAP CLI tests."""

from pathlib import Path

import pytest

from cli.renderer import create_renderer
from cli.platforms import get_platform


@pytest.fixture
def amap_root() -> Path:
    """Repo root = the AMAP source (this repo)."""
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def jinja_env(amap_root):
    return create_renderer(str(amap_root))


@pytest.fixture
def claude_context():
    """Render context for the claude-code platform, no MCPs."""
    return get_platform("claude-code").build_render_context([], "python")
```

- [ ] **Step 3: Write the failing test for fail-loud rendering**

Create `cli/tests/test_render.py`:

```python
"""Tests for the Jinja2 renderer."""

import pytest
from jinja2 import TemplateSyntaxError

from cli.renderer import (
    create_renderer,
    render_string,
    copy_and_render_directory,
)


def test_render_string_resolves_tool_names(jinja_env, claude_context):
    out = render_string(jinja_env, "use {{ tools.read_file }}", claude_context)
    assert out == "use Read"


def test_malformed_template_raises_not_swallowed(jinja_env, claude_context):
    # Unclosed tag must raise, never silently pass through.
    with pytest.raises(TemplateSyntaxError):
        render_string(jinja_env, "broken {{ tools.read_file ", claude_context)


def test_directory_render_propagates_template_errors(tmp_path, jinja_env, claude_context):
    src = tmp_path / "src"
    src.mkdir()
    (src / "good.md").write_text("ok {{ tools.read_file }}", encoding="utf-8")
    (src / "bad.md").write_text("broken {{ tools.read_file ", encoding="utf-8")
    dst = tmp_path / "dst"
    with pytest.raises(TemplateSyntaxError):
        copy_and_render_directory(jinja_env, src, dst, claude_context)
```

- [ ] **Step 4: Run tests to verify failure**

Run: `python -m pytest cli/tests/test_render.py -v`
Expected: `test_render_string_resolves_tool_names` PASS; the two error tests FAIL (current code swallows `TemplateSyntaxError` via `except (UnicodeDecodeError, Exception)`).

- [ ] **Step 5: Fix the swallow in `copy_and_render_directory`**

In `cli/renderer.py`, replace the block at lines 133-146:

```python
            # Try to render text files containing Jinja2 variables
            if _is_text_file(item):
                try:
                    content = item.read_text(encoding="utf-8")
                    if _has_jinja_vars(content):
                        output = render_string(env, content, context)
                        target.write_text(output, encoding="utf-8")
                        # Preserve original file timestamps
                        shutil.copystat(item, target)
                        rendered += 1
                        total += 1
                        continue
                except (UnicodeDecodeError, Exception):
                    pass  # Fall through to plain copy
```

with:

```python
            # Try to render text files containing Jinja2 variables.
            # Only UnicodeDecodeError (binary file with a text extension) is
            # tolerated; template errors must surface, never ship unrendered.
            if _is_text_file(item):
                try:
                    content = item.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    content = None
                if content is not None and _has_jinja_vars(content):
                    output = render_string(env, content, context)
                    target.write_text(output, encoding="utf-8")
                    # Preserve original file timestamps
                    shutil.copystat(item, target)
                    rendered += 1
                    total += 1
                    continue
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest cli/tests/test_render.py -v`
Expected: all 3 PASS.

- [ ] **Step 7: Commit**

```bash
git add cli/tests/__init__.py cli/tests/conftest.py cli/tests/test_render.py cli/renderer.py
git commit -m "fix(cli): surface template errors instead of swallowing them"
```

---

## Task 2: Extract `cli/scaffold.py` shared core + ownership

**Files:**
- Create: `cli/scaffold.py`
- Modify: `cli/commands/init.py`
- Create: `cli/tests/test_scaffold.py`

- [ ] **Step 1: Write the failing test for the shared core**

Create `cli/tests/test_scaffold.py`:

```python
"""Tests for the shared scaffolding core."""

from cli.scaffold import (
    load_manifest,
    has_capability,
    get_ownership,
    resolve_source_path,
)


def test_get_ownership_defaults_to_framework():
    assert get_ownership({"name": "x"}) == "framework"
    assert get_ownership({"name": "x", "ownership": "user"}) == "user"


def test_load_manifest_has_plugins(amap_root):
    manifest = load_manifest(amap_root)
    assert len(manifest["plugins"]) > 0
    assert "mcp_capabilities" in manifest


def test_has_capability(amap_root):
    manifest = load_manifest(amap_root)
    caps = manifest["mcp_capabilities"]
    assert has_capability(["socraticode"], caps, "code_exploration") is True
    assert has_capability([], caps, "code_exploration") is False


def test_resolve_source_path_maps_skills(amap_root):
    p = resolve_source_path(amap_root, "skills/codebase-explorer/")
    assert p == amap_root / ".agent/skills/codebase-explorer/"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cli/tests/test_scaffold.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cli.scaffold'`.

- [ ] **Step 3: Create `cli/scaffold.py`**

Create `cli/scaffold.py`:

```python
"""Shared, non-interactive scaffolding core for AMAP.

Used by both `amap init` (writes directly to target) and `amap update`
(writes to a staging dir, then syncs). Contains no input() calls.
"""

import shutil
from pathlib import Path
from typing import Dict, List

import yaml

from cli.renderer import render_string


# Maps plugin source prefixes to actual directories in the AMAP repo.
SOURCE_MAP = {
    "rules/":               ".agent/rules/",
    "skills/":              ".agent/skills/",
    "workflows/":           ".agent/workflows/",
    "procedures/":          ".agent/procedures/",
    "tools/":               ".agent/tools/",
    "knowledge-templates/": ".knowledge-layer/templates/",
    "knowledge-active/":    ".knowledge-layer/active/",
    "knowledge-long-term/": ".knowledge-layer/long-term/",
    "AGENTS.md":            "AGENTS.md",
}

# File extensions eligible for single-file Jinja auto-render.
_RENDERABLE_SUFFIXES = {".md", ".yaml", ".yml", ".txt"}


def resolve_source_path(amap_root: Path, source: str) -> Path:
    """Resolve a plugin source path to its actual location in the AMAP repo."""
    for prefix, actual_dir in SOURCE_MAP.items():
        if source.startswith(prefix) or source == prefix.rstrip("/"):
            return amap_root / source.replace(prefix, actual_dir, 1)
    return amap_root / source


def load_manifest(amap_root: Path) -> dict:
    """Load the plugin manifest YAML."""
    with open(amap_root / "cli" / "plugin-manifest.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def has_capability(selected_mcps: List[str], mcp_capabilities: dict, required: str) -> bool:
    """True if any selected MCP provides the required capability."""
    return any(
        mcp_capabilities.get(mcp, {}).get("provides") == required
        for mcp in selected_mcps
    )


def get_ownership(plugin: dict) -> str:
    """Return 'framework' (default) or 'user' for a plugin."""
    return plugin.get("ownership", "framework")


def generate_resolved_config(
    target_dir: Path, platform_name: str, selected_mcps: List[str], language: str
) -> None:
    """Write .agent/resolved-config.yaml recording the init/reconfigure choices."""
    config_path = target_dir / ".agent" / "resolved-config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        f.write("# AMAP Resolved Configuration\n")
        f.write("# Generated by: amap init / amap update --reconfigure\n")
        f.write("# The adapter layer is pre-resolved — no runtime lookup needed.\n\n")
        yaml.dump(
            {"resolved": {
                "platform": platform_name,
                "mcps": selected_mcps,
                "language": language,
                "framework_version": "3.0",
            }},
            f, default_flow_style=False, allow_unicode=True,
        )


def scaffold_plugin(
    plugin: dict, source_path: Path, target_path: Path, context: dict, jinja_env
) -> dict:
    """Copy or render a single plugin to target_path.

    Returns a stats dict: {"action": "dir"|"rendered"|"copied",
                           "count": int, "rendered": int}.
    Template errors propagate (never swallowed).
    """
    from cli.renderer import copy_and_render_directory

    if plugin.get("copy_dir"):
        count, rendered = copy_and_render_directory(
            jinja_env, source_path, target_path, context
        )
        return {"action": "dir", "count": count, "rendered": rendered}

    target_path.parent.mkdir(parents=True, exist_ok=True)

    if plugin.get("template") or source_path.suffix.lower() in _RENDERABLE_SUFFIXES:
        try:
            content = source_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = None
        if content is not None and ("{{ " in content or plugin.get("template")):
            output = render_string(jinja_env, content, context)
            target_path.write_text(output, encoding="utf-8")
            shutil.copystat(source_path, target_path)
            return {"action": "rendered", "count": 1, "rendered": 1}

    shutil.copy2(source_path, target_path)
    return {"action": "copied", "count": 1, "rendered": 0}


def scaffold_plugins(
    plugins: List[dict], amap_root: Path, write_root: Path, context: dict,
    jinja_env, mcp_capabilities: dict, selected_mcps: List[str],
    only_framework: bool = False, verbose: bool = True,
) -> dict:
    """Process all plugins into write_root.

    only_framework=True skips ownership=='user' plugins (used by update).
    Returns aggregate stats.
    """
    stats = {"rendered": 0, "copied": 0, "dirs": 0, "skipped": 0}
    for plugin in plugins:
        name = plugin["name"]
        requires = plugin.get("requires_capability")
        if requires and not has_capability(selected_mcps, mcp_capabilities, requires):
            if verbose:
                print(f"  ⏭️  {name:35s} (no {requires})")
            stats["skipped"] += 1
            continue
        if only_framework and get_ownership(plugin) == "user":
            if verbose:
                print(f"  🔒 {name:35s} (user-owned, preserved)")
            stats["skipped"] += 1
            continue

        source_path = resolve_source_path(amap_root, plugin["source"])
        target_path = write_root / plugin["output"]
        if not source_path.exists():
            if verbose:
                print(f"  ⚠️  {name:35s} (source not found: {source_path})")
            stats["skipped"] += 1
            continue

        result = scaffold_plugin(plugin, source_path, target_path, context, jinja_env)
        if result["action"] == "dir":
            stats["dirs"] += 1
            stats["rendered"] += result["rendered"]
        elif result["action"] == "rendered":
            stats["rendered"] += 1
        else:
            stats["copied"] += 1
        if verbose:
            print(f"  ✅ {plugin['output']:35s}")
    return stats


def verify_no_unresolved(root: Path) -> List[Path]:
    """Return text files under root that still contain an unresolved '{{ ' marker."""
    offenders = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _RENDERABLE_SUFFIXES:
            continue
        try:
            if "{{ " in path.read_text(encoding="utf-8"):
                offenders.append(path)
        except UnicodeDecodeError:
            continue
    return offenders


def sync_tree(src: Path, dst: Path) -> int:
    """Copy every file from src over dst (overwrite). Returns file count."""
    count = 0
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        count += 1
    return count
```

- [ ] **Step 4: Run scaffold tests to verify they pass**

Run: `python -m pytest cli/tests/test_scaffold.py -v`
Expected: all 4 PASS.

- [ ] **Step 5: Refactor `cli/commands/init.py` to use the shared core**

Replace the entire contents of `cli/commands/init.py` with:

```python
"""amap init — Scaffold AMAP framework into a target project."""

from pathlib import Path
from typing import List, Optional, Tuple

from cli.platforms import PLATFORMS, get_platform
from cli.renderer import create_renderer
from cli.scaffold import (
    load_manifest,
    scaffold_plugins,
    generate_resolved_config,
)


def prompt_choice(message: str, choices: List[str], default: int = 0) -> str:
    """Interactive single-choice prompt."""
    print(f"\n{message}")
    for i, choice in enumerate(choices):
        marker = "❯" if i == default else " "
        print(f"  {marker} [{i + 1}] {choice}")
    while True:
        raw = input(f"\nChọn (1-{len(choices)}) [{default + 1}]: ").strip()
        if not raw:
            return choices[default]
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass
        print(f"  ⚠️  Chọn số từ 1 đến {len(choices)}")


def prompt_multi(message: str, choices: List[dict]) -> List[str]:
    """Interactive multi-choice prompt. Each choice has 'key' and 'display'."""
    print(f"\n{message}")
    for i, choice in enumerate(choices):
        print(f"  [{i + 1}] {choice['display']}")
    print("\nNhập số thứ tự, cách bởi dấu phẩy (vd: 1,2) hoặc Enter để bỏ qua:")
    raw = input("> ").strip()
    if not raw:
        return []
    selected = []
    for part in raw.split(","):
        try:
            idx = int(part.strip()) - 1
            if 0 <= idx < len(choices):
                selected.append(choices[idx]["key"])
        except ValueError:
            pass
    return selected


def gather_choices(manifest: dict) -> Tuple[str, List[str], str]:
    """Interactively gather (platform_key, selected_mcps, language)."""
    mcp_capabilities = manifest.get("mcp_capabilities", {})
    languages = manifest.get("languages", ["java", "typescript", "python", "other"])

    platform_keys = list(PLATFORMS.keys())
    platform_choices = [get_platform(k).display_name for k in platform_keys]
    chosen_display = prompt_choice("Chọn agent platform:", platform_choices)
    platform_key = platform_keys[platform_choices.index(chosen_display)]
    print(f"\n  ✅ Platform: {get_platform(platform_key).display_name}")

    mcp_choices = [{"key": k, "display": v["display"]} for k, v in mcp_capabilities.items()]
    selected_mcps = prompt_multi("MCP servers có sẵn:", mcp_choices)
    print(f"  ✅ MCPs: {', '.join(selected_mcps) or 'none'}")

    language = prompt_choice("Ngôn ngữ chính của project:", languages)
    print(f"  ✅ Language: {language}")
    return platform_key, selected_mcps, language


def run_init(target_dir: str, amap_root: Optional[str] = None) -> None:
    """Main init command — scaffold AMAP into a target project."""
    target = Path(target_dir).resolve()
    amap = Path(amap_root).resolve() if amap_root else Path(__file__).resolve().parent.parent.parent

    print(f"\n  AMAP Framework v3.0 — init")
    print(f"  Target: {target}\n  Source: {amap}")

    manifest = load_manifest(amap)
    platform_key, selected_mcps, language = gather_choices(manifest)
    platform = get_platform(platform_key)

    print(f"\n{'─' * 50}")
    print(f"  Platform:  {platform.display_name}")
    print(f"  MCPs:      {', '.join(selected_mcps) or 'none'}")
    print(f"  Language:  {language}")
    print(f"  Target:    {target}\n{'─' * 50}")
    if input("\nTiến hành scaffold? [Y/n]: ").strip().lower() == "n":
        print("\n❌ Đã huỷ.")
        return

    context = platform.build_render_context(selected_mcps, language)
    jinja_env = create_renderer(str(amap))
    print("\nScaffolding AMAP framework...\n")
    stats = scaffold_plugins(
        manifest.get("plugins", []), amap, target, context, jinja_env,
        manifest.get("mcp_capabilities", {}), selected_mcps,
    )
    generate_resolved_config(target, platform_key, selected_mcps, language)

    total = stats["rendered"] + stats["copied"] + stats["dirs"]
    print(f"\n{'═' * 50}")
    print(f"  Done! AMAP scaffolded for {platform.display_name}")
    print(f"  {total} plugins installed, {stats['skipped']} skipped")
    print(f"{'═' * 50}")
    print("\n  Next steps:")
    print("  1. Customize .knowledge-layer/long-term/persona.yaml")
    print("  2. Run /dna-scan to build author DNA")
    print("  3. Start your first task: /task <ticket-or-idea>\n")
```

- [ ] **Step 6: Verify init still works end-to-end**

Run:
```bash
rm -rf /tmp/amap_init && mkdir -p /tmp/amap_init
printf "2\n1,2,3\n3\ny\n" | python -m cli.amap init --target /tmp/amap_init >/dev/null
grep -rn "{{ " /tmp/amap_init/.agent/ --include="*.md" | wc -l
grep -c "mcp__socraticode__codebase_search" /tmp/amap_init/.agent/skills/codebase-explorer/SKILL.md
```
Expected: marker count `0`; codebase_search match count `>= 1`.

- [ ] **Step 7: Run the full test suite**

Run: `python -m pytest cli/tests/ -v`
Expected: all PASS.

- [ ] **Step 8: Commit**

```bash
git add cli/scaffold.py cli/commands/init.py cli/tests/test_scaffold.py
git commit -m "refactor(cli): extract shared scaffold core, add plugin ownership"
```

---

## Task 3: Mark knowledge-layer plugins as user-owned

**Files:**
- Modify: `cli/plugin-manifest.yaml:317-329`
- Modify: `cli/tests/test_scaffold.py`

- [ ] **Step 1: Write the failing test**

Append to `cli/tests/test_scaffold.py`:

```python
def test_knowledge_dirs_are_user_owned(amap_root):
    manifest = load_manifest(amap_root)
    by_name = {p["name"]: p for p in manifest["plugins"]}
    assert get_ownership(by_name["knowledge-active-skeleton"]) == "user"
    assert get_ownership(by_name["knowledge-long-term"]) == "user"
    # Templates remain framework-managed.
    assert get_ownership(by_name["knowledge-templates"]) == "framework"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cli/tests/test_scaffold.py::test_knowledge_dirs_are_user_owned -v`
Expected: FAIL (assert `framework == user`).

- [ ] **Step 3: Add `ownership: user` to the two knowledge plugins**

In `cli/plugin-manifest.yaml`, find the `knowledge-active-skeleton` plugin (around line 317) and add an `ownership` line — only the last line is new:

```yaml
  - name: knowledge-active-skeleton
    type: template
    source: knowledge-active/
    template: false
    output: .knowledge-layer/active/
    copy_dir: true
    ownership: user
```

And the `knowledge-long-term` plugin (around line 324) — only the last line is new:

```yaml
  - name: knowledge-long-term
    type: template
    source: knowledge-long-term/
    template: false
    output: .knowledge-layer/long-term/
    copy_dir: true
    ownership: user
```

(`knowledge-templates` is left unchanged, so it stays framework-owned by default.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cli/tests/test_scaffold.py::test_knowledge_dirs_are_user_owned -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cli/plugin-manifest.yaml cli/tests/test_scaffold.py
git commit -m "feat(cli): mark knowledge-layer dirs as user-owned"
```

---

## Task 4: `amap update` command (atomic, preserves user files)

**Files:**
- Create: `cli/commands/update.py`
- Modify: `cli/amap.py:56-77`
- Create: `cli/tests/test_update.py`

- [ ] **Step 1: Write the failing test**

Create `cli/tests/test_update.py`:

```python
"""Tests for amap update."""

from pathlib import Path

import pytest

from cli.commands.init import run_init
from cli.commands.update import run_update


def _init_claude(target, amap_root, monkeypatch):
    # Feed prompts: platform=2 (claude-code), MCPs=1,2,3, language=3, confirm=y
    answers = iter(["2", "1,2,3", "3", "y"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))
    run_init(target_dir=str(target), amap_root=str(amap_root))


def test_update_preserves_user_file_rerenders_framework(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _init_claude(target, amap_root, monkeypatch)

    # User edits a user-owned file and a framework file.
    persona = target / ".knowledge-layer" / "long-term" / "persona.yaml"
    persona.write_text("MY CUSTOM PERSONA\n", encoding="utf-8")
    skill = target / ".agent" / "skills" / "codebase-explorer" / "SKILL.md"
    skill.write_text("user tampered\n", encoding="utf-8")

    run_update(target_dir=str(target), amap_root=str(amap_root))

    # User file untouched.
    assert persona.read_text(encoding="utf-8") == "MY CUSTOM PERSONA\n"
    # Framework file re-rendered (overwritten) with real tool names, no markers.
    body = skill.read_text(encoding="utf-8")
    assert "user tampered" not in body
    assert "mcp__socraticode__codebase_search" in body
    assert "{{ " not in body


def test_update_aborts_when_no_config(tmp_path, amap_root, capsys):
    target = tmp_path / "empty"
    target.mkdir()
    run_update(target_dir=str(target), amap_root=str(amap_root))
    assert "No AMAP installation" in capsys.readouterr().out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cli/tests/test_update.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cli.commands.update'`.

- [ ] **Step 3: Create `cli/commands/update.py`**

```python
"""amap update — re-render framework files, preserve user files.

Renders into a temp staging dir, verifies zero unresolved markers, then
syncs framework files over the target. Aborts without touching the target
if anything fails.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Optional

import yaml

from cli.platforms import get_platform
from cli.renderer import create_renderer
from cli.scaffold import (
    load_manifest,
    scaffold_plugins,
    verify_no_unresolved,
    sync_tree,
    generate_resolved_config,
)


def _load_resolved(target: Path) -> Optional[dict]:
    config_path = target / ".agent" / "resolved-config.yaml"
    if not config_path.exists():
        return None
    with open(config_path, "r", encoding="utf-8") as f:
        return (yaml.safe_load(f) or {}).get("resolved")


def run_update(target_dir: str, amap_root: Optional[str] = None, reconfigure: bool = False) -> None:
    """Re-render framework files into an existing AMAP project."""
    target = Path(target_dir).resolve()
    amap = Path(amap_root).resolve() if amap_root else Path(__file__).resolve().parent.parent.parent

    resolved = _load_resolved(target)
    if resolved is None:
        print(f"\n  ❌ No AMAP installation found in {target}")
        print(f"     Run: amap init --target {target}")
        return

    manifest = load_manifest(amap)

    if reconfigure:
        from cli.commands.init import gather_choices
        print("\n  AMAP update — reconfigure\n")
        platform_key, selected_mcps, language = gather_choices(manifest)
    else:
        platform_key = resolved.get("platform", "generic")
        selected_mcps = resolved.get("mcps", [])
        language = resolved.get("language", "other")

    platform = get_platform(platform_key)
    context = platform.build_render_context(selected_mcps, language)
    jinja_env = create_renderer(str(amap))

    print(f"\n  Updating AMAP ({platform.display_name})...\n")
    staging = Path(tempfile.mkdtemp(prefix="amap-update-"))
    try:
        scaffold_plugins(
            manifest.get("plugins", []), amap, staging, context, jinja_env,
            manifest.get("mcp_capabilities", {}), selected_mcps,
            only_framework=True,
        )
        offenders = verify_no_unresolved(staging)
        if offenders:
            print("\n  ❌ Update aborted — unresolved template markers in:")
            for p in offenders:
                print(f"     • {p.relative_to(staging)}")
            print("  Target was NOT modified.")
            return
        count = sync_tree(staging, target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    if reconfigure:
        generate_resolved_config(target, platform_key, selected_mcps, language)

    print(f"\n  ✅ Updated {count} framework files. User files preserved.\n")
```

- [ ] **Step 4: Wire the `update` subcommand into `cli/amap.py`**

In `cli/amap.py`, after the `status` subparser block (currently ending at line 65), add a new subparser. Insert before `args = parser.parse_args()`:

```python
    # ─── update ───
    update_parser = subparsers.add_parser(
        "update",
        help="Re-render framework files in an existing AMAP project",
    )
    update_parser.add_argument(
        "--target", default=".",
        help="Project directory to update (default: current directory)",
    )
    update_parser.add_argument(
        "--source", default=None,
        help="AMAP repo root (default: auto-detect from CLI location)",
    )
    update_parser.add_argument(
        "--reconfigure", action="store_true",
        help="Re-prompt platform/MCP/language before re-rendering",
    )
```

Then in the dispatch block, add a branch after the `init` branch (before `elif args.command == "status"`):

```python
    elif args.command == "update":
        from cli.commands.update import run_update
        run_update(target_dir=args.target, amap_root=args.source, reconfigure=args.reconfigure)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest cli/tests/test_update.py -v`
Expected: both PASS.

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest cli/tests/ -v`
Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add cli/commands/update.py cli/amap.py cli/tests/test_update.py
git commit -m "feat(cli): add atomic amap update preserving user files"
```

---

## Task 5: `amap update --reconfigure` (switch IDE)

**Files:**
- Modify: `cli/tests/test_update.py`

(The `--reconfigure` code path already exists from Task 4; this task verifies the IDE-switch behavior end-to-end.)

- [ ] **Step 1: Write the failing test**

Append to `cli/tests/test_update.py`:

```python
def test_reconfigure_switches_platform_keeps_user_files(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _init_claude(target, amap_root, monkeypatch)

    persona = target / ".knowledge-layer" / "long-term" / "persona.yaml"
    persona.write_text("KEEP ME\n", encoding="utf-8")

    skill = target / ".agent" / "skills" / "codebase-explorer" / "SKILL.md"
    assert "mcp__socraticode__codebase_search" in skill.read_text(encoding="utf-8")

    # Reconfigure to antigravity (platform=1), MCPs=1,2,3, language=3.
    answers = iter(["1", "1,2,3", "3"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))
    run_update(target_dir=str(target), amap_root=str(amap_root), reconfigure=True)

    body = skill.read_text(encoding="utf-8")
    # Antigravity uses single-underscore MCP prefix.
    assert "mcp_socraticode_codebase_search" in body
    assert "mcp__socraticode__codebase_search" not in body
    assert persona.read_text(encoding="utf-8") == "KEEP ME\n"

    # resolved-config now records antigravity.
    cfg = (target / ".agent" / "resolved-config.yaml").read_text(encoding="utf-8")
    assert "antigravity" in cfg
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest cli/tests/test_update.py::test_reconfigure_switches_platform_keeps_user_files -v`
Expected: PASS (the reconfigure path was implemented in Task 4).

If it fails, debug `run_update(reconfigure=True)` against the assertions before proceeding — do not weaken the test.

- [ ] **Step 3: Commit**

```bash
git add cli/tests/test_update.py
git commit -m "test(cli): verify update --reconfigure switches platform safely"
```

---

## Task 6: `install.sh` wrapper

**Files:**
- Create: `install.sh` (repo root)

- [ ] **Step 1: Create `install.sh`**

```bash
#!/usr/bin/env bash
# AMAP installer — bootstrap a venv and scaffold/update AMAP into a target project.
#
# Usage: ./install.sh /path/to/your/project
set -euo pipefail

AMAP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$AMAP_ROOT/.venv"

TARGET="${1:-}"
if [ -z "$TARGET" ]; then
  echo "Usage: ./install.sh /path/to/your/project"
  exit 1
fi
if [ ! -d "$TARGET" ]; then
  echo "❌ Target directory does not exist: $TARGET"
  exit 1
fi

# Require python3 >= 3.8.
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 not found. Please install Python 3.8 or newer."
  exit 1
fi

# Create the venv on first run and install dependencies.
if [ ! -d "$VENV" ]; then
  echo "→ Creating virtualenv at $VENV"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
  "$VENV/bin/pip" install --quiet "jinja2>=3.1" "pyyaml>=6.0"
fi

PY="$VENV/bin/python"

# Route to update if AMAP already installed, else init.
if [ -f "$TARGET/.agent/resolved-config.yaml" ]; then
  echo "→ Existing AMAP install detected — updating."
  ( cd "$AMAP_ROOT" && "$PY" -m cli.amap update --target "$TARGET" )
else
  echo "→ Fresh install."
  ( cd "$AMAP_ROOT" && "$PY" -m cli.amap init --target "$TARGET" )
fi
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x install.sh`

- [ ] **Step 3: Verify fresh install via install.sh**

Run:
```bash
rm -rf /tmp/amap_sh && mkdir -p /tmp/amap_sh
printf "2\n1,2,3\n3\ny\n" | ./install.sh /tmp/amap_sh >/dev/null
test -f /tmp/amap_sh/.agent/resolved-config.yaml && echo "INIT_OK"
grep -rn "{{ " /tmp/amap_sh/.agent/ --include="*.md" | wc -l
```
Expected: prints `INIT_OK`; marker count `0`.

- [ ] **Step 4: Verify re-run routes to update**

Run:
```bash
echo "MINE" > /tmp/amap_sh/.knowledge-layer/long-term/persona.yaml
./install.sh /tmp/amap_sh >/dev/null
cat /tmp/amap_sh/.knowledge-layer/long-term/persona.yaml
```
Expected: prints `MINE` (update preserved the user file; no prompts appeared).

- [ ] **Step 5: Commit**

```bash
git add install.sh
git commit -m "feat: add install.sh wrapper routing to init/update"
```

---

## Task 7: README usage update

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Locate the existing quick-start section**

Run: `grep -n "pip install\|amap init\|Quick start\|## Cài" README.md`
Expected: shows the current install instructions (added in the SP3 migration).

- [ ] **Step 2: Replace the install instructions with the install.sh flow**

Update the quick-start block so it reads (adapt the surrounding prose/language to match the existing README voice):

````markdown
## Quick start

```bash
git clone <this-repo> amap && cd amap
./install.sh /path/to/your/project
```

The installer asks for your IDE/platform, MCP servers, and primary language,
then scaffolds AMAP into your project with tool names already resolved.

**Update later** (new AMAP version, or switch IDE):

```bash
./install.sh /path/to/your/project          # refresh framework, keep your customizations
# or, from the amap repo, to change platform/MCPs:
.venv/bin/python -m cli.amap update --target /path/to/your/project --reconfigure
```

Framework files (skills, workflows, rules) are re-rendered on update.
Your files under `.knowledge-layer/long-term/` and `.knowledge-layer/active/`
are never overwritten.
````

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document install.sh init/update flow"
```

---

## Self-Review Notes

- **Spec coverage:** §2 install.sh → Task 6; §3 command surface (init/update/reconfigure) → Tasks 4-5; §4 ownership → Tasks 2-3; §5 atomic update → Task 4 (staging + verify + sync); §6 no-swallow → Task 1 + scaffold_plugin in Task 2; §7 testing → Tasks 1-5; §1 distribution model → Tasks 6-7. All covered.
- **Type/name consistency:** `scaffold_plugins`, `scaffold_plugin`, `get_ownership`, `verify_no_unresolved`, `sync_tree`, `generate_resolved_config`, `gather_choices`, `load_manifest` are defined once (Task 2) and reused with identical signatures in Tasks 4-5.
- **Known limitation (spec §8):** an `ownership: user` directory will not receive newly-added framework template files on update — accepted, not implemented here.
