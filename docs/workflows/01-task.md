# Workflow: /task — Orchestrator Chính

> **Command**: `/task <ý-tưởng-hoặc-link>`  
> **Vai trò**: Cổng vào duy nhất cho mọi công việc liên quan đến task

---

## 3 Chế độ sử dụng

| Command | Pha | Mô tả |
|---------|-----|-------|
| `/task <ý-tưởng-hoặc-link>` | Pha 1 | Hiểu vấn đề, chuẩn hoá yêu cầu, explore DB/code/architecture |
| `/task spec <ticket-id>` | Pha 2 | Sinh spec kỹ thuật qua OpenSpec |
| `/task apply <ticket-id>` | Pha 3 | Apply spec vào code |

---

## Pha 1 — Hiểu vấn đề

### Nhận diện loại input

| Loại | Điều kiện | Nhánh |
|------|-----------|-------|
| `HAS_TICKET` | URL hoặc key ticket (ABC-123) | → requirement-analyst → db-explorer → codebase-explorer → architecture-reviewer |
| `HAS_DOC_ONLY` | URL tài liệu (wiki/PRD) | → spec-extract → đánh giá Độ tin cậy |
| `IDEA_ONLY` | Chuỗi text thường | → Tạo file ideation, hỏi-đáp refine scope |

### Nhánh HAS_TICKET (chính)

1. **requirement-analyst** → Chuẩn hoá REQUIREMENT.md.
2. **db-explorer** → Khám phá schema/constraint (nếu chạm data).
3. **codebase-explorer** → Map requirement → module/file.
4. **architecture-reviewer** → Đánh giá xung đột/rủi ro.
5. **opsx:explore** → BẮT BUỘC nếu Độ tin cậy thấp.
6. Ghi AGENT_TRANSPARENCY + TOKEN_LOG.
7. Đánh dấu `phase_state: phase-1-done`.

### BLOCKER Recovery

Nếu architecture-reviewer phát hiện **BLOCKER**:
- Dừng pipeline hoàn toàn.
- Hiển thị issues + gợi ý action.
- Chờ user resolve trước khi tiếp tục.

---

## Pha 2 — Sinh spec (`/task spec`)

1. Đọc REQUIREMENT.md + EXPLORE_CONTEXT.md.
2. Tóm tắt cho user (bối cảnh, kiến trúc, rủi ro).
3. **Hỏi user confirm** — bắt buộc, không được skip.
4. Gọi OpenSpec (`/opsx:propose`) → sinh proposal.md, design.md, tasks.md.
5. Output tại `openspec/changes/<change-id>/`.
6. Đánh dấu `phase_state: phase-2-done`.

> **CRITICAL**: KHÔNG dùng planning mode mặc định. BẮT BUỘC qua OpenSpec.

---

## Pha 3 — Apply spec (`/task apply`) — Micro-loop (SP1b)

1. Đọc spec `tasks.md`, tóm tắt files/modules sẽ chạm.
2. **spec-validator** → pre_apply_gate + ac_coverage.
3. Hỏi xác nhận cuối cùng.
4. **Orchestrate micro-loop** (`.agent/tools/microloop-orchestrator/`):
   a. topo-sort tasks (base trước) → `TASK_QUEUE.md`.
   b. Đọc tier từ `.agent/profiles/execution-mode.yaml`.
   c. Loop mỗi task: lắp `TASK_HANDOFF` (DNA slice + spec slice + snapshot slice +
      written-files) → dispatch executor (`.agent/procedures/executor.md`) →
      mechanical gate SP1a → semantic surface-check (spec-validator §6 phần semantic)
      → mark `[x]` task + `TASK_QUEUE` done → task kế.
      Gate FAIL → feedback executor (≤2 vòng) → vẫn FAIL: `blocked`, hỏi user.
5. Hết task → **extraction review** (`.agent/procedures/reviewer.md`) trên TẤT CẢ file
   mới → `EXTRACTION_REPORT` → trình user (HP-10/11 = WARN).
6. **spec-validator** → post_apply_verify.
7. Gọi **knowledge-curator** → archive + update snapshot + reset.

> DNA-RELOAD (cũ, bước 2a) nghỉ hưu: DNA giờ vào context executor qua `dna_slice` trong
> handoff (cấu trúc), không phải nghi thức reload.

---

## Post-Phase Self-Check

Mỗi pha có self-check bắt buộc trước khi báo "hoàn thành":

| Pha | Checks |
|-----|--------|
| 1 | REQUIREMENT ≠ skeleton, EXPLORE_CONTEXT đã ghi, phase_state = done, TOKEN_LOG đã ghi |
| 2 | Spec file tồn tại, OPENSPEC_STATE = propose_done, TOKEN_LOG đã ghi |
| 3 | Code changes đã tóm tắt, phase_state = completed, TOKEN_LOG TỔNG TASK đã ghi |
