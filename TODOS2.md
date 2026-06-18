# TODOS — AMAP

> Tổng hợp từ review 3 góc (Sản phẩm / Kiến trúc / DX) ngày 2026-06-18.
> Sợi chỉ xuyên suốt: AMAP đang đầu tư vào *độ thuần kiến trúc* (portability, generic, 5-pha)
> trước khi *chứng minh giá trị* và *hạ thuế adoption*. Thứ tự dưới đây de-risk theo chi phí thấp nhất.

---

## Claude Handoff — Next Session / Batch 2

> **Current branch:** `batch1-scaffold-hardening`
> **Remote branch:** `origin/batch1-scaffold-hardening`
> **PR creation URL:** <https://github.com/VIethoangnguyenle/Agent-Memory-Architecture-Protocol/pull/new/batch1-scaffold-hardening>
> **Batch 1 implementation head:** `b9908fa fix(scaffold): fail on unknown template tool keys`
> **Handoff note:** this section is kept at branch `HEAD`; check `git log -1` for the latest handoff commit.
> **Validation:** `python3 -m pytest cli/tests -q` → `74 passed`
> **Final review:** clean; ready to merge. GitHub app could not create PR (`403 Resource not accessible by integration`), and `gh` is not installed.

### Done by Codex / Batch 1

Batch 1 scaffold hardening is implemented and pushed on `origin/batch1-scaffold-hardening`.

| Item | Status | Evidence |
|---|---|---|
| Batch 1 design spec | **DONE** | `docs/superpowers/specs/2026-06-18-batch1-scaffold-hardening-design.md`, commit `9e7e219` |
| Batch 1 implementation plan | **DONE** | `docs/superpowers/plans/2026-06-18-batch1-scaffold-hardening.md`, commit `65a7294` |
| Worktree safety | **DONE** | `.worktrees/` ignored, commit `2e14923` |
| `TODOS.md` audit | **DONE** | stale `P3.2` moved to Done/Stale, commit `7119890` |
| `P1.2` silent tool-resolution guard | **DONE** | required/optional tool-key contract + strict validation, commits `57ea533` and `b9908fa` |
| Unknown `{{ tools.* }}` render failure | **DONE** | Jinja `StrictUndefined` + scaffold regression test, commit `b9908fa` |
| `P1.3 + P2.2` init automation/defaults | **DONE** | `--platform`, `--mcp`, `--language`, `--yes`; safe interactive defaults; commits `2da0ff6`, `30f2d10`, `536fa68` |
| `UP3` golden scaffold snapshots | **DONE** | platform tree snapshots for `antigravity`, `codex`, `claude-code`, `generic`; commit `9961918` |
| Verification | **DONE** | `python3 -m pytest cli/tests -q` → `74 passed` |
| Final code review | **DONE** | final reviewer said ready to merge after `b9908fa` |
| PR creation | **BLOCKED IN ENV** | branch pushed; GitHub app 403; `gh` missing. Use PR URL above. |

### Needs to happen next

| Order | Item | Status | Notes |
|---|---|---|---|
| 1 | Open PR for Batch 1 | **TODO** | Use PR URL above. Base `main`, head `batch1-scaffold-hardening`. |
| 2 | Merge Batch 1 | **TODO** | Safe to merge after PR review; tests and final review are clean. |
| 3 | Start Batch 2 with `P1.1` | **TODO NEXT** | Write/adjust U0 baseline-litmus design spec. Do this before portability registry. |
| 4 | Move to `UP1` eval harness | **TODO AFTER P1.1** | Only after P1.1 protocol is approved/validated. |
| 5 | Move to `P2.1 + UP2` portability registry | **TODO LATER** | Do not start before outcome validation exists. |

### Recommended Batch 2 Scope

Start Batch 2 with **P1.1 — U0 litmus baseline arm**. Do not jump to `P2.1/UP2` portability registry yet; Batch 1 created scaffold guardrails, but the project still needs outcome evidence before larger portability investment.

Suggested Batch 2 scope:

1. Write/adjust a spec for U0 baseline litmus:
   - Compare the same ticket under two arms:
     - AMAP full workflow.
     - Baseline agent with only light repo guidance (`CLAUDE.md` / ad hoc prompt).
   - Measure outcome, not just process: rework, review loops/comments, bug leakage, convention adherence, blast-radius quality, manual intervention count, token cost, and wall-clock.
   - Use at least 3 ticket sizes: tiny, standard, complex.
2. Keep Batch 2 mostly documentation/protocol unless the spec explicitly chooses to implement harness code.
3. After P1.1 is designed/approved, create an implementation plan in `docs/superpowers/plans/`.
4. Only after P1.1 has a validated protocol should Claude move to **UP1 eval harness**.

