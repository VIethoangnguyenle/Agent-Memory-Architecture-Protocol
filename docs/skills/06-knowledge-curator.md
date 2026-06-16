# Skill: Knowledge Curator

> **Tên**: `knowledge-curator`  
> **Vai trò**: Quản lý vòng đời knowledge — archive, rotate, snapshot  
> **Trigger**: Sau khi `/task apply` hoàn thành

---

## Mục tiêu

Quản lý **vòng đời tri thức** trong hệ thống AMAP:

1. **Archive**: Lưu trữ context đã hoàn thành (active/ → archive/).
2. **Update snapshot**: Cập nhật knowledge-snapshot.md với phát hiện mới.
3. **Reset**: Reset active/ về template trống cho task mới.
4. **Rotate**: Quản lý dung lượng archive (xoá cũ khi quá lớn).

---

## 3 Hàm chính

### `archive_active_context(ticket_id, status)`

```
1. Copy toàn bộ .knowledge-layer/active/ → .knowledge-layer/archive/{ticket_id}/
2. Tạo ARCHIVE_META.md trong archive folder:
   - ticket_id, status, timestamp, skills đã dùng, Độ tin cậy cuối
3. Ghi vào AGENT_TRANSPARENCY (mới): "Task {ticket_id} archived"
```

### `update_knowledge_snapshot(discoveries)`

```
1. Đọc discoveries từ EXPLORE_CONTEXT.md:
   - Tables/columns mới phát hiện
   - Modules/services đã map
   - Business rules đã xác nhận
2. Merge vào .knowledge-layer/long-term/knowledge-snapshot.md:
   - Không ghi đè — chỉ bổ sung thông tin mới
   - Đánh dấu timestamp và ticket_id nguồn
```

### `reset_active_context()`

```
1. Reset tất cả file trong .knowledge-layer/active/ về template trống
2. Giữ nguyên thư mục ideation/ (không xoá ý tưởng đang active)
3. Ghi AGENT_TRANSPARENCY mới: "Active context reset"
```

---

## Rotation Policy

Khi archive quá lớn (>50 tickets hoặc >100MB):

- Giữ 20 ticket gần nhất.
- Ticket cũ hơn → nén và chuyển vào `archive/compressed/`.
- Knowledge-snapshot.md **luôn giữ** (không bị rotate).

---

## Nguyên tắc

- **Không xoá knowledge-snapshot**: Snapshot là bộ nhớ dài hạn duy nhất.
- **Mọi archive đều có ARCHIVE_META**: Để trace lại khi cần.
- **Reset trước khi task mới**: Active context phải sạch trước khi bắt đầu task mới.
