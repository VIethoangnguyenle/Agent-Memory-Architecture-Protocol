---
name: codebase-explorer
version: '1.0'
description: >
  Khám phá codebase bằng Socraticode + Understand-Anything để map REQUIREMENT → module/service/file liên quan.
  Dùng khi cần tìm module, file, dependency liên quan đến requirement hiện tại.
  KHÔNG dùng cho: khám phá DB schema (→ db-explorer),
  review kiến trúc/rủi ro (→ architecture-reviewer), sinh spec (→ openspec-propose).
pre_conditions:
  - file: .knowledge-layer/active/REQUIREMENT.md
    condition: not_skeleton
    on_fail: "ABORT — chạy requirement-analyst trước"
  - file: .knowledge-layer/active/EXPLORE_CONTEXT.md
    condition: exists
    on_fail: "WARN — EXPLORE_CONTEXT chưa có, tạo skeleton trước khi ghi"
---

# Codebase Explorer

## 1. Mục tiêu

- Trả lời câu hỏi: **“Yêu cầu này chạm vào những phần code nào?”** ở mức module, service, file, symbol.
- Xây dựng bức tranh high-level về kiến trúc code liên quan tới REQUIREMENT để hỗ trợ:
  - `architecture-reviewer`
  - OpenSpec / propose
  - Ước lượng effort và rủi ro

Skill này chỉ tập trung vào **khảo sát và ghi nhận bối cảnh code**, không thay đổi code và không đề xuất giải pháp chi tiết.

---

## 2. Khi nào dùng

Dùng `codebase-explorer` khi:

- `/task` Pha 1 với input `HAS_TICKET` hoặc requirement đã tương đối rõ
- Nhánh ideation khi cần hiểu codebase hiện tại đang xử lý domain/use case nào
- Trước khi chạy:
  - `architecture-reviewer`
  - OpenSpec `/opsx:propose`

### KG-first cases

Nếu truy vấn thuộc một trong các nhóm sau, agent **phải dùng KG MCP Server trước** rồi mới được dùng Socraticode/grep/view file để kiểm tra chi tiết:

- Hỏi về flow nghiệp vụ end-to-end → `get_domain_detail`, `trace_call_chain`
- Hỏi về cross-module hoặc cross-service interaction → `get_relationships`, `get_layer_info`
- Hỏi về transaction base, ledger, reconciliation → `query_nodes` + `get_node_source`
- Hỏi về dependency chain hoặc high-level execution flow → `trace_call_chain`, `find_impact`

Trong các trường hợp này, **KG MCP Server là nguồn chính** để hiểu flow và dependency.
Socraticode/grep/view file chỉ là bước follow-up để xác nhận chi tiết implementation.

Agent không được tự ý bỏ qua KG tools chỉ vì grep/search cho cảm giác nhanh hơn.

---

## 3. Input

- `.knowledge-layer/active/REQUIREMENT.md`
- (Tuỳ chọn) `.knowledge-layer/active/EXPLORE_CONTEXT.md`
- `.knowledge-layer/templates/knowledge-snapshot.md` (nếu có)
- Trạng thái tool:
  - Socraticode có khả dụng không
  - Repo có sử dụng Understand-Anything không
  - Graph UA đã được build trước đó chưa và còn tin cậy không

---

## 4. Output

Cập nhật `.knowledge-layer/active/EXPLORE_CONTEXT.md` với section:

```md
### Kiến trúc code hiện tại (codebase-explorer)

#### Entry points
- [node_id] Tên — mô tả ngắn

#### Service / module chính
- [node_id] Tên — vai trò [Synchronous API / Background Worker]

#### Data access / adapter
- [node_id] Tên — bảng/collection liên quan

#### Integration / event / job
- [node_id] Tên — loại (Kafka/gRPC/REST)

#### Quan hệ quan trọng
- source_node → relation → target_node

#### Độ tin cậy
- CAO / TRUNG BÌNH / THẤP, kèm giải thích ngắn
```

