# SP0 — Directory Tree Refactor: Design Spec

> Ngày: 2026-06-16 · Sub-project 0 của chương trình AMAP v4.
> Phụ thuộc: không (đây là nền móng). Unblock: SP1, SP4.
> Nguồn: phiên brainstorming 2026-06-16 ([AMAP-v3-assessment.md](../AMAP-v3-assessment.md)).

---

## 1. Mục tiêu

Làm sạch cây thư mục thành **canonical, có tài liệu, đúng ngữ nghĩa lifecycle** — để SP1
(Phase 3 Reliability) có nhà cho component mới, và SP4 (auto-setup) có cấu trúc ổn định để
provision vào từng framework.

**Nguyên tắc xuyên suốt** (kế thừa từ thiết kế kiến trúc): *phân tách theo vòng đời / mutability,
không theo loại file*. Tri thức sống (source of truth) phải tách khỏi template tĩnh.

## 2. Phạm vi

**In scope:**
- Xoá thư mục shortcut trùng lặp / rỗng.
- Tách tri thức sống khỏi `templates/` → `long-term/`.
- Chuẩn hoá naming template.
- Rename `.agent/scripts/` → `.agent/procedures/`.
- Reserve nhà cho component tương lai (`tools/`, `adapters/`, `profiles/`).
- Chuyển `docs/skills` + `docs/workflows` sang **generated từ SKILL.md**.
- Cập nhật toàn bộ path reference (~26 file) + canonical path trong RULES.md §12.

**Out of scope (KHÔNG làm ở SP0):**
- Rename top-level `.agent/` / `.knowledge-layer/` (blast radius khổng lồ; phân tách hiện tại
  đã đúng cho portability — xem §4).
- Nội dung/logic của SP1 (Rule Projector, gate), SP2 (best-practice skills), SP3 (adapter),
  SP4 (setup). SP0 chỉ tạo *chỗ trống* cho chúng.
- Sửa nội dung skill (chỉ di chuyển/đổi path, không viết lại logic).

## 3. Vấn đề cần giải quyết

| # | Vấn đề | Bằng chứng |
|---|--------|-----------|
| ① | Thư mục shortcut trùng/rỗng | `/templates/` & `/workflows/` chỉ chứa README; `/templates/README.md` **giống byte** `.agent/templates/README.md`; `.agent/templates/` rỗng (chỉ README trỏ đi nơi khác) |
| ② | **`templates/` trộn tri thức sống + skeleton tĩnh** | `author-dna.yaml`, `conventions.yaml`, `knowledge-snapshot.md`, `persona.yaml` (SOURCE OF TRUTH, versioned) nằm chung thư mục tên `templates/` cùng `*.tpl.md` (skeleton clone) |
| ③ | Naming template không nhất quán | `REQUIREMENT.tpl.md` (có `.tpl`) vs `feature.md` (không) vs `persona.template.yaml` (`.template`) — 3 quy ước cho cùng khái niệm |
| ④ | `docs/` là bản sao tay của SKILL.md | `docs/skills/01..12` copy từ 14 SKILL.md → drift |
| ⑤ | Không có nhà cho component tương lai; `scripts/` gây hiểu nhầm | `.agent/scripts/` chứa toàn md-procedure, không phải executable; SP1 sẽ thêm executable thật |

## 4. Quyết định nền: GIỮ tách top-level

`.agent/` và `.knowledge-layer/` **giữ nguyên ở top-level**, KHÔNG gộp/rename. Lý do:

- `.agent/` = **framework shippable** — giống nhau mọi dự án, là thứ SP4 đem đi cài.
- `.knowledge-layer/` = **runtime state per-project** — scaffold rỗng, tích luỹ riêng từng dự án.

Phân tách này phục vụ trực tiếp portability (SP4 ship `.agent/`, scaffold `.knowledge-layer/` rỗng).
Rename top-level sẽ churn mọi hardcoded path mà không thêm giá trị → loại bỏ.

## 5. Cây thư mục đích

