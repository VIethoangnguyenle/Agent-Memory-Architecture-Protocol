# Bash-Write Gate (C-22b) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the runtime write-gate so code writes performed via the `Bash`/shell tool (`tee`, `>`, `sed -i`, `cp/mv`, `dd`, `patch`, formatters…) are subject to the same `KNOWLEDGE_CHECKPOINT` gate as `Edit/Write/MultiEdit`, closing residual C-22b.

**Architecture:** Add a pure heuristic parser `parse_shell_writes(command)` that extracts concrete write targets from a shell command and flags unresolved (dynamic) writes. In `main()`, branch by tool type: shell tools route through the parser with git-ignore filtering (D5) and fail-open semantics (D2/D3); edit tools keep the existing path. `extract_target_paths` and `evaluate_write` are **not modified** — all existing behavior and tests stay intact. Finally, add the shell tool to each runtime hook matcher.

**Tech Stack:** Python 3.9+ stdlib (`re`, `shlex`, `subprocess`), pytest (`/usr/bin/python3 -m pytest`, import-mode=importlib per `pyproject.toml`). Claude Code `settings.json`, Codex `.codex/hooks.json`, Antigravity `hooks.json`.

**Spec:** `docs/superpowers/specs/2026-06-20-bash-write-gate-design.md`

**Branch:** `bash-write-gate` (already created; spec already committed).

---

## File Structure

- **`.amap/hooks/write-gate/write_gate.py`** (modify) — add `parse_shell_writes`, `_t3_targets`, `_git_ignored`, tool helpers (`_tool_name`, `_is_shell_tool`, `_command_text`), `_warn`; rewrite `main()` to branch by tool type. `extract_target_paths`, `evaluate_write`, `_print_runtime_decision` unchanged.
- **`.amap/hooks/write-gate/tests/test_write_gate.py`** (modify) — append parser unit tests, git-ignore tests, and shell-branch `main()` integration tests.
- **`.amap/hooks/claude-code/settings.json`** (modify) — matcher `Edit|Write|MultiEdit` → `Edit|Write|MultiEdit|Bash`.
- **`.amap/hooks/codex/hooks.json`** (modify) — add Codex shell tool to matcher.
- **`.amap/hooks/antigravity/hooks.json`** (modify) — add Antigravity command tool to matcher.

Module-level constants assumed by later tasks (define in Task 1 / Task 3):
- `_DYNAMIC = re.compile(r"[\$`*?]")` — markers of an unresolved path.
- `_REDIRECT_RE = re.compile(r"(?<![0-9>])>>?\s*([^\s|&;<>]+)")`.
- `_SEGMENT_RE = re.compile(r"[\n;]|\|\||&&|\|")`.
- `_DEVNULL = {"/dev/null", "/dev/stdout", "/dev/stderr"}`.
- `_SHELL_TOOLS = {"bash", "shell", "local_shell", "run_command", "run_terminal_cmd"}`.

---

### Task 1: `parse_shell_writes` heuristic parser

**Files:**
- Modify: `.amap/hooks/write-gate/write_gate.py`
- Test: `.amap/hooks/write-gate/tests/test_write_gate.py`

- [ ] **Step 1: Write the failing tests**

Append to `.amap/hooks/write-gate/tests/test_write_gate.py`:

```python
def test_parse_redirect_write():
    paths, unresolved = wg.parse_shell_writes("echo x > src/App.java")
    assert paths == [Path("src/App.java")]
    assert unresolved is False


def test_parse_append_redirect():
    paths, _ = wg.parse_shell_writes("echo x >> src/App.java")
    assert paths == [Path("src/App.java")]


def test_parse_ignores_devnull_and_fd_redirect():
    paths, unresolved = wg.parse_shell_writes("run_tests > /dev/null 2>&1")
    assert paths == []
    assert unresolved is False


def test_parse_tee():
    paths, _ = wg.parse_shell_writes("echo x | tee src/App.java")
    assert paths == [Path("src/App.java")]


def test_parse_sed_inplace():
    paths, _ = wg.parse_shell_writes("sed -i 's/a/b/' src/App.java")
    assert paths == [Path("src/App.java")]


def test_parse_cp_and_mv_dest():
    assert wg.parse_shell_writes("cp /tmp/x src/App.java")[0] == [Path("src/App.java")]
    assert wg.parse_shell_writes("mv old.java src/App.java")[0] == [Path("src/App.java")]


def test_parse_dd_of():
    paths, _ = wg.parse_shell_writes("dd if=/tmp/x of=src/App.java")
    assert paths == [Path("src/App.java")]


def test_parse_patch_format():
    paths, _ = wg.parse_shell_writes("*** Add File: src/App.java\n+code\n")
    assert paths == [Path("src/App.java")]


def test_parse_prettier_write():
    paths, _ = wg.parse_shell_writes("prettier --write src/App.js")
    assert paths == [Path("src/App.js")]


def test_parse_readonly_command_has_no_writes():
    paths, unresolved = wg.parse_shell_writes("grep -r foo src && ls -la")
    assert paths == []
    assert unresolved is False


def test_parse_dynamic_path_is_unresolved():
    paths, unresolved = wg.parse_shell_writes('tee "$TARGET"')
    assert paths == []
    assert unresolved is True


def test_parse_git_apply_is_unresolved():
    paths, unresolved = wg.parse_shell_writes("git apply fix.patch")
    assert paths == []
    assert unresolved is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest .amap/hooks/write-gate/tests/test_write_gate.py -k parse -v`
Expected: FAIL with `AttributeError: module 'write_gate' has no attribute 'parse_shell_writes'`.

- [ ] **Step 3: Add the parser implementation**

In `.amap/hooks/write-gate/write_gate.py`, add `import shlex` next to the existing imports, and add these module-level constants after the existing `_PATCH_FILE_RE`:

```python
_DYNAMIC = re.compile(r"[\$`*?]")
_REDIRECT_RE = re.compile(r"(?<![0-9>])>>?\s*([^\s|&;<>]+)")
_SEGMENT_RE = re.compile(r"[\n;]|\|\||&&|\|")
_DEVNULL = {"/dev/null", "/dev/stdout", "/dev/stderr"}
```

Then add the parser functions (place them after `_paths_from_patch_command`):

```python
def _is_dynamic(token: str) -> bool:
    return bool(_DYNAMIC.search(token)) or "$(" in token


def _t3_targets(verb: str, args: list) -> list:
    """Return write targets for a known write command, or [None] if the verb
    writes but no concrete target is parseable."""
    nonflag = [a for a in args if not a.startswith("-")]
    if verb == "tee":
        return nonflag or [None]
    if verb == "sed":
        if any(a == "-i" or a.startswith("-i") for a in args):
            return nonflag[1:] if len(nonflag) > 1 else [None]
        return []
    if verb in ("cp", "mv", "install"):
        return [nonflag[-1]] if nonflag else [None]
    if verb == "dd":
        return [a[3:] for a in args if a.startswith("of=")]
    if verb == "git":
        if args[:1] == ["apply"]:
            return [None]
        if args[:1] == ["checkout"] and "--" in args:
            return args[args.index("--") + 1:] or [None]
        if args[:1] == ["restore"]:
            return [a for a in args[1:] if not a.startswith("-")] or [None]
        return []
    if verb == "prettier":
        return (nonflag or [None]) if "--write" in args else []
    if verb == "gofmt":
        return (nonflag or [None]) if "-w" in args else []
    if verb == "black":
        return nonflag or [None]
    if verb == "ruff":
        if "--fix" in args or "format" in args:
            return [a for a in nonflag if a not in ("format", "check")] or [None]
        return []
    return []


