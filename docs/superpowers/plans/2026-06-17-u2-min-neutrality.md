# U2-min Framework Neutrality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Làm repo framework AMAP trung lập hoàn toàn — loại bỏ sạch nội dung Vietbank, chốt policy file-ownership, và thêm một worked example author-dna (SOLID/Clean Code/Design Patterns).

**Architecture:** Phần lớn là thao tác file + git (skeletonize, xoá, untrack, gitignore) + 2 file tài liệu mới. Không có code runtime mới; "test" của mỗi task là lệnh verify (grep / git / yaml-parse) chạy trước (fail) và sau (pass).

**Tech Stack:** Markdown, YAML, git, grep, Python (chỉ để `yaml.safe_load` verify).

**Spec:** [docs/superpowers/specs/2026-06-17-u2-min-neutrality-design.md](../specs/2026-06-17-u2-min-neutrality-design.md)
**Parent roadmap:** [docs/superpowers/specs/2026-06-17-upgrade-roadmap-design.md](../specs/2026-06-17-upgrade-roadmap-design.md)

---

## File Structure

| File | Trách nhiệm | Hành động |
|---|---|---|
| `.knowledge-layer/long-term/knowledge-snapshot.md` | Skeleton snapshot (framework guidance + cấu trúc section, 0 nội dung business) | Modify (rewrite) |
| `.knowledge-layer/long-term/author-dna.draft.yaml` | (vô nghĩa) | Delete |
| `.knowledge-layer/long-term/persona.yaml` | Per-dev, không track | Untrack + gitignore |
| `.gitignore` | Thêm `persona.yaml` | Modify |
| `docs/examples/author-dna-cleancode.yaml` | Worked example author-dna (SOLID/Clean Code/Design Patterns) | Create |
| `docs/amap-file-ownership-policy.md` | Hợp đồng phân loại sở hữu file (cho U3) | Create |
| `README.md` | Pointer tới worked example | Modify (1 dòng) |

**Verify-only (không sửa):** `author-dna.yaml`, `conventions.yaml` đã trung lập → chỉ kiểm ở Task 7.

---

### Task 1: Skeletonize `knowledge-snapshot.md` (loại bỏ Vietbank hoàn toàn)

**Files:**
- Modify: `.knowledge-layer/long-term/knowledge-snapshot.md`

- [ ] **Step 1: Verify nội dung Vietbank đang tồn tại (test phải FAIL)**

Run:
```bash
grep -ciE "vietbank|OMNI_|SME|teller|BR-LIM|DistributedLockService" .knowledge-layer/long-term/knowledge-snapshot.md
```
Expected: số > 0 (hiện đang có nội dung Vietbank).

- [ ] **Step 2: Ghi đè file bằng skeleton sau (toàn bộ nội dung file mới)**

Ghi `.knowledge-layer/long-term/knowledge-snapshot.md` thành đúng nội dung:

```markdown
# Knowledge Snapshot — Kiến trúc Hệ thống
> Cập nhật lần cuối: —
> Cập nhật bởi: —

Đây là **source of truth kiến trúc tổng thể** của hệ thống.
Được tích luỹ bởi `knowledge-curator` sau mỗi task hoàn thành.

> ⓘ **Đây là skeleton.** Khi `amap init` vào dự án của bạn, file này được seed rỗng;
> `knowledge-curator` điền dần sau mỗi task. Điền các bảng dưới theo đúng format metadata.
> Xem ví dụ author-dna đã điền đầy ở `docs/examples/author-dna-cleancode.yaml`.

---

## Quy ước Metadata Bắt buộc

Mọi entry trong file này đều phải có metadata inline theo format:

```
| Tên entry | ... | `source:{ticket-id hoặc doc-url}` `seen:{YYYY-MM}` `verified:{YYYY-MM}` `status:{active|outdated|superseded}` |
```

**Giải thích field:**

| Field | Ý nghĩa | Ai ghi | Cập nhật khi nào |
|-------|---------|--------|-----------------|
| `source` | Ticket-id hoặc URL tài liệu đầu tiên xác nhận thông tin này | knowledge-curator | Lần đầu thêm vào |
| `seen` | Tháng/năm phát hiện lần đầu (`YYYY-MM`) | knowledge-curator | Chỉ ghi một lần |
| `verified` | Tháng/năm xác nhận gần nhất còn đúng (`YYYY-MM`) | knowledge-curator | Cập nhật mỗi khi task chạm vào entry này và confirm còn đúng |
| `status` | Trạng thái hiện tại của tri thức này | knowledge-curator | Cập nhật khi có thay đổi |

**Quy tắc status:**

- `active` — Đang đúng, đã verified trong vòng 90 ngày hoặc chưa có lý do tin là thay đổi.
- `outdated` — Có dấu hiệu không còn đúng (ticket mới mâu thuẫn, refactor lớn) nhưng chưa xác nhận thay thế. Agent đọc với độ tin cậy **THẤP**.
- `superseded` — Đã được thay thế bởi entry mới hơn. Giữ để audit trail, **không dùng cho reasoning**.

**Quy tắc agent khi đọc:**
- Chỉ dùng entry `status:active` cho reasoning và spec.
- Entry `status:outdated` → phải ghi cảnh báo vào AGENT_TRANSPARENCY trước khi dùng.
- Entry `status:superseded` → bỏ qua hoàn toàn, chỉ đọc khi cần trace lịch sử.

---

## Tổng quan Hệ thống

<!-- Điền khi khám phá hệ thống: -->
- **Tên hệ thống**: <!-- vd: Acme Orders Service -->
- **Stack chính**: <!-- vd: ngôn ngữ / framework -->
- **Database**: <!-- vd: Postgres -->
- **Message Queue**: <!-- nếu có -->
- **Auth**: <!-- vd: JWT -->
- **Cache**: <!-- nếu có -->

---

## Tầng Database

### Bảng/Collection chính

| Tên | Loại | Mô tả ngắn | Metadata |
|-----|------|-----------|----------|
<!-- ví dụ: | `ORDERS` | TABLE | đơn hàng | `source:TICKET-1` `seen:2026-06` `verified:2026-06` `status:active` | -->

### Constraint & Trigger quan trọng

| Tên | Loại | Mô tả | Metadata |
|-----|------|-------|----------|
<!-- ví dụ: | `UQ_ORDER_NO` | UNIQUE | `(ORDER_NO)` | `source:TICKET-1` `seen:2026-06` `verified:2026-06` `status:active` | -->

---

## Kiến trúc Code

> Snapshot này chỉ ghi **sự thật** — module nào tồn tại, gọi gì, ở đâu.
> Quy tắc đặt tên/pattern → xem `conventions.yaml`; triết lý → xem `author-dna.yaml`.

### Module/Service chính

| Module | Package/Path | Vai trò | Metadata |
|--------|-------------|---------|----------|
<!-- ví dụ: | `OrderService` | `com.acme.order` | xử lý vòng đời đơn | `source:TICKET-1` `seen:2026-06` `verified:2026-06` `status:active` | -->

### Entry Points quan trọng

| Endpoint/Handler | Class | Mô tả | Metadata |
|-----------------|-------|-------|----------|
<!-- ví dụ: | POST /orders | `OrderController` | tạo đơn | `source:TICKET-1` `seen:2026-06` `verified:2026-06` `status:active` | -->

---

## Business Rules Đã Xác Nhận

| Rule | Mô tả | Metadata |
|------|-------|----------|
<!-- ví dụ: | BR-ORD-001 | đơn không được vượt hạn mức ngày | `source:TICKET-1` `seen:2026-06` `verified:2026-06` `status:active` | -->

---

## Integration & External Systems

| Hệ thống | Loại | Giao thức | Ghi chú | Metadata |
|---------|------|-----------|---------|----------|
<!-- ví dụ: | Payment GW | downstream | REST | thanh toán | `source:TICKET-1` `seen:2026-06` `verified:2026-06` `status:active` | -->

---

## Non-functional Notes

| Aspect | Mô tả | Metadata |
|--------|-------|----------|
<!-- ví dụ: | Caching | Redis TTL 5m | `source:TICKET-1` `seen:2026-06` `verified:2026-06` `status:active` | -->

---

## Cross-reference Index

> Snapshot chỉ chứa sự thật. Khi cần quy tắc hoặc triết lý → xem đúng store tương ứng.

| Topic | Quy tắc → conventions.yaml | Triết lý → author-dna.yaml |
|-------|---------------------------|---------------------------|
<!-- ví dụ: | Naming | `naming` → class_suffixes | — | -->

---

## Lịch sử cập nhật

| Ticket | Ngày | Hành động | Entries thêm | Entries updated |
|--------|------|-----------|-------------|----------------|
<!-- ví dụ: | TICKET-1 | 2026-06 | Initial snapshot | 5 | 0 | -->

---

## Outdated / Superseded Log

> Các entry đã bị đánh dấu `outdated` hoặc `superseded` được liệt kê tóm tắt ở đây để dễ audit.
> Không xoá chúng khỏi các section trên — chỉ cập nhật `status` field.

| Entry | Section | Status | Lý do | Ticket |
|-------|---------|--------|-------|--------|
| <!-- chưa có --> | | | | |

---

## [M3] Violation Pattern Tracking

> Section này được tự động cập nhật bởi `knowledge-curator` sau mỗi task hoàn thành.
> Dùng để nhận diện các vi phạm rule/workflow lặp đi lặp lại để cải thiện hệ thống.

### Bảng Vi phạm Đã Ghi nhận

| Pattern | Rule bị vi phạm | Lần xảy ra | Task đầu tiên | Task gần nhất | Severity |
|---------|----------------|-----------|--------------|--------------|----------|
| <!-- chưa có --> | | | | | |

**Severity levels**: LOW (cosmetic), MEDIUM (workflow issue), HIGH (data integrity risk), CRITICAL (security/data loss)

### Quy tắc cập nhật

- Chỉ ghi pattern **đã xảy ra ≥ 2 lần** (không ghi one-off).
- Khi cùng pattern xảy ra lần mới: tăng "Lần xảy ra" và cập nhật "Task gần nhất".
- Không ghi tên user vào đây — chỉ ghi pattern hành vi.
- Định kỳ review: khi có ≥ 5 pattern → xem xét bổ sung rule mới vào RULES.md.
```

