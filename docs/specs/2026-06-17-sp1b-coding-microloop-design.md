# SP1b — Coding Micro-loop + Extraction Review: Design Spec

> Ngày: 2026-06-17 · Sub-project 1b của chương trình AMAP v4 (Increment 2 trong assessment §6).
> Phụ thuộc: SP1a (đã xong — mechanical gate là tầng dưới của loop), SP0 (`.agent/profiles/` reserved).
> Unblock: SP1c (Qdrant index cho snapshot slice), SP2 (tool-capability adapter).
> Nguồn: [AMAP-v3-assessment.md](../AMAP-v3-assessment.md) §3–7 + brainstorming 2026-06-17.

---

## 1. Mục tiêu

Viết lại **Pha 3 (`/task apply`)** từ "một lần apply monolithic" → **vòng lặp orchestrated subagent
tuần tự**, giải đúng triệu chứng Pha 3 drift (assessment §3.1): dưới tải generation, model thả các
ràng buộc phụ (DNA: zero-nesting, no-else, max-lines, update task) một cách có hệ thống — đây là
**giới hạn cấu trúc**, không sửa được bằng "nhắc mạnh hơn / reload thêm".

Ba cơ chế (assessment §4.3):
1. **Khử context dilution** — mỗi task chạy trong context sạch, nên attention không bị generation
   của task trước chiếm. Rule ngữ nghĩa được check trên **surface nhỏ** (1 task) thay vì cuối một
   đợt generate dài.
2. **Mark OpenSpec task done = ranh giới vòng lặp** — không phải việc nền. Không advance được sang
   task kế nếu chưa mark. Giải bệnh "miss update OpenSpec task".
3. **State chia sẻ qua FILESYSTEM, không qua context** — task sau đọc file task trước vừa ghi ra
   đĩa. "Context sạch" và "kế thừa nhất quán" hết mâu thuẫn.

**Nguyên lý nền (ràng buộc số 1): portable đa framework, không privilege Claude.** Deliverable cốt
lõi **không phải** code subagent mà là **micro-loop contract trung lập trên filesystem**. Claude
Code Agent-tool chỉ là MỘT adapter trong 3 tier, ngang hàng với fresh-session và inline-reload.
Đồng dạng nguyên lý "IR trung lập → backend" của SP1a (Checkstyle chỉ là một backend).

## 2. Phạm vi

**In scope (SP1b):**
- **Micro-loop contract**: bộ artifact filesystem chuẩn hoá (`TASK_QUEUE`, `TASK_HANDOFF`,
  `TASK_RESULT`, `EXTRACTION_INPUT`, `EXTRACTION_REPORT`) — interface trung lập platform.
- **Orchestrator procedure** (viết lại `task.md` Pha 3): topo-sort → loop dispatch → gate →
  semantic surface-check → mark done → extraction review.
- **Execution-mode adapter** (`.agent/profiles/`): khai báo tier (`subagent` | `fresh-session` |
  `inline-reload`); điểm DUY NHẤT chứa platform-specifics.
- **Extraction review** (component [4]): 1 reviewer thấy TẤT CẢ file mới → HP-10/11, có disk-fallback
  khi không có UA graph.
- Tách `spec-validator §6 post_apply_dna_check`: phần cơ học (đã sang SP1a deterministic) bỏ; phần
  semantic giữ, chạy per-task trên surface nhỏ.
- **DNA-RELOAD** (`task.md` 2a): nghỉ hưu thành *cấu trúc* (DNA slice trong handoff), không phải nghi thức.
- Test bằng fixture trong repo AMAP (không cần Java, không cần real subagent của bất kỳ platform).

**Out of scope (KHÔNG ở SP1b):**
- Qdrant index cho `knowledge-snapshot` slice → **SP1c/SP3**. SP1b đọc thẳng section từ file.
- Tool-capability interface đầy đủ (OpenSpec, UA graph adapter) → **SP2**. SP1b bọc thin reader +
  disk-fallback, target capability trừu tượng, không hardcode tool.
