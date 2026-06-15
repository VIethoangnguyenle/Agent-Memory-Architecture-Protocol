# context-loader.md — Logic Định vị & Nạp File Theo Priority

> Sub-module của bootstrap. Có thể gọi độc lập khi agent cần re-scan context giữa chừng.

---

## Mục tiêu

Xác định và nạp đúng file context phù hợp với task hiện tại, theo thứ tự ưu tiên đã định nghĩa.
Tránh tình trạng agent dùng context cũ của task khác.

---

## Context Priority Matrix

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PRIORITY  │ PATH                                      │ Điều kiện nạp   │
├───────────┼───────────────────────────────────────────┼─────────────────┤
│ P1 (cao)  │ .knowledge-layer/active/REQUIREMENT.md          │ Có nội dung thực│
│ P1        │ .knowledge-layer/active/EXPLORE_CONTEXT.md      │ Có nội dung thực│
│ P1        │ .knowledge-layer/active/AGENT_TRANSPARENCY.md   │ Luôn nạp nếu có │
│ P1        │ .knowledge-layer/active/TOKEN_LOG.md             │ Luôn nạp nếu có │
│ P2        │ .knowledge-layer/active/ideation/ideation-*.md  │ Tất cả file .md │
│ P3 (tĩnh) │ .knowledge-layer/templates/knowledge-snapshot.md│ Luôn nạp nếu có │
│ P3 (tĩnh) │ .knowledge-layer/templates/conventions.yaml     │ Chỉ khi status=approved│
│ P3 (tĩnh) │ .knowledge-layer/templates/author-dna.yaml      │ Chỉ khi status=approved│
│ P4 (thấp) │ .knowledge-layer/archive/{ticket-id}/           │ Chỉ khi P1 trống│
└─────────────────────────────────────────────────────────────────────────┘
```


**conventions.yaml — quy tắc nạp:**
- `status: approved` → nạp cùng knowledge-snapshot, cùng lượt P3.
- `status: draft` → KHÔNG nạp — chưa được approve.
- Không tồn tại → WARN "conventions.yaml chưa có. Agent dùng generic naming. Chạy /convention-scan để tạo."
- conventions.yaml được dùng bởi: `codebase-explorer`, `architecture-reviewer`, `spec-engineer` khi sinh tên class/method.

**Selective loading — tied vào R-Guard-2 artifact type:**

Khi bootstrap nạp conventions.yaml, chỉ load full nếu Pha 3 (`/task apply`) hoặc Pha 2 (`/task spec`).
Với Pha 1 (exploration): chỉ cần Section 1 (naming) + Section 4 (upstream constraints).

**Exception — khi `architecture-reviewer` được gọi trong Pha 1**:
Load đầy đủ cả hai file trước khi chạy skill:
- `conventions.yaml` → toàn bộ (bao gồm `design_patterns`, upstream constraints)
- `author-dna.yaml` → toàn bộ `hard_principles` + `complexity_thresholds`
  (pattern_preferences vẫn `on_demand` — arch-reviewer không cần level đó)

Trigger: khi skill registry detect `architecture-reviewer` sắp được gọi → pre-load đầy đủ.
Không cần artifact name — architecture-reviewer tự xác định boundary từ toàn bộ conventions + DNA HP.

Khi R-Guard-2 detect artifact type (trước khi sinh code), load thêm section tương ứng:

```
ARTIFACT_SECTION_MAP = {
  "Factory"    : ["Factory Design Boundary", "upstream_constraints"],
  "Handler"    : ["Handler naming", "upstream_constraints"],
  "Service"    : ["Service naming", "upstream_constraints"],
  "Repository" : ["Repository naming", "upstream_constraints"],
  "Processor"  : ["Processor naming"],
  "Executor"   : ["Executor naming", "upstream_constraints"],
  "Entity"     : ["Entity naming", "upstream_constraints"],
  "*"          : ["Section 1 naming rules"]  # default — mọi artifact
}
```

Agent đọc sections trong map, không cần load toàn bộ 754 dòng.
Nếu section không tìm thấy trong conventions.yaml → load toàn bộ file (safe fallback).

**author-dna.yaml — quy tắc nạp:**
- `status: approved` → nạp cùng conventions.yaml, cùng lượt P3.
- `status: draft` → KHÔNG nạp — chưa qua interview/approve.
- Không tồn tại → WARN "author-dna.yaml chưa có. Agent dùng generic judgment. Chạy /dna-scan để tạo."
- author-dna.yaml được dùng bởi: `architecture-reviewer` (hard principles), `spec-engineer` (pattern preferences), `/task apply` (style + complexity thresholds).

> **[R-KI-1 — Bắt buộc]**: Nếu external KI (Antigravity, Cursor rules, etc.) chứa
> file `factory-rules.md`, `coding-rules.md`, hoặc bất kỳ file nào duplicate nội dung
> từ `conventions.yaml` / `author-dna.yaml`:
>
> **Agent PHẢI** (không phải "khuyến nghị"):
> 1. Trong phiên detect: WARN user ngay trong bootstrap report (PHASE 0.5).
> 2. Đề xuất action cụ thể: "Replace nội dung `{ki_file}` bằng 1 dòng pointer:
>    `# Xem .knowledge-layer/templates/conventions.yaml + author-dna.yaml`"
> 3. Ghi vào AGENT_TRANSPARENCY: "[R-KI-1] KI conflict detected: {path}. Cleanup pending."
> 4. Nếu user chưa cleanup sau 2 phiên: nhắc lại mỗi bootstrap cho đến khi xử lý.
>
> **Không được** dùng nội dung từ KI file để code nếu nội dung đó mâu thuẫn với `.knowledge-layer/`.
> Lý do: incident 2026-06-08 — KI `factory-rules.md` không có DNA judgment layer → agent sinh code sai pattern.

