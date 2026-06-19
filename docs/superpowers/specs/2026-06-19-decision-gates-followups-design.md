# Decision-Point Gates — Follow-ups (post sub-spec #1)

> Ngày: 2026-06-19
> Trạng thái: P0/P1/P2 COMPLETE trên branch `amap-gate-followups-p1p2`; P3 sub-spec sau vẫn là backlog riêng.
> Nguồn: review findings trong quá trình implement `amap-retro-decision-gates` (2-stage review + final holistic review).
> Liên quan: `2026-06-18-decision-point-gates-design.md`, `2026-06-18-amap-retro-fix-program-design.md`.

Sub-spec #1 đã ship các **evidence-checker deterministic** (`gate-check`), **knowledge-index generator**, **bootstrap diet**, và collapse 4 gate vào rules (net-negative xác nhận). Doc này ban đầu ghi backlog sau merge; hiện các follow-up nhỏ P1/P2 đã được xử lý, còn lại quyết định kiến trúc P0 và các sub-spec sau.

---

## P0 — Gate trigger chưa deterministic (đúng luận điểm cốt lõi)

- **Vấn đề:** Các gate hiện được tham chiếu bằng *prose* trong rules (R-Guard-2/R-Tool-8/R-Flow-2/R-Tool-5) trỏ tới `gate-check/cli.py`. Bản thân *checker* là deterministic + có test, nhưng *trigger* để chạy nó vẫn do agent tự giác — đúng class lỗi "prose bị skip" mà chương trình muốn diệt.
- **Vì sao chưa làm:** Spec §2/§6 định dùng `pre_conditions:` (R-Guard-1) trên skill sinh-artifact. Nhưng đường apply thực tế là `workflows/opsx-apply.md` + `procedures/executor.md` — **không phải `SKILL.md` có frontmatter**. Không có "nhà" tự nhiên cho `pre_conditions`.
- **DONE — Decision 2026-06-19:** chọn option 2, nhưng portable qua scaffold capability, không hook cứng mọi nơi:
  - Capability mới: `write_gate_hook`.
  - Manifest filter mới: `requires_platform_capability`; config adapter riêng có thêm `requires_platform`.
  - `claude-code`: true — scaffold `.claude/settings.json` + `.claude/hooks/write-gate/`.
  - `codex`: true — scaffold `.codex/hooks.json` + `.agents/hooks/write-gate/`.
  - `antigravity`: true — scaffold `.agents/hooks.json` + `.agents/hooks/write-gate/`.
  - `generic`: false — không claim deterministic runtime gate; degrade rõ trong docs/report.
