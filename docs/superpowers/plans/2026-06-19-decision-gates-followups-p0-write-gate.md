# Decision Gates Follow-ups P0 Write Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the P0 recommendation from `2026-06-19-decision-gates-followups-design.md`: a deterministic runtime write gate, shipped only for platforms whose scaffold capability declares support, plus the remaining index-aware checker hardening.

**Architecture:** Add a platform capability named `write_gate_hook`, a manifest filter named `requires_platform_capability`, and a platform-key filter named `requires_platform`. The generic hook logic lives in AMAP source under `.amap/hooks/write-gate/`; platform-specific config adapters wire it into Claude Code, Codex, and Antigravity only when the platform declares the capability. Platforms without `write_gate_hook` do not receive hook config and must degrade explicitly to prose/procedure-level enforcement.

**Tech Stack:** Python 3.9+ stdlib, PyYAML, pytest, Jinja2 scaffold renderer, Claude Code settings JSON, Codex `.codex/hooks.json`, Antigravity `.agents/hooks.json`.

**Spec:** `docs/superpowers/specs/2026-06-19-decision-gates-followups-design.md`

**Primary references checked:**
- Claude Code hooks reference (`https://code.claude.com/docs/en/hooks`) and hooks guide (`https://code.claude.com/docs/en/hooks-guide`). Relevant facts: `PreToolUse` fires before tool calls and can block them; hooks can be registered in settings JSON; `Edit|Write` matchers are supported for file edit tools.
- Codex hooks reference (`https://developers.openai.com/codex/hooks`) and advanced config (`https://developers.openai.com/codex/config-advanced`). Relevant facts: hooks are enabled by default; repo hooks can live in `<repo>/.codex/hooks.json`; `PreToolUse` can match `apply_patch`/`Edit`/`Write`; `apply_patch` hook input reports the patch command.
- Antigravity hooks documentation (`https://antigravity.google/docs/hooks`) and Google Antigravity SDK hook architecture (`https://github.com/google-antigravity/antigravity-sdk-python/blob/main/google/antigravity/hooks/README.md`). Relevant facts: hooks are configured via `hooks.json`; blocking decision hooks can approve or deny built-in tool calls; Antigravity built-in edit tools include `write_to_file`, `replace_file_content`, and `multi_replace_file_content`.

---

## Scope Boundary

This plan follows only `Decision-Point Gates — Follow-ups (post sub-spec #1)`.

In scope:
- P0 runtime write-gate trigger via scaffold capability.
- Residual C-22: block raw `Write/Edit` outside `/task apply` when no valid checkpoint exists.
- Remaining P1 hardening: index-aware rule-id validation and index-aware governance-degrade.

Out of scope:
- Sub-spec #2 mechanical style enforcement.
- Sub-spec #3 build/bookkeeping completion gate.
- Sub-spec #4 knowledge capture correctness.
- Sub-spec #5 full workflow/skill consolidation.

## File Structure

Create:
- `.amap/hooks/write-gate/write_gate.py` — generic hook runner. Reads hook JSON from stdin, extracts target paths for Claude/Codex/Antigravity payloads, decides allow/block, and validates `knowledge/active/KNOWLEDGE_CHECKPOINT.md`.
- `.amap/hooks/write-gate/README.md` — short runtime contract for platforms that wire this hook.
- `.amap/hooks/write-gate/tests/test_write_gate.py` — direct unit tests for hook decisions.
- `.amap/hooks/claude-code/settings.json` — Claude Code hook config, rendered by scaffold into `.claude/settings.json` only when platform is `claude-code`.
- `.amap/hooks/codex/hooks.json` — Codex hook config, rendered by scaffold into `.codex/hooks.json` only when platform is `codex`.
- `.amap/hooks/antigravity/hooks.json` — Antigravity hook config, rendered by scaffold into `.agents/hooks.json` only when platform is `antigravity`.

Modify:
- `cli/platforms/base.py` — add `write_gate_hook: False` to default platform capabilities.
- `cli/platforms/claude_code.py` — set `write_gate_hook: True`, because Claude Code supports `PreToolUse` hooks for `Edit|Write`.
- `cli/platforms/codex.py` — set `write_gate_hook: True`, because Codex supports `PreToolUse` hooks for `apply_patch`/`Edit`/`Write`.
- `cli/platforms/antigravity.py` — set `write_gate_hook: True`, because Antigravity supports blocking pre-tool decision hooks over built-in edit tools.
- `cli/scaffold.py` — support `requires_platform_capability` and `requires_platform` in plugin filtering; map manifest `hooks/` sources to `.amap/hooks/`.
- `cli/plugin-manifest.yaml` — add `write-gate-core` plus platform-specific hook config plugins gated by platform capability and platform key.
- `cli/tests/test_scaffold.py` — test capability filtering.
- `cli/tests/snapshots/{antigravity,codex,claude-code}.txt` — capable platform snapshots should include hook core and their own hook config; `generic.txt` should not.
- `.amap/tools/gate-check/gates.py` — make `validate_knowledge_checkpoint` optionally accept valid rule IDs and `allow_no_knowledge`.
- `.amap/tools/gate-check/cli.py` — add optional `--index` and `--artifact-type` for index-aware validation.
- `.amap/tools/gate-check/tests/test_gates.py` — rule ID and governance-degrade tests.
- `.amap/tools/knowledge-index/generate_index.py` — add small helper for loading index entries, if keeping this logic out of `gates.py` is cleaner.
- `docs/superpowers/specs/2026-06-19-decision-gates-followups-design.md` — mark P0 recommendation selected and update status after implementation.

