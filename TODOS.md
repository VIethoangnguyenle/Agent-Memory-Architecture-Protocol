# TODOS — AMAP

> Tổng hợp từ review 3 góc (Sản phẩm / Kiến trúc / DX) ngày 2026-06-18.
> Sợi chỉ xuyên suốt: AMAP đang đầu tư vào *độ thuần kiến trúc* (portability, generic, 5-pha)
> trước khi *chứng minh giá trị* và *hạ thuế adoption*. Thứ tự dưới đây de-risk theo chi phí thấp nhất.

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
- **What:** `get_tool()` trả về chính tên abstract khi miss → template render thẳng chữ `find_blast_radius` (tool không tồn tại) vào instruction agent. Thêm: (a) test khẳng định mọi platform định nghĩa **cùng tập abstract-op key**, (b) guard lúc render cảnh báo/fail khi gặp op chưa map.
- **Why:** Vi phạm "zero silent failures". `verify_no_unresolved` chỉ bắt marker `{{ `, không bắt abstract-op rò rỉ → output sai mà không ai biết.
- **Context:** [cli/platforms/base.py:96-102](cli/platforms/base.py#L96-L102) (`get_tool`), [cli/scaffold.py:301-324](cli/scaffold.py#L301-L324) (`verify_no_unresolved`), [cli/tests/test_platforms.py](cli/tests/test_platforms.py).
- **Effort:** human ~nửa ngày / CC ~15 phút.
- **Priority:** P1 (nhỏ, an toàn).

### P1.3 + P2.2 — Init automation and safe defaults
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
- **Bundle (S2, từ dashboard review 2026-06-20):** `framework_root` default **lệch nhau** giữa các module — dashboard reader default `.amap` ([cli/dashboard/reader.py:68](cli/dashboard/reader.py#L68)), orchestrator default `.agents` ([.amap/tools/microloop-orchestrator/orchestrator.py:103](.amap/tools/microloop-orchestrator/orchestrator.py#L103)). Chưa nổ vì resolved-config luôn ghi rõ key, nhưng là bẫy. Gom về **một** default canonical khi làm P2.3.

### P2.4 — Sửa quickstart README không copy-paste được
- **What:** Bước 2 dùng placeholder *literal* `{framework_root}` trong lệnh `cp`. Resolve thành ví dụ thật (`.claude/` hoặc `.agents/`) hoặc nói rõ thay bằng gì theo platform.
- **Why:** User copy-paste nguyên `{framework_root}` → lỗi ngay bước onboarding đầu.
- **Context:** [README.md:207](README.md#L207).
- **Effort:** CC ~5 phút.
- **Priority:** P2.

### P2.5 — Nâng dashboard runtime contract thành interface có single-source (chống drift)
- **What:** Tạo một module hằng số contract dùng chung (tên event: `subagent_spawned/started/done/blocked`, `task_*`, `parent_brain_updated`, ...; và `VALID_RUNTIME_STATUS`) import bởi **cả** orchestrator (writer, ship sang target) **lẫn** dashboard reader (cli/). Cân nhắc thêm version field vào `ACTIVITY_LOG`/contract.
- **Why:** Phát hiện 2026-06-20 (architect review tính năng dashboard): orchestrator và reader cùng phụ thuộc một bộ event/status nhưng mỗi bên **hard-code string riêng**. Reader xử unknown-event generic nên không crash, nhưng **không gì chống drift ngữ nghĩa** giữa hai lớp — đây là bề mặt coupling xuyên-lớp duy nhất của tính năng. `ACTIVITY_LOG.jsonl` giờ là interface runtime first-class, nên đáng được đối xử như interface (single source + version) thay vì spec markdown + literal rải rác.
- **Context:** [.amap/tools/microloop-orchestrator/orchestrator.py](.amap/tools/microloop-orchestrator/orchestrator.py) (writer), [cli/dashboard/server.py](cli/dashboard/server.py) `read_runtime` (reader); spec [docs/superpowers/specs/2026-06-19-dashboard-runtime-contract-design.md](docs/superpowers/specs/2026-06-19-dashboard-runtime-contract-design.md) §6.
- **Effort:** CC ~30-45 phút. **Priority:** P2 (interface drift). **KHÔNG làm trong PR #10** (freeze dashboard ở P6).

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

### P3.4 — Archive `active/` TRỌN VẸN theo ticket (root cause: archive một phần)
- **What:** Khi sang ticket mới, archive/reset toàn bộ artifacts ticket cũ khỏi `knowledge/active/`: `TASK_QUEUE.md`, `TASK_HANDOFF.*.md`, `TASK_RESULT.*.md`, **và `PARENT_BRAIN.md`** (mirror cuộc trò chuyện). Dùng event `archive_started`/`archive_done` đã có. Hiện tại reset **một phần**: chỉ `AGENT_TRANSPARENCY` được reset sang ticket mới, các file còn lại bị bỏ lại → overlap.
- **Why:** Phát hiện 2026-06-20 soi BA-Framework live, 3 nguồn 2 ticket cùng lúc: `AGENT_TRANSPARENCY` = `SME-TRANSFER-003` (đang `applying`), nhưng `TASK_QUEUE`+results = `SME-TRANSFER-002` (00:09 hôm trước), `PARENT_BRAIN` = cuộc trò chuyện `SME-TRANSFER-002` (17:29 hôm trước). Chính `PARENT_BRAIN` thú nhận "SME-TRANSFER-002 was already archived/reset in AGENT_TRANSPARENCY.md" → archive không trọn vẹn. Dashboard hiện phase ticket mới đè lên queue + conversation ticket cũ ("overlap"). Lỗi vòng đời artifact, không phải lỗi dashboard.
- **Context:** orchestrator emit ([.amap/tools/microloop-orchestrator/orchestrator.py](.amap/tools/microloop-orchestrator/orchestrator.py)); contract [docs/superpowers/specs/2026-06-19-dashboard-runtime-contract-design.md](docs/superpowers/specs/2026-06-19-dashboard-runtime-contract-design.md) §6 (event `archive_*`). Liên quan P5 roadmap.
- **Effort:** CC ~30-45 phút. **Priority:** P3 (gốc của P3.5).

### P3.5 — Dashboard: ticket-aware, tách artifacts ticket-trước khỏi ticket hiện tại (symptom mitigation)
- **What:** Trong `read_runtime`, lấy `current_ticket` từ `AGENT_TRANSPARENCY`; với `TASK_QUEUE` và `PARENT_BRAIN`, nếu `ticket_id` của chúng `≠ current_ticket` (hoặc mtime ≪ phase mtime) thì đánh dấu "từ ticket trước" thay vì gộp vào progress/parent-panel hiện tại. UI: không khoe `2/2 100%` và không hiện parent-brain cũ dưới ticket mới.
- **Why:** Giảm overlap khi P3.4 chưa làm. Use case thật đã quan sát: queue=002, parent_brain=002, phase=003. **KHÔNG làm trong PR #10** — CEO verdict freeze dashboard ở P6; việc sau, sau khi quay lại từ P1.1.
- **Context:** [cli/dashboard/server.py](cli/dashboard/server.py) `read_runtime`, [cli/dashboard/reader.py](cli/dashboard/reader.py) `read_run`.
- **Effort:** CC ~30 phút. **Priority:** P3. **Depends on:** ưu tiên P3.4 trước (sửa gốc).

### P3.6 — Tách orchestrator: pure loop-protocol vs dashboard emit (SRP nhẹ)
- **What:** `orchestrator.py` đang gánh 2 vai trong một file: pure loop-protocol (`run_loop`/`next_task`/`apply_result`/`topo_sort` — DI, không I/O, unit-test được) và dashboard emit (`append_activity_event`/`write_parent_brain`/`initialize_runtime_queue` — I/O filesystem). Tách phần emit ra module riêng (vd `runtime_emit.py`) khi thuận tiện.
- **Why:** SRP nhẹ; emit đặt cạnh nơi sở hữu lifecycle queue/handoff là hợp lý nên không gấp. Tách giúp test pure-protocol khỏi đụng filesystem rõ ràng hơn.
- **Context:** [.amap/tools/microloop-orchestrator/orchestrator.py](.amap/tools/microloop-orchestrator/orchestrator.py).
- **Effort:** CC ~20 phút. **Priority:** P3 (nhẹ nhất). **Depends on:** nên làm cùng/sau P2.5 (single-source constants).

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
