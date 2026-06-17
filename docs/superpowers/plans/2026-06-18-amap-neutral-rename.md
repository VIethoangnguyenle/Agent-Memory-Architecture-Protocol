# AMAP Neutral (rename + neutrality) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename `.agent/` → `.amap/` and nest `.knowledge-layer/` → `.amap/knowledge/`, then neutralize prose that privileges one tool (Antigravity) or one architecture (CQRS/`BaseWebController`/`MessageBus`) as the default example.

**Architecture:** Three workstreams from [the spec](../specs/2026-06-18-amap-agent-neutral-design.md). **A1** = one atomic rename commit (`git mv` + a single leading-dot-anchored `sed` over operative files + CLI), gated by `grep` checks and the CLI pytest suite. **A2** = surgical prose edits in operative rule/procedure/workflow files + the Lớp-3 KI-detect exclusion fix. **A3** = surgical prose edits in two skill files. Each workstream is one commit.

**Tech Stack:** Bash (`git mv`, `grep`, `sed`), Python 3 CLI with pytest. Run pytest as `/usr/bin/python3 -m pytest` (the `.venv` python has no pytest).

**Refinement of spec §5.3 (flagged):** The spec said "grep `knowledge-layer` → 0". During planning we found bare `knowledge-layer` is also used as a *concept* name in prose (e.g. openspec skills: "knowledge-layer context/pipeline"), which are **not** filesystem paths. We rewrite only `.knowledge-layer` (with leading dot = the directory) and **retain** bare-concept mentions. Verification asserts `.knowledge-layer` (dotted) → 0, not bare `knowledge-layer`.

---

## Task 1: Setup — branch + green baseline

**Files:** none (git + test only)

- [ ] **Step 1: Confirm clean working tree**

Run: `git status --porcelain`
Expected: empty output (no uncommitted changes).

- [ ] **Step 2: Create work branch**

Run: `git switch -c amap-neutral`
Expected: `Switched to a new branch 'amap-neutral'`

- [ ] **Step 3: Capture green baseline (pre-rename)**

Run: `/usr/bin/python3 -m pytest cli/ -q`
Expected: all tests PASS. Record the count (e.g. "N passed"). If any fail *before* changes, stop and report — the rename verification depends on a green baseline.

---

## Task 2: A1 — atomic directory rename + reference rewrite

**Files:**
- Move: `.agent/` → `.amap/`
- Move: `.knowledge-layer/` → `.amap/knowledge/`
- Modify (content, via sed): all operative text files referencing `.agent` or `.knowledge-layer` (≈ `.amap/**`, `cli/**`, `AGENTS.md`, `README.md`, `install.sh`, `upgrade.md`, `.gitignore`, `docs/*.md` outside `docs/superpowers/`)
- Untouched: `docs/superpowers/**` (historical), `.venv`, `.git`, `.pytest_cache`

- [ ] **Step 1: Move the two directories with history preserved**

```bash
git mv .agent .amap
git mv .knowledge-layer .amap/knowledge
```
Expected: no error. `.amap/` now contains `rules/ skills/ workflows/ procedures/ tools/ resolved-config.yaml knowledge/`.

- [ ] **Step 2: Verify the move + history continuity**

```bash
test -d .amap && test -d .amap/knowledge && ! test -d .agent && ! test -d .knowledge-layer && echo "DIRS OK"
git log --follow --oneline -- .amap/procedures/bootstrap.md | head -3
```
Expected: prints `DIRS OK`, and `git log --follow` shows pre-rename history of bootstrap.md (proves `git mv`, not copy+delete).

- [ ] **Step 3: Rewrite path references in one sed pass**

The pattern is anchored on a **leading dot**, so it rewrites the directory paths (`.agent/…`, `.knowledge-layer/…`) and the Python quoted forms (`".agent"`, `".knowledge-layer"`) but never matches bare prose words like `agent` or the concept `knowledge-layer`.

```bash
grep -rlZ -I -e '\.agent' -e '\.knowledge-layer' . \
  --exclude-dir=.git --exclude-dir=.venv --exclude-dir=.pytest_cache --exclude-dir=superpowers \
| xargs -0 sed -i 's#\.knowledge-layer#.amap/knowledge#g; s#\.agent#.amap#g'
```
Notes:
- `--exclude-dir=superpowers` protects `docs/superpowers/` (historical specs/plans **and** this new spec/plan, which already use `.amap`).
- `.knowledge-layer` runs first; its replacement `.amap/knowledge` contains no `.agent` substring, so the second rule is order-safe.
- Python `target / ".knowledge-layer" / "active"` becomes `target / ".amap/knowledge" / "active"` — functionally identical to `".amap" / "knowledge"` (`Path / ".amap/knowledge"` resolves correctly).