- Outcome/quality log (W6) → ngoài SP1b.
- DNA đa-tác-giả (W8) → ngoài SP1b.

## 3. Quyết định đã chốt (brainstorming + assessment)

| Quyết định | Chọn | Nguồn |
|---|---|---|
| Đơn vị vòng lặp | 1 OpenSpec task = 1 micro-loop unit (context sạch) | §4.2 |
| Thứ tự task | topo-sort, **base class trước** | §4.2 |
| Kênh giao tiếp | **filesystem** (contract artifact), không qua context | §4.3.3 |
| Ranh giới advance | mark `[x]` task = bước đóng vòng lặp bắt buộc | §4.3.2 |
| Gate | tái dùng mechanical gate SP1a (deterministic) làm tầng dưới | §4.2 |
| Extraction review | **trong** SP1b (Increment 2), 1 subagent thấy tất cả file | §4.2, §6 |
| Enumerate sibling | UA graph nếu có; **KHÔNG** vector top-k; disk-fallback nếu vắng | §4.5 |
| Portability | neutral contract + 3 execution tier; không privilege Claude | brainstorming |
| snapshot slice | đọc thẳng file (Qdrant hoãn sang SP1c) | §4.5, §6 |
| Retry gate FAIL | max **2 vòng** feedback/task → vẫn FAIL: `blocked`, hỏi user | brainstorming |

## 4. Kiến trúc 5 thành phần (assessment §4.2)

```
   author-dna.yaml ─┐                         knowledge-snapshot.md
   conventions.yaml ─┤ (approved, SoT)             (SoT, đọc section trực tiếp)
        │            │                                   │
  [phần semantic]  ruleset (SP1a, derived)               │ slice
        │            │                                    ▼
        │      ┌──── ORCHESTRATOR (task.md Pha 3) ──── topo-sort task (base trước)
        │      │              │ tuần tự`                        
        ▼      ▼              ▼
   [3] CODING MICRO-LOOP (mỗi task = 1 executor context sạch)
        │  TASK_HANDOFF = DNA slice + spec slice + snapshot slice + 1 task + tóm tắt file đã ghi
        │  executor đọc file cũ TỪ DISK → sinh code CHỈ task này → TASK_RESULT
        ▼
   [2] MECHANICAL GATE (SP1a, deterministic) ← chạy ruleset đã sinh
        │  FAIL → feedback executor fix (≤2 vòng); PASS → semantic surface-check
        │  → mark [x] OpenSpec task → next
        ▼ (hết task)
   [4] EXTRACTION REVIEW (1 reviewer thấy TẤT CẢ file mới) → HP-10/11
        enumerate sibling qua UA graph (disk-fallback nếu vắng) — KHÔNG vector top-k
```

## 5. Micro-loop contract (lõi portable)

Tất cả tier đọc/ghi cùng bộ artifact tại `.knowledge-layer/active/microloop/`. Đây là interface;
"ai chạy task" là chi tiết của tier (§7). Markdown/yaml thuần — không phụ thuộc platform.

| Artifact | Vai trò | Producer → Consumer |
|---|---|---|
| `TASK_QUEUE.md` | Task đã topo-sort + status (`pending`/`in_progress`/`done`/`blocked`) per task. **State bền vững** — resume sau truncation | orchestrator (đọc/ghi) |
| `TASK_HANDOFF.md` | Input contract 1 unit: DNA slice + spec slice + snapshot slice + 1 task + tóm tắt file đã ghi + (feedback nếu retry) | orchestrator → executor |
| `TASK_RESULT.md` | Output contract: file đã ghi, gate status, semantic-check status, self-flagged violations | executor → orchestrator |
| `EXTRACTION_INPUT.md` | TẤT CẢ file mới/đổi của ticket + nhóm nghiệp vụ gợi ý | orchestrator → reviewer |
| `EXTRACTION_REPORT.md` | HP-10/11 findings: cụm class ≥70% trùng, đề xuất Template Method, verdict | reviewer → orchestrator/user |

> State nằm trên disk → vòng lặp **không chết** khi session bị cắt: orchestrator đọc `TASK_QUEUE.md`
> biết task nào dở, resume đúng chỗ. Đây cũng là thứ làm tier `inline-reload` không thua kém về tính
> bền — cùng file, chỉ khác cách spawn.

### 5.1 `TASK_QUEUE.md` (schema)
```yaml
ticket_id: "<ticket>"
spec_path: "openspec/changes/<change-id>/"
execution_mode: "subagent | fresh-session | inline-reload"   # đọc từ profile
tasks:
  - id: T1
    desc: "Tạo BaseXHandler (base class)"
    depends_on: []
    status: done          # pending | in_progress | done | blocked
    retries: 0
  - id: T2
    desc: "XaHandler extends BaseXHandler"
    depends_on: [T1]
    status: in_progress
    retries: 1
