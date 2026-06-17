# Platform-Aware Entry Point File — Design

> Đánh giá tiêu chí 1 (genericity ở tầng coding) của framework AMAP v3, ngày 2026-06-17.
> Scope: phạm vi đa nền tảng agent (multi-platform), KHÔNG bao gồm đa ngôn ngữ/stack.

## Vấn đề

AMAP có adapter layer per-platform (`cli/platforms/*.py`) khai báo `config_entry_point`
khác nhau cho mỗi nền tảng — `antigravity`/`generic` → `AGENTS.md`, `claude-code` →
`CLAUDE.md`, `cursor` → `.cursorrules`. Nhưng pipeline scaffold không bao giờ đọc
`config_entry_point`:

1. **Output filename hardcode.** `cli/plugin-manifest.yaml` khai báo
   `output: AGENTS.md` cho plugin `agents-md`; `cli/scaffold.py` build `target_path`
   trực tiếp từ string này, không qua Jinja. Chọn platform nào lúc `amap init`, file
   sinh ra vẫn luôn tên `AGENTS.md`.
2. **Nội dung hardcode.** 9 file framework (`AGENTS.md` tự tham chiếu 6 lần,
   `bootstrap.md`, `rules-flow.md`, `rules-tool.md`, `RULES.md`, `task.md`,
   `token-tracking.md`, `AGENT_TRANSPARENCY.tpl.md`, `TOKEN_LOG.tpl.md`) chứa literal
   string `"AGENTS.md"`. Ngay cả khi (1) được sửa, nội dung những file này vẫn sẽ
   nhắc sai tên file cho user Claude Code/Cursor — nghiêm trọng nhất là
   `bootstrap.md`: `CHECK AGENTS.md → không có: ABORT`.
