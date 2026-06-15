---
name: author-dna-builder
description: >
  Phân tích codebase để infer coding philosophy và style của tác giả,
  sau đó interview để confirm/bổ sung, encode thành author-dna.yaml.
  Skill này tạo ra "judgment layer" — lens mà agent dùng khi evaluate
  design và propose solution ở mọi pha.
trigger: /dna-scan
approve_trigger: /approve-dna
---

# Author DNA Builder

## 1. Mục tiêu & Triết lý thiết kế

`author-dna.yaml` khác hoàn toàn với `conventions.yaml`:

| | conventions.yaml | author-dna.yaml |
|-|-----------------|-----------------|
| **Capture** | Naming, suffix, package structure | Coding philosophy, decision principles |
| **Nguồn** | Extract từ code (observable) | Infer từ code + confirm với tác giả |
| **Agent dùng như** | Naming rule khi generate code | Judgment lens khi evaluate design |
| **Có thể sai không** | Hiếm — convention rõ trong code | Có — hypothesis cần author confirm |
| **Update khi nào** | Sau refactor lớn | Khi philosophy thay đổi (hiếm) |

**Nguyên tắc quan trọng nhất**: Agent KHÔNG tự kết luận philosophy từ code.
Agent chỉ được kết luận sau khi tác giả xác nhận. Mọi inference đều là
"hypothesis" cho đến khi có `confirmed: true` trong author-dna.yaml.

---

## 2. Khi nào dùng

- Lần đầu onboard project vào hệ thống (chạy sau `/convention-scan`).
- Tác giả cảm thấy agent đang đề xuất code "đúng về output nhưng sai về style".
- `author-dna.yaml` chưa tồn tại hoặc `status: stale`.
- Sau khi codebase có thay đổi kiến trúc lớn.

Không dùng khi:
- Đang ở giữa Pha 2 hoặc Pha 3 của một task cụ thể.
- Chỉ muốn tra cứu DNA (đọc `author-dna.yaml` trực tiếp).

---

## 3. Quy trình — 4 giai đoạn

### GIAI ĐOẠN 1: Code Evidence Scan

Mục tiêu: Thu thập evidence thực tế từ codebase, không infer intent.

#### 1A. Complexity Profile

```
CALL: get_graph_stats()
  → Lấy tổng số class, method, package

QUERY UA: query_nodes(type="method", limit=500)
  → Lấy tất cả method
  FOR EACH method:
    GET: get_node_source(node_id)  [chỉ lấy method body, không full class]
    ANALYZE:
      - Đếm số if/else/switch/ternary trong body
      - Đếm độ sâu lồng nhau (nesting depth)
      - Đếm số early return
      - Đếm số dòng
    CLASSIFY:
      complexity_score = if_count + (nesting_depth * 2) + switch_count
      complexity_label = HIGH (>10) | MEDIUM (4-10) | LOW (0-3)

AGGREGATE:
  - Distribution: % method LOW / MEDIUM / HIGH complexity
  - Top 5 method complexity cao nhất (có thể là legacy)
  - Top 5 method clean nhất (exemplar của style)
  - Average nesting depth toàn codebase
  - Early return frequency: tổng early return / tổng method
```

#### 1B. Design Pattern Detection

```
QUERY UA: query_nodes(type="class", filter="name matches pattern")
  Patterns cần tìm:
  - Chain of Responsibility: *Processor, *Handler với field "next" hoặc list<>
  - Strategy: I*Strategy, *Strategy implements I*
  - Factory: I*Factory, *Factory với method create/build/make
  - Specification: *Specification, *Spec với method isSatisfiedBy
  - Builder: *Builder với method chain (return this)
  - Decorator: *Decorator wraps *
  - Template Method: abstract class với protected method
  - Observer: *Listener, *Observer, *EventHandler
  - Command: *Command với execute() method

  FOR EACH pattern found:
    GET: get_relationships(node_id) để verify structure đúng pattern
    RECORD:
      - pattern_name
      - occurrence_count
      - exemplar_node_id (class đơn giản nhất, dễ đọc nhất)
      - exemplar_file_path
```

#### 1C. If/Else vs Pattern Substitution Detection

