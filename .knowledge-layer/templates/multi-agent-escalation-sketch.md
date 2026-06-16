---
status: DRAFT — Chỉ triển khai khi Violation Log confirm cần thiết
version: '0.1'
created: 2026-06-16
trigger: Sau 5+ tasks, nếu Violation Log cho thấy Lớp 1-3 không đủ
related:
  - .agent/workflows/task.md (flow hiện tại)
  - .agent/skills/spec-validator/SKILL.md §6 (DNA check hiện tại)
  - .knowledge-layer/templates/author-dna.yaml (DNA source)
---

# Multi-Agent Escalation Sketch (Kịch bản B)

> ⚠️ **Đây là bản DRAFT lưu trữ — KHÔNG phải spec triển khai.**
> Chỉ chuyển sang triển khai khi có data thực tế từ Violation Log.

---

## 1. Khi nào kích hoạt?

### Escalation Criteria (đọc từ Violation Log trong AGENT_TRANSPARENCY)

Sau **5 tasks** đã chạy với Lớp 1-3 (Session Boundary + DNA Re-read + Spec-Validator DNA Check):

| Pattern trong Violation Log | Chẩn đoán | Escalation |
|---|---|---|
| ≥ 2 tasks có **DNA BLOCK** violation dù DNA-RELOAD đã chạy | Mode Switching quá mạnh — re-read không đủ | → **Escalation A**: Executor Isolation |
| ≥ 3 tasks user **không tách session** + có WARN/BLOCK kèm theo | User không tuân thủ session boundary | → **Escalation B**: Hard Session Block |
| Cả hai pattern trên | Cả agent lẫn user đều có vấn đề | → **Escalation C**: Full Multi-Agent |
| Violation Log phần lớn CLEAN hoặc chỉ WARN nhẹ | Lớp 1-3 đã đủ | → **Không escalate** — giữ nguyên |

> **Quan trọng**: Quyết định escalation phải dựa trên data, không phải cảm tính.

---

## 2. Ba mức Escalation

### Escalation A: Executor Isolation (cho Mode Switching)

**Vấn đề**: Agent đã đọc DNA nhưng khi sinh code vẫn bị LLM pre-trained bias lấn át.

**Giải pháp**: Tách code generation ra session riêng — session chỉ chứa spec + DNA, không chứa toàn bộ context exploration.

**Thay đổi so với flow hiện tại**:

```
HIỆN TẠI (1 session cho Pha 3):
  Session: [Bootstrap + Spec + DNA-RELOAD + Code Gen + DNA-Check]
                                              ↑
                                     Context đã quá dài
                                     DNA bị đẩy xa

ESCALATION A (2 session cho Pha 3):
  Session 3a: [Bootstrap + Spec review + SPEC_HANDOFF sinh ra]
  Session 3b: [Bootstrap + DNA-RELOAD + SPEC_HANDOFF + Code Gen + DNA-Check]
                                                        ↑
                                               Context ngắn, DNA fresh
```

**File mới cần tạo**:

```yaml
# SPEC_HANDOFF.md — Giao diện giữa Session 3a và 3b
# Vị trí: .knowledge-layer/active/SPEC_HANDOFF.md

ticket_id: "<ticket>"
spec_path: "openspec/changes/<change-id>/"
impact_set:
  - path: "src/main/.../XxxHandler.java"
    change_type: MODIFY
    reason: "Thêm logic xử lý field Y"
  - path: "src/main/.../XxxExecutor.java"
    change_type: NEW
    reason: "Executor mới cho step Z"
boundary_constraints:
  - "KHÔNG chạm vào package xxx.core"
  - "KHÔNG sửa interface YyyService"
dna_focus:
  - "hard_principles: tất cả"
  - "complexity_thresholds: tất cả"
  - "style: constructor injection, early return"
```

**Thay đổi trong task.md**:
- Pha 3 bước 2 (Tóm tắt cho user) → sinh `SPEC_HANDOFF.md`
- Pha 3 bước 5 (Code gen) → **yêu cầu session mới**, chỉ load SPEC_HANDOFF + DNA + spec
- Không cần Reviewer Agent riêng — spec-validator DNA check vẫn chạy ở cuối

**Effort**: ~50 dòng sửa task.md + 1 template mới. Trung bình.

---

### Escalation B: Hard Session Block (cho user behavior)