- **Các option đã cân nhắc:**
  1. Mở rộng cơ chế `pre_conditions` để **workflow** cũng khai báo được (skill-lint + R-Guard-1 hỗ trợ workflow), rồi gắn gate vào `opsx-apply.md`.
  2. Thêm một **runtime pre-Write/Edit hook** chặn ghi code khi gate chưa pass (đã hoãn ở #1 vì portability — chỉ làm cho platform hỗ trợ hook, degrade-graceful cho platform không hỗ trợ).
  3. Tách một **apply SKILL.md** có frontmatter `pre_conditions` làm entry cho code-gen, để R-Guard-1 fire.
- **Exit:** một fixture chứng minh "thiếu KNOWLEDGE_CHECKPOINT hợp lệ → không vào được apply" được enforce ngoài prose.

## P0 — Residual C-22 (write thô ngoài flow)

- **DONE** B + selective-C **không** chặn agent dùng `Write/Edit` thô ngoài mọi `/task` skill. Runtime write-gate hiện chặn app-code writes thiếu `KNOWLEDGE_CHECKPOINT` hợp lệ trên platform có `write_gate_hook`.

## P1 — Hardening checker (gate-by-evidence chặt hơn)

- `gate-check/gates.py`:
  - **DONE** `_DEGRADE` dùng `.*` same-line → có thể false-positive khi "KG unavailable" và "MEDIUM" xuất hiện rời rạc cùng dòng. Đã siết bằng compact bounded match + regression test. Commit: `26c1a59`.
  - **DONE** `_RULE_ID` `\b[A-Z]{2,3}-\d+\b` khớp cả `ISO-9001`/`PR-42`/`RFC-2119`. `gate-check` giờ nhận `valid_rule_ids` từ `knowledge-index.yaml` và reject rule-id ngoài index.
  - **DONE** Governance-degrade (`no approved … LOW`) hiện pass *bất kể* có rule-id — giờ chỉ pass khi caller cho biết index không có matching entries.

## P1 — Genericity: `ARTIFACT_SECTION_MAP`

- **DONE** `context-loader.md` còn map cứng `Factory/Service/Handler/Repository/...` (pre-existing, nay relabel "cũ — vẫn dùng để khớp `applies_to`"). Đã generic-hoá: decision-gate match trực tiếp theo `applies_to` từ project, bỏ map cứng. Commit: `2c85735`.

## P1 — MCP-status tại bootstrap

- **DONE** `bootstrap.md` PHASE 5 report hiện **không có** dòng MCP-status → probe không bị bắt buộc ngay đầu phiên. Đã thêm MCP-status bắt buộc: in node/edge count thật hoặc dòng degrade và pass `mcp-status` gate. Commit: `54b2d17`.

## P2 — Test infra (pre-existing, không do branch này gây ra)

- **DONE** `pytest cli/tests .amap/tools` lỗi collection do `tests/__init__.py` trùng tên package giữa các tool dir → đã thêm `[tool.pytest.ini_options] addopts = "--import-mode=importlib"` vào `pyproject.toml`. Commit: `5e7ef99`.
- **DONE** `test_snapshots.py` không hermetic: scaffold từ cây sống nên file gitignored local (`knowledge/long-term/persona.yaml`, `tools/rule-projector/generated/*`) lọt vào output → đã exclude per-project instance/build artifacts ở renderer. Commit: `5e7ef99`.
- **DONE** `knowledge-index/`: đã thêm integration test cho `build_index`/`main` ghi file thật → assert số entry. Commit: `7b90335`.

## P3 — Phần còn lại của chương trình (sub-spec riêng)

Xem `2026-06-18-amap-retro-fix-program-design.md` §5:
- **#2** Mechanical style enforcement (rule-projector → checkstyle/linter, cắm vào verify gate) — sẽ là chỗ enforce cơ học cho SP-6/SP-7/FQN/spacing (cluster D).
- **#3** Verification & bookkeeping gate (chặn "Done" tới khi build pass + transparency/token) — compose với completion-gate của Gate #3.
- **#4** Knowledge capture correctness (teaching-moment → đúng store trong phiên).
- **#5** Model-driven consolidation (normalize toàn bộ skill/workflow về gate model + audit merge/xoá) — chỗ "refactor toàn bộ"; P0 gate-trigger ở trên có thể giải quyết trong #5 nếu chọn option 1/3.

---

## Ưu tiên tiếp theo
P3 sub-spec #2..#5 theo thứ tự chương trình:
1. Mechanical style enforcement.
2. Verification & bookkeeping gate.
3. Knowledge capture correctness.
4. Model-driven consolidation.

## Completed on `amap-gate-followups-p1p2`

- `803f9d5` — ship `gate-check` + `knowledge-index` tools via `amap init`.
- `4f558ad` — add C-10/C-22 regression fixtures.
- `5e7ef99` — pin pytest import mode and exclude per-project/build artifacts from scaffold copy.
- `7b90335` — add `knowledge-index` integration tests.
- `26c1a59` — tighten `_DEGRADE`.
- `2c85735` — genericize context-loader artifact-type slice.
- `54b2d17` — force MCP-status probe line at bootstrap.
