# Platform-Native Framework Root Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `amap init` scaffold the full AMAP runtime into each selected platform's native framework root, with no `.amap/` created for Antigravity, Codex, or Claude Code.

**Architecture:** Add `platform.framework_root` as the canonical target root for rendered AMAP runtime files. Render manifest outputs and framework prose through that root, make resolved-config lookup root-aware, and disable secondary native skill mirroring for platforms whose canonical root already contains `skills/`. Keep Generic on `.amap/`.

**Tech Stack:** Python 3.8+, PyYAML, Jinja2, pytest, bash `install.sh`, Markdown/YAML framework templates.

## Global Constraints

- Antigravity canonical framework root is `.agents/`.
- Codex canonical framework root is `.agents/`.
- Claude Code canonical framework root is `.claude/`.
- Generic canonical framework root is `.amap/`.
- Cursor is out of scope for this change.
- Fresh Antigravity, Codex, and Claude Code installs must not create `.amap/`.
- Existing legacy `.amap/` directories must not be deleted automatically.
- Platform and language prompts are single-select checkbox-style prompts.
- MCP prompt is multi-select checkbox-style.
- Each target project has one primary language.
- Source repository template content may remain under `.amap/`.
- No application code in target projects is changed.

---

## File Structure

Modify:

- `cli/platforms/base.py`: add `framework_root` to the platform API and render context.
- `cli/platforms/antigravity.py`: set `framework_root = ".agents"` and disable mirror export.
- `cli/platforms/codex.py`: set `framework_root = ".agents"` and disable mirror export.
- `cli/platforms/claude_code.py`: set `framework_root = ".claude"` and disable mirror export.
- `cli/platforms/__init__.py`: remove Cursor from the selectable platform registry for this change.
- `cli/plugin-manifest.yaml`: render all runtime output paths through `{{ platform.framework_root }}`.
- `cli/scaffold.py`: make resolved-config generation/loading root-aware and expose warnings for stale legacy roots.
- `cli/commands/init.py`: pass platform into resolved-config generation, implement checkbox-style prompt helpers, and print platform-root-aware next steps.
- `cli/commands/update.py`: load/write selected root, reconfigure safely, and warn about legacy `.amap`.
- `cli/commands/status.py`: report skills/workflows/knowledge/DNA from the resolved framework root.
- `install.sh`: detect installs in `.agents`, `.claude`, or `.amap`.
- `AGENTS.md`: templatize AMAP runtime paths with `{{ platform.framework_root }}`.
- `.amap/rules/**/*.md`, `.amap/skills/**/*.md`, `.amap/workflows/**/*.md`, `.amap/procedures/**/*.md`, `.amap/knowledge/**/*.md`, `.amap/tools/**/*.md`, `.amap/profiles/**/*.yaml`: templatize active runtime paths.
- `README.md`, `docs/amap-file-ownership-policy.md`: update platform root documentation.

Modify tests:

- `cli/tests/test_platforms.py`: assert platform roots and disabled mirror export for native-root platforms.
- `cli/tests/test_scaffold.py`: cover root-aware resolved config and manifest rendering behavior.
- `cli/tests/test_init.py`: assert no `.amap/` for Antigravity, Codex, Claude Code, and verify Generic still uses `.amap/`.
- `cli/tests/test_update.py`: cover legacy config lookup, reconfigure root switching, and warning-only stale `.amap`.
- `cli/tests/test_status.py`: assert status reads from selected framework root.
- Add or extend prompt tests in `cli/tests/test_init.py` for single- and multi-select fallback behavior.

Do not modify:

- `report-dual-directory-issue.md`, unless the user separately asks to revise the report.
- Existing unrelated local edits in `AGENTS.md`; if touched for this task, inspect and preserve user changes.

## Task 1: Add Platform Framework Roots

**Files:**
- Modify: `cli/platforms/base.py`
- Modify: `cli/platforms/antigravity.py`
- Modify: `cli/platforms/codex.py`
- Modify: `cli/platforms/claude_code.py`
- Modify: `cli/platforms/__init__.py`
- Modify: `cli/tests/test_platforms.py`

**Interfaces:**
- Produces: `BasePlatform.framework_root: str`
- Produces: render context key `context["platform"]["framework_root"]`
- Produces: native-root platforms return `native_skill_export is None`
- Consumes: existing `get_platform(platform_key)` registry

- [ ] **Step 1: Write failing platform-root tests**

Add these tests to `cli/tests/test_platforms.py`:

```python
from cli.platforms import PLATFORMS, get_platform
from cli.platforms.generic import GenericPlatform


def test_platform_framework_roots():
    assert get_platform("antigravity").framework_root == ".agents"
    assert get_platform("codex").framework_root == ".agents"
    assert get_platform("claude-code").framework_root == ".claude"
    assert get_platform("generic").framework_root == ".amap"


def test_native_root_platforms_do_not_need_skill_mirror():
    assert get_platform("antigravity").native_skill_export is None
    assert get_platform("codex").native_skill_export is None
    assert get_platform("claude-code").native_skill_export is None


def test_render_context_includes_framework_root():
    ctx = get_platform("antigravity").build_render_context(["socraticode"], "python")
    assert ctx["platform"]["framework_root"] == ".agents"


def test_cursor_is_out_of_scope_for_platform_selection():
    assert "cursor" not in PLATFORMS


def test_generic_platform_defaults_to_amap_root():
    assert GenericPlatform().framework_root == ".amap"
    assert GenericPlatform().native_skill_export is None
```

Remove or update old assertions that expect Antigravity, Codex, or Claude Code to have `native_skill_export`.

- [ ] **Step 2: Run the failing tests**

Run:

```bash
python3 -m pytest cli/tests/test_platforms.py -v
```

Expected: FAIL because `framework_root` does not exist yet, native exports are still configured, and Cursor is still registered.

- [ ] **Step 3: Implement `framework_root` in `BasePlatform`**

In `cli/platforms/base.py`, add the property and render context entry:

```python
    @property
    def framework_root(self) -> str:
        """Canonical AMAP runtime root inside a target project.

        This is where rules, skills, workflows, procedures, tools, profiles,
        knowledge, and resolved-config.yaml are scaffolded for the platform.
        """
        return ".amap"
```

Update `build_render_context()`:

```python
        return {
            "platform": {
                "name": self.name,
                "display_name": self.display_name,
                "config_entry_point": self.config_entry_point,
                "framework_root": self.framework_root,
            },
            "tools": self.tool_mapping,
            "capabilities": self.capabilities,
            "mcps": mcps,
            "language": language,
            "framework_version": "3.0",
        }
```

- [ ] **Step 4: Override platform roots and disable mirror export**

In `cli/platforms/antigravity.py`:

```python
    framework_root = ".agents"
    native_skill_export = None
```

In `cli/platforms/codex.py`:

```python
    framework_root = ".agents"
    native_skill_export = None
```

In `cli/platforms/claude_code.py`:

```python
    framework_root = ".claude"
    native_skill_export = None
```

Update notes so they describe direct framework roots, for example Antigravity:

```python
    notes = [
        "AGENTS.md is loaded via user_rules in Antigravity config",
        "AMAP runtime scaffolds into .agents/",
        "MCP tools use prefix: mcp_<server>_<tool>",
        "Supports browser_subagent for visual tasks",
    ]
```

- [ ] **Step 5: Remove Cursor from selectable platform registry**

In `cli/platforms/__init__.py`, remove the `CursorPlatform` import and `"cursor": CursorPlatform` registry entry.

Keep the file deterministic. The expected order after removal is:

```python
PLATFORMS = {
    "antigravity": AntigravityPlatform,
    "claude-code": ClaudeCodePlatform,
    "generic": GenericPlatform,
    "codex": CodexPlatform,
}
```

- [ ] **Step 6: Run platform tests**

Run:

```bash
python3 -m pytest cli/tests/test_platforms.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add cli/platforms/base.py cli/platforms/antigravity.py cli/platforms/codex.py cli/platforms/claude_code.py cli/platforms/__init__.py cli/tests/test_platforms.py
git commit -m "feat(cli): add platform framework roots"
```

## Task 2: Make Resolved Config Root-Aware

**Files:**
- Modify: `cli/scaffold.py`
- Modify: `cli/tests/test_scaffold.py`

**Interfaces:**
- Produces: `resolved_config_candidates(target: Path) -> list[Path]`
- Produces: `generate_resolved_config(target_dir: Path, platform, selected_mcps: list[str], language: str) -> None`
- Produces: `load_resolved_config(target: Path) -> Optional[dict]` with `framework_root` included in the returned dict
- Consumes: `platform.framework_root`

- [ ] **Step 1: Write failing resolved-config tests**

Add to `cli/tests/test_scaffold.py`:

```python
from cli.platforms import get_platform
from cli.scaffold import generate_resolved_config, load_resolved_config, resolved_config_candidates


def test_resolved_config_candidates_include_native_and_legacy_roots(tmp_path):
    candidates = [p.relative_to(tmp_path).as_posix() for p in resolved_config_candidates(tmp_path)]
    assert candidates == [
        ".agents/resolved-config.yaml",
        ".claude/resolved-config.yaml",
        ".amap/resolved-config.yaml",
    ]


def test_generate_resolved_config_uses_platform_framework_root(tmp_path):
    platform = get_platform("antigravity")
    generate_resolved_config(tmp_path, platform, ["socraticode"], "python")

    config = tmp_path / ".agents" / "resolved-config.yaml"
    assert config.exists()
    assert not (tmp_path / ".amap").exists()
    body = config.read_text(encoding="utf-8")
    assert "platform: antigravity" in body
    assert "framework_root: .agents" in body


def test_load_resolved_config_reads_agents_config(tmp_path):
    config = tmp_path / ".agents" / "resolved-config.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(
        "resolved:\n"
        "  platform: antigravity\n"
        "  framework_root: .agents\n"
        "  mcps: [socraticode]\n"
        "  language: python\n",
        encoding="utf-8",
    )

    resolved = load_resolved_config(tmp_path)
    assert resolved["platform"] == "antigravity"
    assert resolved["framework_root"] == ".agents"


def test_load_resolved_config_reads_legacy_amap_config(tmp_path):
    _write_resolved_config(
        tmp_path,
        "resolved:\n  platform: generic\n  mcps: []\n  language: python\n",
    )

    resolved = load_resolved_config(tmp_path)
    assert resolved["platform"] == "generic"
    assert resolved["framework_root"] == ".amap"
```