- [ ] **Step 4: Verify zero remaining dotted path references (spec §5.1–5.3)**

```bash
echo "--- .agent (expect 0) ---"
grep -rn "\.agent" . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=.pytest_cache --exclude-dir=superpowers
echo "--- .knowledge-layer dotted (expect 0) ---"
grep -rn "\.knowledge-layer" . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=.pytest_cache --exclude-dir=superpowers
```
Expected: **no output** from either grep. (Bare `knowledge-layer` concept mentions may remain — that is intentional; do not "fix" them.)

- [ ] **Step 5: Sanity-check the .gitignore was rewritten**

```bash
grep -n "amap" .gitignore
```
Expected: shows `.amap/tools/rule-projector/generated/*`, the matching `!…/.gitkeep`, and `.amap/knowledge/long-term/persona.yaml`. No `.agent` or `.knowledge-layer` remain in the file.

- [ ] **Step 6: Run the CLI test suite (the real gate)**

Run: `/usr/bin/python3 -m pytest cli/ -q`
Expected: same pass count as the Task 1 baseline. If a test fails, read the assertion — it almost certainly points to a path the sed produced; fix that line and re-run. Do **not** proceed until green.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor(layout): rename .agent -> .amap, nest knowledge under .amap/knowledge

Reverses SP0 §4 on the branding/agent-independence axis. New installs
scaffold .amap/; existing-install migration deferred to U3 (amap migrate).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: A2 — neutralize Antigravity-first framing + Lớp-3 fix

All edits below operate on the **post-rename** content (path tokens are already `.amap/...`). Each is a unique, surgical replacement. Principle: lead generic; no single tool is the first/sole example. **Do not** touch platform adapters (`cli/platforms/antigravity.py`), the functional detect *paths*, or already-neutral lists.

**Files:**
- Modify: `.amap/procedures/bootstrap.md` (PHASE 0.5 intro, detect block + Lớp-3 exclusion, Lý do)
- Modify: `.amap/rules/rules-guard.md:101`
- Modify: `.amap/rules/rules-flow.md:27,31`
- Modify: `.amap/procedures/context-loader.md:77`
- Modify: `.amap/workflows/task.md:254`

- [ ] **Step 1: bootstrap.md — PHASE 0.5 intro (de-privilege ordering)**

OLD:
```
> Ngăn "false sense of completeness" khi agent runtime có hệ thống KI external (Antigravity, Cursor rules, GitHub Copilot instructions, etc.)
```
NEW:
```
> Ngăn "false sense of completeness" khi agent runtime có hệ thống KI external (vd: Cursor rules, GitHub Copilot instructions, Antigravity knowledge, v.v.)
```

- [ ] **Step 2: bootstrap.md — detect block reorder + Lớp-3 exclusion fix**

OLD (note: line already reads `.amap/knowledge/` after Task 2):
```
  - ~/.gemini/antigravity/knowledge/
  - ~/.cursor/rules/
  - .github/copilot-instructions.md
  - .cursorrules
  - Bất kỳ file nào có tên *-rules.md hoặc *-ki.md ngoài .amap/knowledge/
```
NEW (Antigravity no longer first; exclusion broadened to the whole `.amap/` namespace — the Lớp-3 fix):
```
  - ~/.cursor/rules/
  - .cursorrules
  - .github/copilot-instructions.md
  - ~/.gemini/antigravity/knowledge/
  - Bất kỳ file nào có tên *-rules.md hoặc *-ki.md ngoài .amap/
```

- [ ] **Step 3: bootstrap.md — Lý do (de-anchor from the Antigravity incident)**

OLD:
```
**Lý do**: Incident 2026-06-08 — agent dựa vào `~/.gemini/antigravity/knowledge/factory-rules.md`
(không version-controlled, không có DNA judgment layer) thay vì `.amap/knowledge/long-term/conventions.yaml`.
External KI tạo ảo giác "đã đủ context" trong khi thiếu hoàn toàn judgment layer.
```
NEW:
```
**Lý do**: Một class lỗi đã quan sát được — agent dựa vào KI external (vd một file `*-rules.md` do tool
runtime sinh ra: không version-controlled, không có DNA judgment layer) thay vì
`.amap/knowledge/long-term/conventions.yaml`. External KI tạo ảo giác "đã đủ context" trong khi thiếu
hoàn toàn judgment layer.
```