---

### Task 1: Platform filters for scaffold plugins

**Files:**
- Modify: `cli/platforms/base.py`
- Modify: `cli/scaffold.py`
- Test: `cli/tests/test_scaffold.py`

- [ ] **Step 1: Write the failing scaffold capability test**

Append to `cli/tests/test_scaffold.py`:

```python
def test_scaffold_plugins_skips_platform_capability_plugin_when_absent(tmp_path, amap_root, jinja_env, claude_context):
    from cli.scaffold import scaffold_plugins

    source = amap_root / ".amap" / "knowledge" / "templates" / "TOKEN_LOG.tpl.md"
    assert source.exists()

    plugins = [{
        "name": "write-gate-settings",
        "type": "hook",
        "source": "knowledge-templates/TOKEN_LOG.tpl.md",
        "output": "{{ platform.framework_root }}/hooks/write-gate/TOKEN_LOG.tpl.md",
        "requires_platform_capability": "write_gate_hook",
    }]

    context = {**claude_context, "capabilities": {**claude_context["capabilities"], "write_gate_hook": False}}
    stats = scaffold_plugins(
        plugins, amap_root, tmp_path, context, jinja_env,
        mcp_capabilities={}, selected_mcps=[], verbose=False,
    )

    assert stats["skipped"] == 1
    assert not (tmp_path / ".claude" / "hooks" / "write-gate" / "TOKEN_LOG.tpl.md").exists()
```

Append the positive case:

```python
def test_scaffold_plugins_includes_platform_capability_plugin_when_present(tmp_path, amap_root, jinja_env, claude_context):
    from cli.scaffold import scaffold_plugins

    plugins = [{
        "name": "write-gate-settings",
        "type": "hook",
        "source": "knowledge-templates/TOKEN_LOG.tpl.md",
        "output": "{{ platform.framework_root }}/hooks/write-gate/TOKEN_LOG.tpl.md",
        "requires_platform_capability": "write_gate_hook",
    }]

    context = {**claude_context, "capabilities": {**claude_context["capabilities"], "write_gate_hook": True}}
    stats = scaffold_plugins(
        plugins, amap_root, tmp_path, context, jinja_env,
        mcp_capabilities={}, selected_mcps=[], verbose=False,
    )

    assert stats["copied"] == 1
    assert (tmp_path / ".claude" / "hooks" / "write-gate" / "TOKEN_LOG.tpl.md").exists()
```

Append the platform-key negative case:

```python
def test_scaffold_plugins_skips_platform_specific_plugin_for_other_platform(tmp_path, amap_root, jinja_env, claude_context):
    from cli.scaffold import scaffold_plugins

    plugins = [{
        "name": "codex-write-gate-settings",
        "type": "hook",
        "source": "knowledge-templates/TOKEN_LOG.tpl.md",
        "output": ".codex/hooks.json",
        "requires_platform": "codex",
    }]

    stats = scaffold_plugins(
        plugins, amap_root, tmp_path, claude_context, jinja_env,
        mcp_capabilities={}, selected_mcps=[], verbose=False,
    )

    assert stats["skipped"] == 1
    assert not (tmp_path / ".codex" / "hooks.json").exists()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
/usr/bin/python3 -m pytest cli/tests/test_scaffold.py::test_scaffold_plugins_skips_platform_capability_plugin_when_absent cli/tests/test_scaffold.py::test_scaffold_plugins_includes_platform_capability_plugin_when_present cli/tests/test_scaffold.py::test_scaffold_plugins_skips_platform_specific_plugin_for_other_platform -v
```

Expected: first and third tests fail because `requires_platform_capability` and `requires_platform` are ignored.

- [ ] **Step 3: Add default platform capability**

In `cli/platforms/base.py`, extend `BasePlatform.capabilities`:

```python
    @property
    def capabilities(self) -> Dict[str, bool]:
        """Platform-specific capabilities."""
        return {
            "subagent": False,
            "persistent_terminal": False,
            "artifacts": False,
            "image_generation": False,
            "browser": False,
            "write_gate_hook": False,
        }
```

- [ ] **Step 4: Add scaffold filters**

In `cli/scaffold.py`, inside `scaffold_plugins()` after the MCP `requires_capability` check:

```python
        platform_requires_name = plugin.get("requires_platform")
        platform_name = context.get("platform", {}).get("name")
        if platform_requires_name:
            allowed = (
                platform_requires_name
                if isinstance(platform_requires_name, list)
                else [platform_requires_name]
            )
            if platform_name not in allowed:
                if verbose:
                    print(f"  ⏭️  {name:35s} (platform: {platform_name}, needs: {', '.join(allowed)})")
                stats["skipped"] += 1
                continue

        platform_requires = plugin.get("requires_platform_capability")
        if platform_requires and not context.get("capabilities", {}).get(platform_requires, False):
            if verbose:
                print(f"  ⏭️  {name:35s} (no platform capability: {platform_requires})")
            stats["skipped"] += 1
            continue
```

