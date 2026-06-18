---
description: Scan codebase để infer coding philosophy → interview tác giả → sinh author-dna.draft.yaml.
---

# /dna-scan — Workflow Scan Author DNA

Workflow này orchestrate skill `author-dna-builder` để tạo coding DNA — judgment layer cho agent.

> **Thứ tự khuyến nghị**: Chạy `/convention-scan` trước → `/dna-scan` sau.
> DNA builder cần conventions.yaml để cross-check và tránh duplicate (SKILL.md §4 Check 1).

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
  → Không tồn tại:
    WARN:
    "⚠️ conventions.yaml chưa có. DNA scan vẫn chạy được,
     nhưng sẽ không thể cross-check duplicate với conventions.
     Khuyến nghị chạy /convention-scan trước.
     Tiếp tục không? [Y/N]"
    → User chọn N: ABORT
    → User chọn Y: tiếp tục với WARN

CHECK 3: author-dna.yaml đã tồn tại?
  → Tồn tại + meta.status == "approved":
    HỎI user:
    "author-dna.yaml đã có (approved). Chọn mode:
     [A] Add — thêm principle mới, giữ cái cũ
     [U] Update — cập nhật principle hiện có
     [R] Full rescan — scan lại toàn bộ từ đầu
     [S] Skip — không scan"
    → User chọn [S]: ABORT
    → Truyền mode vào skill
  → Không tồn tại hoặc status != "approved":
    → Tiếp tục (full scan mặc định)
```

---

## Bước 1 — Dispatch skill

```
INVOKE: author-dna-builder
  Truyền:
    - scan_mode: full | add | update (từ Bước 0)
    - conventions_path: {{ platform.framework_root }}/knowledge/long-term/conventions.yaml (nếu có)

  Skill thực hiện 4 giai đoạn:
    1. Code Evidence Scan (5 dimensions)
    2. Hypothesis Generation
    3. Interview Protocol (interactive với user)
    4. Encode → author-dna.draft.yaml

  CHI TIẾT LOGIC: Xem {{ platform.framework_root }}/skills/author-dna-builder/SKILL.md
```

> **Lưu ý:** Giai đoạn 3 (Interview) là INTERACTIVE — agent hỏi, user trả lời.
> Workflow không can thiệp vào interview flow — để skill xử lý.

---

## Bước 2 — Post-scan report

```
SAU KHI skill hoàn thành (tất cả 4 giai đoạn):

VERIFY: {{ platform.framework_root }}/knowledge/long-term/author-dna.draft.yaml tồn tại?
  → Không: ERROR "Scan + interview hoàn thành nhưng draft không được tạo."
  → Có: tiếp tục

HIỂN THỊ cho user:
  "✅ DNA scan + interview hoàn thành.

   📊 Kết quả:
   • {n} hypotheses proposed
   • {n} confirmed, {n} rejected, {n} partial
   • {n} principles author-added (ngoài code evidence)
   • Hard principles: {n} | Style preferences: {n} | Creative overrides: {n}
   • Mechanically checkable (SP1a): {n}/{total}

   📄 Draft: {{ platform.framework_root }}/knowledge/long-term/author-dna.draft.yaml
   → Mở file trong IDE, review + chỉnh trực tiếp.
   → Khi sẵn sàng: /approve-dna để commit chính thức."
```

---

## Bước 3 — Cập nhật AGENT_TRANSPARENCY

```
APPEND vào {{ platform.framework_root }}/knowledge/active/AGENT_TRANSPARENCY.md:
  [x] /dna-scan: scan + interview hoàn thành
  - Mode: {full | add | update}
  - Giai đoạn 1 (scan): {n} methods analyzed, {n} patterns found
  - Giai đoạn 2 (hypothesis): {n} hypotheses ({n} HIGH, {n} MEDIUM, {n} LOW)
  - Giai đoạn 3 (interview): {n} confirmed, {n} rejected, {n} partial
  - Giai đoạn 4 (encode): author-dna.draft.yaml generated
  - Cross-check conventions: {done | skipped (no conventions.yaml)}
  - Draft: author-dna.draft.yaml (chờ review)
  - Next: /approve-dna
```

---

## Error Cases

| Tình huống | Hành động |
|---|---|
| Code exploration chưa sẵn sàng | ABORT, hướng dẫn `/index-source` |
| conventions.yaml chưa có | WARN, cho phép tiếp tục nếu user confirm |
| Interview bị gián đoạn (session truncate) | Draft lưu partial — user chạy lại `/dna-scan [A]` để bổ sung |
| Draft file đã tồn tại từ scan trước | Hỏi: overwrite hay giữ? |
| Không tìm được pattern (codebase quá nhỏ / quá generic) | WARN, tạo draft minimal, gợi ý interview open-ended |
