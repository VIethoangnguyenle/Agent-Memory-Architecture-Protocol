# bootstrap.md — Script Tự động Nhận diện & Nạp Context

> Agent thực thi script này ngay khi bắt đầu phiên. Pseudo-code có tính ràng buộc.
> Chi tiết thuật toán định vị file: xem `context-loader.md`.

---

## PHASE 0 — Pre-flight

```
CHECK AGENTS.md        → không có: ABORT "Repo chưa cấu hình Agent Memory Architecture."
CHECK .agent/rules/RULES.md → không có: WARN, tiếp tục với guardrails mặc định
READ: AGENTS.md
READ: .agent/rules/RULES.md              ← manifest + index
READ: .agent/rules/rules-flow.md         ← flow constraints
READ: .agent/rules/rules-tool.md         ← tool permissions
READ: .agent/rules/rules-exec.md         ← data/arch/cost/obs
READ: .agent/rules/rules-knowledge.md    ← knowledge lifecycle + path
READ: .agent/rules/rules-guard.md        ← pre-invoke guards (đọc SAU cùng)
```
Logou
### PHASE 0.5 — External KI Conflict Check

> Ngăn "false sense of completeness" khi agent runtime có hệ thống KI external (Antigravity, Cursor rules, GitHub Copilot instructions, etc.)

```
DETECT external KI:
  Kiểm tra sự tồn tại của bất kỳ path nào sau:
  - ~/.gemini/antigravity/knowledge/
  - ~/.cursor/rules/
  - .github/copilot-instructions.md
  - .cursorrules
  - Bất kỳ file nào có tên *-rules.md hoặc *-ki.md ngoài .knowledge-layer/

IF external KI detected:
  1. WARN bắt buộc trong bootstrap report:
     "⚠️ [R-KI-1] External KI detected: {path}
      SOURCE OF TRUTH = .knowledge-layer/ — KI chỉ được dùng làm pointer.
      Nếu KI mâu thuẫn với .knowledge-layer/: LUÔN ưu tiên .knowledge-layer/."
  2. Ghi vào AGENT_TRANSPARENCY:
     "[R-KI-1] KI conflict pending cleanup: {path}"
  3. Đề xuất action trong bootstrap report:
     "→ Action: Replace nội dung {ki_file} bằng pointer:
        `# Xem .knowledge-layer/templates/conventions.yaml + author-dna.yaml`"
  4. Nếu phát hiện KI file duplicate conventions/DNA:
     **Từ chối dùng KI file đó trong phiên này** — chỉ dùng .knowledge-layer/.

IF external KI NOT detected:
  → tiếp tục bình thường