- [ ] **Step 3: Verify skeleton sạch (test phải PASS)**

Run:
```bash
grep -ciE "vietbank|OMNI_|SME|teller|BR-LIM|DistributedLockService" .knowledge-layer/long-term/knowledge-snapshot.md
```
Expected: `0`.

- [ ] **Step 4: Verify cấu trúc framework còn nguyên**

Run:
```bash
grep -cE "^## (Quy ước Metadata Bắt buộc|Tầng Database|Business Rules|\[M3\] Violation Pattern Tracking)" .knowledge-layer/long-term/knowledge-snapshot.md
```
Expected: `4` (các section guidance được giữ lại).

- [ ] **Step 5: Commit**

```bash
git add .knowledge-layer/long-term/knowledge-snapshot.md
git commit -m "refactor(neutrality): skeletonize knowledge-snapshot, remove Vietbank arch"
```

---

### Task 2: Xoá `author-dna.draft.yaml`

**Files:**
- Delete: `.knowledge-layer/long-term/author-dna.draft.yaml`

- [ ] **Step 1: Verify file đang được track (test phải cho thấy file tồn tại)**

Run:
```bash
git ls-files .knowledge-layer/long-term/author-dna.draft.yaml
```
Expected: in ra đường dẫn (file đang track).

- [ ] **Step 2: Xoá file khỏi git + đĩa**

```bash
git rm .knowledge-layer/long-term/author-dna.draft.yaml
```