> [!IMPORTANT]
> Luôn ghi kèm `node_id` cho mỗi component quan trọng.
> Điều này cho phép `architecture-reviewer` và OpenSpec dùng `get_node_source(node_id)` để đọc code thực tế mà không cần search lại.

Chỉ ghi những gì cần để skill khác hiểu bối cảnh. Không dump toàn bộ call graph hoặc copy nguyên nội dung file.

---

## 5. Công cụ — Thứ tự ưu tiên

### 5.1 Primary: KG MCP Server (`understand-anything`)

KG MCP Server cung cấp truy vấn **có cấu trúc** vào knowledge graph + domain graph.
Đây là công cụ **ưu tiên số 1** cho mọi truy vấn codebase có tính structured.

| Tool | Khi nào dùng |
|------|-------------|
| `get_graph_stats` | **Luôn gọi đầu tiên** — kiểm tra graph health, freshness, node/edge count |
| `query_nodes` | Tìm module/file/class/function liên quan đến REQUIREMENT (fuzzy search, phân trang) |
| `get_node_detail` | Xem chi tiết node: layer, complexity, tags, relationship count |
| `get_node_source` | **Đọc source code thực tế** từ graph node — thay thế việc mở file riêng |
| `get_relationships` | Hiểu dependency giữa components (imports, calls, extends, implements) |
| `trace_call_chain` | Trace execution flow từ entry point xuống |
| `find_entry_points` | Tìm API endpoints / handlers (orphan functions có outgoing calls) |
| `find_impact` | Blast radius — xem thay đổi 1 node ảnh hưởng gì |
| `get_layer_info` | Hiểu kiến trúc layering (service, adapter, domain…) |
| `get_domain_overview` | High-level business domains và flows |
| `get_domain_detail` | Chi tiết business flow: entities, rules, steps |
| `get_tour` | Guided walkthrough — hữu ích khi onboarding hoặc cần bức tranh tổng thể |

**Workflow điển hình**:
```
get_graph_stats → query_nodes(keyword) → get_node_detail(id)
                                       → get_node_source(id)  ⭐ đọc code
                                       → get_relationships(id)
                                       → trace_call_chain(id)
```

### 5.2 Secondary: UA Skills (`/understand-chat`, `/understand-domain`)

UA skills dùng cho **câu hỏi open-ended**, cần reasoning mà KG tools không trả lời trực tiếp:

- "Tại sao flow này được thiết kế như vậy?"
- "So sánh 2 cách implement khác nhau của pattern X"
- "Giải thích tổng quan kiến trúc cho người mới"

> [!NOTE]
> Nếu KG graph chưa có hoặc quá cũ → UA skills trở thành primary.
> Khi đó, gợi ý user chạy `/understand` để rebuild graph.

#### `/understand`
- Chỉ dùng để build hoặc refresh global graph khi user chủ động hoặc khi thật sự cần.
- Không mặc định yêu cầu chạy cho mọi task.

#### `/understand-chat`
- Dùng khi cần hỏi câu hỏi mở hoặc cần graph-based reasoning phức tạp.
- Là **fallback** cho KG tools, không phải primary.

#### `/understand-domain` (tuỳ chọn)
- Dùng khi cần nhìn luồng nghiệp vụ hoặc domain flow ở mức tổng quát mà `get_domain_detail` chưa đủ.

### 5.3 Supplement: Socraticode

Dùng để:

- Semantic search code (khi KG query_nodes fuzzy search chưa đủ)
- Cross-check implementation sau khi đã có flow từ KG
- Tìm code patterns mà graph không index

### 5.4 Fallback: grep/search/view file

Nếu KG, UA, và Socraticode đều không khả dụng, fallback về grep/search/IDE navigation.
Khi fallback, phải ghi rõ hạn chế vào `.knowledge-layer/active/AGENT_TRANSPARENCY.md`.

---

## 6. Quy trình

### Bước 1 — Chuẩn bị từ REQUIREMENT

Đọc `.knowledge-layer/active/REQUIREMENT.md` và trích:

- Use case chính
- Entity/khái niệm chính
- Hành động chính liên quan tới code

Dùng các mục này làm từ khoá truy vấn.

### Bước 2 — Xác định phạm vi codebase

- Nếu monorepo:
  - Khoanh vùng module/service có khả năng liên quan dựa trên tên thư mục, tài liệu, `knowledge-snapshot.md`
- Nếu single service:
  - Ưu tiên các thư mục code chính như `src`, `app`, `domain`
- **Quan trọng**: Phân loại rõ tính chất của module/service liên quan là phục vụ API (Synchronous) hay xử lý nền (Background Worker / Kafka / Job) để các skill sau dễ dàng check Topology.

Ghi phạm vi khảo sát vào `.knowledge-layer/active/EXPLORE_CONTEXT.md`.

### Bước 3 — Kiểm tra trạng thái KG graph

1. Gọi `get_graph_stats` để kiểm tra:
   - Graph có tồn tại không (node count > 0)
   - Graph có đủ mới không (analyzedAt)
2. Nếu graph OK → dùng KG tools làm nguồn chính (Bước 4)
3. Nếu graph chưa có hoặc quá cũ:
   - Gợi ý user chạy `/understand` để rebuild graph
   - Trong lúc chờ, dùng Socraticode/search với độ tin cậy thấp hơn

Không mặc định yêu cầu rebuild graph cho mọi task.

### Bước 4 — Khảo sát bằng KG MCP Server

Nếu truy vấn thuộc nhóm `KG-first`, bước này là **bắt buộc**.

Dùng KG tools để:

- `query_nodes(keyword)` → tìm module/file/class liên quan đến REQUIREMENT
- `get_node_detail(id)` → xem layer, complexity, tags
- `get_node_source(id)` → **đọc code thực tế** để verify logic
- `get_relationships(id)` → hiểu dependency
- `trace_call_chain(id)` → trace flow từ entry point
- `get_domain_detail(domain_name)` → business flow, rules, steps
- `find_entry_points` → tìm API endpoints nếu chưa biết

Nếu cần câu hỏi open-ended, fallback sang `/understand-chat`.

### Bước 5 — Khảo sát bổ sung bằng Socraticode

Dùng Socraticode để:

- Xác nhận entry point cụ thể
- Tìm file, symbol, call site chính
- Làm rõ phần implementation mà UA đã chỉ ra
- Tìm impact area chi tiết hơn

Nếu truy vấn không thuộc nhóm `UA-first`, Socraticode có thể là điểm bắt đầu.  
Nếu truy vấn thuộc nhóm `UA-first`, Socraticode chỉ là bước follow-up sau UA.

### Bước 6 — Cross-check: Code thủ công + DB cross-reference

#### 6a — Đọc code thủ công (tuỳ chọn)

Nếu cần, đọc nhanh code ở một số file/symbol quan trọng để xác nhận:

- đúng use case
- rẽ nhánh logic chính
- flag/toggle quan trọng
- adapter/integration chính

Chỉ đọc phần cần thiết, không đọc toàn bộ codebase.

#### 6b — DB cross-reference (BẮT BUỘC khi code chạm data layer)

> [!IMPORTANT]
> Khi Bước 4–5 phát hiện code **chạm tới config tables, transaction metadata, hoặc state management** — nhận diện qua các pattern sau:
> - **Factory / Repository / DAO** đọc từ bảng config (`AD_*`, `CF_*`, `SYS_*`…)
> - **Entity / Model** map sang bảng transaction hoặc metadata
> - **Enum / Definition** resolve từ giá trị trong DB (ví dụ: `ServiceDefinition.fromServiceCode()`)
> - **Adapter / Client** gọi external service dựa trên config DB
>
> → Agent **PHẢI** gọi `db-explorer` hoặc dùng MCP `db-remote` trực tiếp để **verify data thực tế** trước khi ghi kết luận gap vào EXPLORE_CONTEXT.

