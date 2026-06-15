# Skill: Requirement Analyst

> **Tên**: `requirement-analyst`  
> **Vai trò**: Business Analyst — chuẩn hoá yêu cầu thành REQUIREMENT.md  
> **Trigger**: Nhánh `HAS_TICKET` trong workflow `/task`

---

## Mục tiêu

Biến ticket thô (Jira, Confluence, PRD, hoặc mô tả miệng) thành file `REQUIREMENT.md` chuẩn hoá, đảm bảo:

- Rõ ràng về **scope** (in-scope / out-of-scope).
- Acceptance Criteria (AC) cụ thể, đo được.
- Giả định và vấn đề mở được liệt kê rõ.
- Context đủ để các skill tiếp theo (db-explorer, codebase-explorer, architecture-reviewer) hoạt động chính xác.

---

## Quy trình

### Bước 1 — Thu thập nguồn

- Đọc ticket gốc (link/ID do user cung cấp).
- Đọc tất cả tài liệu liên kết trong ticket (wiki, PRD, design doc…).
- Nếu có `knowledge-snapshot.md` → đọc để hiểu bối cảnh hệ thống tổng quan.

### Bước 2 — Phân tích và chuẩn hoá

Sinh file `.knowledge-layer/active/REQUIREMENT.md` với các section:

1. **Context**: Bối cảnh business, ai liên quan, tại sao cần làm.
2. **As-is / To-be**: Trạng thái hiện tại vs trạng thái mong muốn.
3. **Scope**: In-scope (rõ ràng) và Out-of-scope (tránh hiểu nhầm).
4. **Acceptance Criteria**: Danh sách AC dạng checklist.
5. **Giả định**: Những điều agent assume nhưng chưa được xác nhận.
6. **Vấn đề mở**: Câu hỏi cần user/BA trả lời trước khi tiếp tục.

### Bước 3 — Xác nhận với user

- Hiển thị REQUIREMENT.md cho user review.
- Thu thập feedback, cập nhật lại nếu cần.

---

## Đầu ra

| File | Vị trí |
|------|--------|
| `REQUIREMENT.md` | `.knowledge-layer/active/REQUIREMENT.md` |

---

## Nguyên tắc

- **Không bịa requirement**: Nếu thiếu thông tin → ghi vào "Giả định" hoặc "Vấn đề mở".
- **Ngôn ngữ trung tính**: Không encode domain cụ thể — chỉ mô tả business logic.
- **Trung thực về Độ tin cậy**: Nếu ticket mơ hồ → ghi rõ trong metadata.
