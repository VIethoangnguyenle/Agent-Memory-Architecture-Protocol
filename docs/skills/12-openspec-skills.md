# Skill: OpenSpec Skills (Explore + Propose + Archive)

> **Vai trò**: Quản lý change lifecycle trong OpenSpec  
> **3 skill con**: `openspec-explore`, `openspec-propose`, `openspec-archive-change`

---

## 1. OpenSpec Explore

> **Trigger**: `/opsx:explore` hoặc Pha 1 khi Độ tin cậy thấp

**Mục tiêu**: Thinking partner — khám phá ý tưởng, điều tra vấn đề, làm rõ yêu cầu.

**Đặc điểm**:
- Là **stance**, không phải workflow — không có bước bắt buộc.
- **Chỉ suy nghĩ**, KHÔNG implement code.
- Dùng ASCII diagram để visualize.
- Có thể tạo OpenSpec artifacts (proposal, design, spec) nếu user yêu cầu.
- Kết thúc tự nhiên: flow vào proposal, hoặc chỉ provide clarity.

---

## 2. OpenSpec Propose

> **Trigger**: `/opsx:propose` hoặc Pha 2 trong `/task spec`  
> **Pre-conditions**: REQUIREMENT.md phải có nội dung, Pha 1 phải hoàn thành.

**Mục tiêu**: Tạo change mới với đầy đủ artifacts trong 1 bước.

**Output artifacts**:
- `proposal.md` — What & Why.
- `design.md` — How.
- `tasks.md` — Implementation steps.

**Quy trình**:
1. Load knowledge-layer context (REQUIREMENT + EXPLORE_CONTEXT).
2. Tạo change directory: `openspec new change "<name>"`.
3. Lấy artifact build order: `openspec status --change "<name>" --json`.
4. Tạo artifacts theo dependency order.
5. Hiển thị final status.

---

## 3. OpenSpec Archive Change

> **Trigger**: `/opsx:archive` sau khi implementation hoàn thành

**Mục tiêu**: Finalise và archive change đã hoàn thành.

**Quy trình**:
1. Chọn change (hỏi user nếu ambiguous).
2. Check artifact completion status.
3. Check task completion status.
4. Assess delta spec sync state.
5. Move change → `openspec/changes/archive/YYYY-MM-DD-<name>/`.
6. Sync với knowledge-curator (archive active context, update snapshot, reset).

---

## Tích hợp với Knowledge Layer

Sau khi archive OpenSpec change, gọi `knowledge-curator` để:
- Archive `.knowledge-layer/active/` → `archive/{ticket-id}/`.
- Update `knowledge-snapshot.md` với phát hiện mới.
- Reset `active/` cho task mới.
