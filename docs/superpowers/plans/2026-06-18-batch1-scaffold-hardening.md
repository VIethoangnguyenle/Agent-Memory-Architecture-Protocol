# Batch 1 Scaffold Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden AMAP scaffold behavior by removing stale TODO guidance, failing early on platform tool-map drift, adding non-interactive init choices, and snapshot-testing platform output layouts.

**Architecture:** Keep the current Python CLI architecture. Add validation at the platform-adapter boundary, add explicit choice resolution in `cli.commands.init`, and put structural snapshot assertions in tests so later portability work has a stable safety net.

**Tech Stack:** Python 3.9+, argparse, pathlib, pytest, Jinja2/PyYAML already used by the CLI.

## Global Constraints

- Do not migrate platform definitions to YAML/data registry in this batch.
- Do not remove legacy `resolved-config.yaml` lookup paths.
- Do not implement `amap migrate`, `--dry-run`, drift detection, or eval harnesses.
- Do not change generated framework prose unless a test exposes an existing scaffold correctness issue.
- Platform selection has no interactive default; empty platform input is invalid.
- Interactive language selection defaults to `other`.
- Golden snapshots store normalized relative file trees only, not file contents, absolute paths, temp paths, or timestamps.

---

## File Structure

- `TODOS.md`: mark the init footer item as done/stale, merge init automation/default work, and promote golden snapshots into the immediate sequence.
- `cli/platforms/base.py`: define the required abstract tool-key contract, validation error, and platform validation methods.
- `cli/platforms/codex.py`: add explicit `get_space_pages` passthrough.
- `cli/platforms/generic.py`: add explicit `get_space_pages` passthrough.
- `cli/commands/init.py`: add explicit choice resolution, safe interactive prompts, option validation, and `run_init()` parameters for non-interactive usage.
- `cli/amap.py`: add argparse flags for `amap init`.
- `cli/tests/test_platforms.py`: cover required keyset and validation failures.
- `cli/tests/test_init.py`: cover non-interactive init, safe prompt behavior, invalid options, and CLI argument forwarding.
- `cli/tests/test_scaffold.py`: keep existing scaffold guard tests unchanged.
- `cli/tests/test_snapshots.py`: new structural snapshot tests for platform scaffold output.
- `cli/tests/snapshots/{antigravity,codex,claude-code,generic}.txt`: normalized expected file trees.

---

### Task 1: Audit `TODOS.md`

**Files:**
- Modify: `TODOS.md`

**Interfaces:**
- Consumes: current `TODOS.md` roadmap text and the approved Batch 1 spec.
- Produces: a clearer roadmap where completed/stale work is not still presented as pending.

- [ ] **Step 1: Edit `TODOS.md` to mark stale and merged items**

Apply these content changes:

```markdown
### P1.3 + P2.2 — Init automation and safe defaults
- **What:** Add flags for `amap init`: `--platform`, `--mcp`, `--language`, `--yes`. Keep interactive as the default, but prevent enter-through from silently installing Antigravity + Java. Platform has no interactive default; language defaults to `other`.
- **Why:** Init must be scriptable for CI/onboarding, and defaults must not silently choose the wrong runtime or language.
- **Context:** [cli/commands/init.py](cli/commands/init.py), [cli/amap.py](cli/amap.py). Supersedes the old separate `P1.3` and `P2.2` entries.
- **Effort:** CC ~30-45 minutes.
- **Priority:** P1.
```

Move the existing `P3.2 — Next-steps footer sau amap init` entry to a short completed/stale section:

```markdown
## Done / Stale

### P3.2 — Next-steps footer sau `amap init`
- **Status:** Done before Batch 1. `run_init()` already prints platform-root-aware next steps, and `cli/tests/test_init.py` covers the output.
```

Promote `UP3` by editing its priority line to:

```markdown
- **Priority:** P1 hardening guard. Do before large portability refactors.
```