```
.knowledge-layer/
├── active/                      ← working memory (GIỮ NGUYÊN)
│   ├── REQUIREMENT.md, EXPLORE_CONTEXT.md, AGENT_TRANSPARENCY.md, TOKEN_LOG.md
│   └── ideation/
├── archive/                     ← episodic past tasks (GIỮ NGUYÊN)
├── long-term/         ★MỚI      ← LIVE source-of-truth (tách khỏi templates/)
│   ├── author-dna.yaml
│   ├── author-dna.draft.yaml
│   ├── conventions.yaml
│   ├── conventions.draft.yaml   (nếu tồn tại)
│   ├── knowledge-snapshot.md
│   ├── persona.yaml
│   └── persona.template.yaml
└── templates/                   ← CHỈ skeleton tĩnh, naming thống nhất
    ├── REQUIREMENT.tpl.md, EXPLORE_CONTEXT.tpl.md, AGENT_TRANSPARENCY.tpl.md
    ├── TOKEN_LOG.tpl.md, ARCHIVE_META.tpl.md
    └── feature.tpl.md, fixbug.tpl.md, changerequest.tpl.md,
        refactor.tpl.md, ideation.tpl.md           ← đổi sang .tpl.md

.agent/
├── rules/                       (GIỮ)
├── skills/                      (GIỮ — best-practice ở SP2)
├── workflows/                   (GIỮ; bỏ README trùng)
├── procedures/        ★RENAME   ← từ scripts/ (bootstrap, context-loader, context-compressor, token-tracking)
├── tools/             ★RESERVE  ← executable thật (SP1: rule-projector, hooks)
├── adapters/          ★RESERVE  ← tool-capability adapter (SP3)
└── profiles/          ★RESERVE  ← framework profile Claude/Cursor/Antigravity (SP4)

docs/
├── AMAP-v3-assessment.md
├── specs/                       ← spec các sub-project (file này)
├── sketches/          ★MỚI      ← design sketch (nhận multi-agent-escalation-sketch.md)
├── skills/            ★GENERATED ← sinh từ SKILL.md, KHÔNG sửa tay
└── workflows/         ★GENERATED ← sinh từ workflows/*.md

XOÁ:        /templates/   /workflows/   .agent/templates/
DI CHUYỂN:  .knowledge-layer/templates/multi-agent-escalation-sketch.md → docs/sketches/
```

**Hệ phân cấp memory sau refactor** (khớp mô hình agentmemory đang xây):
`active/` (working) · `long-term/` (judgment + map sống) · `archive/` (episodic) · `templates/` (skeleton tĩnh).

## 6. Bản đồ migration (file-by-file)

### 6.1 Di chuyển sang `long-term/`
| Từ | Đến |
|----|-----|
| `.knowledge-layer/templates/author-dna.yaml` | `.knowledge-layer/long-term/author-dna.yaml` |
| `.knowledge-layer/templates/author-dna.draft.yaml` | `.knowledge-layer/long-term/author-dna.draft.yaml` |
| `.knowledge-layer/templates/conventions.yaml` | `.knowledge-layer/long-term/conventions.yaml` |
| `.knowledge-layer/templates/knowledge-snapshot.md` | `.knowledge-layer/long-term/knowledge-snapshot.md` |
| `.knowledge-layer/templates/persona.yaml` | `.knowledge-layer/long-term/persona.yaml` |
| `.knowledge-layer/templates/persona.template.yaml` | `.knowledge-layer/long-term/persona.template.yaml` |

> Dùng `git mv` để giữ history. `conventions.draft.yaml` di chuyển nếu tồn tại.

### 6.2 Rename naming template (trong `templates/`)
| Từ | Đến |
|----|-----|
| `feature.md` | `feature.tpl.md` |
| `fixbug.md` | `fixbug.tpl.md` |
| `changerequest.md` | `changerequest.tpl.md` |
| `refactor.md` | `refactor.tpl.md` |
| `ideation.md` | `ideation.tpl.md` |

> Quy ước thống nhất: **mọi skeleton tĩnh dùng hậu tố `.tpl.md`** (hoặc `.tpl.yaml`).

### 6.3 Rename thư mục
| Từ | Đến |
|----|-----|
| `.agent/scripts/` | `.agent/procedures/` (4 file: bootstrap, context-loader, context-compressor, token-tracking) |

### 6.4 Xoá
- `/templates/` (chỉ README trùng)
- `/workflows/` (chỉ README trùng)
- `.agent/templates/` (chỉ README rỗng nghĩa)

### 6.5 Di chuyển sang docs
- `.knowledge-layer/templates/multi-agent-escalation-sketch.md` → `docs/sketches/multi-agent-escalation-sketch.md`

### 6.6 Reserve nhà tương lai
- Tạo `.agent/tools/`, `.agent/adapters/`, `.agent/profiles/` mỗi thư mục có `README.md` 1 dòng:
  - `tools/`: "Executable tooling — populated by SP1 (rule-projector, git hooks)."
  - `adapters/`: "Tool-capability adapters — populated by SP3."
  - `profiles/`: "Per-framework setup profiles — populated by SP4."