- [ ] **Step 3: Verify đã biến mất (test phải PASS)**

Run:
```bash
git ls-files .knowledge-layer/long-term/author-dna.draft.yaml; test ! -e .knowledge-layer/long-term/author-dna.draft.yaml && echo GONE
```
Expected: không in đường dẫn + in `GONE`.

- [ ] **Step 4: Commit**

```bash
git commit -m "chore(neutrality): remove meaningless author-dna.draft.yaml"
```

---

### Task 3: Untrack `persona.yaml` + thêm vào `.gitignore`

**Files:**
- Modify: `.gitignore`
- Untrack: `.knowledge-layer/long-term/persona.yaml`

- [ ] **Step 1: Verify persona.yaml đang bị track (test phải FAIL = đang track sai)**

Run:
```bash
git ls-files .knowledge-layer/long-term/persona.yaml
```
Expected: in đường dẫn (đang track — đây là cái cần sửa).

- [ ] **Step 2: Thêm dòng vào cuối `.gitignore`**

Thêm vào `.gitignore` (giữ nguyên các dòng cũ, thêm khối này ở cuối):

```gitignore

# Per-dev: persona là phong cách tương tác riêng từng developer (seed từ persona.template.yaml)
.knowledge-layer/long-term/persona.yaml
```

- [ ] **Step 3: Gỡ persona.yaml khỏi index (giữ file trên đĩa)**

```bash
git rm --cached .knowledge-layer/long-term/persona.yaml
```

- [ ] **Step 4: Verify không còn track + đã bị ignore (test phải PASS)**

Run:
```bash
git ls-files .knowledge-layer/long-term/persona.yaml; git check-ignore .knowledge-layer/long-term/persona.yaml; test -e .knowledge-layer/long-term/persona.yaml && echo "ON_DISK"
```
Expected: dòng `git ls-files` rỗng; `git check-ignore` in đường dẫn (đã ignore); in `ON_DISK` (file còn trên đĩa).

- [ ] **Step 5: Verify persona.template.yaml VẪN được track**

Run:
```bash
git ls-files .knowledge-layer/long-term/persona.template.yaml
```
Expected: in đường dẫn (template vẫn track để seed).

- [ ] **Step 6: Commit**

```bash
git add .gitignore
git commit -m "fix(neutrality): untrack persona.yaml + gitignore (per-dev, matches README)"
```

---

### Task 4: Tạo worked example `docs/examples/author-dna-cleancode.yaml`

**Files:**
- Create: `docs/examples/author-dna-cleancode.yaml`

- [ ] **Step 1: Verify file chưa tồn tại (test phải FAIL)**

Run:
```bash
test -e docs/examples/author-dna-cleancode.yaml && echo EXISTS || echo MISSING
```
Expected: `MISSING`.

- [ ] **Step 2: Tạo file với nội dung sau (toàn bộ)**

Ghi `docs/examples/author-dna-cleancode.yaml`:

```yaml
# author-dna.yaml — VÍ DỤ THAM KHẢO (worked example)
# Một author-dna ĐÃ ĐIỀN ĐẦY, mã hoá triết lý code kinh điển:
# SOLID + Clean Code + Design Patterns (GoF).
# Mục đích: cho thấy "skeleton rỗng → khi điền đầy trông thế nào".
# ĐÂY KHÔNG phải DNA của dự án bạn — chạy `/dna-scan` để build DNA thật từ codebase.

version: "1.1"

meta:
  author: "example"
  interview_date: "2026-06-17"
  approved_at: "2026-06-17"
  scanned_by: "author-dna-builder"
  status: approved
  stats: {}
  source_split: {}

# SECTION 1: Hard Principles — agent KHÔNG đề xuất solution vi phạm.
hard_principles:
  HP-1:
    name: "Single Responsibility (SRP)"
    description: >
      Mỗi class/method chỉ có một lý do để thay đổi. Tách concern: business
      logic, persistence, presentation không trộn trong một unit.
    agent_action: REJECT_AND_PROPOSE
    confirmed: true
    source: "Clean Code (R. Martin) · SOLID"
    author_note: "Một unit — một trách nhiệm"
    exemplar:
      node_id: ""
      file_path: ""
      description: "SRP"
    scope: all
    exceptions: []
  HP-2:
    name: "Open/Closed (OCP)"
    description: >
      Mở để mở rộng, đóng để sửa đổi. Thêm hành vi mới bằng cách thêm code
      (Strategy, polymorphism), không sửa code đang chạy ổn định.
    agent_action: REJECT_AND_PROPOSE
    confirmed: true
    source: "SOLID"
    author_note: "Mở rộng không sửa đổi"
    exemplar:
      node_id: ""
      file_path: ""
      description: "OCP"
    scope: all
    exceptions: []
  HP-3:
    name: "Liskov / Interface Segregation / Dependency Inversion"
    description: >
      Subtype thay thế được base (LSP); interface nhỏ chuyên biệt (ISP);
      phụ thuộc abstraction chứ không phụ thuộc concrete (DIP).
    agent_action: REJECT_AND_PROPOSE
    confirmed: true
    source: "SOLID"
    author_note: "L-I-D của SOLID"
    exemplar:
      node_id: ""
      file_path: ""
      description: "LSP/ISP/DIP"
    scope: all
    exceptions: []
  HP-4:
    name: "Clean Code — hàm nhỏ, tên có ý nghĩa"
    description: >
      Hàm ngắn làm một việc; tên biểu đạt ý định; không side-effect ẩn;
      tránh comment thừa bằng cách đặt tên tốt.
    agent_action: REJECT_AND_PROPOSE
    confirmed: true
    source: "Clean Code (R. Martin)"
    author_note: "Code đọc như văn xuôi"
    exemplar:
      node_id: ""
      file_path: ""
      description: "Clean Code"
    scope: all
    exceptions: []

# SECTION 2: Style Preferences (Soft) — ưu tiên, không reject.
style_preferences:
  SP-1:
    name: "Early return thay vì nesting sâu"
    description: "Guard clause + early return để giữ nesting nông."
    confirmed: true

# SECTION 3: Creative Overrides — nơi chủ đích break convention.
creative_overrides: {}

# SECTION 4: Pattern Preferences — design pattern prefer cho từng use case.
pattern_preferences:
  PP-1:
    use_case: "Nhiều thuật toán hoán đổi runtime"
    pattern: "Strategy"
    note: "Đóng gói mỗi thuật toán sau một interface chung (hỗ trợ OCP)."
  PP-2:
    use_case: "Khởi tạo object phức tạp / chọn implementation theo input"
    pattern: "Factory Method / Abstract Factory"
    note: "Tách logic khởi tạo khỏi business logic."
  PP-3:
    use_case: "Khung xử lý cố định, vài bước thay đổi"
    pattern: "Template Method"
    note: "Base định nghĩa skeleton; subclass override bước cụ thể."

# SECTION 5: Complexity Thresholds
complexity_thresholds:
  max_nesting_depth: 2
  max_method_branches: 4
  max_lines_per_method: 40
  early_return_required: true
  confirmed: true

# SECTION 6: Codebase Evidence Summary
codebase_evidence_summary: {}

# SECTION 7: Rejected Hypotheses Log
rejected_hypotheses: {}
```

- [ ] **Step 3: Verify YAML hợp lệ + có cấu trúc đúng (test phải PASS)**

Run:
```bash
.venv/bin/python -c "import yaml,sys; d=yaml.safe_load(open('docs/examples/author-dna-cleancode.yaml')); assert d['version']=='1.1'; assert set(d['hard_principles'])=={'HP-1','HP-2','HP-3','HP-4'}; assert set(d['pattern_preferences'])=={'PP-1','PP-2','PP-3'}; print('OK')"
```
Expected: `OK`.

- [ ] **Step 4: Verify không lẫn nội dung project (test phải PASS)**