Update old `_write_resolved_config()` helper only if necessary; keep it writing `.amap/resolved-config.yaml` for legacy tests.

- [ ] **Step 2: Run failing scaffold tests**

Run:

```bash
python3 -m pytest cli/tests/test_scaffold.py::test_resolved_config_candidates_include_native_and_legacy_roots cli/tests/test_scaffold.py::test_generate_resolved_config_uses_platform_framework_root cli/tests/test_scaffold.py::test_load_resolved_config_reads_agents_config cli/tests/test_scaffold.py::test_load_resolved_config_reads_legacy_amap_config -v
```

Expected: FAIL because candidate lookup and new signature do not exist.

- [ ] **Step 3: Implement root-aware config helpers**

In `cli/scaffold.py`, add:

```python
def resolved_config_candidates(target: Path) -> List[Path]:
    """Return supported resolved-config locations in preference order."""
    return [
        target / ".agents" / "resolved-config.yaml",
        target / ".claude" / "resolved-config.yaml",
        target / ".amap" / "resolved-config.yaml",
    ]
```

Replace `generate_resolved_config()` with:

```python
def generate_resolved_config(
    target_dir: Path, platform, selected_mcps: List[str], language: str
) -> None:
    """Write resolved-config.yaml under the platform's framework root."""
    config_path = target_dir / platform.framework_root / "resolved-config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        f.write("# AMAP Resolved Configuration\n")
        f.write("# Generated by: amap init / amap update --reconfigure\n")
        f.write("# The adapter layer is pre-resolved — no runtime lookup needed.\n\n")
        yaml.dump(
            {"resolved": {
                "platform": platform.name,
                "framework_root": platform.framework_root,
                "mcps": selected_mcps,
                "language": language,
                "framework_version": "3.0",
            }},
            f, default_flow_style=False, allow_unicode=True,
        )
```

Replace `load_resolved_config()` with:

```python
def _read_resolved_config(config_path: Path) -> Optional[dict]:
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError:
        return None
    resolved = (data or {}).get("resolved")
    if not isinstance(resolved, dict):
        return None
    return resolved


def load_resolved_config(target: Path) -> Optional[dict]:
    """Load resolved config from native or legacy roots."""
    from cli.platforms import get_platform

    valid = []
    for config_path in resolved_config_candidates(target):
        if not config_path.exists():
            continue
        resolved = _read_resolved_config(config_path)
        if resolved is None:
            continue
        platform_key = resolved.get("platform", "generic")
        try:
            expected_root = get_platform(platform_key).framework_root
        except ValueError:
            expected_root = ".amap"
        resolved.setdefault("framework_root", expected_root)
        resolved["_config_path"] = str(config_path)
        valid.append(resolved)

    if not valid:
        return None

    for resolved in valid:
        path = Path(resolved["_config_path"])
        if path.parent.as_posix().endswith(resolved["framework_root"]):
            return resolved

    return valid[0]
```

- [ ] **Step 4: Update callers for new `generate_resolved_config()` signature**

In `cli/commands/init.py`, change:

```python
generate_resolved_config(target, platform_key, selected_mcps, language)
```

to:

```python
generate_resolved_config(target, platform, selected_mcps, language)
```

In `cli/commands/update.py`, change:

```python
generate_resolved_config(target, platform_key, selected_mcps, language)
```

to:

```python
generate_resolved_config(target, platform, selected_mcps, language)
```

- [ ] **Step 5: Run scaffold tests**

Run:

```bash
python3 -m pytest cli/tests/test_scaffold.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add cli/scaffold.py cli/commands/init.py cli/commands/update.py cli/tests/test_scaffold.py
git commit -m "feat(cli): resolve config from platform roots"
```

## Task 3: Render Manifest Outputs Into `framework_root`

**Files:**
- Modify: `cli/plugin-manifest.yaml`
- Modify: `cli/tests/test_init.py`
- Modify: `cli/tests/test_scaffold.py`

**Interfaces:**
- Consumes: `context["platform"]["framework_root"]`
- Produces: rendered plugin output under selected framework root

- [ ] **Step 1: Write failing init invariant tests**

