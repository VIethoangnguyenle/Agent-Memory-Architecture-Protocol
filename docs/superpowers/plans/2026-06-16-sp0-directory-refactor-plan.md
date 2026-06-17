# SP0 — Directory Tree Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tái cấu trúc cây thư mục AMAP — tách tri thức sống khỏi template tĩnh, xoá thư mục trùng lặp, chuẩn hoá naming, reserve nhà cho component tương lai — mà không đổi logic skill/workflow/rule.

**Architecture:** Refactor thuần file (di chuyển/đổi tên/xoá + cập nhật path string). Mọi thay đổi là cơ học và verify được bằng `grep` gate. Dùng `git mv` để giữ history. "Test" của plan này = các grep gate (0 path cũ sót lại), không phải unit test.

**Tech Stack:** git, bash (`git mv`, `grep`, `sed`, `find`). Không có code runtime.

---

## Quy ước chung cho mọi find/replace

- Phạm vi: toàn repo, chỉ `*.md` và `*.yaml`, **loại trừ** `.git/`, `docs/specs/`, `docs/plans/`.
  (Hai thư mục docs/specs + docs/plans cố ý ghi cả path cũ lẫn mới để tài liệu hoá migration —
  KHÔNG được sed vào chúng.)
- Mẫu lệnh chuẩn dùng lại nhiều lần:

```bash
# Tìm file chứa pattern (để review trước khi sửa)
grep -rln "PATTERN" --include="*.md" --include="*.yaml" . | grep -vE '\.git/|docs/(specs|plans)/'

# Thay thế an toàn trên đúng tập file đó
grep -rln "PATTERN" --include="*.md" --include="*.yaml" . | grep -vE '\.git/|docs/(specs|plans)/' \
  | xargs sed -i 's|OLD|NEW|g'
```

- Sau mỗi task có gate grep phải trả **0 dòng** trước khi commit.

---

## Deferred (KHÔNG làm ở SP0)

- **docs/ generation** (sinh `docs/skills` + `docs/workflows` từ SKILL.md) → chuyển sang **SP2**.
  SP0 chỉ sửa path chết bên trong `docs/skills/06-knowledge-curator.md` và `08-author-dna-builder.md`
  (Task 1), không xoá docs, không viết generator.
- Top-level rename `.agent/` / `.knowledge-layer/` → không bao giờ (xem spec §4).

---

## Task 1: Migrate live-knowledge files → `long-term/` + cập nhật mọi reference

**Files:**
- Create dir: `.knowledge-layer/long-term/`
- Move: `.knowledge-layer/templates/{author-dna.yaml, author-dna.draft.yaml, conventions.yaml, knowledge-snapshot.md, persona.yaml, persona.template.yaml}` → `.knowledge-layer/long-term/`
- Modify (path refs): `.agent/rules/{rules-flow,rules-guard,rules-knowledge}.md`, `.agent/scripts/{bootstrap,context-loader}.md`, `.agent/skills/**/SKILL.md` (+ references), `.agent/workflows/{task,approve-conventions}.md`, `AGENTS.md`, `README.md`, `.knowledge-layer/README.md`, `docs/skills/{06-knowledge-curator,08-author-dna-builder}.md`

- [ ] **Step 1: Tạo thư mục đích**

```bash
mkdir -p .knowledge-layer/long-term
```

- [ ] **Step 2: Di chuyển file tri thức sống bằng `git mv` (giữ history)**

```bash
cd .knowledge-layer/templates
for f in author-dna.yaml author-dna.draft.yaml conventions.yaml knowledge-snapshot.md persona.yaml persona.template.yaml; do
  [ -f "$f" ] && git mv "$f" ../long-term/"$f"
done
cd -
```

