---
name: convention-intelligence-builder
version: '1.0'
description: >
  Scan codebase qua UA + Socraticode để extract naming conventions, class suffix patterns,
  và layer-specific design principles. Sinh conventions.draft.yaml để user review trước khi approve.
  Dùng khi onboard project mới hoặc sau refactor lớn cần cập nhật conventions.
  KHÔNG dùng cho: viết convention thủ công (→ edit trực tiếp conventions.yaml),
  review kiến trúc/rủi ro (→ architecture-reviewer), infer coding philosophy (→ author-dna-builder).
---

# Convention Intelligence Builder

## 1. Mục tiêu

Extract **implicit conventions** từ codebase thực tế — không phải generic best practice — và đưa chúng vào `.knowledge-layer/templates/conventions.yaml` để agent dùng khi sinh spec và code.

Hai nguồn được scan đồng thời qua UA Knowledge Graph:
- **Project codebase** (`PROJECT_ROOTS`) — convention project-native, có thể có exception có lý do.
- **Upstream shared library** (`UPSTREAM_ROOTS`) — convention từ shared library bắt buộc tuân theo, không override.

Output cuối là `conventions.draft.yaml` → user review + edit trong IDE → chạy `/approve-conventions` để commit chính thức.

---

## 2. Khi nào dùng

Trigger skill này khi:
- Bắt đầu onboard một project mới vào hệ thống Agent Memory.
- Sau refactor lớn (rename package, đổi layer architecture).
- User cảm thấy agent đang đề xuất tên class/file không khớp với convention thực tế.
- `conventions.yaml` chưa tồn tại hoặc `status: stale` trong metadata.

Không dùng khi:
- Chỉ muốn tra cứu convention (đọc `conventions.yaml` trực tiếp).
- Task đang ở Pha 2/3 — không nên scan convention giữa chừng spec.

---

## 3. Nguồn dữ liệu

| Nguồn | Tool | Ghi chú |
|-------|------|---------|
| UA Knowledge Graph (project) | `query_nodes`, `get_node_detail`, `get_node_source` | Nguồn chính cho naming pattern |
| UA Knowledge Graph (upstream) | Cùng tool, filter theo `UPSTREAM_ROOTS` path | Tag `origin: upstream` |
| Socraticode semantic search | `codebase_search`, `codebase_context_search` | Làm giàu pattern khi UA fuzzy |
| Domain graph UA | `get_domain_overview`, `get_domain_detail` | Hiểu layer boundaries |

---

## 4. Quy trình chi tiết

### Bước 1 — Kiểm tra trạng thái UA graph

```
CALL: get_graph_stats()
  IF graph không tồn tại hoặc quá cũ:
    → WARN: "UA graph chưa sẵn sàng. Chạy /understand trước."
    → ABORT
  IF graph OK:
    → Ghi nhận: project_root path, upstream_root path (nếu có upstream library)
    → Dùng path prefix để phân biệt origin sau này
```

---

### Bước 2 — Structural Audit (5 chiều)

Chạy song song 5 chiều scan qua UA + Socraticode:

| Chiều | Nội dung | Tool chính |
|-------|----------|------------|
| **2A** | File & Class Naming Patterns (suffix grouping) | UA `query_nodes(type="class")` |
| **2B** | Package / Layer Structure | UA `get_domain_overview()` |
| **2C** | Architecture Core Patterns & Dispatch | UA `get_relationships()` |
| **2D** | Upstream Conventions từ shared library | UA `query_nodes(upstream)` |
| **2E** | Test & Config Conventions | Socraticode `codebase_search()` |

> **Chi tiết đầy đủ (scan queries per dimension)**: Xem [references/structural-audit-scan.md](references/structural-audit-scan.md)

### Bước 3 — Pattern Consolidation

Sau khi có raw data từ 5 chiều, consolidate thành structured findings:

```
FOR EACH pattern category:
  1. Tính confidence score:
     - HIGH   : count >= 10, consistent across layers
     - MEDIUM : count 3-9, hoặc có exception nhỏ
     - LOW    : count < 3, hoặc contradicted by other evidence

  2. Phân biệt origin:
     - project-native : source_path trong PROJECT_ROOTS
     - upstream       : source_path trong UPSTREAM_ROOTS

  3. Detect exceptions (nếu có):
     - Pattern X xuất hiện 15 lần nhưng có 2 file vi phạm
     → Ghi nhận exception, không bỏ qua

  4. Ghi evidence:
     - Ít nhất 2-3 ví dụ cụ thể (class name, file path) cho mỗi pattern
```

---

### Bước 4 — Sinh conventions.draft.yaml

Ghi ra `.knowledge-layer/templates/conventions.draft.yaml` với 7 sections:
Naming Conventions, Package Structure, Design Patterns, Upstream Constraints,
Test Conventions, Exceptions & Inconsistencies, Needs Review.

### Bước 5 — Summary Report cho User

Xuất bảng tóm tắt: HIGH/MEDIUM/LOW patterns, upstream constraints, exceptions, needs review.

### Bước 6 — /approve-conventions Workflow

Validate draft → Cross-check với snapshot → Promote to approved → Update context-loader.

> **Chi tiết đầy đủ (YAML template + report format + approve workflow)**: Xem [references/conventions-draft-template.md](references/conventions-draft-template.md)

---

## 5. Re-scan Policy & Agent Usage

- **Re-scan modes**: [U] Update, [R] Rebuild, [S] Skip
- **Agent usage sau approve**: enforce naming ở Pha 2, warn ở architecture review, KHÔNG override upstream constraints

## [L4] Delta Scan Mode

Scan chỉ files changed since last scan. Fallback to full scan nếu >20% files thay đổi.

> **Chi tiết đầy đủ (re-scan, usage, delta algorithm)**: Xem [references/rescan-usage-guide.md](references/rescan-usage-guide.md)

---

## 7. Cập nhật AGENT_TRANSPARENCY

```
- [x] convention-intelligence-builder
- Scanned: {n} project nodes, {n} upstream nodes
- Patterns extracted: {n} high, {n} medium, {n} low confidence
- Upstream constraints: {n} mandatory rules từ {upstream_library}
- conventions.yaml status: draft | approved
- Warnings: {list nếu có conflict với snapshot}
```
