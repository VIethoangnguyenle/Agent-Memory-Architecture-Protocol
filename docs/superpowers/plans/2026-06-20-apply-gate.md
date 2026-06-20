# Apply-Gate (C-23) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the runtime write-gate require apply-entry evidence — `Pha 2 DONE` (spec phase complete) and no unresolved `[BLOCKER-ARCH]` — before allowing any non-framework code write, closing the `/opsx:apply` back door (#2) and operationalizing R-Flow-2 apply-entry (#3) in one workflow-agnostic mechanism.

**Architecture:** Add a pure validator `validate_apply_gate` to `gate-check/gates.py` (exposed via a `gate-check apply-gate` CLI subcommand), then call it from `write_gate.evaluate_write` after the existing knowledge-checkpoint check. Because `evaluate_write` is shared by both the Edit/Write and Bash (C-22b) branches, both write paths inherit the apply-gate. Framework artifacts stay exempt.

**Tech Stack:** Python 3.9+ stdlib (`re`), pytest (`/usr/bin/python3 -m pytest`, import-mode=importlib per `pyproject.toml`).

**Spec:** `docs/superpowers/specs/2026-06-20-apply-gate-design.md`

**Branch:** `apply-gate` (already created, stacked on `bash-write-gate`/PR #12; spec already committed). Merge after #12.

---

## File Structure

- **`.amap/tools/gate-check/gates.py`** (modify) — add `validate_apply_gate(text) -> Result`. Pure text validator, sibling to `validate_phase_chain`.
- **`.amap/tools/gate-check/cli.py`** (modify) — register `"apply-gate": "validate_apply_gate"` in `VALIDATORS`.
- **`.amap/tools/gate-check/tests/test_gates.py`** (modify) — unit tests for the validator + a CLI test.
- **`.amap/hooks/write-gate/write_gate.py`** (modify) — `evaluate_write` calls `validate_apply_gate` against `AGENT_TRANSPARENCY.md` after checkpoint passes.
- **`.amap/hooks/write-gate/tests/test_write_gate.py`** (modify) — 2 existing allow-tests get an `AGENT_TRANSPARENCY` fixture; add new block/allow tests.
- **`.amap/rules/rules-flow.md`** (modify) — one sentence on R-Flow-2 noting apply-entry is now hook-enforced.

---

### Task 1: `validate_apply_gate` validator + CLI subcommand

**Files:**
- Modify: `.amap/tools/gate-check/gates.py`
- Modify: `.amap/tools/gate-check/cli.py`
- Test: `.amap/tools/gate-check/tests/test_gates.py`

- [ ] **Step 1: Write the failing tests**

First check how `test_gates.py` imports the module (it already imports the `gates` module — match the existing alias; the snippets below assume it is available as `g`, as in the existing tests). Append:

```python
def test_apply_gate_passes_with_pha2_and_no_blocker():
    assert g.validate_apply_gate("Pha 1 DONE\nPha 2 DONE\n").ok is True


def test_apply_gate_fails_without_pha2():
    result = g.validate_apply_gate("Pha 1 DONE\n")
    assert result.ok is False
    assert "Pha 2 DONE" in result.reason


def test_apply_gate_fails_with_open_blocker():
    text = "Pha 1 DONE\nPha 2 DONE\n[BLOCKER-ARCH] coupling risk\n"
    assert g.validate_apply_gate(text).ok is False


def test_apply_gate_passes_when_blocker_resolved():
    text = (
        "Pha 1 DONE\nPha 2 DONE\n"
        "[BLOCKER-ARCH] coupling risk\n"
        "[BLOCKER-ARCH RESOLVED] 2026-06-20 user approved approach\n"
    )
    assert g.validate_apply_gate(text).ok is True
```

Also add a CLI test (match how the file loads `cli` — if there is no existing cli import, load it via importlib like the followups-spec test did):

```python
def test_cli_apply_gate_exit_codes(tmp_path):
    import importlib.util
    cli_mod = Path(__file__).resolve().parents[1] / "cli.py"
    spec = importlib.util.spec_from_file_location("cli", cli_mod)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)

    f = tmp_path / "AGENT_TRANSPARENCY.md"
    f.write_text("Pha 1 DONE\nPha 2 DONE\n", encoding="utf-8")
    assert cli.main(["apply-gate", str(f)]) == 0
    f.write_text("Pha 1 DONE\n", encoding="utf-8")
    assert cli.main(["apply-gate", str(f)]) == 1
```

(If `Path` or `importlib` is not already imported at the top of `test_gates.py`, add `from pathlib import Path`.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -k apply_gate -v`
Expected: FAIL — `AttributeError: module 'gates' has no attribute 'validate_apply_gate'` and the CLI test fails on the unknown `apply-gate` choice.

- [ ] **Step 3: Implement the validator**

In `.amap/tools/gate-check/gates.py`, add this function right after `validate_phase_chain` (keep `import re` — already present):

```python
def validate_apply_gate(text: str) -> Result:
    """Apply-entry evidence (R-Flow-2): spec phase complete + no open blocker.

    PASS requires a 'Pha 2 DONE' marker and that every '[BLOCKER-ARCH]' has a
    matching '[BLOCKER-ARCH RESOLVED]'. Unlike validate_phase_chain, a 'Pha 1
    DONE'-only transparency does NOT pass — code writes need the spec phase done.
    """
    if not re.search(r"Pha\s*2\s*DONE", text):
        return Result(False, "apply-gate: no 'Pha 2 DONE' marker (spec phase not complete)")
    opens = text.count("[BLOCKER-ARCH]")
    resolved = text.count("[BLOCKER-ARCH RESOLVED]")
    if opens > resolved:
        return Result(False, f"apply-gate: {opens - resolved} unresolved [BLOCKER-ARCH]")
    return Result(True)
```

(Note: `text.count("[BLOCKER-ARCH]")` matches the open marker literally; `[BLOCKER-ARCH RESOLVED]` has a space before `RESOLVED`, so it is NOT counted as an open marker — the two counts are independent.)

- [ ] **Step 4: Register the CLI subcommand**

In `.amap/tools/gate-check/cli.py`, add to the `VALIDATORS` dict:

```python
    "apply-gate": "validate_apply_gate",
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -v`
Expected: all PASS (new apply_gate tests + every pre-existing gate test).

- [ ] **Step 6: Commit**

```bash
git add .amap/tools/gate-check/gates.py .amap/tools/gate-check/cli.py .amap/tools/gate-check/tests/test_gates.py
git commit -m "feat(gate-check): add apply-gate validator (Pha 2 DONE + no open blocker)"
```

---

### Task 2: Wire apply-gate into `evaluate_write`

**Files:**
- Modify: `.amap/hooks/write-gate/write_gate.py`
- Test: `.amap/hooks/write-gate/tests/test_write_gate.py`

- [ ] **Step 1: Update the two existing allow-tests to include an apply-evidence fixture**

These two tests will require `AGENT_TRANSPARENCY.md` with `Pha 2 DONE` after this task. Adding the file now is harmless under current code (it is ignored), so they stay green across the change.

In `test_allows_app_write_with_valid_checkpoint` (creates `framework = tmp_path / ".amap"` and a checkpoint), add after the checkpoint is written:

```python
    (framework / "knowledge" / "active" / "AGENT_TRANSPARENCY.md").write_text(
        "Pha 1 DONE\nPha 2 DONE\n", encoding="utf-8"
    )
```

In `test_bash_write_to_code_allows_with_valid_checkpoint` (chdir to tmp_path, creates checkpoint under `tmp_path/.amap/...`), add after the checkpoint is written:

```python
    (tmp_path / ".amap" / "knowledge" / "active" / "AGENT_TRANSPARENCY.md").write_text(
        "Pha 1 DONE\nPha 2 DONE\n", encoding="utf-8"
    )
```

- [ ] **Step 2: Add the new failing tests**

Append to `.amap/hooks/write-gate/tests/test_write_gate.py`:

```python
def _write_valid_checkpoint(active_dir):
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / "KNOWLEDGE_CHECKPOINT.md").write_text(
        "## DNA\nSP-6 staircase\n"
        "## Codebase evidence\nnode_id: svc.UserService#42\nblast-radius: 3 nodes\n",
        encoding="utf-8",
    )


def test_blocks_app_write_when_transparency_missing(tmp_path):
    _write_valid_checkpoint(tmp_path / ".amap" / "knowledge" / "active")
    result = wg.evaluate_write(tmp_path, Path("src/App.java"), framework_root=".amap")
    assert result.ok is False
    assert "AGENT_TRANSPARENCY" in result.reason


def test_blocks_app_write_with_checkpoint_but_no_pha2(tmp_path):
    active = tmp_path / ".amap" / "knowledge" / "active"
    _write_valid_checkpoint(active)
    (active / "AGENT_TRANSPARENCY.md").write_text("Pha 1 DONE\n", encoding="utf-8")
    result = wg.evaluate_write(tmp_path, Path("src/App.java"), framework_root=".amap")
    assert result.ok is False
    assert "Pha 2 DONE" in result.reason


def test_blocks_app_write_with_open_blocker(tmp_path):
    active = tmp_path / ".amap" / "knowledge" / "active"
    _write_valid_checkpoint(active)
    (active / "AGENT_TRANSPARENCY.md").write_text(
        "Pha 1 DONE\nPha 2 DONE\n[BLOCKER-ARCH] coupling risk\n", encoding="utf-8"
    )
    result = wg.evaluate_write(tmp_path, Path("src/App.java"), framework_root=".amap")
    assert result.ok is False


def test_allows_app_write_with_checkpoint_and_apply_evidence(tmp_path):
    active = tmp_path / ".amap" / "knowledge" / "active"
    _write_valid_checkpoint(active)
    (active / "AGENT_TRANSPARENCY.md").write_text(
        "Pha 1 DONE\nPha 2 DONE\n", encoding="utf-8"
    )
    result = wg.evaluate_write(tmp_path, Path("src/App.java"), framework_root=".amap")
    assert result.ok is True
```

- [ ] **Step 3: Run tests to verify the new ones fail**

Run: `/usr/bin/python3 -m pytest .amap/hooks/write-gate/tests/test_write_gate.py -k "transparency or pha2 or blocker or apply_evidence" -v`
Expected: `test_blocks_app_write_when_transparency_missing`, `test_blocks_app_write_with_checkpoint_but_no_pha2`, and `test_blocks_app_write_with_open_blocker` FAIL (current code allows the write once the checkpoint is valid). `test_allows_app_write_with_checkpoint_and_apply_evidence` already passes.

- [ ] **Step 4: Implement the apply-gate check in `evaluate_write`**

In `.amap/hooks/write-gate/write_gate.py`, find the tail of `evaluate_write`:

```python
    result = gates.validate_knowledge_checkpoint(
        checkpoint.read_text(encoding="utf-8"),
        valid_rule_ids=valid_rule_ids,
        allow_no_knowledge=index_empty,
    )
    if result.ok:
        return Decision(True)
    return Decision(False, f"Invalid KNOWLEDGE_CHECKPOINT before code write: {result.reason}")
```

Replace it with:

```python
    result = gates.validate_knowledge_checkpoint(
        checkpoint.read_text(encoding="utf-8"),
        valid_rule_ids=valid_rule_ids,
        allow_no_knowledge=index_empty,
    )
    if not result.ok:
        return Decision(False, f"Invalid KNOWLEDGE_CHECKPOINT before code write: {result.reason}")

    transparency = project_root / framework_root / "knowledge" / "active" / "AGENT_TRANSPARENCY.md"
    if not transparency.exists():
        return Decision(False, f"Missing {transparency.relative_to(project_root)} apply evidence before code write: {target_path}")
    apply_result = gates.validate_apply_gate(transparency.read_text(encoding="utf-8"))
    if not apply_result.ok:
        return Decision(False, f"{apply_result.reason} before code write: {target_path}")
    return Decision(True)
```

(`gates` is the module already loaded earlier in `evaluate_write` via `_load_gate_check`; reuse it — do not load it again.)

- [ ] **Step 5: Run the full hook suite to verify pass + no regressions**

Run: `/usr/bin/python3 -m pytest .amap/hooks/write-gate/tests/test_write_gate.py -v`
Expected: ALL pass — the 4 new apply-gate tests, the 2 updated allow-tests, and every other pre-existing test (parser, git-ignore, Bash branch, block-without-checkpoint, framework-exempt).

- [ ] **Step 6: Commit**

```bash
git add .amap/hooks/write-gate/write_gate.py .amap/hooks/write-gate/tests/test_write_gate.py
git commit -m "feat(write-gate): require apply evidence (Pha 2 DONE + no open blocker) before code write"
```

---

### Task 3: Update R-Flow-2 doc to reflect hook enforcement

**Files:**
- Modify: `.amap/rules/rules-flow.md`

- [ ] **Step 1: Update the Apply-entry bullet**

In `.amap/rules/rules-flow.md`, find the R-Flow-2 Apply-entry bullet ending with:

```
  "Scope rõ nên bỏ spec" KHÔNG hợp lệ — spec artifact là bắt buộc, không phải phán đoán agent.
```

Add this sentence immediately after it (same bullet):

```
  Apply-entry này được enforce cơ học bởi write-gate hook (apply-gate): code-write vào app-code bị chặn nếu AGENT_TRANSPARENCY.md thiếu `Pha 2 DONE` hoặc còn `[BLOCKER-ARCH]` chưa resolve — workflow-agnostic, áp cả khi gọi thẳng `/opsx:apply`.
```

- [ ] **Step 2: Sanity check the file still reads coherently**

Run: `/usr/bin/grep -n "apply-gate\|Apply-entry" .amap/rules/rules-flow.md`
Expected: shows the new sentence under the Apply-entry bullet.

- [ ] **Step 3: Commit**

```bash
git add .amap/rules/rules-flow.md
git commit -m "docs(rules): note R-Flow-2 apply-entry is now hook-enforced (apply-gate)"
```

---

### Task 4: Full verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full affected suite**

Run: `/usr/bin/python3 -m pytest .amap/hooks .amap/tools cli/tests -q`
Expected: all PASS.

- [ ] **Step 2: Manual smoke — checkpoint present but spec phase NOT done → blocked**

```bash
rm -rf /tmp/amap_ag_smoke && mkdir -p /tmp/amap_ag_smoke/.amap/knowledge/active && cd /tmp/amap_ag_smoke
printf '## DNA\nSP-6\n## Codebase\nnode_id: x#1\nblast-radius: 2 nodes\n' > .amap/knowledge/active/KNOWLEDGE_CHECKPOINT.md
printf 'Pha 1 DONE\n' > .amap/knowledge/active/AGENT_TRANSPARENCY.md
echo '{"tool_name":"Bash","tool_input":{"command":"echo x > src/App.java"}}' \
  | /usr/bin/python3 /home/zane/Desktop/agent-memory-arch-v3/.amap/hooks/write-gate/write_gate.py --framework-root .amap --runtime claude; echo "exit=$?"
```
Expected: stderr mentions `Pha 2 DONE`, `exit=2`.

- [ ] **Step 3: Manual smoke — spec phase done → allowed**

```bash
printf 'Pha 1 DONE\nPha 2 DONE\n' > /tmp/amap_ag_smoke/.amap/knowledge/active/AGENT_TRANSPARENCY.md
cd /tmp/amap_ag_smoke
echo '{"tool_name":"Bash","tool_input":{"command":"echo x > src/App.java"}}' \
  | /usr/bin/python3 /home/zane/Desktop/agent-memory-arch-v3/.amap/hooks/write-gate/write_gate.py --framework-root .amap --runtime claude; echo "exit=$?"
```
Expected: `exit=0`.

---

## Self-Review

**Spec coverage:**
- §3.1 `validate_apply_gate` → Task 1 (validator + unit tests).
- §3.2 CLI `apply-gate` subcommand → Task 1 (VALIDATORS + CLI test).
- §3.3 wire into `evaluate_write` (shared by Edit/Write + Bash) → Task 2.
- §4 strictness (app-code requires Pha 2 DONE; framework exempt) → covered by `evaluate_write`'s existing `_is_framework_artifact` early-return (unchanged) + Task 2 tests (`test_allows_app_write...` for exempt paths remain green).
- §5 file list → Tasks 1–3 touch exactly those files.
- §6 acceptance criteria → Task 1 unit tests + Task 2 integration tests + Task 4 smokes (incl. the exit-condition: checkpoint-valid-but-no-Pha2 → blocked at the hook).
- R-Flow-2 doc accuracy → Task 3.
- Residual (R-Apply-1 confirm, spec-validator) → intentionally not implemented (spec §2, §7).

**Placeholder scan:** No TBD/TODO. The "match how the file imports" notes in Task 1 are concrete instructions (follow the existing alias) with working fallbacks given, not undefined work.

**Type/name consistency:** `validate_apply_gate(text) -> Result` defined in Task 1, called as `gates.validate_apply_gate(...)` in Task 2 and `cli.main(["apply-gate", ...])` via the `"apply-gate": "validate_apply_gate"` VALIDATORS entry. `Result(ok, reason)`, `Decision(ok, reason)`, `_is_framework_artifact`, `_load_gate_check`, `evaluate_write` names match the existing code. The `Pha\s*2\s*DONE` regex matches the marker format written by `task.md` and validated by `validate_phase_chain`.
