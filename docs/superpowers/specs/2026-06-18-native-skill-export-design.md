# Native Skill + Workflow Export — Design Spec

> Ngày: 2026-06-18 · Phát sinh từ phiên brainstorming riêng (sau khi amap-neutral đã merge), KHÔNG phải
> Topic B (multi-persona presets) đã nêu trong [amap-agent-neutral-design](2026-06-18-amap-agent-neutral-design.md).
> Đứng độc lập ngoài bảng work-item của [upgrade-roadmap-design](2026-06-17-upgrade-roadmap-design.md), cùng
> hạng mục với [platform-entry-point-design](2026-06-17-platform-entry-point-design.md) (đánh giá tiêu chí
> genericity ở tầng tool, không gate bởi SP3-portability).
> Phục vụ North Star: **#4 IDE/agent-independent**.
>
> **Phạm vi 6 nhóm artifact của `.amap/`:** spec này export **skills + workflows** (cả hai đều là content
> dạng "frontmatter description + invoke theo tên" — cùng hình dạng theo chuẩn open agent-skill). **rules,
> procedures, profiles, tools, knowledge** được xét tới ở §4.6 và **không** cần export tương tự — lý do
> cụ thể cho từng nhóm, không phải bỏ sót.

---

## 1. Vấn đề

AMAP có 14 skill chuyên biệt (`requirement-analyst`, `db-explorer`, `architecture-reviewer`...) sống ở
`.amap/skills/<name>/SKILL.md`. Cách duy nhất một agent biết về chúng hiện nay là **tự đọc prose**:
`bootstrap.md` PHASE 1 đọc `skill-index.yaml` (frontmatter `name`+`description` của mọi skill), tự dựng
một "skill-registry" trong context, rồi agent tự chọn skill theo description khi cần.

Cách này hoạt động trên mọi platform — nhưng bỏ qua một sự thật: **hầu hết platform agent hiện đại đã có
sẵn cơ chế native discovery cho đúng khái niệm "skill"** (folder + `SKILL.md` + frontmatter `name`/
`description`, agent runtime tự quét và tự chọn) — AMAP đang tự làm lại thủ công bằng tay đúng việc mà
runtime đã làm sẵn, và bỏ lỡ lợi ích native (hiện trong skill-picker/autocomplete của tool, được runtime
lazy-load hiệu quả hơn).

**Gap thứ hai, cụ thể hơn:** `cli/platforms/` chỉ có 4 adapter (`antigravity`, `claude-code`, `cursor`,
`generic`) — **không có Codex** dù Codex CLI là một target thực tế.

**Gap thứ ba:** 9 file trong `.amap/workflows/` (`task.md`, `idea-to-task.md`, `opsx-*.md`...) có
frontmatter `description:` và quy ước `/command-name` trong H1 — về hình dạng giống `SKILL.md` gần như
1:1, chỉ thiếu key `name` (xem §4.3). Chúng cũng chỉ được agent biết tới qua đọc prose (`bootstrap.md`
PHASE 2), cùng class vấn đề với skill — không lý do gì để chỉ export skill mà bỏ qua workflow.

---

## 2. Tiền đề đã kiểm chứng (research 2026-06-18)

