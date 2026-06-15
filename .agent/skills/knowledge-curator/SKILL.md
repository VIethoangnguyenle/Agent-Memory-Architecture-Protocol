---
name: knowledge-curator
description: Quản lý vòng đời knowledge — archive context hoàn thành, reset active/, cập nhật knowledge-snapshot sau mỗi task.
---

# Knowledge Curator — Quản lý Vòng đời Knowledge

## 1. Mục tiêu

- **Archive** context đã hoàn thành vào `.knowledge-layer/archive/{ticket-id}/` sau khi task xong.
- **Reset** `.knowledge-layer/active/` về template skeleton sạch sẵn sàng cho task mới.
- **Cập nhật** `.knowledge-layer/templates/knowledge-snapshot.md` với phát hiện mới từ task vừa hoàn thành.
- **Rotate** archive khi quá nhiều (giữ N tickets gần nhất, nén/log các ticket cũ hơn).

Skill này là **lifecycle manager** — không sinh requirement, không review kiến trúc.

---

## 2. Khi nào dùng

Kích hoạt `knowledge-curator` khi:

- `/task apply` hoàn thành thành công → archive task đã xong.
- User yêu cầu "đóng task" hoặc "reset context" trực tiếp.
- Bootstrap phát hiện conflict giữa active context và task mới → user chọn reset.
- Định kỳ: khi `archive/` có hơn 20 tickets → rotate.

---

## 3. Các hàm chính

### 3.1 `archive_active_context(ticket_id, status="completed")`

```
INPUT:  ticket_id (string) — ID của ticket
        status    (enum)   — một trong: completed | stashed | cancelled

PRE-CHECK (theo R-Guard-1):
  1. Đọc `phase_state` trong AGENT_TRANSPARENCY.md (block `## Phase State`)
  2. Nếu phase_state ∉ {completed, cancelled} và status=completed:
     → WARN: "phase_state chưa là `completed` — xác nhận apply đã xong chưa?"
  3. Nếu phase_state = `blocked-by-arch` | `blocked-by-data`:
     → ABORT: "Task đang bị BLOCK — không thể archive cho đến khi block được resolve"
   4. Kiểm tra `.knowledge-layer/active/TOKEN_LOG.md` tồn tại và có nội dung (không chỉ template):
      → Nếu KHÔNG tồn tại hoặc chỉ là skeleton:
         WARN: "TOKEN_LOG.md chưa được ghi. Tạo retroactively (estimate từ AGENT_TRANSPARENCY) trước khi archive."
         Ghi cảnh báo vào AGENT_TRANSPARENCY: "[TOKEN-LOG-MISSING] TOKEN_LOG không tồn tại lúc archive."
         Tiếp tục archive (không ABORT) — nhưng ARCHIVE_META ghi `token_total_estimate: unknown`.
OUTPUT: archive/{ticket_id}/ được tạo với đầy đủ file

Status meanings:
  completed  ← Đã apply xong, task kết thúc. knowledge-curator sẽ chạy update_knowledge_snapshot.
  stashed    ← Tạm dừng (hot-swap hoặc chen task), có thể resume. KHÔNG update snapshot.
  cancelled  ← Bỏ giữa chừng, không tiếp tục. KHÔNG update snapshot.

STEPS:
1. Tạo thư mục: .knowledge-layer/archive/{ticket_id}/
2. Copy:
   - .knowledge-layer/active/REQUIREMENT.md      → archive/{ticket_id}/REQUIREMENT.md
   - .knowledge-layer/active/EXPLORE_CONTEXT.md  → archive/{ticket_id}/EXPLORE_CONTEXT.md
   - .knowledge-layer/active/AGENT_TRANSPARENCY.md → archive/{ticket_id}/AGENT_TRANSPARENCY.md
   - .knowledge-layer/active/TOKEN_LOG.md        → archive/{ticket_id}/TOKEN_LOG.md (nếu có)
   - .knowledge-layer/active/ideation/           → archive/{ticket_id}/ideation/ (nếu có)
3. Tạo archive/{ticket_id}/ARCHIVE_META.md:
   - ticket_id: {ticket_id}
   - archived_at: <timestamp>
   - status: {status}
   - summary: <1-2 câu tóm tắt task đã làm gì>
   - phase_at_archive: <đọc từ `phase_state` trong AGENT_TRANSPARENCY.md>
   - stash_note: <chỉ khi status=stashed: lý do stash và ticket hot-swap là gì>
   - token_total_estimate: <tổng token từ TOKEN_LOG.md nếu có, "unknown" nếu không có>
