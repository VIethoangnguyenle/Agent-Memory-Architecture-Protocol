---
name: convention-intelligence-builder
description: Scan codebase qua UA + Socraticode để extract naming conventions, class suffix patterns, và layer-specific design principles. Sinh conventions.draft.yaml để user review trước khi approve chính thức.
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

#### 2A. File & Class Naming Patterns

```
QUERY UA: query_nodes(type="class", limit=200)
  → Lấy tên tất cả class
  → GROUP BY suffix:
      *Service, *ServiceImpl, *Repository, *RepositoryImpl
      *Handler, *Processor, *Command, *Query, *Event
      *Factory, *Builder, *Mapper, *Converter, *Validator
      *Controller, *Facade, *UseCase, *Manager
      *Config, *Properties, *Constants, *Enum
      *Request, *Response, *DTO, *Model, *Entity, *VO
      *Exception, *Error, *ExceptionHandler
  → COUNT occurrence per suffix
  → FILTER: chỉ giữ suffix có count >= 3 (đủ để thành convention)

QUERY Socraticode: codebase_context_search("naming convention class suffix")
  → Bổ sung các pattern UA có thể bỏ sót
```

#### 2B. Package / Layer Structure

```
CALL: get_domain_overview()
  → Liệt kê tất cả domain/layer hiện có
  → Map layer name → package path pattern

CALL: get_domain_detail(mỗi layer)
  → Hiểu responsibility của từng layer
  → Detect pattern: Clean Architecture / Hexagonal / Layered / CQRS

QUERY UA: query_nodes(type="package")
  → Extract package naming: {project_package_root}.{module}.{layer}
  → Identify depth convention (mấy cấp package)
```

#### 2C. Architecture Core Patterns & Dispatch Mechanisms

```
QUERY UA: query_nodes(type="class", filter="suffix IN [Controller, Command, Query, Handler, Processor]")
  FOR EACH node:
    CALL: get_relationships(node_id)
      → Khám phá cách Controller tương tác với Logic Layer: Controller gọi trực tiếp Handler/Service hay đi qua MessageBus / Dispatcher?
      → Controller có bắt buộc kế thừa Base class nào không (ví dụ: BaseWebController)?
    CALL: get_node_source(node_id)
      → Đọc actual implementation (chỉ signature, không toàn bộ body)
      → Nếu phát hiện CQRS (Controller -> MessageBus -> Command -> Handler), đánh dấu đây là kiến trúc cốt lõi với mức độ MANDATORY (upstream_constraints).
```

#### 2D. Upstream Conventions từ shared library

```
QUERY UA: query_nodes(filter="source_path STARTS_WITH {upstream_root}")
  → Lấy tất cả class/interface từ upstream library
  → GROUP BY type: Base*, I*, Abstract*, common annotations...
  → Đây là convention MANDATORY — project downstream PHẢI follow

CALL: get_node_detail(mỗi base class/interface quan trọng)
  → Extract: abstract method naming, field naming, annotation usage
  → Tag tất cả với origin: upstream, weight: mandatory
```

#### 2E. Test & Config Conventions

```
QUERY Socraticode: codebase_search("@Test class", limit=50)
  → Detect: test class suffix (*Test, *Spec, *IT)
  → Detect: test method naming (should_*, when_*_then_*, given_*)

QUERY UA: query_nodes(type="class", filter="name CONTAINS 'Config' OR name CONTAINS 'Properties'")
  → Extract config class naming pattern
  → Detect: @ConfigurationProperties prefix convention
```

---

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

Ghi ra `.knowledge-layer/templates/conventions.draft.yaml`:

```yaml
# conventions.draft.yaml
# Generated by convention-intelligence-builder
# Scanned at: {timestamp}
# Project: {project_root}
# Upstream: {upstream_root}
# Status: DRAFT — chưa được approve. Chạy /approve-conventions sau khi review.

meta:
  generated_at: "YYYY-MM-DDTHH:MM:SS"
  scanned_by: "convention-intelligence-builder"
  graph_stats:
    nodes_scanned: {n}
    upstream_nodes_scanned: {n}
  status: draft  # draft | approved | stale

# ─────────────────────────────────────────────
# SECTION 1: Naming Conventions
# weight: mandatory = từ upstream library, không override
#          recommended = project-native, có thể có exception có lý do
# confidence: high | medium | low
# evidence: 2-3 ví dụ class name thực tế
# ─────────────────────────────────────────────
naming:
  class_suffixes:
    # --- Entry mẫu (agent tự sinh từ scan, KHÔNG copy nguyên mẫu) ---
    - suffix: "{Suffix}"          # e.g. "ServiceImpl", "Handler", "Repository"
      layer: "{layer_name}"       # e.g. service, handler, repository
      weight: recommended         # mandatory | recommended
      origin: project             # project | upstream
      confidence: high            # high | medium | low
      count: {n}                  # Số class thực tế tìm thấy
      evidence:
        - "{ExampleClass1}"       # Tên class thật từ codebase
        - "{ExampleClass2}"
        - "{ExampleClass3}"
      note: ""                    # Ghi chú thêm (base class, pattern đặc biệt)

    # Thêm entry cho mỗi suffix có count >= 3
    # Agent tự detect từ scan: *Service, *ServiceImpl, *Repository, *Handler,
    #                          *Processor, *Entity, *Factory, *Controller, etc.

  method_naming:
    - pattern: "{methodPattern}"  # e.g. "findBy{Field}", "handle{Action}"
      layer: "{layer_name}"
      weight: recommended
      origin: project
      confidence: high
      evidence:
        - "{exampleMethod1}"
        - "{exampleMethod2}"

# ─────────────────────────────────────────────
# SECTION 2: Package Structure
# ─────────────────────────────────────────────
package_structure:
  root: "{project_package_root}"  # e.g. "com.example.myapp", "vn.company.project"
  depth: {n}                      # Số cấp package trung bình
  layers:
    # --- Entry mẫu (agent tự sinh từ scan) ---
    - name: "{layer_name}"        # e.g. controller, service, repository, handler
      path_pattern: "**.{layer_path}.**"
      responsibility: "{mô tả ngắn trách nhiệm layer}"
    # Thêm entry cho mỗi layer phát hiện được
  architecture_style: "{style}"   # layered | hexagonal | clean | cqrs
  note: ""

# ─────────────────────────────────────────────
# SECTION 3: Design Patterns Detected
# ─────────────────────────────────────────────
design_patterns:
  # --- Entry mẫu (agent tự sinh từ scan) ---
  - pattern: "{PatternName}"      # e.g. "Processor Chain", "Factory Interface", "Strategy"
    confidence: high
    origin: project               # project | upstream
    weight: recommended           # mandatory | recommended
    evidence:
      - "{ExampleClass1}"
      - "{ExampleClass2}"
    structure: "{NamingStructure}" # e.g. "{Action}{Domain}Processor extends BaseProcessor"
    note: ""

# ─────────────────────────────────────────────
# SECTION 4: Upstream Constraints ({upstream_library})
# Agent KHÔNG ĐƯỢC đề xuất thay đổi các convention này
# ─────────────────────────────────────────────
upstream_constraints:
  library: "{upstream_library}"   # e.g. "dvnh-common", "shared-kernel", "core-lib"
  path: "{upstream_root}"
  mandatory_interfaces:
    # --- Entry mẫu (agent tự sinh từ scan upstream) ---
    - name: "{InterfaceName}"     # e.g. "IBaseEntity<ID>", "IRepository<T>"
      must_implement: true
      note: ""
  mandatory_base_classes:
    - name: "{BaseClassName}"     # e.g. "BaseService", "AbstractHandler<Req,Res>"
      must_extend: true
      note: ""
  mandatory_annotations:
    # Chỉ ghi nếu scan upstream phát hiện custom annotation bắt buộc
    # - annotation: "@CustomTransactional"
    #   instead_of: "@Transactional"
    #   scope: "service layer"
  mandatory_interfaces_prefix:
    # e.g. "I{Domain}Factory" nếu upstream enforce prefix convention
    # - "{PrefixPattern}"

# ─────────────────────────────────────────────
# SECTION 5: Test Conventions
# ─────────────────────────────────────────────
test_conventions:
  class_suffix: "Test"
  method_pattern: "should_{action}_{condition}"
  confidence: medium
  evidence:
    - "should_throw_exception_when_limit_exceeded"

# ─────────────────────────────────────────────
# SECTION 6: Detected Exceptions & Inconsistencies
# Những nơi code KHÔNG follow convention — để agent biết mà không bị confuse
# ─────────────────────────────────────────────
exceptions:
  # --- Entry mẫu (agent tự sinh khi phát hiện inconsistency) ---
  - file: "{filename}"
    expected_convention: "{expected}"
    actual: "{actual_naming}"
    reason: "{lý do biết được hoặc 'Unknown'}"
    ticket: ""                    # ticket sẽ fix nếu có

# ─────────────────────────────────────────────
# SECTION 7: Low Confidence — Cần user xác nhận
# Agent không tự dùng các convention này cho đến khi được approve
# ─────────────────────────────────────────────
needs_review:
  - pattern: "{PatternDescription}"
    evidence_count: {n}
    examples:
      - "{ExampleClass1}"
    question: "{câu hỏi cụ thể cho user xác nhận}"
```

