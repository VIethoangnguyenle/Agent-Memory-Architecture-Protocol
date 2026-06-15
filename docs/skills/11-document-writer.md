# Skill: Document Writer

> **Tên**: `document-writer`  
> **Vai trò**: Khung chuẩn viết tài liệu kỹ thuật  
> **Trigger**: Khi cần tạo mới hoặc cập nhật tài liệu (README, ADR, runbook…)

---

## Mục tiêu

Tạo tài liệu **đúng**, **hữu ích**, **dễ bảo trì**, tránh suy diễn không có bằng chứng.

---

## 6 Loại tài liệu hỗ trợ

1. **README / Overview** — Mục đích, phạm vi, quick start.
2. **Architecture / Design** — Bối cảnh, kiến trúc, patterns, trade-offs.
3. **How-to / Usage guide** — Các bước thực hiện, ví dụ.
4. **Runbook / Troubleshooting** — Triệu chứng, chẩn đoán, xử lý.
5. **ADR** — Context, Decision, Alternatives, Consequences.
6. **Module reference** — Tài liệu module hạ tầng.

---

## Quy trình 8 giai đoạn

1. **Xác định loại tài liệu** — Hỏi user nếu chưa rõ.
2. **Thu thập thông tin** — Bài toán, phạm vi, cách dùng, kiến trúc.
3. **Quy tắc bằng chứng** — Mọi mô tả phải được xác minh từ source code.
4. **Chọn cấu trúc** — Theo loại tài liệu.
5. **Visualize đúng chỗ** — Mermaid khi cần, không thêm để "đủ form".
6. **Cách viết** — Tiếng Việt, rõ ràng, ưu tiên What/When/Why.
7. **Đồng bộ** — Sync với tài liệu liên quan khi cần.
8. **Validation** — Kiểm tra trước khi hoàn tất.

---

## Nguyên tắc cốt lõi

> Code trả lời "How". Tài liệu ưu tiên trả lời "What", "When", và "Why".  
> Tài liệu tốt không phải dài nhất — đó là tài liệu đúng, ngắn gọn, cập nhật.
