# Workflow: /idea-to-task — Từ Ý Tưởng Sang Task

> **Command**: `/idea-to-task`  
> **Vai trò**: Chuyển kết quả ideation thành draft ticket + gợi ý chạy `/task spec`

---

## Khi nào dùng

- Đã có file `ideation-*.md` trong `.knowledge-layer/active/ideation/`.
- User muốn biến ý tưởng thành **task chính thức** trong hệ thống ticket.

---

## Quy trình

### Bước 1 — Chọn file ideation
- Nếu user chỉ rõ → tìm file khớp.
- Nếu không → liệt kê file gần nhất, hỏi user chọn.

### Bước 2 — Trích xuất thông tin
Từ file ideation, lấy: tóm tắt, động lực, scope đề xuất, AC gợi ý, ghi chú kỹ thuật.

### Bước 3 — Sinh draft ticket
- **Summary**: 1 câu ngắn, rõ ràng.
- **Description**: Bối cảnh, mục tiêu, scope (in/out), ghi chú kỹ thuật.
- **AC**: Checklist từ AC gợi ý trong ideation.

### Bước 4 — Trao đổi & refine với user

### Bước 5 — Tạo ticket & kết nối
- Nếu có MCP ticket → tạo tự động.
- Nếu không → user copy-paste, cung cấp ticket ID.
- Gợi ý: `/task <ticket-id>` để chạy full pipeline.

---

## Ideation Expiry (M4)

- Mỗi file ideation có `ideation_expiry` (mặc định: created_at + 30 ngày).
- Khi hết hạn: `[K]` Giữ thêm 30 ngày | `[C]` Convert ngay | `[A]` Archive.
- Auto-archive nếu không phản hồi thêm 30 ngày.

---

## Status Flow

```
active → expired → [K] → active (extended)
active → expired → [C] → converted
active → expired → [A] → archived
active → converted (via /idea-to-task) → converted
```