---

## Thuật toán định vị theo Task Type

### Khi nhận `/task <input>`:

```
1. Xác định task_type từ input:
   - Chứa ticket key (ABC-123, PROJ-456) hoặc URL ticket → HAS_TICKET
   - Chứa URL wiki/Confluence/PRD nhưng không có ticket → HAS_DOC_ONLY
   - Còn lại → IDEA_ONLY

2. Xác định context cần nạp theo task_type:
   ┌────────────────┬─────────────────────────────────────────────────────┐
   │ Task Type      │ Context cần nạp                                     │
   ├────────────────┼─────────────────────────────────────────────────────┤
   │ IDEA_ONLY      │ knowledge-snapshot (nếu có) + active ideations      │
   │ HAS_DOC_ONLY   │ knowledge-snapshot + active REQUIREMENT (nếu có)    │
   │ HAS_TICKET     │ TẤT CẢ: REQUIREMENT + EXPLORE_CONTEXT + snapshot    │
   └────────────────┴─────────────────────────────────────────────────────┘

3. Nạp context theo priority, ghi status vào AGENT_TRANSPARENCY
```

### Khi nhận `/task spec <ticket-id>`:

```
REQUIRED:
  → .knowledge-layer/active/REQUIREMENT.md      (PHẢI có, nếu không: ABORT pha 2)
  → .knowledge-layer/active/EXPLORE_CONTEXT.md  (PHẢI có, nếu không: WARN, hạ tin cậy)

OPTIONAL:
  → .knowledge-layer/templates/knowledge-snapshot.md
  → .knowledge-layer/archive/{ticket-id}/       (nếu active context khác ticket)
```

### Khi nhận `/task apply <ticket-id>`:

```
REQUIRED:
  → Spec file tương ứng ticket (trong thư mục spec/ hoặc được ghi trong AGENT_TRANSPARENCY)
  → .knowledge-layer/active/REQUIREMENT.md

VERIFICATION:
  → architecture-reviewer không đánh dấu BLOCKER
  → User đã confirm rõ ràng
```

---

## Định vị File Theo Ticket ID

Khi có ticket-id cụ thể, context-loader tìm kiếm theo thứ tự:

```
1. .knowledge-layer/active/REQUIREMENT.md
   → Kiểm tra metadata section có ticket_id khớp không
   → Nếu khớp: nạp và dùng
   → Nếu không khớp: cảnh báo "Active context thuộc ticket khác"

2. .knowledge-layer/archive/{ticket-id}/REQUIREMENT.md
   → Nếu tìm thấy: hỏi user có muốn restore không
   → Nếu restore: copy archive/{ticket-id}/* → active/

3. Không tìm thấy ở đâu:
   → Thông báo: "Chưa có context cho ticket này. Chạy /task <ticket-id> để tạo mới."
```

---

## Re-scan Context (giữa chừng task)

Agent có thể gọi context-loader tại bất kỳ điểm nào trong workflow khi:
- Skill A đã ghi xong file → skill B cần đọc file đó
- User yêu cầu "đọc lại context"
- Agent phát hiện file có thể đã thay đổi

```
FUNCTION rescan_active_context():
  RE-READ: .knowledge-layer/active/REQUIREMENT.md
  RE-READ: .knowledge-layer/active/EXPLORE_CONTEXT.md
  RE-READ: .knowledge-layer/active/AGENT_TRANSPARENCY.md
  UPDATE: in-memory context state
  REPORT: "Context refreshed. Changes detected: [list nếu có]"
```

---

