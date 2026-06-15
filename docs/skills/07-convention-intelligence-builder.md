# Skill: Convention Intelligence Builder

> **Tên**: `convention-intelligence-builder`  
> **Vai trò**: Scan codebase → extract naming conventions và design patterns  
> **Trigger**: `/convention-scan`, onboard project mới, sau refactor lớn

---

## Mục tiêu

Extract **implicit conventions** từ codebase thực tế và đưa vào `conventions.yaml` để agent dùng khi sinh spec và code.

---

## 5 Chiều Scan

| Chiều | Nội dung |
|-------|----------|
| **File & Class Naming** | Suffix patterns (*Service, *Repository, *Handler…) |
| **Package / Layer** | Domain/layer structure, architecture style |
| **Architecture Patterns** | Controller → Logic dispatch mechanisms |
| **Upstream Conventions** | Base classes, interfaces bắt buộc từ shared library |
| **Test & Config** | Test class suffix, method naming, config patterns |

---

## Output: `conventions.draft.yaml` (7 sections)

1. Naming Conventions — class suffixes, method naming
2. Package Structure — root, depth, layers
3. Design Patterns — patterns detected với evidence
4. Upstream Constraints — mandatory interfaces/base classes
5. Test Conventions — class suffix, method pattern
6. Exceptions — nơi code KHÔNG follow convention
7. Needs Review — patterns cần user xác nhận

---

## 3 Chế độ scan

| Mode | Mô tả |
|------|--------|
| **Full** | Scan toàn bộ codebase |
| **Delta** | Chỉ files changed since last scan |
| **Update** | Delta + merge vào conventions.yaml hiện tại |

Sau khi review: `/approve-conventions` để commit chính thức.
