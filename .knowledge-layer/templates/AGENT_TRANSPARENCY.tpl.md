---
schema: agent-transparency/v1
ticket_id: "<!-- ticket-id -->"
updated_at: "<!-- timestamp -->"
phase_state: bootstrapped
openspec_state: null
confidence_level: null
# phase_state values: bootstrapped | phase-1-in-progress | phase-1-done | phase-2-in-progress | phase-2-done | phase-3-in-progress | blocked-by-arch | blocked-by-data | applying | completed
# openspec_state values: null | propose_done | apply_done
# confidence_level values: null | CAO | TRUNG-BINH | THAP
---

# AGENT_TRANSPARENCY — Template
> Ticket: <!-- ticket-id -->
> Cập nhật lần cuối: <!-- timestamp -->

<!-- TODO: fill in — file này là template skeleton, không phải context thực -->

---

## Phase State

```
phase_state: bootstrapped
```

<!-- Values (chọn một):
  bootstrapped        ← mới khởi động, chưa vào pha nào
  phase-1-in-progress ← đang chạy Pha 1
  phase-1-done        ← Pha 1 hoàn thành (REQUIREMENT + EXPLORE_CONTEXT đã ghi)
  phase-2-in-progress ← đang chạy Pha 2 (spec)
  phase-2-done        ← Pha 2 hoàn thành (OpenSpec đã propose)
  phase-3-in-progress ← đang apply
  blocked-by-arch     ← architecture-reviewer gửi BLOCKER, chờ user quyết định
  blocked-by-data     ← thiếu dữ liệu/DB, đang chờ backfill/seed
  applying            ← /opsx:apply đang chạy
  completed           ← apply xong, knowledge-curator đã archive
-->

---

## Bootstrap Log

- Bootstrap tại: <!-- timestamp -->
- AGENTS.md: [ ] loaded
- RULES.md: [ ] loaded
- Lịch sử pha: <!-- Bootstrap | <time> | Task: <input> -->

---

## Nguồn đã đọc

- [ ] AGENTS.md
- [ ] .agent/rules/RULES.md
- [ ] REQUIREMENT.md
- [ ] EXPLORE_CONTEXT.md
- [ ] knowledge-snapshot.md
- [ ] Tài liệu (wiki/Confluence/PRD/…)
- [ ] Codebase (UA / Socraticode / search)
- [ ] Database (qua db-explorer)

---

## Tool / Skill đã gọi thành công

- [ ] requirement-analyst
- [ ] spec-extract
- [ ] db-explorer
- [ ] codebase-explorer
- [ ] architecture-reviewer
- [ ] knowledge-curator
- [ ] OpenSpec (`/opsx:explore`, `/opsx:propose`, `/opsx:apply`)
- [ ] Knowledge Graph MCP:
  - [ ] get_graph_stats
  - [ ] query_nodes
  - [ ] get_node_source
  - [ ] get_relationships / trace_call_chain
  - [ ] get_domain_detail
  - [ ] find_impact / find_entry_points
- [ ] Understand-Anything (`/understand`, `/understand-chat`)
- [ ] Socraticode

---

## Cảnh báo / Hạn chế

<!-- Ghi rõ các vấn đề: UA chưa chạy, thiếu quyền DB, tài liệu tin cậy thấp... -->

---

## Lịch sử pha

| Pha | Thời điểm | phase_state | Mô tả |
|-----|-----------|-------------|-------|
| Bootstrap | <!-- time --> | bootstrapped | Task: <!-- input --> |

<!-- Quy tắc cập nhật phase_state:
  - Mỗi khi phase_state thay đổi: cập nhật cả block `## Phase State` ở trên và thêm dòng mới vào bảng này.
  - Resume check: đọc `phase_state` trong block `## Phase State` — nếu là `phase-1-done` trở lên thì không re-trigger Pha 1.
-->

---

## Đánh giá Độ tin cậy tổng thể

**<!-- CAO / TRUNG BÌNH / THẤP -->** — <!-- 1-2 câu lý do -->
