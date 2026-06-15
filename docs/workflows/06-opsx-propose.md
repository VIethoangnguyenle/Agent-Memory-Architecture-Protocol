# Workflow: /opsx:propose — Propose Change

> **Command**: `/opsx:propose`  
> **Vai trò**: Tạo change mới + sinh toàn bộ artifacts trong 1 bước

---

## Mục tiêu

Tạo bộ artifacts hoàn chỉnh cho một change:
- `proposal.md` — What & Why.
- `design.md` — How.
- `tasks.md` — Implementation steps.

---

## Quy trình

### Bước 1 — Xác định change
- Nếu user cung cấp tên → dùng trực tiếp.
- Nếu không → hỏi user mô tả, derive tên kebab-case.

### Bước 2 — Tạo change directory
```bash
openspec new change "<name>"
```
Output: `openspec/changes/<name>/` với `.openspec.yaml`.

### Bước 3 — Lấy artifact build order
```bash
openspec status --change "<name>" --json
```
Parse `applyRequires` và `artifacts`.

### Bước 4 — Tạo artifacts theo dependency order
Với mỗi artifact:
1. `openspec instructions <artifact-id> --change "<name>" --json`
2. Đọc dependency artifacts.
3. Tạo file theo template.
4. Re-run status, kiểm tra completion.

### Bước 5 — Hiển thị final status

---

## Tích hợp Knowledge Layer

Nếu knowledge-layer context có sẵn:
- `REQUIREMENT.md` → populate proposal (what & why).
- `EXPLORE_CONTEXT.md` → populate design (how).
- `knowledge-snapshot.md` → bối cảnh hệ thống.

---

## Guardrails

- Tạo TẤT CẢ artifacts cần cho implementation.
- Đọc dependency artifacts trước khi tạo mới.
- `context` và `rules` là constraints cho agent, KHÔNG copy vào file output.
- Hỏi user nếu context unclear.