```

### 5.2 `TASK_HANDOFF.md` (schema — input cho executor)
```yaml
task: { id: T2, desc: "..." }
dna_slice:            # CHỈ entry liên quan task, không dump cả DNA
  hard_principles: [HP-6, HP-7, HP-10]
  complexity_thresholds: { ... }
  style: [SP-1, ...]
spec_slice: "<trích phần spec cho task này>"
snapshot_slice: "<section knowledge-snapshot liên quan module>"
written_files:        # tóm tắt file task trước đã ghi (đọc từ disk để biết kế thừa)
  - { path: "BaseXHandler.java", summary: "abstract execute(), template method doX→doY→doZ" }
boundary: ["KHÔNG sửa interface YyyService"]
feedback: null        # nếu retry: nội dung gate FAIL + hint fix
```

### 5.3 `TASK_RESULT.md` (schema — output từ executor)
```yaml
task_id: T2
changed_files:
  - { path: "XaHandler.java", change_type: NEW, summary: "extends BaseXHandler, override doY" }
gate_status: PASS         # PASS | FAIL — điền sau khi orchestrator chạy gate (xem §6)
gate_violations: []
self_flagged: []          # executor tự nghi ngờ điều gì
```

## 6. Orchestrator procedure (data flow)

```
orchestrator (task.md Pha 3):
  1. Đọc spec tasks.md → topo-sort theo depends_on (base trước) → ghi TASK_QUEUE.md
  2. loop mỗi task status=pending (hoặc resume in_progress):
       a. set status=in_progress
       b. lắp TASK_HANDOFF.md (slice DNA+spec+snapshot+task+written-summary từ disk)
       c. dispatch(handoff) theo execution_mode (§7) → executor ghi TASK_RESULT.md
       d. MECHANICAL GATE (SP1a) chạy ruleset trên changed_files:
            FAIL → ghi feedback vào TASK_HANDOFF, retries++, re-dispatch
                   nếu retries > 2 → status=blocked, dừng loop, báo user
            PASS → semantic surface-check (spec-validator §6 phần semantic) trên DIFF 1 task
                   → mark [x] trong tasks.md + status=done → task kế
  3. hết task pending:
       a. lắp EXTRACTION_INPUT.md (mọi changed_files toàn ticket + nhóm nghiệp vụ)
       b. dispatch reviewer 1 lần (thấy TẤT CẢ) → EXTRACTION_REPORT.md
       c. trình user duyệt report (HP-10/11 là FLAG_AND_WARN — không tự sửa)
  4. knowledge-curator → archive + update snapshot + reset (giữ như flow cũ)
