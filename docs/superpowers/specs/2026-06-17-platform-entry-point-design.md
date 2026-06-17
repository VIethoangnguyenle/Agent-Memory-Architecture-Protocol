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
3. **`amap status` gate hardcode** ([cli/commands/status.py:17-22](../../../cli/commands/status.py#L17-L22))
   — status có đọc resolved-config để hiển thị (dòng 29), nhưng *cổng kiểm tra "đã cài
   chưa"* lại check tồn tại `AGENTS.md` tuyệt đối. Cài cho claude-code (sinh `CLAUDE.md`,
   không có `AGENTS.md`) → bị báo nhầm "chưa cài AMAP" và thoát sớm trước cả khi đọc
   resolved-config.
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

Đảo thứ tự: `load_resolved_config(target)` TRƯỚC, rồi mới quyết định "đã cài chưa".

- Có resolved config → `get_platform(platform_key).config_entry_point` → check
  `target / <entry_point>` tồn tại.
- Không có resolved config → fallback check `target / "AGENTS.md"` (legacy default).
  Nếu có → vẫn báo "đã cài (legacy installation)" như hành vi hiện tại; nếu không →
  "chưa cài AMAP".

> Lý do giữ fallback: legacy install (có `AGENTS.md`, chưa có resolved-config) hiện
> được [status.py:17-22](../../../cli/commands/status.py#L17-L22) báo là "legacy
> installation" — vẫn coi là đã cài. Nếu chỉ check entry-point-từ-resolved-config
> mà bỏ fallback, legacy install sẽ bị báo nhầm "chưa cài".

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
`sync_tree(staging, target)` → `generate_resolved_config(target, ...)`. Đóng đúng lỗ
hổng bất đối xứng: `update` đã có gate này, `init` — lần ghi đầu tiên và dễ vỡ nhất —
thì chưa.

### 6b. Đóng blind spot của `verify_no_unresolved` cho file không-suffix

`verify_no_unresolved` ([scaffold.py:178-195](../../../cli/scaffold.py#L178-L195))
lọc theo `suffix in _TEXT_EXTENSIONS`. Nhưng entry-point của Cursor là `.cursorrules`
— `Path(".cursorrules").suffix == ""`, không nằm trong `_TEXT_EXTENSIONS` → **không
bao giờ được quét**. Đây chính là file mà fix này sinh ra động, và là platform rủi ro
nhất nếu sót marker. (Cùng class với commit `e303a0d` "close marker-check blind spot
for non-md/yaml file types".)

Sửa: `verify_no_unresolved` LUÔN quét các file entry-point đã biết bất kể suffix.
Cách làm: gom tập tên entry-point từ tất cả platform
(`{get_platform(k).config_entry_point for k in PLATFORMS}`); một file được quét nếu
`suffix in _RENDERED_SUFFIXES` **hoặc** `name` nằm trong tập entry-point đó. Như vậy
`.cursorrules` (và bất kỳ entry-point dotfile nào thêm sau) luôn được kiểm.

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
- Test mới (regression cho §6b): file `.cursorrules` chứa marker `{{ }}` chưa render
  trong staging PHẢI bị `verify_no_unresolved` bắt — chứng minh blind spot đã đóng.
- Test mới: `amap status` trên legacy install (có `AGENTS.md`, xoá resolved-config)
  vẫn báo "đã cài (legacy)" — bảo vệ fallback ở §4.

## Edge cases / giả định

- Chạy `amap init` hai lần trên cùng target để đổi platform (thay vì dùng
  `update --reconfigure`) — ngoài scope. `init` giả định target mới/rỗng; đổi
  platform phải qua `update --reconfigure`.
- `generic` và `antigravity` đều resolve về `AGENTS.md` — không có gì thay đổi với
  user đang dùng 2 platform này.
- **Templatize chính `AGENTS.md` ở root repo này (quyết định đã chốt):** repo lưu
  source-as-template (các `SKILL.md` đã chứa sẵn `{{ tools.* }}` raw); riêng root
  `AGENTS.md` hiện sạch marker và đang được dogfood đọc trực tiếp. Sau fix, root
  `AGENTS.md` sẽ chứa literal `{{ platform.config_entry_point }}` (kể cả H1 title) khi
  đọc trực tiếp. **Chấp nhận** — nhất quán với model "source == template" đã áp đồng
  nhất cho mọi file framework khác; để dogfood repo này thì render qua `amap init`/
  `update` như mọi target. Không tách bản render riêng cho root để tránh hai cơ chế
  song song.