- [ ] **Step 2: Review the roadmap text for duplicate headings**

Run:

```bash
rg -n "P1.3|P2.2|P3.2|UP3|Done / Stale" TODOS.md
```

Expected: the old standalone `P1.3` and `P2.2` no longer appear as separate pending headings; `P3.2` appears only under `Done / Stale`; `UP3` has P1 hardening wording.

- [ ] **Step 3: Commit the docs audit**

```bash
git add TODOS.md
git commit -m "docs(todo): align batch1 hardening roadmap"
```

---

### Task 2: Add Platform Tool-Mapping Validation

**Files:**
- Modify: `cli/platforms/base.py`
- Modify: `cli/platforms/antigravity.py`
- Modify: `cli/platforms/claude_code.py`
- Modify: `cli/platforms/codex.py`
- Modify: `cli/platforms/generic.py`
- Test: `cli/tests/test_platforms.py`

**Interfaces:**
- Produces: `REQUIRED_TOOL_KEYS: frozenset[str]`
- Produces: `PlatformToolMappingError(ValueError)`
- Produces: `BasePlatform.unsupported_tools -> set[str]`
- Produces: `BasePlatform.validate_tool_mapping() -> None`
- Produces: `BasePlatform.get_tool(abstract_name: str) -> str`
- Consumes: existing `PLATFORMS`, `get_platform()`, and `build_render_context()`

- [ ] **Step 1: Write failing platform keyset tests**

Add to `cli/tests/test_platforms.py`:

```python
import pytest

from cli.platforms.base import (
    REQUIRED_TOOL_KEYS,
    BasePlatform,
    PlatformToolMappingError,
)


def test_all_platforms_define_required_tool_keyset():
    for key, cls in PLATFORMS.items():
        platform = cls()
        missing = REQUIRED_TOOL_KEYS - set(platform.tool_mapping) - platform.unsupported_tools
        extra_unsupported = platform.unsupported_tools - REQUIRED_TOOL_KEYS
        assert missing == set(), f"{key} missing tool mappings: {sorted(missing)}"
        assert extra_unsupported == set(), (
            f"{key} declares unknown unsupported tools: {sorted(extra_unsupported)}"
        )


def test_build_render_context_fails_on_missing_required_tool_mapping():
    class BrokenPlatform(BasePlatform):
        name = "broken"
        display_name = "Broken"
        config_entry_point = "AGENTS.md"
        tool_mapping = {"read_file": "Read"}

    with pytest.raises(PlatformToolMappingError) as exc:
        BrokenPlatform().build_render_context([], "python")

    message = str(exc.value)
    assert "broken" in message
    assert "missing required tool mappings" in message
    assert "write_file" in message


def test_get_tool_fails_for_unknown_required_operation():
    platform = get_platform("generic")

    with pytest.raises(PlatformToolMappingError) as exc:
        platform.get_tool("not_a_real_tool")

    assert "not_a_real_tool" in str(exc.value)
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```bash
python -m pytest cli/tests/test_platforms.py::test_all_platforms_define_required_tool_keyset cli/tests/test_platforms.py::test_build_render_context_fails_on_missing_required_tool_mapping cli/tests/test_platforms.py::test_get_tool_fails_for_unknown_required_operation -q
```

Expected: FAIL because `REQUIRED_TOOL_KEYS`, `PlatformToolMappingError`, and `unsupported_tools` do not exist yet.

- [ ] **Step 3: Implement the platform mapping contract**

Modify `cli/platforms/base.py`:

```python
"""Base platform definition — abstract interface for all agent platforms."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set


REQUIRED_TOOL_KEYS = frozenset({
    "read_file",
    "write_file",
    "edit_file",
    "multi_edit_file",
    "search_text",
    "list_directory",
    "run_command",
    "command_status",
    "send_input",
    "search_code",
    "index_code",
    "code_status",
    "get_dependencies",
    "trace_flow",
    "find_blast_radius",
    "get_symbol",
    "list_symbols",
    "graph_stats",
    "graph_build",
    "search_docs",
    "get_page",
    "list_spaces",
    "get_space_pages",
    "search_web",
    "read_url",
})


class PlatformToolMappingError(ValueError):
    """Raised when a platform adapter cannot resolve required AMAP tool keys."""
```

Add these members to `BasePlatform`:

```python
    @property
    def unsupported_tools(self) -> Set[str]:
        """Required abstract operations intentionally unsupported by this platform."""
        return set()

    def validate_tool_mapping(self) -> None:
        """Fail early when a platform adapter drifts from AMAP's tool contract."""
        missing = REQUIRED_TOOL_KEYS - set(self.tool_mapping) - self.unsupported_tools
        extra_unsupported = self.unsupported_tools - REQUIRED_TOOL_KEYS
        if missing:
            raise PlatformToolMappingError(
                f"{self.name} missing required tool mappings: {', '.join(sorted(missing))}"
            )
        if extra_unsupported:
            raise PlatformToolMappingError(
                f"{self.name} declares unknown unsupported tools: "
                f"{', '.join(sorted(extra_unsupported))}"
            )