## Graceful Degradation Rules

| File thiếu | Hành động |
|-----------|-----------|
| REQUIREMENT.md trống | Tiếp tục nhưng WARN, hạ độ tin cậy |
| EXPLORE_CONTEXT.md trống | Tiếp tục, mark "Chưa explore" trong TRANSPARENCY |
| knowledge-snapshot.md thiếu | WARN "Kiến trúc tổng thể chưa có snapshot. Kết luận kiến trúc có độ tin cậy THẤP hơn." |
| archive/ trống | Bình thường, không cần warn |
| Toàn bộ active/ trống | Bootstrap sạch, không có context cũ |

---

## Output Format

Sau khi chạy context-loader, agent phải có thể trả lời:

```
CONTEXT_SUMMARY = {
  "active_task": "<ticket-id hoặc null>",
  "requirement_status": "loaded | empty | template-only",
  "explore_context_status": "loaded | empty",
  "knowledge_snapshot": "available | missing",
  "active_ideations": ["ideation-sdk-bill-payment.md", ...],
  "archive_count": 3,
  "warnings": ["knowledge-snapshot missing", ...]
}
```

---

## Policy: Các Case Đặc biệt (Concern 2)

Design giả định "1 task tại 1 thời điểm". Ba case sau cần protocol rõ để không phụ thuộc vào hội thoại:

---

### Case A: Task Nóng (Hot-swap)

Xảy ra khi: User đang làm PROJ-123 (pha 1 hoặc 2) nhưng đột nhiên cần xử lý gấp PROJ-456.

```
DETECT: active task = PROJ-123, user request = PROJ-456

PROMPT:
  "ð¥ Task nóng: PROJ-456 trong khi PROJ-123 đang ở [pha hiện tại].

   Chọn cách xử lý:
   [H] Hoàn tất nhanh PROJ-123 trước (nếu có thể)
   [S] Stash PROJ-123 → xử lý PROJ-456 → resume sau
   [A] Bỏ PROJ-123 luôn, archive và bắt đầu PROJ-456"

IF [S] (Stash):
  1. knowledge-curator.archive_active_context("PROJ-123", status="stashed")
     → ARCHIVE_META.md phải ghi status=stashed (khác với completed)
  2. reset_active_context()
  3. Bắt đầu PROJ-456 trên context sạch
  4. Ghi vào AGENT_TRANSPARENCY của PROJ-456:
     "Hot-swap từ PROJ-123 (stashed tại archive/PROJ-123/)"

IF [H] (Hoàn tất nhanh):
  → Giữ context, tiếp tục PROJ-123 đến điểm dừng an toàn rồi stash

Resume stash sau:
  context-loader.restore_from_archive("PROJ-123")
  → Ghi note: "Resumed from stash"
```

**Stash status trong ARCHIVE_META.md:**

```
status: stashed          ← chưa hoàn thành, có thể resume
status: completed        ← đã apply xong
status: cancelled        ← bỏ giữa chừng, không resume
```

---

### Case B: So sánh với Ticket Cũ

Xảy ra khi: User muốn xem lại context của PROJ-100 (archived) trong khi PROJ-200 đang active.

```
DETECT: user request = "đọc lại context PROJ-100"

PROMPT:
  "Đọc bảng so sánh hay restore toàn bộ?
   [R] Read-only: hiển thị REQUIREMENT + EXPLORE_CONTEXT của PROJ-100 (đang active = PROJ-200)
   [F] Full restore: dừng PROJ-200, load PROJ-100 vào active/"

IF [R] (Read-only — khuyến nghị):
  1. Đọc file từ archive/PROJ-100/ nhưng KHÔNG copy vào active/
  2. Hiển thị inline trong trả lời của agent
  3. Ghi vào AGENT_TRANSPARENCY (PROJ-200):
     "Read-only access archive/PROJ-100/ cho mục đích so sánh"
  4. Active context của PROJ-200 không bị ảnh hưởng

IF [F] (Full restore):
  → Chạy Stash PROJ-200 trước, rồi restore_from_archive(PROJ-100)
```

**Rule cứng**: Không bao giờ đồng thời có 2 task `active` trong `active/`. Read-only từ archive là cach duy nhất để xem ticket cũ mà không phá vỡ task đang chạy.

---

### Case C: Đổi task giữa Pha 2 và Pha 3

Xảy ra khi: Đã chạy `/task spec PROJ-123` xong (Pha 2), nhưng trước khi apply, user muốn quay lại chỉnh REQUIREMENT.