| Platform | Convention native skill/command | Nguồn |
|---|---|---|
| **Claude Code** | `.claude/skills/<name>/SKILL.md` (project) hoặc `~/.claude/skills/` (personal). Frontmatter bắt buộc `name`+`description`. | [code.claude.com/docs/skills](https://code.claude.com/docs/en/skills) — và chính phiên brainstorming này là bằng chứng trực tiếp (skill list trong system-reminder). |
| **Codex CLI** | `.agents/skills/<name>/SKILL.md` — REPO scope quét từ CWD lên tới repo root; cũng có USER (`$HOME/.agents/skills`), ADMIN, SYSTEM scope. Custom prompts (`~/.codex/prompts/`) **deprecated**, skill là hướng được khuyến nghị. Dựa trên **open standard agentskills.io** (`github.com/openai/skills`). | [developers.openai.com/codex/skills](https://developers.openai.com/codex/skills) |
| **Google Antigravity** | `<project-root>/.agents/skills/` (project scope). | [Google Codelab](https://codelabs.developers.google.com/getting-started-with-antigravity-skills) |
| **Cursor** | `.cursor/commands/<name>.md` — file phẳng, **KHÔNG có frontmatter**, chỉ invoke thủ công (agent không tự chọn theo description — khác hẳn mô hình "skill"). | [Cursor Docs](https://cursor.com/docs/cli/reference/slash-commands), [ibuildwith.ai](https://www.ibuildwith.ai/blog/cursor-rules-skills-and-commands-oh-my-when-to-use-each/) |

**Phát hiện quan trọng:** Codex CLI và Antigravity **cùng hội tụ về một path** (`.agents/skills/`) vì cả
hai implement chung open standard agentskills.io — không phải trùng hợp, là chuẩn liên-tool đang hình
thành (cùng họ với `AGENTS.md` đã là convention liên-tool).

**Đối chiếu với premise cũ:** [amap-agent-neutral-design §1](2026-06-18-amap-agent-neutral-design.md)
khẳng định `.agent/` (số ít) không phải convention Antigravity — **vẫn đúng**, vì convention thật là
`.agents/` (số nhiều), tên khác hoàn toàn. Rename `.agent/` → `.amap/` không xung đột với phát hiện này.

---

## 3. Mục tiêu & ranh giới

- `.amap/skills/<name>/SKILL.md` và `.amap/workflows/<name>.md` **vẫn là nguồn duy nhất** được author —
  đúng pattern "source-as-template, render khi install" đã dùng cho `AGENTS.md`/`CLAUDE.md`
  ([platform-entry-point-design](2026-06-17-platform-entry-point-design.md)).
- `amap init`/`update` **thêm** một bước render mỗi skill/workflow ra **một path native thứ hai** theo
  platform đã chọn — hoàn toàn additive, không sửa nội dung `.amap/skills/`, `.amap/workflows/`, hay
  `bootstrap.md`.
- **KHÔNG sửa `bootstrap.md` PHASE 1** (skill discovery thủ công) — giữ nguyên cho MỌI platform. Đây là
  ranh giới quan trọng nhất: thêm cơ chế adapter (như `tool_mapping`/`config_entry_point` đã có) là chấp
  nhận được; sửa **prose vận hành** theo platform thì vi phạm chính nguyên tắc neutrality vừa chốt ở
  [amap-agent-neutral-design](2026-06-18-amap-agent-neutral-design.md) (operative prose không phân biệt
  platform; chỉ adapter layer được phân biệt). PHASE 1 chạy trùng lặp với native discovery trên Claude
  Code là **lãng phí token nhưng vô hại** — chấp nhận, không tối ưu trong spec này.
- Thêm `cli/platforms/codex.py` — adapter mới, độc lập với phần native-export.

---

## 4. Thiết kế

### 4.1 `BasePlatform.native_skill_export` — property mới

```python
@property
def native_skill_export(self) -> Optional[dict]:
    """Nơi (nếu có) platform tự động phát hiện skill theo convention riêng.

    None = không có native discovery; skill chỉ tồn tại qua bootstrap.md (như hiện tại).
    dir: thư mục gốc, tên skill được nối vào tự động.
    strip_frontmatter: True → xuất bản phẳng <name>.md, bỏ YAML frontmatter,
      pre_conditions (nếu có) được render lại thành checklist trong body.
    flatten: True → output <dir>/<name>.md (không có subfolder), ngược lại
      <dir>/<name>/SKILL.md.
    """
    return None
```

| Platform | `native_skill_export` |
|---|---|
| `claude-code` | `{"dir": ".claude/skills", "strip_frontmatter": False, "flatten": False}` → `.claude/skills/<name>/SKILL.md` |
| `codex` *(mới)* | `{"dir": ".agents/skills", "strip_frontmatter": False, "flatten": False}` → `.agents/skills/<name>/SKILL.md` |
| `antigravity` | `{"dir": ".agents/skills", "strip_frontmatter": False, "flatten": False}` → `.agents/skills/<name>/SKILL.md` |
| `cursor` | `{"dir": ".cursor/commands", "strip_frontmatter": True, "flatten": True}` → `.cursor/commands/<name>.md` |
| `generic` | `None` (không đổi) |

Verbatim copy (sau Jinja render bình thường) cho 3 platform đầu — không transform gì khác ngoài đổi path.

### 4.2 Transform cho Cursor (`strip_frontmatter`)

Cursor cấm frontmatter trong file command. Hàm `export_as_flat_command(skill_md_text: str) -> str`
(mới, `cli/scaffold.py` hoặc `cli/renderer.py`):

1. Parse YAML frontmatter (`name`, `description`, `pre_conditions`, ...).
2. Output: `# {name}\n\n> {description}\n\n` + (nếu có `pre_conditions`) `## Pre-conditions\n` +
   mỗi entry render thành 1 bullet `- {condition mô tả} → nếu fail: {on_fail}` + `\n---\n` + body
   markdown gốc (sau dòng `---` đóng frontmatter thứ hai).
3. **Lý do bắt buộc bước 2 cho `pre_conditions`:** nếu xoá sạch frontmatter mà không render lại,
   user Cursor invoke command native sẽ mất hẳn các gate (`"ABORT — bootstrap chưa chạy"`...) vốn đang nằm
   trong frontmatter — silent regression đúng cho người dùng platform này. Không drop, inline.

### 4.3 Scaffold — một pass mới, không sửa entry trong manifest

Mọi skill/workflow plugin trong `plugin-manifest.yaml` đã có `type: skill` (14 entries,
[cli/plugin-manifest.yaml:94-192](../../../cli/plugin-manifest.yaml#L94)) hoặc `type: workflow` (9
entries, [cli/plugin-manifest.yaml:195-248](../../../cli/plugin-manifest.yaml#L195)) sẵn — không cần sửa
manifest.

Thêm hàm `scaffold_native_skill_exports(plugins, write_root, platform, jinja_env, context)` trong
[cli/scaffold.py](../../../cli/scaffold.py), gọi **sau** `scaffold_plugins()` chính trong `run_init`/
`run_update`:

```
IF platform.native_skill_export is None: return  # no-op, vd generic

FOR each plugin WHERE plugin["type"] IN ("skill", "workflow"):
    source_file = write_root / plugin["output"]   # SKILL.md (dir output) hoặc <name>.md (file output)
    text = source_file.read_text() (nếu là dir output: source_file / "SKILL.md")
    name = plugin["name"].removeprefix("workflow-")   # "workflow-task" → "task"

    IF text không bắt đầu bằng "---" (không có frontmatter — vd workflow-tdd hiện tại):
        SKIP + WARN "no frontmatter, cannot derive description — add one to enable native export"
        CONTINUE

    IF frontmatter thiếu key `name` (đúng trường hợp mọi workflow — chỉ có `description`):
        chèn `name: {name}` vào đầu frontmatter trước khi export (skill đã có `name` sẵn, no-op)

    export = platform.native_skill_export
    IF export["flatten"]:
        target = write_root / export["dir"] / f"{name}.md"
    ELSE:
        target = write_root / export["dir"] / name / "SKILL.md"
    content = export_as_flat_command(text) if export["strip_frontmatter"] else text
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
```

Đọc từ `write_root / plugin["output"]` (đã render xong ở bước trước) thay vì source gốc trong repo AMAP
— đảm bảo native export luôn khớp 100% với bản đã Jinja-render cho project đích (mcps/language/platform
context), không phải bản raw chưa render.

**Pre-req nhỏ phát sinh:** `workflow-tdd` ([.amap/workflows/tdd.md](../../../.amap/workflows/tdd.md))
hiện không có frontmatter — sẽ bị SKIP+WARN cho tới khi thêm 3 dòng `---\ndescription: ...\n---` ở đầu
file (mechanical, tách thành 1 commit nhỏ trước hoặc trong plan, không phải phát hiện mới cần spec riêng).

### 4.4 `cli/platforms/codex.py` — adapter mới

```python
class CodexPlatform(BasePlatform):
    name = "codex"
    display_name = "OpenAI Codex CLI"
    config_entry_point = "AGENTS.md"   # xác nhận: developers.openai.com/codex/guides/agents-md
    native_skill_export = {"dir": ".agents/skills", "strip_frontmatter": False, "flatten": False}
    tool_mapping = {  # abstract passthrough — KHÔNG có tên tool cụ thể đã verify cho Codex CLI
        "read_file": "read_file", "write_file": "write_file", ...  # giống generic.py
    }
```

`tool_mapping` của Codex **giữ abstract** (giống `generic.py`) vì Codex CLI không công khai document tên
tool nội bộ theo cách Claude Code/Antigravity làm — đoán tên cụ thể ở đây là bịa, không phải verify.
Đăng ký vào `cli/platforms/__init__.py` `PLATFORMS["codex"] = CodexPlatform`.

### 4.5 Test mới

- `test_scaffold.py`: init platform `claude-code` → assert `.claude/skills/requirement-analyst/SKILL.md`
  tồn tại, nội dung khớp `.amap/skills/requirement-analyst/SKILL.md` đã render.
- Init platform `codex` → assert `.agents/skills/<name>/SKILL.md` tồn tại cho cả 14 skill; assert
  `AGENTS.md` (không phải file khác) là entry point.
- Init platform `antigravity` → assert `.agents/skills/<name>/SKILL.md` tồn tại (cùng path, platform
  khác).
- Init platform `cursor` → assert `.cursor/commands/<name>.md` tồn tại, **không chứa** `---` frontmatter
  marker, **có chứa** dòng pre-condition gốc (vd text của `on_fail`) cho skill có `pre_conditions`.
- Init platform `generic` → assert không có thư mục `.claude/`, `.agents/`, `.cursor/` nào được tạo.
- `amap update` (mọi platform có native export): re-render xoá/ghi đè đúng — sync giống mọi file
  framework-owned khác, không cần test riêng ngoài test hiện có cho `sync_tree`.
- Init platform `claude-code` → assert `.claude/skills/task/SKILL.md` tồn tại (từ `workflow-task`) và
  frontmatter có cả `name: task` (chèn) và `description` (giữ từ source).
- Init bất kỳ platform có native export → assert `workflow-tdd` **không** xuất hiện trong path native
  (do thiếu frontmatter) và build log có WARN tương ứng; không làm fail build.

### 4.6 Vì sao rules / procedures / profiles / tools / knowledge không export tương tự

| Nhóm | Có cần native export? | Lý do |
|---|---|---|
| **rules/** (`RULES.md`, `rules-flow.md`...) | **Không** — đã được phục vụ qua kênh native tương ứng | "Rules" trong các tool này là khái niệm *always-loaded, không phải pick-from-list* — đúng vai trò của `config_entry_point` (`CLAUDE.md`/`AGENTS.md`/`.cursorrules`) mà [platform-entry-point-design](2026-06-17-platform-entry-point-design.md) đã giải quyết. Export `rules-*.md` riêng lẻ thành "skill" sẽ sai bản chất (rules không được *invoke theo tên*, chúng luôn áp dụng). |
| **procedures/** (`bootstrap.md`, `context-loader.md`, `executor.md`...) | **Không** | Không file nào có frontmatter `description` — đây là sub-routine nội bộ được `workflows`/`rules` tham chiếu bằng prose, không phải artifact người dùng chọn theo tên. Đã verify: cả 6 file trong `.amap/procedures/*.md` đều bắt đầu bằng heading `#` thuần (`head -1`), không file nào mở bằng `---` frontmatter. |
| **profiles/** (`execution-mode.yaml`) | **Không** | Dữ liệu cấu hình thuần (YAML config), không phải nội dung hướng dẫn agent — không có khái niệm "invoke" áp dụng. |
| **tools/** (`rule-projector`, `microloop-orchestrator`, `skill-lint`, `skill-index`) | **Không** | Là script/CLI thật (Python), chạy qua `run_command`/Bash — đã agent-independent theo cách khác (không phụ thuộc UI skill-picker của platform nào). Đăng ký native "tool calling" (MCP-style) là bài toán khác, lớn hơn, đã có chỗ trong roadmap (SP3-portability "tool-capability interface") — không lặp lại ở đây. |
| **knowledge/** (`active/`, `long-term/`, `archive/`) | **Không** | Runtime state/data agent đọc-viết qua `Read`/`Write`, không phải nội dung "skill" để discover. Không platform nào có khái niệm native cho "memory file" tương đương agent-skill. |

**Theo dõi riêng (không verify được qua nguồn chính thức trong phiên này):** một số nguồn cho biết Cursor
đang chuyển từ `.cursorrules` (1 file) sang `.cursor/rules/*.mdc` (nhiều file, scope theo glob) cho chính
nhóm "rules". Nếu đúng, `config_entry_point = ".cursorrules"` hiện tại của `CursorPlatform` có thể đang
nhắm vào convention cũ. **Để ngoài phạm vi spec này** — cần một vòng research+verify riêng (cùng cấp độ
rigor như §2) trước khi sửa, không đoán.

---

## 5. Phương án đã xem xét và loại bỏ

**B — `.agents/skills/` làm nguồn canonical duy nhất, symlink `.claude/skills/` vào đó.** Triệt tiêu
hoàn toàn duplication. Loại bỏ vì: symlink fragile trên Windows/zip-checkout/một số CI; mở lại quyết định
layout A1 (vừa chốt 4 ngày trước) chỉ để tiết kiệm vài KB duplicate trên các file `.md` nhỏ — không đáng.
`.amap/skills/` còn chứa field riêng của AMAP (`pre_conditions`) không thuộc open standard — coi nó là
artifact của open standard cũng là gán nhầm vai trò.

**C — Defer toàn bộ vào SP3-portability, không làm spec riêng bây giờ.** Đúng tinh thần sequencing của
roadmap, nhưng mục tiêu phiên brainstorm này là nghĩ rõ kiến trúc *trước khi* thêm platform/dự án downstream
mới — defer mâu thuẫn với chính lý do mở phiên này.

---

## 6. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|---|---|
| Claude Code / Codex parser có thể không chấp nhận field frontmatter ngoài `name`/`description` (vd `pre_conditions`, `version`) | Cả hai docs chỉ nói "required: name, description", không nói "exclusive". Rủi ro thấp nhưng **chưa verify thực tế** — verify bằng cách init thật + mở skill trong Claude Code, kiểm tra `/skill-name` xuất hiện đúng, trước khi merge. |
| Codex `tool_mapping` để abstract có thể không hữu ích thực tế | Chấp nhận — đây là giới hạn thông tin công khai, không phải lỗi thiết kế; downstream user tự map nếu cần (giống `generic` hiện tại). |
| Trùng lặp nội dung giữa `.amap/skills/` và export native → lệch nếu một bên bị sửa tay | Native export luôn bị `amap update` ghi đè (framework-owned, như mọi file render khác) — không khác gì rủi ro đã có với `CLAUDE.md`/`AGENTS.md` hiện tại. |
| PHASE 1 bootstrap.md đọc lại skill-index.yaml dù Claude Code đã tự discover — tốn token thừa | Đã ghi nhận ở §3, chấp nhận, không tối ưu trong spec này — tối ưu hoá điều kiện theo platform sẽ phá nguyên tắc "operative prose neutral". |
| Cursor "command" không có description-based auto-trigger — user phải biết tên skill để gọi `/` | Giới hạn thật của Cursor, không phải bug AMAP — ghi rõ trong `notes` của `CursorPlatform`. |

---

## 7. Verification ("done")

1. Mọi test mới ở §4.5 pass: `/usr/bin/python3 -m pytest cli/`.
2. `cli/platforms/__init__.py` có `codex` trong `PLATFORMS`; `get_platform("codex")` không lỗi.
3. Init mỗi platform (`claude-code`, `codex`, `antigravity`, `cursor`, `generic`) trên thư mục tạm →
   đúng bảng path ở §4.1, không có path nào của platform khác bị tạo nhầm.
4. `.cursor/commands/*.md` không còn ký tự `---` ở đầu file (frontmatter đã strip) nhưng vẫn còn nội dung
   gốc của `on_fail` cho ít nhất 1 skill có `pre_conditions`.
5. `grep -rn "native_skill_export" cli/platforms/` → xuất hiện ở `base.py` + đúng 4 subclass override
   (claude_code, codex, antigravity, cursor) — generic không override (dùng default `None`).
6. `bootstrap.md` **không bị sửa** — `git diff` rỗng cho file này (xác nhận ranh giới §3 không bị phá).
7. Cả 9 workflow (trừ `workflow-tdd` cho tới khi có frontmatter) xuất hiện ở native path cho mỗi platform
   hỗ trợ, với `name` được chèn đúng (khớp `plugin["name"]` đã bỏ prefix `workflow-`).
8. `.amap/rules/`, `.amap/procedures/`, `.amap/profiles/`, `.amap/tools/`, `.amap/knowledge/` — **không**
   có file nào bị copy ra ngoài path hiện hữu của chúng (xác nhận §4.6 không bị implement quá tay).

---

## 8. Ngoài phạm vi

- Tối ưu hoá bootstrap.md PHASE 1 để skip khi platform đã native-discover — xem rủi ro §6, cố tình không
  làm để giữ neutrality.
- Xác định chính xác tool nội bộ của Codex CLI (`tool_mapping` cụ thể) — cần thêm thông tin công khai chưa
  có; để lại `codex.py` ở dạng abstract passthrough.
- Antigravity CLI (biến thể command-line riêng, khác Antigravity IDE) — một vài nguồn không-chính-thức
  (blog) gợi ý nó dùng path global khác (`~/.gemini/antigravity-cli/skills/`); không đưa vào spec này vì
  chưa xác minh qua nguồn chính thức tương đương Codelab. Nếu cần, làm sub-spec riêng sau khi verify.
- Đăng ký AMAP framework skill vào catalog `agentskills.io`/`github.com/openai/skills` — đó là publish
  ra bên ngoài, khác hẳn "consume convention" mà spec này làm.
- Migration cho install cũ (đã `amap init` trước khi có spec này) — chạy `amap update` là đủ, vì native
  export là file mới được thêm vào, không phải sửa file cũ; không cần migration logic riêng.
- Thêm frontmatter cho `workflow-tdd` (pre-req nêu ở §4.3) — 1 commit nhỏ riêng, mechanical, không cần
  thiết kế.
- Verify/sửa `CursorPlatform.config_entry_point` nếu `.cursor/rules/*.mdc` thật sự đã thay thế
  `.cursorrules` — xem theo dõi riêng ở §4.6, cần vòng research riêng trước khi động vào.
- Native export cho `rules/`, `procedures/`, `profiles/`, `tools/`, `knowledge/` — xem lý do từng nhóm ở
  §4.6; không phải bị quên, là quyết định có chủ đích.
