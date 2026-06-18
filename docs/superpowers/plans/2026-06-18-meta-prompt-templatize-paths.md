# Templatize meta-prompt.md Framework Paths Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace every literal `.amap/` path in `.amap/meta-prompt.md` with `{{ platform.framework_root }}` (and merge the duplicated directory-tree branch in §0), so `amap init` renders correct framework paths for every platform — fixing the failing leakage test and adding leakage coverage for Codex and Claude Code.

**Architecture:** `.amap/meta-prompt.md` is the meta-prompt template; its body is rendered verbatim by `amap init`, so literal `.amap/` leaks into every non-Generic platform's entry point. The fix is pure content: restructure the §0 directory tree into a single nested root, then globally replace remaining literal `.amap/` with the Jinja variable. The existing `test_antigravity_..._do_not_reference_active_amap_paths` test scans rendered output for `.amap/`; we add Codex and Claude Code twins so all three non-Generic roots are guarded.

**Tech Stack:** Markdown template, Jinja2 (`{{ platform.framework_root }}`), pytest. Test runner: `/usr/bin/python3 -m pytest` (the repo `.venv` has no pytest).

---

## Background facts (verified)

- `.amap/meta-prompt.md` is the **only** framework file still using literal `.amap/`: 32 occurrences across 29 lines (`grep -o '\.amap/' .amap/meta-prompt.md | wc -l` → 32). All 44 other framework files already use `{{ platform.framework_root }}`.
- No occurrence of `.amap` *without* a trailing slash exists (`grep -n '\.amap\b' .amap/meta-prompt.md | grep -v '\.amap/'` → empty), so a `.amap/` → variable replacement cannot accidentally hit the framework name "AMAP".
- Platform prompt order in `amap init` is `[antigravity, claude-code, generic, codex]`, so single-select answers are: antigravity=`"1"`, claude-code=`"2"`, generic=`"3"`, codex=`"4"`.
- The currently-failing test is `cli/tests/test_init.py::test_antigravity_rendered_framework_files_do_not_reference_active_amap_paths`.

---

## File Structure

Modify:
- `.amap/meta-prompt.md` — restructure §0 tree + replace all literal `.amap/`.
- `cli/tests/test_init.py` — add two leakage tests (Codex, Claude Code).

Do not modify:
- The stale skill/workflow/tool lists inside `.amap/meta-prompt.md` (missing `spec-validator`, `opsx-*`, `rule-projector`, etc.) — out of scope, separate task.
- Any other file.

---

## Task 1: Add failing leakage tests for Codex and Claude Code

**Files:**
- Test: `cli/tests/test_init.py`

- [ ] **Step 1: Add the two new tests**

Insert these two functions in `cli/tests/test_init.py` immediately **after** the existing `test_antigravity_rendered_framework_files_do_not_reference_active_amap_paths` function (which ends with `assert offenders == []` around line 138):

```python
def test_codex_rendered_framework_files_do_not_reference_active_amap_paths(
    tmp_path, amap_root, monkeypatch,
):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["4", "1,2,3", "3", "y"])

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


def test_claude_code_rendered_framework_files_do_not_reference_active_amap_paths(
    tmp_path, amap_root, monkeypatch,
):
    target = tmp_path / "proj"
    _answers(monkeypatch, ["2", "1,2,3", "3", "y"])

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

- [ ] **Step 2: Run the three leakage tests to confirm they fail (RED)**

Run:
```bash
/usr/bin/python3 -m pytest cli/tests/test_init.py -k "do_not_reference_active_amap_paths" -v
```
Expected: 3 FAILED (antigravity already failing; codex and claude_code now also fail). Each failure shows the rendered entry point (`AGENTS.md` / `CLAUDE.md`) in the `offenders` list, because the meta-prompt still emits literal `.amap/`.

- [ ] **Step 3: Commit the failing tests**

```bash
git add cli/tests/test_init.py
git commit -m "test(init): expect no .amap/ leakage for codex and claude-code"
```

---

## Task 2: Templatize paths and merge the duplicated tree branch

**Files:**
- Modify: `.amap/meta-prompt.md`

- [ ] **Step 1: Restructure the §0 directory tree**

In `.amap/meta-prompt.md`, replace the entire `txt` fenced block in section `## 0. Cây thư mục & ý nghĩa` — the block that begins with `project-root/` and ends at the closing fence right before `## 1. Bootstrap Protocol` (current lines 15–94) — with this block. This merges the two former top-level branches (`.amap/knowledge/` and `.amap/`) into one nested root and switches the path to the Jinja variable:

````txt
```txt
project-root/
│
├── {{ platform.config_entry_point }}      ← Meta-prompt chính (file này) — đọc đầu tiên
│
└── {{ platform.framework_root }}/         ← Toàn bộ framework + bộ nhớ (memory hierarchy + agent infra)
    ├── knowledge/                          ← Memory Hierarchy (bộ nhớ phân tầng)
    │   ├── active/                          ← Working memory — context cho task đang xử lý
    │   │   ├── REQUIREMENT.md               ← Yêu cầu chuẩn hoá (ghi bởi requirement-analyst)
    │   │   ├── EXPLORE_CONTEXT.md           ← Bối cảnh DB + code (ghi bởi db/codebase-explorer)
    │   │   ├── AGENT_TRANSPARENCY.md        ← Observability log (mọi skill đều ghi)
    │   │   ├── TOKEN_LOG.md                 ← Token usage tracking theo pha (ghi bởi mọi pha)
    │   │   └── ideation/                    ← Ý tưởng thô chưa thành ticket
    │   │       └── ideation-*.md
    │   ├── long-term/                       ← Long-term memory — judgment sống + bản đồ kiến trúc (source-of-truth)
    │   │   ├── knowledge-snapshot.md        ← Snapshot kiến trúc toàn hệ thống (tích luỹ qua mỗi task)
    │   │   ├── conventions.yaml             ← Convention codebase (approved, P3 context)
    │   │   ├── author-dna.yaml              ← Coding philosophy tác giả (approved, P3 judgment layer)
    │   │   ├── author-dna.draft.yaml        ← DNA đang review (KHÔNG load vào context)
    │   │   ├── persona.yaml                 ← Phong cách tương tác (local, gitignored)
    │   │   └── persona.template.yaml        ← Template persona (committed)
    │   ├── archive/                         ← Episodic memory — context task đã hoàn thành (theo ticket-id)
    │   │   └── {ticket-id}/
    │   │       ├── REQUIREMENT.md
    │   │       ├── EXPLORE_CONTEXT.md
    │   │       └── AGENT_TRANSPARENCY.md
    │   └── templates/                       ← Skeleton tĩnh để clone khi bootstrap (CHỈ template, không chứa knowledge sống)
    │       ├── REQUIREMENT.tpl.md
    │       ├── EXPLORE_CONTEXT.tpl.md
    │       ├── AGENT_TRANSPARENCY.tpl.md
    │       ├── TOKEN_LOG.tpl.md
    │       ├── ARCHIVE_META.tpl.md
    │       ├── feature.tpl.md
    │       ├── fixbug.tpl.md
    │       ├── changerequest.tpl.md
    │       ├── refactor.tpl.md
    │       └── ideation.tpl.md
    ├── rules/
    │   ├── RULES.md                         ← Rules manifest + index (entry point)
    │   ├── rules-flow.md                    ← Flow, Spec/Apply & Bootstrap rules
    │   ├── rules-tool.md                    ← MCP & tool permissions
    │   ├── rules-exec.md                    ← Data, Architecture, Cost & Observability
    │   ├── rules-knowledge.md               ← Knowledge Lifecycle, Path & Convention rules
    │   └── rules-guard.md                   ← Pre-invoke Guards, R-DNA-7, R-KI-1
    ├── skills/                              ← Reusable skill modules
    │   ├── requirement-analyst/
    │   │   └── SKILL.md
    │   ├── spec-extract/
    │   │   └── SKILL.md
    │   ├── db-explorer/
    │   │   └── SKILL.md
    │   ├── codebase-explorer/
    │   │   └── SKILL.md
    │   ├── architecture-reviewer/
    │   │   └── SKILL.md
    │   ├── knowledge-curator/               ← Quản lý vòng đời knowledge
    │   │   └── SKILL.md
    │   ├── convention-intelligence-builder/
    │   │   └── SKILL.md                     ← Convention Scanner — extract naming + architecture patterns
    │   └── author-dna-builder/
    │       └── SKILL.md                     ← Infer coding philosophy + interview → author-dna.yaml
    ├── workflows/                           ← Orchestration logic
    │   ├── task.md                          ← Workflow chính (3 pha)
    │   ├── idea-to-task.md                  ← Ideation → Draft ticket
    │   └── index-source.md                  ← Lập chỉ mục Socraticode
    ├── procedures/                          ← Bootstrap & context procedures
    │   ├── bootstrap.md                     ← Procedure tự động nhận diện & nạp context
    │   ├── context-loader.md                ← Logic định vị file theo priority
    │   ├── context-compressor.md            ← Nén context khi vượt budget
    │   └── token-tracking.md                ← Protocol tracking token usage theo pha
    ├── tools/                               ← Công cụ hỗ trợ (SP1+SP2)
    │   ├── skill-lint/                      ← Skill schema validator (SP2)
    │   │   ├── validate_skills.py
    │   │   └── tests/
    │   └── README.md
    ├── resolved-config.yaml                 ← Pre-resolved platform + MCP config (generated by amap init)
    └── profiles/                            ← Execution mode config
        └── execution-mode.yaml
```
````

