---
description: Orchestrator /task (đa pha) cho ideation + ticket + OpenSpec.
---

# /task — Orchestrator chính

`/task` là cổng vào duy nhất cho mọi công việc liên quan đến task trong repo này.

Các chế độ sử dụng:

- `/task <ý-tưởng-hoặc-link>`      → Pha 1: ideation / requirement / explore.
- `/task spec <ticket-id-or-link>` → Pha 2: sinh spec (propose).
- `/task apply <ticket-id>`        → Pha 3: apply spec vào code.

Trước khi kết thúc mỗi pha quan trọng, hãy cập nhật `.knowledge-layer/active/AGENT_TRANSPARENCY.md`.

> **Path convention**: Tất cả file context tuân theo quy ước trong `.agent/rules/RULES.md` section "Path Convention".

---

## 0. Bootstrap context (bắt buộc)

Trước khi bắt đầu bất kỳ nhánh nào, luôn chạy bước bootstrap:

1. Kiểm tra `.knowledge-layer/active/REQUIREMENT.md`:
   - Nếu file có nội dung thật (không chỉ là template trống) → hỏi user:
     > "Active context đang có dữ liệu từ task trước. Reset cho task mới hay giữ lại?"
   - Nếu user chọn reset hoặc file là template trống → giữ nguyên skeleton.
2. Tương tự cho `.knowledge-layer/active/EXPLORE_CONTEXT.md`.
3. Reset `.knowledge-layer/active/AGENT_TRANSPARENCY.md`:
   - Ghi mới với task/ticket ID hiện tại.
   - Đánh dấu `[x] AGENTS.md` và `[x] .agent/rules/RULES.md` nếu đã đọc.
   - Ghi vào "Lịch sử pha": `Bootstrap | <thời điểm> | Task: <input>`.

4. Tạo hoặc reset `.knowledge-layer/active/TOKEN_LOG.md`:
   - Nếu chưa tồn tại: tạo từ template `.knowledge-layer/templates/TOKEN_LOG.tpl.md`.
   - Điền: ticket-id (hoặc "unknown" nếu IDEA_ONLY), timestamp bắt đầu, model name (nếu biết).
   - Ghi bootstrap token estimate vào section "Bootstrap".

---

## 1. `/task <ý-tưởng-hoặc-link>` — Pha 1: Hiểu vấn đề

### 1.1 Nhận diện loại input

Từ giá trị `<ý-tưởng-hoặc-link>`, phân loại:

- Chuỗi chứa URL hoặc key của ticket (ví dụ: `ABC-123`) → `HAS_TICKET`.
- Chuỗi chứa URL tài liệu (wiki/Confluence/PRD/...) nhưng không có ticket → `HAS_DOC_ONLY`.
- Còn lại → `IDEA_ONLY`.

Sau khi nhận diện:

- Cập nhật `.knowledge-layer/active/AGENT_TRANSPARENCY.md` mục "Nguồn đã đọc" với loại input tương ứng.
- Ghi lại raw input (ý tưởng, link) để trace.

---

### 1.2 Nhánh IDEA_ONLY — Ideation

1. Tạo file `ideation-*.md` trong `.knowledge-layer/active/ideation/` theo template:
   - Ghi:
     - Tóm tắt ý tưởng.
     - Động lực (tại sao muốn làm).
     - Bối cảnh sơ bộ (hệ thống nào, đối tượng chính là ai).
2. Hỏi–đáp với user để:
   - Làm rõ mục tiêu business.
   - Gợi ý phạm vi (in-scope / out-of-scope).
   - Gợi ý các Acceptance Criteria ở mức high-level.
3. (Tuỳ chọn) Gọi `codebase-explorer`:
   - Để hiểu codebase hiện tại đang có module/service nào *có thể* liên quan.
   - Ghi lại vào `ideation-*.md` phần “Liên hệ với hệ thống hiện tại”.
4. Cập nhật lại `ideation-*.md` với:
   - Scope đề xuất.
   - AC đề xuất (chưa phải commit cuối cùng).
5. Cập nhật `.knowledge-layer/active/AGENT_TRANSPARENCY.md`:
   - Đánh dấu đã tạo/ cập nhật file ideation.