- [ ] **Step 4: rules-guard.md:101 — reorder enumeration**

OLD:
```
Khi bootstrap phát hiện external KI (Antigravity, Cursor rules, `.cursorrules`, v.v.):
```
NEW:
```
Khi bootstrap phát hiện external KI (vd: Cursor rules, `.cursorrules`, Antigravity knowledge, v.v.):
```

- [ ] **Step 5: rules-flow.md:27 — reorder runtime list**

OLD:
```
  file output convention từ Antigravity, Gemini, Claude, v.v.).
```
NEW:
```
  file output convention của agent runtime, vd Claude, Cursor, Gemini, Antigravity, v.v.).
```

- [ ] **Step 6: rules-flow.md:31 — de-sole-example**

OLD:
```
  - Agent runtime defaults (kể cả các tool như Antigravity planning) là **secondary** — chỉ dùng
```
NEW:
```
  - Agent runtime defaults (kể cả planning mode của các tool như Cursor, Antigravity, v.v.) là **secondary** — chỉ dùng
```

- [ ] **Step 7: context-loader.md:77 — reorder enumeration**

OLD:
```
> **[R-KI-1 — Bắt buộc]**: Nếu external KI (Antigravity, Cursor rules, etc.) chứa
```
NEW:
```
> **[R-KI-1 — Bắt buộc]**: Nếu external KI (vd Cursor rules, Antigravity knowledge, etc.) chứa
```

- [ ] **Step 8: task.md:254 — de-sole-example**

OLD:
```
     runtime có planning mode nằm ngoài workflow này (Antigravity, v.v.).
```
NEW:
```
     runtime có planning mode nằm ngoài workflow này (vd Cursor, Antigravity, v.v.).
```

- [ ] **Step 9: Verify framing + Lớp-3 + that support is intact**

```bash
echo "--- Lớp-3: exclusion is .amap/ not .amap/knowledge/ ---"
grep -n "ngoài .amap/" .amap/procedures/bootstrap.md
echo "--- Antigravity never leads as sole/first example (manual scan) ---"
grep -rn "Antigravity\|antigravity" .amap --include="*.md"
echo "--- support intact: adapter + detect paths still present ---"
test -f cli/platforms/antigravity.py && grep -q "antigravity/knowledge" .amap/procedures/bootstrap.md && echo "SUPPORT OK"
```
Expected: exclusion line shows `ngoài .amap/` (no `/knowledge`); every remaining `Antigravity` mention is either a functional detect path or one item in a multi-tool list (none leading/sole); prints `SUPPORT OK`.

- [ ] **Step 10: Re-run CLI tests (prose edits must not break anything)**

Run: `/usr/bin/python3 -m pytest cli/ -q`
Expected: same pass count as baseline.

- [ ] **Step 11: Commit**

```bash
git add -A
git commit -m "refactor(neutrality): de-privilege Antigravity in operative prose + fix KI-detect exclusion

A2 + Lớp-3: tool examples now lead generic; KI-detect exclusion broadened
to the whole .amap/ namespace so framework files are never flagged as external KI.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: A3 — genericize privileged architecture examples

**Files:**
- Modify: `.amap/skills/architecture-reviewer/SKILL.md:208`
- Modify: `.amap/skills/convention-intelligence-builder/references/structural-audit-scan.md:47-53`

Keep the neutral multi-pattern list (`CQRS, MVC, Hexagonal`) and the "read constraints from `conventions.yaml`" mechanism. Only remove the specific class names used as the sole example.

- [ ] **Step 1: architecture-reviewer/SKILL.md:208 — hypothetical, no class names**

OLD:
```
   - Ví dụ: Nếu `conventions.yaml` quy định API phải kế thừa `BaseWebController` và dùng `MessageBus`, phải bắt lỗi ngay nếu Requirement/Spec dự định inject trực tiếp Handler vào Controller. Không hardcode CQRS vào skill này, nhưng phải đọc và áp dụng từ file convention.