Update `cli/tests/test_init.py` platform indices after Cursor removal:

```txt
1 = antigravity
2 = claude-code
3 = generic
4 = codex
```

Add or update tests:

```python
def test_init_antigravity_uses_agents_as_only_framework_root(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["1", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert not (target / ".amap").exists()
    assert (target / ".agents" / "resolved-config.yaml").exists()
    assert (target / ".agents" / "rules" / "RULES.md").exists()
    assert (target / ".agents" / "skills" / "requirement-analyst" / "SKILL.md").exists()
    assert (target / ".agents" / "knowledge" / "long-term" / "author-dna.yaml").exists()
    assert (target / "AGENTS.md").exists()


def test_init_codex_uses_agents_as_only_framework_root(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["4", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert not (target / ".amap").exists()
    assert (target / ".agents" / "resolved-config.yaml").exists()
    assert (target / ".agents" / "skills" / "requirement-analyst" / "SKILL.md").exists()


def test_init_claude_uses_claude_as_only_framework_root(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert not (target / ".amap").exists()
    assert (target / ".claude" / "resolved-config.yaml").exists()
    assert (target / ".claude" / "rules" / "RULES.md").exists()
    assert (target / ".claude" / "skills" / "requirement-analyst" / "SKILL.md").exists()
    assert (target / "CLAUDE.md").exists()


def test_init_generic_keeps_amap_framework_root(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["3", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    assert (target / ".amap" / "resolved-config.yaml").exists()
    assert (target / ".amap" / "skills" / "requirement-analyst" / "SKILL.md").exists()
    assert not (target / ".agents").exists()
    assert not (target / ".claude" / "skills").exists()
```

Remove old tests that expect native mirror exports into `.agents/skills` or `.claude/skills` in addition to `.amap`.

- [ ] **Step 2: Run failing init tests**

Run:

```bash
python3 -m pytest cli/tests/test_init.py -v
```

Expected: FAIL because manifest still outputs `.amap/...`.

- [ ] **Step 3: Update manifest paths**

In `cli/plugin-manifest.yaml`, replace every runtime output prefix:

```yaml
output: .amap/
```

with:

```yaml
output: "{{ platform.framework_root }}/
```

Concrete examples:

```yaml
  - name: rules-manifest
    type: rule
    source: rules/RULES.md
    template: false
    output: "{{ platform.framework_root }}/rules/RULES.md"

  - name: requirement-analyst
    type: skill
    source: skills/requirement-analyst/
    template: false
    output: "{{ platform.framework_root }}/skills/requirement-analyst/"
    copy_dir: true

  - name: knowledge-long-term
    type: template
    source: knowledge-long-term/
    template: false
    output: "{{ platform.framework_root }}/knowledge/long-term/"
    copy_dir: true
    ownership: user
```

Apply this to:

```txt
rules
skills
workflows
procedures
tools
knowledge/templates
knowledge/active
knowledge/long-term
profiles if present in the manifest
```

- [ ] **Step 4: Keep source mapping unchanged**

Do not change `SOURCE_MAP` in `cli/scaffold.py` for this task. It should continue mapping source prefixes to the source repo's `.amap/...` directories:

```python
"skills/": ".amap/skills/",
"workflows/": ".amap/workflows/",
```

- [ ] **Step 5: Run init tests**

Run:

```bash
python3 -m pytest cli/tests/test_init.py -v
```

Expected: PASS after deleting/updating old mirror-export assertions.

- [ ] **Step 6: Commit**

```bash
git add cli/plugin-manifest.yaml cli/tests/test_init.py cli/tests/test_scaffold.py
git commit -m "feat(cli): scaffold runtime into platform root"
```

## Task 4: Make Init Prompts Checkbox-Style

**Files:**
- Modify: `cli/commands/init.py`
- Modify: `cli/tests/test_init.py`

**Interfaces:**
- Produces: `prompt_single_checkbox(message: str, choices: list[str], default: int = 0) -> str`
- Produces: `prompt_multi_checkbox(message: str, choices: list[dict]) -> list[str]`
- Consumes: existing `gather_choices(manifest)` contract returning `(platform_key, selected_mcps, language)`

- [ ] **Step 1: Write prompt helper tests**

Add to `cli/tests/test_init.py`:

```python
from cli.commands.init import prompt_multi_checkbox, prompt_single_checkbox


def test_prompt_single_checkbox_returns_default_on_enter(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")
    assert prompt_single_checkbox("Choose", ["A", "B"], default=1) == "B"


def test_prompt_single_checkbox_accepts_number(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *a, **k: "1")
    assert prompt_single_checkbox("Choose", ["A", "B"], default=1) == "A"


def test_prompt_multi_checkbox_returns_empty_on_enter(monkeypatch):
    choices = [{"key": "a", "display": "A"}, {"key": "b", "display": "B"}]
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")
    assert prompt_multi_checkbox("MCPs", choices) == []


def test_prompt_multi_checkbox_accepts_comma_numbers(monkeypatch):
    choices = [{"key": "a", "display": "A"}, {"key": "b", "display": "B"}]
    monkeypatch.setattr("builtins.input", lambda *a, **k: "1,2")
    assert prompt_multi_checkbox("MCPs", choices) == ["a", "b"]
```

