# Canonical resolved-config: derive + unify (P2.3) — Design

> **Date:** 2026-06-21
> **Status:** Approved (design) — ready for implementation plan
> **Branch:** `canonical-resolved-config` (off `main`).
> **Lineage:** roadmap **P2.3** ("gom resolved-config về một vị trí canonical") + dashboard
> review 2026-06-20 bundle **S2** (`framework_root` default lệch giữa reader và orchestrator).
> Cross-pollinated from a study of `open-gsd/gsd-core` (canonical-path / immutable-tree
> pattern); see §7.

---

## 1. Context & problem

`resolved-config.yaml` được đọc bởi **hai phía** với mô hình khác nhau:

- **Agent runtime** (`rules-tool.md`, `bootstrap.md`, `m7-memory-push.md`, `meta-prompt.md`):
  prompt được render cho *một* platform cụ thể nên `{{ platform.framework_root }}` đã bake
  sẵn — agent **luôn biết** framework_root và đọc config ngay tại đó. **Không có**
  chicken-and-egg.
- **Python CLI** ([cli/scaffold.py](../../../cli/scaffold.py) `load_resolved_config`, 4 call
  site: `update`, `status`, `mcp/doctor`, `dashboard/reader`): chạy generic trên target bất
  kỳ, **không biết** platform → phải scan nhiều candidate. Đây là nơi chicken-and-egg tồn tại.

**Kết luận nền (định hình scope):** chicken-and-egg là *bất khả tiêu về bản chất* — vị trí
config phụ thuộc platform, mà platform lại nằm *trong* config. Nhưng nó **bị chặn trên**:
`framework_root` chỉ ∈ {`.amap`, `.agents`, `.claude`}, cả 3 đều **suy ra được từ registry
`PLATFORMS`**. Vì vậy "ép config về một vị trí vật lý duy nhất, tách khỏi framework_root" là
hướng **sai** — nó phá vỡ mô hình "config nằm cùng framework_root" mà agent dựa vào, kéo theo
phải re-template hàng loạt operational file + cây trong `meta-prompt.md`.

Khuyết tật **thật** không phải "có scan", mà là 3 điểm:

1. **Candidate hardcode** — `resolved_config_candidates`
   ([cli/scaffold.py:63-69](../../../cli/scaffold.py#L63-L69)) liệt kê 3 literal
   (`.agents`/`.claude`/`.amap`) thay vì derive từ `PLATFORMS` → drift khi thêm platform mới
   với root mới.
2. **Default fallback lệch nhau** — dashboard reader default `.amap`
   ([cli/dashboard/reader.py:68](../../../cli/dashboard/reader.py#L68)), orchestrator default
   `.agents` ([.amap/tools/microloop-orchestrator/orchestrator.py:103](../../../.amap/tools/microloop-orchestrator/orchestrator.py#L103)),
   `load_resolved_config` fallback `.amap`
   ([cli/scaffold.py:121](../../../cli/scaffold.py#L121)). Cả ba là "defensive-dead" (callers
   luôn truyền/ghi key) nhưng là bẫy semantic-drift.
3. **Ambiguity nhiều config** — đổi platform để lại config cũ; cả config cũ lẫn mới đều
   "match root của chính nó" → tie-break `valid[0]`
   ([cli/scaffold.py:129-134](../../../cli/scaffold.py#L129-L134)) có thể chọn config **cũ**.

## 2. Approach — A (Derive + Unify), KHÔNG dời file

Giữ config dưới `framework_root` (agent không đổi, không re-template), chỉ sửa tầng Python:
derive candidate từ registry, hợp nhất default về một hằng số canonical, và **enforce invariant
"đúng một config"** bằng sweep-on-write. Không migration ngoài luồng (config hiện hữu vẫn nằm
trong candidate set derived → vẫn tìm thấy).

**Đã loại — không làm:** dời config về `.amap/` cố định tách khỏi framework_root (phá mô hình
agent, blast radius lớn, ngược "Surgical Changes"). Xem §8.

## 3. Mechanism

### §3.1 — Single source cho canonical root
- Thêm `CANONICAL_FRAMEWORK_ROOT = ".amap"` vào [cli/__init__.py](../../../cli/__init__.py)
  (cạnh `FRAMEWORK_VERSION`).
- Test bất biến: `CANONICAL_FRAMEWORK_ROOT == get_platform("generic").framework_root` → hằng số
  không thể drift khỏi default thật của base/generic ([cli/platforms/base.py:133](../../../cli/platforms/base.py#L133)).

### §3.2 — Derive candidate từ registry (bỏ 3 literal)
`resolved_config_candidates`:
```python
def resolved_config_candidates(target: Path) -> List[Path]:
    from cli.platforms import PLATFORMS, get_platform
    roots = {get_platform(k).framework_root for k in PLATFORMS}        # {.amap,.agents,.claude}
    ordered = [CANONICAL_FRAMEWORK_ROOT, *sorted(roots - {CANONICAL_FRAMEWORK_ROOT})]
    return [target / r / "resolved-config.yaml" for r in ordered]
```
Thêm platform/root mới → candidate tự bao gồm. Canonical đứng đầu ⇒ thứ tự tất định.
Sửa luôn fallback [cli/scaffold.py:121](../../../cli/scaffold.py#L121) `expected_root = ".amap"`
→ `CANONICAL_FRAMEWORK_ROOT`.

### §3.3 — Diệt default-divergence (S2)
- **reader** ([cli/dashboard/reader.py:68](../../../cli/dashboard/reader.py#L68)):
  `resolved.get("framework_root", CANONICAL_FRAMEWORK_ROOT)` (import từ `cli`).
- **orchestrator** ([.amap/tools/microloop-orchestrator/orchestrator.py:103](../../../.amap/tools/microloop-orchestrator/orchestrator.py#L103)):
  **bỏ hẳn default** `framework_root=".agents"` → tham số bắt buộc. Lý do: orchestrator là
  runtime artifact standalone (`copy_dir`, chỉ import stdlib+yaml → **không** import được hằng
  số chung); không caller production nào dựa vào default (chỉ 2 test); một default sai trỏ
  `TASK_HANDOFF`/`TASK_RESULT` vào nhầm thư mục → fail-loud tốt hơn đoán im lặng. Cập nhật 2
  test ([.amap/tools/microloop-orchestrator/tests/test_runtime_contract.py](../../../.amap/tools/microloop-orchestrator/tests/test_runtime_contract.py))
  truyền `framework_root` tường minh.
  **Lưu ý Python:** `framework_root` đứng sau `execution_mode="subagent"`; bỏ default mà giữ
  nguyên thứ tự ⇒ `SyntaxError` (non-default sau default). Plan phải làm `framework_root`
  **keyword-only** (chèn `*,` trước nó) — không reorder positional để khỏi vỡ call-site khác.

### §3.4 — Enforce invariant "đúng một config" (sweep-on-write)
Trong `generate_resolved_config` ([cli/scaffold.py:72-91](../../../cli/scaffold.py#L72-L91)),
**sau** khi ghi config vào root active, xóa `resolved-config.yaml` ở các candidate root *khác*.
Guard (verify-before-delete) để delete an toàn:
1. Chỉ xét đúng path `resolved-config.yaml` trong các candidate root **≠ root active**.
2. Chỉ xóa nếu file parse được thành **AMAP-generated config** (`_read_resolved_config` trả
   `dict`, tức có key `resolved:`). Không bao giờ đụng file lạ trùng tên.
3. Best-effort: file không tồn tại / không đọc được → bỏ qua, không raise.

(Guard "skip in-repo" được xác nhận **thừa**: repo không track `resolved-config.yaml` nào;
verify ở (2) đã đủ chặn mọi xóa ngoài ý muốn.)

### §3.5 — `load_resolved_config` giữ deterministic, không cần mtime
Steady-state sau §3.4 chỉ còn ≤1 config nên tie-break hiếm khi chạy. Giữ logic preference hiện
có (ưu tiên config có vị trí khớp `framework_root` của chính nó), nhưng fallback giờ tất định
nhờ thứ tự canonical-first ở §3.2. Cho install **legacy đa-config** (chưa qua `update` để
sweep): load vẫn chọn tất định canonical-first thay vì ngẫu nhiên — không dùng mtime (tín hiệu
mong manh trong môi trường high-churn). Lần `amap update` kế tiếp sẽ sweep về single-config.

## 4. Files

- [cli/__init__.py](../../../cli/__init__.py) — thêm `CANONICAL_FRAMEWORK_ROOT`.
- [cli/scaffold.py](../../../cli/scaffold.py) — `resolved_config_candidates` derive;
  `load_resolved_config` fallback dùng hằng số; `generate_resolved_config` sweep-on-write.
- [cli/dashboard/reader.py](../../../cli/dashboard/reader.py) — default dùng hằng số.
- [.amap/tools/microloop-orchestrator/orchestrator.py](../../../.amap/tools/microloop-orchestrator/orchestrator.py)
  — bỏ default `framework_root`.
- [.amap/tools/microloop-orchestrator/tests/test_runtime_contract.py](../../../.amap/tools/microloop-orchestrator/tests/test_runtime_contract.py)
  — truyền `framework_root` tường minh.
- `cli/tests/*` — test mới (xem §5).

## 5. Test plan / acceptance

- **Hằng số bất biến:** `CANONICAL_FRAMEWORK_ROOT == get_platform("generic").framework_root`.
- **Derive candidate:** `resolved_config_candidates(target)` trả đúng `{root}/resolved-config.yaml`
  cho **mọi** root trong `{get_platform(k).framework_root for k in PLATFORMS}`, canonical đứng
  đầu. Thêm 1 platform giả lập root mới (hoặc parametrize) → candidate tự có.
- **Load đúng root:** với config đặt ở `.claude` (platform=claude_code), `load_resolved_config`
  chọn đúng nó; `framework_root` trả về = `.claude`.
- **Load đa-config tất định:** dựng 2 config (`.amap` generic + `.claude` claude_code) → load
  trả kết quả **tất định** (canonical-first), không phụ thuộc mtime.
- **Sweep-on-write:** sau `generate_resolved_config` cho claude_code khi đã có sẵn config ở
  `.amap` → chỉ còn `.claude/resolved-config.yaml`; file AMAP-generated ở `.amap` bị xóa;
  một file lạ **trùng tên** không-phải-AMAP-config (không có key `resolved:`) **không** bị xóa;
  file không liên quan khác giữ nguyên.
- **Divergence guard:** test assert reader và orchestrator không còn literal root default lệch
  canonical (orchestrator: gọi `initialize_runtime_queue` thiếu `framework_root` → `TypeError`,
  chứng minh default đã bỏ).
- **Golden snapshot (UP3):** [cli/tests/test_snapshots.py](../../../cli/tests/test_snapshots.py)
  **không đổi** — config vẫn render vào framework_root.
- **Regression callers:** `status` trên install không-config vẫn in cảnh báo "legacy"
  (load trả `None`); `update`/`doctor` vẫn resolve đúng.
- **Exit condition:** sau `amap init` rồi đổi platform + `amap update`, target chỉ chứa **đúng
  một** `resolved-config.yaml` (ở root active); `load_resolved_config` trả nó tất định.

## 6. Error handling

Giữ nguyên hành vi hiện có: không config → `load_resolved_config` trả `None`; YAML hỏng →
config đó bị skip. Sweep best-effort (missing/unreadable → bỏ qua). Không thêm exception path
mới ngoài việc orchestrator nay fail-loud khi thiếu `framework_root` (chủ đích).

## 7. Lineage — gsd-core cross-pollination

Pattern lấy từ [open-gsd/gsd-core](https://github.com/open-gsd/gsd-core)
`hooks/gsd-ensure-canonical-path.js`: tách rạch ròi **immutable framework tree** (máy quản,
canonical) khỏi **user/runtime artifacts** (giữ nguyên), và **self-heal** state lệch ở
boundary. Ở đây áp dụng có chọn lọc: "self-heal" = sweep-on-write hợp nhất về single-config;
"không đụng user artifact" = guard verify-AMAP-generated-before-delete. Không bê nguyên cỗ máy
symlink/consent của gsd-core (thừa cho AMAP — xem `amap-framework-generic-boundary`).

## 8. Non-goals / residual

- **Không dời config khỏi framework_root** (Approach C đã loại): sẽ phá mô hình agent đọc config
  tại `{{ platform.framework_root }}` và buộc re-template `rules-tool.md`/`bootstrap.md`/
  `meta-prompt.md`/… — blast radius lớn, ngược intent surgical.
- **Không xóa scan** hoàn toàn (Approach B pointer đã loại): chicken-and-egg là bất khả tiêu;
  scan-derived + single-config invariant là cách xử đúng, không cần thêm artifact pointer
  (nguồn drift mới).
- **Không dùng mtime** để tie-break (tín hiệu mong manh trong high-churn).
- **Không** đụng tầng capability/portability (P2.1/UP2) — độc lập, vẫn gated sau P1.1.
