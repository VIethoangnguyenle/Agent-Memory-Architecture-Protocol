# rules-knowledge.md — Knowledge Lifecycle, Path Convention & Convention Rules

> Sub-file của RULES.md. Đọc qua manifest `RULES.md`.

---

## 10. Knowledge Lifecycle Rules

### R-KL-1: Archive bắt buộc sau Apply

- Sau khi `/task apply` hoàn thành, skill `knowledge-curator` PHẢI:
  - Archive toàn bộ `active/` vào `archive/{ticket-id}/`.
  - Cập nhật `knowledge-snapshot.md`.
  - Reset `active/` về template skeleton.
- Không được bắt đầu task mới trong khi `active/` vẫn còn context của task cũ mà chưa archive.

### R-KL-2: Restore phải xác nhận

- Khi restore context từ archive:
  - Nếu `active/` đang có context → PHẢI hỏi user trước khi ghi đè.
  - Không tự ý ghi đè context đang active.

### R-KL-3: knowledge-snapshot là source of truth kiến trúc

- `knowledge-snapshot.md` là nguồn kiến trúc tổng thể duy nhất cho toàn bộ hệ thống.
- Mọi phát hiện mới có giá trị lâu dài (schema, module mới, business rule quan trọng) PHẢI được cập nhật vào đây.
- Không xoá thông tin cũ trong knowledge-snapshot; chỉ bổ sung hoặc đánh dấu "outdated".

### R-KL-4: Archive rotation

- Khi archive có hơn 20 tickets: `knowledge-curator.rotate_archive()` được phép chạy.
- Không xoá archive mà không đã log summary vào `ARCHIVE_LOG.md` trước.

---

---

## 12. Path Convention — Cập nhật v2.0

### R-Path-1: Quy ước đường dẫn bắt buộc (v2.0)

Tất cả file context cho task hiện tại nằm ở `.knowledge-layer/active/`.
Tất cả template nằm ở `.knowledge-layer/templates/`.
Archive theo ticket nằm ở `.knowledge-layer/archive/{ticket-id}/`.
Agent infrastructure (skills, workflows, scripts, rules) nằm ở `.agent/`.

| File | Path | Ai ghi | Ai đọc |
|------|------|--------|--------|
| REQUIREMENT | `.knowledge-layer/active/REQUIREMENT.md` | requirement-analyst, spec-extract | db-explorer, codebase-explorer, architecture-reviewer, openspec-propose |
| EXPLORE_CONTEXT | `.knowledge-layer/active/EXPLORE_CONTEXT.md` | db-explorer, codebase-explorer, architecture-reviewer | architecture-reviewer, openspec-propose |
| AGENT_TRANSPARENCY | `.knowledge-layer/active/AGENT_TRANSPARENCY.md` | Mọi skill + workflow | User, architecture-reviewer |
| Knowledge Snapshot | `.knowledge-layer/long-term/knowledge-snapshot.md` | knowledge-curator (tích luỹ) | codebase-explorer, architecture-reviewer, bootstrap |
| Ideation files | `.knowledge-layer/active/ideation/ideation-*.md` | /task (IDEA_ONLY) | /idea-to-task |
| Archive | `.knowledge-layer/archive/{ticket-id}/` | knowledge-curator | bootstrap, context-loader |
| Archive Log | `.knowledge-layer/archive/ARCHIVE_LOG.md` | knowledge-curator | bootstrap |

---

---

## 13. Convention Rules

### R-Conv-1: conventions.yaml là nguồn naming duy nhất

- Khi `conventions.yaml` tồn tại với `status: approved`, mọi tên class/method/package được đề xuất bởi agent (trong spec, apply, hoặc ideation) PHẢI align với conventions.yaml.
- Không được đề xuất tên vi phạm convention mà không ghi rõ lý do vào AGENT_TRANSPARENCY.

### R-Conv-2: Upstream constraints không được override

- Mọi entry trong `upstream_constraints` section của conventions.yaml có `weight: mandatory` là **bất biến**.
- Agent không được đề xuất thay thế `BaseEntity`, `BaseRepository`, `@DvnhTransactional`, hoặc bất kỳ constraint nào từ `dvnh-common` — kể cả khi user yêu cầu.
- Nếu bị yêu cầu: ghi rõ "Không thể thực hiện — vi phạm upstream constraint từ dvnh-common (R-Conv-2)" và giải thích lý do kỹ thuật.

### R-Conv-3: Draft không được dùng cho reasoning

- `conventions.draft.yaml` (chưa approve) KHÔNG được nạp vào context P3.
- Agent không được tham chiếu đến conventions.draft.yaml khi sinh spec hoặc apply code.
- Chỉ sau `/approve-conventions` → conventions.yaml mới có hiệu lực.

### R-Conv-4: Conflict conventions vs snapshot phải resolve trước khi approve

- Nếu `/approve-conventions` phát hiện mâu thuẫn giữa conventions.draft.yaml và knowledge-snapshot.md:
  - PHẢI hỏi user chọn source of truth.
  - Không được tự resolve bằng cách ưu tiên một bên.
  - Kết quả resolve được ghi vào cả 2 file.

### R-Conv-5: Re-scan bắt buộc sau refactor lớn

- Sau task loại `refactor` hoàn thành (status=completed):
  - knowledge-curator **PHẢI** ghi vào AGENT_TRANSPARENCY:
    `[R-Conv-5] conventions.yaml có thể stale sau refactor. Chạy /convention-scan [U] trước task tiếp theo.`
  - Ghi `conv_rescan_required: true` vào ARCHIVE_META.md của ticket đó.
- Trong **bootstrap của phiên tiếp theo**: nếu `conv_rescan_required: true` tồn tại trong archive gần nhất:
  - **BLOCK** nhận lệnh `/task spec` hoặc `/task apply` cho đến khi:
    - User chạy `/convention-scan [U]`, HOẶC
    - User xác nhận rõ ràng "bỏ qua re-scan, tiếp tục" (ghi lý do vào AGENT_TRANSPARENCY)
  - Không block `/task <input>` (Pha 1 exploration vẫn OK — chưa sinh code)
- Lý do: conventions.yaml stale là silent failure — agent không biết mình dùng rule cũ.
  Khác với token overhead (có thể detect), staleness không có warning tự nhiên.

---