- [ ] **Step 2: Run failing prompt tests**

Run:

```bash
python3 -m pytest cli/tests/test_init.py::test_prompt_single_checkbox_returns_default_on_enter cli/tests/test_init.py::test_prompt_single_checkbox_accepts_number cli/tests/test_init.py::test_prompt_multi_checkbox_returns_empty_on_enter cli/tests/test_init.py::test_prompt_multi_checkbox_accepts_comma_numbers -v
```

Expected: FAIL because helper names do not exist.

- [ ] **Step 3: Implement single-select checkbox fallback**

In `cli/commands/init.py`, replace or wrap `prompt_choice()` with:

```python
def prompt_single_checkbox(message: str, choices: List[str], default: int = 0) -> str:
    """Interactive single-select prompt displayed as checkbox-style choices.

    The fallback input remains numeric to keep tests and plain terminals
    deterministic.
    """
    print(f"\n{message}")
    for i, choice in enumerate(choices):
        marker = "x" if i == default else " "
        print(f"  [{marker}] [{i + 1}] {choice}")
    while True:
        raw = input(f"\nChọn một mục (1-{len(choices)}) [{default + 1}]: ").strip()
        if not raw:
            return choices[default]
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass
        print(f"  ⚠️  Chọn số từ 1 đến {len(choices)}")
```

- [ ] **Step 4: Implement multi-select checkbox fallback**

In `cli/commands/init.py`, replace or wrap `prompt_multi()` with:

```python
def prompt_multi_checkbox(message: str, choices: List[dict]) -> List[str]:
    """Interactive multi-select prompt displayed as checkbox-style choices."""
    print(f"\n{message}")
    for i, choice in enumerate(choices):
        print(f"  [ ] [{i + 1}] {choice['display']}")
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
```

- [ ] **Step 5: Update `gather_choices()` to use the new helpers**

Replace:

```python
chosen_display = prompt_choice("Chọn agent platform:", platform_choices)
```

with:

```python
chosen_display = prompt_single_checkbox("Chọn agent platform:", platform_choices)
```

Replace:

```python
selected_mcps = prompt_multi("MCP servers có sẵn:", mcp_choices)
```

with:

```python
selected_mcps = prompt_multi_checkbox("MCP servers có sẵn:", mcp_choices)
```

Replace:

```python
language = prompt_choice("Ngôn ngữ chính của project:", languages)
```

with:

```python
language = prompt_single_checkbox("Ngôn ngữ chính của project:", languages)
```

- [ ] **Step 6: Run prompt and init tests**

Run:

```bash
python3 -m pytest cli/tests/test_init.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add cli/commands/init.py cli/tests/test_init.py
git commit -m "feat(cli): add checkbox-style init prompts"
```

## Task 5: Make Update, Status, and Installer Use Platform Roots

**Files:**
- Modify: `cli/commands/update.py`
- Modify: `cli/commands/status.py`
- Modify: `install.sh`
- Modify: `cli/tests/test_update.py`
- Modify: `cli/tests/test_status.py`

**Interfaces:**
- Consumes: `resolved["framework_root"]`
- Produces: root-aware update/status behavior
- Produces: warning-only behavior for stale `.amap`

- [ ] **Step 1: Write update tests for platform roots**

Update `cli/tests/test_update.py` platform indices after Cursor removal.

Add tests:

```python
def test_update_uses_resolved_framework_root(tmp_path, amap_root, monkeypatch):
    target = tmp_path / "proj"
    answers = iter(["1", "1,2,3", "3", "y"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))
    run_init(target_dir=str(target), amap_root=str(amap_root))

    skill = target / ".agents" / "skills" / "codebase-explorer" / "SKILL.md"
    skill.write_text("tampered\n", encoding="utf-8")

    run_update(target_dir=str(target), amap_root=str(amap_root))

    assert "tampered" not in skill.read_text(encoding="utf-8")
    assert not (target / ".amap").exists()


def test_reconfigure_to_claude_writes_claude_root_and_warns_about_legacy_amap(
    tmp_path, amap_root, monkeypatch, capsys,
):
    target = tmp_path / "proj"
    answers = iter(["3", "1,2,3", "3", "y"])  # generic first
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))
    run_init(target_dir=str(target), amap_root=str(amap_root))
    assert (target / ".amap").exists()

    answers = iter(["2", "1,2,3", "3"])  # reconfigure to claude-code
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))
    run_update(target_dir=str(target), amap_root=str(amap_root), reconfigure=True)

    assert (target / ".claude" / "resolved-config.yaml").exists()
    assert (target / ".claude" / "skills" / "requirement-analyst" / "SKILL.md").exists()
    assert (target / ".amap").exists()
    assert "legacy .amap" in capsys.readouterr().out
```