- [ ] **Step 5: Run tests to verify pass**

Run:

```bash
/usr/bin/python3 -m pytest cli/tests/test_scaffold.py::test_scaffold_plugins_skips_platform_capability_plugin_when_absent cli/tests/test_scaffold.py::test_scaffold_plugins_includes_platform_capability_plugin_when_present cli/tests/test_scaffold.py::test_scaffold_plugins_skips_platform_specific_plugin_for_other_platform -v
```

Expected: all three tests PASS.

- [ ] **Step 6: Commit**

```bash
git add cli/platforms/base.py cli/scaffold.py cli/tests/test_scaffold.py
git commit -m "feat(scaffold): gate plugins by platform and capability"
```

---

### Task 2: Generic write-gate hook runner

**Files:**
- Create: `.amap/hooks/write-gate/write_gate.py`
- Create: `.amap/hooks/write-gate/README.md`
- Create: `.amap/hooks/write-gate/tests/test_write_gate.py`

- [ ] **Step 1: Write failing tests**

Create `.amap/hooks/write-gate/tests/test_write_gate.py`:

```python
import importlib.util
import json
from pathlib import Path

MOD = Path(__file__).resolve().parents[1] / "write_gate.py"
spec = importlib.util.spec_from_file_location("write_gate", MOD)
wg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wg)


def test_extracts_file_path_from_claude_write_payload():
    payload = {"tool_name": "Write", "tool_input": {"file_path": "src/App.java"}}
    assert wg.extract_target_paths(payload) == [Path("src/App.java")]


def test_extracts_paths_from_codex_apply_patch_payload():
    payload = {
        "tool_name": "apply_patch",
        "tool_input": {
            "command": "*** Begin Patch\n"
            "*** Update File: src/App.java\n"
            "@@\n"
            "-old\n"
            "+new\n"
            "*** Add File: docs/superpowers/specs/x.md\n"
            "+# Spec\n"
            "*** End Patch\n"
        },
    }
    assert wg.extract_target_paths(payload) == [
        Path("src/App.java"),
        Path("docs/superpowers/specs/x.md"),
    ]


def test_extracts_path_from_antigravity_toolcall_payload():
    payload = {
        "toolCall": {
            "name": "replace_file_content",
            "args": {"file_path": "src/App.java"},
        }
    }
    assert wg.extract_target_paths(payload) == [Path("src/App.java")]


def test_allows_framework_and_openspec_artifact_writes(tmp_path):
    root = tmp_path
    assert wg.evaluate_write(root, Path(".claude/knowledge/active/KNOWLEDGE_CHECKPOINT.md")).ok is True
    assert wg.evaluate_write(root, Path("openspec/changes/x/specs/foo/spec.md")).ok is True


def test_blocks_app_write_without_checkpoint(tmp_path):
    result = wg.evaluate_write(tmp_path, Path("src/App.java"))
    assert result.ok is False
    assert "KNOWLEDGE_CHECKPOINT" in result.reason


def test_allows_app_write_with_valid_checkpoint(tmp_path):
    checkpoint = tmp_path / ".claude" / "knowledge" / "active" / "KNOWLEDGE_CHECKPOINT.md"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_text(
        "## DNA\nSP-6 staircase\n"
        "## Codebase evidence\nnode_id: svc.UserService#42\nblast-radius: 3 nodes\n",
        encoding="utf-8",
    )

    result = wg.evaluate_write(tmp_path, Path("src/App.java"), framework_root=".claude")
    assert result.ok is True


def test_main_blocks_with_exit_2_for_claude_pretooluse(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    payload = {"tool_name": "Write", "tool_input": {"file_path": "src/App.java"}}
    code = wg.main(["--framework-root", ".claude"], stdin_text=json.dumps(payload))
    captured = capsys.readouterr()
    assert code == 2
    assert "KNOWLEDGE_CHECKPOINT" in captured.err


def test_main_blocks_when_edit_payload_has_no_target_path(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    payload = {"tool_name": "Write", "tool_input": {"content": "x"}}
    code = wg.main(["--framework-root", ".claude"], stdin_text=json.dumps(payload))
    captured = capsys.readouterr()
    assert code == 2
    assert "Unable to identify target path" in captured.err


def test_main_blocks_with_codex_json_decision(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "apply_patch",
        "tool_input": {"command": "*** Begin Patch\n*** Update File: src/App.java\n@@\n-x\n+y\n*** End Patch\n"},
    }
    code = wg.main(["--framework-root", ".agents", "--runtime", "codex"], stdin_text=json.dumps(payload))
    captured = capsys.readouterr()
    assert code == 0
    out = json.loads(captured.out)
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_main_blocks_with_antigravity_json_decision(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    payload = {"toolCall": {"name": "write_to_file", "args": {"file_path": "src/App.java"}}}
    code = wg.main(["--framework-root", ".agents", "--runtime", "antigravity"], stdin_text=json.dumps(payload))
    captured = capsys.readouterr()
    assert code == 0
    assert json.loads(captured.out)["decision"] == "deny"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
/usr/bin/python3 -m pytest .amap/hooks/write-gate/tests/test_write_gate.py -v
```

Expected: FAIL because `write_gate.py` does not exist.

- [ ] **Step 3: Implement minimal hook runner**