## 7. Cập nhật path reference (phần nặng nhất)

**Blast radius đo được:** ~26 file tham chiếu `.knowledge-layer/templates/`; `knowledge-snapshot`
xuất hiện ở 17 file.

**Chiến lược:**
1. **Cập nhật canonical trước**: RULES.md §12 R-Path-1 (nguồn path canonical duy nhất) — đổi
   `templates/{author-dna,conventions,knowledge-snapshot,persona}` → `long-term/...`.
2. **Find/replace có kiểm soát** các pattern trên toàn repo (`*.md`, `*.yaml`), loại trừ `.git/`:
   - `knowledge-layer/templates/author-dna` → `knowledge-layer/long-term/author-dna`
   - `knowledge-layer/templates/conventions` → `knowledge-layer/long-term/conventions`
   - `knowledge-layer/templates/knowledge-snapshot` → `knowledge-layer/long-term/knowledge-snapshot`
   - `knowledge-layer/templates/persona` → `knowledge-layer/long-term/persona`
   - `agent/scripts/` → `agent/procedures/`
   - template renames: `templates/feature.md` → `templates/feature.tpl.md` (và tương tự)
3. **KHÔNG đụng** các path `templates/*.tpl.md` còn lại (chúng vẫn ở templates/).
4. Cập nhật cây thư mục mô tả trong `AGENTS.md`, `README.md`, `.knowledge-layer/README.md`.

## 8. docs/ generation

- SKILL.md (frontmatter `name`, `description`, `version` + body) là **single source of truth**.
- Viết generator (đặt tại `.agent/tools/` khi SP1 có, hoặc script tạm trong SP0) sinh
  `docs/skills/*.md` + `docs/skills/00-index.md` từ các `SKILL.md`.
- Tương tự cho `docs/workflows/` từ `.agent/workflows/*.md`.
- Thêm header cảnh báo vào mỗi file generated: `<!-- AUTO-GENERATED từ SKILL.md — KHÔNG sửa tay -->`.
- **Sync-check** (tinh thần Rule Projector): bước verify so sánh docs generated với nguồn; lệch → FAIL.

> Nếu generator vượt scope SP0, fallback: xoá `docs/skills` + `docs/workflows` (bỏ duplication),
> để SKILL.md là doc duy nhất, và đưa generator vào SP2. Quyết định lúc writing-plans.

## 9. Verification (định nghĩa "done")

1. `grep -r "knowledge-layer/templates/\(author-dna\|conventions\|knowledge-snapshot\|persona\)"`
   trên toàn repo (trừ `.git/`) → **0 kết quả**.
2. `grep -r "agent/scripts/"` → **0 kết quả**.
3. `grep -r "templates/\(feature\|fixbug\|changerequest\|refactor\|ideation\)\.md"` → **0 kết quả**
   (đã thành `.tpl.md`).
4. Các thư mục `/templates/`, `/workflows/`, `.agent/templates/` không còn tồn tại.
5. `.knowledge-layer/long-term/` chứa đủ 6–7 file tri thức sống; `git log --follow` thấy history liền mạch.
6. `.agent/procedures/` chứa đủ 4 md-procedure.
7. `.agent/tools|adapters|profiles/` tồn tại với README placeholder.
8. RULES.md §12 R-Path-1 phản ánh path mới; không còn path cũ trong bất kỳ rule/skill/workflow.
9. (nếu chọn generated docs) docs/ sinh lại khớp SKILL.md; sync-check pass.

## 10. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|--------|-----------|
| Sót path khi find/replace → agent đọc file không tồn tại lúc bootstrap | Verification §9 step 1–3 là hard gate; chạy grep trước khi commit |
| `git mv` làm mất history nếu copy+delete nhầm | Bắt buộc dùng `git mv`, không `cp`+`rm` |
| Generator docs vượt scope, kéo dài SP0 | Fallback §8: xoá duplication, đẩy generator sang SP2 |
| Reference trong file `.draft.yaml` hoặc comment bị bỏ sót | grep bao gồm `*.yaml`; kiểm cả comment |
| Người dùng/CI đang dựa vào path cũ | SP0 là refactor nội bộ framework; thông báo trong commit message + cập nhật README |

## 11. Không phá vỡ điều gì

- `.knowledge-layer/active/.gitignore` và `archive/.gitkeep` giữ nguyên.
- Logic skill/workflow/rule **không đổi** — chỉ path string + vị trí file.
- `phase_state`, bootstrap flow, OpenSpec integration: không ảnh hưởng.