Key docs for Claude to read first:

- `docs/superpowers/specs/2026-06-18-batch1-scaffold-hardening-design.md`
- `docs/superpowers/plans/2026-06-18-batch1-scaffold-hardening.md`
- `docs/superpowers/specs/2026-06-17-upgrade-roadmap-design.md`
- `TODOS.md` sections `P1.1` and `UP1`

Recommended first user-facing question for Claude:

> "Batch 1 is ready to merge. For Batch 2, should I first write the U0 baseline-litmus design spec, or do you want me to merge/open the Batch 1 PR first?"

---

## P1 — Làm trước (đòn bẩy cao, chi phí thấp)

### P1.1 — U0 litmus phải có baseline arm (đo outcome, không đo process)
- **What:** Sửa spec U0 để chạy A/B trên cùng ticket: (1) AMAP full 5-pha; (2) cùng agent chỉ với CLAUDE.md + ad hoc. Đo **outcome**: rework (review comment / vòng sửa / bug lọt), convention adherence, blast-radius bắt đúng, số lần can thiệp tay, token + wall-clock mỗi arm.
- **Why:** North Star hiện tại (Generic, Knowledge-first, Long-term memory, IDE-independent) đều là *means*. Không phép đo nào chạm tới giá trị thật (diff đúng hơn, ít rework hơn). U0 đang đo "process chạy E2E được không", không đo "AMAP có đáng so với baseline không". Đây là phép đo quyết định cả thesis.
- **Context:** [docs/superpowers/specs/2026-06-17-upgrade-roadmap-design.md](docs/superpowers/specs/2026-06-17-upgrade-roadmap-design.md) §4 (U0), §6 (R1). R1 fix (Vietbank + `active/` rỗng) đo được cold-start accumulation nhưng (a) agent có thể đã thấy codebase Vietbank từ trước → vẫn nhiễm, (b) "accumulation" vẫn là process metric. Baseline arm là mảnh còn thiếu.
- **Exit:** litmus-report chứa so sánh AMAP-arm vs baseline-arm trên **≥3 ticket** (tiny/standard/complex), verdict định lượng: giảm rework X%, tốn thêm Y% token.
- **Effort:** human ~2-3 ngày / CC: thiết kế protocol ~30 phút (chạy ticket thật vẫn tốn thời gian thật).
- **Priority:** P1. **Depends on:** U2-min (repo sạch) như roadmap.

