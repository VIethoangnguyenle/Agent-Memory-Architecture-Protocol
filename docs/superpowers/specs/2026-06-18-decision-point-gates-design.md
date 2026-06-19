# Sub-spec #1 — Decision-Point Gates (Spine)

> Ngày: 2026-06-18
> Trạng thái: APPROVED (brainstorm) — chờ user review file
> Program: `docs/superpowers/specs/2026-06-18-amap-retro-fix-program-design.md`
> Cơ chế đã chốt: **B (artifact-precondition gate) + chọn lọc C (probe/build)**; tenet **gate-by-evidence**.

---

## 1. Mục tiêu & Success criteria

**Mục tiêu:** biến các luật process/knowledge từ *prose-bị-skip* thành **gate fire-được tại điểm ra quyết định**, kéo knowledge **just-in-time** (không phình bootstrap), và **net-negative** về prose.

**Success criteria (đo được):**

1. **Bootstrap diet:** bootstrap không còn nạp full `author-dna.yaml`/`conventions.yaml`/`knowledge-snapshot.md`; chỉ nạp `knowledge-index.yaml`. Token bootstrap của knowledge layer giảm rõ rệt (đo bằng số dòng nạp).
2. **4 gate có test:** mỗi gate có một fixture chứng minh: *thiếu bằng chứng → ABORT/degrade*; *đủ bằng chứng → pass*.
3. **Net-negative:** ≥ 9 khối `[CRITICAL]` prose-rule (R-Guard-2, R-Flow-1/2/3, R-Tool-4/5/5b, R-Adapter-2, R-Tool-8) được **collapse** thành precondition + evidence-requirement; tổng dòng rule giảm.
4. **Tái hiện chống regression:** trên kịch bản C-10 (subagent vi phạm SP-6) và C-22 (bỏ spec), gate chặn được — chứng minh bằng fixture, không cần chạy lại task thật.

## 2. Cơ chế chung: gate = precondition + checkpoint artifact

Mọi gate dùng **chung một hình dạng**, tái dùng máy `pre_conditions` của R-Guard-1 (đã có: `exists`, `not_empty`, `not_skeleton`, `phase_done`, `on_fail: ABORT|WARN`):

```
(điểm quyết định)
  → tra knowledge-index   (nhẹ, đã nạp ở bootstrap)
  → kéo đúng SLICE just-in-time (DNA entry / conv section / snapshot module khớp artifact_type)
  → ghi 1 CHECKPOINT artifact chứa BẰNG CHỨNG bắt buộc
  → bước sau: precondition kiểm checkpoint (exists + not_skeleton + chứa field bắt buộc)
       thiếu → on_fail
```

**Tenet gate-by-evidence:** precondition **không** kiểm "agent có gọi tool không" (không kiểm được) mà kiểm **nội dung artifact** — thứ chỉ hành động đúng mới sinh ra (node_id, blast-radius, probe-numbers, rule-id đã áp dụng). Prose dạng "hãy gọi X / prefer Y" bị **xoá**, vì bằng chứng tự loại đường sai.

## 3. Bootstrap diet + knowledge-index

### 3.1 Vấn đề hiện tại

`procedures/bootstrap.md` PHASE 3 eager-load full `author-dna.yaml`, full `conventions.yaml` (852 dòng), `knowledge-snapshot.md`; PHASE 5 còn **mandate** "đọc TẤT CẢ confirmed entries trước khi code". Báo cáo chứng minh thua kép: (a) đọc rồi quên (24% reads = bootstrap-quên-ngay), (b) phình context.

### 3.2 Thay đổi

Nhân bản pattern PHASE 1 (skills lazy-load qua `skill-index.yaml`) cho knowledge:

- Thêm `knowledge/long-term/knowledge-index.yaml` — **artifact dẫn xuất, sinh runtime per-project** bởi `knowledge-curator` (mirror `tools/skill-index/generate_index.py`), từ chính `author-dna.yaml`/`conventions.yaml`/`knowledge-snapshot.md` của repo đó. **Không** nằm trong framework template; **không** commit như nguồn (đối xử như build output).
- Ví dụ dưới đây là **giá trị của project ngân hàng đang dogfood — KHÔNG phải nội dung framework**, chỉ minh hoạ *hình dạng*:

  ```yaml
  - id: SP-6
    store: author-dna
    title: "Constructor fields theo staircase độ dài tăng dần"
    applies_to: [Constructor, Service, Executor, Handler, Factory]
    mechanically_checkable: true
  - id: factory-design-boundary
    store: conventions
    title: "Factory không chứa business logic; reuse trước khi tạo mới"
    applies_to: [Factory]
    mechanically_checkable: false
  - id: module:user-status-change
    store: snapshot
    title: "Flow đổi trạng thái user (lock/unlock/cancel)"
    applies_to: [Handler, Executor]
  ```

- **PHASE 3 (sửa):** thay nạp full 3 file bằng nạp `knowledge-index.yaml`. Full body chỉ kéo JIT tại gate.
- **PHASE 5 (sửa):** bỏ mandate "đọc TẤT CẢ confirmed entries"; report ghi `🧠 DNA-index: loaded — {n} entries indexed` thay vì `{n} confirmed entries read`.