```
DETECT: active task = PROJ-123, pha hiện tại = spec-done (chưa apply)
        user request = sửa lại REQUIREMENT

PROMPT:
  "â ï¸ Spec của PROJ-123 đã được sinh (Pha 2). Sửa REQUIREMENT sẽ invalidate spec hiện tại.

   [P] Patch nhỏ: Chỉ sửa REQUIREMENT, sinh lại spec từ đầu (Pha 2)
   [K] Giữ nguyên spec, chỉ ghi note và sửa sau apply
   [A] Abort spec hiện tại, quay về Pha 1 toàn bộ"

IF [P] (Patch):
  1. Ghi vào AGENT_TRANSPARENCY: "Spec invalidated do thay đổi REQUIREMENT tại [timestamp]"
  2. Đánh dấu spec file hiện tại là DRAFT-INVALIDATED (rename hoặc thêm marker)
  3. Cập nhật REQUIREMENT.md
  4. Chạy lại `/task spec PROJ-123`

IF [K] (Giữ spec):
  1. Ghi note vào REQUIREMENT.md: "[PENDING CHANGE] mô tả thay đổi"
  2. Ghi vào AGENT_TRANSPARENCY: "Spec và REQUIREMENT có delta chưa được sync"
  3. Tiếp tục apply, xử lý delta sau
```

**Rule cứng**: Khi Pha 2 đã xong mà REQUIREMENT thay đổi, **phải ghi rõ** vào AGENT_TRANSPARENCY rằng spec và requirement có thể lệch. Không được để tình trạng này “am thầm”.

---

## [M2] Knowledge-Snapshot Domain Keyword Filtering

Khi knowledge-snapshot.md quá lớn (> 8K tokens), không nạp toàn bộ — chỉ load sections liên quan đến domain của task hiện tại.

```
FUNCTION load_snapshot_filtered(requirement_md):
  1. Trích domain keywords từ REQUIREMENT.md:
     - Đọc section "Bối cảnh" + "Phạm vi" + "Acceptance Criteria"
     - Tách ra: entity names, table names, service names, business terms
     - Ví dụ: ["DAILY_TRANS", "limit", "ValidateProcessor", "bill-payment"]

  2. Đọc knowledge-snapshot.md theo section:
     - Với mỗi section (## header): kiểm tra xem header hoặc 5 dòng đầu có chứa bất kỳ keyword nào không
     - Nếu match: nạp toàn bộ section đó
     - Nếu không match: bỏ qua (chỉ giữ section header để biết cấu trúc)

  3. Luôn nạp:
     - Section "Tổng quan Hệ thống" (bất kể keyword)
     - Section "Quy ước Metadata Bắt buộc"

  4. Ghi vào AGENT_TRANSPARENCY:
     "[M2-FILTER] knowledge-snapshot: loaded {n}/{total} sections.
      Keywords: {keyword_list}. Sections loaded: {section_names}."

  5. Nếu tổng sau filter vẫn > 8K tokens:
     → Chuyển sang context-compressor Mode A cho snapshot
```

**Khi nào áp dụng**:
- knowledge-snapshot.md tồn tại VÀ size > 8,000 tokens estimate.
- Áp dụng với cả lượt nạp ban đầu (bootstrap) và re-scan giữa chừng.

**Fallback**:
- Nếu không trích được keyword từ REQUIREMENT (file trống/skeleton):
  → Nạp toàn bộ snapshot (không filter) + WARN "Thiếu keywords từ REQUIREMENT, nạp snapshot đầy đủ".

---

## [C1] Tích hợp Context Compressor

context-loader tích hợp với `.agent/scripts/context-compressor.md` tại 2 điểm:

### Điểm 1 — Sau khi tính tổng token

Ngay sau khi nạp tất cả file context (cuối thuật toán định vị), tính tổng token estimate:

```
AFTER loading all context files:
  file_estimates = {file: estimate_tokens(content) for file, content in loaded}
  total_estimate = sum(file_estimates.values())

  FOR file, tokens IN file_estimates.items():
    IF tokens > 8000:
      → context-compressor.compress_file_mode_a(file)  ← Mode A

  IF total_estimate > 50000:
    → context-compressor.compress_context_mode_b()     ← Mode B

  Ghi tổng vào TOKEN_LOG.md section "Bootstrap":
    "Context loaded: ~{total_estimate}K tokens từ {n} files"
```

### Điểm 2 — Bootstrap PHASE 2.5 (Resume detection)

Trong `bootstrap.md` PHASE 2.5, sau khi xác định phiên bị truncate:

```
IF phase_state != "bootstrapped" AND session_is_new:
  → context-compressor.compress_context_mode_c()      ← Mode C
  → Không chạy full context-loader (chỉ minimal context từ Mode C)
  → Dừng bootstrap tại đây, chờ user ra lệnh tiếp theo
```
