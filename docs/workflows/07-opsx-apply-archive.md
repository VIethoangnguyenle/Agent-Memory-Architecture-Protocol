# Workflow: /opsx:apply + /opsx:archive — Apply & Archive

> **Commands**: `/opsx:apply`, `/opsx:archive`  
> **Vai trò**: Implement tasks từ spec + Archive change đã hoàn thành

---

## /opsx:apply — Implement Tasks

### Quy trình

1. **Chọn change** — từ input hoặc hỏi user.
2. **Kiểm tra status** — `openspec status --change "<name>" --json`.
3. **Lấy apply instructions** — `openspec instructions apply --change "<name>" --json`.
4. **Đọc context files** — proposal, specs, design, tasks.
5. **Hiển thị progress** — Schema, N/M tasks complete.
6. **Implement tasks** — Loop qua từng task, code changes, mark `[x]` khi xong.
7. **Báo cáo** — Tasks completed, overall progress, suggest archive.

### Pause khi
- Task unclear → hỏi clarification.
- Design issue discovered → suggest update artifacts.
- Error/blocker → report và chờ guidance.

---

## /opsx:archive — Archive Change

### Quy trình

1. **Chọn change** — hỏi user nếu ambiguous.
2. **Check artifact completion** — WARN nếu có artifact chưa done.
3. **Check task completion** — WARN nếu có task chưa xong.
4. **Assess delta spec sync** — so sánh delta specs vs main specs.
5. **Perform archive**:
   ```bash
   mv openspec/changes/<name> openspec/changes/archive/YYYY-MM-DD-<name>
   ```
6. **Display summary** — Change name, schema, archive location, sync status.

### Tích hợp Knowledge Curator (L2)

Sau khi archive OpenSpec change, gọi `knowledge-curator`:
1. `archive_active_context(ticket_id)` → backup active/.
2. `update_knowledge_snapshot(discoveries)` → update bộ nhớ dài hạn.
3. `reset_active_context()` → reset cho task mới.

---

## Guardrails

- Không block archive vì warnings — chỉ inform và confirm.
- Luôn hỏi user chọn change nếu không chỉ rõ.
- Keep code changes minimal và scoped theo từng task.
- Pause on errors — không guess.