6. Gợi ý user:
   - Tạo ticket chính thức (Jira/…).
   - Sau khi có ticket, dùng `/task <ticket-link-or-id>` để đi tiếp Pha 1 cho `HAS_TICKET`.

---

### 1.3 Nhánh HAS_DOC_ONLY — Có tài liệu, chưa có ticket

1. Gọi skill `spec-extract`:
   - Trích nội dung có cấu trúc từ tài liệu vào `.knowledge-layer/active/REQUIREMENT.md`.
   - Ghi rõ nguồn tài liệu (URL, tên trang).
2. Kiểm tra Độ tin cậy do `spec-extract` gán:
   - Nếu **THẤP**:
     - Ghi cảnh báo vào `.knowledge-layer/active/AGENT_TRANSPARENCY.md`.
     - Thông báo cho user rằng tài liệu chưa đủ tin cậy để đi tiếp (architecture/spec/implementation).
     - Dừng pipeline tại đây cho tới khi tài liệu được cập nhật.
   - Nếu **CAO/TRUNG BÌNH**:
     - Có thể dùng `/opsx:explore` để thảo luận thêm với user dựa trên REQUIREMENT vừa tạo.
3. Gợi ý user:
   - Tạo ticket từ `REQUIREMENT`.
   - Sau đó quay lại `/task <ticket-link-or-id>` để đi qua luồng `HAS_TICKET`.

---

### 1.4 Nhánh HAS_TICKET — Task cụ thể

1. Gọi `requirement-analyst`:
   - Đọc toàn bộ ticket + tài liệu liên kết.
   - Chuẩn hoá `.knowledge-layer/active/REQUIREMENT.md` với context, As-is/To-be, scope, AC, giả định, vấn đề yêu cầu.
2. Nếu requirement chạm tới dữ liệu:
   - Gọi `db-explorer`:
     - Khám phá tầng database liên quan (schema, constraint, trigger/procedure…).
     - Cập nhật section "Tầng Database (db-explorer)" trong `.knowledge-layer/active/EXPLORE_CONTEXT.md`.
3. Gọi `codebase-explorer`:
   - Đọc `.knowledge-layer/active/REQUIREMENT.md`, map yêu cầu → module/service/file.
   - **[GATE] Kiểm tra trạng thái KG graph trước bất kỳ tool nào khác** (theo R-Tool-5b):
     - Gọi `get_graph_stats` (KG MCP Server) để xem graph có tồn tại và đủ mới không.
     - Nếu **graph OK** → dùng KG tools làm nguồn chính:
       - `query_nodes` → tìm nodes liên quan đến REQUIREMENT.
       - `get_node_source` → đọc code thực tế.
       - `get_relationships`, `trace_call_chain` → hiểu dependency và flow.
       - `get_domain_detail` → business flow nếu cần.
     - Nếu **chưa có graph hoặc quá cũ**:
       - Gợi ý user chạy `/understand` để rebuild graph.
       - Trong lúc chờ, dùng Socraticode/search/grep với Độ tin cậy thấp hơn.
   - Nếu cần câu hỏi open-ended → dùng `/understand-chat` (secondary).
   - Bổ sung bằng Socraticode cho semantic search khi KG fuzzy search chưa đủ.
   - Cập nhật section "Kiến trúc code hiện tại (codebase-explorer)" trong `.knowledge-layer/active/EXPLORE_CONTEXT.md`.
   - **Ghi kèm node_id** cho mỗi component quan trọng → cho phép architecture-reviewer dùng `get_node_source(id)` sau.
4. Gọi `architecture-reviewer`:
   - Đối chiếu `.knowledge-layer/active/REQUIREMENT.md` + `.knowledge-layer/active/EXPLORE_CONTEXT.md` + `.knowledge-layer/templates/knowledge-snapshot.md`.
   - Nếu EXPLORE_CONTEXT có node IDs → dùng KG tools (`find_impact`, `get_node_source`, `get_relationships`) để verify.
   - Đánh giá:
     - Điểm align với kiến trúc hiện tại.
     - Điểm xung đột/rủi ro (boundary, ownership, coupling, DB, non-functional…).
   - Ghi mức độ nghiêm trọng (LOW/MEDIUM/HIGH/BLOCKER) và Độ tin cậy kiến trúc (CAO/TRUNG BÌNH/THẤP).
