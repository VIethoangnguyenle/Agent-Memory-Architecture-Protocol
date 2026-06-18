# Templatize meta-prompt.md Framework Paths — Design

> **Ngày:** 2026-06-18
> **Loại:** Bug fix (test failure) + cleanup nhỏ trong cùng file
> **Scope:** `.amap/meta-prompt.md` — thay literal `.amap/` path bằng `{{ platform.framework_root }}`,
> gộp 1 chỗ tree-structure trùng nhánh trong cùng file. Thêm 1 test Codex tương đương test Antigravity
> đã có.

---

## 1. Vấn đề

`cli/tests/test_init.py::test_antigravity_rendered_framework_files_do_not_reference_active_amap_paths`
fail. Test này quét toàn bộ file đã render bởi `amap init` cho platform Antigravity và assert không
file nào còn chứa literal `.amap/` (trừ khi có cụm "legacy .amap" hoặc "source repo").

**Nguyên nhân (đã xác minh):** `.amap/meta-prompt.md` là **file duy nhất** trong toàn bộ framework
còn dùng literal `.amap/` path — 32 lần xuất hiện trên 29 dòng. 44 file khác (toàn bộ `rules/`,
`skills/*/SKILL.md`, `procedures/`, `knowledge/templates/`, ...) đã được chuyển sang
`{{ platform.framework_root }}` trong commit `d9924fc` (`platform-native-framework-root`). File này
bị bỏ sót vì lúc đó nó còn ở root (`AGENTS.md`), ngoài cây `.amap/` — pass đó chỉ quét trong `.amap/`.

Literal `.amap/` render verbatim cho **mọi** platform non-Generic, nên bug ảnh hưởng cả ba root:
Antigravity (`.agents`), Codex (`.agents`), và Claude Code (`.claude`) — file render ra vẫn in
`.amap/...` trong khi file thật được scaffold vào `.agents/...` hoặc `.claude/...`. Chỉ Antigravity
hiện có test che leakage này; Codex và Claude Code không có (test claude-code hiện tại,
`test_init_templatizes_entry_point_references`, chỉ check vắng `{{ ` và tên entry-point, không check
`.amap/`).

## 2. Quyết định đã chốt

- **Cách fix duy nhất hợp lệ:** templatize toàn bộ literal `.amap/` trong `.amap/meta-prompt.md`
  thành `{{ platform.framework_root }}`, đúng pattern đã dùng ở 44 file khác.
  - Hai alternative đã xét và loại: (a) làm lơi assertion của test — phá vỡ invariant mà SP1 dựng ra
    (rendered output không lẫn framework path sai); (b) giữ literal `.amap/` cho riêng entry-point —
    phủ nhận chính tính năng `platform-native-framework-root` đã ship.
- **Kèm 1 cleanup tối thiểu trong cùng file:** cây thư mục ở §0 ([.amap/meta-prompt.md:16-94](../../../.amap/meta-prompt.md))
  hiện hiển thị `.amap/knowledge/` và `.amap/` (rules/skills/workflows/...) như **hai nhánh top-level
  riêng** dưới `project-root/`. Sai — `knowledge/` thực tế là con của cùng thư mục với `rules/`,
  `skills/` (xác minh: `ls .amap/` → `knowledge, procedures, profiles, rules, skills, tools,
  workflows` đều là sibling). Đây đúng 2 dòng (20 và 52) đang phải sửa cho path-fix, nên gộp lại thành
  1 cây lồng đúng — nếu không sửa, sau khi templatize sẽ hiển thị 2 nhánh `{{ platform.framework_root }}/...`
  trùng tên, rõ ràng sai hơn hiện tại.
- **Không đụng** danh sách skill/workflow/tool bị stale trong cùng file (thiếu `spec-validator`,
  `document-writer`, `infra-tdd`, các workflow `opsx-*`, `executor.md`/`reviewer.md`,
  `rule-projector`, `microloop-orchestrator`). Đây là vấn đề content-accuracy lớn hơn, tách thành
  task riêng sau.
- **Thêm test cho Codex và Claude Code:** cả hai cùng dính bug nhưng chưa có test leakage. Thêm 2
  test giống cấu trúc test Antigravity hiện có, đổi platform answer sang Codex và Claude Code. Sau
  fix, cả ba root non-Generic (`.agents` Antigravity, `.agents` Codex, `.claude`) đều có guard chống
  regression `.amap/` leakage.

## 3. Phạm vi thay đổi

### 3.1 `.amap/meta-prompt.md`

**a) Gộp tree §0 (dòng 16–94)** — thay 2 nhánh top-level trùng thành 1 cây lồng đúng:

```
project-root/
│
├── {{ platform.config_entry_point }}     ← Meta-prompt chính (file này) — đọc đầu tiên
│
└── {{ platform.framework_root }}/        ← Agent Infrastructure Layer (rules, skills, workflows, knowledge...)
    ├── knowledge/                         ← Memory Hierarchy (bộ nhớ phân tầng)
    │   ├── active/ ...
    │   ├── long-term/ ...
    │   ├── archive/ ...
    │   └── templates/ ...
    ├── rules/ ...
    ├── skills/ ...
    ├── workflows/ ...
    ├── procedures/ ...
    ├── tools/ ...
    ├── resolved-config.yaml ...
    └── profiles/ ...
```

Nội dung con (tên file, comment giải thích sau `←`) giữ nguyên 100% như hiện tại — chỉ đổi cấu trúc
lồng + prefix box-drawing characters cho đúng độ sâu mới, và đổi `.amap/` → `{{ platform.framework_root }}/`.

**b) Thay literal `.amap/` còn lại (30 chỗ ngoài tree) thành `{{ platform.framework_root }}/`**, theo
từng khối:

| Section | Dòng (hiện tại) | Số chỗ |
|---|---|---|
| Bootstrap Bước 1 — đọc core config | 106–111 | 6 |
| Bootstrap Bước 2 — scan skills | 117 | 1 |
| Bootstrap Bước 3 — nạp workflows | 124–127 | 4 |
| Bootstrap Bước 4 — Context Loader priority | 135, 138, 141, 144 | 4 |
| §2.1 Flow — file path mỗi bước | 202, 206, 210 | 3 |
| §3 Skill Registry — lệnh validate | 288 | 1 |
| §4 Observability — file transparency | 296 | 1 |
| §5 Archive Protocol | 312 (×2), 313, 314, 317 (×2) | 6 |
| §7.1 Persona config file | 340, 341, 347 (×2) | 4 |

Tổng 30 + 2 (trong tree) = 32, khớp số đếm gốc. Không có route nào sót: đã verify bằng
`grep -o '\.amap/' .amap/meta-prompt.md` trước và sẽ verify lại = 0 sau khi sửa.

**Không đổi:** mọi chỗ "AMAP" (tên framework, viết hoa, không có `/`) — đây là proper noun, không
phải path. Đã verify bằng `grep -n '\.amap\b' | grep -v '\.amap/'` → rỗng, nên không có case nhập
nhằng giữa path và tên framework.

### 3.2 `cli/tests/test_init.py`

Thêm 2 test mới ngay sau `test_antigravity_rendered_framework_files_do_not_reference_active_amap_paths`,
cùng logic quét, chỉ đổi platform answer:
- `test_codex_rendered_framework_files_do_not_reference_active_amap_paths` — answer `"4"` (Codex).
- `test_claude_code_rendered_framework_files_do_not_reference_active_amap_paths` — answer `"2"`
  (Claude Code; root `.claude`).

## 4. Test & Verification

- `cli/tests/test_init.py::test_antigravity_rendered_framework_files_do_not_reference_active_amap_paths`
  → phải chuyển từ FAIL → PASS.
- 2 test mới (Codex, Claude Code) → PASS (fix áp dụng chung cho mọi platform).
- Full suite `/usr/bin/python3 -m pytest cli/tests/ -q` → **100% pass**, không còn known-failure nào
  (khác với lần fix trước, lần này không có exception "pre-existing, ngoài phạm vi" — đây chính là
  task fix nó).
- Smoke kiểm tra platform Generic không đổi hành vi: `framework_root` của Generic = `.amap`, nên sau
  templatize, output render cho Generic vẫn in ra `.amap/...` giống y hệt hôm nay (chỉ khác nguồn là
  biến thay vì literal).
- `grep -o '\.amap/' .amap/meta-prompt.md | wc -l` → phải bằng 0 sau khi sửa (dùng `grep -o` đếm số
  lần xuất hiện, nhất quán với cách đếm 32 ở §1; `grep -c` đếm dòng nên không dùng cho count).
- **Verify cây thư mục thủ công** (test KHÔNG che phần này): render entry-point cho 1 platform non-Generic
  rồi đọc lại §0 bằng mắt — xác nhận chỉ còn 1 nhánh top-level `{{ platform.framework_root }}/`, lồng
  đúng, không lệch box-drawing/độ thụt.

## 5. Tiêu chí Done

- `.amap/meta-prompt.md` không còn literal `.amap/`.
- Cây thư mục §0 không còn 2 nhánh top-level trùng tên.
- `cli/tests/ -q` 100% pass.
- Output render cho Generic không đổi nội dung hiển thị.
- `git diff --check` sạch.

## 6. Ngoài phạm vi

- Cập nhật danh sách skill/workflow/tool bị stale trong cùng file (việc riêng, lớn hơn).
- Sửa bất kỳ file nào khác ngoài `.amap/meta-prompt.md` và `cli/tests/test_init.py`.
- Thay đổi nội dung/ý nghĩa của bất kỳ rule, skill, hay workflow nào.
