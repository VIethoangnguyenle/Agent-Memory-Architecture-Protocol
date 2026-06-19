# [M7] Hook đẩy Agent Memory sau task

> Reference file — extracted from SKILL.md for progressive disclosure.

## Trigger

Gọi SAU `update_knowledge_snapshot` và TRƯỚC `reset_active_context`.
Chỉ khi `status == "completed"` (không push cho stashed/cancelled).

## 3 tầng lọc chất lượng

Trước khi gọi `memory_save`, curator PHẢI đi qua 3 tầng:

### Tầng 0 — Pre-check (agent-memory có cấu hình không?)

Đọc `resolved-config.yaml → mcps`. Nếu KHÔNG chứa `agent-memory`:
→ Bỏ qua toàn bộ memory push, ghi vào AGENT_TRANSPARENCY: `[M7-SKIP] agent-memory chưa cấu hình`.
→ KHÔNG gọi `memory_smart_search` hay `memory_save`.

Nếu có `agent-memory` → tiếp sang Tầng 1.

### Tầng 1 — Gate (CÓ nên lưu không?)

| Câu hỏi | Nếu KHÔNG → hành động |
|---------|----------------------|
| Kiến thức đã verified bằng evidence (code merged, test pass, production ok)? | ❌ **KHÔNG LƯU** — chỉ là suy đoán |
| Có value cho task tương lai không? Có khả năng tái sử dụng? | ❌ **KHÔNG LƯU** — chỉ đúng cho task này |
| Có PII, credential, hoặc sensitive data không? | ❌ **KHÔNG LƯU** — vi phạm R-Data-1 |

Nếu cả 3 điều kiện đều đạt → tiếp sang Tầng 2.
Nếu bất kỳ điều kiện nào KHÔNG đạt → bỏ qua memory push, ghi vào AGENT_TRANSPARENCY: `[M7-SKIP] Lý do: {reason}`

### Tầng 2 — Dedup (đã có record cùng topic chưa?)

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

### Tầng 3 — Quota

- Tối đa **1 `memory_save` call** per task (R-Exec-3).
- Nếu task có nhiều bài học → chọn **1 cái quan trọng nhất**, tổng hợp các cái khác vào `content`.

## Gọi `memory_save` (native — không cần mapping)

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

## Hướng dẫn chọn kind

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

## Tính lũy đẳng (Idempotency)

- `ticket_id` sinh UUID5 xác định → Qdrant point ID.
- Gọi `memory_save` 2 lần cùng `ticket_id` → **cập nhật**, không tạo bản trùng.
- Không cần tìm kiếm trước để kiểm tra trùng lặp.

## Triển khai theo giai đoạn (R-Tool-6)

| Giai đoạn | Hành vi |
|-----------|--------|
| Tuần 1 | **Bỏ qua push hoàn toàn** — chỉ đọc, quan sát |
| Tuần 2 | Push có xác nhận — curator tóm tắt record sẽ lưu, **hỏi user trước khi gọi `memory_save`** |
| Tuần 3+ | Push tự động — user giữ quyền từ chối theo phiên |

**Graduation trigger** — tự động đề xuất chuyển stage:

```
FUNCTION check_m7_graduation():
  current_stage = đọc từ AGENT_TRANSPARENCY history hoặc conventions.yaml memory_push.stage
  tasks_completed_at_current_stage = đếm số task archive thành công kể từ stage hiện tại

  IF tasks_completed_at_current_stage >= 5:
    → SUGGEST: "[M7-GRAD] {n} tasks hoàn thành ở stage {current}.
               Đề xuất graduate lên stage {next}. Confirm?"
    → Nếu user đồng ý: ghi stage mới vào AGENT_TRANSPARENCY
    → Nếu user từ chối: ghi "[M7-GRAD] Declined by user" và reset counter

  Chạy mỗi khi archive_active_context() hoàn thành.
```

## Ghi AGENT_TRANSPARENCY

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
