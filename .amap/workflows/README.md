# Workflows — User-facing Shortcuts

Đây là thư mục tham chiếu nhanh cho các workflow chính. Logic đầy đủ nằm trong `.amap/workflows/`.

---

## Danh sách Workflow

| Lệnh | File định nghĩa | Mô tả |
|------|----------------|-------|
| `/task <input>` | `.amap/workflows/task.md` | Pha 1: Hiểu vấn đề, requirement, explore |
| `/task spec <ticket>` | `.amap/workflows/task.md` | Pha 2: Sinh spec kỹ thuật |
| `/task apply <ticket>` | `.amap/workflows/task.md` | Pha 3: Apply spec vào code |
| `/idea-to-task` | `.amap/workflows/idea-to-task.md` | Chuyển ideation → draft ticket |
| `/index-source` | `.amap/workflows/index-source.md` | Lập chỉ mục Socraticode |

---

## Quick Start

```
# Bắt đầu với ý tưởng mới
/task Thêm tính năng giới hạn số lệnh lập lệnh theo ngày cho từng nhân viên

# Bắt đầu với ticket có sẵn
/task https://jira.example.com/browse/ABC-123

# Chuyển ideation thành ticket
/idea-to-task

# Sinh spec sau khi đã có requirement + context
/task spec ABC-123

# Apply spec vào code
/task apply ABC-123
```