4a. **[H1 — BLOCKER Recovery]** Nếu `architecture-reviewer` đánh dấu mức **BLOCKER**:
   - Cập nhật `phase_state: blocked-by-arch` trong AGENT_TRANSPARENCY.md.
   - Ghi rõ vào AGENT_TRANSPARENCY.md:
     ```
     [BLOCKER-ARCH] {mô tả blocker}
     Cần action: {gợi ý cụ thể — workshop kiến trúc / làm rõ requirement / bổ sung khám phá}
     Unblock khi: {điều kiện để tiếp tục — vd: "user xác nhận approach"}
     ```
   - **Dừng pipeline** — không tiếp tục sang Pha 2 khi còn BLOCKER chưa resolve.
   - Hiển thị cho user:
     - Tóm tắt blocker (1-3 câu).
     - Gợi ý action cụ thể để unblock.
     - Câu hỏi rõ ràng để user quyết định.
   - **Khi user đã resolve** (xác nhận approach hoặc điều chỉnh requirement):
     - Cập nhật `phase_state: phase-1-done` (xoá blocked state).
     - Ghi vào AGENT_TRANSPARENCY: `[BLOCKER-ARCH RESOLVED] {timestamp} — {cách resolve}`
     - Tiếp tục flow bình thường.

   Tương tự cho **BLOCKED-DATA** (từ R-Flow-4):
   - Cập nhật `phase_state: blocked-by-data`.
   - Ghi `[BLOCKED-DATA] {mô tả} — tiếp tục với assumption đã ghi.`
   - Tiếp tục flow dựa trên assumption (không chờ data — theo R-Flow-4).

5. Gọi `/opsx:explore` — **[H2] BẮT BUỘC** trong các trường hợp sau, tuỳ chọn còn lại:
   - **BẮT BUỘC khi**:
     - Độ tin cậy kiến trúc từ `architecture-reviewer` = **THẤP** hoặc **TRUNG BÌNH**, HOẶC
     - `task_type` = `changerequest` (thay đổi behaviour hiện tại, không phải feature mới).
   - **Tuỳ chọn khi**: Độ tin cậy = CAO và task_type = feature / fixbug / refactor.
   - Nội dung explore:
     - Tóm tắt lại hiểu biết hiện tại cho user:
       - `.knowledge-layer/active/REQUIREMENT.md`.
       - Bối cảnh code + DB từ `.knowledge-layer/active/EXPLORE_CONTEXT.md`.
       - Các rủi ro kiến trúc chính.
     - Cho phép user đặt câu hỏi, refine thêm trước khi sang Pha 2.
   - Ghi vào AGENT_TRANSPARENCY: `[H2] opsx-explore: {required|optional} — lý do: {confidence level hoặc task_type}`
6. Cập nhật `.knowledge-layer/active/AGENT_TRANSPARENCY.md`:
   - Nguồn đã đọc (ticket, tài liệu, code/DB).
   - Skill/tool đã gọi thành công:
     - requirement-analyst, db-explorer, codebase-explorer, architecture-reviewer.
     - Knowledge Graph MCP (chi tiết):
       - `[ ] get_graph_stats`
       - `[ ] query_nodes`
       - `[ ] get_node_source`
       - `[ ] get_relationships / trace_call_chain`
       - `[ ] get_domain_detail`
       - `[ ] find_impact / find_entry_points`
     - UA skills (nếu có).
     - Socraticode (nếu có).
   - Cảnh báo:
     - Thiếu KG graph / thiếu quyền DB / thiếu codebase-access.
   - Độ tin cậy tổng quan sau Pha 1.

7. Ghi token checkpoint vào `.knowledge-layer/active/TOKEN_LOG.md`:
   - Điền timestamp kết thúc Pha 1.
   - Estimate token Pha 1: input (files đọc + tool calls) + output (REQUIREMENT + EXPLORE_CONTEXT + AGENT_TRANSPARENCY).
   - Liệt kê tool calls đáng chú ý (get_node_source nhiều lần, tài liệu dài...).
   - Cập nhật dòng "Pha 1" trong bảng Tóm tắt.
   - Nếu tổng Pha 1 > 50,000 tokens estimate: ghi cảnh báo vào section "Cảnh báo".
   - Tham chiếu protocol đầy đủ: `.agent/scripts/token-tracking.md`.

