# Re-scan Policy, Agent Usage & Delta Scan

> Reference file — extracted from SKILL.md for progressive disclosure.

## Khi conventions.yaml đã có — Re-scan Policy

Nếu `conventions.yaml` đã tồn tại (status: approved), skill sẽ:

```
1. Hiển thị thông tin file hiện tại:
   - approved_at, số patterns
2. Hỏi user:
   [U] Update: scan lại, merge với conventions.yaml hiện tại
       → Chỉ thêm pattern mới, không xoá cũ
       → Pattern cũ bị contradict → đánh dấu "needs_re_review"
   [R] Rebuild: scan lại hoàn toàn, sinh draft.yaml mới từ đầu
       → User review toàn bộ lại
   [S] Skip: dùng conventions.yaml hiện tại
```

---

## Cách Agent Dùng conventions.yaml Sau Khi Approve

Sau khi approved, agent phải:

- Khi sinh spec (Pha 2): đọc conventions.yaml trước khi đề xuất tên class/method.
- Khi `architecture-reviewer` phát hiện tên class trong REQUIREMENT không khớp convention → ghi warning vào EXPLORE_CONTEXT.
- Khi `codebase-explorer` tìm module → ưu tiên match với layer pattern trong `package_structure`.
- **KHÔNG override** `upstream_constraints` dù user yêu cầu — ghi rõ lý do từ chối nếu bị yêu cầu.

---

## [L4] Delta Scan Mode

### Mục đích

Thay vì scan toàn bộ codebase (full scan), delta scan chỉ phân tích **những file đã thay đổi** kể từ lần scan trước.
Nhanh hơn, ít tốn token hơn, phù hợp sau refactor hoặc task lớn mà không cần scan lại toàn bộ.

### Trigger Delta Scan

```
MODES:
  [F] Full scan    — scan toàn bộ codebase (default, onboard lần đầu)
  [D] Delta scan   — chỉ scan files changed since last scan
  [U] Update scan  — như [D] nhưng merge kết quả vào conventions.yaml hiện tại (không tạo lại từ đầu)
```

User chọn mode khi gọi `/convention-scan` hoặc khi R-Conv-5 suggest.

### Delta Scan Algorithm

```
FUNCTION delta_scan():
  1. Đọc conventions.yaml (hoặc conventions.draft.yaml):
     - Lấy metadata: last_scan_at, last_scan_commit (nếu có)
  2. Xác định files changed since last_scan_at:
     - Ưu tiên: git diff (nếu có git MCP/tool)
     - Fallback: filter files có modified_time > last_scan_at
  3. Filter chỉ source files (*.java, *.kt, v.v.) — bỏ qua config, test, docs
  4. Với mỗi file changed:
     - Query KG MCP: get_node_detail(file) → check node còn mới không
     - Nếu node OK: extract naming patterns từ file đó
     - Nếu graph outdated cho file này: dùng file read + pattern matching
  5. So sánh pattern mới với conventions hiện tại:
     - Pattern giống → chỉ update verified_at
     - Pattern mới → thêm vào draft với note "delta scan {date}"
     - Pattern mâu thuẫn → đánh dấu conflict, hỏi user
  6. Cập nhật metadata trong conventions.draft.yaml:
     last_scan_at: {today}
     scan_mode: delta
     files_scanned: {n}
     changes_detected: {n}

REPORT:
  "Delta scan hoàn thành. Scanned {n} files. {m} pattern mới/thay đổi."
```

### Khi Delta Scan Không Đủ

Nếu delta scan phát hiện > 20% file thay đổi so với tổng số file → đề xuất full scan thay thế.
```
IF changed_files / total_files > 0.2:
  → WARN: "Nhiều file thay đổi ({pct}%). Cân nhắc Full Scan thay vì Delta."
```
