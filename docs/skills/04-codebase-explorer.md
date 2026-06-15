# Skill: Codebase Explorer

> **Tên**: `codebase-explorer`  
> **Vai trò**: Code Mapper — map REQUIREMENT → module/service/file  
> **Trigger**: Sau `db-explorer` trong pipeline `/task`

---

## Mục tiêu

Sử dụng **Socraticode MCP** và **Knowledge Graph** để:

- Map từng yêu cầu trong REQUIREMENT.md → module/service/file cụ thể trong codebase.
- Hiểu dependency giữa các module.
- Xác định blast radius (phạm vi ảnh hưởng) của thay đổi dự kiến.

---

## Công cụ sử dụng

| Công cụ | Mục đích |
|---------|----------|
| **Knowledge Graph MCP** (nguồn chính) | `query_nodes` → tìm class/module, `get_node_source` → đọc code, `get_relationships` → dependency, `trace_call_chain` → call flow |
| **Socraticode MCP** (bổ sung) | `codebase_search` → semantic search, `codebase_graph_query` → dependency graph |

---

## Quy trình

### Bước 1 — Kiểm tra trạng thái Knowledge Graph

```
CALL: get_graph_stats()
  IF graph OK → dùng KG tools làm nguồn chính.
  IF chưa có graph → gợi ý user chạy /understand, dùng Socraticode tạm thời.
```

### Bước 2 — Map requirement → code

Với mỗi requirement/AC trong REQUIREMENT.md:

- Tìm class/module liên quan qua `query_nodes`.
- Đọc source code qua `get_node_source`.
- Trace dependency qua `get_relationships`.

### Bước 3 — Xác định blast radius

- Sử dụng `find_impact` hoặc `codebase_impact` để tìm files/modules bị ảnh hưởng.
- Ghi kèm **node_id** cho mỗi component quan trọng → cho architecture-reviewer dùng sau.

### Bước 4 — Ghi output

Cập nhật section "Kiến trúc code hiện tại (codebase-explorer)" trong `EXPLORE_CONTEXT.md`.

---

## Đầu ra

| File | Section |
|------|---------|
| `EXPLORE_CONTEXT.md` | Kiến trúc code hiện tại (codebase-explorer) |

---

## Nguyên tắc

- **Knowledge Graph first**: Ưu tiên KG tools, fallback sang Socraticode khi KG không khả dụng.
- **Ghi node_id**: Cho phép các skill sau trace lại code thực tế.
- **Không suy đoán**: Nếu KG chưa có graph → ghi rõ Độ tin cậy THẤP.
