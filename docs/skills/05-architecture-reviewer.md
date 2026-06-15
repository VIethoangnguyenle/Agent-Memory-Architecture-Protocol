# Skill: Architecture Reviewer

> **Tên**: `architecture-reviewer`  
> **Vai trò**: Kiến trúc sư đánh giá — phát hiện xung đột và rủi ro  
> **Trigger**: Trước `/task spec` trong pipeline

---

## Mục tiêu

Đối chiếu REQUIREMENT.md với kiến trúc hệ thống thực tế (từ EXPLORE_CONTEXT.md + knowledge-snapshot.md) để:

- Đánh giá mức độ **align** với kiến trúc hiện tại.
- Phát hiện **xung đột/rủi ro** (boundary violation, coupling, ownership conflict…).
- Ghi mức độ nghiêm trọng: `LOW` / `MEDIUM` / `HIGH` / `BLOCKER`.

---

## Các chiều đánh giá

| Chiều | Câu hỏi chính |
|-------|----------------|
| **Boundary** | Requirement có xâm phạm boundary module/service khác không? |
| **Ownership** | Thay đổi có chạm module do team khác sở hữu không? |
| **Coupling** | Solution dự kiến có tạo coupling mới không mong muốn không? |
| **Data integrity** | Thay đổi DB có ảnh hưởng consistency/constraint không? |
| **Non-functional** | Performance, security, scalability có bị ảnh hưởng không? |

---

## Mức độ nghiêm trọng

| Mức | Ý nghĩa | Hành động |
|-----|----------|-----------|
| `LOW` | Rủi ro nhỏ, có thể tiếp tục | Ghi nhận, tiếp tục pipeline |
| `MEDIUM` | Rủi ro trung bình, cần lưu ý | Ghi nhận, khuyến nghị review |
| `HIGH` | Rủi ro lớn, cần giải quyết | Hiển thị cho user, yêu cầu quyết định |
| `BLOCKER` | Không thể tiếp tục | **Dừng pipeline**, yêu cầu user resolve |

---

## Đầu ra

- Cập nhật `EXPLORE_CONTEXT.md` với phần đánh giá kiến trúc.
- Ghi Độ tin cậy kiến trúc (`CAO` / `TRUNG BÌNH` / `THẤP`).
- Nếu `BLOCKER` → ghi chi tiết vào `AGENT_TRANSPARENCY.md`.

---

## Tích hợp với conventions.yaml và author-dna.yaml

- Nếu `conventions.yaml` tồn tại → kiểm tra tên class/module trong REQUIREMENT có khớp convention không.
- Nếu `author-dna.yaml` tồn tại → kiểm tra design có align với coding philosophy không.