Run:
```bash
grep -ciE "vietbank|OMNI_|SME|teller" docs/examples/author-dna-cleancode.yaml
```
Expected: `0`.

- [ ] **Step 5: Commit**

```bash
git add docs/examples/author-dna-cleancode.yaml
git commit -m "docs(examples): add filled-in author-dna example (SOLID/Clean Code/patterns)"
```

---

### Task 5: Tạo policy doc `docs/amap-file-ownership-policy.md`

**Files:**
- Create: `docs/amap-file-ownership-policy.md`

- [ ] **Step 1: Verify chưa tồn tại (test phải FAIL)**

Run:
```bash
test -e docs/amap-file-ownership-policy.md && echo EXISTS || echo MISSING
```
Expected: `MISSING`.

- [ ] **Step 2: Tạo file với nội dung sau (toàn bộ)**

Ghi `docs/amap-file-ownership-policy.md`:

```markdown
# AMAP — File-Ownership Policy

> **Phiên bản:** 1.0 · **Ngày:** 2026-06-17
> **Vai trò:** Hợp đồng phân loại sở hữu file. Các lệnh CLI (`init` / `update` / `migrate`) PHẢI tuân.
> **Người tiêu thụ chính:** U3 (`amap migrate`). Nguồn: U2-min spec.

## 1. Bốn nhóm sở hữu

| Nhóm | `init` | `update` | `migrate` | Gồm |
|---|---|---|---|---|
| **Framework-owned** | render/copy | **re-render/ghi đè** | bỏ qua | `.agent/{rules,skills,workflows,procedures,tools}`, `AGENTS.md`, entry-point file, `.knowledge-layer/templates/`, `docs/` |
| **Seeded-then-user-owned** | seed skeleton 1 lần | **giữ nguyên (không đụng)** | **backfill schema additive** | `.knowledge-layer/long-term/{author-dna.yaml, conventions.yaml, knowledge-snapshot.md}` |
| **Per-dev (gitignored)** | seed từ `*.template` | giữ nguyên | bỏ qua | `persona.yaml`, `.knowledge-layer/active/*` (runtime) |
| **Generated (gitignored)** | tạo | tái sinh | bỏ qua | `rule-projector/generated/*`, `__pycache__`, `resolved-config.yaml` |

## 2. Invariant cứng — Ba file sống

`author-dna.yaml`, `knowledge-snapshot.md`, `conventions.yaml` là **TÀI LIỆU SỐNG, tiến hoá theo thời
gian trong dự án chính** (knowledge-curator cập nhật snapshot sau mỗi task; DNA giàu lên qua teaching
moment R-DNA-7; conventions cập nhật khi rescan).

1. **Bản chất kép.** Trong repo AMAP = skeleton framework-owned. Trong project user = user-owned đang
   tiến hoá. Hai bản decoupled.
2. **Seed một lần** khi `amap init`. Từ đó bản của user tiến hoá độc lập.
3. **`update` TUYỆT ĐỐI KHÔNG ghi đè** ba file này trong project user.
4. **`migrate` chỉ ADDITIVE schema** — thêm field thiếu kèm default, **không bao giờ chạm
   content/giá trị** user/agent đã tích luỹ.
5. **Version stamp tách biệt content:** schema có `version` riêng (vd `version: "1.1"`); migrate so
   version để biết field cần backfill, không suy luận từ content.

> ⚠️ Đây là điểm dễ mất dữ liệu nhất khi nâng version. Policy này là hợp đồng mà U3 phải tuân.
```

- [ ] **Step 3: Verify nội dung chủ chốt có mặt (test phải PASS)**

Run:
```bash
grep -cE "Seeded-then-user-owned|Invariant cứng|ADDITIVE schema" docs/amap-file-ownership-policy.md
```
Expected: `3`.

- [ ] **Step 4: Commit**

```bash
git add docs/amap-file-ownership-policy.md
git commit -m "docs: add AMAP file-ownership policy (contract for amap migrate / U3)"
```

---

### Task 6: Thêm pointer tới worked example trong `README.md`

**Files:**
- Modify: `README.md` (mục "2. Tuỳ chỉnh persona" quanh dòng 174-179)

- [ ] **Step 1: Đọc đoạn cần sửa để lấy anchor chính xác**

Run:
```bash
grep -n "Sửa persona.yaml theo phong cách tương tác mong muốn" README.md
```
Expected: in ra số dòng (vd `179`).

- [ ] **Step 2: Chèn pointer ngay sau khối code persona (sau dòng `# Sửa persona.yaml ...`)**

Thêm đoạn sau ngay dưới khối ``` của mục "2. Tuỳ chỉnh persona":

```markdown

> 💡 Muốn xem một `author-dna.yaml` đã điền đầy trông thế nào? Tham khảo
> [docs/examples/author-dna-cleancode.yaml](docs/examples/author-dna-cleancode.yaml)
> — ví dụ mã hoá SOLID / Clean Code / Design Patterns (chỉ tham khảo, không copy vào dự án).
```

- [ ] **Step 3: Verify pointer có mặt (test phải PASS)**

Run:
```bash
grep -c "docs/examples/author-dna-cleancode.yaml" README.md
```
Expected: `1`.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs(readme): link worked author-dna example"
```

---

### Task 7: Final neutrality verification (Definition of Done gate)

**Files:** none (chỉ verify).

- [ ] **Step 1: Verify 0 nội dung Vietbank trong mọi file framework-owned (test phải PASS)**

Run:
```bash
grep -riE "vietbank|sme omni|OMNI_[A-Z]|teller|jira\.example" \
  .agent .knowledge-layer AGENTS.md README.md docs/examples \
  | grep -viE "docs/superpowers/(specs|plans)" || echo "CLEAN"
```
Expected: `CLEAN` (không match nào ngoài thư mục specs/plans — nơi tên Vietbank chỉ xuất hiện trong văn cảnh lịch sử của chính các spec).

- [ ] **Step 2: Verify ba file sống vẫn là skeleton trung lập**

Run:
```bash
grep -ciE "vietbank|OMNI_|java 17|spring boot|oracle" \
  .knowledge-layer/long-term/author-dna.yaml \
  .knowledge-layer/long-term/conventions.yaml \
  .knowledge-layer/long-term/knowledge-snapshot.md
```
Expected: `0` cho cả ba file (in ra `<file>:0`).

- [ ] **Step 3: Verify git tree đúng (persona untracked, draft xoá, example + policy có)**

Run:
```bash
git ls-files .knowledge-layer/long-term/persona.yaml .knowledge-layer/long-term/author-dna.draft.yaml; \
git ls-files docs/examples/author-dna-cleancode.yaml docs/amap-file-ownership-policy.md
```
Expected: hai dòng đầu rỗng (persona + draft không track); hai file example + policy được in (đã track).

- [ ] **Step 4: (Nếu mọi check PASS) đánh dấu U2-min hoàn tất**

Không cần commit thêm. U2-min Definition of Done đạt → **mở khoá U0** (litmus trên framework sạch).

---

## Self-Review (đã chạy khi viết plan)

- **Spec coverage:** §3.1 long-term cleanup → Task 1,2,3; §3.2 worked example → Task 4 (+pointer Task 6);
  §3.3 policy + §4 invariant → Task 5; §5 Exit criteria → Task 7 (+ rải trong các task). ✅ phủ hết.
- **Placeholder scan:** không có TBD/TODO; mọi file mới có nội dung đầy đủ; mọi verify có lệnh + expected. ✅
- **Type/anchor consistency:** tên file/đường dẫn nhất quán giữa các task và §File Structure; HP-1..HP-4 / PP-1..PP-3 khớp giữa Task 4 nội dung và Step 3 assert. ✅
- **Ghi chú:** README đã sẵn nói persona gitignored (FAQ dòng 319) → không cần sửa câu đó, chỉ thêm pointer ví dụ (Task 6).
