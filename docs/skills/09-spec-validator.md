# Skill: Spec Validator

> **Tên**: `spec-validator`  
> **Vai trò**: Quality gate — kiểm tra spec trước và sau khi apply  
> **Trigger**: Trước và sau `/task apply`

---

## Mục tiêu

- **Pre-apply gate**: Chặn apply khi spec có vấn đề nghiêm trọng.
- **AC coverage check**: Đảm bảo mỗi AC trong REQUIREMENT.md được cover bởi ít nhất 1 task.
- **Post-apply verify**: Sau apply, kiểm tra files đã thay đổi vs spec dự kiến.

Skill này là **quality gate** — không sinh spec, không sửa code.

---

## 3 Hàm chính

### `pre_apply_gate(spec_path, requirement_path)`

6 checks:
- [C1] Spec có change_id rõ ràng?
- [C2] proposal.md có "what" và "why"?
- [C3] spec/tasks có ít nhất 1 task?
- [C4] Spec có chạm ngoài PROJECT_ROOTS?
- [C5] OPENSPEC_STATE = "propose_done"?
- [C6] Contract-Spec alignment (optional).

Kết quả: **PASS** hoặc **BLOCK**.

### `check_ac_coverage(spec_path, requirement_path)`

So sánh AC list trong REQUIREMENT.md với tasks trong spec. Báo WARN nếu có AC chưa được cover. Không block — chỉ inform.

### `post_apply_verify(spec_path, changed_files)`

So sánh files dự kiến bị chạm (từ spec) với files thực tế đã thay đổi. Báo WARN nếu mismatch. Không auto-rollback.

---

## Tích hợp trong pipeline

```
/task apply → pre_apply_gate → check_ac_coverage → [user confirm] → apply → post_apply_verify
```

Nếu `pre_apply_gate` = BLOCK → dừng hoàn toàn, gợi ý chạy lại `/task spec`.