Create `.amap/hooks/write-gate/write_gate.py`:

```python
"""Runtime write gate for AMAP decision-point evidence.

Command-hook contract:
- stdin: JSON payload from the agent runtime hook.
- Claude Code: exit 0 allows; exit 2 blocks with stderr reason.
- Codex: stdout JSON with hookSpecificOutput.permissionDecision allow|deny.
- Antigravity: stdout JSON with decision allow|deny.
"""
import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Decision:
    ok: bool
    reason: str = ""


def _load_gate_check(framework_root: Path):
    mod = framework_root / "tools" / "gate-check" / "gates.py"
    spec = importlib.util.spec_from_file_location("gates", mod)
    gates = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gates)
    return gates


_PATCH_FILE_RE = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", re.MULTILINE)


def _path_from_value(value):
    if isinstance(value, str) and value.strip():
        return Path(value.strip())
    return None


def _paths_from_patch_command(command: str):
    return [Path(match.strip()) for match in _PATCH_FILE_RE.findall(command or "")]


def extract_target_paths(payload: dict):
    tool_input = payload.get("tool_input") or {}
    tool_call = payload.get("toolCall") or {}
    tool_args = tool_call.get("args") or {}

    direct = (
        _path_from_value(tool_input.get("file_path"))
        or _path_from_value(tool_input.get("path"))
        or _path_from_value(tool_args.get("file_path"))
        or _path_from_value(tool_args.get("path"))
        or _path_from_value(tool_args.get("FilePath"))
    )
    if direct:
        return [direct]

    command = tool_input.get("command") or tool_args.get("CommandLine") or ""
    return _paths_from_patch_command(command)


def _is_framework_artifact(path: Path, framework_root: str) -> bool:
    parts = path.as_posix()
    return (
        parts.startswith(f"{framework_root}/")
        or parts.startswith("openspec/")
        or parts.startswith("docs/superpowers/specs/")
        or parts.startswith("docs/superpowers/plans/")
    )


def evaluate_write(project_root: Path, target_path: Path, framework_root: str = ".amap") -> Decision:
    if not target_path.as_posix():
        return Decision(True)
    if _is_framework_artifact(target_path, framework_root):
        return Decision(True)

    checkpoint = project_root / framework_root / "knowledge" / "active" / "KNOWLEDGE_CHECKPOINT.md"
    if not checkpoint.exists():
        return Decision(False, f"Missing {checkpoint.relative_to(project_root)} before code write: {target_path}")

    gates = _load_gate_check(project_root / framework_root)
    result = gates.validate_knowledge_checkpoint(checkpoint.read_text(encoding="utf-8"))
    if result.ok:
        return Decision(True)
    return Decision(False, f"Invalid KNOWLEDGE_CHECKPOINT before code write: {result.reason}")


def main(argv=None, stdin_text=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework-root", default=".amap")
    parser.add_argument("--runtime", choices=["claude", "codex", "antigravity"], default="claude")
    args = parser.parse_args(argv)
    raw = stdin_text if stdin_text is not None else sys.stdin.read()
    payload = json.loads(raw or "{}")
    targets = extract_target_paths(payload)
    if not targets:
        decision = Decision(False, "Unable to identify target path for write-gate payload")
    else:
        decisions = [evaluate_write(Path.cwd(), target, framework_root=args.framework_root) for target in targets]
        decision = next((item for item in decisions if not item.ok), Decision(True))
    if decision.ok:
        if args.runtime == "codex":
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}))
        elif args.runtime == "antigravity":
            print(json.dumps({"decision": "allow"}))
        return 0

    if args.runtime == "codex":
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": decision.reason,
            }
        }))
        return 0
    if args.runtime == "antigravity":
        print(json.dumps({"decision": "deny", "reason": decision.reason}))
        return 0
    print(decision.reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

Create `.amap/hooks/write-gate/README.md`:

```markdown
# AMAP Write Gate Hook

Runtime hook for platforms that support pre-write/pre-edit tool interception.

The hook blocks application-code writes unless
`knowledge/active/KNOWLEDGE_CHECKPOINT.md` exists and passes
`tools/gate-check/gates.py::validate_knowledge_checkpoint`.

Framework artifacts, OpenSpec artifacts, and AMAP planning/spec docs are allowed
so the agent can create the checkpoint/spec before implementation writes.

