# Workflow: /index-source — Lập Chỉ Mục Socraticode

> **Command**: `/index-source`  
> **Vai trò**: Lập chỉ mục mã nguồn trên Socraticode MCP

---

## Mục tiêu

Index codebase trên Socraticode MCP để có khả năng:
- `codebase_search` — tìm kiếm code ngữ nghĩa.
- `codebase_graph_query` — truy vấn đồ thị phụ thuộc.
- `codebase_context_search` — khám phá pattern và quy ước.

---

## Quy trình

### Bước 1 — Xác minh Local Index (GATE)
```bash
ls .understand-anything/knowledge-graph.json
```
Nếu không tìm thấy → **DỪNG**, yêu cầu chạy `/setup-knowledge` trước.

### Bước 2 — Kiểm tra trạng thái hiện tại
- Đã index → hỏi user có muốn re-index không.
- Chưa index → bắt đầu indexing.
- Đang index → poll progress.

### Bước 3 — Kích hoạt indexing
```
codebase_index(projectPath)
```

### Bước 4 — Poll cho đến khi hoàn thành
Poll `codebase_status` mỗi 15 giây, báo cáo progress.

### Bước 5 — Báo cáo hoàn thành
Hiển thị: Files, Chunks, Thời gian, Trạng thái.

---

## Rào chắn

- Local knowledge graph PHẢI tồn tại trước.
- Luôn hỏi trước khi re-index.
- Không gián đoạn indexing đang chạy.
- Workflow chỉ đọc — không sửa code.
