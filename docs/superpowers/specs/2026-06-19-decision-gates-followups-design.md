# Decision-Point Gates — Follow-ups (post sub-spec #1)

> Ngày: 2026-06-19
> Trạng thái: BACKLOG — các hạng mục tồn đọng sau khi sub-spec #1 merge.
> Nguồn: review findings trong quá trình implement `amap-retro-decision-gates` (2-stage review + final holistic review).
> Liên quan: `2026-06-18-decision-point-gates-design.md`, `2026-06-18-amap-retro-fix-program-design.md`.

Sub-spec #1 đã ship các **evidence-checker deterministic** (`gate-check`), **knowledge-index generator**, **bootstrap diet**, và collapse 4 gate vào rules (net-negative xác nhận). Doc này ghi những gì **chưa** làm, để fix sau merge.

---

## P0 — Gate trigger chưa deterministic (đúng luận điểm cốt lõi)

- **Vấn đề:** Các gate hiện được tham chiếu bằng *prose* trong rules (R-Guard-2/R-Tool-8/R-Flow-2/R-Tool-5) trỏ tới `gate-check/cli.py`. Bản thân *checker* là deterministic + có test, nhưng *trigger* để chạy nó vẫn do agent tự giác — đúng class lỗi "prose bị skip" mà chương trình muốn diệt.
- **Vì sao chưa làm:** Spec §2/§6 định dùng `pre_conditions:` (R-Guard-1) trên skill sinh-artifact. Nhưng đường apply thực tế là `workflows/opsx-apply.md` + `procedures/executor.md` — **không phải `SKILL.md` có frontmatter**. Không có "nhà" tự nhiên cho `pre_conditions`.
- **Cần quyết định thiết kế (chọn 1):**
  1. Mở rộng cơ chế `pre_conditions` để **workflow** cũng khai báo được (skill-lint + R-Guard-1 hỗ trợ workflow), rồi gắn gate vào `opsx-apply.md`.
  2. Thêm một **runtime pre-Write/Edit hook** chặn ghi code khi gate chưa pass (đã hoãn ở #1 vì portability — chỉ làm cho platform hỗ trợ hook, degrade-graceful cho platform không hỗ trợ).
  3. Tách một **apply SKILL.md** có frontmatter `pre_conditions` làm entry cho code-gen, để R-Guard-1 fire.
- **Exit:** một fixture chứng minh "thiếu KNOWLEDGE_CHECKPOINT hợp lệ → không vào được apply" được enforce ngoài prose.

## P0 — Residual C-22 (write thô ngoài flow)

- B + selective-C **không** chặn agent dùng `Write/Edit` thô ngoài mọi `/task` skill. Đã ghi nhận honest trong R-Flow-2 ("cần runtime Write-hook sau"). Cùng nhóm quyết định với P0 ở trên (option 2 giải quyết cả hai).

## P1 — Hardening checker (gate-by-evidence chặt hơn)

- `gate-check/gates.py`:
  - `_DEGRADE` dùng `.*` same-line → có thể false-positive khi "KG unavailable" và "MEDIUM" xuất hiện rời rạc cùng dòng. Siết pattern (anchor punctuation / giới hạn khoảng cách).
  - `_RULE_ID` `\b[A-Z]{2,3}-\d+\b` khớp cả `ISO-9001`/`PR-42`/`RFC-2119`. Cân nhắc: nhận một danh sách rule-id hợp lệ từ `knowledge-index.yaml` (project-supplied) thay vì regex thuần — vẫn giữ generic.
  - Governance-degrade (`no approved … LOW`) hiện pass *bất kể* có rule-id — agent có thể viết dòng này để bypass khi DNA *đã* tồn tại. Cân nhắc chỉ cho phép khi index thực sự rỗng cho artifact-type đó.

## P1 — Genericity: `ARTIFACT_SECTION_MAP`

- `context-loader.md` còn map cứng `Factory/Service/Handler/Repository/...` (pre-existing, nay relabel "cũ — vẫn dùng để khớp `applies_to`"). Vi phạm §3.3 (no artifact-type vocabulary trong framework source). Generic-hoá: lấy artifact-type vocabulary từ `applies_to` của project, bỏ map cứng.

## P1 — MCP-status tại bootstrap

- `bootstrap.md` PHASE 5 report hiện **không có** dòng MCP-status → probe không bị bắt buộc ngay đầu phiên. Gate #4 (`mcp-status`) áp dụng khi agent *có* phát MCP-status, nhưng thêm một bước probe bắt buộc ở bootstrap (in node/edge count thật hoặc dòng degrade) sẽ chặn triệt để false "Runtime Ready" như sự cố gốc.

## P2 — Test infra (pre-existing, không do branch này gây ra)

- `pytest cli/tests .amap/tools` lỗi collection do `tests/__init__.py` trùng tên package giữa các tool dir → cần `--import-mode=importlib`. Fix: thêm `[tool.pytest.ini_options] addopts = "--import-mode=importlib"` vào `pyproject.toml` (hoặc bỏ `__init__.py` trùng).
- `test_snapshots.py` không hermetic: scaffold từ cây sống nên file gitignored local (`knowledge/long-term/persona.yaml`, `tools/rule-projector/generated/*`) lọt vào output → fail giả khi dev có các file đó. Fix: fixture scaffold từ `git archive` (clean export) thay vì cây sống; và/hoặc scaffold nên copy `persona.template.yaml` chứ không phải `persona.yaml`, và loại trừ `generated/`.
- `knowledge-index/`: chưa có integration test cho `build_index`/`main` (chỉ test `walk_entries`/`index_snapshot`). Thêm test ghi file thật → assert số entry.

## P3 — Phần còn lại của chương trình (sub-spec riêng)

Xem `2026-06-18-amap-retro-fix-program-design.md` §5:
- **#2** Mechanical style enforcement (rule-projector → checkstyle/linter, cắm vào verify gate) — sẽ là chỗ enforce cơ học cho SP-6/SP-7/FQN/spacing (cluster D).
- **#3** Verification & bookkeeping gate (chặn "Done" tới khi build pass + transparency/token) — compose với completion-gate của Gate #3.
- **#4** Knowledge capture correctness (teaching-moment → đúng store trong phiên).
- **#5** Model-driven consolidation (normalize toàn bộ skill/workflow về gate model + audit merge/xoá) — chỗ "refactor toàn bộ"; P0 gate-trigger ở trên có thể giải quyết trong #5 nếu chọn option 1/3.

---

## Ưu tiên đề xuất
P0 (gate-trigger + C-22, một quyết định kiến trúc chung) → P1 (hardening + genericity + bootstrap probe) → P2 (test infra, rẻ, bảo vệ CI) → P3 (sub-spec #2..#5 theo thứ tự chương trình).