- [ ] **Step 2: Write status tests for platform roots**

In `cli/tests/test_status.py`, add:

```python
from cli.commands.status import run_status


def test_status_reads_skills_from_agents_root(tmp_path, capsys):
    root = tmp_path / ".agents"
    (root / "skills" / "requirement-analyst").mkdir(parents=True)
    (root / "workflows").mkdir(parents=True)
    (root / "workflows" / "task.md").write_text("# task\n", encoding="utf-8")
    (root / "knowledge" / "active").mkdir(parents=True)
    (root / "knowledge" / "archive").mkdir(parents=True)
    (root / "knowledge" / "long-term").mkdir(parents=True)
    (root / "knowledge" / "long-term" / "author-dna.yaml").write_text("meta:\n  status: approved\n", encoding="utf-8")
    (root / "resolved-config.yaml").write_text(
        "resolved:\n"
        "  platform: antigravity\n"
        "  framework_root: .agents\n"
        "  mcps: []\n"
        "  language: python\n"
        "  framework_version: '3.0'\n",
        encoding="utf-8",
    )
    (tmp_path / "AGENTS.md").write_text("# agents\n", encoding="utf-8")

    run_status(str(tmp_path))

    out = capsys.readouterr().out
    assert "Platform:  antigravity" in out
    assert "requirement-analyst" in out
    assert "/task" in out
    assert "Author DNA: approved" in out
```

- [ ] **Step 3: Run failing update/status tests**

Run:

```bash
python3 -m pytest cli/tests/test_update.py cli/tests/test_status.py -v
```

Expected: FAIL where code still hardcodes `.amap`.

- [ ] **Step 4: Update `run_update()` paths**

In `cli/commands/update.py`, derive:

```python
framework_root = resolved.get("framework_root", platform.framework_root)
```

When reconfiguring, after selecting `platform`, use `platform.framework_root` for new rendering. Keep `scaffold_plugins(..., staging, context, ...)` unchanged because manifest output already contains the root.

After sync and config write, warn when legacy `.amap` remains beside native roots:

```python
def warn_legacy_amap(target: Path, platform) -> None:
    legacy = target / ".amap"
    if platform.framework_root != ".amap" and legacy.exists():
        print(f"  ⚠️  legacy .amap remains at {legacy}; not removed automatically.")
```

Call it before final success output.

- [ ] **Step 5: Update stale root cleanup to avoid deleting `.amap`**

Remove old native export cleanup logic that deletes `.agents/skills` or `.claude/skills` as mirror directories. These are now framework roots. Reconfigure must not delete a root automatically if it could contain knowledge.

Acceptable warning behavior:

```python
for root in [".agents", ".claude", ".amap"]:
    root_path = target / root
    if root != platform.framework_root and root_path.exists():
        print(f"  ⚠️  stale framework root detected: {root_path}")
```

Do not call `shutil.rmtree()` on framework roots in this task.

- [ ] **Step 6: Update `run_status()` paths**

In `cli/commands/status.py`, after loading config:

```python
framework_root = resolved.get("framework_root", get_platform(platform).framework_root)
root = target / framework_root
```

Replace hardcoded paths:

```python
skills_dir = target / ".amap" / "skills"
workflows_dir = target / ".amap" / "workflows"
kl_active = target / ".amap/knowledge" / "active"
kl_archive = target / ".amap/knowledge" / "archive"
dna = target / ".amap/knowledge" / "long-term" / "author-dna.yaml"
dna_draft = target / ".amap/knowledge" / "long-term" / "author-dna.draft.yaml"
```

with:

```python
skills_dir = root / "skills"
workflows_dir = root / "workflows"
kl_active = root / "knowledge" / "active"
kl_archive = root / "knowledge" / "archive"
dna = root / "knowledge" / "long-term" / "author-dna.yaml"
dna_draft = root / "knowledge" / "long-term" / "author-dna.draft.yaml"
```

Print the root:

```python
print(f"  🧭 Root:      {framework_root}")
```

- [ ] **Step 7: Update `install.sh` detection**

Replace:

```bash
if [ -f "$TARGET/.amap/resolved-config.yaml" ]; then
```

with:

```bash
if [ -f "$TARGET/.agents/resolved-config.yaml" ] || \
   [ -f "$TARGET/.claude/resolved-config.yaml" ] || \
   [ -f "$TARGET/.amap/resolved-config.yaml" ]; then
```

- [ ] **Step 8: Run update/status tests**

Run:

```bash
python3 -m pytest cli/tests/test_update.py cli/tests/test_status.py -v
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add cli/commands/update.py cli/commands/status.py install.sh cli/tests/test_update.py cli/tests/test_status.py
git commit -m "feat(cli): use platform roots for update and status"
```