4. Verify: đọc lại các file đã copy, đảm bảo không corrupt
5. IF status == "completed":
   → tiếp tục chạy update_knowledge_snapshot(discoveries)
   ELSE:
   → bỏ qua update_knowledge_snapshot (context chưa hoàn chỉnh)
6. REPORT: "Archived ticket {ticket_id} [{status}] to .knowledge-layer/archive/{ticket_id}/"
```

### 3.2 `reset_active_context()`

```
INPUT:  none
OUTPUT: .knowledge-layer/active/ được reset về template skeleton

STEPS:
1. Đọc template từ:
   - .knowledge-layer/templates/REQUIREMENT.tpl.md (nếu có) → copy → active/REQUIREMENT.md
   - .knowledge-layer/templates/EXPLORE_CONTEXT.tpl.md → copy → active/EXPLORE_CONTEXT.md
   - .knowledge-layer/templates/AGENT_TRANSPARENCY.tpl.md → copy → active/AGENT_TRANSPARENCY.md
2. Nếu template .tpl.md không tồn tại:
   → Tạo file trống với skeleton tối thiểu (chỉ có header section)
3. Xoá toàn bộ file trong active/ideation/ (trừ .gitkeep nếu có)
4. Reset TOKEN_LOG.md:
   → Xoá (hoặc rename sang TOKEN_LOG.{timestamp}.bak nếu muốn giữ)
   → Tạo file mới từ template TOKEN_LOG.tpl.md (trống, chờ task mới điền)
5. REPORT: "Active context reset. Ready for new task."
```

### 3.3 `update_knowledge_snapshot(discoveries)`

```
INPUT:  discoveries — list các phát hiện từ task vừa hoàn thành
        (trích từ EXPLORE_CONTEXT.md và AGENT_TRANSPARENCY.md)
OUTPUT: .knowledge-layer/templates/knowledge-snapshot.md được cập nhật

STEPS:
1. Đọc EXPLORE_CONTEXT.md + AGENT_TRANSPARENCY.md của task vừa xong
2. Với mỗi discovery: chạy qua Promotion Criteria (xem Bảng Phân loại bên dưới)
3. Nếu được promote → thêm vào đúng section trong snapshot với đủ 4 field metadata:
   source:{ticket-id} seen:{YYYY-MM} verified:{YYYY-MM} status:active
4. Nếu có entry cũ cùng tên/khái niệm trong snapshot:
   - Nếu discovery mới đồng thuận → chỉ cập nhật verified:{date}
   - Nếu discovery mới mâu thuẫn → đánh dấu entry cũ là status:superseded,
     thêm entry mới và ghi rõ “Supersedes entry cũ (ticket {cũ})”
   - Nếu không chắc → đánh dấu cũ là status:outdated, cần verify thủ công
5. Thêm entry vào “Lịch sử cập nhật”: ticket, ngày, số entry thêm/updated

WARN: Nếu knowledge-snapshot.md trống (mới tạo repo):
  → Tạo cấu trúc ban đầu từ template knowledge-snapshot.md
