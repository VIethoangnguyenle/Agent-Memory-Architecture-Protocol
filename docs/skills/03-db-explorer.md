# Skill: DB Explorer

> **Tên**: `db-explorer`  
> **Vai trò**: Database Explorer — khám phá schema, constraint, trigger/procedure  
> **Trigger**: Khi REQUIREMENT chạm tới dữ liệu (trong pipeline `/task`)

---

## Mục tiêu

Khám phá tầng database (SQL + NoSQL) để hiểu:

- **Schema**: Bảng, cột, kiểu dữ liệu, quan hệ.
- **Constraint**: PK, FK, unique, check constraint.
- **Business logic ẩn**: Trigger, stored procedure, computed column.
- **Index**: Chiến lược index hiện tại, potential performance issues.

Kết quả được ghi vào section "Tầng Database" của `EXPLORE_CONTEXT.md`.

---

## Khi nào dùng

- REQUIREMENT.md đề cập đến bảng/cột/query/migration.
- Task liên quan đến thay đổi data model.
- Cần hiểu business logic ẩn trong DB layer.

---

## Quy trình

### Bước 1 — Xác định scope DB

- Đọc REQUIREMENT.md → trích xuất entity/table name liên quan.
- Xác định DB engine (PostgreSQL, MySQL, MongoDB…).

### Bước 2 — Khám phá schema

Sử dụng MCP `db-remote`:

- List tables/collections liên quan.
- Describe columns, types, constraints.
- Map foreign key relationships.

### Bước 3 — Tìm business logic ẩn

- Scan triggers trên các table liên quan.
- Scan stored procedures/functions.
- Ghi nhận computed columns, default values có logic.

### Bước 4 — Ghi output

Cập nhật section "Tầng Database (db-explorer)" trong `.knowledge-layer/active/EXPLORE_CONTEXT.md`:

- Schema summary (table, columns, types).
- Relationship map.
- Trigger/procedure list.
- Potential concerns (missing indexes, orphan FK…).

---

## Đầu ra

| File | Section |
|------|---------|
| `EXPLORE_CONTEXT.md` | Tầng Database (db-explorer) |

---

## Nguyên tắc

- **Chỉ đọc**: Không bao giờ modify database.
- **Ghi rõ giả định**: Nếu không có quyền truy cập DB → ghi Độ tin cậy THẤP.
- **Bảo mật**: Không log dữ liệu nhạy cảm (PII, credentials).