**Điều kiện cần:** mỗi entry DNA/conventions/snapshot mang tag `applies_to` (artifact types) để gate cắt slice. Đây là cùng index mà cả 4 gate + subagent injection dùng lại → một nguồn, nhiều nơi dùng.

### 3.3 Ranh giới generic (BẮT BUỘC)

Framework **chỉ** định nghĩa: schema index, generator, gate logic, và quy ước "entry mang tag `applies_to`". Framework **không** chứa: giá trị entry, danh sách `applies_to`, hay vocabulary artifact-type.

- `knowledge-index.yaml` là **build output per-project** — gitignore/treat-as-generated, không vào framework template.
- Vocabulary artifact-type (`Factory/Service/Handler/...`) **KHÔNG là enum cứng trong framework** — gate match theo *bất kỳ tag `applies_to` nào project tự định nghĩa* (string tự do, nguồn từ conventions của repo).
- Khi collapse R-Guard-2: **generic-hoá luôn** — bỏ tên artifact cụ thể (`Factory/Service/Repository`) khỏi prose rule, thay bằng "match theo `applies_to` của entry".

## 4. Bốn gate

### Gate #1 — Knowledge-before-code

- **Sửa:** C-10 (SP-6 dù approved), C-04/C-11 (over-engineering, không reuse), Cluster A.
- **Điểm quyết định:** trước khi tạo/sửa artifact (Factory/Service/Executor/Handler...).
- **Bằng chứng bắt buộc** — `KNOWLEDGE_CHECKPOINT.<artifact>.md`:
  - DNA entry khớp `artifact_type` (từ index) + constraint chính.
  - Conventions section cho artifact-type.
  - **Codebase-facts:** `node_id` các component *đã có thể reuse* + blast-radius (`find_impact`) — **hoặc** dòng degrade `KG unavailable — MEDIUM`.
- **Precondition (trên skill sinh code / `opsx-apply`):** checkpoint `exists` + `not_skeleton` + chứa ≥1 rule-id khớp + (node_id **hoặc** degrade line). `on_fail: ABORT`.
- **Chống over-engineering:** checkpoint buộc liệt kê "component sẵn có tìm được" → không gọi graph thì điền không nổi; gọi thì thấy `ITransactionFactory.exists()` → Factory mới lộ ra là thừa *trước khi code*.
- **Collapse:** R-Guard-2 (checklist prose) → 1 precondition.

### Gate #2 — Subagent knowledge injection

