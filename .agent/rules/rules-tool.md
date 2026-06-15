# rules-tool.md — Tool Rules (MCP & Tool Permissions)

> Sub-file của RULES.md. Đọc qua manifest `RULES.md`.

---

## 3. Tool Rules — Quyền với MCP & tool

### R-Tool-1: db-explorer chỉ đọc

- `db-explorer` chỉ được:
  - Đọc metadata (schema, constraint, trigger/procedure, index, view…).
  - Đọc sample data **không PII**, với limit nhỏ.
- Cấm:
  - Sinh hoặc chạy lệnh DDL/DML thay đổi dữ liệu/schema từ skill này.

### R-Tool-2: codebase access an toàn

- `codebase-explorer` và Socraticode chỉ được:
  - Đọc file, tìm symbol, call graph.
- Mọi thao tác **ghi** vào code phải đi qua:
  - Spec đã được chấp thuận.
  - Pha `/task apply`.

### R-Tool-3: OpenSpec apply có kiểm soát

- `/opsx:apply` chỉ được gọi khi:
  - Có spec tương ứng với ticket (sinh từ `/task spec`).
  - User đã được tóm tắt file/module bị chạm và xác nhận rõ ràng.

### R-Tool-4: Understand-Anything (UA)

- UA chỉ được dùng để:
  - Xây dựng/truy vấn knowledge graph về code, không thay đổi code.
- Không ép chạy `/understand` mỗi task:
  - Chỉ gợi ý khi repo chưa có graph hoặc sau refactor lớn.
- Nếu không có UA:
  - Các kết luận kiến trúc phải hạ Độ tin cậy (xem Architecture Rules).
- UA skills (`/understand-chat`) là **secondary** cho KG MCP Server (xem R-Tool-5).

### R-Tool-5: Knowledge Graph MCP (`understand-anything`)

- KG MCP Server chỉ được dùng để:
  - Truy vấn/đọc knowledge graph, domain graph, và source code.
  - Không thay đổi code.
- **Ưu tiên KG tools trước UA skills** cho truy vấn có cấu trúc:
  - `query_nodes`, `get_node_detail`, `get_node_source`
  - `get_relationships`, `trace_call_chain`, `find_impact`
  - `get_domain_overview`, `get_domain_detail`
  - `get_layer_info`, `find_entry_points`, `get_tour`
- UA skills (`/understand-chat`) chỉ dùng khi:
  - Câu hỏi open-ended, cần reasoning.
  - KG graph chưa có hoặc quá cũ.
- `get_node_source` tuân thủ R-Data-1:
  - Không log raw PII từ source code vào context files.
- Khi ghi vào `EXPLORE_CONTEXT`, **luôn kèm node_id** cho các component quan trọng:
  - Cho phép skill downstream dùng `get_node_source(node_id)` trực tiếp.

### R-Tool-5b: Cấm dùng grep/file-search thô khi UA graph available

- Khi cần khảo sát codebase (trong `codebase-explorer` hoặc bất kỳ pha nào của `/task`):
  - **Bước bắt buộc đầu tiên**: Gọi `get_graph_stats` để kiểm tra graph tồn tại và còn mới.
  - **Nếu graph available** (tồn tại, không quá cũ):
    - **Không được** dùng `grep_search`, `read_file`, `list_files` như nguồn chính để tracing dependency.
    - **Phải** dùng KG tools: `query_nodes` → `get_node_source` → `get_relationships` / `trace_call_chain`.
    - Grep/file-search chỉ được dùng như **supplement** (xác nhận chi tiết nhỏ sau khi đã có graph context).
  - **Nếu graph không available hoặc quá cũ**:
    - Ghi vào AGENT_TRANSPARENCY: "KG graph unavailable — dùng grep/search với độ tin cậy TRUNG BÌNH".
    - Hạ Độ tin cậy kiến trúc xuống TRUNG BÌNH (theo R-Arch-1).
    - Gợi ý user chạy `/understand` để rebuild graph.
- Lý do: Biết tên class cụ thể không đủ — blast-radius (vùng ảnh hưởng) chỉ thấy được qua dependency graph, không phải grep kết quả trực tiếp.


### R-Tool-6: Agent Memory MCP — Ranh giới sử dụng

Các tool MCP `agent-memory` chỉ là **lớp truy xuất phụ**.
Chúng bổ sung — không bao giờ thay thế — Bootstrap Protocol, thứ tự ưu tiên context-loader P1→P4,
hay `knowledge-snapshot.md` với tư cách nguồn sự thật chính thức.

**Bootstrap PHẢI hoàn tất (§1 AGENTS.md) trước khi gọi bất kỳ memory tool nào.**

#### Danh sách tool được phép

| Tool | Quyền truy cập | Budget |
|------|----------------|--------|
| `memory_smart_search` | ✅ Được phép | Tính vào memory budget |
| `memory_recall` | ✅ Được phép | Tính vào memory budget |
| `memory_sessions` | ✅ Được phép | **Miễn** — chỉ chẩn đoán |
| `memory_audit` | ✅ Được phép | **Miễn** — chỉ chẩn đoán |
| `memory_health` | ✅ Được phép | **Miễn** — kiểm tra hạ tầng |
| `memory_save` | ⛔ Chỉ qua `knowledge-curator` post-task hook | 1 lần ghi / Pha 3 |
| `memory_governance_delete` | ⛔ Không bao giờ (chỉ admin thủ công) | — |

`memory_sessions`, `memory_audit`, và `memory_health` là diagnostic tools — không ảnh hưởng reasoning, miễn khỏi memory budget.

#### Ngữ cảnh sử dụng được phép

- **Pha 1 exploration**: agent phát hiện module/table/service trong `REQUIREMENT.md` trùng với archive cũ → đề xuất `memory_smart_search` trước khi thực thi; ghi tín hiệu trong `AGENT_TRANSPARENCY.md`.
- **Trước spec (Pre-spec)**: `memory_recall` để tra cứu quyết định kiến trúc trước đó.
- **Sau task (Pha 3)**: `memory_save` chỉ qua `knowledge-curator` post-task hook.

#### Xử lý xung đột

Nếu kết quả từ agent-memory mâu thuẫn với `knowledge-snapshot.md`,
snapshot thắng vô điều kiện (R-KL-3).

#### Yêu cầu minh bạch (R-Obs-1)

Khi kết quả memory ảnh hưởng đến reasoning, agent PHẢI ghi vào `AGENT_TRANSPARENCY.md`:
- Tool đã gọi
- Query đã dùng
- Tóm tắt kết quả
- Độ tin cậy: `CAO | TRUNG-BÌNH | THẤP`
- Ghi chú: `agent-memory recall — ảnh hưởng reasoning`

#### Bảo vệ đường ghi (Write-path guard)

Gọi `memory_save` hoặc `memory_governance_delete` ngoài `knowledge-curator` post-task hook là **CẤM**.
Agent không được auto-save memory trong exploration, spec, hoặc apply phases.

---
