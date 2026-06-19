# Agent Memory — MCP Capability tùy chọn + định vị vai trò

**Ngày:** 2026-06-19
**Trạng thái:** Design (chờ review)

## Vấn đề

`agent-memory` (MCP server, Qdrant-backed) được rules và skill tham chiếu như thể luôn
khả dụng, nhưng **không** nằm trong danh sách MCP cho chọn lúc `amap init`.

Cụ thể, `mcp_capabilities` trong [plugin-manifest.yaml](../../../cli/plugin-manifest.yaml)
chỉ có 4 server: `socraticode`, `understand-anything` (`code_exploration`), `db-remote`
(`db_access`), `confluence` (`document_search`). Không có `agent-memory`.

Hệ quả là một bất đối xứng:

- `db-explorer` / `codebase-explorer` được gate bằng `requires_capability` → không chọn MCP
  thì skill không ship.
- `knowledge-curator` (gọi `memory_save` ở hook M7) **luôn ship vô điều kiện**, và R-Tool-6
  ([rules-tool.md](../../../.amap/rules/rules-tool.md)) điều phối tool `agent-memory` như thể
  luôn có sẵn — dù init không cho cấu hình nó.

Đồng thời, wording hiện tại gọi agent-memory là *"lớp truy xuất phụ"*, dễ bị hiểu nhầm là
"kém quan trọng" thay vì mô tả đúng bản chất.

## Bản chất của agent-memory (định vị)

Hai trục độc lập:

- **Thẩm quyền (authority):** agent-memory là **lớp kinh nghiệm dài hạn tham khảo
  (advisory)** — những gì agent đã đúc kết và lưu lên Qdrant *sau* các task trước
  ("trước đây TỪNG làm thế nào"). Nó **không phải kiến thức chính** về hệ thống hiện tại.
  Kiến thức chính = `knowledge-snapshot.md`, `db-explorer`, KG. Khi mâu thuẫn, **kiến thức
  chính thắng tuyệt đối** (R-KL-3, giữ nguyên).
- **Cấu hình (config):** ở trục này agent-memory *nên* được đối xử ngang db-remote/UA —
  tức **chọn được lúc init + degrade sạch khi vắng mặt**. Selectable ≠ authoritative.

Thiết kế này sửa trục cấu hình (lỗ hổng kỹ thuật) và làm sắc trục thẩm quyền (wording),
**không** nâng agent-memory lên ngang hàng thẩm quyền với kiến thức chính.

## Phạm vi

**Trong phạm vi:**

1. Thêm `agent-memory` thành MCP capability tùy chọn trong manifest.
2. Runtime degrade sạch khi không chọn (cơ chế giống KG).
3. Làm sắc wording R-Tool-6 đúng bản chất "kinh nghiệm tham khảo dài hạn".
4. Test phần CLI/manifest.

**Ngoài phạm vi:** triển khai/host MCP server agent-memory thật; thay đổi semantics
recall/save; thay đổi memory budget numbers.

## Thiết kế

### Phần 1 — Định vị khái niệm (wording)

Trong [rules-tool.md](../../../.amap/rules/rules-tool.md) R-Tool-6, thay câu mở đầu
*"chỉ là lớp truy xuất phụ"* bằng định nghĩa rõ:

> `agent-memory` là **lớp kinh nghiệm dài hạn** — những gì agent đã đúc kết và lưu lên
> Qdrant *sau* các task trước. Dữ liệu mang tính **tham khảo/advisory** ("trước đây TỪNG
> làm thế nào"), **không phải kiến thức chính** về hệ thống hiện tại. Khi mâu thuẫn với
> kiến thức chính (`knowledge-snapshot.md`, db-explorer, KG), **kiến thức chính thắng
> tuyệt đối**.

Giữ nguyên toàn bộ ràng buộc hiện có: bảng quyền tool, write-path guard, conflict→snapshot
wins. Chỉ thêm 2–3 dòng định nghĩa. Không sửa thành "ngang hàng authority".

### Phần 2 — Capability model (init cho chọn được)

Thêm vào `mcp_capabilities` trong [plugin-manifest.yaml](../../../cli/plugin-manifest.yaml):

```yaml
  agent-memory:
    provides: memory
    display: "Agent Memory — Kinh nghiệm dài hạn (Qdrant, tham khảo sau task)"
```

→ Xuất hiện trong multi-select lúc `amap init` ([init.py](../../../cli/commands/init.py)),
và được ghi vào `mcps:` của `resolved-config.yaml`
([scaffold.py](../../../cli/scaffold.py) `generate_resolved_config`).

**Quyết định thiết kế:** capability `memory` **chỉ dùng để chọn + ghi config**, KHÔNG dùng
làm `requires_capability` gate file nào. `knowledge-curator` còn nhiều nhiệm vụ khác
(snapshot/reset) nên vẫn ship vô điều kiện — việc bật/tắt memory xử lý ở **runtime**
(Phần 3), không loại trừ lúc scaffold. Đây là điểm khác với KG: `understand-anything` vừa
là capability vừa là `requires_capability` của `codebase-explorer`; còn `memory` chỉ là
selection-only.

### Phần 3 — Runtime degrade (cơ chế A)

Một nguồn sự thật duy nhất: `resolved-config.yaml → mcps`. Các touch-point:

1. **[bootstrap.md](../../../.amap/procedures/bootstrap.md)** — mở rộng MCP probe (hiện chỉ
   ví dụ KG): nếu `mcps` có `agent-memory` → probe `memory_health`, ghi
   `🔌 MCP: agent-memory: healthy`. Nếu vắng → dòng degrade chuẩn
   `agent-memory unavailable — skip recall/save`.
2. **R-Tool-6** — thêm nhánh: memory không có trong config → mọi
   `memory_smart_search`/`memory_recall` bị **skip**, ghi degrade vào
   `AGENT_TRANSPARENCY.md` (không bịa kết quả).
3. **[m7-memory-push.md](../../../.amap/skills/knowledge-curator/references/m7-memory-push.md)**
   — thêm **Tầng 0 (pre-check)** trước Tầng 1: nếu không có capability `memory` →
   `[M7-SKIP] agent-memory chưa cấu hình`, bỏ qua toàn bộ push.
4. **[rules-exec.md](../../../.amap/rules/rules-exec.md)** (memory budget, dòng 75) — ghi chú
   budget chỉ áp dụng khi memory khả dụng.
5. **Verify:** [gate-check mcp-status](../../../.amap/tools/gate-check/) — kiểm tra có
   whitelist dòng degrade theo chuỗi cố định không; nếu có, thêm mẫu dòng degrade của
   agent-memory để gate pass.

### Phần 4 — Testing

- [cli/tests/test_init.py](../../../cli/tests/test_init.py) /
  [test_scaffold.py](../../../cli/tests/test_scaffold.py): assert `agent-memory` có trong
  `mcp_capabilities` và chọn được; khi chọn → `resolved-config.mcps` chứa nó; khi không
  chọn → init không lỗi, không có nó.
- Snapshot tests ([cli/tests/snapshots/](../../../cli/tests/snapshots/)): cập nhật nếu output
  init thay đổi.
- Không thêm test cho hành vi runtime degrade (đó là instruction cho agent, không phải code)
  — chỉ verify phần CLI/manifest.

## Tiêu chí thành công

- `amap init` hiển thị `agent-memory` trong multi-select MCP.
- Chọn agent-memory → `resolved-config.yaml` có `agent-memory` trong `mcps`.
- Không chọn → init chạy bình thường; bootstrap/R-Tool-6/M7 ghi degrade thay vì giả định
  tool tồn tại.
- R-Tool-6 mô tả đúng bản chất "kinh nghiệm tham khảo dài hạn — dưới kiến thức chính".
- `pytest` xanh.
