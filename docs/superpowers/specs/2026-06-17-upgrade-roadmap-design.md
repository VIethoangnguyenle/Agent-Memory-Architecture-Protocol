# Upgrade Roadmap — Đưa AMAP v3 về Production-Ready (Generic + Portable)

> **Phiên bản:** 1.0 | **Ngày:** 2026-06-17
> **Loại:** Strategy / Sequencing design (roadmap, không phải feature design)
> **Scope:** Tái cấu trúc 4 ưu tiên trong `upgrade.md` (P0–P3) thành một roadmap thực thi
> có thứ tự, phân rã được thành các sub-spec độc lập.
> **Output:** Roadmap + phân rã sub-project. Mỗi work item sau đó chạy vòng
> spec → plan → implement riêng. Doc này là **parent index** của các sub-spec đó.

---

## 1. North Star (tiêu chí chấm điểm mọi quyết định)

Mục đích cuối: biến AMAP thành một framework **chỉ ship quy trình + mindset phát triển**,
không ship nội dung dự án. Bốn thuộc tính đích — dùng làm **Definition of Done** cho toàn roadmap:

1. **Generic** — repo framework chỉ chứa skeleton + quy trình; nội dung business của một dự án
   cụ thể (vd Vietbank) sống ở repo đích, không lẫn vào framework.
2. **Knowledge-first** — dẫn dắt bởi tầng tri thức / bộ MCP (code search, graph, doc search).
3. **Long-term memory** — có cơ chế nhớ dài hạn (memory hierarchy: active / long-term / archive).
4. **IDE/agent-independent** — chạy trên Claude, Codex, Cursor, Gemini... không khoá vào một loại;
   workflow phụ thuộc *năng lực trừu tượng*, không phải tool cụ thể.

> **Nguyên tắc đọc roadmap:** mỗi item được xếp thứ tự theo việc nó phục vụ thuộc tính North Star
> nào, và phục vụ mạnh tới đâu. Item không phục vụ thuộc tính nào (chỉ DX/adoption) bị lùi xuống cuối.

---

## 2. Hiện trạng đã hiệu chỉnh (grounding)

`upgrade.md` mô tả 4 việc như thể đều còn nguyên. Kiểm tra repo cho thấy thực tế khác:

| Hạng mục | Trạng thái thực | Bằng chứng |
|---|---|---|
| **SP1 — Phase 3 Reliability** (rule-projector, microloop, outcome loop) | **Đã BUILD, pass fixture test, CHƯA validate E2E** | `.agent/tools/rule-projector/` (projector + IR schema + backends + git hook + generated), `.agent/tools/microloop-orchestrator/` (orchestrator + contract + extraction + outcome + stats + tiers) đều có code + tests |
| **P2 — Neutrality** | **Phần lớn đã xử lý** | `knowledge-snapshot.md` còn 215 dòng / 1 ref "vietbank"; commit `0e5d2b0` strip author-dna/conventions từ ~1548 → 85 dòng |
| **P1 — Workflow tiering** | **Chưa có** | `tiers/` trong orchestrator là tier *reload DNA* trong Pha 3, không phải phân loại task ở cổng `/task` |
| **P3 — `amap migrate`** | **Chưa có** | `cli/commands/` chỉ có init/status/update |
| **IDE-independence (tool-capability interface)** | **Chưa có spec; gap thật** | ~16 file framework (rules + workflows + skills) hardcode `opsx`/`socraticode`/`get_graph_stats`/`antigravity` (W5). SP2 spec **tự loại trừ**: *"Portability layer / tool adapter — thuộc SP3+"* |

**Hệ quả then chốt:**
- 3/4 thuộc tính North Star (knowledge-first, long-term memory, generic-content) **đã build** → cần
  **validate**, không cần build mới.
- Thuộc tính DUY NHẤT còn thiếu build = **IDE-independence** → là một sub-project **mới, chưa specced**
  (gọi là **SP3-portability**). Đây là đòn bẩy build lớn nhất tới North Star.
- "SP2 (skill standardization)" là việc **khác**, đã có spec, đóng vai **enabler** cho SP3-portability.

---

## 3. Các work item (đặt tên + ánh xạ P0–P3)

| Item | Bản chất | Phục vụ North Star | Map upgrade.md |
|---|---|---|---|
| **U2-min** — dọn dư lượng project khỏi repo framework + chốt policy file-ownership | cleanup + policy | #1 Generic (gate) | P2 (phần gating) |
| **U0** — litmus E2E trên ticket thật | *validation, không build* | #2 #3 (chứng minh hoạt động) | P0 |
| **U3** — `amap migrate` (backfill schema additive) | build CLI, độc lập | nền cho release | P3 |
| **SP2** — skill standardization (đã có spec) | enabler cho portability | tiền đề #4 | — |
| **SP3-portability** — tool-capability interface | build, **mới** | **#4 IDE-independence** | — (+ nuốt U2-full) |
| **U1** — workflow tiering ở `/task` | build, hình theo bằng chứng | DX/adoption (không phải North Star) | P1 |