```
Mục tiêu: Tìm bằng chứng TÁC GIẢ ĐÃ CHỦ Ý thay thế if/else bằng pattern.

STRATEGY: So sánh "nơi nên có if/else nhưng không có" với "pattern được dùng thay thế"

QUERY UA: query_nodes(type="class", filter="implements *Factory OR *Strategy")
  FOR EACH factory/strategy:
    GET: get_node_source()
    ANALYZE: Method create/execute có if/else không?
      → Nếu KHÔNG có if/else nhưng xử lý nhiều case: đây là substitution evidence

QUERY Socraticode: codebase_search("switch", limit=50)
  → Tìm tất cả switch statement
  → Nếu count rất thấp so với số case xử lý: strong evidence dùng pattern thay switch

QUERY Socraticode: codebase_search("instanceof", limit=50)
  → instanceof nhiều = ad-hoc type checking = KHÔNG phải style này
  → instanceof ít = polymorphism được dùng đúng

RECORD:
  - switch_count_total
  - instanceof_count_total
  - factory_without_switch: số Factory không dùng switch
  - strategy_without_if: số Strategy không dùng if để dispatch
```

#### 1D. Layer Boundary Discipline

```
Mục tiêu: Xem tác giả có "creative override" layer boundary không,
và nếu có thì theo pattern nào.

QUERY UA: get_domain_overview()
  → Liệt kê tất cả layer

FOR EACH layer pair (A calls B):
  CALL: get_relationships(layer_A_nodes) filtered to layer_B
  ANALYZE:
    - Có layer nào gọi "ngược chiều" (controller → domain trực tiếp bỏ qua service)?
    - Có class nào bridge 2 layer theo cách không conventional?
    - Có abstract layer nào được inject vào layer không expected?

  Nếu phát hiện "override":
    GET: get_node_source(bridge_class)
    NOTE: "Đây là creative override hay anti-pattern?" → để nguyên, không kết luận
```

#### 1E. Code Duplication vs Abstraction Tendency

```
QUERY Socraticode: codebase_context_search("common logic abstraction helper util")
  → Xem tác giả có xu hướng extract common logic không

QUERY UA: query_nodes(type="class", filter="name contains 'Helper' OR 'Util' OR 'Common'")
  → Đếm helper/util class
  → Nếu ít: tác giả prefer đặt common logic ở chỗ khác (Base class? Interface default? Composition?)

QUERY UA: query_nodes(type="class", filter="extends Base*")
  → Base class abstraction có nhiều không?
  → Inheritance depth trung bình
```

---

### GIAI ĐOẠN 2: Hypothesis Generation

Từ evidence Giai đoạn 1, agent tạo **danh sách hypothesis có cấu trúc**.

**Mỗi hypothesis phải có:**
- `id`: HP-{n}
- `claim`: Phát biểu cụ thể về style/philosophy
- `confidence`: HIGH | MEDIUM | LOW (dựa trên số lượng và tính nhất quán của evidence)
- `evidence_summary`: 2-3 dòng data cụ thể từ code
- `exemplar`: Node_id hoặc file path của ví dụ rõ nhất
- `counter_evidence`: Những nơi KHÔNG follow pattern này (nếu có)
- `question_for_author`: Câu hỏi cụ thể để confirm

**Ví dụ hypothesis output:**

```
HP-1 [HIGH confidence]
Claim: "Tác giả áp dụng nguyên tắc zero-nested-if nhất quán"
Evidence:
  - 87% method trong codebase có nesting depth = 0
  - Average nesting depth: 0.3 (rất thấp)
  - 23 method có early return pattern
  - Chỉ 3 method có if lồng — đều trong legacy package
Exemplar: <ClassNameProcessor>.validate() [node_id: xxx]
Counter-evidence: <LegacyService>.processRequest() — legacy, chưa refactor
Question: "Em thấy hầu hết code không có if lồng, và những nơi có thì đều trong
           legacy package. Đây có phải nguyên tắc anh áp dụng nhất quán không?
           Hay có ngoại lệ nào không phải legacy mà vẫn OK?"

HP-2 [HIGH confidence]
Claim: "Tác giả ưu tiên Chain of Responsibility thay vì if/else dispatch"
Evidence:
  - {n} Processor class implement cùng interface, không có if dispatch
  - 0 switch statement trong service layer
  - Factory classes: {n}/{n} không dùng if/switch để chọn implementation
Exemplar: <ExemplarProcessor> [node_id: yyy]
Counter-evidence: (không có)
Question: "Đây có phải pattern anh intentionally chọn cho mọi dispatch logic,
           hay chỉ áp dụng cho validation flow?"

HP-3 [MEDIUM confidence]
Claim: "Tác giả prefer composition over inheritance"
Evidence:
  - Inheritance depth average: 1.2 (chủ yếu chỉ extend BaseEntity/BaseRepository)
  - 0 class extend business class (chỉ extend infra base class)
  - Nhiều interface injection hơn abstract class
Counter-evidence: <AbstractXxxProcessor> (1 case)
Question: "Em thấy hầu hết không dùng inheritance cho business logic.
           <AbstractXxxProcessor> là exception hay có pattern riêng?"
```