### P1.2 — Fix silent-failure trong tool resolution
- **Status:** Done in Batch 1 on `batch1-scaffold-hardening` (`57ea533`, final hardening fix `b9908fa`). Keep this entry for historical context until the branch is merged.
- **What:** `get_tool()` trả về chính tên abstract khi miss → template render thẳng chữ `find_blast_radius` (tool không tồn tại) vào instruction agent. Thêm: (a) test khẳng định mọi platform định nghĩa **cùng tập abstract-op key**, (b) guard lúc render cảnh báo/fail khi gặp op chưa map.
- **Why:** Vi phạm "zero silent failures". `verify_no_unresolved` chỉ bắt marker `{{ `, không bắt abstract-op rò rỉ → output sai mà không ai biết.
- **Context:** [cli/platforms/base.py:96-102](cli/platforms/base.py#L96-L102) (`get_tool`), [cli/scaffold.py:301-324](cli/scaffold.py#L301-L324) (`verify_no_unresolved`), [cli/tests/test_platforms.py](cli/tests/test_platforms.py).
- **Effort:** human ~nửa ngày / CC ~15 phút.
- **Priority:** P1 (nhỏ, an toàn).

### P1.3 + P2.2 — Init automation and safe defaults
- **Status:** Done in Batch 1 on `batch1-scaffold-hardening` (`2da0ff6`, fixes `30f2d10` and `536fa68`). Keep this entry for historical context until the branch is merged.
- **What:** Add flags for `amap init`: `--platform`, `--mcp`, `--language`, `--yes`. Keep interactive as the default, but prevent enter-through from silently installing Antigravity + Java. Platform has no interactive default; language defaults to `other`.
- **Why:** Init must be scriptable for CI/onboarding, and defaults must not silently choose the wrong runtime or language.
- **Context:** [cli/commands/init.py](cli/commands/init.py), [cli/amap.py](cli/amap.py). Supersedes the old separate `P1.3` and `P2.2` entries.
- **Effort:** CC ~30-45 minutes.
- **Priority:** P1.

---

## P2 — Quan trọng (sau khi P1 mở khoá)

### P2.1 — Resolve portability theo trục MCP/capability (mở rộng adapter scaffold-time)
- **What:** `tool_mapping` value chuyển thành (hoặc thêm tầng) **abstract-op → required-capability → MCP đã chọn cung cấp capability đó** (tái dùng `provides` trong manifest), fallback về tool native của platform / generic khi không MCP nào cung cấp. Route ~16 chỗ hardcode trong body qua render context `tools`.
- **Why:** Hiện `tool_mapping` map abstract-op → **một MCP cụ thể** (`socraticode`, `confluence` hardcode). Hai user cùng Claude Code nhưng MCP code-search khác nhau đều nhận `mcp__socraticode__...`. Lớp "portable" không portable đúng trên trục quan trọng nhất. **Đây là hiện thân thật của SP3-portability — và rẻ hơn nhiều so với "build mới" roadmap đang frame**, vì adapter đã tồn tại.
- **Context:** [cli/platforms/base.py:37-102](cli/platforms/base.py#L37-L102), [cli/platforms/claude_code.py:28-44](cli/platforms/claude_code.py#L28-L44), [cli/scaffold.py:48-53](cli/scaffold.py#L48-L53) (`has_capability` đã có notion `provides` nhưng chỉ dùng gate plugin). Roadmap SP3: [docs/superpowers/specs/2026-06-17-upgrade-roadmap-design.md](docs/superpowers/specs/2026-06-17-upgrade-roadmap-design.md) §4.
- **Effort:** human ~3-5 ngày / CC ~1-2 giờ.
- **Priority:** P2. **Depends on:** P1.1 (validate trước khi đổ công vào portability), P1.2.

### P2.3 — Gom resolved-config về một vị trí canonical
- **What:** Hiện config có thể ở 3 nơi (`.agents`/`.claude`/`.amap`) với preference-order + fallback. Gom về **một** vị trí theo `platform.framework_root`, bỏ multi-candidate scan, thay bằng một migration cho layout cũ.
- **Why:** 6 commit gần nhất toàn về path resolution (platform-native-root, meta-prompt-relocation, templatize-paths, neutral-rename) = cùng một bề mặt bị sửa đi sửa lại = smell kiến trúc. Bề mặt 3-vị-trí × platform-root sinh bug lặp.
- **Context:** [cli/scaffold.py:61-132](cli/scaffold.py#L61-L132) (`resolved_config_candidates`, `load_resolved_config`).
- **Effort:** human ~1 ngày / CC ~30 phút.
- **Priority:** P2.

### P2.4 — Sửa quickstart README không copy-paste được
- **What:** Bước 2 dùng placeholder *literal* `{framework_root}` trong lệnh `cp`. Resolve thành ví dụ thật (`.claude/` hoặc `.agents/`) hoặc nói rõ thay bằng gì theo platform.
- **Why:** User copy-paste nguyên `{framework_root}` → lỗi ngay bước onboarding đầu.
- **Context:** [README.md:207](README.md#L207).
- **Effort:** CC ~5 phút.
- **Priority:** P2.

---

## P3 — Nice to have

### P3.1 — DRY `framework_version "3.0"`
- **What:** Hardcode 2 chỗ → một nguồn sự thật.
- **Context:** [cli/platforms/base.py:117](cli/platforms/base.py#L117), [cli/scaffold.py:86](cli/scaffold.py#L86).
- **Effort:** CC ~5 phút. **Priority:** P3.

### P3.3 — Cập nhật framing chi phí SP3 trong roadmap
- **What:** Sau khi xác nhận P2.1 (SP3 = mở rộng adapter, không phải greenfield), cập nhật §2/§4 roadmap: SP3 từ "spec mới, đòn bẩy build lớn nhất" → "mở rộng adapter + migrate ~16 ref + test". Điều này dịch lại bài toán "portability có đáng không".
- **Context:** [docs/superpowers/specs/2026-06-17-upgrade-roadmap-design.md](docs/superpowers/specs/2026-06-17-upgrade-roadmap-design.md) §2, §4.
- **Effort:** CC ~15 phút. **Priority:** P3. **Depends on:** P2.1.

## Done / Stale

### P3.2 — Next-steps footer sau `amap init`
- **Status:** Done before Batch 1. `run_init()` already prints platform-root-aware next steps, and `cli/tests/test_init.py` covers the output.

---

## Upgrades — nâng cấp/đổi hướng cấu trúc (net-new, không phải fix)

> Khác với P1–P3 (sửa lỗi). Đây là thay đổi cấu trúc/chiến lược. Đặt tên UP để tránh nhầm với U0–U3/SP của roadmap.
> Thứ tự đề xuất: UP1 + UP3 trước (rẻ, bảo vệ mọi thay đổi sau), rồi UP2, UP4, UP5 sau cùng.

### UP1 — Eval harness: biến validate-first thành tín hiệu liên tục
- **What:** Harness lặp lại được: vài fixture ticket trong repo mẫu + scorer (rubric, có thể LLM-judge) → chạy AMAP-arm vs baseline-arm → xuất delta chất lượng. Cắm vào CI mỗi khi đổi rules/skills/meta-prompt.
- **Why:** Gap lớn nhất của dự án — có test cho CLI (scaffold đúng không) nhưng **zero test cho giá trị cốt lõi** (protocol có làm agent ra output tốt hơn không). Mỗi lần refactor rule/skill hiện không có gì bắt được "vừa làm agent tệ đi". Harness biến chất lượng thành regression test, hiện thực hoá toàn bộ finding CEO.
- **Context:** Mở rộng P1.1 từ litmus một-lần thành signal liên tục. Tái dùng instrumentation ở [.amap/procedures/token-tracking.md](.amap/procedures/token-tracking.md).
- **Effort:** CC ~1-2 giờ dựng khung; chạy ticket thật vẫn tốn thời gian thật.
- **Priority:** cao nhất trong Upgrades. **Depends on:** P1.1 (baseline arm).

### UP2 — Platform/MCP registry dạng data, không phải code
- **What:** Chuyển mỗi platform từ class Python (`tool_mapping` hardcode) sang YAML khai báo (một file/platform hoặc một registry). Thêm platform/MCP = thêm data.
- **Why:** (a) biến FAQ "thêm platform custom" thành thật (không cần viết Python); (b) abstract-op keyset validate schema ở một chỗ → diệt nguyên lớp silent-failure **về cấu trúc**, không chỉ bằng test (gộp với P1.2); (c) P2.1 capability-resolution thành data-driven. Phép đơn giản hoá làm portability rẻ thật.
- **Context:** [cli/platforms/base.py](cli/platforms/base.py), [cli/platforms/claude_code.py](cli/platforms/claude_code.py) và các platform khác.
- **Effort:** human ~2-3 ngày / CC ~1 giờ.
- **Priority:** sau UP1/UP3. **Depends on:** liên quan P1.2, P2.1.

### UP3 — Golden-snapshot test mỗi platform
- **Status:** Done in Batch 1 on `batch1-scaffold-hardening` (`9961918`). Keep this entry for historical context until the branch is merged.
- **What:** `amap init` cho từng platform vào fixture, snapshot toàn bộ cây output, diff mỗi lần đổi. Regression ở path-resolution fail CI ngay.
- **Why:** Churn lặp (6 commit về path resolution) cho thấy bề mặt platform × framework_root rất giòn. Đây là một test bắt được phần lớn churn gần đây.
- **Context:** [cli/tests/](cli/tests/), [cli/scaffold.py](cli/scaffold.py). Bổ trợ P2.3 (gom config canonical).
- **Effort:** CC ~30 phút.
- **Priority:** P1 hardening guard. Do before large portability refactors.

### UP4 — `amap init/update --dry-run` + drift detection
- **What:** `--dry-run` hiện diff trước khi ghi; `amap status --check-drift` cảnh báo khi file framework-owned bị sửa tay (sẽ bị overwrite khi update).
- **Why:** `update` re-render file framework → user sợ bị ghi đè (chính nỗi sợ này sinh ra file-ownership policy). Dry-run + drift xây niềm tin cho mô hình idempotent-update.
- **Context:** [cli/commands/update.py](cli/commands/update.py), [cli/commands/status.py](cli/commands/status.py), [docs/amap-file-ownership-policy.md](docs/amap-file-ownership-policy.md).
- **Effort:** human ~1 ngày / CC ~30 phút.
- **Priority:** trung bình.

### UP5 — (Tham vọng) Phase collapse theo knowledge state
- **What:** Phase trở nên collapsible theo trạng thái tri thức — nếu output của một phase đã cached/ổn định trong knowledge layer (vd kiến trúc module này vừa explore), thì short-circuit nó. Thuế 5-pha giảm dần khi tri thức chín.
- **Why:** Câu trả lời cấu trúc cho bài toán thuế adoption, hiện thực dream-state "AMAP vô hình". Tham vọng hơn U1 tiering (vốn chỉ phân loại theo kích thước task).
- **Context:** Liên quan U1 ([roadmap §4](docs/superpowers/specs/2026-06-17-upgrade-roadmap-design.md)), memory hierarchy active/long-term.
- **Effort:** human ~1 tuần+ / CC ~vài giờ. **Direction — nên qua office-hours/spec trước khi build.**
- **Priority:** sau khi validate xong (UP1 + P1.1). **Depends on:** P1.1, UP1.