- [ ] **Step 3: Verify move — file ở long-term/, không còn ở templates/**

Run:
```bash
ls .knowledge-layer/long-term/
grep -rl "" .knowledge-layer/templates/ 2>/dev/null | grep -E 'author-dna|conventions|knowledge-snapshot|persona' || echo "CLEAN: no live-knowledge left in templates/"
```
Expected: `long-term/` liệt kê 6 file; dòng cuối in `CLEAN`.

- [ ] **Step 4: Cập nhật canonical path trong RULES.md §12 (R-Path-1) TRƯỚC**

Mở `.agent/rules/RULES.md`, tìm section 12 / R-Path-1. Đổi mọi đường dẫn:
`.knowledge-layer/templates/author-dna.yaml` → `.knowledge-layer/long-term/author-dna.yaml`
(và tương tự cho `conventions.yaml`, `knowledge-snapshot.md`, `persona*.yaml`).
Dùng Edit tool cho từng dòng để chắc chắn đúng ngữ cảnh canonical.

- [ ] **Step 5: Find/replace toàn repo cho 4 nhóm path**

```bash
for name in author-dna conventions knowledge-snapshot persona; do
  grep -rln "knowledge-layer/templates/$name" --include="*.md" --include="*.yaml" . \
    | grep -vE '\.git/|docs/(specs|plans)/' \
    | xargs --no-run-if-empty sed -i "s|knowledge-layer/templates/$name|knowledge-layer/long-term/$name|g"
done
```

- [ ] **Step 6: Gate — 0 path cũ sót lại**

Run:
```bash
grep -rln "knowledge-layer/templates/\(author-dna\|conventions\|knowledge-snapshot\|persona\)" \
  --include="*.md" --include="*.yaml" . | grep -vE '\.git/|docs/(specs|plans)/' \
  && echo "FAIL: còn path cũ" || echo "PASS: 0 path cũ"
```
Expected: `PASS: 0 path cũ`

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor(sp0): tách tri thức sống sang .knowledge-layer/long-term/

author-dna, conventions, knowledge-snapshot, persona là source-of-truth sống —
tách khỏi templates/ (skeleton tĩnh). Cập nhật ~24 reference + canonical RULES.md §12.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Chuẩn hoá naming template → `.tpl.md`

**Files:**
- Rename: `.knowledge-layer/templates/{feature,fixbug,changerequest,refactor,ideation}.md` → `*.tpl.md`
- Modify (path refs): bất kỳ file nào trỏ tới các template trên (thường `.agent/workflows/task.md`, `AGENTS.md`, README)

- [ ] **Step 1: Rename bằng `git mv`**

```bash
cd .knowledge-layer/templates
for f in feature fixbug changerequest refactor ideation; do
  [ -f "$f.md" ] && git mv "$f.md" "$f.tpl.md"
done
cd -
```

- [ ] **Step 2: Verify rename**

Run:
```bash
ls .knowledge-layer/templates/ | grep -E '^(feature|fixbug|changerequest|refactor|ideation)'
```
Expected: tất cả hiển thị dạng `*.tpl.md`, không còn `*.md` trần.

- [ ] **Step 3: Cập nhật reference**

```bash
for f in feature fixbug changerequest refactor ideation; do
  grep -rln "templates/$f\.md" --include="*.md" --include="*.yaml" . \
    | grep -vE '\.git/|docs/(specs|plans)/' \
    | xargs --no-run-if-empty sed -i "s|templates/$f\.md|templates/$f.tpl.md|g"
done
```

- [ ] **Step 4: Gate — 0 reference cũ**

Run:
```bash
grep -rln "templates/\(feature\|fixbug\|changerequest\|refactor\|ideation\)\.md" \
  --include="*.md" --include="*.yaml" . | grep -vE '\.git/|docs/(specs|plans)/' \
  && echo "FAIL" || echo "PASS: 0 reference cũ"
```
Expected: `PASS: 0 reference cũ`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor(sp0): chuẩn hoá naming template task-type sang .tpl.md

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Rename `.agent/scripts/` → `.agent/procedures/`

**Files:**
- Rename dir: `.agent/scripts/` → `.agent/procedures/` (4 file: bootstrap, context-loader, context-compressor, token-tracking)
- Modify (path refs): `.agent/workflows/task.md`, `.agent/procedures/context-loader.md`, `AGENTS.md`, `.knowledge-layer/README.md`

- [ ] **Step 1: Rename dir bằng `git mv`**

```bash
git mv .agent/scripts .agent/procedures
```

- [ ] **Step 2: Verify**

Run:
```bash
ls .agent/procedures/ && test ! -d .agent/scripts && echo "PASS: scripts/ gone"
```
Expected: 4 file md liệt kê; `PASS: scripts/ gone`.

- [ ] **Step 3: Cập nhật reference `agent/scripts/` → `agent/procedures/`**

```bash
grep -rln "agent/scripts/" --include="*.md" --include="*.yaml" . \
  | grep -vE '\.git/|docs/(specs|plans)/' \
  | xargs --no-run-if-empty sed -i 's|agent/scripts/|agent/procedures/|g'
```

- [ ] **Step 4: Gate — 0 reference cũ**

Run:
```bash
grep -rln "agent/scripts/" --include="*.md" --include="*.yaml" . \
  | grep -vE '\.git/|docs/(specs|plans)/' && echo "FAIL" || echo "PASS: 0 ref agent/scripts"
```
Expected: `PASS: 0 ref agent/scripts`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor(sp0): rename .agent/scripts -> .agent/procedures (chứa md-procedure, không phải executable)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Xoá thư mục shortcut trùng/rỗng

**Files:**
- Delete: `/templates/`, `/workflows/`, `.agent/templates/`

- [ ] **Step 1: Xác nhận chúng chỉ chứa README (an toàn để xoá)**

Run:
```bash
find templates workflows .agent/templates -type f 2>/dev/null
```
Expected: chỉ thấy 3 file `README.md` (không có nội dung độc nhất nào khác).

- [ ] **Step 2: Xoá bằng `git rm`**

```bash
git rm -r templates workflows .agent/templates
```

- [ ] **Step 3: Gate — thư mục không còn**

Run:
```bash
for d in templates workflows .agent/templates; do test ! -e "$d" && echo "OK gone: $d" || echo "FAIL: $d still exists"; done
```
Expected: 3 dòng `OK gone`.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor(sp0): xoá thư mục shortcut trùng lặp (/templates, /workflows, .agent/templates)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Di chuyển design sketch → `docs/sketches/`

**Files:**
- Create dir: `docs/sketches/`
- Move: `.knowledge-layer/templates/multi-agent-escalation-sketch.md` → `docs/sketches/multi-agent-escalation-sketch.md`

- [ ] **Step 1: Tạo dir + git mv**

```bash
mkdir -p docs/sketches
git mv .knowledge-layer/templates/multi-agent-escalation-sketch.md docs/sketches/multi-agent-escalation-sketch.md
```

- [ ] **Step 2: Cập nhật reference (nếu có file nào trỏ tới)**

```bash
grep -rln "templates/multi-agent-escalation-sketch" --include="*.md" --include="*.yaml" . \
  | grep -vE '\.git/|docs/(specs|plans)/' \
  | xargs --no-run-if-empty sed -i 's|.knowledge-layer/templates/multi-agent-escalation-sketch|docs/sketches/multi-agent-escalation-sketch|g'
```

- [ ] **Step 3: Gate**

Run:
```bash
test -f docs/sketches/multi-agent-escalation-sketch.md \
  && ! test -f .knowledge-layer/templates/multi-agent-escalation-sketch.md \
  && echo "PASS" || echo "FAIL"
```
Expected: `PASS`

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor(sp0): chuyển multi-agent-escalation-sketch sang docs/sketches/

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Reserve nhà cho component tương lai

**Files:**
- Create: `.agent/tools/README.md`, `.agent/adapters/README.md`, `.agent/profiles/README.md`

- [ ] **Step 1: Tạo 3 thư mục + README placeholder**

```bash
mkdir -p .agent/tools .agent/adapters .agent/profiles
printf '# tools/\n\nExecutable tooling — populated by SP1 (rule-projector, git hooks).\n' > .agent/tools/README.md
printf '# adapters/\n\nTool-capability adapters (propose_spec, explore_code, query_graph) — populated by SP3.\n' > .agent/adapters/README.md
printf '# profiles/\n\nPer-framework setup profiles (Claude, Cursor, Antigravity) — populated by SP4.\n' > .agent/profiles/README.md
```

- [ ] **Step 2: Gate**

Run:
```bash
for d in tools adapters profiles; do test -f ".agent/$d/README.md" && echo "OK: $d" || echo "FAIL: $d"; done
```
Expected: 3 dòng `OK`.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "refactor(sp0): reserve .agent/{tools,adapters,profiles} cho SP1/SP3/SP4

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Cập nhật mô tả cây thư mục trong tài liệu

**Files:**
- Modify: `AGENTS.md` (cây thư mục section 0), `README.md` (Tổng quan Kiến trúc), `.knowledge-layer/README.md`

- [ ] **Step 1: Cập nhật cây thư mục trong `AGENTS.md`**

Mở `AGENTS.md` section "0. Cây thư mục & ý nghĩa". Sửa block ASCII tree:
- `templates/` → tách thành `long-term/` (author-dna, conventions, knowledge-snapshot, persona) và `templates/` (chỉ `*.tpl.md`).
- `scripts/` → `procedures/`.
- Thêm `tools/`, `adapters/`, `profiles/` (ghi chú "reserved cho SP1/3/4").
- Xoá mô tả `.agent/templates/` và shortcut `/templates`, `/workflows`.
Dùng Edit tool.

- [ ] **Step 2: Cập nhật `README.md` block "Tổng quan Kiến trúc"** tương tự Step 1 (Edit tool).

- [ ] **Step 3: Cập nhật `.knowledge-layer/README.md`** — phản ánh `long-term/` + `templates/` chỉ skeleton.

- [ ] **Step 4: Gate — không còn mô tả path cũ trong tài liệu**

Run:
```bash
grep -rn "scripts/\|templates/author-dna\|templates/conventions\|templates/knowledge-snapshot\|templates/persona" \
  AGENTS.md README.md .knowledge-layer/README.md && echo "FAIL: còn mô tả cũ" || echo "PASS"
```
Expected: `PASS`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "docs(sp0): cập nhật mô tả cây thư mục theo cấu trúc mới

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Final verification gate (toàn bộ §9 của spec)

**Files:** không sửa — chỉ verify.

- [ ] **Step 1: Chạy toàn bộ gate**

Run:
```bash
echo "=== 1. live-knowledge paths ==="; grep -rln "knowledge-layer/templates/\(author-dna\|conventions\|knowledge-snapshot\|persona\)" --include="*.md" --include="*.yaml" . | grep -vE '\.git/|docs/(specs|plans)/' && echo "FAIL 1" || echo "PASS 1"
echo "=== 2. scripts path ==="; grep -rln "agent/scripts/" --include="*.md" --include="*.yaml" . | grep -vE '\.git/|docs/(specs|plans)/' && echo "FAIL 2" || echo "PASS 2"
echo "=== 3. bare template names ==="; grep -rln "templates/\(feature\|fixbug\|changerequest\|refactor\|ideation\)\.md" --include="*.md" --include="*.yaml" . | grep -vE '\.git/|docs/(specs|plans)/' && echo "FAIL 3" || echo "PASS 3"
echo "=== 4. shortcut dirs gone ==="; for d in templates workflows .agent/templates; do test ! -e "$d" && echo "OK gone $d" || echo "FAIL $d"; done
echo "=== 5. long-term populated ==="; ls .knowledge-layer/long-term/ | wc -l
echo "=== 6. procedures populated ==="; ls .agent/procedures/ | wc -l
echo "=== 7. reserved dirs ==="; for d in tools adapters profiles; do test -f ".agent/$d/README.md" && echo "OK $d" || echo "FAIL $d"; done
```
Expected: `PASS 1/2/3`; mục 4 ba dòng `OK gone`; mục 5 ≥ 6; mục 6 = 4; mục 7 ba dòng `OK`.

- [ ] **Step 2: Verify git history liền mạch cho file đã move**

Run:
```bash
git log --follow --oneline .knowledge-layer/long-term/author-dna.yaml | head -3
git log --follow --oneline .knowledge-layer/long-term/knowledge-snapshot.md | head -3
```
Expected: thấy commit history trước SP0 (chứng tỏ `git mv` giữ được lineage).

- [ ] **Step 3: Sanity — bootstrap không trỏ path chết**

Run:
```bash
grep -n "knowledge-layer/long-term\|agent/procedures" .agent/procedures/bootstrap.md | head
```
Expected: bootstrap đã trỏ path mới (nếu nó load các file tri thức/procedure).

- [ ] **Step 4: Commit (nếu có chỉnh sót khi verify)**

```bash
git add -A && git commit -m "chore(sp0): final verification fixes" || echo "Nothing to commit — SP0 clean"
```

---

## Self-Review (đã chạy khi viết plan)

**Spec coverage:**
- Spec §6.1 (move long-term) → Task 1 ✓
- Spec §6.2 (rename templates .tpl.md) → Task 2 ✓
- Spec §6.3 (scripts→procedures) → Task 3 ✓
- Spec §6.4 (xoá shortcut dirs) → Task 4 ✓
- Spec §6.5 (move sketch) → Task 5 ✓
- Spec §6.6 (reserve homes) → Task 6 ✓
- Spec §7 (path update + RULES.md canonical) → Task 1 Step 4–6 ✓
- Spec §8 (docs generation) → **Deferred sang SP2** (ghi rõ ở mục Deferred) ✓
- Spec §9 (verification) → Task 8 ✓
- Tài liệu tree (AGENTS.md/README) → Task 7 ✓

**Placeholder scan:** Không có TBD/TODO; mọi step có lệnh thật + expected output. ✓

**Type/path consistency:** Tên thư mục (`long-term`, `procedures`, `tools/adapters/profiles`) và pattern grep nhất quán giữa các task và với spec. Loại trừ `docs/specs|plans` đồng nhất ở mọi find/replace. ✓