## Task 6: Templatize Framework Runtime Path References

**Files:**
- Modify: `AGENTS.md`
- Modify: `.amap/rules/*.md`
- Modify: `.amap/skills/**/*.md`
- Modify: `.amap/workflows/*.md`
- Modify: `.amap/procedures/*.md`
- Modify: `.amap/knowledge/**/*.md`
- Modify: `.amap/tools/**/*.md`
- Modify: `.amap/profiles/**/*.yaml`
- Modify: `cli/tests/test_init.py`

**Interfaces:**
- Consumes: Jinja render context `platform.framework_root`
- Produces: rendered runtime instructions with platform-specific paths

- [ ] **Step 1: Add rendered path invariant test**

In `cli/tests/test_init.py`, add:

```python
def test_antigravity_rendered_framework_files_do_not_reference_active_amap_paths(
    tmp_path, amap_root, monkeypatch,
):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["1", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    offenders = []
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".yaml", ".yml", ".txt"} and path.name != "AGENTS.md":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if ".amap/" in text and "legacy .amap" not in text and "source repo" not in text:
            offenders.append(path.relative_to(target).as_posix())
    assert offenders == []
```

- [ ] **Step 2: Run failing invariant test**

Run:

```bash
python3 -m pytest cli/tests/test_init.py::test_antigravity_rendered_framework_files_do_not_reference_active_amap_paths -v
```

Expected: FAIL because many rendered files still contain `.amap/`.

- [ ] **Step 3: Mechanically replace active runtime path references**

Use `rg` to inspect first:

```bash
rg -n "\\.amap/" AGENTS.md .amap README.md docs/amap-file-ownership-policy.md
```

Replace active runtime references like:

```txt
.amap/rules
.amap/skills
.amap/workflows
.amap/procedures
.amap/tools
.amap/profiles
.amap/knowledge
```

with:

```txt
{{ platform.framework_root }}/rules
{{ platform.framework_root }}/skills
{{ platform.framework_root }}/workflows
{{ platform.framework_root }}/procedures
{{ platform.framework_root }}/tools
{{ platform.framework_root }}/profiles
{{ platform.framework_root }}/knowledge
```

Do not replace source-repo explanations where `.amap/` explicitly describes the AMAP repository source layout. If a sentence describes target runtime layout, replace it.

- [ ] **Step 4: Handle YAML strings carefully**

For YAML files such as `.amap/profiles/execution-mode.yaml`, quote templated values:

```yaml
checkstyle_xml: "{{ platform.framework_root }}/tools/rule-projector/generated/checkstyle.generated.xml"
```

Do not leave unquoted values that start with `{`.

- [ ] **Step 5: Run render safety tests**

Run:

```bash
python3 -m pytest cli/tests/test_init.py::test_antigravity_rendered_framework_files_do_not_reference_active_amap_paths cli/tests/test_render.py cli/tests/test_scaffold.py -v
```

Expected: PASS.

- [ ] **Step 6: Run skill lint**

Run:

```bash
python3 .amap/tools/skill-lint/validate_skills.py
```

Expected: PASS. If lint rejects Jinja in frontmatter paths, update the lint schema to allow `{{ platform.framework_root }}` in path-like strings and add a focused lint test.

- [ ] **Step 7: Commit**

```bash
git add AGENTS.md .amap README.md docs/amap-file-ownership-policy.md cli/tests/test_init.py
git commit -m "refactor(framework): templatize runtime root paths"
```

## Task 7: Update Documentation and Next-Step Text

**Files:**
- Modify: `README.md`
- Modify: `docs/amap-file-ownership-policy.md`
- Modify: `cli/commands/init.py`
- Modify: `cli/tests/test_init.py`

**Interfaces:**
- Consumes: `platform.framework_root`
- Produces: user-facing docs and init output that match selected root

- [ ] **Step 1: Add init output test for root-aware next steps**

In `cli/tests/test_init.py`, add:

```python
def test_init_next_steps_use_platform_framework_root(tmp_path, amap_root, monkeypatch, capsys):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["1", "1,2,3", "3", "y"])

    run_init(target_dir=str(target), amap_root=str(amap_root))

    out = capsys.readouterr().out
    assert "Customize .agents/knowledge/long-term/persona.yaml" in out
    assert ".amap/knowledge/long-term/persona.yaml" not in out
```

- [ ] **Step 2: Run failing output test**

Run:

```bash
python3 -m pytest cli/tests/test_init.py::test_init_next_steps_use_platform_framework_root -v
```

Expected: FAIL because next steps still hardcode `.amap`.

- [ ] **Step 3: Update init next steps**

In `cli/commands/init.py`, replace:

```python
print("  1. Customize .amap/knowledge/long-term/persona.yaml")
```

with:

```python
print(f"  1. Customize {platform.framework_root}/knowledge/long-term/persona.yaml")
```

- [ ] **Step 4: Update README platform root docs**

