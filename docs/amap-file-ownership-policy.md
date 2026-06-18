# AMAP — File-Ownership Policy

> **Phiên bản:** 1.0 · **Ngày:** 2026-06-17
> **Vai trò:** Hợp đồng phân loại sở hữu file. Các lệnh CLI (`init` / `update` / `migrate`) PHẢI tuân.
> **Người tiêu thụ chính:** U3 (`amap migrate`). Nguồn: U2-min spec.

## 1. Bốn nhóm sở hữu

| Nhóm | `init` | `update` | `migrate` | Gồm |
|---|---|---|---|---|
| **Framework-owned** | render/copy | **re-render/ghi đè** | bỏ qua | `{framework_root}/{rules,skills,workflows,procedures,tools}`, `AGENTS.md`/`CLAUDE.md`, entry-point file, `{framework_root}/knowledge/templates/`, `docs/examples/` (nguồn meta-prompt: `.amap/meta-prompt.md` → render ra entry-point downstream) |
| **Seeded-then-user-owned** | seed skeleton 1 lần | **giữ nguyên (không đụng)** | **backfill schema additive** | `{framework_root}/knowledge/long-term/{author-dna.yaml, conventions.yaml, knowledge-snapshot.md}` |
| **Per-dev (gitignored)** | seed từ `*.template` | giữ nguyên | bỏ qua | `{framework_root}/knowledge/long-term/persona.yaml`, `{framework_root}/knowledge/active/*` (runtime) |
| **Generated (gitignored)** | tạo | tái sinh | bỏ qua | `{framework_root}/tools/rule-projector/generated/*`, `__pycache__`, `{framework_root}/resolved-config.yaml` |

## 2. Invariant cứng — Ba file sống

`author-dna.yaml`, `knowledge-snapshot.md`, `conventions.yaml` là **TÀI LIỆU SỐNG, tiến hoá theo thời
gian trong dự án chính** (knowledge-curator cập nhật snapshot sau mỗi task; DNA giàu lên qua teaching
moment R-DNA-7; conventions cập nhật khi rescan).

1. **Bản chất kép.** Trong repo AMAP = skeleton framework-owned. Trong project user = user-owned đang
   tiến hoá. Hai bản decoupled.
2. **Seed một lần** khi `amap init`. Từ đó bản của user tiến hoá độc lập.
3. **`update` TUYỆT ĐỐI KHÔNG ghi đè** ba file này trong project user.
4. **`migrate` chỉ ADDITIVE schema** — thêm field thiếu kèm default, **không bao giờ chạm
   content/giá trị** user/agent đã tích luỹ.
5. **Version stamp tách biệt content:** schema có `version` riêng (vd `version: "1.1"`); migrate so
   version để biết field cần backfill, không suy luận từ content.

> ⚠️ Đây là điểm dễ mất dữ liệu nhất khi nâng version. Policy này là hợp đồng mà U3 phải tuân.
