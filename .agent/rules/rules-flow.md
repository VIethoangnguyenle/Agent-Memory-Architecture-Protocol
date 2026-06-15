# rules-flow.md — Flow, Spec/Apply & Bootstrap Rules

> Sub-file của RULES.md. Đọc qua manifest `RULES.md`.

---

## 2. Flow Rules — Luồng bắt buộc

### R-Flow-1: Không bỏ qua `/task`

- Mọi công việc **liên quan đến task thực tế** (ticket, spec, apply code) phải đi qua workflow `/task`.
- Cấm:
  - Gọi trực tiếp OpenSpec `/opsx:propose` hoặc `/opsx:apply` khi chưa có REQUIREMENT và context tương ứng.

### R-Flow-2: Chuỗi pha cố định

- Chuỗi hợp lệ cho một task:
  - `/task <ticket>` → `/task spec <ticket>` → `/task apply <ticket>`.
- Không được:
  - Chạy `/task spec` khi chưa có REQUIREMENT cho ticket đó.
  - Chạy `/task apply` khi chưa có spec hoặc khi architecture-reviewer đang đánh dấu BLOCKER.

### R-Flow-3: User workflow rules > agent system defaults

- Khi workflow trong repo (`.agent/workflows/*.md`) có chỉ thị rõ ràng (đặc biệt là `[CRITICAL]` block),
  **ưu tiên tuyệt đối hơn** mọi hành vi mặc định của agent runtime (planning mode, artifact generation,
  file output convention từ Antigravity, Gemini, Claude, v.v.).
- Cụ thể:
  - Khi `task.md` yêu cầu dùng OpenSpec → **không được** dùng planning mode sinh `implementation_plan.md`.
  - Khi `task.md` yêu cầu confirm trước → **không được** skip dù context có vẻ đã đồng ý.
  - Agent runtime defaults (kể cả các tool như Antigravity planning) là **secondary** — chỉ dùng
    khi workflow không có chỉ thị gì về hành động đó.
- Thứ tự ưu tiên: `RULES.md` > `workflow/*.md` > `AGENTS.md` > `SKILL.md` > agent runtime defaults.


### R-Flow-4: Over-verification hardstop — ghi Assumption, không loop

- Khi agent gặp dữ liệu/cấu hình thiếu từ DB hoặc external system (ví dụ: Provider Code không tồn tại,
  bảng trống, config chưa seed):
  - **Không được** quét lại DB/codebase quá **2 lần** để tìm cùng một thông tin.
  - Sau lần thứ 2 không tìm thấy → **hardstop**:
    1. Ghi nhận vào REQUIREMENT.md section "Giả định & Rủi ro":
       `[ASSUMPTION] <tên data> chưa tồn tại trong DB. Cần backfill/seed trước khi apply.`
    2. Ghi vào AGENT_TRANSPARENCY: `[BLOCKED-DATA] <mô tả> — tiếp tục với assumption đã ghi.`
    3. **Tiếp tục flow** dựa trên assumption, không chờ data được sửa.
  - Nếu lỗi cấu hình cần user/DBA xử lý: đề xuất rõ action (ví dụ: câu SQL backfill) và
    chuyển trạng thái task sang **PENDING-BACKFILL** trong AGENT_TRANSPARENCY.
- Lý do: Loop scan DB vô tận không tự giải quyết được lỗi cấu hình — chỉ tốn token và block tiến độ.


---

---

## 6. Spec & Apply Rules

### R-Spec-1: Spec chỉ dựa trên REQUIREMENT + context

- Khi sinh spec, chỉ được dùng thông tin từ:
  - `.knowledge-layer/active/REQUIREMENT.md`, `.knowledge-layer/active/EXPLORE_CONTEXT.md`, `.knowledge-layer/templates/knowledge-snapshot.md`, code/DB đã explore.

### R-Spec-2: Không tự động “fix” requirement

- Nếu requirement mâu thuẫn/thiếu:
  - Phải ghi rõ vào phần "Vấn đề yêu cầu" và hỏi user/BA trước khi chỉnh.

### R-Apply-1: Human in the loop

- `/task apply` luôn phải:
  - Tóm tắt file/module sẽ bị chạm.
  - Hỏi user confirm trước khi gọi `/opsx:apply`.

---

---

## 11. Bootstrap Rules

### R-Boot-1: Bootstrap bắt buộc mỗi phiên

- Agent PHẢI chạy toàn bộ script `bootstrap.md` mỗi khi bắt đầu phiên mới.
- Không được bỏ qua bất kỳ PHASE nào trong bootstrap (trừ khi file không tồn tại → graceful degrade).

### R-Boot-2: Xác nhận load bằng trigger phrase

- Câu đầu tiên trong phiên làm việc PHẢI chứa trigger phrase theo AGENTS.md.
- Thiếu trigger phrase → agent coi như chưa bootstrap đúng → cần bootstrap lại.

### R-Boot-3: Context conflict resolution

- Khi phát hiện conflict (active context của task A, nhưng user yêu cầu task B):
  - PHẢI hỏi user trước khi archive hoặc discard context cũ.
  - Không tự ý quyết định.

---