---

### Bước 5 — Summary Report cho User

Sau khi sinh file, xuất ra **bảng tóm tắt** để user biết cần review gì:

```
📋 Convention scan hoàn thành. Kết quả:

NAMING ({n} patterns):
  ✅ HIGH confidence ({n}): {suffix1}, {suffix2}, ...
  ⚠️  MEDIUM ({n}): {suffix3}, {suffix4}, ...
  ❓ LOW — cần xác nhận ({n}): {suffix5}, ...

UPSTREAM CONSTRAINTS từ {upstream_library} ({n} mandatory):
  🔒 {BaseClass1}, {Interface1}, ...

EXCEPTIONS phát hiện ({n}):
  ⚠️  {filename} — {mô tả vi phạm}

NEEDS REVIEW ({n} câu hỏi):
  ❓ {pattern} — {lý do cần xác nhận}

→ File đã được ghi tại: .knowledge-layer/templates/conventions.draft.yaml
→ Mở file, review và edit trực tiếp trong IDE.
→ Khi xong: chạy /approve-conventions để commit chính thức.
```

---

### Bước 6 — /approve-conventions Workflow

Khi user chạy `/approve-conventions`:

```
1. VALIDATE conventions.draft.yaml:
   - File tồn tại và parse được (valid YAML)?
   - status vẫn là "draft"?
   - Không có field bắt buộc nào bị xoá?
   → Nếu fail: báo lỗi cụ thể, không tiếp tục.

2. CROSS-CHECK với knowledge-snapshot.md:
   - Có entry nào trong conventions mâu thuẫn với snapshot không?
   - Ví dụ: snapshot ghi "{PatternA}" nhưng conventions ghi "{PatternB khác}"
   → Nếu có conflict: list ra, hỏi user chọn source of truth.

3. PROMOTE:
   - Rename: conventions.draft.yaml → conventions.yaml
   - Update metadata:
       status: approved
       approved_at: {timestamp}
   - GIỮ conventions.draft.yaml như là backup (đổi tên thành conventions.draft.{timestamp}.yaml.bak)

4. UPDATE context-loader priority:
   - conventions.yaml được nạp ở P3 cùng knowledge-snapshot.md
   - Ghi vào AGENT_TRANSPARENCY: "[x] conventions.yaml loaded"

5. GHI vào AGENT_TRANSPARENCY hiện tại:
   - "[x] convention-intelligence-builder: scan + approve"
   - Số patterns approved, số upstream constraints

6. NOTIFY user:
   "✅ conventions.yaml đã được commit.
    Agent sẽ dùng {n} naming conventions và {n} upstream constraints
    từ phiên làm việc tiếp theo."
```

---

## 5. Khi conventions.yaml đã có — Re-scan Policy

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

## 6. Cách Agent Dùng conventions.yaml Sau Khi Approve

Sau khi approved, agent phải:

- Khi sinh spec (Pha 2): đọc conventions.yaml trước khi đề xuất tên class/method.
- Khi `architecture-reviewer` phát hiện tên class trong REQUIREMENT không khớp convention → ghi warning vào EXPLORE_CONTEXT.
- Khi `codebase-explorer` tìm module → ưu tiên match với layer pattern trong `package_structure`.
- **KHÔNG override** `upstream_constraints` dù user yêu cầu — ghi rõ lý do từ chối nếu bị yêu cầu.

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