**Vấn đề**: User không tách session dù được nhắc → context dài → dilution.

**Giải pháp**: Chuyển SESSION-BOUNDARY từ WARN sang BLOCK.

**Thay đổi trong task.md**:

```markdown
## Thay đổi so với hiện tại

# HIỆN TẠI:
- Nếu user tiếp tục trong cùng session:
  - Ghi WARN vào AGENT_TRANSPARENCY
  - **Không block** — vẫn cho phép tiếp tục

# ESCALATION B:
- Nếu user tiếp tục trong cùng session:
  - Ghi BLOCK vào AGENT_TRANSPARENCY
  - **Từ chối tiếp tục**: "Vui lòng mở session mới. Context hiện tại đã quá dài
    để đảm bảo chất lượng code."
  - Chỉ cho phép bypass nếu user gõ: `/force-continue` (ghi audit trail)
```

**Effort**: ~10 dòng sửa task.md. Rất nhỏ.

**Rủi ro**: Gây khó chịu cho user nếu task nhỏ, đơn giản.
**Mitigation**: Chỉ block khi token count > threshold (e.g. > 50K tokens trong session).

---

### Escalation C: Full Multi-Agent (cho cả hai vấn đề)

**Vấn đề**: Cả Mode Switching lẫn session discipline đều không giải quyết được.

**Giải pháp**: 3 roles (Architect / Executor / Reviewer), mỗi role 1 session, giao tiếp qua file.

#### Vai trò & Phạm vi

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (task.md)                        │
│  Quyết định role nào chạy, kiểm tra handoff, routing BLOCK     │
├─────────────┬──────────────────┬────────────────────────────────┤
│  Session 1  │    Session 2     │          Session 3             │
│  ARCHITECT  │    EXECUTOR      │          REVIEWER              │
│             │                  │                                │
│ Input:      │ Input:           │ Input:                         │
│ - Ticket    │ - SPEC_HANDOFF   │ - SPEC_HANDOFF                 │
│ - Context   │ - Spec artifacts │ - EXECUTION_RESULT             │
│             │ - DNA + Conv     │ - Spec artifacts               │
│ Output:     │                  │ - DNA + Conv                   │
│ - REQ.md    │ Output:          │                                │
│ - EXPLORE   │ - Code changes   │ Output:                        │
│ - Spec      │ - EXECUTION_     │ - REVIEW_REPORT                │
│ - SPEC_     │   RESULT.md      │   (PASS|PASS_WITH_NOTES|BLOCK) │
│   HANDOFF   │                  │                                │
│             │ Boundary:        │ Boundary:                      │
│ Boundary:   │ ❌ Sửa REQ/Spec │ ❌ Sửa code                    │
│ ❌ Sinh code│ ❌ Mở rộng scope │ ❌ Sửa spec                    │
│ ❌ Apply    │ ✅ Chỉ code      │ ✅ Chỉ verify                  │
│ ✅ Design   │    trong impact  │    + recommend                 │
└─────────────┴──────────────────┴────────────────────────────────┘
```

#### Handoff Contracts

3 file giao tiếp giữa các role — đặt tại `.knowledge-layer/active/`:

**a. SPEC_HANDOFF.md** (Architect → Executor)

```markdown
# SPEC_HANDOFF
ticket_id: ...
spec_path: openspec/changes/<change-id>/
impact_set:
  - file, change_type, reason
boundary_constraints:
  - "Không chạm ..."
dna_focus:
  - section cần đặc biệt chú ý trong DNA
notes_for_executor:
  - Context bổ sung mà Architect muốn truyền đạt
```

**b. EXECUTION_RESULT.md** (Executor → Reviewer)

```markdown
# EXECUTION_RESULT
ticket_id: ...
changed_files:
  - path, change_summary, lines_changed
dna_reload_done: true
dna_violations_self_detected:
  - rule, severity, fixed, note
notes:
  - Bất kỳ concern nào Executor muốn flag
```

**c. REVIEW_REPORT.md** (Reviewer → Orchestrator)

```markdown
# REVIEW_REPORT
ticket_id: ...
verdict: PASS | PASS_WITH_NOTES | BLOCK

checks:
  spec_compliance: PASS | FAIL — mô tả
  boundary_compliance: PASS | FAIL — mô tả
  dna_compliance: PASS | FAIL — mô tả (dùng logic §6 spec-validator)
  ac_coverage: PASS | FAIL — mô tả

