# Skill: Infra TDD (Technical Design Document)

> **Tên**: `infra-tdd`  
> **Vai trò**: Viết Technical Design Document chuẩn hoá 5 tầng hybrid  
> **Trigger**: `/tdd <module-name>`, "viết TDD", "design doc"

---

## Mục tiêu

Tạo TDD chuẩn hoá trả lời **5 câu hỏi** theo format hybrid — cho cả non-tech (BA/PM) và tech (Dev/Architect) đọc cùng một tài liệu.

---

## Cấu trúc 5 Tầng

| Tầng | Đối tượng | Mục đích |
|------|-----------|----------|
| **T0 — Bối cảnh Nghiệp vụ** | BA, PM, Stakeholder | Nghiệp vụ giải quyết gì? Flow nào? Business rules? |
| **T1 — Chiến lược** | Tech Lead, Architect | Ai bị đau? Metric nào cải thiện? Ai ký duyệt? |
| **T2 — Kiến trúc** | Dev, Architect | Component, boundary, data flow, failure domain? |
| **T3 — Quyết định** | Dev, Architect | Alternatives? Tại sao chọn cái này? Trade-off? |
| **T4 — Vận hành** | Tech Leads, Trưởng phòng | Monitoring metrics, alert thresholds, config reference |

---

## Knowledge-First Protocol

**BẮT BUỘC** sử dụng knowledge tools (UA Knowledge Graph, Socraticode, db-explorer, codebase-explorer) trước khi viết mỗi tầng. Mọi claim phải dựa trên evidence thực tế.

---

## Format Standards

- **FS-1**: Attribution Header bắt buộc.
- **FS-2**: Navigation Footer bắt buộc.
- **FS-3**: Hub + Sub-doc khi > 500 dòng.
- **FS-4**: Design Patterns Summary Table trong T2.
- **FS-5**: Code Examples (NÊN / KHÔNG NÊN).
- **FS-6**: Configuration Reference trong T4.

---

## Đầu ra

| File | Vị trí |
|------|--------|
| TDD file | `docs/tdd/<module>-TDD.md` |
| ADR files | `docs/tdd/<module>-adr/NNNN-title.md` |
