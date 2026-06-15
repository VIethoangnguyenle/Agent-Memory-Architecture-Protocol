# Skill: Spec Extract

> **Tên**: `spec-extract`  
> **Vai trò**: Document Analyst — trích yêu cầu từ tài liệu phi cấu trúc  
> **Trigger**: Nhánh `HAS_DOC_ONLY` trong workflow `/task`

---

## Mục tiêu

Trích xuất **spec có cấu trúc** từ tài liệu dạng tự do (wiki, Confluence, PRD, RFC) và chuyển vào `REQUIREMENT.md`. Đi kèm **đánh giá Độ tin cậy** để pipeline biết có nên tiếp tục hay dừng lại chờ tài liệu tốt hơn.

---

## Khi nào dùng

- User cung cấp link tài liệu nhưng **chưa có ticket**.
- Tài liệu chứa yêu cầu nghiệp vụ nhưng chưa được chuẩn hoá.

---

## Quy trình

### Bước 1 — Đọc tài liệu nguồn

- Sử dụng MCP Confluence (`confluence_get_page`, `confluence_search`) hoặc đọc URL trực tiếp.
- Ghi nhận metadata: tên trang, tác giả, ngày cập nhật.

### Bước 2 — Trích xuất có cấu trúc

Từ nội dung tài liệu, extract:

- **Business context**: Mục tiêu, đối tượng, vấn đề cần giải quyết.
- **Functional requirements**: Chức năng cụ thể được mô tả.
- **Non-functional requirements**: Performance, security, compliance…
- **Acceptance Criteria**: Bất kỳ tiêu chí nào tài liệu đề cập.

### Bước 3 — Đánh giá Độ tin cậy

| Mức | Điều kiện |
|-----|-----------|
| **CAO** | Tài liệu rõ ràng, có AC cụ thể, tác giả xác định |
| **TRUNG BÌNH** | Tài liệu đủ thông tin nhưng thiếu chi tiết kỹ thuật |
| **THẤP** | Tài liệu mơ hồ, thiếu scope, không có AC |

### Bước 4 — Ghi output

- Ghi vào `.knowledge-layer/active/REQUIREMENT.md`.
- Ghi nguồn tài liệu (URL, tên trang) để trace.
- Nếu Độ tin cậy = THẤP → pipeline tạm dừng, thông báo user.

---

## Đầu ra

| File | Vị trí |
|------|--------|
| `REQUIREMENT.md` | `.knowledge-layer/active/REQUIREMENT.md` |

---

## Nguyên tắc

- **Trung thành với nguồn**: Không suy diễn thêm requirement ngoài nội dung tài liệu.
- **Ghi rõ Độ tin cậy**: Để pipeline biết có nên tiếp tục hay chờ tài liệu bổ sung.
- **Ghi rõ gaps**: Những phần tài liệu thiếu → "Vấn đề mở" trong REQUIREMENT.md.