In `README.md`, document the platform matrix:

```markdown
| Platform | Framework root | Entry point |
|----------|----------------|-------------|
| Antigravity | `.agents/` | `AGENTS.md` |
| Codex CLI | `.agents/` | `AGENTS.md` |
| Claude Code | `.claude/` | `CLAUDE.md` |
| Generic | `.amap/` | `AGENTS.md` |
```

Replace statements that say every install has one `.amap/` directory with platform-root wording:

```markdown
AMAP renders its runtime into the selected platform's framework root. Generic installs use `.amap/`; Antigravity and Codex use `.agents/`; Claude Code uses `.claude/`.
```

- [ ] **Step 5: Update ownership policy docs**

In `docs/amap-file-ownership-policy.md`, replace concrete `.amap/...` target examples with `{framework_root}/...` and include the matrix from the README.

Do not claim old `.amap` installs are auto-deleted.

- [ ] **Step 6: Run docs-related tests**

Run:

```bash
python3 -m pytest cli/tests/test_init.py::test_init_next_steps_use_platform_framework_root -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add README.md docs/amap-file-ownership-policy.md cli/commands/init.py cli/tests/test_init.py
git commit -m "docs: describe platform framework roots"
```

## Task 8: Full Regression and Manual Smoke Test

**Files:**
- No planned source modifications
- May modify tests only if a regression exposes a real missing assertion

**Interfaces:**
- Consumes: all earlier tasks
- Produces: verified release-ready behavior

- [ ] **Step 1: Run full test suite**

Run:

```bash
python3 -m pytest cli/tests -v
```

Expected: PASS.

- [ ] **Step 2: Run skill lint**

Run:

```bash
python3 .amap/tools/skill-lint/validate_skills.py
```

Expected: PASS.

- [ ] **Step 3: Smoke test Antigravity init**

Run:

```bash
tmp="$(mktemp -d)"
printf '1\n1,2,3\n3\ny\n' | python3 -m cli.amap init --target "$tmp"
test ! -e "$tmp/.amap"
test -e "$tmp/.agents/resolved-config.yaml"
test -e "$tmp/.agents/skills/requirement-analyst/SKILL.md"
test -e "$tmp/.agents/rules/RULES.md"
test -e "$tmp/AGENTS.md"
rm -rf "$tmp"
```

Expected: all commands exit 0.

- [ ] **Step 4: Smoke test Claude init**

Run:

```bash
tmp="$(mktemp -d)"
printf '2\n1,2,3\n3\ny\n' | python3 -m cli.amap init --target "$tmp"
test ! -e "$tmp/.amap"
test -e "$tmp/.claude/resolved-config.yaml"
test -e "$tmp/.claude/skills/requirement-analyst/SKILL.md"
test -e "$tmp/.claude/rules/RULES.md"
test -e "$tmp/CLAUDE.md"
rm -rf "$tmp"
```

Expected: all commands exit 0.

- [ ] **Step 5: Smoke test Generic init**

Run:

```bash
tmp="$(mktemp -d)"
printf '3\n1,2,3\n3\ny\n' | python3 -m cli.amap init --target "$tmp"
test -e "$tmp/.amap/resolved-config.yaml"
test -e "$tmp/.amap/skills/requirement-analyst/SKILL.md"
test -e "$tmp/AGENTS.md"
rm -rf "$tmp"
```

Expected: all commands exit 0.

- [ ] **Step 6: Smoke test Codex init**

Run:

```bash
tmp="$(mktemp -d)"
printf '4\n1,2,3\n3\ny\n' | python3 -m cli.amap init --target "$tmp"
test ! -e "$tmp/.amap"
test -e "$tmp/.agents/resolved-config.yaml"
test -e "$tmp/.agents/skills/requirement-analyst/SKILL.md"
test -e "$tmp/AGENTS.md"
rm -rf "$tmp"
```

Expected: all commands exit 0.

- [ ] **Step 7: Check rendered Antigravity output for active `.amap` paths**

Run:

```bash
tmp="$(mktemp -d)"
printf '1\n1,2,3\n3\ny\n' | python3 -m cli.amap init --target "$tmp"
grep -R "\.amap/" "$tmp" || true
rm -rf "$tmp"
```

Expected: no active runtime instructions reference `.amap/`. Matches are allowed only if they explicitly mention legacy migration or source repository layout.

- [ ] **Step 8: Final git status review**

Run:

```bash
git status --short
```

Expected: only intentional changes are present. Do not include unrelated pre-existing edits unless they are part of this implementation.

- [ ] **Step 9: Commit any final test/doc fix**

If Step 1-8 required a small final correction, inspect the exact changed files first:

```bash
git status --short
git diff --stat
```

Then stage only files changed for the final correction. For example, if the final correction touched only init tests:

```bash
git add cli/tests/test_init.py
git commit -m "test(cli): verify platform-native framework roots"
```

If no corrections were needed, do not create an empty commit.
