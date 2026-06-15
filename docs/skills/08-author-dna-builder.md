# Skill: Author DNA Builder

> **Tên**: `author-dna-builder`  
> **Vai trò**: Infer coding philosophy → interview tác giả → encode judgment layer  
> **Trigger**: `/dna-scan`, sau convention-scan

---

## Mục tiêu

Tạo `author-dna.yaml` — **judgment layer** mà agent dùng khi evaluate design và propose solution. Khác với `conventions.yaml` (capture naming/structure), Author DNA capture **coding philosophy và decision principles**.

| | conventions.yaml | author-dna.yaml |
|-|-----------------|-----------------|
| **Capture** | Naming, suffix, package | Coding philosophy, decision principles |
| **Nguồn** | Extract từ code | Infer từ code + confirm với tác giả |
| **Agent dùng như** | Naming rule | Judgment lens khi evaluate design |

---

## Quy trình — 4 giai đoạn

### Giai đoạn 1: Code Evidence Scan
Scan 5 chiều: complexity profile, design patterns, if/else substitution, layer boundary discipline, duplication vs abstraction tendency.

### Giai đoạn 2: Hypothesis Generation
Từ evidence → tạo danh sách hypothesis có cấu trúc (id, claim, confidence, evidence, question).

### Giai đoạn 3: Interview Protocol
Trình bày hypothesis cho tác giả → `[C]onfirm` / `[R]eject` / `[P]artially` / `[E]xpand`.

### Giai đoạn 4: Encode → author-dna.draft.yaml
Confirmed hypothesis → `hard_principles` / `style_preferences` / `creative_overrides`. Rejected → `rejected_hypotheses` (để không re-infer).

---

## Cách agent dùng author-dna.yaml

- **Pha 2 (Spec)**: Kiểm tra solution có vi phạm hard principle không → tự refactor trước khi propose.
- **Pha 3 (Apply)**: Scan code diff cho nested if, switch, instanceof → flag DNA alerts.
- **Architecture Review**: Kiểm tra design có align với DNA không → WARN nếu không.

---

## Đầu ra

| File | Vị trí |
|------|--------|
| `author-dna.draft.yaml` | `.knowledge-layer/templates/author-dna.draft.yaml` |
| `author-dna.yaml` (sau `/approve-dna`) | `.knowledge-layer/templates/author-dna.yaml` |
