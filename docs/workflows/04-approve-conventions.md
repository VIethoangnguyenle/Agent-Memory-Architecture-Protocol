# Workflow: /approve-conventions — Commit Convention

> **Command**: `/approve-conventions`  
> **Vai trò**: Promote conventions.draft.yaml → conventions.yaml chính thức

---

## Điều kiện

1. Có `conventions.draft.yaml` (sinh bởi `/convention-scan`).
2. User đã review và edit trực tiếp trong IDE.
3. Sẵn sàng commit.

---

## Quy trình

### Bước 1 — Validate file
- File tồn tại? YAML hợp lệ? `meta.status == "draft"`?
- Các section bắt buộc: meta, naming, package_structure, upstream_constraints.

### Bước 2 — Cross-check với knowledge-snapshot.md
- Tìm mâu thuẫn rõ ràng giữa conventions và snapshot.
- Nếu có conflict → hỏi user chọn source of truth.

### Bước 3 — Promote draft → approved
1. Cập nhật `meta.status: approved`, `meta.approved_at`.
2. Rename: `conventions.draft.yaml` → `conventions.yaml`.
3. Backup: `conventions.draft.{timestamp}.yaml.bak`.

### Bước 4 — Cập nhật AGENT_TRANSPARENCY

### Bước 5 — Thông báo user
```
✅ conventions.yaml đã được commit.
Agent sẽ dùng {n} naming conventions và {n} upstream constraints
từ phiên làm việc tiếp theo.
```

---

## Error Cases

| Tình huống | Hành động |
|-----------|-----------|
| File không tồn tại | ABORT, hướng dẫn chạy `/convention-scan` |
| YAML parse error | ABORT, báo dòng lỗi |
| Conflict với snapshot | Hỏi user chọn source of truth |
| Đã approve lần 2 | Hỏi overwrite hay merge |
