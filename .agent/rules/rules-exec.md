# rules-exec.md — Data, Architecture, Cost & Observability Rules

> Sub-file của RULES.md. Đọc qua manifest `RULES.md`.

---

## 4. Data Rules — Dữ liệu & bảo mật

### [CRITICAL] R-Data-1: PII & bí mật

- Không được log/copy dữ liệu nhạy cảm (PII, credential, token…) vào:
  - `.knowledge-layer/active/REQUIREMENT.md`, `.knowledge-layer/active/EXPLORE_CONTEXT.md`, `.knowledge-layer/active/AGENT_TRANSPARENCY.md`.
- Nếu tool trả về data nghi là PII:
  - Chỉ tóm tắt pattern, không lưu raw record.

### [CRITICAL] R-Data-2: Sample data

- Khi đọc sample data:
  - Luôn giới hạn số bản ghi nhỏ.
  - Ưu tiên schema inference.

---

---

## 5. Architecture & Reliability Rules

### [CRITICAL] R-Arch-1: Độ tin cậy kiến trúc ràng buộc tool

- Độ tin cậy đánh giá kiến trúc không được là CAO nếu:
  - UA chưa chạy / không khả dụng **và**
  - db-explorer chưa chạy cho phần dữ liệu liên quan.

### [CRITICAL] R-Arch-2: Respect boundaries

- Không đề xuất phá vỡ boundary/module rõ ràng hiện có mà không ghi rõ rủi ro trong `architecture-reviewer`.

### [CRITICAL] R-Arch-3: Explore Database First (Data-Driven Architecture)

- Mọi requirement liên quan đến dữ liệu (mã dịch vụ mới, bảng mới, logic định tuyến theo database):
  - **BẮT BUỘC** phải gọi `db-explorer` (sử dụng `db-remote`) để soi dữ liệu/schema thực tế **TRƯỚC KHI** phân tích mã nguồn bằng `codebase-explorer`.
  - Nghiêm cấm việc đưa ra kết luận kiến trúc hoặc propose code nếu thiếu bằng chứng (evidence) từ Database.

---

---

## 7. Cost & Execution Rules

### [CRITICAL] R-Exec-1: Giới hạn vòng lặp & tool call

- Mỗi lượt `/task` có giới hạn mềm về số tool call. Nếu vượt:
  - Agent nên dừng, ghi vào `.knowledge-layer/active/AGENT_TRANSPARENCY.md` và hỏi user.

### [REFERENCE] R-Exec-2: Thời gian chạy

- Nếu một pipeline kéo dài quá lâu:
  - Agent cần tóm tắt trạng thái và đề nghị chia nhỏ thành phiên mới.

### [CRITICAL] R-Exec-3: Tool call budget per phase (complexity-scaled)

Budget được điều chỉnh theo complexity tier — xác định ở đầu mỗi pha dựa trên scope:

| Tier | Điều kiện | Pha 1 KG/UA/Socraticode | Pha 2 opsx | Pha 3 apply |
|------|-----------|------------------------|------------|-------------|
| **simple** | scope ≤ 1 module, không chạm DB schema | 10 / 3 / 5 | 3 | 5 |
| **standard** | scope 1-2 modules HOẶC có DB read | 20 / 5 / 10 | 5 | 10 |
| **complex** | scope ≥ 3 modules HOẶC DB schema change + integration | 30 / 10 / 15 | 8 | 15 |

Cách xác định tier:
- Đọc REQUIREMENT.md scope (In-scope items) → đếm modules/services liên quan.
- Nếu chưa có REQUIREMENT → dùng **standard** làm mặc định.
- Ghi tier đã chọn vào AGENT_TRANSPARENCY: `[BUDGET] Tier: {tier} — lý do: {reason}`.

- **Memory budget** — áp dụng cho `memory_smart_search` + `memory_recall`:
  - **Pha 1** (`/task <input>`): tối đa **5 memory calls**.
  - **Pha 2** (`/task spec`): tối đa **3 memory calls**.
  - **Pha 3** (`/task apply`): **0 memory read calls**; **1 `memory_save` call** qua `knowledge-curator` post-task hook only.
  - `memory_sessions`, `memory_audit`, `memory_health` là **exempt** — không tính vào budget.
- Khi đạt 80% budget của một pha:
  - Ghi cảnh báo vào `AGENT_TRANSPARENCY.md`: `[BUDGET-WARNING] Pha X: đã dùng Y/Z calls`.
- Khi vượt 100%:
  - **Hardstop** — dừng pha, cập nhật `AGENT_TRANSPARENCY.md`, hỏi user có muốn tiếp tục không.
  - Không được tự mở rộng budget mà không có xác nhận của user.
- Lý do: Ngăn agent loop không giới hạn khi gặp KG query mơ hồ hoặc sparse results.

### [CRITICAL] R-Exec-4: TOKEN_LOG checkpoint bắt buộc

- Trước khi báo hoàn thành bất kỳ pha nào (Pha 1/2/3), agent **PHẢI**:
  - Ghi checkpoint vào `.knowledge-layer/active/TOKEN_LOG.md` (timestamp + token estimate).
  - Cập nhật bảng Tóm tắt tương ứng pha đó.
- Nếu TOKEN_LOG.md chưa tồn tại khi bắt đầu Pha 1:
  - Tạo từ template, điền ticket-id, timestamp bắt đầu, model name.
- POST-PHASE SELF-CHECK trong `task.md` đã liệt TOKEN_LOG — rule này enforce nó thành **hard constraint**.
- Vi phạm: ghi vào AGENT_TRANSPARENCY `[R-Exec-4] TOKEN_LOG chưa ghi — phải ghi trước khi tiếp.` và **không được kết thúc pha**.

---

---

## 8. Observability & Audit Rules

### [CRITICAL] R-Obs-1: AGENT_TRANSPARENCY bắt buộc

- Sau mỗi pha quan trọng (`/task` Pha 1/2/3, `/idea-to-task`):
  - Phải cập nhật `.knowledge-layer/active/AGENT_TRANSPARENCY.md` (nguồn đã đọc, tool đã gọi, cảnh báo, độ tin cậy).

### [CRITICAL] R-Obs-2: Log vi phạm rule

- Nếu có ý định vi phạm rule:
  - Không thực thi.
  - Ghi lại trong `.knowledge-layer/active/AGENT_TRANSPARENCY.md` (ý định, ID rule, cách xử lý).

---