> **Lưu ý**: Các placeholder `<ClassName>` sẽ được thay bằng tên thực tế
> từ kết quả scan ở Giai đoạn 1. Agent KHÔNG được bịa tên class.

---

### GIAI ĐOẠN 3: Interview Protocol

Agent trình bày hypothesis và hỏi theo cấu trúc sau:

```
"Em đã đọc toàn bộ codebase và có {n} hypothesis về coding style của anh.
Em sẽ trình bày từng hypothesis với evidence thực tế — anh confirm, reject,
hoặc làm rõ thêm.

Với mỗi hypothesis:
  [C] Confirm — đúng, encode vào DNA
  [R] Reject — sai hoặc chỉ tình cờ
  [P] Partially — đúng nhưng có điều kiện/ngoại lệ (anh mô tả thêm)
  [E] Expand — đúng, và còn nhiều hơn thế (anh muốn thêm)

Bắt đầu với hypothesis có confidence cao nhất:"
```

**Sau mỗi response của author:**

```
IF [C]: Ghi confirmed: true, lưu lý giải ngắn nếu author cung cấp
IF [R]: Ghi confirmed: false, lưu lý do reject để không re-infer sau này
IF [P]: Ghi confirmed: partial, lưu điều kiện/ngoại lệ, tạo sub-rule
IF [E]: Ghi confirmed: true, mở interview question mới để capture phần mở rộng
```

**Sau tất cả hypothesis từ code, agent hỏi thêm:**

```
"Ngoài những pattern em phát hiện được từ code, anh có nguyên tắc nào
trong đầu mà chưa thể hiện rõ trong codebase hiện tại không?
(Ví dụ: nguyên tắc anh muốn áp dụng nhưng codebase cũ chưa được refactor)"
```

→ Đây là nơi capture **philosophy chưa được code hóa** — quan trọng nhất.

---

### GIAI ĐOẠN 4: Encode → author-dna.yaml

**[PRE-PLACEMENT CHECKS — bắt buộc trước khi ghi entry bất kỳ]**

### Check 1 — Cross-check conventions.yaml (Gap 1)

Trước khi tạo SP/PP entry mới, scan conventions.yaml:
- Tìm kiếm tên tương đương trong Section 8 (Coding Philosophy) và Section 1 (Naming).
- Nếu tìm thấy entry tương tự với ≥70% overlap về nội dung:
  → Không tạo SP/PP mới.
  → Ghi note vào phiên: "Teaching moment đã cover bởi {CP-XX} trong conventions.yaml."
  → Chỉ tạo nếu author-dna cần capture WHY/HOW mà conventions chưa có.

### Check 2 — R-DNA-7 Step 0: Phân tách abstraction level (Gap 2)

Trước khi place entry, test:
```
1. Bỏ tên cụ thể (table, class, method, column) → bài học còn đúng?
   CÓ  → author-dna (WHY/HOW)
   KHÔNG → tiếp

2. Về naming/structure/organization?
   CÓ  → conventions.yaml (WHAT)
   KHÔNG → tiếp

3. Về kiến trúc/component/relationship cụ thể?
   CÓ  → knowledge-snapshot.md (WHAT IS)
```
Dấu hiệu ghi SAI level: entry author-dna phải liệt kê tên bảng/cột → đang ghi nhầm chỗ.

### Check 3 — Deep confirmation (Gap 3)

Confirmation với tác giả phải validate 3 chiều, không chỉ "pattern có đúng không?":

```
Q1 (scope):    "Pattern này áp dụng ở đâu — toàn bộ codebase hay chỉ transaction module?"
Q2 (intent):   "Đây là rule bắt buộc hay lựa chọn thiết kế tuỳ context?"
Q3 (enforcement): "Nếu agent thấy vi phạm, phản ứng thế nào?
                   REJECT_AND_PROPOSE / FLAG_AND_WARN / SUGGEST?"
```

Không được ghi `REJECT_AND_PROPOSE` trừ khi author xác nhận rõ ràng "bắt buộc, không có ngoại lệ".
Default enforcement nếu không hỏi: `FLAG_AND_WARN`.

---

Sau interview, agent tổng hợp thành file:

```
GENERATE: .knowledge-layer/templates/author-dna.draft.yaml

FOR EACH confirmed hypothesis:
  → Encode vào section phù hợp (hard_principles / style_preferences / creative_overrides)
  → Gắn exemplar node_id thực tế từ evidence scan
  → Ghi confirmed: true + source: "codebase-inferred + author-confirmed"

FOR EACH author-added principle (từ open-ended question):
  → Encode với source: "author-described"
  → exemplar: null (chưa có trong code hiện tại)
  → agent_note: "Chưa có evidence trong code — cần tìm khi gặp task liên quan"

FOR EACH rejected hypothesis:
  → Ghi vào section rejected_hypotheses (để không re-infer)

META:
  - interview_date
  - hypotheses_proposed / confirmed / rejected / partial
  - principles_author_added (số principle author bổ sung ngoài code)
```

**Sau khi sinh draft:**

```
"author-dna.draft.yaml đã được tạo tại .knowledge-layer/templates/.
Anh mở file, đọc lại toàn bộ — chỉnh trực tiếp nếu cần.
Khi sẵn sàng: /approve-dna để commit chính thức."
```

---

## 4. /approve-dna Workflow

```
1. VALIDATE author-dna.draft.yaml:
   - YAML hợp lệ?
   - Có ít nhất 1 hard_principle được confirmed?
   - Tất cả exemplar node_id còn tồn tại trong UA graph?
     IF node_id không tồn tại: WARN, không block

2. CHECK conflict với conventions.yaml:
   - Nếu author-dna có principle mâu thuẫn với convention
     (ví dụ: DNA nói "không dùng X" nhưng conventions.yaml liệt kê X là pattern)
   → LIST conflicts, hỏi author resolve

3. PROMOTE:
   - Rename: author-dna.draft.yaml → author-dna.yaml
   - Update: meta.status = approved, meta.approved_at = timestamp
   - Backup: author-dna.draft.{timestamp}.yaml.bak

4. UPDATE AGENT_TRANSPARENCY:
   "[x] /approve-dna: author-dna.yaml committed
    - Hard principles: {n}
    - Style preferences: {n}
    - Creative overrides: {n}
    - Rejected hypotheses logged: {n}
    - Source: {n} codebase-inferred + {n} author-described"

5. NOTIFY:
   "✅ author-dna.yaml committed. Agent sẽ dùng coding DNA của anh
    như judgment layer từ phiên tiếp theo.

    Quan trọng: Khi agent đề xuất solution vi phạm hard principle,
    agent sẽ tự flag và propose alternative trước khi anh phải nói."
```

---

## 5. Cách Agent Dùng author-dna.yaml

### 5A. Pha 2 — Sinh spec

```
TRƯỚC khi propose bất kỳ solution nào:
  READ: author-dna.yaml → hard_principles
  FOR EACH hard_principle:
    IF solution_draft vi phạm principle:
      → KHÔNG đưa ra solution đó
      → Tự refactor sang approach align với DNA
      → Ghi note trong spec: "Approach X được chọn thay Y vì HP-{id}"

  READ: creative_overrides
  IF task input (Confluence/wiki) mô tả if/else flow:
    → FLAG: "Tài liệu mô tả if/else, em propose structure-based alternative"
    → Show cả 2: original if/else approach + DNA-aligned approach
    → Để author quyết định
```

### 5B. Pha 3 — Apply/Review

```
Khi review code change (từ /opsx:apply hoặc PR review):
  SCAN change diff cho:
    - Nested if depth > max_nesting_depth: FLAG HP-{id}
    - Switch statement mới: FLAG HP-{id} nếu có pattern alternative
    - instanceof check mới: FLAG — suggest polymorphism
    - Method complexity > threshold: FLAG HP-{id}

  FORMAT flag:
    "⚠️ DNA-ALERT [HP-{id}]: Đoạn này dùng if/else dispatch cho {n} case.
     Theo style của anh, đây là ứng viên tốt cho Strategy/Factory pattern.
     Muốn em propose refactor không?"
```

### 5C. Architecture Review

```
Khi architecture-reviewer đánh giá design:
  READ: author-dna.yaml → hard_principles + creative_overrides
  FOR EACH proposed component/layer:
    CHECK: Design này có align với DNA không?
    IF không align:
      → WARN trong EXPLORE_CONTEXT: "Design X có thể không align với HP-{id}"
      → Suggest DNA-aligned alternative
      → Không BLOCK (chỉ WARN) vì architecture decision phức tạp hơn code-level
```

### 5D. Khi không có author-dna.yaml