---

## 4. Định nghĩa từng sub-spec (entry / scope / exit / deliverable)

### U2-min — Dọn dư lượng project (gate cho litmus trung thực)
- **Entry:** ngay bây giờ.
- **Scope:** quét file *framework-owned* (`knowledge-snapshot.md`, ví dụ trong `rules/`, `skills/`)
  tìm nội dung business Vietbank; chốt **policy "framework vs project"** — repo framework chỉ ship
  skeleton + kiến trúc *của chính AMAP*; nội dung dự án thật sống ở repo đích. Phân loại rõ
  **file user-owned vs framework-owned** (đầu vào cho U3). Xác nhận `.gitignore` phủ `active/`.
- **Exit:** 0 nội dung business project trong file framework-owned; 1 file policy ngắn; bảng phân
  loại file-ownership.
- **Deliverable:** policy doc + repo sạch. **Nhỏ** (chủ yếu verify + dời 1 dư lượng + viết policy).

### U0 — Litmus E2E (validation, KHÔNG build)
- **Entry:** U2-min xong; có 1 ticket Standard-complexity thật (đụng DB + code).
- **Scope:** chạy full `Ideation → Requirement → Architecture → Spec → Apply` trên ticket thật với
  bản SP1 hiện tại. **Instrument ma sát:** chỗ agent khựng, mechanical gate bắn đúng/sai (false
  positive), token/pha, chỗ người phải can thiệp tay. **Chạy trên Vietbank với `active/` reset rỗng**
  để vừa thực chiến vừa quan sát knowledge-accumulation từ cold-start.
- **Exit:** `litmus-report` — friction points đã xếp hạng + verdict "SP1 chạy E2E được/không".
- **Deliverable:** `litmus-report`. **Triage rule:** mỗi friction item phân loại
  `(thuộc-U1-tiering)` / `(patch-SP1)` / `(issue-mới)` để ngăn rework vô hạn.
- **Lưu ý:** đây là **test protocol**, không sửa code trong phạm vi U0. Fix tách thành patch SP1 sau.

### U3 — `amap migrate` (build CLI, song song)
- **Entry:** ngay bây giờ, độc lập litmus. Tiêu thụ bảng file-ownership của U2-min.
- **Scope:** **subcommand `amap migrate` riêng** (không nhét vào `update`; `update` chỉ gọi nó).
  Migration **additive** cho file *user-owned* (`author-dna.yaml`, `conventions.yaml`, `persona.yaml`):
  dấu version trong file → phát hiện schema cũ → thêm field mới kèm default → **không bao giờ ghi đè
  giá trị user** → báo diff.
- **Exit:** update project cũ backfill field mới an toàn.
- **Deliverable:** lệnh `amap migrate` + test phủ additive-merge + no-clobber.

### SP2 — Skill standardization (đã có spec, enabler)
- **Entry:** độc lập litmus → chạy song song với U3.
- **Scope:** theo `2026-06-17-sp2-skill-standardization-design.md` — chuẩn hoá 14 skills về
  frontmatter/body/I/O contract.
- **Vai trò trong roadmap:** I/O contract chuẩn hoá là **tiền đề** để SP3-portability swap tool
  backend sạch (orchestrator route theo `pre_conditions`/`outputs` thay vì biết tool cụ thể).

### SP3-portability — Tool-capability interface (build, MỚI)
- **Entry:** sau U0 (process đã validate + patch blocker) và SP2 (skill contract đã chuẩn).
- **Scope:** định nghĩa **interface năng lực trừu tượng** (`propose_spec`, `explore_code`,
  `query_graph`, `search_docs`...) để workflow/skill/rule phụ thuộc *năng lực*, không phải tool cụ thể
  (OpenSpec, Socraticode, UA MCP). Rút ~16 chỗ hardcode về adapter resolve qua `amap init`. **Nuốt
  phần tách Core / Project Pack của U2-full.** Rule Projector nên sinh **IR trung lập (JSON)** trước,
  backend dịch sang Checkstyle/PMD — thêm ngôn ngữ chỉ thêm backend.
- **Exit:** 0 tool cụ thể hardcode trong protocol body; framework chạy được trên ≥2 agent
  (vd Claude Code + một agent khác / generic fallback).
- **Deliverable:** capability interface + adapter layer + Core/Project boundary doc.
- **Lưu ý:** đây mới là hiện thân của thuộc tính North Star #4 — **cần spec riêng**.

### U1 — Workflow tiering ở `/task` (build, cuối / optional)
- **Entry:** đã có `litmus-report` (chỗ cắt tier dựa trên bằng chứng, không đoán).
- **Scope:** classifier ở cổng `/task` → tiny / standard / complex. Tiny bỏ explore nặng (DB/arch),
  commit nhanh. Chốt: **tín hiệu phân loại** (heuristic / user khai báo / LLM-judge), mỗi tier bỏ gì,
  **tương tác với DNA tiered-loading (SMALL/MEDIUM/LARGE)** và **mechanical gate (vẫn chạy ở MỌI tier)**.
  **Mặc định bảo thủ:** nghi ngờ → standard.