(Note: the child entries are preserved exactly as today — the stale skill/workflow/tool lists are intentionally NOT updated here. Only the nesting and the path prefix change. Comment-column alignment need not be pixel-perfect.)

- [ ] **Step 2: Globally replace the remaining literal `.amap/`**

After Step 1 the §0 tree no longer contains `.amap/`; the remaining occurrences are all path references in prose/code blocks (Bootstrap steps, Context Loader, Flow, Archive, Persona). Replace them all in one pass:

```bash
sed -i 's|\.amap/|{{ platform.framework_root }}/|g' .amap/meta-prompt.md
```

- [ ] **Step 3: Verify zero literal `.amap/` remain**

```bash
/usr/bin/python3 -c "print(open('.amap/meta-prompt.md').read().count('.amap/'))"
```
Expected: `0`.

- [ ] **Step 4: Run the three leakage tests (now GREEN)**

```bash
/usr/bin/python3 -m pytest cli/tests/test_init.py -k "do_not_reference_active_amap_paths" -v
```
Expected: 3 PASSED (antigravity, codex, claude_code).

- [ ] **Step 5: Run the full CLI suite**

```bash
/usr/bin/python3 -m pytest cli/tests/ -q
```
Expected: 100% pass, **0 failures** (the previously known failure is now fixed; no remaining known-failures).

- [ ] **Step 6: Manually verify the rendered directory tree (test cannot check this)**

The leakage test only scans for the `.amap/` string — it does not verify the tree is structurally correct. Render the entry point for one non-Generic platform and eyeball §0:

```bash
/usr/bin/python3 - <<'PY'
import tempfile, pathlib, builtins
from cli.commands.init import run_init
d = tempfile.mkdtemp(prefix="amap-treecheck-")
it = iter(["4", "1,2,3", "3", "y"])  # codex
builtins.input = lambda *a, **k: next(it)
run_init(target_dir=d, amap_root=str(pathlib.Path.cwd()))
text = (pathlib.Path(d) / "AGENTS.md").read_text(encoding="utf-8")
start = text.index("project-root/")
end = text.index("## 1.", start)
print(text[start:end])
PY
```
Confirm by eye: exactly one top-level `.agents/` branch (rendered from `{{ platform.framework_root }}/`), with `knowledge/`, `rules/`, `skills/`, `workflows/`, `procedures/`, `tools/`, `resolved-config.yaml`, `profiles/` nested under it; no second duplicate top-level branch; box-drawing/indentation reads cleanly; no `{{ ` left.

- [ ] **Step 7: Confirm clean diff and commit**

```bash
git diff --check
git add .amap/meta-prompt.md
git commit -m "fix(meta-prompt): templatize framework paths, merge duplicated tree branch"
```
Expected: `git diff --check` prints nothing.