8. **Đánh dấu Pha 1 hoàn thành** vào `.knowledge-layer/active/AGENT_TRANSPARENCY.md`:
   - Thêm dòng vào section "Lịch sử pha": `Pha 1 DONE | <timestamp> | REQUIREMENT + EXPLORE_CONTEXT đã ghi`
   - Cập nhật `phase_state: phase-1-done` trong block `## Phase State`.
   - Ghi rõ ticket_id (hoặc "HAS_DOC_ONLY / IDEA_ONLY" nếu không có ticket).
   - **Mục đích**: Khi phiên bị truncate và resume, agent đọc được marker này để biết Pha 1 đã xong
     → **không được re-trigger Pha 1** dù active context có vẻ thiếu ticket ID.
   > **Resume rule**: Nếu `phase_state` = `phase-1-done` hoặc cao hơn → coi Pha 1 đã hoàn thành.
   > Không hỏi lại, không re-run exploration. Chuyển thẳng sang hướng dẫn user chạy `/task spec`.

9. **[POST-PHASE SELF-CHECK — Pha 1]** Trước khi báo "Pha 1 xong" với user:
   - `[ ]` REQUIREMENT.md không còn là skeleton (có nội dung thực).
   - `[ ]` EXPLORE_CONTEXT.md đã được ghi (db-explorer và/hoặc codebase-explorer đã chạy).
   - `[ ]` AGENT_TRANSPARENCY.md có `phase_state: phase-1-done`.
   - `[ ]` TOKEN_LOG.md đã ghi checkpoint Pha 1.
   - `[ ]` architecture-reviewer đã chạy và ghi độ tin cậy.
   Nếu bất kỳ ô nào chưa tick: hoàn thành trước khi tiếp tục.

10. **[SESSION-BOUNDARY — Pha 1]** Sau khi POST-PHASE SELF-CHECK pass:
    - Thông báo user:
      > "Pha 1 hoàn thành. **Vui lòng mở session mới** để chạy `/task spec`.
      > Context đã lưu đầy đủ vào `.knowledge-layer/active/`.
      > Session mới sẽ Bootstrap fresh — rule/DNA ở top-of-mind, tránh Context Dilution."
    - Nếu user tiếp tục trong cùng session (gọi `/task spec` ngay):
      - Ghi WARN vào AGENT_TRANSPARENCY: `[SESSION-BOUNDARY] Tiếp tục cùng session sau Pha 1 — rủi ro Context Dilution.`
      - **Không block** — vẫn cho phép tiếp tục, nhưng ghi vào Violation Log.


---

## 2. `/task spec <ticket-id-or-link>` — Pha 2: Sinh spec (propose)

Mục tiêu: dùng OpenSpec để sinh **spec kỹ thuật** dựa trên REQUIREMENT + bối cảnh hệ thống đã hiểu ở Pha 1.

> **[CRITICAL / BẮT BUỘC]**: 
> - **KHÔNG ĐƯỢC** dùng thói quen mặc định của Agent (như tự ý sinh file `implementation_plan.md` hay `plan.md` ở ngoài thư mục repo).
> - **BẮT BUỘC** phải gọi quy trình OpenSpec (`/opsx-propose` hoặc sử dụng skill `openspec-propose`) để sinh bộ artifact chuẩn (`proposal.md`, `design.md`, `spec.md`, `tasks.md`) lưu vào `openspec/changes/<change-id>/`.

1. Định vị context theo ticket:
   - Đọc `.knowledge-layer/active/REQUIREMENT.md` tương ứng ticket.
   - Đọc `.knowledge-layer/active/EXPLORE_CONTEXT.md` (tầng DB + code liên quan).
2. Tóm tắt nhanh cho user:
   - Bối cảnh business.
   - Kiến trúc hiện tại chạm tới yêu cầu.
   - Rủi ro chính (nếu có) từ architecture-reviewer.
3. Cập nhật `.knowledge-layer/active/AGENT_TRANSPARENCY.md`:
   - Đánh dấu đã vào Pha 2 (`/task spec`).
   - Ghi nguồn đã đọc.