- **Exit:** path tiny rẻ hơn đo được (token); full pipeline giữ nguyên cho standard/complex.
- **Deliverable:** task classifier + tier routing.

---

## 5. Thứ tự thực thi & gate (xương sống)

```
Track Validate :  U2-min ──► U0 ──► (patch SP1 nếu litmus lộ blocker)
Track Harden   :  U3 (amap migrate)   ∥   SP2 (skill standardization)
                            └───────────────┬───────────────┘
                                            ▼
                            SP3-portability  (tool-capability interface = IDE-independence;
                                              nuốt phần tách Core/Project của U2-full)
                                            ▼
                            U1 tiering  (cuối / optional polish)
```

**Logic gate (soft-gate có mục tiêu, KHÔNG phải hard-gate chặn tất):**
- **U2-min chặn U0** — phải sạch trước thì litmus mới đo trung thực được knowledge-accumulation.
- **U0 chặn U1** — đây mới là chỗ "pause feature dev" của upgrade.md *thực sự* có nghĩa: đừng build
  *tiering* mù khi chưa có friction log.
- **U0 + SP2 chặn SP3-portability** — chỉ đầu tư làm process *portable* sau khi process đã *chạy đúng*
  (validate) và *skill contract đã chuẩn* (enabler).
- **U3 KHÔNG bị chặn** — đụng CLI, không đụng protocol → song song an toàn.
- **SP2 KHÔNG bị chặn bởi litmus** — chỉnh file skill, độc lập → song song với U3.

**So với upgrade.md:** thứ tự đổi từ `P0→P1→P2→P3` (tuần tự, litmus chặn tất) thành
`(U2-min→U0) ∥ U3,SP2 → SP3-portability → U1`. Khác biệt cốt lõi: (a) litmus chỉ chặn đúng cái cần
chặn; (b) **portability tách thành SP3-portability riêng và nâng lên trước U1** vì nó là thuộc tính
North Star; (c) **U1 tiering xuống cuối** vì không phục vụ thuộc tính North Star nào.

---

## 6. Rủi ro & quyết định đã chốt

| # | Rủi ro | Xử lý (đã chốt) |
|---|---|---|
| R1 | **Litmus không trung thực** — agent đã biết sẵn kiến trúc nếu snapshot còn dữ liệu | U0 chạy **Vietbank + `active/` reset rỗng**, đo cái gì được tích luỹ mới từ cold-start |
| R2 | **Friction log nở ngoài tầm** — litmus lộ bug to hơn tiering | Triage rule trong U0: `(U1-tiering)` / `(patch-SP1)` / `(issue-mới)` |
| R3 | **Tiering phân loại sai** — tiny bị xếp nhầm → bỏ arch review → vỡ | Mặc định bảo thủ (nghi ngờ → standard); gate cơ học vẫn chạy ở mọi tier |
| R4 | **U3 ↔ U2-min coupling mềm** (dù song song) | U2-min chốt phân loại file-ownership **trước**; U3 chỉ đụng file user-owned |
| R5 | **Chồng lấn neutrality** | U2-min sinh **policy**; SP3-portability **implement** phần tách Core/Project theo policy đó. Không làm hai lần |
| R6 | **SP2 spec quá hẹp** so với portability | Đã xác nhận: SP2 = skill standardization; portability tách hẳn thành **SP3-portability** (spec mới) |

---

## 7. Ánh xạ ngược về upgrade.md (truy vết)

| upgrade.md | Trong roadmap này |
|---|---|
| **P0** — Litmus test trên dự án thực | **U0** (giữ ưu tiên cao, đứng đầu track Validate) |
| **P1** — Workflow tiering | **U1** (lùi xuống cuối — không phục vụ North Star) |
| **P2** — Dọn knowledge-snapshot / neutrality | **U2-min** (gate) + phần cấu trúc nuốt vào **SP3-portability** |
| **P3** — Schema migration | **U3** (`amap migrate` riêng, chạy song song) |
| *(ẩn trong upgrade.md)* — IDE-independence | **SP3-portability** (nâng lên trước U1) |

---

## 8. Phân rã & bước tiếp theo

Doc này là **parent index**. Mỗi item là một vòng spec → plan → implement riêng, theo thứ tự ở §5:

1. **U2-min** (nhỏ, gate) — spec riêng.
2. **U0** (test protocol) — spec riêng (litmus protocol + instrument + triage rule).
3. **U3** (`amap migrate`) — spec riêng (song song).
4. **SP2** — đã có spec, thực thi.
5. **SP3-portability** — **spec mới** (đòn bẩy North Star lớn nhất).
6. **U1** — spec riêng (sau khi có `litmus-report`).

Sub-project nên brainstorm đầu tiên theo vòng đầy đủ: **U2-min** (mở khoá U0) hoặc **U0** (mở khoá phần
còn lại) — tuỳ ưu tiên muốn validate sớm hay dọn sạch trước.
