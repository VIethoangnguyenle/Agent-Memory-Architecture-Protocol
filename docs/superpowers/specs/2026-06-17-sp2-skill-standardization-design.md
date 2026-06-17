# SP2 — Chuẩn hoá Skills (Skill Standardization)

> **Phiên bản:** 1.0 | **Ngày:** 2026-06-17
> **Scope:** Chuẩn hoá 14 skills về frontmatter schema, body sections, và I/O contract thống nhất.
> **Approach:** Lint-first — viết validator trước, chạy report, sửa theo report.

---

## 1. Bối cảnh & Vấn đề

### 1.1 Hiện trạng

AMAP v3 có 14 skills trong `.agent/skills/`. Qua audit, mức chuẩn hoá rất lệch:

| Tiêu chí | Có | Thiếu |
|---|---|---|
| `pre_conditions` frontmatter | 6/14 | 8/14 |
| Anti-pattern ("KHÔNG dùng cho") | 10/14 | 4/14 |
| Output/I/O contract rõ ràng | 10/14 | 4/14 |
| Gotchas section | 6/14 | 8/14 |

### 1.2 Hệ quả

- **Orchestrator routing sai**: Thiếu `pre_conditions` → skill chạy khi chưa đủ context.
- **Knowledge-curator mù**: Thiếu `outputs` → không biết skill ghi file nào để archive.
- **Agent chọn sai skill**: Thiếu "KHÔNG dùng cho" → gọi skill sai vai trò.
- **Không enforce được dài hạn**: Thêm skill mới không có chuẩn để tuân theo.

### 1.3 Scope KHÔNG bao gồm

- Gate trùng lặp (W9) — tách scope riêng.
- Portability layer / tool adapter — thuộc SP3+.

---

## 2. Thiết kế

### 2.1 Triết lý Hybrid

Kết hợp 2 trường phái:

- **Từ Superpowers (industry best-practice 2026):** Description tự mô tả trigger + anti-pattern
  ("Dùng khi... KHÔNG dùng cho..."). Tối ưu cho discoverability — model tự chọn skill từ description.
- **Từ AMAP (orchestrator-driven):** Giữ `pre_conditions` + `outputs` machine-parseable vì
  AMAP cần orchestrator gate tự động (skill không tự chạy mà được `/task` dispatch).

### 2.2 Frontmatter Schema

```yaml
---
# === BẮT BUỘC — Discoverability ===
name: string              # kebab-case, unique across skills, 1-64 ký tự
description: >            # >= 20 ký tự. Chứa "Dùng khi..." + "KHÔNG dùng cho..."
  Dùng khi [trigger conditions].
  KHÔNG dùng cho: [anti-patterns] (→ skill-thay-thế).
version: string           # Định dạng X.Y (vd: '1.0', '2.1')

# === CÓ ĐIỀU KIỆN — Chỉ khi skill cần gate tự động ===
pre_conditions:           # Danh sách guard trước khi chạy
  - file: string          #   Đường dẫn file cần kiểm tra
    condition: string     #   Điều kiện (not_skeleton | exists | phase_done)
    on_fail: string       #   Hành động khi fail (ABORT | WARN + lý do)

# === CÓ ĐIỀU KIỆN — Chỉ khi skill ghi file ===
outputs:                  # I/O contract
  - path: string          #   Đường dẫn file output
    action: string        #   Loại ghi (write | append | update)

# === TUỲ CHỌN ===
compatibility: string     # Phụ thuộc tool bên ngoài (vd: "Yêu cầu openspec CLI")
---
```

**Loại bỏ so với hiện tại:**
- `license` → chuyển về repo-level LICENSE
- `metadata.author` / `metadata.language` / `metadata.based-on` → không portable, thừa

**Merge vào `description`:**
- `trigger` field riêng → nhập vào description theo chuẩn "Dùng khi..."

### 2.3 Body Sections bắt buộc

| # | Heading | Bắt buộc | Nội dung |
|---|---------|----------|----------|
| 1 | `## Mục tiêu` | ✅ | 2-4 bullet: skill giải bài toán gì, phạm vi hoạt động |
| 2 | `## Khi nào sử dụng` | ✅ | Trigger conditions chi tiết |
| 3 | `## Khi nào KHÔNG sử dụng` | ✅ | Anti-pattern + routing sang skill đúng |
| 4 | `## Quy trình` | ✅ | Step-by-step — linh hoạt tuỳ skill |
| 5 | `## Đầu ra` | ✅ | File ghi, format, ví dụ cụ thể |
| 6 | `## Lưu ý quan trọng` | Tuỳ chọn | Gotchas/cạm bẫy — chỉ skill đã gặp vấn đề |

**Nguyên tắc:**
- Section `## Quy trình` được tự do cấu trúc — mỗi skill có bản chất khác nhau.
- Gate Function (nếu có) viết inline trong `## Quy trình`, không tạo section riêng.
- Lint chỉ check **minimum bar** — không chặn section bổ sung.

---

## 3. Lint Script

### 3.1 Vị trí

```
.agent/tools/skill-lint/
├── validate_skills.py
└── tests/
    └── test_validate_skills.py
```

### 3.2 Checks

```
FRONTMATTER:
  [F1] name         — tồn tại, kebab-case, unique across skills
  [F2] description  — tồn tại, >= 20 ký tự, chứa "Dùng khi" HOẶC "Use when"
  [F3] version      — tồn tại, match pattern X.Y
  [F4] pre_conditions — nếu có: mỗi entry phải có file + condition + on_fail
  [F5] outputs      — nếu có: mỗi entry phải có path + action

BODY SECTIONS:
  [B1] ## Mục tiêu              — heading tồn tại
  [B2] ## Khi nào sử dụng       — heading tồn tại (hoặc "Khi nào dùng")
  [B3] ## Khi nào KHÔNG sử dụng — heading tồn tại (hoặc "Khi nào KHÔNG dùng")
  [B4] ## Quy trình             — heading tồn tại (hoặc "Quy trình thực hiện")
  [B5] ## Đầu ra                — heading tồn tại (hoặc "Output")
```

### 3.3 Output format

```
=== SKILL LINT REPORT ===

  skill-name           F1 F2 F3 F4 F5 B1 B2 B3 B4 B5  STATUS
  requirement-analyst  ✅ ✅ ✅ ✅ ✅ ✅ ✅ ✅ ✅ ✅  PASS
  author-dna-builder   ✅ ❌ ✅ -- -- ✅ ✅ ❌ ✅ ❌  FAIL (3)
  ...

Exit code: 0 (all pass) | 1 (có lỗi)
```

---

## 4. Kế hoạch thực hiện

| Bước | Nội dung | Deliverable |
|------|----------|-------------|
| **1** | Viết `validate_skills.py` + `test_validate_skills.py` | Script + tests |
| **2** | Chạy lint → report thiếu gì trên 14 skills | Report table |
| **3** | Sửa từng SKILL.md theo report | 14 files chuẩn hoá |
| **4** | Chạy lint lại → confirm 14/14 PASS | Validation |

---

## 5. Verify

- **Tự động:** `python validate_skills.py` exit 0 trên toàn bộ 14 skills.
- **Thủ công:** Review ngẫu nhiên 2-3 skill đã sửa, đảm bảo nội dung không bị mất.
