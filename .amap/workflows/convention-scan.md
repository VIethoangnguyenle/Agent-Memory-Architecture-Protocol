---
description: Scan codebase để extract naming conventions và design patterns → sinh conventions.draft.yaml cho user review.
---

# /convention-scan — Workflow Scan Convention

Workflow này orchestrate skill `convention-intelligence-builder` để extract conventions từ codebase.

---

## Bước 0 — Kiểm tra prerequisites

```
CHECK 1: Code exploration tool sẵn sàng?
  CALL: {{ tools.code_status }}()
  → Không sẵn sàng:
    "⚠️ Code exploration chưa sẵn sàng.
     Chạy /index-source trước để lập chỉ mục codebase."
    → ABORT

CHECK 2: conventions.yaml đã tồn tại?
  → Tồn tại + meta.status == "approved":
    HỎI user:
    "conventions.yaml đã có (approved). Chọn mode:
     [U] Update — scan delta (chỉ files thay đổi), merge kết quả
     [R] Rebuild — scan lại toàn bộ từ đầu
     [S] Skip — không scan, giữ nguyên"
    → User chọn [S]: ABORT
    → User chọn [U] hoặc [R]: truyền mode vào skill
  → Không tồn tại hoặc status != "approved":
    → Tiếp tục (full scan mặc định)

CHECK 3: conventions.draft.yaml đã tồn tại từ scan trước?
  → Tồn tại:
    HỎI user:
    "conventions.draft.yaml đã tồn tại (chưa approve). Chọn:
     [O] Overwrite — scan mới, ghi đè draft cũ
     [K] Keep — giữ draft cũ, không scan
     [A] Approve — chuyển sang /approve-conventions luôn"
    → User chọn [K]: ABORT
    → User chọn [A]: chuyển sang workflow /approve-conventions, ABORT workflow này
    → User chọn [O]: tiếp tục (overwrite)
  → Không tồn tại: tiếp tục
```

---

## Bước 1 — Dispatch skill

```
INVOKE: convention-intelligence-builder
  Truyền:
    - scan_mode: full | update | rebuild (từ Bước 0)
    - project_roots: (từ resolved-config hoặc cwd)
    - upstream_roots: (nếu có shared library)

  Skill thực hiện:
    1. Structural Audit (5 chiều)
    2. Pattern Consolidation
    3. Sinh conventions.draft.yaml
    4. Summary Report

  CHI TIẾT LOGIC: Xem {{ platform.framework_root }}/skills/convention-intelligence-builder/SKILL.md
```

---

## Bước 2 — Post-scan report

```
SAU KHI skill hoàn thành:

VERIFY: {{ platform.framework_root }}/knowledge/long-term/conventions.draft.yaml tồn tại?
  → Không: ERROR "Scan hoàn thành nhưng draft không được tạo. Kiểm tra log."
  → Có: tiếp tục

HIỂN THỊ cho user:
  "✅ Convention scan hoàn thành.

   📊 Kết quả:
   • {n} naming conventions ({n} high, {n} medium, {n} low confidence)
   • {n} design patterns detected
   • {n} upstream constraints
   • {n} exceptions/inconsistencies cần review

   📄 Draft: {{ platform.framework_root }}/knowledge/long-term/conventions.draft.yaml
   → Mở file trong IDE, review + edit trực tiếp.
   → Khi sẵn sàng: /approve-conventions để commit chính thức."
```

---

## Bước 3 — Cập nhật AGENT_TRANSPARENCY

```
APPEND vào {{ platform.framework_root }}/knowledge/active/AGENT_TRANSPARENCY.md:
  [x] /convention-scan: scan hoàn thành
  - Mode: {full | update | rebuild}
  - Patterns: {n} high, {n} medium, {n} low
  - Draft: conventions.draft.yaml (chờ review)
  - Next: /approve-conventions
```

---

## Error Cases

| Tình huống | Hành động |
|---|---|
| Code exploration chưa sẵn sàng | ABORT, hướng dẫn `/index-source` |
| Scan thất bại giữa chừng | Ghi WARN vào AGENT_TRANSPARENCY, báo user |
| Draft file đã tồn tại từ scan trước | Hỏi: overwrite hay giữ bản cũ? |
| Không tìm được pattern nào (codebase quá nhỏ) | WARN, tạo draft minimal với note |