4. Hỏi user confirm — **bắt buộc, không được skip**:
   - Hỏi rõ: “Dùng bộ REQUIREMENT + context hiện tại để sinh spec nhé?”
   - Nếu user yêu cầu điều chỉnh nhỏ (scope, AC, approach…), cập nhật trước khi tiếp tục.
   > **[HARDBLOCK]**: Không được suy luận “user đã đồng ý” từ message trước đó, dù message có vẻ
   > rõ ràng (ví dụ: _“triển khai spec để coding”_ không có nghĩa đã confirm OpenSpec flow).
   > Đây là checkpoint kiểm soát duy nhất trước khi thực thi — nếu bỏ qua, mọi lỗi sau đều
   > không phát hiện được sớm.
5. Khi user xác nhận rõ ràng:
   - Cập nhật `phase_state: phase-2-in-progress` trong AGENT_TRANSPARENCY.md.
   - Gọi OpenSpec:
     - Thường là `/opsx:propose` (hoặc `/opsx:new` tuỳ convention).
   - **Không được** dùng planning mode mặc định của agent (sinh `implementation_plan.md`, `plan.md`,
     hoặc bất kỳ file nào ra ngoài `openspec/changes/<change-id>/`) — kể cả khi agent
     runtime có planning mode nằm ngoài workflow này (Antigravity, v.v.).
   - Chờ spec được sinh ra (file spec riêng, ví dụ trong thư mục `spec/`).
   - Xác nhận output path là `openspec/changes/<change-id>/` trước khi báo cáo hoàn thành.
   - **[H5 — State Invalidation]** Sau khi `/opsx:propose` thành công:
     - Ghi `OPENSPEC_STATE: propose_done` vào AGENT_TRANSPARENCY.md (section Cảnh báo / Hạn chế).
     - Cập nhật `phase_state: phase-2-done`.
     - Ý nghĩa: bất kỳ thay đổi requirement nào SAU điểm này đều làm OpenSpec spec hiện tại
       **stale** — phải chạy lại `/opsx:propose` nếu REQUIREMENT bị sửa.
6. Thông báo:
   - Đường dẫn hoặc tên file spec.
   - Nhắc user review, cho feedback (có thể lặp lại `/opsx:propose` nếu cần refine).
7. Cập nhật `.knowledge-layer/active/AGENT_TRANSPARENCY.md`:
   - Ghi rõ:
     - Đã sinh spec cho ticket nào.
     - File spec tương ứng.
     - Độ tin cậy (dựa trên chất lượng REQUIREMENT + context).

8. Ghi token checkpoint vào `.knowledge-layer/active/TOKEN_LOG.md`:
   - Điền timestamp kết thúc Pha 2.
   - Estimate token Pha 2: input (REQUIREMENT + EXPLORE_CONTEXT + OpenSpec instructions) + output (spec file).
   - Cập nhật dòng "Pha 2" trong bảng Tóm tắt.
   - Tham chiếu protocol đầy đủ: `.agent/scripts/token-tracking.md`.

9. **[POST-PHASE SELF-CHECK — Pha 2]** Trước khi báo "Pha 2 xong" với user:
   - `[ ]` spec file tồn tại trong `openspec/changes/<change-id>/`.
   - `[ ]` AGENT_TRANSPARENCY.md có `phase_state: phase-2-done`.
   - `[ ]` `OPENSPEC_STATE: propose_done` đã ghi vào AGENT_TRANSPARENCY.md.
   - `[ ]` TOKEN_LOG.md đã ghi checkpoint Pha 2.
   Nếu bất kỳ ô nào chưa tick: hoàn thành trước khi tiếp tục.

10. **[SESSION-BOUNDARY — Pha 2]** Sau khi POST-PHASE SELF-CHECK pass:
    - Thông báo user:
      > "Pha 2 hoàn thành. **Vui lòng mở session mới** để chạy `/task apply`.
      > Spec đã lưu tại `openspec/changes/<change-id>/`.
      > Session mới sẽ Bootstrap fresh — DNA/conventions ở top-of-mind khi code."
    - Nếu user tiếp tục trong cùng session:
      - Ghi WARN vào AGENT_TRANSPARENCY: `[SESSION-BOUNDARY] Tiếp tục cùng session sau Pha 2 — rủi ro Context Dilution khi code.`
      - **Không block** — nhưng **BẮT BUỘC** chạy DNA-RELOAD (bước 2a trong Pha 3).

