# AMAP Agent-Neutral — Design Spec

> Ngày: 2026-06-18 · Topic A của phiên brainstorming 2026-06-18.
> Phục vụ North Star: **#1 Generic** + **#4 IDE/agent-independent**.
> Nguồn: phiên brainstorming với user (đối chiếu [sp0-directory-refactor](2026-06-16-sp0-directory-refactor-design.md) §4 và [u2-min-neutrality](2026-06-17-u2-min-neutrality-design.md)).

---

## 1. Mục tiêu & ranh giới

Làm AMAP **đọc ra trung-lập-agent** — xoá cảm giác "framework chỉ dành cho Antigravity". Hai workstream:

- **A1** — rename `.agent/` → `.amap/`; gộp `.knowledge-layer/` vào `.amap/knowledge/`.
- **A2** — trung-lập-hoá framing "Antigravity-first" trong các file vận hành.

**Đảo quyết định SP0 §4 (có chủ đích):** SP0 từng giữ `.agent/` top-level vì rename "churn không thêm
giá trị" — nhưng SP0 **chỉ cân nhắc trục kỹ thuật/portability**, không xét trục *cái tên có signal được
tính agent-independent hay không*. Spec này bổ sung đúng trục đó: tên `.agent` (và việc Antigravity luôn
là ví dụ mặc định) tạo perception sai về phạm vi framework. Giá trị = branding/neutrality, không phải kỹ thuật.

