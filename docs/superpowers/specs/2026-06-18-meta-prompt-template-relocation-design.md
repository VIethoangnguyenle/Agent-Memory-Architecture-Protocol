# Meta-Prompt Template Relocation — Design

> **Ngày:** 2026-06-18
> **Loại:** Refactor / repo-layout fix (không thay đổi hành vi downstream)
> **Scope:** Tách template meta-prompt downstream ra khỏi root repo framework để các
> agent dùng `AGENTS.md` làm entry point (Codex, Antigravity) không auto-load nhầm
> template khi đang phát triển *chính* framework.

---

## 1. Vấn đề

Root `AGENTS.md` trong repo framework **không phải** hướng dẫn để làm việc trên repo này —
nó là **template nguồn của meta-prompt downstream**:

- [cli/plugin-manifest.yaml:50-54](../../../cli/plugin-manifest.yaml) — plugin `agents-md`
  lấy `source: AGENTS.md`, render ra `output: {{ platform.config_entry_point }}`.
- [cli/scaffold.py:27](../../../cli/scaffold.py) — `SOURCE_MAP` map `AGENTS.md → AGENTS.md`.
- Body file đầy placeholder Jinja `{{ platform.config_entry_point }}` — chỉ hợp lệ *sau khi render*.

Khi `amap init` chạy vào dự án đích, file này render thành entry point đúng theo IDE:
Claude Code → `CLAUDE.md`, Codex/Antigravity → `AGENTS.md`, Cursor → `.cursorrules`.

**Bất đối xứng gây lỗi:** trong repo framework, Claude Code auto-load `CLAUDE.md`
(behavioral guidelines — đúng), nhưng Codex/Antigravity auto-load root `AGENTS.md` —
tức là **template downstream** (đầy `{{ }}`, ép chạy bootstrap "chồng yêu" + flow
Ideation→Apply). Vô lý khi đang phát triển chính framework.

## 2. Quyết định đã chốt

- **Vị trí mới:** `.amap/meta-prompt.md`. Nhất quán với toàn bộ source content framework
  (rules, skills, workflows, procedures, tools) vốn đã sống trong `.amap/` qua `SOURCE_MAP`,
  và `.amap/**` vốn đã chứa Jinja template (từ platform-native-root work).
- **Không để file con trỏ ở root cho Codex.** Root chỉ còn `CLAUDE.md`. Khi dev framework
  bằng Codex/Antigravity, agent không auto-load gì — trade-off chấp nhận được theo phạm vi
  "chỉ tách template".
- **Hành vi downstream không đổi.** `output` vẫn là `{{ platform.config_entry_point }}`.

## 3. Cơ chế render (đã xác minh)

Body của file được render nhờ **đuôi `.md` + có chuỗi `{{ `**
([cli/scaffold.py:170-176](../../../cli/scaffold.py), `scaffold_plugin`):

```python
if plugin.get("template") or source_path.suffix.lower() in _RENDERABLE_SUFFIXES:
    ...
    if content is not None and ("{{ " in content or plugin.get("template")):
        output = render_string(jinja_env, content, context)
```

Cờ `template: false` ở manifest **không ảnh hưởng** việc render body cho file `.md`.
Vì vậy chỉ cần đổi `source` path; không cần sửa body, không cần đổi cờ.

## 4. Các thay đổi

| # | File | Thay đổi |
|---|------|----------|
| 1 | `AGENTS.md` → `.amap/meta-prompt.md` | `git mv` (giữ lịch sử). **Không sửa body** — chỉ dùng `{{ platform.config_entry_point }}`, không hardcode "AGENTS.md". |
| 2 | [cli/plugin-manifest.yaml:52](../../../cli/plugin-manifest.yaml) | `source: AGENTS.md` → `source: meta-prompt.md`. Giữ `output: "{{ platform.config_entry_point }}"`. |
| 3 | [cli/scaffold.py:27](../../../cli/scaffold.py) | `SOURCE_MAP`: `"AGENTS.md": "AGENTS.md"` → `"meta-prompt.md": ".amap/meta-prompt.md"`. `resolve_source_path` khớp prefix → trả về `amap_root / ".amap/meta-prompt.md"`. |
| 4 | [docs/amap-file-ownership-policy.md:11](../../amap-file-ownership-policy.md) | Thêm 1 dòng ghi chú: nguồn template meta-prompt nay ở `.amap/meta-prompt.md` (entry-point downstream vẫn là framework-owned như cũ). |

**Không đụng:** README (mô tả cấu trúc *downstream* — target vẫn có `AGENTS.md`/`CLAUDE.md`,
vẫn đúng); body template; platform adapter; mapping `config_entry_point`; `install.sh`
(không tham chiếu root `AGENTS.md`).

## 5. Test

- **Thêm** trong [cli/tests/test_scaffold.py](../../../cli/tests/test_scaffold.py): assert
  `resolve_source_path(amap_root, "meta-prompt.md")` trả về đường dẫn kết thúc bằng
  `.amap/meta-prompt.md`.
- **Chạy lại** `cli/tests/` — đặc biệt `test_init.py`: `amap init` cho claude-code, codex,
  generic vẫn render entry point đúng, không sót `{{ `; `verify_no_unresolved` sạch.
- **Smoke:** `amap init` vào temp dir cho 3 platform → entry point tồn tại + đã render.

## 6. Tiêu chí Done

- `.amap/meta-prompt.md` tồn tại; root **không còn** `AGENTS.md`.
- `cli/plugin-manifest.yaml` + `cli/scaffold.py` trỏ đúng nguồn mới.
- `/usr/bin/python3 -m pytest cli/tests/ -q` xanh.
- `amap init` 3 platform render entry point chuẩn (không `{{ ` sót).
- `git diff --check` sạch.

## 7. Ngoài phạm vi

- Thêm dev-guide riêng cho Codex/Antigravity khi phát triển framework (đã chọn không làm).
- Đổi tên/đuôi sang `.tpl.md` hay `.j2` (giữ `.md` để renderer xử lý không đổi).
- Thay đổi bất kỳ hành vi downstream nào.