---

## 3. `/task apply <ticket-id>` — Pha 3: Apply spec vào code

Mục tiêu: dùng OpenSpec để áp dụng spec đã được chấp thuận vào codebase một cách có kiểm soát.

1. Định vị spec & context:
   - Tìm spec tương ứng ticket (tên file hoặc metadata trong spec).
   - Đọc spec để nắm:
     - File/module sẽ bị chạm.
     - Thay đổi chính (API, logic, DB migration… nếu có).
2. Tóm tắt cho user:
   - “Spec này dự kiến sẽ chạm vào: …”
   - “Các loại thay đổi chính: …”

2a. **[DNA-RELOAD — BẮT BUỘC]** Trước khi sinh bất kỳ đoạn code nào:
    > Gate này chống Mode Switching — kéo DNA/conventions về recency window ngay trước khi code.
    > Kết hợp với Session Boundary (Lớp 1) tạo "sandwich defense": rule ở đầu (bootstrap) + cuối (re-read) context.
    - **READ**: `.knowledge-layer/templates/author-dna.yaml`
      - Focus: `hard_principles` (HP-1..HP-11) + `complexity_thresholds` + `style_preferences` liên quan
    - **READ**: `.knowledge-layer/templates/conventions.yaml` (nếu tồn tại, `status: approved`)
    - Ghi checkpoint vào AGENT_TRANSPARENCY:
      ```
      [DNA-RELOAD] Re-read DNA + conventions trước Pha 3.
      HP loaded: HP-1 (Chain of Responsibility), HP-2 (Template Method), HP-5 (Factory boundary),
                 HP-6 (Zero nesting), HP-7 (No else), HP-8 (SOLID), HP-9 (Config-driven),
                 HP-10 (Post-impl review), HP-11 (Bản chất nghiệp vụ)
      Thresholds: max_nesting=1, max_method_branches=3, max_lines=30, early_return=required
      Conventions: <loaded|not_found|draft_skipped>
      ```
    - **Nếu DNA-RELOAD chưa ghi** → R-Guard-2 checkpoint (đã có) sẽ reject từng artifact.
      DNA-RELOAD là gate cho **TOÀN BỘ pha**, R-Guard-2 là gate cho **từng artifact**.

3. **[M1 — Spec Validation]** Chạy `spec-validator` trước khi apply:
   - Gọi `spec-validator.pre_apply_gate(spec_path, requirement_path)`:
     - Nếu **BLOCK**: dừng apply, hiển thị issues, hỏi user fix spec rồi chạy lại `/task spec`.
     - Nếu **PASS**: tiếp tục.
   - Gọi `spec-validator.check_ac_coverage(spec_path, requirement_path)`:
     - Nếu có AC chưa cover: hiển thị danh sách, hỏi user có muốn tiếp không.

4. Hỏi **xác nhận cuối cùng**:
   - Nêu rõ đây là bước sẽ đề nghị thay đổi code theo spec.
   - Nếu user muốn, có thể giới hạn phạm vi (chỉ generate patch, không apply; hoặc chỉ apply một phần).
5. Khi user đồng ý:
   - Gọi lệnh apply của OpenSpec (tuỳ convention, ví dụ `/opsx:apply`):
     - Tuân thủ mode an toàn nếu có (dry-run, diff-only, PR-only…).
6. Sau khi apply:
   - Chạy `spec-validator.post_apply_verify(spec_path, changed_files)` — ghi kết quả vào AGENT_TRANSPARENCY.
   - Nếu có diff/PR, thông báo lại link hoặc danh sách file thay đổi.
   - Đề nghị bước tiếp theo:
     - Review code.
     - Update test.
     - Triển khai / release, v.v. (ở mức gợi ý, không ép).
7. Cập nhật `.knowledge-layer/active/AGENT_TRANSPARENCY.md`:
   - Đánh dấu:
     - Đã chạy `/task apply`.
     - Code đã được chỉnh theo spec (ở mức đề xuất/patch/PR).
   - Ghi:
     - Spec nào đã apply.
     - Bất kỳ hạn chế nào (ví dụ: apply một phần, lỗi khi apply, cần manual follow-up).

