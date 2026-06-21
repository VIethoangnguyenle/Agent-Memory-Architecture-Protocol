# Memory Tool Capability Templating + ranh giới provider agentmemory

**Ngày:** 2026-06-21
**Trạng thái:** Design (chờ review)
**Mã:** C-27 (nối tiếp C-26 db-query templating)
**Nguồn:** phiên brainstorming 2026-06-21; nền tảng [AMAP-v3-assessment.md](../../AMAP-v3-assessment.md) §W5/§7-SP2 và spec [2026-06-19-agent-memory-mcp-capability-design.md](2026-06-19-agent-memory-mcp-capability-design.md).

---

## 1. Vấn đề

Memory tool layer của AMAP đang ở trạng thái **nửa-trừu-tượng**:

- **Đã xong (spec 2026-06-19):** `agent-memory` là capability chọn được lúc init (`provides: memory`), runtime degrade sạch khi vắng, ranh giới thẩm quyền rõ (advisory < `knowledge-snapshot.md`).
- **Còn lock-in:** tên tool **concrete** của agentmemory (`memory_smart_search`, `memory_recall`, `memory_sessions`, `memory_audit`, `memory_health`, `memory_save`, `memory_governance_delete`) bị **hardcode literal** trong [rules-tool.md](../../../.amap/rules/rules-tool.md) (R-Tool-6, bảng quyền), [m7-memory-push.md](../../../.amap/skills/knowledge-curator/references/m7-memory-push.md) và [bootstrap.md](../../../.amap/procedures/bootstrap.md). File M7 còn ghi thẳng *"Gọi `memory_save` (native — không cần mapping)"*.

Đây là chính bệnh **W5 (coupling ở tầng tool)**: PR C-26 đã đưa `db_query` qua lớp `{{ tools.* }}`, nhưng memory thì bỏ qua hẳn lớp đó. Tên tool AMAP hardcode **trùng khít 1:1** API của `agentmemory` → đổi provider là mọi rule/skill gãy.

**Câu hỏi đi kèm (đã chốt trong brainstorm):** có bundle `agentmemory` vào AMAP không? → **Không.** Xem §4.

## 2. Bản chất (định vị, không đổi)

Giữ nguyên hai trục đã chốt ở spec 2026-06-19:

- **Thẩm quyền:** agent-memory = kinh nghiệm advisory; khi mâu thuẫn, kiến thức chính (`knowledge-snapshot.md`, db-explorer, KG) **thắng tuyệt đối** (R-KL-3). Spec này KHÔNG đụng.
- **Cấu hình:** selectable + degrade. Spec này KHÔNG đụng.

Spec này chỉ sửa **trục biểu diễn tool**: thay tên literal bằng abstract op, đúng pattern C-26.

## 3. Phạm vi

**Trong phạm vi:**

1. Khai báo các abstract memory op trong tool layer ([base.py](../../../cli/platforms/base.py)) + map ở cả 5 platform.
2. Refactor mọi tham chiếu tên tool memory literal trong file templated → `{{ tools.dynamic_memory_* }}`.
3. Gỡ câu *"native — không cần mapping"* trong M7.
4. Ghi rõ ranh giới provider: agentmemory **không** bundle, project cuối cài **MCP-only** (tắt auto-capture hooks). Tài liệu hoá thành một setup recipe.
5. Test phần CLI/platform + verify không còn literal sót.

**Ngoài phạm vi:**