def parse_shell_writes(command: str):
    """Heuristically extract concrete write targets from a shell command.

    Returns (paths, unresolved):
    - paths: list[Path] of concrete write targets (deduped, order-preserving).
    - unresolved: True if a recognized write verb had a dynamic/unparseable path.
    """
    command = command or ""
    raw_paths = []
    unresolved = False

    raw_paths.extend(_paths_from_patch_command(command))

    for seg in _SEGMENT_RE.split(command):
        seg = seg.strip()
        if not seg:
            continue
        for match in _REDIRECT_RE.finditer(seg):
            target = match.group(1)
            if target in _DEVNULL:
                continue
            if _is_dynamic(target):
                unresolved = True
            else:
                raw_paths.append(Path(target))
        try:
            tokens = shlex.split(seg)
        except ValueError:
            tokens = seg.split()
        if not tokens:
            continue
        verb = Path(tokens[0]).name
        for target in _t3_targets(verb, tokens[1:]):
            if target is None or _is_dynamic(target):
                unresolved = True
            else:
                raw_paths.append(Path(target))

    seen, paths = set(), []
    for p in raw_paths:
        key = p.as_posix()
        if key not in seen:
            seen.add(key)
            paths.append(p)
    return paths, unresolved
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `/usr/bin/python3 -m pytest .amap/hooks/write-gate/tests/test_write_gate.py -k parse -v`
Expected: all `test_parse_*` PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/hooks/write-gate/write_gate.py .amap/hooks/write-gate/tests/test_write_gate.py
git commit -m "feat(write-gate): add parse_shell_writes heuristic parser"
```

---

### Task 2: `_git_ignored` classification helper (D5)

**Files:**
- Modify: `.amap/hooks/write-gate/write_gate.py`
- Test: `.amap/hooks/write-gate/tests/test_write_gate.py`

- [ ] **Step 1: Write the failing tests**

Append to `.amap/hooks/write-gate/tests/test_write_gate.py`:

```python
import subprocess


def _init_git_repo(root):
    subprocess.run(["git", "init", "-q"], cwd=str(root), check=True)
    (root / ".gitignore").write_text("coverage/\ndist/\n", encoding="utf-8")


def test_git_ignored_true_for_ignored_path(tmp_path):
    _init_git_repo(tmp_path)
    assert wg._git_ignored(tmp_path, Path("coverage/lcov.info")) is True


def test_git_ignored_false_for_tracked_source(tmp_path):
    _init_git_repo(tmp_path)
    assert wg._git_ignored(tmp_path, Path("src/App.java")) is False