The runner is runtime-aware:
- `--runtime claude` blocks with exit code 2 and stderr.
- `--runtime codex` blocks with Codex `PreToolUse` JSON.
- `--runtime antigravity` blocks with Antigravity decision JSON.
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
/usr/bin/python3 -m pytest .amap/hooks/write-gate/tests/test_write_gate.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/hooks/write-gate/
git commit -m "feat(write-gate): add runtime checkpoint hook runner"
```

---

### Task 3: Scaffold write-gate hooks for capable platforms

**Files:**
- Modify: `cli/platforms/claude_code.py`
- Modify: `cli/platforms/codex.py`
- Modify: `cli/platforms/antigravity.py`
- Modify: `cli/scaffold.py`
- Modify: `cli/plugin-manifest.yaml`
- Create: `.amap/hooks/claude-code/settings.json`
- Create: `.amap/hooks/codex/hooks.json`
- Create: `.amap/hooks/antigravity/hooks.json`
- Modify: `cli/tests/snapshots/antigravity.txt`
- Modify: `cli/tests/snapshots/codex.txt`
- Modify: `cli/tests/snapshots/claude-code.txt`
- Test: `cli/tests/test_snapshots.py`

- [ ] **Step 1: Write failing manifest/snapshot expectation**

Append to `cli/tests/test_scaffold.py`:

```python
def test_manifest_declares_write_gate_plugins(amap_root):
    manifest = load_manifest(amap_root)
    by_name = {p["name"]: p for p in manifest["plugins"]}
    assert by_name["write-gate-core"]["requires_platform_capability"] == "write_gate_hook"
    assert by_name["write-gate-core"]["source"] == "hooks/write-gate/"
    assert by_name["claude-code-write-gate-settings"]["requires_platform_capability"] == "write_gate_hook"
    assert by_name["claude-code-write-gate-settings"]["requires_platform"] == "claude-code"
    assert by_name["codex-write-gate-hooks"]["requires_platform_capability"] == "write_gate_hook"
    assert by_name["codex-write-gate-hooks"]["requires_platform"] == "codex"
    assert by_name["antigravity-write-gate-hooks"]["requires_platform_capability"] == "write_gate_hook"
    assert by_name["antigravity-write-gate-hooks"]["requires_platform"] == "antigravity"
```

Append to `cli/tests/test_platforms.py`:

```python
def test_write_gate_hook_capability_matrix():
    assert get_platform("claude-code").capabilities["write_gate_hook"] is True
    assert get_platform("codex").capabilities["write_gate_hook"] is True
    assert get_platform("antigravity").capabilities["write_gate_hook"] is True
    assert get_platform("generic").capabilities["write_gate_hook"] is False
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
/usr/bin/python3 -m pytest cli/tests/test_scaffold.py::test_manifest_declares_write_gate_plugins cli/tests/test_platforms.py::test_write_gate_hook_capability_matrix -v
```

Expected: FAIL because manifest entries and platform capability values do not exist yet.

- [ ] **Step 3: Enable write-gate capability on hook-capable platforms**

In `cli/platforms/claude_code.py`, add:

```python
        "write_gate_hook": True,
```

to the existing `capabilities` dict.

In `cli/platforms/antigravity.py`, add:

```python
        "write_gate_hook": True,
```

to the existing `capabilities` dict.

In `cli/platforms/codex.py`, add:

```python
    capabilities = {
        "subagent": False,
        "persistent_terminal": False,
        "artifacts": False,
        "image_generation": False,
        "browser": False,
        "write_gate_hook": True,
    }
```

- [ ] **Step 4: Add hooks source mapping**

In `cli/scaffold.py`, add this entry to `SOURCE_MAP`:

```python
    "hooks/":              ".amap/hooks/",
```

- [ ] **Step 5: Add Claude Code hook settings template**

Create `.amap/hooks/claude-code/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/{{ platform.framework_root }}/hooks/write-gate/write_gate.py --framework-root {{ platform.framework_root }} --runtime claude"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 6: Add Codex hook config template**

Create `.amap/hooks/codex/hooks.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "apply_patch|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/python3 \"$(git rev-parse --show-toplevel)/{{ platform.framework_root }}/hooks/write-gate/write_gate.py\" --framework-root {{ platform.framework_root }} --runtime codex",
            "statusMessage": "Checking AMAP write gate"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 7: Add Antigravity hook config template**

Create `.amap/hooks/antigravity/hooks.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "write_to_file|replace_file_content|multi_replace_file_content",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/python3 \"$(git rev-parse --show-toplevel)/{{ platform.framework_root }}/hooks/write-gate/write_gate.py\" --framework-root {{ platform.framework_root }} --runtime antigravity",
            "statusMessage": "Checking AMAP write gate"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 8: Add manifest plugins**

In `cli/plugin-manifest.yaml`, after the `knowledge-index` tool entry:

```yaml
  - name: write-gate-core
    type: hook
    source: hooks/write-gate/
    template: false
    output: "{{ platform.framework_root }}/hooks/write-gate/"
    copy_dir: true
    requires_platform_capability: write_gate_hook

  - name: claude-code-write-gate-settings
    type: hook
    source: hooks/claude-code/settings.json
    template: true
    output: "{{ platform.framework_root }}/settings.json"
    requires_platform_capability: write_gate_hook
    requires_platform: claude-code

  - name: codex-write-gate-hooks
    type: hook
    source: hooks/codex/hooks.json
    template: true
    output: ".codex/hooks.json"
    requires_platform_capability: write_gate_hook
    requires_platform: codex

  - name: antigravity-write-gate-hooks
    type: hook
    source: hooks/antigravity/hooks.json
    template: true
    output: "{{ platform.framework_root }}/hooks.json"
    requires_platform_capability: write_gate_hook
    requires_platform: antigravity
```

- [ ] **Step 9: Run manifest/capability tests**

Run:

```bash
/usr/bin/python3 -m pytest cli/tests/test_scaffold.py::test_manifest_declares_write_gate_plugins cli/tests/test_platforms.py::test_write_gate_hook_capability_matrix -v
```

Expected: PASS.

- [ ] **Step 10: Run snapshot test and refresh intended platform snapshots**

Run:

```bash
/usr/bin/python3 -m pytest cli/tests/test_snapshots.py::test_platform_scaffold_tree_matches_snapshot -q
```

Expected: snapshot differences caused by capable platforms receiving hook core and native hook config.

Claude Code receives:

```text
.claude/hooks/
.claude/hooks/write-gate/
.claude/hooks/write-gate/write_gate.py
.claude/hooks/write-gate/README.md
.claude/hooks/write-gate/tests/test_write_gate.py
.claude/settings.json
```

Codex receives:

```text
.agents/hooks/
.agents/hooks/write-gate/
.agents/hooks/write-gate/write_gate.py
.agents/hooks/write-gate/README.md
.agents/hooks/write-gate/tests/test_write_gate.py
.codex/hooks.json
```

Antigravity receives:

```text
.agents/hooks.json
.agents/hooks/
.agents/hooks/write-gate/
.agents/hooks/write-gate/write_gate.py
.agents/hooks/write-gate/README.md
.agents/hooks/write-gate/tests/test_write_gate.py
```

Refresh snapshots with the existing project-local method used in prior work:

```bash
/usr/bin/python3 - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from cli.commands.init import run_init
from cli.tests.test_snapshots import PLATFORM_OPTIONS, _snapshot_tree

root = Path.cwd()
snap_dir = root / "cli" / "tests" / "snapshots"
for platform_key in sorted(PLATFORM_OPTIONS):
    with TemporaryDirectory() as td:
        target = Path(td) / "proj"
        options = PLATFORM_OPTIONS[platform_key]
        run_init(
            target_dir=str(target),
            amap_root=str(root),
            platform_key=platform_key,
            selected_mcps=options["mcps"],
            language=options["language"],
            assume_yes=True,
        )
        (snap_dir / f"{platform_key}.txt").write_text(_snapshot_tree(target), encoding="utf-8")
PY
```

- [ ] **Step 11: Verify hook config is platform-specific**

Run:

```bash
rg -n "settings.json|hooks.json|hooks/write-gate" cli/tests/snapshots
```

Expected:
- `claude-code.txt` contains `.claude/settings.json` and `.claude/hooks/write-gate/...`.
- `codex.txt` contains `.codex/hooks.json` and `.agents/hooks/write-gate/...`.
- `antigravity.txt` contains `.agents/hooks.json` and `.agents/hooks/write-gate/...`.
- `generic.txt` does not contain hook config or `hooks/write-gate`.

- [ ] **Step 12: Run tests**

Run:

```bash
/usr/bin/python3 -m pytest cli/tests .amap/tools .amap/hooks -q
```

Expected: all PASS.

- [ ] **Step 13: Commit**

```bash
git add cli/platforms/claude_code.py cli/platforms/codex.py cli/platforms/antigravity.py cli/scaffold.py cli/plugin-manifest.yaml .amap/hooks/claude-code/settings.json .amap/hooks/codex/hooks.json .amap/hooks/antigravity/hooks.json cli/tests/test_scaffold.py cli/tests/test_platforms.py cli/tests/snapshots/
git commit -m "feat(scaffold): ship write gate hook for capable platforms"
```

---

### Task 4: Index-aware rule-id validation

**Files:**
- Modify: `.amap/tools/gate-check/gates.py`
- Modify: `.amap/tools/gate-check/cli.py`
- Test: `.amap/tools/gate-check/tests/test_gates.py`

- [ ] **Step 1: Write failing tests**

Append to `.amap/tools/gate-check/tests/test_gates.py`:

```python
def test_knowledge_checkpoint_rejects_ruleid_not_in_valid_set():
    text = (
        "## DNA\nISO-9001 mentioned here\n"
        "## Codebase\nnode_id: svc.UserService#42\nblast-radius: 3 nodes\n"
    )
    result = g.validate_knowledge_checkpoint(text, valid_rule_ids={"SP-6"})
    assert result.ok is False
    assert "valid rule-id" in result.reason


def test_knowledge_checkpoint_accepts_ruleid_from_valid_set():
    text = (
        "## DNA\nSP-6 staircase\n"
        "## Codebase\nnode_id: svc.UserService#42\nblast-radius: 3 nodes\n"
    )
    assert g.validate_knowledge_checkpoint(text, valid_rule_ids={"SP-6"}).ok is True
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py::test_knowledge_checkpoint_rejects_ruleid_not_in_valid_set .amap/tools/gate-check/tests/test_gates.py::test_knowledge_checkpoint_accepts_ruleid_from_valid_set -v
```

Expected: FAIL because `validate_knowledge_checkpoint` does not accept `valid_rule_ids`.

- [ ] **Step 3: Update validator signature**

In `.amap/tools/gate-check/gates.py`, change:

```python
def validate_knowledge_checkpoint(text: str) -> Result:
```

to:

```python
def validate_knowledge_checkpoint(text: str, valid_rule_ids=None, allow_no_knowledge: bool = True) -> Result:
```

Then replace rule-id detection with:

```python
    cited_rule_ids = set(_RULE_ID.findall(text))
    if valid_rule_ids is not None:
        valid_rule_ids = set(valid_rule_ids)
        if not cited_rule_ids.intersection(valid_rule_ids):
            return Result(False, "no valid rule-id from knowledge-index cited")
    elif not cited_rule_ids:
        return Result(False, "no rule-id (e.g. SP-6) cited")
```