```

#### Bảng Phân loại Promotion Criteria

Mỗi discovery rơi vào đúng một trong các bucket:

| Bucket | Điều kiện | Hành động |
|--------|-----------|----------|
| **PROMOTE → snapshot** | Đủ tất cả: (1) có evidence trực tiếp từ DB/code (không suy luận), (2) khả năng tái sử dụng ở task khác cao, (3) không mang context riêng của một ticket duy nhất, (4) không thuộc phạm vi conventions.yaml hoặc author-dna.yaml (xem bảng phân vùng bên dưới) | Thêm vào đúng section, gắn đủ metadata |
| **REDIRECT → conventions** | Nội dung là **quy tắc** đặt tên, coding style, design pattern boundary, cấu trúc thư mục | Không ghi vào snapshot. Đề xuất cập nhật vào `conventions.yaml` (hoặc `conventions.draft.yaml` nếu chưa approve) |
| **REDIRECT → author-dna** | Nội dung là **triết lý** lập trình, lý do chọn pattern, coding philosophy, judgment principle | Không ghi vào snapshot. Đề xuất cập nhật vào `author-dna.yaml` (hoặc `author-dna.draft.yaml`) |
| **ARCHIVE only** | Một trong: (1) đặc thù cho ticket này (ví dụ: workaround tạm thời), (2) còn đang tranh luận / chưa xác nhận, (3) chỉ liên quan một business case hẹp | Lưu trong archive/{ticket-id}/EXPLORE_CONTEXT.md, không lên snapshot |
| **DISCARD** | Một trong: (1) suy luận thuần túy không có evidence, (2) đã có entry tốt hơn trong snapshot rồi, (3) PII hoặc secret | Không ghi vào đâu cả |

**Bảng phân vùng kiến thức (điều kiện 4):**

| Loại nội dung | Thuộc store nào | Ví dụ |
|--------------|----------------|-------|
| **Sự thật** — hệ thống có gì, cái gì gọi cái gì | `knowledge-snapshot` ✅ | "Bảng X có column Y", "Module A gọi Module B" |
| **Quy tắc** — viết code thế nào, đặt tên ra sao | `conventions.yaml` | "Table prefix phải là OMNI_", "Factory không chứa business logic" |
| **Triết lý** — tại sao chọn cách này | `author-dna.yaml` | "HP-1: Chain of Responsibility vì need-driven" |
| **Bài học** — team đã gặp gì, giải quyết ra sao | `agent-memory` | "Bug race condition → fix bằng DB-first read" |

**Quy tắc mức trừu tượng khi REDIRECT:**

- `conventions.yaml` và `author-dna.yaml` phải viết **generic** — mô tả quy tắc/triết lý ở mức pattern, không gắn vào tên bảng/class/ticket cụ thể.
- Tên cụ thể (vd: `OMNI_DAILY_TRANS_REQ_LIMIT`) chỉ xuất hiện trong `evidence` (minh chứng), không phải trong `description` (mô tả quy tắc).
- Nếu quy tắc chỉ đúng cho 1 bảng/1 class cụ thể → đó là **sự thật**, thuộc snapshot, không phải convention.

**Ví dụ áp dụng:**

| Phát hiện | Bucket | Lý do |
|-----------|--------|-------|
| Bảng `OMNI_DAILY_TRANS_REQ_LIMIT` có column `AMOUNT`, `COMPANY_ID` | PROMOTE | DB schema thực tế, tái sử dụng cao |
| `ValidateTransactionLimitProcessor` chưa check bảng `OMNI_DAILY_TRANS_REQ_LIMIT` | PROMOTE | Code gap có evidence, relevant cho nhiều task |
| "Table prefix phải dùng `OMNI_` cho bảng project-native" | REDIRECT → conventions | Đây là **quy tắc**, không phải sự thật. Thuộc conventions.yaml |
| "Dùng Chain of Responsibility vì need-driven, không ép buộc" | REDIRECT → author-dna | Đây là **triết lý**, không phải sự thật. Thuộc author-dna.yaml |
| "Chiến lược cần thêm cột X" (chưa confirm) | ARCHIVE | Còn đang propose, chưa xác nhận |
| Kafka topic tên `omni.transaction.created` (suy luận từ naming convention) | ARCHIVE | Chưa có evidence trực tiếp |
| Sample data 5 dòng từ bảng user | DISCARD | PII potential, không có giá trị kiến trúc |
| Logic validate giống hệt entry cũ đã có trong snapshot | DISCARD | Dư thừa |

#### Quy trình xử lý Entry Cũ Stale

Mỗi lần chạy `update_knowledge_snapshot`, ngoài việc thêm mới, còn kiểm tra:

```
FOR EACH entry trong snapshot có status:active:
  IF verified < (today - 90 days):
    IF task hiện tại “đụng” vào entry này (mention trong EXPLORE_CONTEXT):
      → cập nhật verified:{today} (confirm còn đúng)
    ELSE:
      → GIỮ NGuyÊN, không tự chuyển sang outdated
         (chỉ agent có evidence mới mới được thay đổi status)
```

**Lý do**: Không tự đánh dấu `outdated` chỉ vì lâu không verify. `verified` cũ không có nghĩa là sai — chỉ có evidence mâu thuẫn mới thực sự làm entry stale.

### 3.4 `restore_from_archive(ticket_id)`

```
INPUT:  ticket_id — ticket muốn restore
OUTPUT: .knowledge-layer/active/ được điền lại từ archive