```

**Điểm mấu chốt portability:** procedure chỉ gọi abstraction `dispatch(handoff) → result`. Logic
loop, topo-sort, gate, mark-done **giống hệt** mọi tier. Chỉ `dispatch` khác — và nó đọc tier từ profile.

## 7. Execution tiers (adapter — điểm DUY NHẤT chứa platform-specifics)

`.agent/profiles/execution-mode.yaml` khai báo tier hiện tại. Đổi platform = đổi 1 dòng, không sửa loop.

| Tier | Platform | `dispatch(handoff)` làm gì |
|---|---|---|
| `subagent` | Claude Code | Spawn Agent tool, prompt = "đọc TASK_HANDOFF, sinh code, ghi TASK_RESULT". Isolation đầy đủ. |
| `fresh-session` | Cursor / Antigravity | Ghi handoff + chỉ thị user mở context/session mới chạy **executor procedure** (`.agent/procedures/`). Context sạch qua session mới. |
| `inline-reload` | fallback đơn-session | Agent tự reload handoff slice (xoá context exploration cũ khỏi attention), sinh code cùng session. LCD — phải chạy đúng. |

**Nguyên tắc:** không nhánh logic nào ngoài `dispatch` được giả định Agent tool tồn tại. Nếu
`inline-reload` chạy đúng → mọi platform chạy đúng. `subagent` chỉ là tối ưu isolation, không phải
điều kiện cần.

## 8. Extraction review (component [4])

1 reviewer thấy **toàn bộ** file mới (không vector top-k — §4.5). Capability `enumerate_siblings`:
- **có UA graph** → query graph để liệt kê class cùng nhóm (đầy đủ, đúng §4.5);
- **không có** → **disk-fallback**: `EXTRACTION_INPUT` đã chứa danh sách file mới, reviewer đọc thẳng,
  nhóm theo **bản chất nghiệp vụ** (HP-11, không theo tên action), flag cụm logic trùng >70% và đề
  xuất Template Method (HP-10).

HP-10/HP-11 là `FLAG_AND_WARN` (theo author-dna) → report là **khuyến nghị**, không tự sửa, không
block. User quyết định refactor hay archive.

## 9. Thay đổi file ngoài tool (blast radius — assessment §5)

| File hiện tại | Thay đổi |
|---|---|
| `docs/workflows/01-task.md` Pha 3 + workflow tương ứng | **Viết lại**: "một lần apply" → orchestrated micro-loop §6 |
| `.agent/skills/spec-validator/SKILL.md §6` `post_apply_dna_check` | **Tách**: cơ học (SP1a lo) bỏ khỏi đây; semantic giữ, chạy per-task surface nhỏ |
| `task.md` DNA-RELOAD (bước 2a) | **Nghỉ hưu**: reload thành DNA slice trong handoff (cấu trúc), không nghi thức |
| `.agent/profiles/execution-mode.yaml` | **Mới**: khai báo tier |
| `.agent/procedures/executor.md`, `.agent/procedures/reviewer.md` | **Mới**: procedure cho fresh-session/inline tier |
| `spec-validator` pre_apply_gate / ac_coverage / post_apply_verify | **Giữ nguyên** |

## 10. File layout (tool + procedure)

```
.agent/tools/microloop-orchestrator/
├── orchestrator.py          # topo-sort + loop protocol + contract assembly/parse (CLI)
├── contract.py              # đọc/ghi 5 artifact (schema validate)
├── tiers/
│   ├── __init__.py
│   ├── subagent.py          # dispatch qua Agent tool (Claude)
│   ├── fresh_session.py     # sinh handoff + chỉ thị mở session mới
│   └── inline_reload.py     # reload slice cùng session
├── tests/
│   ├── fixtures/
│   │   ├── sample-tasks.md            # có depends_on base-first
│   │   ├── sample-dna.yaml
│   │   ├── sample-snapshot.md
│   │   ├── expected-queue.yaml        # sau topo-sort
│   │   ├── expected-handoff-T2.yaml
│   │   └── sample-extraction-input.md # 3 class ~80% trùng
│   ├── test_toposort.py
│   ├── test_handoff_assembly.py
│   ├── test_loop_protocol.py          # PASS/FAIL/retry/resume/escalate
│   ├── test_degradation.py            # inline-reload chạy đúng contract
│   └── test_extraction.py             # disk-fallback flag được cụm trùng
├── requirements.txt
└── README.md
.agent/profiles/execution-mode.yaml
.agent/procedures/executor.md
.agent/procedures/reviewer.md
```

## 11. Test strategy (TDD trong repo AMAP, không Java, không privilege Claude)

Lõi là **contract assembly/parsing + loop protocol** — test hoàn toàn bằng fixture, độc lập platform
(không nhánh test nào cần real subagent):

- **Topo-sort:** `sample-tasks.md` (dependency base-first) → assert thứ tự `TASK_QUEUE` khớp `expected-queue`.
- **Handoff assembly:** DNA+spec+snapshot mẫu + task T2 → assert `TASK_HANDOFF` chứa đúng slice
  (CHỈ entry liên quan, không dump cả DNA — chống context bloat).
- **Loop protocol:** giả lập `TASK_RESULT` gate PASS → assert mark done + advance; gate FAIL → assert
  retry với feedback; FAIL 3 lần → assert `blocked` + dừng.
- **Resume:** `TASK_QUEUE` có task `in_progress` → assert orchestrator resume đúng chỗ (không làm lại task done).
- **Degradation:** profile `inline-reload` → assert cùng contract vẫn chạy; assert KHÔNG nhánh nào
  yêu cầu Agent tool (test bằng cách chạy protocol mà không có dispatch subagent).
- **Extraction:** `sample-extraction-input` 3 class ~80% trùng → assert report flag cụm + đề xuất
  Template Method, kể cả nhánh disk-fallback (không UA graph).

## 12. Verification (định nghĩa "done")

1. `pytest tests/` xanh toàn bộ (topo-sort + handoff + protocol + resume + degradation + extraction).
2. Topo-sort: task có `depends_on` luôn xếp sau dependency (base trước) trên fixture.
3. Handoff chỉ chứa slice liên quan — assert không chứa entry DNA ngoài danh sách task (chống bloat).
4. Loop protocol: gate FAIL → retry ≤2 → vẫn FAIL → `blocked` (không loop vô hạn).
5. Resume: kill giữa chừng (task `in_progress`) → orchestrator tiếp đúng chỗ, không lặp task done.
6. **Degradation (portability gate):** chạy full protocol ở tier `inline-reload` → hoàn tất queue
   mà KHÔNG gọi Agent tool. Chứng minh không lệ thuộc Claude.
7. Extraction review flag được cụm class trùng >70% qua disk-fallback (không cần UA graph).
8. `task.md` Pha 3 viết lại trỏ đúng orchestrator procedure; `spec-validator §6` tách semantic;
   DNA-RELOAD thành slice trong handoff.
9. Mechanical gate SP1a được gọi đúng trong loop (tái dùng, không viết lại).

## 13. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|---|---|
| `inline-reload` không thật sự "sạch" context (cùng session) | Reload slice tường minh + xoá exploration cũ khỏi attention; tier này là LCD, chấp nhận yếu hơn `subagent` nhưng vẫn hơn monolithic |
| Handoff slice thiếu context task cần → executor sinh sai | `written_files` summary + executor đọc file thật TỪ DISK (không chỉ dựa summary); boundary tường minh |
| Topo-sort sai khi task có circular dependency | Phát hiện cycle → ERROR sớm, báo user sửa spec |
| UA graph vắng làm extraction yếu | disk-fallback nhóm theo bản chất nghiệp vụ; HP-10/11 là WARN nên false-negative không block |
| OpenSpec coupling (đọc tasks.md) | thin reader, abstract để SP2 swap; không hardcode đường dẫn OpenSpec trong loop logic |
| Tier subagent của Cursor/Antigravity khác Claude | chỉ cần implement `dispatch` cho tier đó; contract + loop không đổi |

## 14. Không phá vỡ điều gì

- Mechanical gate SP1a tái dùng nguyên trạng (không sửa).
- `spec-validator` pre_apply_gate / ac_coverage / post_apply_verify giữ nguyên.
- Contract artifact là **thêm mới** ở `.knowledge-layer/active/microloop/` — không đụng artifact cũ.
- Repo AMAP test bằng fixture; không cần Java, không cần real subagent của bất kỳ platform.
- Profile `subagent` không bắt buộc — mọi platform chạy được ở `inline-reload` (portability gate §12.6).