Keep the existing codebase evidence checks unchanged.

- [ ] **Step 4: Run tests**

Run:

```bash
/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/tools/gate-check/gates.py .amap/tools/gate-check/tests/test_gates.py
git commit -m "fix(gate-check): validate checkpoint rule ids against knowledge index"
```

---

### Task 5: Index-aware governance-degrade

**Files:**
- Modify: `.amap/tools/gate-check/gates.py`
- Test: `.amap/tools/gate-check/tests/test_gates.py`

- [ ] **Step 1: Write failing tests**

Append to `.amap/tools/gate-check/tests/test_gates.py`:

```python
def test_governance_degrade_requires_no_knowledge_allowed():
    gov = "## Applicable DNA/Conventions\nno approved DNA/conventions for this artifact-type — generic patterns, LOW confidence\n"
    assert g.validate_knowledge_checkpoint(gov, allow_no_knowledge=False).ok is False
    assert g.validate_knowledge_checkpoint(gov, allow_no_knowledge=True).ok is True
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py::test_governance_degrade_requires_no_knowledge_allowed -v
```

Expected: FAIL because governance-degrade currently always passes.

- [ ] **Step 3: Update governance branch**

In `.amap/tools/gate-check/gates.py`, change:

```python
    if _NO_KNOWLEDGE.search(text):
        return Result(True)  # fresh project: no approved DNA/conventions yet → proceed at LOW confidence
```

to:

```python
    if _NO_KNOWLEDGE.search(text):
        if allow_no_knowledge:
            return Result(True)
        return Result(False, "governance-degrade is allowed only when knowledge-index has no matching entries")
```

- [ ] **Step 4: Run tests**

Run:

```bash
/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/tools/gate-check/gates.py .amap/tools/gate-check/tests/test_gates.py
git commit -m "fix(gate-check): make governance degrade index-aware"
```

---

### Task 6: CLI support for `--index` and `--artifact-type`

**Files:**
- Modify: `.amap/tools/gate-check/cli.py`
- Test: `.amap/tools/gate-check/tests/test_gates.py`

- [ ] **Step 1: Write failing CLI test**

Append to `.amap/tools/gate-check/tests/test_gates.py`:

```python
def test_cli_uses_index_to_reject_unknown_ruleid(tmp_path):
    import importlib.util
    cli_mod = Path(__file__).resolve().parents[1] / "cli.py"
    spec2 = importlib.util.spec_from_file_location("cli", cli_mod)
    cli = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(cli)

    checkpoint = tmp_path / "KNOWLEDGE_CHECKPOINT.md"
    checkpoint.write_text(
        "## DNA\nISO-9001\n"
        "## Codebase\nnode_id: svc.UserService#42\nblast-radius: 3 nodes\n",
        encoding="utf-8",
    )
    index = tmp_path / "knowledge-index.yaml"
    index.write_text(
        "entries:\n"
        "  - id: SP-6\n"
        "    store: author-dna\n"
        "    title: staircase\n"
        "    applies_to: [Constructor]\n",
        encoding="utf-8",
    )

    assert cli.main(["knowledge-checkpoint", str(checkpoint), "--index", str(index), "--artifact-type", "Constructor"]) == 1
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py::test_cli_uses_index_to_reject_unknown_ruleid -v
```

Expected: FAIL because the CLI accepts only two positional args.

- [ ] **Step 3: Implement CLI argument parser**

Replace `.amap/tools/gate-check/cli.py` argument handling with:

```python
import argparse
import yaml
```

Add:

```python
def _load_index_rule_ids(index_path, artifact_type=None):
    data = yaml.safe_load(Path(index_path).read_text(encoding="utf-8")) or {}
    entries = data.get("entries") or []
    matched = []
    for entry in entries:
        applies = entry.get("applies_to") or []
        if artifact_type is None or artifact_type in applies:
            matched.append(entry["id"])
    return set(matched), len(matched) == 0
```

Update `main()`:

```python
def main(argv=None):
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("gate", choices=VALIDATORS)
    parser.add_argument("file")
    parser.add_argument("--index")
    parser.add_argument("--artifact-type")
    args = parser.parse_args(argv)

    g = _load_gates()
    text = Path(args.file).read_text(encoding="utf-8")
    kwargs = {}
    if args.gate == "knowledge-checkpoint" and args.index:
        valid_rule_ids, index_empty = _load_index_rule_ids(args.index, args.artifact_type)
        kwargs["valid_rule_ids"] = valid_rule_ids
        kwargs["allow_no_knowledge"] = index_empty

    res = getattr(g, VALIDATORS[args.gate])(text, **kwargs)
    print(("PASS" if res.ok else f"FAIL — {res.reason}"))
    return 0 if res.ok else 1
```

- [ ] **Step 4: Run CLI tests**

Run:

```bash
/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/tools/gate-check/cli.py .amap/tools/gate-check/tests/test_gates.py
git commit -m "feat(gate-check): load checkpoint rule ids from knowledge index"
```

---

### Task 7: Wire write-gate to index-aware validation when index exists

**Files:**
- Modify: `.amap/hooks/write-gate/write_gate.py`
- Test: `.amap/hooks/write-gate/tests/test_write_gate.py`