STEPS:
1. Kiểm tra archive/{ticket_id}/ tồn tại
   → Nếu không: ERROR "Không tìm thấy archive cho ticket {ticket_id}"
2. Kiểm tra active/ có context đang active không:
   → Nếu có: WARN và hỏi user có muốn archive trước không
3. Copy từ archive/{ticket_id}/:
   - REQUIREMENT.md → active/REQUIREMENT.md
   - EXPLORE_CONTEXT.md → active/EXPLORE_CONTEXT.md
   - AGENT_TRANSPARENCY.md → active/AGENT_TRANSPARENCY.md
   - ideation/ → active/ideation/ (nếu có)
4. Thêm note vào AGENT_TRANSPARENCY.md:
   "Restored from archive at <timestamp> — Tiếp tục task {ticket_id}"
5. REPORT: "Context restored for ticket {ticket_id}. Ready to continue."
```

### 3.5 `rotate_archive(keep_n=20)`

```
INPUT:  keep_n — số lượng tickets archive muốn giữ lại (default: 20)
OUTPUT: archive cũ được nén/log, giữ lại N tickets gần nhất

STEPS:
1. LIST tất cả thư mục trong .knowledge-layer/archive/ → sort by date DESC
2. Nếu count > keep_n:
   tickets_to_rotate = list[keep_n:]
   FOR EACH ticket in tickets_to_rotate:
     a. Đọc ARCHIVE_META.md → lấy summary
     b. Append vào .knowledge-layer/archive/ARCHIVE_LOG.md:
        - ticket_id, archived_at, status, summary
     c. XOÁ thư mục archive/{ticket_id}/
3. REPORT: "Rotated {n} old tickets to ARCHIVE_LOG.md. Keeping {keep_n} most recent."
```

---

## 4. Workflow tích hợp

```
/task apply <ticket> hoàn thành
    ↓
knowledge-curator.archive_active_context(ticket_id)
    ↓
knowledge-curator.update_knowledge_snapshot(discoveries)
    ↓
knowledge-curator.push_to_agent_memory(ticket_id)    ← NEW: Agent Memory hook
    ↓
knowledge-curator.reset_active_context()
    ↓
Agent sẵn sàng nhận task mới
```

---

## 8. [M7] Hook đẩy Agent Memory sau task

### Trigger

Gọi SAU `update_knowledge_snapshot` và TRƯỚC `reset_active_context`.
Chỉ khi `status == "completed"` (không push cho stashed/cancelled).

### 3 tầng lọc chất lượng

Trước khi gọi `memory_save`, curator PHẢI đi qua 3 tầng:

#### Tầng 1 — Gate (CÓ nên lưu không?)

| Câu hỏi | Nếu KHÔNG → hành động |
|---------|----------------------|
| Kiến thức đã verified bằng evidence (code merged, test pass, production ok)? | ❌ **KHÔNG LƯU** — chỉ là suy đoán |
| Có value cho task tương lai không? Có khả năng tái sử dụng? | ❌ **KHÔNG LƯU** — chỉ đúng cho task này |
| Có PII, credential, hoặc sensitive data không? | ❌ **KHÔNG LƯU** — vi phạm R-Data-1 |

Nếu cả 3 điều kiện đều đạt → tiếp sang Tầng 2.
Nếu bất kỳ điều kiện nào KHÔNG đạt → bỏ qua memory push, ghi vào AGENT_TRANSPARENCY: `[M7-SKIP] Lý do: {reason}`

#### Tầng 2 — Dedup (đã có record cùng topic chưa?)

```
CALL: memory_smart_search(topic_summary, project_id=<project>, limit=3)

NẾU kết quả trả về có record cùng topic (similarity cao):
  → Đây là CẬP NHẬT, không phải thêm mới
  → Dùng ticket_id của record CŨ để upsert đè lên
  → Ghi rõ trong content: "Thay thế {old_ticket_id}: {lý do cập nhật}"

NẾU không có record tương tự:
  → Tiếp tục với ticket_id hiện tại