**Lý do**: Chỉ nhìn code sẽ dẫn tới kết luận sai về scope thay đổi. Ví dụ: code có enum thiếu entry nhưng DB config đã sẵn sàng → gap thực tế nhỏ hơn nhiều so với suy luận từ code alone.

**Checklist tối thiểu khi trigger**:
1. Xác định bảng config/data liên quan từ Factory/Entity name.
2. Dùng `db-remote` kiểm tra: bảng có tồn tại không, data đã được seed chưa, constraint có phù hợp không.
3. Ghi kết quả verify vào EXPLORE_CONTEXT — rõ ràng phân biệt "đã có trong DB" vs "cần thêm/sửa".

**Nếu không thể kết nối DB** (MCP unavailable, thiếu quyền…):
- Ghi rõ hạn chế vào AGENT_TRANSPARENCY.
- Hạ độ tin cậy section DB xuống THẤP.
- Không được kết luận gap dựa trên suy luận khi có thể verify bằng DB.

### Bước 7 — Ghi vào EXPLORE_CONTEXT

Cập nhật section `Kiến trúc code hiện tại (codebase-explorer)` theo format chuẩn.

Nếu có khác biệt giữa KG và Socraticode:

- Ghi rõ điểm chưa nhất quán
- Đánh dấu cần kiểm tra sâu hơn
- Hạ độ tin cậy nếu cần

> [!IMPORTANT]
> Ghi kèm `node_id` cho mỗi entry point, service, adapter quan trọng để các skill downstream có thể gọi `get_node_source(id)` trực tiếp.

### Bước 8 — Cập nhật AGENT_TRANSPARENCY

Trong `.knowledge-layer/active/AGENT_TRANSPARENCY.md`:

- Đánh dấu đã dùng:
  - `codebase-explorer`
  - `Knowledge Graph MCP` — chi tiết từng tool:
    - `[ ] get_graph_stats`
    - `[ ] query_nodes`
    - `[ ] get_node_source`
    - `[ ] get_relationships / trace_call_chain`
    - `[ ] get_domain_detail`
    - `[ ] find_impact / find_entry_points`
  - `Understand-Anything (UA skills)` nếu có
  - `Socraticode` nếu có
- Ghi rõ:
  - tool nào không khả dụng
  - tool nào là nguồn chính (KG / UA / Socraticode)
  - có đang ở trạng thái `no graph` hay không

---

## 7. Lưu ý

- Giữ nội dung generic, không encode domain cụ thể.
- Không tự động chạy re-index hoặc thao tác nặng trên repo; chỉ gợi ý user khi cần.
- Với truy vấn flow/cross-module/transaction-base, không được bỏ qua KG tools chỉ vì grep/search cho cảm giác nhanh hơn.
- Ưu tiên `get_node_source` để đọc code thay vì mở file thủ công — giúp giữ context gọn và có node ID tracking.
- Skill này chỉ khám phá và ghi nhận codebase cho requirement hiện tại.
- Mọi đề xuất thay đổi kiến trúc hay implement chi tiết thuộc về `architecture-reviewer` và OpenSpec.
---

## Gotchas

- **[G1] Socraticode phải index trước**: `codebase_search` chỉ hoạt động sau khi `codebase_index` chạy xong 100%. Kiểm tra bằng `codebase_status` — nếu chưa indexed, gợi ý user chạy `/index-source`.
- **[G2] UA project name phải match chính xác**: `list_projects()` trả về project name — dùng tên đó cho mọi UA query. Đoán tên sẽ gây "project not found" error.
- **[G3] File watcher lag**: Nếu user vừa edit file, Socraticode file watcher có thể chưa bắt kịp (<5s delay). Khi search trả kết quả cũ cho file mới sửa, dùng `codebase_update` để force re-index file đó.
- **[G4] Symbol graph vs File graph**: UA có 2 loại graph — symbol-level (function/class) và file-level. Khi trace call chain, dùng symbol graph (`trace_call_chain`). Khi xem dependency, dùng file graph (`get_relationships`).