**Tiền đề đã kiểm chứng:** `.agent/` **không** phải convention của Antigravity — Antigravity đọc ở
`~/.gemini/antigravity/knowledge/` ([bootstrap.md:29](../../../.agent/procedures/bootstrap.md#L29)).
Không tool nào phụ thuộc tên thư mục `.agent/`. → Rename **an toàn kỹ thuật**, không phá integration.

### Ranh giới chống over-correct (BẮT BUỘC)

A2 **KHÔNG** gỡ bỏ Antigravity. Antigravity là platform first-class, có adapter riêng
([cli/platforms/antigravity.py](../../../cli/platforms/antigravity.py)). Những thứ sau **giữ nguyên**:

- Platform adapter `antigravity.py` + đăng ký trong `cli/platforms/__init__.py`.
- Các detect path chức năng: `~/.gemini/antigravity/knowledge/`, `~/.cursor/rules/`,
  `.github/copilot-instructions.md`, `.cursorrules` — đây là *mục tiêu phát hiện thật*, không phải prose.
- Mọi chỗ liệt kê tool **đã trung lập** (vd `tools/README.md` ghi "Cursor/Antigravity" — Cursor đứng trước; profiles; `fresh_session.py` docstring) — không đụng.

A2 chỉ sửa **prose nơi Antigravity bị privileged**: đứng đầu enumeration mặc định, là ví dụ độc tôn,
hoặc là incident neo cứng cho một rule tổng quát.

---

## 2. Layout đích (A1)

```
.amap/
├── rules/  skills/  workflows/  procedures/  tools/   ← framework (shipped, version-controlled)
├── resolved-config.yaml
└── knowledge/                ← (was .knowledge-layer/) runtime state per-project
    ├── active/               (nội dung gitignored — working memory)
    ├── archive/
    ├── long-term/            (persona.yaml gitignored — per-dev)
    └── templates/            (skeleton tĩnh)
```

**Layout = Option 1 (nested phẳng):** một dotdir `.amap/` duy nhất; framework giữ tên dir cũ (churn thấp);
runtime nằm dưới `.amap/knowledge/`. SP0 ship/scaffold split vẫn còn — chỉ chuyển từ "hai dir top-level"
sang "subdir trong `.amap/`": installer ship `.amap/{rules,skills,workflows,procedures,tools}`, scaffold
`.amap/knowledge/` (active rỗng, long-term + templates có seed).

**Lợi ích phụ của namespace gộp:** exclusion của KI-detect (Phần 4, bug Lớp-3) rút về **một gốc duy nhất**
= "ngoài `.amap/`" — sạch hơn so với hai gốc rời rạc.

**Tradeoff đã chấp nhận:** gộp 1 dir nghĩa là `rm -rf .amap` xoá luôn memory tích luỹ. Rủi ro thực tế thấp
(CLI `update` không bao giờ xoá file user-owned). User đã duyệt Option 1.

---

## 3. Migration & rewrite tham chiếu (A1)

### 3.1 Di chuyển thư mục (dùng `git mv` để giữ history)

| Từ | Đến |
|----|-----|
| `.agent/` | `.amap/` |
| `.knowledge-layer/` | `.amap/knowledge/` |

> `.amap/knowledge/active/.gitignore` đi theo `git mv` tự động.

### 3.2 Rewrite chuỗi tham chiếu — CHÚ Ý 2 dạng

1. **Dạng slash** (md/yaml/sh): `.agent/` → `.amap/`; `.knowledge-layer/` → `.amap/knowledge/`.
2. **Dạng quoted-component** (Python): `".agent"` / `'.agent'` → `".amap"`; `".knowledge-layer"` →
   path `.amap/knowledge`. Có ở [scaffold.py:65,84](../../../cli/scaffold.py#L65),
   [status.py:55,63](../../../cli/commands/status.py#L55).

### 3.3 CLI (điểm dễ sót nhất)

| Vị trí | Sửa |
|--------|-----|
| `SOURCE_MAP` [scaffold.py:18-28](../../../cli/scaffold.py#L18) | `.agent/*` → `.amap/*`; `knowledge-*` → `.amap/knowledge/*` |
| [plugin-manifest.yaml](../../../cli/plugin-manifest.yaml) | ~38 dòng `output: .agent/...` → `.amap/...`; output `.knowledge-layer/...` → `.amap/knowledge/...` |
| `generate_resolved_config` / `load_resolved_config` [scaffold.py:65,84](../../../cli/scaffold.py#L65) | `.agent/resolved-config.yaml` → `.amap/resolved-config.yaml` |
| [status.py:55,63](../../../cli/commands/status.py#L55) | `.agent/skills`, `.agent/workflows` → `.amap/...` |
| [templatize.py:81-83](../../../cli/tools/templatize.py#L81) | `.agent/{skills,workflows,procedures}` → `.amap/...` |
| `cli/tests/` (test_scaffold, test_update, test_init) | mọi expectation `.agent` → `.amap` |

### 3.4 File vận hành khác

`AGENTS.md`, `README.md`, `install.sh`, `.gitignore`, `.knowledge-layer/README.md` (→ `.amap/knowledge/README.md`),
và 21 file trong `.agent/**` (tự nằm trong cây đã `git mv`, nhưng nội dung text vẫn cần rewrite path).

`.gitignore` sau rewrite:
```
.amap/tools/rule-projector/generated/*
!.amap/tools/rule-projector/generated/.gitkeep
...
.amap/knowledge/long-term/persona.yaml
```

### 3.5 docs lịch sử — GIỮ NGUYÊN

18 file trong `docs/superpowers/specs|plans` tham chiếu `.agent/` là **bản ghi tại thời điểm cũ**. Rewrite =
falsify history. → **Không sửa.** Spec này là source-of-truth hiện hành. Verification grep (Phần 5) loại trừ
`docs/superpowers/`.

---

## 4. A2 — trung-lập-hoá framing + bug Lớp-3

### 4.1 Inventory prose cần sửa (Antigravity bị privileged)

| File:line | Vấn đề | Hướng sửa |
|-----------|--------|-----------|
| [bootstrap.md:52](../../../.agent/procedures/bootstrap.md#L52) | **Lý do** neo 100% vào incident Antigravity (2026-06-08, `factory-rules.md`) | Giữ bài học (external KI thiếu judgment layer → ảo giác đủ context); bỏ neo cứng vào path/tool cụ thể → viết generic |
| [bootstrap.md:24,29](../../../.agent/procedures/bootstrap.md#L24) | Antigravity đứng đầu enumeration / detect list | Generic-first; Antigravity không độc tôn vị trí đầu |
| [rules-guard.md:101](../../../.agent/rules/rules-guard.md#L101) | "(Antigravity, Cursor rules, …)" | Reorder neutral |
| [rules-flow.md:27,31](../../../.agent/rules/rules-flow.md#L27) | "convention từ Antigravity, …"; "tool như Antigravity planning" | Reorder / generic |
| [context-loader.md:77](../../../.agent/procedures/context-loader.md#L77) | "(Antigravity, Cursor rules, etc.)" | Reorder neutral |
| [task.md:254](../../../.agent/workflows/task.md#L254) | Antigravity là ví dụ độc tôn cho "planning mode ngoài workflow" | Generic ("runtime có planning mode riêng, vd …") |

> **Nguyên tắc:** mô tả generic trước, ví dụ tool sau theo thứ tự không tôn riêng tool nào. Không file vận
> hành nào để Antigravity làm ví dụ mặc định/độc tôn.

### 4.2 Bug Lớp-3 (correctness — nằm trong A1, không chỉ perception)

[bootstrap.md:33](../../../.agent/procedures/bootstrap.md#L33) detect `*-rules.md`/`*-ki.md` *"ngoài
`.knowledge-layer/`"*. Sau rename, framework rules + knowledge cùng nằm dưới `.amap/`.

- **Sửa:** exclusion đổi thành **"ngoài `.amap/`"** (cả namespace) → file của chính framework không bao giờ
  bị nhận nhầm là "external KI".
- Hôm nay chưa nổ chỉ vì framework rules đặt tên prefix (`rules-flow.md`), không khớp suffix `*-rules.md` —
  may, không phải thiết kế. Namespace gộp (Phần 2) làm fix này thành 1 gốc duy nhất.

---

## 5. Verification ("done")

1. `grep -rn "\.agent/" --exclude-dir=.git --exclude-dir=.venv .` (loại `docs/superpowers/`) → **0**.
2. `grep -rn "\.agent" cli/` (bắt cả dạng quoted-component `".agent"` trong Python) → **0**.
3. `grep -rn "knowledge-layer" --exclude-dir=.git --exclude-dir=.venv .` (loại `docs/superpowers/`) → **0**.
4. `.amap/` tồn tại đủ `rules skills workflows procedures tools knowledge resolved-config.yaml`;
   `.agent/` và `.knowledge-layer/` **không còn**.
5. `.gitignore` trỏ path mới; `git check-ignore .amap/knowledge/active/<file>` và
   `.amap/knowledge/long-term/persona.yaml` vẫn ignored.
6. CLI tests pass: `/usr/bin/python3 -m pytest cli/` (dùng `/usr/bin/python3`, không phải venv).
7. `git log --follow .amap/...` thấy history liền mạch (đã dùng `git mv`).
8. A2: không file vận hành nào để Antigravity làm ví dụ độc tôn/đầu-mặc-định; adapter `antigravity.py` +
   detect path còn nguyên; `cli/tests` Antigravity vẫn pass.
9. Lớp-3: exclusion KI-detect = "ngoài `.amap/`"; framework rule files không bị flag là external KI.

---

## 6. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|--------|-----------|
| Sót tham chiếu → agent đọc path không tồn tại lúc bootstrap | Grep gate Phần 5 step 1-3 (cả 2 dạng) là hard gate trước commit; chạy CLI tests |
| `git mv` mất history nếu lỡ `cp`+`rm` | Bắt buộc `git mv` cho cả 2 di chuyển dir |
| Over-correct A2 → vô tình gỡ support Antigravity | Ranh giới §1: adapter + detect path + liệt kê neutral **giữ nguyên**; chỉ sửa prose privileged |
| Nested layout phá pattern gitignore | Rewrite path trong `.gitignore`; verify §5 step 5 |
| docs lịch sử còn path cũ → người đọc tương lai bối rối | Spec này là source-of-truth; ghi rõ "docs lịch sử giữ nguyên có chủ đích" |

---

## 7. Ngoài phạm vi

- **`amap migrate`** cho install ngoài đang dùng `.agent/` → để **U3** (`amap migrate` đã lên kế hoạch trong
  upgrade-roadmap). Spec này chỉ lo repo framework + install **mới**. Ghi 1 dòng breaking-change trong commit.
  *U3 sẽ phải xử lý thêm bước `.agent`→`.amap` + `.knowledge-layer`→`.amap/knowledge`.*
- Rewrite docs lịch sử (specs/plans cũ).
- Gỡ Antigravity khỏi danh sách platform.
- **Topic B (multi-persona presets)** — spec riêng sau.