3. **`amap status` hardcode** ([cli/commands/status.py:17](../../../cli/commands/status.py#L17))
   check tồn tại `AGENTS.md` tuyệt đối, không tra `.agent/resolved-config.yaml` để
   biết platform thật đã chọn.
4. **`amap update --reconfigure` không dọn file cũ.** Đổi platform (vd
   antigravity → claude-code) chỉ `sync_tree` (copy thêm), không xoá file
   entry-point cũ — để lại `AGENTS.md` rác song song với `CLAUDE.md` mới.

`claude_code.py`/`cursor.py` adapter đã implement đầy đủ (tool_mapping,
config_entry_point đúng) — vấn đề nằm hoàn toàn ở bước nối dây scaffold, không phải
thiếu adapter.

## Mục tiêu

- Scaffold ghi đúng filename entry-point theo platform đã chọn.
- Toàn bộ nội dung framework (rules/procedures/workflows/templates) tự tham chiếu
  đúng tên file đã được resolve, không còn literal cứng.
- `amap status` nhận diện đúng installation bất kể platform.
- `amap update --reconfigure` dọn sạch file entry-point cũ khi đổi platform.
- `amap init` có cùng safety net (staging + verify-no-unresolved-marker) như
  `amap update`, vì fix này thêm Jinja marker vào ~10 file và `init` hiện ghi
  thẳng vào target không qua bước chặn nào.

## Non-goals

- Đổi tên thư mục `.agent/` hoặc `.knowledge-layer/` theo platform — đây là thư mục
  nội bộ của AMAP CLI, không được agent runtime nào đọc trực tiếp theo convention,
  nên không cần biến đổi.
- Đa ngôn ngữ/stack (author-dna/conventions/knowledge-snapshot per-project content) —
  báo cáo 2026-06-16 đã xác nhận tầng này content-agnostic by design; là tiêu chí
  khác, không thuộc spec này.
- Thêm platform mới ngoài 4 cái đã có (antigravity, claude-code, cursor, generic).

## Thiết kế

### 1. Render context đã sẵn

`BasePlatform.build_render_context()` (`cli/platforms/base.py`) đã expose
`platform.config_entry_point` cho mọi file được Jinja-render. Không cần thêm context
mới.

### 2. Manifest + scaffold: output filename động

- `cli/plugin-manifest.yaml`: plugin `agents-md` đổi
  `output: AGENTS.md` → `output: "{{ platform.config_entry_point }}"`.
- `cli/scaffold.py` trong `scaffold_plugins()`: resolve `plugin["output"]` qua
  `render_string(jinja_env, plugin["output"], context)` trước khi join với
  `write_root` để tạo `target_path`. An toàn no-op với output không chứa `{{`.

### 3. Nội dung: thay literal bằng biến Jinja

Thay `AGENTS.md` → `{{ platform.config_entry_point }}` trong:

- `AGENTS.md` (6 chỗ, gồm H1 title — sẽ tự hiển thị đúng tên file thật, vd
  `# CLAUDE.md — Agent Memory Architecture Protocol` cho user Claude Code)
- `.agent/procedures/bootstrap.md` (gồm cả ABORT check string)
- `.agent/rules/rules-flow.md`
- `.agent/rules/rules-tool.md`
- `.agent/rules/RULES.md`
- `.agent/workflows/task.md`
- `.agent/procedures/token-tracking.md`
- `.knowledge-layer/templates/AGENT_TRANSPARENCY.tpl.md`
- `.knowledge-layer/templates/TOKEN_LOG.tpl.md`

Không xung đột cú pháp với placeholder single-brace sẵn có trong các `.tpl.md`
(`{n}`, `{ticket-id}`) — Jinja chỉ parse double-brace `{{ }}`. Không cần đổi flag
`template:` trong manifest — `copy_and_render_directory`/`scaffold_plugin` đã tự
render bất kỳ file text nào chứa `{{ `.

### 4. `amap status`

Thay check cứng `target / "AGENTS.md"` bằng: `load_resolved_config(target)` → lấy
`platform_key` → `get_platform(platform_key).config_entry_point` → check
`target / <entry_point>`. Nếu không có resolved config, giữ nguyên nhánh
"chưa cài AMAP" hiện tại.

### 5. `amap update --reconfigure`: dọn file cũ

Trước khi `gather_choices` ghi đè resolved config, lưu lại
`old_platform = get_platform(resolved.get("platform", "generic"))`. Sau khi
`sync_tree` xong, nếu `reconfigure` và
`old_platform.config_entry_point != platform.config_entry_point` → xoá
`target / old_platform.config_entry_point` (file này luôn `ownership: framework`,
nhất quán với việc nó vốn đã bị overwrite mỗi lần update).

### 6. `amap init`: đưa về cùng safety model với `update`

Refactor `run_init` (`cli/commands/init.py`): scaffold vào `tempfile.mkdtemp()`
staging dir trước (giống `run_update`), chạy `verify_no_unresolved(staging)`, abort
rõ ràng (không đụng gì vào target) nếu còn marker chưa render, ngược lại
`sync_tree(staging, target)`. Đóng đúng lỗ hổng bất đối xứng: `update` đã có gate
này, `init` — lần ghi đầu tiên và dễ vỡ nhất — thì chưa.

### 7. Test

- Mở rộng `test_reconfigure_switches_platform_keeps_user_files`: assert `CLAUDE.md`
  tồn tại (không phải `AGENTS.md`) sau init claude-code; sau reconfigure sang
  antigravity, assert `AGENTS.md` tồn tại và `CLAUDE.md` đã bị xoá.
- Test mới: init platform `cursor`, assert `.cursorrules` tồn tại, nội dung đã
  render đúng, không còn `{{ ` leftover.
- Test mới: `amap status` trên target platform non-default (claude-code) báo cáo
  đúng "đã cài".
- Test mới: `run_init` abort sạch (target rỗng/không đổi) khi template cố ý hỏng để
  lại marker chưa resolve trong staging.

## Edge cases / giả định

- Chạy `amap init` hai lần trên cùng target để đổi platform (thay vì dùng
  `update --reconfigure`) — ngoài scope. `init` giả định target mới/rỗng; đổi
  platform phải qua `update --reconfigure`.
- `generic` và `antigravity` đều resolve về `AGENTS.md` — không có gì thay đổi với
  user đang dùng 2 platform này.
