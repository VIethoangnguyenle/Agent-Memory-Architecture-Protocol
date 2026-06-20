# Apply-Gate — phase + blocker evidence in the write-gate (C-23)

> **Date:** 2026-06-20
> **Status:** Approved (design) — ready for implementation plan
> **Branch:** `apply-gate` (stacked on `bash-write-gate` / PR #12; merge after #12).
> **Lineage:** addresses audit items **#2** (`/opsx:apply` back door) and **#3** (gates
> not wired into the workflow) from `memory: amap-enforcement-audit-2026-06-20`. Builds on
> the runtime write-gate (C-22) and its Bash extension (C-22b).

---

## 1. Bối cảnh & vấn đề

Audit 2026-06-20 phát hiện hai lỗ hổng liên quan:

- **#2 — `/opsx:apply` là cửa sau.** `workflows/opsx-apply.md` là workflow OpenSpec vanilla
  ("can be invoked anytime"), không confirm / không spec-validator / không phase-chain.
- **#3 — gate không wired vào workflow.** `gate-check` chỉ xuất hiện trong `rules/` +
  `procedures/`; đường apply thật là `procedures/executor.md` + `workflows/opsx-apply.md`
  (không phải SKILL.md có `pre_conditions`), nên không có điểm nào gọi gate deterministically.

**Nhận định then chốt:** write-gate hook là **workflow-agnostic** — nó fire trên mọi
Edit/Write/MultiEdit/Bash bất kể vào bằng `/task apply` hay `/opsx:apply`. Vì vậy gate
`knowledge-checkpoint` (R-Guard-2) **đã** áp cho cả đường `/opsx:apply`. Cái cửa sau còn
bỏ qua thực chất là: **đã spec chưa (phase)** và **còn BLOCKER-ARCH chưa resolve không**
— chính là apply-entry condition của R-Flow-2 ([rules-flow.md] §2).

→ Cả #2 và #3 giải được bằng **cùng cơ chế đã chứng minh**: thêm bằng chứng apply-entry
vào write-gate. Không cần sửa file vanilla `opsx-apply.md` (giữ portability OpenSpec).

## 2. Mục tiêu & phi mục tiêu

- **Mục tiêu:** một code-write vào path non-framework chỉ được phép khi:
  1. `KNOWLEDGE_CHECKPOINT.md` hợp lệ (đã có từ C-22), **và**
  2. `AGENT_TRANSPARENCY.md` có marker **`Pha 2 DONE`** (spec đã sinh), **và**
  3. **không còn `[BLOCKER-ARCH]` chưa resolve** (mỗi `[BLOCKER-ARCH]` có `[BLOCKER-ARCH RESOLVED]` tương ứng).
  Deterministic, workflow-agnostic → khóa cửa sau `/opsx:apply` (#2) + operationalize
  R-Flow-2 apply-entry (#3) trong cùng một cơ chế.
- **Phi mục tiêu (residual, ghi nhận):**
  - **R-Apply-1 (human confirm)** — bản chất tương tác per-session; hook không kiểm được
    bằng file-evidence mà không bị gameable. Vẫn là nghĩa vụ prose trong `task.md`.
  - **spec-validator pre-apply** — concern riêng (chất lượng spec), có thể là gate sau.
  - Không sửa `opsx-apply.md` / `task.md` / `executor.md` (chỉ doc-accuracy ở rules).

## 3. Cơ chế

### 3.1 Validator mới — `gates.py`
`validate_apply_gate(text) -> Result`:
- FAIL nếu thiếu marker `Pha 2 DONE` (regex `Pha\s*2\s*DONE`).
- FAIL nếu `count("[BLOCKER-ARCH]") > count("[BLOCKER-ARCH RESOLVED]")`.
- Ngược lại PASS.
- Dùng check riêng — KHÔNG tái dùng `validate_phase_chain` (nó pass cả khi chỉ có Pha 1).

### 3.2 CLI — `gate-check/cli.py`
Đăng ký subcommand `apply-gate` → `validate_apply_gate`. Cho phép test và để #3 dùng nếu
sau này muốn gọi tường minh trong workflow.

### 3.3 Wire vào `write_gate.evaluate_write`
Sau khi `knowledge-checkpoint` pass và trước khi return PASS:
- Đọc `{project_root}/{framework_root}/knowledge/active/AGENT_TRANSPARENCY.md`.
- Thiếu file → BLOCK (`"Missing AGENT_TRANSPARENCY apply evidence ..."`).
- Chạy `validate_apply_gate`; FAIL → BLOCK với reason từ validator.
- `evaluate_write` dùng chung cho cả Edit/Write **và** Bash branch (C-22b) → cả hai đường
  ghi đều bị apply-gate. Framework artifacts vẫn exempt (return sớm như cũ).

## 4. Hệ quả strictness (đã duyệt)

Sau thay đổi, **mọi** code-write vào app-code (non-framework) yêu cầu đã qua `/task spec`
(có `Pha 2 DONE`). Đúng tinh thần R-Flow-1. File framework (`.amap/`, `openspec/`,
`docs/superpowers/`) vẫn exempt → phát triển chính AMAP và artifact spec/plan không bị
chặn. Sửa app-code tay ngoài flow ở downstream sẽ bị chặn — đây là chủ đích.

## 5. Phạm vi thay đổi (files)

- `.amap/tools/gate-check/gates.py` — thêm `validate_apply_gate`.
- `.amap/tools/gate-check/cli.py` — thêm `apply-gate` vào `VALIDATORS`.
- `.amap/tools/gate-check/tests/test_gates.py` — test validator (pass / thiếu Pha2 / blocker mở).
- `.amap/hooks/write-gate/write_gate.py` — `evaluate_write` thêm apply-gate check.
- `.amap/hooks/write-gate/tests/test_write_gate.py` — cập nhật test cũ (thêm AGENT_TRANSPARENCY
  có Pha 2 DONE) + test mới (block khi thiếu Pha2 / blocker mở; allow khi đủ).
- `.amap/rules/rules-flow.md` — cập nhật R-Flow-2 ghi rõ apply-entry giờ hook-enforced (doc accuracy, không đổi logic rule).

## 6. Test plan / Acceptance criteria

**`validate_apply_gate` (unit):**
- `Pha 2 DONE`, no blocker → PASS.
- thiếu `Pha 2 DONE` → FAIL.
- `[BLOCKER-ARCH]` không có RESOLVED → FAIL; có RESOLVED tương ứng → PASS.

**`evaluate_write` / hook (integration):**
- checkpoint hợp lệ NHƯNG thiếu Pha 2 DONE → BLOCK.
- checkpoint hợp lệ + Pha 2 DONE + no blocker → ALLOW.
- checkpoint hợp lệ + Pha 2 DONE + blocker mở → BLOCK.
- framework artifact (`.amap/...`, `openspec/...`) → ALLOW (exempt, không cần phase).
- Bash code-write (compose C-22b): cùng luật apply-gate áp dụng.

**Regression:** cập nhật `test_allows_app_write_with_valid_checkpoint` để kèm AGENT_TRANSPARENCY
hợp lệ; mọi test khác xanh.

**Exit condition:** fixture chứng minh code-write có checkpoint hợp lệ NHƯNG chưa `Pha 2 DONE`
bị block ở runtime hook (exit 2 Claude / deny Codex+Antigravity) — tức `/opsx:apply` không
thể apply code khi chưa qua spec phase.

## 7. Residual đã biết

- R-Apply-1 confirm + spec-validator pre-apply chưa enforce cơ học (xem §2).
- `eval`/dynamic shell vẫn ngoài tầm (kế thừa từ C-22b threat model).