```

> Lưu ý: Bước search này KHÔNG tính vào memory budget Pha 3 (nó là một phần của curator hook, không phải reasoning).

#### Tầng 3 — Quota

- Tối đa **1 `memory_save` call** per task (R-Exec-3).
- Nếu task có nhiều bài học → chọn **1 cái quan trọng nhất**, tổng hợp các cái khác vào `content`.

### Gọi `memory_save` (native — không cần mapping)

```
memory_save(
  ticket_id   = "<ticket-id>",
  project_id  = "<project identifier from REQUIREMENT.md>",
  author      = "<from persona.yaml user_info.name hoặc git config user.name>",
  kind        = "<chọn từ kind selection guide bên dưới>",
  topic       = "<1-line summary of key learning — ngắn gọn, searchable>",
  content     = "<concise knowledge distilled from task — verified facts only>",
  confidence  = "<high|medium|low>"
)
```

### Hướng dẫn chọn kind

| kind | Khi nào dùng |
|------|-------------|
| `bug_fix` | Task sửa bug — root cause + giải pháp đã xác nhận |
| `architecture_decision` | Quyết định kiến trúc/kỹ thuật quan trọng đã áp dụng |
| `pattern` | Pattern tái sử dụng đã phát hiện hoặc áp dụng |
| `convention` | Quy ước đặt tên/code mới được thiết lập |
| `gotcha` | Bẫy không rõ ràng, pitfall đã gặp và giải quyết |
| `investigation` | Kết quả nghiên cứu **đã xác nhận** (không phải suy đoán) |
| `requirement` | Nhận thức nghiệp vụ quan trọng đã xác thực |
| `deployment` | Bài học vận hành/deploy đã xác nhận |
| `other` | Bất kỳ kiến thức nào đáng nhớ không thuộc các loại trên |

### Tính lũy đẳng (Idempotency)

- `ticket_id` sinh UUID5 xác định → Qdrant point ID.
- Gọi `memory_save` 2 lần cùng `ticket_id` → **cập nhật**, không tạo bản trùng.
- Không cần tìm kiếm trước để kiểm tra trùng lặp.

### Triển khai theo giai đoạn (R-Tool-6)

| Giai đoạn | Hành vi |
|-----------|--------|
| Tuần 1 | **Bỏ qua push hoàn toàn** — chỉ đọc, quan sát |
| Tuần 2 | Push có xác nhận — curator tóm tắt record sẽ lưu, **hỏi user trước khi gọi `memory_save`** |
| Tuần 3+ | Push tự động — user giữ quyền từ chối theo phiên |

### Ghi AGENT_TRANSPARENCY

Sau khi push (hoặc bỏ qua), ghi vào AGENT_TRANSPARENCY.md:

```
[M7-MEMORY] Đẩy Agent Memory:
  - Hành động: <đã_đẩy | bỏ_qua | cập_nhật_bản_cũ>
  - ticket_id: <ticket-id>
  - kind: <kind>
  - topic: <topic>
  - Kiểm tra chất lượng: <ĐẠT | BỎ_QUA lý_do>
  - Kiểm tra trùng lặp: <không_trùng | thay_thế {old_ticket_id}>
```

---

## 5. Cập nhật AGENT_TRANSPARENCY

Trong `.knowledge-layer/active/AGENT_TRANSPARENCY.md`:

- Ghi lại mỗi action đã thực hiện:
  - `[x] knowledge-curator: archive_active_context({ticket_id})`
  - `[x] knowledge-curator: update_knowledge_snapshot`
  - `[x] knowledge-curator: reset_active_context`
- Ghi lại nếu có lỗi trong quá trình archive (và đã xử lý thế nào).

---

## 6. [M6] TOKEN_LOG Calibration

### Mục tiêu

Cải thiện độ chính xác của TOKEN_LOG.md theo thời gian bằng cách so sánh estimate với actual usage (nếu biết).

### Calibration Workflow

```
FUNCTION calibrate_token_estimates(ticket_id):
  INPUT: ticket_id — ticket vừa hoàn thành

  1. Đọc archive/{ticket_id}/TOKEN_LOG.md:
     - Lấy các estimate: Pha 1, Pha 2, Pha 3, TỔNG

  2. Nếu model API trả về actual token count (vd: Claude usage metadata):
     - So sánh: estimate vs actual cho từng pha
     - Tính ratio: actual / estimate

  3. Cập nhật calibration note vào .knowledge-layer/templates/TOKEN_LOG.tpl.md:
     - Section "Calibration History":
       | ticket_id | pha | estimate | actual | ratio | note |
     - Ghi average ratio sau 3+ tickets

  4. Nếu average ratio > 1.5 (estimate thấp hơn actual 50%+):
     → WARN: "TOKEN estimate đang thấp hơn thực tế. Cân nhắc nhân hệ số 1.5x."
     → Ghi vào AGENT_TRANSPARENCY: "[M6-CALIBRATE] Hệ số calibration: {ratio}x"

  5. Nếu không có actual data:
     → Bỏ qua calibration lần này, ghi note "no-actual-data"