```

Replace `get_tool()` with:

```python
    def get_tool(self, abstract_name: str) -> str:
        """Resolve abstract operation to concrete tool name."""
        if abstract_name in self.tool_mapping:
            return self.tool_mapping[abstract_name]
        raise PlatformToolMappingError(
            f"{self.name} has no mapping for abstract tool operation: {abstract_name}"
        )
```

At the start of `build_render_context()` add:

```python
        self.validate_tool_mapping()
```

- [ ] **Step 4: Add explicit missing keys to Codex and Generic**

Add this entry to both `cli/platforms/codex.py` and `cli/platforms/generic.py` inside `tool_mapping`, next to the other document-search keys:

```python
        "get_space_pages":   "get_space_pages",
```

Do not remove self-mapping entries from Codex or Generic; explicit passthrough is intentional.

- [ ] **Step 5: Run platform tests**

Run:

```bash
python -m pytest cli/tests/test_platforms.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit platform validation**

```bash
git add cli/platforms cli/tests/test_platforms.py
git commit -m "test(platforms): fail on missing tool mappings"
```

---

### Task 3: Add Non-Interactive Init and Safe Prompt Defaults

**Files:**
- Modify: `cli/commands/init.py`
- Modify: `cli/amap.py`
- Test: `cli/tests/test_init.py`

**Interfaces:**
- Produces: `prompt_single_checkbox(message: str, choices: List[str], default: Optional[int] = 0) -> str`
- Produces: `parse_multi_values(values: Optional[List[str]]) -> List[str]`
- Produces: `resolve_init_choices(manifest: dict, platform_key: Optional[str], selected_mcps: Optional[List[str]], language: Optional[str], assume_yes: bool) -> Tuple[str, List[str], str]`
- Updates: `run_init(target_dir: str, amap_root: Optional[str] = None, platform_key: Optional[str] = None, selected_mcps: Optional[List[str]] = None, language: Optional[str] = None, assume_yes: bool = False) -> None`
- Consumes: `PLATFORMS`, manifest `mcp_capabilities`, manifest `languages`

- [ ] **Step 1: Write failing tests for safe prompts and explicit choices**

Add to `cli/tests/test_init.py`:

```python
import pytest

from cli.commands.init import (
    parse_multi_values,
    resolve_init_choices,
)


def test_prompt_single_checkbox_requires_choice_when_default_is_none(monkeypatch):
    answers = iter(["", "2"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))

    assert prompt_single_checkbox("Choose", ["A", "B"], default=None) == "B"


def test_parse_multi_values_accepts_repeated_and_comma_values():
    assert parse_multi_values(["socraticode,confluence", "db-remote"]) == [
        "socraticode",
        "confluence",
        "db-remote",
    ]


def test_resolve_init_choices_accepts_complete_non_interactive_options(amap_root):
    manifest = load_manifest(amap_root)

    platform_key, selected_mcps, language = resolve_init_choices(
        manifest,
        platform_key="generic",
        selected_mcps=["socraticode", "confluence"],
        language="python",
        assume_yes=True,
    )

    assert platform_key == "generic"
    assert selected_mcps == ["socraticode", "confluence"]
    assert language == "python"


def test_resolve_init_choices_rejects_yes_with_missing_required_options(amap_root):
    manifest = load_manifest(amap_root)

    with pytest.raises(ValueError) as exc:
        resolve_init_choices(
            manifest,
            platform_key="generic",
            selected_mcps=[],
            language=None,
            assume_yes=True,
        )

    assert "--yes requires --platform and --language" in str(exc.value)


def test_resolve_init_choices_rejects_invalid_platform(amap_root):
    manifest = load_manifest(amap_root)

    with pytest.raises(ValueError) as exc:
        resolve_init_choices(
            manifest,
            platform_key="unknown",
            selected_mcps=[],
            language="python",
            assume_yes=True,
        )

    assert "Unknown platform" in str(exc.value)


def test_run_init_non_interactive_generic(tmp_path, amap_root):
    target = tmp_path / "proj"

    run_init(
        target_dir=str(target),
        amap_root=str(amap_root),
        platform_key="generic",
        selected_mcps=[],
        language="other",
        assume_yes=True,
    )

    assert (target / ".amap" / "resolved-config.yaml").exists()
    assert (target / "AGENTS.md").exists()
```

Add this import near the top of `cli/tests/test_init.py`:

```python
from cli.scaffold import load_manifest
```

- [ ] **Step 2: Run new tests and verify they fail**

Run:

```bash
python -m pytest cli/tests/test_init.py::test_prompt_single_checkbox_requires_choice_when_default_is_none cli/tests/test_init.py::test_parse_multi_values_accepts_repeated_and_comma_values cli/tests/test_init.py::test_resolve_init_choices_accepts_complete_non_interactive_options cli/tests/test_init.py::test_resolve_init_choices_rejects_yes_with_missing_required_options cli/tests/test_init.py::test_resolve_init_choices_rejects_invalid_platform cli/tests/test_init.py::test_run_init_non_interactive_generic -q
```

Expected: FAIL because the new helpers and `run_init()` parameters do not exist.

- [ ] **Step 3: Implement safe prompt and choice resolution**

Modify imports in `cli/commands/init.py`:

```python
from typing import List, Optional, Tuple
```

Replace `prompt_single_checkbox()` with:

```python
def prompt_single_checkbox(
    message: str, choices: List[str], default: Optional[int] = 0
) -> str:
    """Interactive single-select prompt displayed as checkbox-style choices."""
    print(f"\n{message}")
    for i, choice in enumerate(choices):
        marker = "x" if default is not None and i == default else " "
        print(f"  [{marker}] [{i + 1}] {choice}")

    prompt_suffix = f" [{default + 1}]" if default is not None else ""
    while True:
        raw = input(f"\nChọn một mục (1-{len(choices)}){prompt_suffix}: ").strip()
        if not raw and default is not None:
            return choices[default]
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass
        print(f"  ⚠️  Chọn số từ 1 đến {len(choices)}")
```

Add:

```python
def parse_multi_values(values: Optional[List[str]]) -> List[str]:
    """Normalize repeated or comma-separated CLI option values."""
    if not values:
        return []
    parsed = []
    for value in values:
        for part in value.split(","):
            item = part.strip()
            if item:
                parsed.append(item)
    return parsed


def _validate_selected_mcps(selected_mcps: List[str], mcp_capabilities: dict) -> None:
    unknown = [mcp for mcp in selected_mcps if mcp not in mcp_capabilities]
    if unknown:
        raise ValueError(f"Unknown MCP server(s): {', '.join(unknown)}")


def _validate_language(language: str, languages: List[str]) -> None:
    if language not in languages:
        raise ValueError(
            f"Unknown language: {language}. Available: {', '.join(languages)}"
        )


def resolve_init_choices(
    manifest: dict,
    platform_key: Optional[str] = None,
    selected_mcps: Optional[List[str]] = None,
    language: Optional[str] = None,
    assume_yes: bool = False,
) -> Tuple[str, List[str], str]:
    """Resolve init choices from explicit options or interactive prompts."""
    mcp_capabilities = manifest.get("mcp_capabilities", {})
    languages = manifest.get("languages", ["java", "typescript", "python", "other"])
    selected_mcps = selected_mcps or []

    if assume_yes and (platform_key is None or language is None):
        raise ValueError("--yes requires --platform and --language")

    if platform_key is not None and platform_key not in PLATFORMS:
        raise ValueError(
            f"Unknown platform: {platform_key}. Available: {', '.join(PLATFORMS)}"
        )
    _validate_selected_mcps(selected_mcps, mcp_capabilities)
    if language is not None:
        _validate_language(language, languages)

    if platform_key is None:
        platform_keys = list(PLATFORMS.keys())
        platform_choices = [get_platform(k).display_name for k in platform_keys]
        chosen_display = prompt_single_checkbox(
            "Chọn agent platform:", platform_choices, default=None
        )
        platform_key = platform_keys[platform_choices.index(chosen_display)]
    print(f"\n  ✅ Platform: {get_platform(platform_key).display_name}")

    if not selected_mcps and not assume_yes:
        mcp_choices = [
            {"key": k, "display": v["display"]}
            for k, v in mcp_capabilities.items()
        ]
        selected_mcps = prompt_multi_checkbox("MCP servers có sẵn:", mcp_choices)
    print(f"  ✅ MCPs: {', '.join(selected_mcps) or 'none'}")

    if language is None:
        default_language = languages.index("other") if "other" in languages else None
        language = prompt_single_checkbox(
            "Ngôn ngữ chính của project:", languages, default=default_language
        )
    print(f"  ✅ Language: {language}")
    return platform_key, selected_mcps, language
```

Replace `gather_choices()` body with:

```python
def gather_choices(manifest: dict) -> Tuple[str, List[str], str]:
    """Interactively gather (platform_key, selected_mcps, language)."""
    return resolve_init_choices(manifest)
```

- [ ] **Step 4: Update `run_init()` to accept explicit choices and skip confirm with `--yes`**

Change the signature:

```python
def run_init(
    target_dir: str,
    amap_root: Optional[str] = None,
    platform_key: Optional[str] = None,
    selected_mcps: Optional[List[str]] = None,
    language: Optional[str] = None,
    assume_yes: bool = False,
) -> None:
```

Replace choice gathering:

```python
    manifest = load_manifest(amap)
    platform_key, selected_mcps, language = resolve_init_choices(
        manifest,
        platform_key=platform_key,
        selected_mcps=selected_mcps,
        language=language,
        assume_yes=assume_yes,
    )
    platform = get_platform(platform_key)
```

Replace confirm:

```python
    if not assume_yes and input("\nTiến hành scaffold? [Y/n]: ").strip().lower() == "n":
        print("\n❌ Đã huỷ.")
        return
```

- [ ] **Step 5: Add CLI flags and forward them to `run_init()`**

Modify `cli/amap.py` init parser:

```python
    init_parser.add_argument(
        "--platform",
        default=None,
        help="Agent platform key, e.g. antigravity, claude-code, codex, generic",
    )
    init_parser.add_argument(
        "--mcp",
        action="append",
        default=None,
        help="MCP server key. Repeat or pass comma-separated values.",
    )
    init_parser.add_argument(
        "--language",
        default=None,
        help="Primary project language from cli/plugin-manifest.yaml",
    )
    init_parser.add_argument(
        "--yes",
        action="store_true",
        help="Run non-interactively; requires --platform and --language",
    )
```

