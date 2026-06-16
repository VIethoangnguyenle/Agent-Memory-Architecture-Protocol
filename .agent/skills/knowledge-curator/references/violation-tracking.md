# [M3] Violation Pattern Tracking

> Reference file — extracted from SKILL.md for progressive disclosure.

## Mục đích

Tích lũy pattern vi phạm rule/workflow qua các task để nhận diện vấn đề hệ thống (không phải lỗi ngẫu nhiên).

## `track_violation_patterns(ticket_id)`

```
INPUT: ticket_id — ticket vừa archive

STEPS:
1. Đọc archive/{ticket_id}/AGENT_TRANSPARENCY.md
   → Tìm tất cả entry có format:
     - "[VIOLATION]", "[RULE-VIOLATION]", "[WORKFLOW-VIOLATION]"
     - Rule ID bị vi phạm (vd: R-Flow-3, R-Apply-1)
     - Mô tả pattern hành vi

2. Với mỗi violation tìm thấy:
   a. Đọc violation_pattern từ description (normalize về dạng slug)
      Ví dụ: "skip confirm step" → pattern_id = "skip-confirm-step"
   b. Kiểm tra .knowledge-layer/long-term/knowledge-snapshot.md
      section "[M3] Violation Pattern Tracking":
      - Nếu pattern_id đã tồn tại:
        → Tăng "Lần xảy ra" += 1
        → Cập nhật "Task gần nhất" = ticket_id
      - Nếu pattern_id chưa tồn tại VÀ đây là lần xảy ra ≥ 2:
        → Thêm row mới vào bảng vi phạm

3. Cập nhật "Violation Trend" section:
   - Tổng số patterns
   - Pattern phổ biến nhất (max "Lần xảy ra")

4. Nếu bất kỳ pattern có "Lần xảy ra" ≥ 5:
   → WARN vào AGENT_TRANSPARENCY:
     "[M3-ALERT] Pattern '{pattern_id}' đã xảy ra {n} lần.
      Cân nhắc bổ sung rule mới vào RULES.md để ngăn lặp lại."

5. Ghi vào ARCHIVE_META.md:
   violations_tracked: {n_violations_found}
   new_patterns_added: {n_new}
```

## Tích hợp vào archive_active_context

Gọi `track_violation_patterns` như một bước trong `archive_active_context`:

```
archive_active_context(ticket_id):
  ... (các steps hiện tại) ...
  IF status == "completed":
    → update_knowledge_snapshot(discoveries)
    → track_violation_patterns(ticket_id)   ← M3: thêm bước này
  → reset_active_context()
```

## Bảo mật / Privacy

- Không lưu tên user, IP, hay thông tin định danh.
- Chỉ lưu pattern hành vi (what happened, not who did it).
- Violation data dùng để cải thiện rules, không để blame.