def test_git_ignored_false_when_not_a_git_repo(tmp_path):
    assert wg._git_ignored(tmp_path, Path("coverage/lcov.info")) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest .amap/hooks/write-gate/tests/test_write_gate.py -k git_ignored -v`
Expected: FAIL with `AttributeError: module 'write_gate' has no attribute '_git_ignored'`.

- [ ] **Step 3: Implement the helper**

In `.amap/hooks/write-gate/write_gate.py`, add `import subprocess` next to the other imports, and add this function after `parse_shell_writes`:

```python
def _git_ignored(project_root: Path, path: Path) -> bool:
    """True if `path` is git-ignored under project_root. Not-a-git-repo, missing
    git, or any error degrades to False (treat as a gated, non-ignored path)."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", path.as_posix()],
            cwd=str(project_root),
            capture_output=True,
        )
    except (FileNotFoundError, OSError):
        return False
    return result.returncode == 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `/usr/bin/python3 -m pytest .amap/hooks/write-gate/tests/test_write_gate.py -k git_ignored -v`
Expected: all three PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/hooks/write-gate/write_gate.py .amap/hooks/write-gate/tests/test_write_gate.py
git commit -m "feat(write-gate): add git-ignore classification helper"
```

---

### Task 3: Shell-branch routing in `main()` (D1/D2/D3/D5)

**Files:**
- Modify: `.amap/hooks/write-gate/write_gate.py`
- Test: `.amap/hooks/write-gate/tests/test_write_gate.py`

- [ ] **Step 1: Write the failing tests**

Append to `.amap/hooks/write-gate/tests/test_write_gate.py`:

```python
def test_bash_write_to_code_blocks_without_checkpoint(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    payload = {"tool_name": "Bash", "tool_input": {"command": "echo x > src/App.java"}}
    code = wg.main(["--framework-root", ".amap"], stdin_text=json.dumps(payload))
    captured = capsys.readouterr()
    assert code == 2
    assert "KNOWLEDGE_CHECKPOINT" in captured.err


def test_bash_write_to_code_allows_with_valid_checkpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    checkpoint = tmp_path / ".amap" / "knowledge" / "active" / "KNOWLEDGE_CHECKPOINT.md"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_text(
        "## DNA\nSP-6 staircase\n"
        "## Codebase evidence\nnode_id: svc.UserService#42\nblast-radius: 3 nodes\n",
        encoding="utf-8",
    )
    payload = {"tool_name": "Bash", "tool_input": {"command": "tee src/App.java"}}
    code = wg.main(["--framework-root", ".amap"], stdin_text=json.dumps(payload))
    assert code == 0


def test_bash_readonly_command_allowed_fail_open(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = {"tool_name": "Bash", "tool_input": {"command": "grep -r foo src && ls"}}
    code = wg.main(["--framework-root", ".amap"], stdin_text=json.dumps(payload))
    assert code == 0


def test_bash_write_to_gitignored_path_allowed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    (tmp_path / ".gitignore").write_text("coverage/\n", encoding="utf-8")
    payload = {"tool_name": "Bash", "tool_input": {"command": "echo x > coverage/lcov.info"}}
    code = wg.main(["--framework-root", ".amap"], stdin_text=json.dumps(payload))
    assert code == 0


def test_bash_write_to_framework_artifact_allowed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = {"tool_name": "Bash", "tool_input": {"command": "echo x > .amap/knowledge/active/REQUIREMENT.md"}}
    code = wg.main(["--framework-root", ".amap"], stdin_text=json.dumps(payload))
    assert code == 0


def test_bash_dynamic_write_warns_and_allows(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    payload = {"tool_name": "Bash", "tool_input": {"command": 'tee "$TARGET"'}}
    code = wg.main(["--framework-root", ".amap"], stdin_text=json.dumps(payload))
    captured = capsys.readouterr()
    assert code == 0
    assert "unresolved" in captured.err.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest .amap/hooks/write-gate/tests/test_write_gate.py -k bash -v`
Expected: FAIL — `test_bash_readonly_command_allowed_fail_open` returns exit 2 ("Unable to identify target path"), and the block/allow cases misbehave, because `main()` does not yet treat Bash as a shell tool.

- [ ] **Step 3: Add tool helpers**

In `.amap/hooks/write-gate/write_gate.py`, add this constant near the other module constants:

```python
_SHELL_TOOLS = {"bash", "shell", "local_shell", "run_command", "run_terminal_cmd"}
```

Add these helpers after `_git_ignored`:

```python
def _tool_name(payload: dict) -> str:
    return payload.get("tool_name") or (payload.get("toolCall") or {}).get("name") or ""


def _is_shell_tool(name: str) -> bool:
    return name.lower() in _SHELL_TOOLS


def _command_text(payload: dict) -> str:
    tool_input = payload.get("tool_input") or {}
    tool_args = (payload.get("toolCall") or {}).get("args") or {}
    return tool_input.get("command") or tool_args.get("CommandLine") or tool_args.get("command") or ""


def _warn(message: str) -> None:
    print(message, file=sys.stderr)
```

- [ ] **Step 4: Rewrite `main()` to branch by tool type**

In `.amap/hooks/write-gate/write_gate.py`, replace the entire `main()` function with:

```python
def main(argv=None, stdin_text=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework-root", default=".amap")
    parser.add_argument("--runtime", choices=["claude", "codex", "antigravity"], default="claude")
    args = parser.parse_args(argv)
    raw = stdin_text if stdin_text is not None else sys.stdin.read()
    payload = json.loads(raw or "{}")
    root = Path.cwd()

    if _is_shell_tool(_tool_name(payload)):
        targets, unresolved = parse_shell_writes(_command_text(payload))
        targets = [t for t in targets if not _git_ignored(root, t)]
        if not targets:
            if unresolved:
                _warn("write-gate: shell write with unresolved path — allowed (heuristic).")
            decision = Decision(True)
        else:
            decisions = [
                evaluate_write(root, target, framework_root=args.framework_root)
                for target in targets
            ]
            decision = next((item for item in decisions if not item.ok), Decision(True))
    else:
        targets = extract_target_paths(payload)
        if not targets:
            decision = Decision(False, "Unable to identify target path for write-gate payload")
        else:
            decisions = [
                evaluate_write(root, target, framework_root=args.framework_root)
                for target in targets
            ]
            decision = next((item for item in decisions if not item.ok), Decision(True))

    return _print_runtime_decision(args.runtime, decision)
```

- [ ] **Step 5: Run the full hook test suite to verify pass + no regressions**

Run: `/usr/bin/python3 -m pytest .amap/hooks/write-gate/tests/test_write_gate.py -v`
Expected: all tests PASS — the new `bash` tests and every pre-existing `Edit/Write/apply_patch/antigravity` test.

- [ ] **Step 6: Commit**

```bash
git add .amap/hooks/write-gate/write_gate.py .amap/hooks/write-gate/tests/test_write_gate.py
git commit -m "feat(write-gate): gate shell writes with fail-open + gitignore routing"
```

---

### Task 4: Add shell tool to runtime hook matchers

**Files:**
- Modify: `.amap/hooks/claude-code/settings.json`
- Modify: `.amap/hooks/codex/hooks.json`
- Modify: `.amap/hooks/antigravity/hooks.json`

- [ ] **Step 1: Verify the exact shell-tool matcher token per runtime**

The hook only fires if the matcher token equals the runtime's shell tool name. Confirm against the runtime hook docs (same references used by the C-22 P0 plan):
- Claude Code (`https://code.claude.com/docs/en/hooks`): shell tool is `Bash`.
- Codex (`https://developers.openai.com/codex/hooks`): confirm the local shell tool token (expected `shell`; the runner already accepts `shell`/`local_shell`).
- Antigravity (`https://antigravity.google/docs/hooks`): confirm the command/terminal tool token (expected `run_command`).

If a runtime's actual token differs, use the verified token in that runtime's matcher below **and** add it to `_SHELL_TOOLS` in `write_gate.py` if not already present.

- [ ] **Step 2: Update the Claude Code matcher**

In `.amap/hooks/claude-code/settings.json`, change:

```json
        "matcher": "Edit|Write|MultiEdit",
```

to:

```json
        "matcher": "Edit|Write|MultiEdit|Bash",
```

- [ ] **Step 3: Update the Codex matcher**

In `.amap/hooks/codex/hooks.json`, change:

```json
        "matcher": "apply_patch|Edit|Write",
```

to (using the token verified in Step 1):

```json
        "matcher": "apply_patch|Edit|Write|shell",
```

- [ ] **Step 4: Update the Antigravity matcher**

In `.amap/hooks/antigravity/hooks.json`, change:

```json
        "matcher": "write_to_file|replace_file_content|multi_replace_file_content",
```

to (using the token verified in Step 1):

```json
        "matcher": "write_to_file|replace_file_content|multi_replace_file_content|run_command",
```

- [ ] **Step 5: Validate JSON well-formedness**

Run:
```bash
/usr/bin/python3 -c "import json; [json.load(open(p)) for p in ['.amap/hooks/claude-code/settings.json','.amap/hooks/codex/hooks.json','.amap/hooks/antigravity/hooks.json']]; print('OK')"
```
Expected: `OK`.

- [ ] **Step 6: Refresh scaffold snapshots only if affected**

Run: `/usr/bin/python3 -m pytest cli/tests/test_snapshots.py -q`
Expected: PASS. The snapshots capture the file tree, so a matcher-string change usually does not affect them. **If** a snapshot test fails because hook config content is captured, refresh with the project-local method:

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

- [ ] **Step 7: Commit**

```bash
git add .amap/hooks/claude-code/settings.json .amap/hooks/codex/hooks.json .amap/hooks/antigravity/hooks.json cli/tests/snapshots/
git commit -m "feat(write-gate): match shell tool in runtime hook configs"
```

---

### Task 5: Full verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full affected test suite**

Run: `/usr/bin/python3 -m pytest .amap/hooks .amap/tools cli/tests -q`
Expected: all PASS.

- [ ] **Step 2: Manual end-to-end smoke (block path)**

Run from the repo root with no checkpoint present:
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"echo x > /tmp/amap_probe_src/App.java"}}' \
  | /usr/bin/python3 .amap/hooks/write-gate/write_gate.py --framework-root .amap --runtime claude; echo "exit=$?"
```
Expected: stderr mentions `KNOWLEDGE_CHECKPOINT`, `exit=2`.

> Note: `/tmp/...App.java` is non-framework and (outside any git repo) not git-ignored, so it is gated — this confirms the block path. Read-only commands like `grep` return `exit=0`.

- [ ] **Step 3: Manual end-to-end smoke (fail-open path)**

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"grep -r foo src"}}' \
  | /usr/bin/python3 .amap/hooks/write-gate/write_gate.py --framework-root .amap --runtime claude; echo "exit=$?"
```
Expected: `exit=0`, no block reason.

- [ ] **Step 4: Final commit (if any snapshot/cleanup remains)**

```bash
git status
# commit only if there are uncommitted, intended changes
```

---

## Self-Review

**Spec coverage:**
- §2 heuristic pre-parse → Task 1 (`parse_shell_writes`).
- D1 parity (reuse `evaluate_write`) → Task 3 `main()` shell branch calls `evaluate_write`.
- D2 fail-open for shell, fail-closed for edit tools → Task 3 (`_is_shell_tool` branch vs `else`).
- D3 warn-and-allow on dynamic path → Task 1 (`unresolved` flag) + Task 3 (`_warn`, `test_bash_dynamic_write_warns_and_allows`).
- D4 formatters under same rule → Task 1 (`prettier`/`gofmt`/`ruff`/`black` in `_t3_targets`) + Task 3 parity.
- D5 skip git-ignored → Task 2 (`_git_ignored`) + Task 3 filter (`test_bash_write_to_gitignored_path_allowed`).
- §4.1 parser tiers T1–T3 → Task 1 (`_paths_from_patch_command`, `_REDIRECT_RE`, `_t3_targets`).
- §4.3 tool-awareness per runtime → Task 3 (`_SHELL_TOOLS`) + Task 4 (matchers).
- §5 file list → Tasks 1–4 cover every listed file; `cli/tests/snapshots` handled conditionally in Task 4 Step 6.
- §7 acceptance criteria → Task 3 integration tests + Task 5 manual smokes.
- Surgical guarantee (evaluate_write / Edit-Write unchanged) → Task 3 Step 5 runs full pre-existing suite for regression.

**Placeholder scan:** No TBD/TODO. The one "verify token" item (Task 4 Step 1) is a concrete verification action with default values supplied and a fallback instruction — not an undefined requirement.

**Type/name consistency:** `parse_shell_writes` returns `(paths, unresolved)` in Task 1 and is consumed with that shape in Task 3. `_git_ignored(project_root, path)` signature matches between Task 2 definition and Task 3 call. `_tool_name`/`_is_shell_tool`/`_command_text`/`_warn`/`_t3_targets`/`Decision`/`evaluate_write`/`extract_target_paths`/`_print_runtime_decision` names are used consistently across tasks. `_SHELL_TOOLS` defined in Task 3, referenced in Task 4.