Modify the init command branch:

```python
    if args.command == "init":
        from cli.commands.init import parse_multi_values, run_init
        run_init(
            target_dir=args.target,
            amap_root=args.source,
            platform_key=args.platform,
            selected_mcps=parse_multi_values(args.mcp),
            language=args.language,
            assume_yes=args.yes,
        )
```

- [ ] **Step 6: Add CLI parser forwarding test**

Add to `cli/tests/test_init.py`:

```python
def test_cli_init_forwards_non_interactive_options(monkeypatch, tmp_path):
    from cli import amap

    captured = {}

    def fake_run_init(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("cli.commands.init.run_init", fake_run_init)
    monkeypatch.setattr(
        "sys.argv",
        [
            "amap",
            "init",
            "--target",
            str(tmp_path),
            "--platform",
            "generic",
            "--mcp",
            "socraticode,confluence",
            "--language",
            "python",
            "--yes",
        ],
    )

    amap.main()

    assert captured["target_dir"] == str(tmp_path)
    assert captured["platform_key"] == "generic"
    assert captured["selected_mcps"] == ["socraticode", "confluence"]
    assert captured["language"] == "python"
    assert captured["assume_yes"] is True
```

- [ ] **Step 7: Run init tests**

Run:

```bash
python -m pytest cli/tests/test_init.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit init automation**

```bash
git add cli/commands/init.py cli/amap.py cli/tests/test_init.py
git commit -m "feat(init): support non-interactive choices"
```

---

### Task 4: Add Structural Golden Snapshot Tests

**Files:**
- Create: `cli/tests/test_snapshots.py`
- Create: `cli/tests/snapshots/antigravity.txt`
- Create: `cli/tests/snapshots/codex.txt`
- Create: `cli/tests/snapshots/claude-code.txt`
- Create: `cli/tests/snapshots/generic.txt`

**Interfaces:**
- Consumes: `run_init(..., assume_yes=True)` from Task 3.
- Produces: normalized tree snapshot tests that fail when platform output layout changes.

- [ ] **Step 1: Add snapshot test module**

Create `cli/tests/test_snapshots.py`:

```python
"""Structural golden snapshots for platform scaffold output."""

from pathlib import Path

import pytest

from cli.commands.init import run_init


PLATFORM_OPTIONS = {
    "antigravity": {
        "mcps": ["socraticode", "confluence", "db-remote"],
        "language": "python",
    },
    "codex": {
        "mcps": ["socraticode", "confluence", "db-remote"],
        "language": "python",
    },
    "claude-code": {
        "mcps": ["socraticode", "confluence", "db-remote"],
        "language": "python",
    },
    "generic": {
        "mcps": [],
        "language": "other",
    },
}


def _snapshot_tree(root: Path) -> str:
    entries = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if "__pycache__" in rel:
            continue
        suffix = "/" if path.is_dir() else ""
        entries.append(f"{rel}{suffix}")
    return "\n".join(entries) + "\n"


@pytest.mark.parametrize("platform_key", sorted(PLATFORM_OPTIONS))
def test_platform_scaffold_tree_matches_snapshot(tmp_path, amap_root, platform_key):
    target = tmp_path / "proj"
    options = PLATFORM_OPTIONS[platform_key]

    run_init(
        target_dir=str(target),
        amap_root=str(amap_root),
        platform_key=platform_key,
        selected_mcps=options["mcps"],
        language=options["language"],
        assume_yes=True,
    )

    actual = _snapshot_tree(target)
    snapshot_path = (
        Path(__file__).resolve().parent
        / "snapshots"
        / f"{platform_key}.txt"
    )
    expected = snapshot_path.read_text(encoding="utf-8")
    assert actual == expected