```

### Token Estimate Guidelines (Calibrated)

Dùng khi không có actual data:

| Activity | Estimate (tokens) |
|----------|-------------------|
| Đọc REQUIREMENT.md (đầy đủ) | ~1,500–3,000 |
| Đọc EXPLORE_CONTEXT.md (đầy đủ) | ~2,000–5,000 |
| Đọc knowledge-snapshot.md (filtered) | ~1,000–4,000 |
| 1 KG tool call (query + result) | ~500–1,500 |
| 1 UA call | ~2,000–5,000 |
| Ghi REQUIREMENT.md | ~1,000–2,000 |
| Ghi EXPLORE_CONTEXT.md | ~1,500–3,000 |
| Sinh spec (openspec-propose) | ~3,000–8,000 |
| 1 file apply (small) | ~500–2,000 |
| 1 file apply (medium/large) | ~2,000–8,000 |

**Quy tắc estimate tổng**:
- Cộng tất cả activities trong pha.
- Thêm 20% overhead cho system prompt + tool call boilerplate.
- Nếu calibration ratio > 1.0: nhân thêm ratio đó.

### Cập nhật TOKEN_LOG trong Archive

Khi `archive_active_context()` chạy:
- Copy TOKEN_LOG.md vào archive (đã có trong STEPS).
- Sau khi calibrate (nếu có actual data): cập nhật bản archive với actual numbers.
- Ghi `calibration_status: done | no-data | pending` vào ARCHIVE_META.md.

---

## 7. [M3] Violation Pattern Tracking

### Mục đích

Tích lũy pattern vi phạm rule/workflow qua các task để nhận diện vấn đề hệ thống (không phải lỗi ngẫu nhiên).

### `track_violation_patterns(ticket_id)`

```
INPUT: ticket_id — ticket vừa archive

STEPS:
1. Đọc archive/{ticket_id}/AGENT_TRANSPARENCY.md
   → Tìm tất cả entry có format:
     - "[VIOLATION]", "[RULE-VIOLATION]", "[WORKFLOW-VIOLATION]"
     - Rule ID bị vi phạm (vd: R-Flow-3, R-Apply-1)
     - Mô tả pattern hành vi

2. Với mỗi violation tìm thấy:
   a. Đọc violation_pattern từ description (normalize về dạng slug)
      Ví dụ: "skip confirm step" → pattern_id = "skip-confirm-step"
   b. Kiểm tra .knowledge-layer/templates/knowledge-snapshot.md
      section "[M3] Violation Pattern Tracking":
      - Nếu pattern_id đã tồn tại:
        → Tăng "Lần xảy ra" += 1
        → Cập nhật "Task gần nhất" = ticket_id
      - Nếu pattern_id chưa tồn tại VÀ đây là lần xảy ra ≥ 2:
        → Thêm row mới vào bảng vi phạm

3. Cập nhật "Violation Trend" section:
   - Tổng số patterns
   - Pattern phổ biến nhất (max "Lần xảy ra")

4. Nếu bất kỳ pattern có "Lần xảy ra" ≥ 5:
   → WARN vào AGENT_TRANSPARENCY:
     "[M3-ALERT] Pattern '{pattern_id}' đã xảy ra {n} lần.
      Cân nhắc bổ sung rule mới vào RULES.md để ngăn lặp lại."

5. Ghi vào ARCHIVE_META.md:
   violations_tracked: {n_violations_found}
   new_patterns_added: {n_new}
```

### Tích hợp vào archive_active_context

Gọi `track_violation_patterns` như một bước trong `archive_active_context`:

```
archive_active_context(ticket_id):
  ... (các steps hiện tại) ...
  IF status == "completed":
    → update_knowledge_snapshot(discoveries)
    → track_violation_patterns(ticket_id)   ← M3: thêm bước này
  → reset_active_context()
```

### Bảo mật / Privacy

- Không lưu tên user, IP, hay thông tin định danh.
- Chỉ lưu pattern hành vi (what happened, not who did it).
- Violation data dùng để cải thiện rules, không để blame.