- [ ] **Step 1: Write failing test**

Append to `.amap/hooks/write-gate/tests/test_write_gate.py`:

```python
def test_blocks_app_write_when_checkpoint_ruleid_not_in_index(tmp_path):
    framework = tmp_path / ".claude"
    checkpoint = framework / "knowledge" / "active" / "KNOWLEDGE_CHECKPOINT.md"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_text(
        "## DNA\nISO-9001\n"
        "## Codebase evidence\nnode_id: svc.UserService#42\nblast-radius: 3 nodes\n",
        encoding="utf-8",
    )
    index = framework / "knowledge" / "long-term" / "knowledge-index.yaml"
    index.parent.mkdir(parents=True)
    index.write_text(
        "entries:\n"
        "  - id: SP-6\n"
        "    store: author-dna\n"
        "    title: staircase\n"
        "    applies_to: [Constructor]\n",
        encoding="utf-8",
    )

    result = wg.evaluate_write(tmp_path, Path("src/App.java"), framework_root=".claude")
    assert result.ok is False
    assert "valid rule-id" in result.reason
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
/usr/bin/python3 -m pytest .amap/hooks/write-gate/tests/test_write_gate.py::test_blocks_app_write_when_checkpoint_ruleid_not_in_index -v
```

Expected: FAIL because write_gate does not load `knowledge-index.yaml`.

- [ ] **Step 3: Implement index loading in write gate**

In `.amap/hooks/write-gate/write_gate.py`, import `yaml` and add:

```python
def _load_all_rule_ids(index_path: Path):
    if not index_path.exists():
        return None, True
    data = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
    entries = data.get("entries") or []
    return {entry["id"] for entry in entries if "id" in entry}, len(entries) == 0
```

In `evaluate_write()`, before validating checkpoint:

```python
    index_path = project_root / framework_root / "knowledge" / "long-term" / "knowledge-index.yaml"
    valid_rule_ids, index_empty = _load_all_rule_ids(index_path)
    result = gates.validate_knowledge_checkpoint(
        checkpoint.read_text(encoding="utf-8"),
        valid_rule_ids=valid_rule_ids,
        allow_no_knowledge=index_empty,
    )
```

- [ ] **Step 4: Run hook tests**

Run:

```bash
/usr/bin/python3 -m pytest .amap/hooks/write-gate/tests/test_write_gate.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/hooks/write-gate/write_gate.py .amap/hooks/write-gate/tests/test_write_gate.py
git commit -m "feat(write-gate): enforce checkpoint ids against knowledge index"
```

---

### Task 8: Update P0 spec status and final verification

**Files:**
- Modify: `docs/superpowers/specs/2026-06-19-decision-gates-followups-design.md`

- [ ] **Step 1: Update spec recommendation**

In the P0 section, replace the three-option undecided wording with:

```markdown
- **Decision:** chọn option 2, nhưng làm portable qua scaffold capability:
  `requires_platform_capability: write_gate_hook`.
- Platform có runtime pre-write/pre-edit hook → scaffold hook deterministic.
- Platform không có capability → không ship hook config; report degrade rõ ràng, không claim deterministic.
- Concrete adapters:
  - Claude Code (`PreToolUse`, matcher `Edit|Write|MultiEdit`, blocks via exit code 2).
  - Codex (`PreToolUse`, matcher `apply_patch|Edit|Write`, blocks via `permissionDecision: deny`).
  - Antigravity (`PreToolUse`, matcher `write_to_file|replace_file_content|multi_replace_file_content`, blocks via `decision: deny`).
- Generic remains `write_gate_hook: false`.
```

Mark P0 as implemented once Task 7 passes.

- [ ] **Step 2: Run full verification**

Run:

```bash
/usr/bin/python3 -m pytest cli/tests .amap/tools .amap/hooks -q
```

Expected: all PASS.

- [ ] **Step 3: Confirm scaffold output**

Run:

```bash
rg -n "write-gate|settings.json" cli/tests/snapshots
```

Expected:
- Claude Code snapshot includes `.claude/settings.json` and `.claude/hooks/write-gate/`.
- Codex snapshot includes `.codex/hooks.json` and `.agents/hooks/write-gate/`.
- Antigravity snapshot includes `.agents/hooks.json` and `.agents/hooks/write-gate/`.
- Generic snapshot does not include write-gate runtime hook files.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-06-19-decision-gates-followups-design.md
git commit -m "docs(spec): mark capability-gated write gate decision"
```

---

## Self-Review

Spec coverage:
- P0 gate-trigger deterministic: Tasks 1-3 and 7.
- Residual C-22 write-tho outside flow: Tasks 2-3 block raw app writes without checkpoint.
- `_RULE_ID` index-aware: Tasks 4 and 6.
- Governance-degrade index-aware: Tasks 5 and 6.
- P1/P2 completed items are not reimplemented.

Placeholder scan:
- No `TBD`, `TODO`, or "implement later" placeholders.
- Every code-changing step includes exact file paths and concrete code.

Type consistency:
- Capability name is consistently `write_gate_hook`.
- Manifest keys are consistently `requires_platform_capability` and `requires_platform`.
- Hook runner function names are consistently `extract_target_paths`, `evaluate_write`, and `main`.
- Gate CLI args are consistently `--index` and `--artifact-type`.