```

**Lý do**: Incident 2026-06-08 — agent dựa vào `~/.gemini/antigravity/knowledge/factory-rules.md`
(không version-controlled, không có DNA judgment layer) thay vì `.knowledge-layer/templates/conventions.yaml`.
External KI tạo ảo giác "đã đủ context" trong khi thiếu hoàn toàn judgment layer.

**Periodic re-scan**: Ngoài bootstrap, cũng chạy scan này khi:
- `knowledge-curator` chạy `archive_active_context` (kiểm tra xem có KI mới xuất hiện).
- Phát hiện KI file có `last_modified` mới hơn lần scan cuối → WARN ngay.

---

## PHASE 1 — Skill Discovery

```
SCAN .agent/skills/*/SKILL.md
  EXTRACT: chỉ YAML frontmatter (name, description) + section "Khi nào dùng" (trigger_conditions)
  KHÔNG ĐỌC: full instruction body — defer đến khi trigger condition match
  REGISTER vào skill-registry (in-memory): {name, description, triggers}
  ON ERROR (file corrupt): SKIP + WARN
```

> **Lý do lazy-load**: Full SKILL.md = 100-475 dòng/file × 14 skills ≈ 2,000-6,000 dòng.
> Chỉ cần frontmatter + triggers (≈ 10-20 dòng/skill) để biết khi nào invoke.
> Full instructions được đọc khi skill thực sự được gọi.

---

## PHASE 2 — Workflow Discovery

```
READ .agent/workflows/task.md          → /task
READ .agent/workflows/idea-to-task.md  → /idea-to-task
READ .agent/workflows/index-source.md  → /index-source (optional)
```

---

## PHASE 2.5 — Session Resume Check (bắt buộc)

> Phát hiện khi nào phiên bị truncate và agent đang resume giữa chừng task.
> **Không được bỏ qua phase này** — đây là nguyên nhân gốc của class lỗi "agent dùng thói quen mặc định khi resume".

```
DETECT resume context:
  IF active/REQUIREMENT.md có nội dung thực (không phải skeleton)
  AND active/AGENT_TRANSPARENCY.md có entry pha nào đó đã chạy (Pha 1/2/3)
  THEN → đây là phiên RESUME (không phải task mới)

IF RESUME:
  1. BẮT BUỘC re-read .agent/workflows/task.md để nạp lại toàn bộ CRITICAL blocks
     (đặc biệt: CRITICAL block ở đầu Section 2 — OpenSpec requirement)
  2. Xác định pha hiện tại từ AGENT_TRANSPARENCY (tìm dòng "Pha X DONE" trong section "Lịch sử pha"):
     - Có `Pha 1 DONE`, chưa có `Pha 2 DONE` → đang chờ `/task spec`
       → CRITICAL: phải dùng OpenSpec. **Không re-trigger Pha 1** dù ticket ID có vẻ thiếu.
     - Có `Pha 2 DONE`, chưa có `Pha 3 DONE` → đang chờ `/task apply`
       → CRITICAL: phải xác nhận spec path là `openspec/changes/<id>/`.
     - Không có marker nào → Pha 1 chưa chạy → task mới bình thường
  3. Ghi vào bootstrap report:
     ⚠️ Resume phiên: task {ticket_id} đang ở {pha hiện tại} — đã re-read workflow constraints
  4. KHÔNG suy luận "user đã đồng ý" từ context cũ:
     - Mọi bước confirm bắt buộc trong workflow vẫn phải thực hiện lại
     - Checkpoint summary ≠ full context

IF NOT RESUME (task mới hoặc active trống):
  → tiếp tục bình thường
```

**Rule liên kết**: R-Boot-1, R-Boot-3 (RULES.md) + CRITICAL block trong task.md Section 2.

---

## PHASE 3 — Context Loader

Nạp file theo thứ tự ưu tiên. Logic đầy đủ: `context-loader.md`.

| Priority | Path | Điều kiện nạp | Nếu thiếu |
|----------|------|--------------|-----------|
| P1 | `.knowledge-layer/active/REQUIREMENT.md` | Tồn tại + không phải skeleton | status = "empty" |
| P1 | `.knowledge-layer/active/EXPLORE_CONTEXT.md` | Tồn tại + không phải skeleton | status = "empty" |
| P1 | `.knowledge-layer/active/AGENT_TRANSPARENCY.md` | Tồn tại | bỏ qua |
| P2 | `.knowledge-layer/active/ideation/ideation-*.md` | Tất cả file .md | danh sách rỗng |
| P2 | `.knowledge-layer/templates/knowledge-snapshot.md` | Luôn nạp nếu tồn tại | **BLOCK** — ghi vào bootstrap report: "⛔ knowledge-snapshot.md MISSING — độ tin cậy kiến trúc = KHÔNG XÁC ĐỊNH. Chạy `/index-source` để tạo." |
| P2 | `.knowledge-layer/templates/conventions.yaml` | status=approved | **BLOCK** — như hiện tại |
| P2 | `.knowledge-layer/templates/author-dna.yaml` | status=approved | **BLOCK** — như hiện tại |
| P4 | `.knowledge-layer/archive/` | Chỉ khi P1 trống | đọc metadata của ≤10 ticket gần nhất |

**Skeleton detection**: File là template skeleton nếu chứa `<!-- TODO: fill in -->` hoặc độ dài < 200 ký tự.

---

## PHASE 4 — Conflict Detection

```
IF REQUIREMENT.status == "active":
  PROMPT user:
    "Active context từ task: <ticket-id>
     REQUIREMENT: <tóm tắt 1 dòng> | EXPLORE_CONTEXT: <có/trống>
     [A] Tiếp tục task cũ  [B] Reset + archive tự động  [C] Xem chi tiết"

  IF [B]: knowledge-curator.archive_active_context() → reset_active_context()
  IF [A/C]: giữ nguyên context
```

---

## PHASE 5 — Bootstrap Report + Write Transparency

Xuất ra câu đầu tiên bắt buộc chứa trigger phrase từ `persona.yaml` (field: `greeting`).
Nếu `persona.yaml` không tồn tại → dùng `"Ready"`.

Format:

```
{greeting} — Em đã load xong:
✅ Core: AGENTS.md v{version} + RULES (manifest + 5 modules: flow, tool, exec, knowledge, guard)
✅ Skills ({n}): [list all discovered skill names]
✅ Workflows: /task (3 pha) | /idea-to-task | /index-source
📋 Active: REQUIREMENT={active/empty} | EXPLORE_CONTEXT={active/empty} | Ideation={n} file
🗺️ Snapshot: {loaded — n entries / MISSING ⛔}
📐 Conventions: {approved/draft/missing} {— n patterns, n upstream constraints nếu approved}
🧠 Author DNA: {approved/draft/missing} {— n confirmed entries read}
🔢 Token Log: {exists/new} {— tổng estimate nếu task đang dở}
📦 Archive: {n} ticket(s) — Latest: {ticket-id} ({date})
⚠️ {warnings nếu có}
```

> **Bắt buộc sau khi nạp**:
> - `author-dna.yaml` status=approved → agent PHẢI đọc tất cả entries `confirmed: true` trước khi nhận lệnh code.
>   Dấu hiệu đã đọc: bootstrap report ghi `🧠 Author DNA: approved — {n} confirmed entries read`.
> - `knowledge-snapshot.md` → agent PHẢI đọc sections "Kiến trúc Code" và "Business Rules Đã Xác Nhận"
>   trước khi nhận lệnh code bất kỳ liên quan đến feature/factory/service.
>   Dấu hiệu đã đọc: bootstrap report ghi `🗺️ Snapshot: loaded — {n} entries`.
>   Nếu snapshot MISSING: ghi `🗺️ Snapshot: MISSING ⛔` và hạ confidence kiến trúc = KHÔNG XÁC ĐỊNH.
> Nếu KHÔNG ghi các dòng này = R-Guard-1 sẽ block các skill downstream.

Sau đó ghi vào `.knowledge-layer/active/AGENT_TRANSPARENCY.md` — section Bootstrap:

```
- Timestamp, AGENTS.md [x], RULES.md [x], Skills loaded [list], Workflows [list]
- Context state: {requirement/explore_context/snapshot status}
- Warnings: {list}
```

---

## Error Handling

| Tình huống | Hành động |
|-----------|-----------|
| AGENTS.md không tồn tại | ABORT |
| Skill file corrupt | SKIP + WARN |
| active/ file không đọc được | WARN, treat as empty |
| archive/ > 50 tickets | Chỉ đọc metadata 10 gần nhất |
| knowledge-snapshot.md thiếu | WARN, hạ độ tin cậy kiến trúc |