violations:
  - rule, severity, file, suggestion

notes:
  - Khuyến nghị cho Architect/Executor nếu cần vòng lặp lại

route_back:
  - null               ← nếu PASS
  - ARCHITECT           ← nếu lỗi ở spec/design
  - EXECUTOR            ← nếu lỗi ở code/DNA
```

#### Routing Logic (trong task.md)

```
Orchestrator nhận REVIEW_REPORT:

IF verdict == PASS:
  → Archive (knowledge-curator)
  → Done

IF verdict == PASS_WITH_NOTES:
  → Hiển thị notes cho user
  → User decide: archive hoặc gửi lại Executor

IF verdict == BLOCK:
  IF route_back == ARCHITECT:
    → Mở session mới cho Architect
    → Architect sửa spec → sinh SPEC_HANDOFF mới
    → Quay lại Executor
  IF route_back == EXECUTOR:
    → Mở session mới cho Executor
    → Executor fix violations → sinh EXECUTION_RESULT mới
    → Quay lại Reviewer

Max loop: 2 vòng. Nếu vẫn BLOCK → escalate cho user quyết định.
```

#### Effort ước tính

| Item | Effort |
|------|--------|
| 3 template mới (SPEC_HANDOFF, EXECUTION_RESULT, REVIEW_REPORT) | Trung bình |
| Sửa task.md §3 thành multi-session routing | Cao |
| Tái sử dụng spec-validator §6 cho Reviewer | Thấp (đã có) |
| Test & iterate | Cao |
| **Tổng** | **~200+ dòng, 5+ file, vài ngày** |

---

## 3. Quyết định Escalation: Decision Tree

```
                    Violation Log sau 5 tasks
                            │
                 ┌──────────┴──────────┐
                 │                     │
          Phần lớn CLEAN         Có violations
          hoặc WARN nhẹ          đáng kể
                 │                     │
           ✅ Giữ nguyên        ┌──────┴──────┐
           Lớp 1-3 đủ          │             │
                          DNA BLOCK      SESSION WARN
                          chiếm đa số   chiếm đa số
                                │             │
                         Escalation A    Escalation B
                      (Executor Iso)  (Hard Block)
                                │             │
                                └──────┬──────┘
                                       │
                                 Nếu vẫn không đủ
                                 sau 3 tasks nữa
                                       │
                                 Escalation C
                               (Full Multi-Agent)
```

---

## 4. Nguyên tắc thiết kế

1. **Progressive**: A → B → C, không nhảy thẳng vào C.
2. **Data-driven**: Mỗi mức escalation phải có evidence từ Violation Log.
3. **Reversible**: Nếu sau escalation violation giảm hẳn, có thể quay lại mức thấp hơn.
4. **Generic**: Handoff contracts không hardcode project-specific rules — đọc từ DNA/conventions.
5. **Compatible**: Không break flow hiện tại — chỉ thêm session split points.

---

## 5. Rủi ro & Trade-off của Multi-Agent

| Rủi ro | Mô tả | Mitigation |
|--------|-------|------------|
| **Context loss qua handoff** | SPEC_HANDOFF có thể miss nuance mà Architect biết | Template chuẩn hóa + `notes_for_executor` field |
| **Overhead cho task nhỏ** | 3 sessions + 3 handoff files cho task sửa 2 dòng code | Chỉ enforce cho task HIGH/CRITICAL risk |
| **Token cost x3** | Mỗi session bootstrap riêng | Chấp nhận — trade-off cho quality |
| **Loop vô hạn** | Reviewer BLOCK → Executor fix → Reviewer BLOCK lại | Max 2 vòng, sau đó escalate user |
| **Maintenance complexity** | 3 template + routing logic | Tái sử dụng spec-validator (đã có) |

---

## 6. Khi nào KHÔNG nên Multi-Agent

- Task LOW risk (sửa typo, thêm config, rename)
- Token budget giới hạn
- User muốn tốc độ hơn quality
- Project mới chưa có DNA/conventions (không có gì để verify)

→ Gợi ý: thêm field `risk_level` vào REQUIREMENT.md, chỉ trigger Multi-Agent khi `risk_level: HIGH | CRITICAL`.