7. Ghi token checkpoint CUỐI TASK vào `.knowledge-layer/active/TOKEN_LOG.md`:
   - Điền timestamp kết thúc Pha 3.
   - Estimate token Pha 3: input (spec + codebase context) + output (code changes).
   - Cập nhật dòng "Pha 3" và dòng **TỔNG TASK** trong bảng Tóm tắt.
   - Đây là lần ghi cuối trước khi `knowledge-curator` archive TOKEN_LOG.md.
   - Tham chiếu protocol đầy đủ: `.agent/scripts/token-tracking.md`.

8. **[POST-PHASE SELF-CHECK — Pha 3]** Trước khi gọi knowledge-curator archive:
   - `[ ]` DNA-RELOAD checkpoint đã ghi vào AGENT_TRANSPARENCY (bước 2a).
   - `[ ]` Code changes / diff / PR đã được tóm tắt cho user.
   - `[ ]` AGENT_TRANSPARENCY.md có `phase_state: applying` → đã cập nhật thành `completed`.
   - `[ ]` TOKEN_LOG.md đã ghi TỔNG TASK.
   - `[ ]` Không có BLOCKER chưa resolve trong AGENT_TRANSPARENCY.md.
   - `[ ]` spec-validator.post_apply_dna_check đã chạy (xem spec-validator §3.4).
   Nếu bất kỳ ô nào chưa tick: hoàn thành trước khi gọi knowledge-curator.

9. **[SESSION-BOUNDARY — Pha 3]** Sau khi archive hoàn thành:
    - Thông báo user:
      > "Task hoàn thành và đã archive. **Vui lòng mở session mới** cho task tiếp theo.
      > Session mới sẽ Bootstrap fresh với knowledge-snapshot đã cập nhật."
    - Đây là kết thúc tự nhiên của task — session mới là best practice, không chỉ là gợi ý.

---

## 4. Lưu ý chung cho `/task`

- `/task` chỉ là **orchestrator**:
  - Không thay thế logic chi tiết của từng skill (requirement-analyst, db-explorer, codebase-explorer, architecture-reviewer, spec-extract, OpenSpec).
  - Chỉ quyết định **thứ tự gọi** và **điều kiện dừng/tiếp tục** giữa các pha.
- Ngôn ngữ và xử lý luôn generic:
  - Không encode domain nghiệp vụ cụ thể vào workflow.
  - Chỉ nói về ticket, tài liệu, DB, codebase, spec, kiến trúc.
- Luôn trung thực về trạng thái:
  - Nếu thiếu UA, thiếu DB access, thiếu code access → phải được phản ánh rõ trong `.knowledge-layer/active/AGENT_TRANSPARENCY.md` và trong Độ tin cậy của mọi kết luận.

---

## 5. Tích hợp Knowledge Curator (v2.0)

Sau khi `/task apply` Pha 3 hoàn thành thành công:

```
1. Gọi knowledge-curator.archive_active_context(ticket_id):
   - Lưu toàn bộ active/ vào .knowledge-layer/archive/{ticket_id}/

2. Gọi knowledge-curator.update_knowledge_snapshot(discoveries):
   - Trích discoveries từ EXPLORE_CONTEXT.md:
     - Các table/column mới phát hiện
     - Modules/services đã map
     - Business rules đã xác nhận
   - Cập nhật .knowledge-layer/templates/knowledge-snapshot.md

3. Gọi knowledge-curator.reset_active_context():
   - Reset active/ về skeleton sạch

4. Cập nhật .knowledge-layer/active/AGENT_TRANSPARENCY.md (mới, sau reset):
   - Ghi: "Task {ticket_id} completed and archived at {timestamp}"
   - Mark: [x] knowledge-curator: archive + update_snapshot + reset

5. Thông báo user:
   "Task {ticket_id} đã hoàn thành. Context đã được archive.
    Knowledge snapshot đã cập nhật với {n} phát hiện mới.
    Sẵn sàng nhận task mới!"
```

---

## 6. Path Convention

> Path canonical cho tất cả file context được định nghĩa tại một nơi duy nhất:
> **`.agent/rules/RULES.md` — Section 12, R-Path-1**
>
> Không duplicate bảng path ở đây. Khi cần tra cứu path, đọc RULES.md.