```
NEW:
```
   - Ví dụ (giả định, không phải mặc định): nếu `conventions.yaml` quy định API phải kế thừa một base class nhất định và mọi lệnh phải đi qua một message/command bus, thì phải bắt lỗi ngay khi Requirement/Spec định đi tắt (vd gọi thẳng tầng dưới, bỏ qua bus). Skill này **không** hardcode bất kỳ pattern nào (CQRS/MVC/Hexagonal…) — luôn đọc constraint từ `conventions.yaml` rồi enforce.
```

- [ ] **Step 2: structural-audit-scan.md:47-53 — genericize scanner examples**

OLD:
```
      → Khám phá cách Controller tương tác với Logic Layer: Controller gọi trực tiếp
        Handler/Service hay đi qua MessageBus / Dispatcher?
      → Controller có bắt buộc kế thừa Base class nào không (ví dụ: BaseWebController)?
    CALL: {{ tools.read_file }}(node_id)
      → Đọc actual implementation (chỉ signature, không toàn bộ body)
      → Nếu phát hiện CQRS (Controller -> MessageBus -> Command -> Handler),
        đánh dấu đây là kiến trúc cốt lõi với mức độ MANDATORY (upstream_constraints).
```
NEW:
```
      → Khám phá cách Controller tương tác với Logic Layer: Controller gọi trực tiếp
        Handler/Service hay đi qua một message bus / dispatcher?
      → Controller có bắt buộc kế thừa base class nào không (vd một base class chung do dự án quy định)?
    CALL: {{ tools.read_file }}(node_id)
      → Đọc actual implementation (chỉ signature, không toàn bộ body)
      → Nếu phát hiện một dispatch pattern bắt buộc (vd CQRS: Controller → bus → Command → Handler),
        đánh dấu đây là kiến trúc cốt lõi với mức độ MANDATORY (upstream_constraints).
```

- [ ] **Step 3: Verify the specific class names are gone (spec §5.10)**

```bash
grep -rn "BaseWebController\|MessageBus" .amap/skills
```
Expected: **no output**.

- [ ] **Step 4: Verify neutral content was preserved**

```bash
grep -rn "CQRS, MVC, Hexagonal" .amap/skills/architecture-reviewer/SKILL.md
grep -rn "conventions.yaml" .amap/skills/architecture-reviewer/SKILL.md | head -1
```
Expected: the multi-pattern list line and the "read from conventions.yaml" mechanism both still present.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor(neutrality): genericize privileged architecture examples in skills

A3: replace BaseWebController/MessageBus sole-examples with generic placeholders;
keep the multi-pattern list and the read-from-conventions.yaml mechanism.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Final verification against spec §5

**Files:** none (verification only)

- [ ] **Step 1: Run the full spec "done" checklist**

```bash
echo "1+2. .agent refs (expect 0):"
grep -rn "\.agent" . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=.pytest_cache --exclude-dir=superpowers
echo "3. .knowledge-layer dotted refs (expect 0):"
grep -rn "\.knowledge-layer" . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=.pytest_cache --exclude-dir=superpowers
echo "4. dirs:"
test -d .amap && test -d .amap/knowledge && ! test -d .agent && ! test -d .knowledge-layer && echo "DIRS OK"
echo "5. gitignore ignores persona + generated:"
git check-ignore .amap/knowledge/long-term/persona.yaml .amap/tools/rule-projector/generated/x 2>/dev/null
echo "9. Lớp-3 exclusion:"
grep -n "ngoài .amap/" .amap/procedures/bootstrap.md
echo "10. A3 class names gone (expect 0):"
grep -rn "BaseWebController\|MessageBus" .amap/skills
```
Expected: greps for `.agent`, `.knowledge-layer`, and the A3 class names print nothing; `DIRS OK`; gitignore reports the two paths; the Lớp-3 line shows `ngoài .amap/`.

- [ ] **Step 2: Full CLI test suite green (spec §5.6)**

Run: `/usr/bin/python3 -m pytest cli/ -q`
Expected: same pass count as the Task 1 baseline.

- [ ] **Step 3: History continuity (spec §5.7)**

Run: `git log --follow --oneline -- .amap/knowledge/long-term/persona.template.yaml | head -3`
Expected: shows commits predating this rename (proves `git mv` preserved history for the nested move too).

- [ ] **Step 4: Report**

Summarize: dirs moved, reference greps clean, CLI suite green (N passed), A2/A3 edits applied, Lớp-3 fixed. Note that existing-install migration (`.agent`→`.amap` in downstream projects) remains deferred to U3, and Topic B (multi-persona) is a separate spec.
```