- Đổi semantics recall/save, memory budget numbers, hay ranh giới thẩm quyền (đã chốt ở spec 2026-06-19).
- Triển khai/host server agentmemory thật.
- Auto-install agentmemory từ AMAP (cố tình KHÔNG làm — §4).
- Map provider thứ 2 / file `*.adapter.yaml` riêng (defer tới khi có provider #2).

## 4. Quyết định nền: KHÔNG bundle agentmemory vào AMAP

`agentmemory` chỉ được dùng ở **project cuối**, **không** đặt vào template/cli của AMAP. Lý do:

| Lý do | Chi tiết |
|---|---|
| Phá portability | Bundle 1 provider concrete = tái tạo đúng lock-in C-27 đang gỡ; AMAP phải phụ thuộc capability trừu tượng. |
| Lệch stack | agentmemory = Node ≥20 + binary Rust `iii-engine` (50–100MB) + embedding model (~30–50MB), chạy server nền (cổng 3111–3113, 49134). AMAP cli = Python. |
| Sai tầng vòng đời | agentmemory là server **dùng-chung cấp máy/người dùng** ("all agents share the same memory server") — tài liệu gốc nói thẳng *"fundamentally incompatible with per-project vendoring"*. AMAP scaffold per-project. |
| Xung đột governance | `agentmemory connect` mặc định cài **12 auto-capture hooks** bắt memory trên mọi tool-use, không cần hành động — NGƯỢC HẲN governance gated của AMAP (M7: 1 save/task, 3 tầng lọc, no-PII, top-K). Auto-capture sẽ ghi đúng thứ AMAP cấm. |
| Vốn optional | Capability `memory` đã optional; bundle mâu thuẫn. |

**Cách dùng đúng ở project cuối (MCP-only, hooks OFF):**

```
npx -y @agentmemory/mcp        # chỉ MCP shim — KHÔNG cài 12 hooks
```
hoặc thêm thủ công block `mcpServers` vào config platform; **KHÔNG** chạy `agentmemory connect --with-hooks`, **bỏ** 15 skill của agentmemory (chồng lấn knowledge-curator/bootstrap). AMAP giữ toàn quyền memory governance qua M7.

→ AMAP ship: **một setup recipe** (markdown) mô tả cách này; KHÔNG ship engine. Vị trí đề xuất: `.amap/profiles/agent-memory-setup.md` (dùng thư mục `profiles/` đã reserve ở SP0). State agentmemory nằm ở `~/.agentmemory/` — **không commit vào repo** (khớp nguyên tắc sẵn có).

## 5. Thiết kế

### Phần 1 — Abstract memory ops trong tool layer

Theo đúng precedent `db_query`: abstract op nằm trong **`REQUIRED_TOOL_KEYS`** (không phải `OPTIONAL_TOOL_KEYS`), map ở **mọi** platform. Lý do bắt buộc REQUIRED: các tên này được tham chiếu trong **rule core luôn render** (R-Tool-6 luôn ship), nên `{{ tools.* }}` phải luôn resolve — nếu để OPTIONAL và một platform quên map, `StrictUndefined` sẽ làm render fail. `db_query` (MCP `db-remote` cũng optional) đã theo đúng logic này.

Thêm 7 op vào [base.py](../../../cli/platforms/base.py) `REQUIRED_TOOL_KEYS`. Prefix `dynamic_memory_` để khẳng định bản chất episodic/advisory, phân biệt rõ với repo knowledge.

| Abstract op | Tool concrete (provider) | Semantic R-Tool-6 |
|---|---|---|
| `dynamic_memory_search` | `memory_smart_search` | read — tính budget |
| `dynamic_memory_recall` | `memory_recall` | read — tính budget |
| `dynamic_memory_sessions` | `memory_sessions` | diagnostic — miễn budget |
| `dynamic_memory_audit` | `memory_audit` | diagnostic — miễn budget |
| `dynamic_memory_health` | `memory_health` | infra probe — miễn budget |
| `dynamic_memory_save` | `memory_save` | write — chỉ qua M7, 1/Pha 3 |
| `dynamic_memory_forget` | `memory_governance_delete` | admin-only — agent không gọi |

Map ở 5 platform theo đúng `mcp_tool_prefix` của từng platform (form, không đổi tên tool):

| Platform | prefix | Ví dụ `dynamic_memory_save` → |
|---|---|---|
| claude-code | `mcp__` | `mcp__agent-memory__memory_save` |
| antigravity | `mcp_` | `mcp_agent-memory_memory_save` |
| cursor | (bare) | `memory_save` |
| codex | (bare) | `memory_save` |
| generic | (bare) | `memory_save` |

> Khác `db_query` (map tới **server name** `db-remote` vì chỉ cần tham chiếu server): memory cần **tool-level** vì 7 tool có quyền khác nhau (search vs save vs delete) — giống cách socraticode map tool-level.

### Phần 2 — Refactor file templated dùng abstract op

Grep xác nhận **5 file templated** chứa tên tool literal — cả 5 đều phải refactor:

- **[rules-tool.md](../../../.amap/rules/rules-tool.md)** R-Tool-6: bảng quyền + ngữ cảnh + write-path guard + degrade → thay mọi tên literal bằng `{{ tools.dynamic_memory_* }}`. Giữ nguyên semantic (budget, restricted, admin-only, conflict→snapshot).
- **[rules-exec.md](../../../.amap/rules/rules-exec.md)** (memory budget): `memory_smart_search`/`memory_recall` (tính budget) + `memory_sessions`/`memory_audit`/`memory_health` (miễn) → abstract op tương ứng.
- **[m7-memory-push.md](../../../.amap/skills/knowledge-curator/references/m7-memory-push.md)**: thay `memory_save`/`memory_smart_search` bằng abstract op; **gỡ** tiêu đề *"Gọi `memory_save` (native — không cần mapping)"* → *"Gọi `{{ tools.dynamic_memory_save }}`"*.
- **[knowledge-curator/SKILL.md](../../../.amap/skills/knowledge-curator/SKILL.md)**: thay tham chiếu tên tool memory literal → abstract op.
- **[bootstrap.md](../../../.amap/procedures/bootstrap.md)**: probe `memory_health` → `{{ tools.dynamic_memory_health }}`.
- Dòng degrade chuỗi cố định (`agent-memory unavailable — skip recall/save`) **giữ nguyên literal** — nó là thông điệp log, không phải lệnh gọi tool, và gate-check whitelist theo chuỗi đó.

### Phần 3 — Promote-to-knowledge KHÔNG phải provider op

Hành vi "đưa kinh nghiệm ổn định vào repo knowledge" là `knowledge-curator` ghi vào `knowledge-snapshot.md` — **governance core của AMAP**, KHÔNG phải tool agentmemory. → KHÔNG thêm abstract op nào cho nó, KHÔNG map ra provider. Giữ nguyên là hành vi curator hiện có (YAGNI: không tạo abstraction mới).

### Phần 4 — Setup recipe (provider boundary)

Tạo `.amap/profiles/agent-memory-setup.md`: lệnh `npx -y @agentmemory/mcp`, mẫu block `mcpServers`, cảnh báo "KHÔNG `connect --with-hooks`, KHÔNG dùng 15 skill agentmemory, KHÔNG commit `~/.agentmemory/`". Recipe là tài liệu tĩnh; không phải executable, không auto-run.

### Phần 5 — Testing & verify

- [cli/tests/](../../../cli/tests/): assert 7 `dynamic_memory_*` op có trong `REQUIRED_TOOL_KEYS`; `validate_tool_mapping()` pass cho cả 5 platform (map đủ); `build_render_context` đưa op vào namespace `tools`.
- Snapshot tests: cập nhật nếu output render đổi.
- Verify de-hardcode: grep toàn `.amap/` (file templated) → **0** literal `memory_smart_search|memory_recall|memory_sessions|memory_audit|memory_health|memory_save|memory_governance_delete` ngoài (a) platform mapping trong `cli/`, (b) dòng degrade cố định. `verify_no_unresolved` (đã có) đảm bảo không còn `{{ }}` sót sau init.

## 6. Tiêu chí thành công

- 7 abstract memory op trong `REQUIRED_TOOL_KEYS`, map ở cả 5 platform; `pytest` xanh.
- Render init (có agent-memory): `{{ tools.dynamic_memory_save }}` → tên tool đúng prefix từng platform; 0 marker sót.
- Render init (không agent-memory): vẫn render OK (op vẫn map, runtime degrade lo phần vắng) — không lỗi.
- 0 literal tool name memory trong file templated (trừ dòng degrade); M7 không còn câu "native — không cần mapping".
- `.amap/profiles/agent-memory-setup.md` mô tả cài MCP-only, hooks OFF.
- R-Tool-6 semantic (budget/restricted/admin/conflict) không đổi.

## 7. Rủi ro

| Rủi ro | Giảm thiểu |
|---|---|
| `StrictUndefined` gãy render khi quên map | Để op trong REQUIRED → `validate_tool_mapping` fail sớm, rõ ràng, trước render |
| Tên tool agentmemory đổi giữa version | Đúng lý do cần lớp này — sửa 1 chỗ (mapping) thay vì N rule |
| Lẫn promote-to-knowledge vào provider mapping | §3 ghi rõ: core governance, không map |
| Over-engineer adapter.yaml khi mới 1 provider | Defer file riêng; dùng `tool_mapping` tới khi có provider #2 |
| Sót literal khi refactor | §5 grep là hard gate trước commit |

## 8. Không phá vỡ điều gì

- Semantic R-Tool-6, memory budget (rules-exec.md), 3 tầng lọc M7, ranh giới thẩm quyền R-KL-3: **không đổi**.
- Cơ chế capability/degrade của spec 2026-06-19: **không đổi** (chỉ thay biểu diễn tool).
- `db_query` và mọi abstract op hiện có: không ảnh hưởng.
- Không thêm dependency, không bundle engine, không đụng knowledge layer.