```
IF author-dna.yaml không tồn tại HOẶC status != approved:
  → Agent dùng conventions.yaml (naming only)
  → Không có judgment layer cho code style
  → WARN trong bootstrap report: "author-dna.yaml chưa có. Agent dùng generic
    code style. Chạy /dna-scan để tạo coding DNA."
```

---

## 6. Re-scan & Update Protocol

### Khi cần update DNA

```
Trigger: User cảm thấy agent đang flag sai, hoặc có principle mới

Mode:
  [A] Add principle: Thêm principle mới, không re-scan toàn bộ
      → Agent hỏi: principle gì, có exemplar trong code không?
      → Append vào author-dna.yaml trực tiếp
      → Không cần /approve-dna lại (chỉ cần user confirm trong chat)

  [U] Update existing: Sửa principle đã có (thêm ngoại lệ, làm rõ scope)
      → Edit trực tiếp trong file
      → Chạy /approve-dna để validate lại

  [R] Full rescan: Sau kiến trúc thay đổi lớn
      → Chạy lại toàn bộ /dna-scan
      → Previous DNA được archive, không xoá
```

### Rejected hypothesis log

```
Trong author-dna.yaml, section rejected_hypotheses giúp agent
KHÔNG re-infer lại cùng sai lầm trong tương lai:

rejected_hypotheses:
  - id: HP-{n}-rejected
    original_claim: "<claim bị tác giả bác bỏ>"
    rejection_reason: "<lý do từ tác giả>"
    logged_at: "<timestamp>"
```

---

## 7. AGENT_TRANSPARENCY

```
[x] author-dna-builder: /dna-scan
  - Giai đoạn 1 (scan): {n} method analyzed, {n} pattern found
  - Giai đoạn 2 (hypothesis): {n} hypotheses generated
    ({n} HIGH, {n} MEDIUM, {n} LOW confidence)
  - Giai đoạn 3 (interview): {n} confirmed, {n} rejected, {n} partial
  - Giai đoạn 4 (encode): author-dna.draft.yaml generated
  - Status: awaiting /approve-dna
```

---

## [L5] Periodic Re-Validation Trigger

### Mục đích

`author-dna.yaml` có thể bị stale khi codebase thay đổi lớn (refactor, kiến trúc mới).
L5 định nghĩa điều kiện để **tự động gợi ý** re-validation với tác giả.

### Điều kiện trigger re-validation

```
FUNCTION should_revalidate_dna():
  Đọc author-dna.yaml metadata: last_validated_at, last_scan_commit

  TRIGGER nếu BẤT KỲ điều kiện sau đúng:
  1. Thời gian: today - last_validated_at > 90 ngày
  2. Scope thay đổi: có ít nhất 2 task loại refactor hoàn thành kể từ last_validated_at
     (kiểm tra archive/ ARCHIVE_META: status=completed, task_type=refactor)
  3. Manual: user chạy `/dna-scan` trực tiếp

  KHÔNG trigger nếu:
  - author-dna.yaml có status: draft (chưa approved lần đầu)
  - Đang ở giữa Pha 2 hoặc Pha 3 của task
```

### Re-validation Workflow

```
FUNCTION trigger_dna_revalidation():
  1. Ghi vào AGENT_TRANSPARENCY:
     "[L5-DNA-REVALIDATE] author-dna.yaml có thể stale.
      Lý do: {time/refactor/manual}. Last validated: {last_validated_at}."
  2. Thông báo user (non-blocking):
     "author-dna.yaml chưa được validate {n} ngày/sau {n} refactor.
      Muốn chạy lại /dna-scan để cập nhật? (Không bắt buộc)"
  3. Nếu user đồng ý: chạy author-dna-builder với mode "re-validate"
  4. Nếu user từ chối: đánh dấu author-dna.yaml với note:
     re_validation_declined_at: {today}
     → Không hỏi lại trong 30 ngày

RE-VALIDATE mode:
  - Scan codebase để tìm pattern thay đổi (tương tự hybrid mode hiện tại).
  - Không xoá entries đã confirmed: true — chỉ hỏi về entries có thể đã thay đổi.
  - So sánh code patterns mới vs confirmed entries → highlight gaps.
  - Interview lại tác giả chỉ về những gap này (không phỏng vấn lại từ đầu).
```

### Ghi vào knowledge-curator

Khi bootstrap phát hiện trigger condition:
- knowledge-curator PHẢI gợi ý re-validation trong lúc `archive_active_context` (sau task refactor hoàn thành).
- Ghi vào ARCHIVE_META.md: `dna_revalidation_suggested: true`