- **Sửa:** 10 subagent / 0 knowledge reads → SP-6 lan ra.
- **Bản chất:** subagent chỉ có prompt của nó, không thừa kế context, không nên/không được tự đọc knowledge (R-Tool-8). Knowledge **phải PUSH lúc dispatch**.
- **Bước 1 — cắt slice (index→matched), nhúng inline:** orchestrator tra index theo artifact_type của node → lấy đúng DNA/conv/snapshot slice + node_id/blast-radius đã gom → **nhúng inline vào prompt subagent** + ghi bản sao `TASK_HANDOFF.<node-id>.md`.
- **Bước 2 — gate dispatch:** precondition trên `invoke_subagent`: `TASK_HANDOFF.<node-id>.md` tồn tại + section "Applicable DNA/Conventions" `not_skeleton` + chứa rule-id khớp artifact_type. Thiếu → ABORT dispatch (không spawn được).
- **Bước 3 — verify output:** output subagent kèm `node-checkpoint` ("đã áp SP-6, SP-7, Factory-boundary"); precondition *chấp nhận* output kiểm checkpoint; linter cơ học (sub-spec #2) gác cửa cuối cho rule `mechanically_checkable`.
- **Bước 4 — thiếu slice:** subagent **không tự explore**, ghi `CONTEXT_REQUEST.<node-id>.md` → orchestrator enrich → re-dispatch.
- **Collapse:** R-Tool-8 (permissive prose "chỉ orchestrator được enrich") → 1 precondition cứng (dispatch-gate).

### Gate #3 — Phase-non-bypass

- **Sửa:** C-22 (CRITICAL systemic) — bỏ Pha Spec vì "tiết kiệm token".
- **Điểm quyết định:** (a) vào `/task apply`; (b) phát report "Done".
- **Bằng chứng bắt buộc:** marker phase trong `AGENT_TRANSPARENCY` (`Pha 1 DONE`, `Pha 2 DONE` + spec path) và spec artifact tại `openspec/changes/<id>/`.
- **Gate — hai lớp:**
  1. *Apply-entry:* precondition `phase_done(spec)` AND `spec_exists(openspec/changes/<id>/)`. Thiếu → ABORT.
  2. *Completion:* không được phát "Done" tới khi một **phase-chain self-check** xác nhận đủ chuỗi marker REQUIREMENT→spec→apply. "Bỏ spec cho đỡ tốn token" mất hiệu lực vì *spec artifact* là bắt buộc, không phải *phán đoán* agent. (Phần *build-pass + bookkeeping* của completion thuộc sub-spec #3; hai latch compose với nhau — #1 lo phase-chain, #3 lo build/transparency.)
- **Residual (ghi rõ, không giấu):** B + selective-C **không** chặn "agent dùng Write/Edit thô ngoài mọi /task skill" — cần hook chặn-Write (đã hoãn vì portability), ghi là *future optional hook*. C-22 thực tế trong báo cáo có gọi apply-equivalent + phát "Done" → completion-gate fire được.
- **Collapse:** R-Flow-1 + R-Flow-2 + R-Flow-3 → phase-precondition + completion-gate.

### Gate #4 — MCP-probe (verify/degrade)

- **Sửa:** UA false "Runtime Ready" — khai ready từ resolved-config mà không verify tool-list.
- **Điểm quyết định:** bootstrap MCP-status + lần khảo sát codebase đầu tiên.
- **Bằng chứng bắt buộc (gate-by-evidence áp cho probe):** MCP-status **phải nhúng số thật** từ `get_graph_stats`/`list_projects` (node count, edge count, freshness, project name).
- **Gate:** MCP-status hợp lệ *chỉ khi* có probe-numbers. "Runtime Ready" rỗng = invalid → buộc rẽ degrade: `KG unavailable — grep fallback, MEDIUM` + hạ confidence kiến trúc + gợi ý `/understand`. Không in nổi count nếu không gọi tool → false-ready bất khả.
- **Ranh giới:** **không** sửa infra (CLI thiếu `mcp_config.json`) — đó là `amap doctor`/install (item kế cận, ngoài #1). Gate chỉ sửa *lỗi framework*: không khai-có-MCP khi thiếu bằng chứng.
- **Collapse:** R-Tool-4 + R-Tool-5 + R-Tool-5b + R-Adapter-2 → 1 evidence-requirement, dùng chung nhánh degrade với Gate #1.

## 5. Bốn gate = một cơ chế, bốn điểm cắm

| Gate | Điểm cắm | Bằng chứng buộc có | Prose collapse |
|------|----------|--------------------|----------------|
| #1 knowledge-before-code | trước khi sinh artifact | DNA/conv slice + node_id/blast-radius \| degrade | R-Guard-2 |
| #2 subagent injection | trước khi dispatch subagent | handoff chứa slice + output mang evidence tuân thủ | R-Tool-8 |
| #3 phase-non-bypass | vào apply + phát Done | marker phase + spec artifact | R-Flow-1/2/3 |
| #4 MCP-probe | bootstrap + explore đầu | probe-numbers \| degrade line | R-Tool-4/5/5b + R-Adapter-2 |

Gate #4 quyết nhánh bằng-chứng cho #1; #2 dùng lại slice của #1; #3 bọc ngoài. Một máy `pre_conditions` + checkpoint-artifact, bốn chỗ cắm.

## 6. Artifact / file thay đổi

**Mới:**
- `knowledge/long-term/knowledge-index.yaml` (sinh bởi knowledge-curator).
- `knowledge/templates/KNOWLEDGE_CHECKPOINT.tpl.md`.
- `procedures/decision-gate.md` — procedure dùng chung cho 4 gate.

**Sửa:**
- `procedures/bootstrap.md` — PHASE 3 diet, PHASE 5 report-from-index + report-from-probe.
- `rules/rules-guard.md` — R-Guard-2 → precondition-artifact form.
- `rules/rules-flow.md` — R-Flow-1/2/3 → phase-precondition + completion-gate.
- `rules/rules-tool.md` — R-Tool-4/5/5b + R-Adapter-2 → 1 evidence-requirement; R-Tool-8 → dispatch-gate.
- Frontmatter `pre_conditions:` của skill sinh-artifact (executor / `openspec-apply`) + skill orchestrator (subagent dispatch).
- `tools/skill-index/generate_index.py` — thêm/anh em generator cho knowledge-index.

**Cần tag dữ liệu:** thêm `applies_to` cho entries trong `author-dna.yaml`, `conventions.yaml`, `knowledge-snapshot.md` (knowledge-curator duy trì).

## 7. Verification

- **Fixture per-gate:** dựng input tối thiểu, assert precondition ABORT khi thiếu evidence và pass khi đủ. Không cần MCP thật (mock probe-numbers / thiếu).
- **Regression kịch bản thật:** fixture C-10 (handoff thiếu SP-6 slice → dispatch ABORT) và C-22 (apply thiếu spec marker → ABORT; Done thiếu chuỗi → block).
- **Golden-snapshot:** cập nhật snapshot `amap init` per-platform (Batch 1/UP3) theo bề mặt mới; giữ scaffold-test xanh.
- **Net-negative:** script đếm khối `[CRITICAL]` + dòng rule trước/sau, assert giảm.

## 8. Ranh giới #1

Không gồm: formatting/linter (#2), build-verify/bookkeeping (#3), teaching-moment capture (#4), full skill/workflow consolidation (#5), infra `mcp_config` fix, runtime Write-hook.