```

- [ ] **Step 2: Run snapshot tests and verify they fail because fixtures are missing**

Run:

```bash
python -m pytest cli/tests/test_snapshots.py -q
```

Expected: FAIL with `FileNotFoundError` for missing snapshot files.

- [ ] **Step 3: Generate initial snapshot fixture contents**

Run this helper locally to print the four normalized trees:

```bash
python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from cli.commands.init import run_init

repo = Path(".").resolve()
platforms = {
    "antigravity": (["socraticode", "confluence", "db-remote"], "python"),
    "codex": (["socraticode", "confluence", "db-remote"], "python"),
    "claude-code": (["socraticode", "confluence", "db-remote"], "python"),
    "generic": ([], "other"),
}

def tree(root):
    entries = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if "__pycache__" in rel:
            continue
        entries.append(f"{rel}{'/' if path.is_dir() else ''}")
    return "\n".join(entries) + "\n"

out = repo / "cli" / "tests" / "snapshots"
out.mkdir(parents=True, exist_ok=True)
for platform, (mcps, language) in platforms.items():
    with TemporaryDirectory() as tmp:
        target = Path(tmp) / "proj"
        run_init(
            target_dir=str(target),
            amap_root=str(repo),
            platform_key=platform,
            selected_mcps=mcps,
            language=language,
            assume_yes=True,
        )
        (out / f"{platform}.txt").write_text(tree(target), encoding="utf-8")
        print(f"wrote {out / f'{platform}.txt'}")
PY
```

- [ ] **Step 4: Add invariant assertions to snapshot test**

Append to `test_platform_scaffold_tree_matches_snapshot()` after the equality assertion:

```python
    if platform_key in {"antigravity", "codex"}:
        assert "AGENTS.md" in actual
        assert ".agents/resolved-config.yaml" in actual
        assert ".amap/resolved-config.yaml" not in actual
    elif platform_key == "claude-code":
        assert "CLAUDE.md" in actual
        assert ".claude/resolved-config.yaml" in actual
        assert ".amap/resolved-config.yaml" not in actual
    elif platform_key == "generic":
        assert "AGENTS.md" in actual
        assert ".amap/resolved-config.yaml" in actual
        assert ".agents/resolved-config.yaml" not in actual
        assert ".claude/resolved-config.yaml" not in actual
```

- [ ] **Step 5: Run snapshot tests**

Run:

```bash
python -m pytest cli/tests/test_snapshots.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit snapshots**

```bash
git add cli/tests/test_snapshots.py cli/tests/snapshots
git commit -m "test(init): snapshot platform scaffold trees"
```

---

### Task 5: Full Verification and Regression Sweep

**Files:**
- Verify: files touched in Tasks 1-4.

**Interfaces:**
- Consumes: all previous task outputs.
- Produces: passing full CLI test suite and smoke-tested non-interactive init.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest cli/tests/test_platforms.py cli/tests/test_init.py cli/tests/test_scaffold.py cli/tests/test_snapshots.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full CLI tests**

Run:

```bash
python -m pytest cli/tests -q
```

Expected: PASS.

- [ ] **Step 3: Run non-interactive smoke checks**

Run:

```bash
rm -rf /tmp/amap-smoke /tmp/amap-smoke-codex
python -m cli.amap init --target /tmp/amap-smoke --platform generic --language other --yes
python -m cli.amap init --target /tmp/amap-smoke-codex --platform codex --mcp socraticode --language python --yes
test -f /tmp/amap-smoke/.amap/resolved-config.yaml
test -f /tmp/amap-smoke-codex/.agents/resolved-config.yaml
```

Expected: both init commands finish without prompting; both `test -f` commands exit 0.

- [ ] **Step 4: Check no unintended uncommitted changes remain**

Run:

```bash
git status --short
```

Expected: clean, or only intentional files that need a final commit.

- [ ] **Step 5: Finish with a clean worktree**

Run:

```bash
git status --short
```

Expected: no output. If this prints files, return to the task that owns those files, finish its test cycle, and commit with that task's commit message.
