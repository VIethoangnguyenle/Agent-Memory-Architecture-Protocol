# Knowledge Snapshot — Kiến trúc Hệ thống
> Cập nhật lần cuối: 2026-06-04
> Cập nhật bởi: brainstorm-daily-trans-req-limit

Đây là **source of truth kiến trúc tổng thể** của hệ thống.
Được tích luỹ bởi `knowledge-curator` sau mỗi task hoàn thành.

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

- **Tên hệ thống**: Vietbank SME Omni
- **Stack chính**: Java 17 / Spring Boot 3.x
- **Database**: Oracle (primary, JPA), MongoDB (auxiliary, module_mongo)
- **Message Queue**: Kafka (BO trigger, inter-service events)
- **Auth**: JWT
- **Cache**: Redis (distributed), Caffeine (local in-memory)

---

## Tầng Database

### Bảng/Collection chính

| Tên | Loại | Mô tả ngắn | Metadata |
|-----|------|-----------|----------|
| `OMNI_DAILY_TRANS_REQ_LIMIT` | TABLE (planned) | HM lập lệnh/ngày tùy chỉnh theo DN, serviceType, ccy | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |
| `AD_PACKAGE_SERVICE_TYPE_LIMIT` | TABLE | HM gói mặc định theo serviceType — bao gồm `dailyCusTransReqAmountLimit` | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |
| `OMNI_CUS_TRANS_REQ_CHECK` | TABLE | Tracking accumulated amount lập lệnh/ngày (virtual limit tracking) | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |

### Constraint & Trigger quan trọng

| Tên | Loại | Mô tả | Metadata |
|-----|------|-------|----------|
| `UQ_DAILY_TRANS_REQ_LIMIT` | UNIQUE | `(COMPANY_ID, SERVICE_TYPE_CODE, CCY)` trên `OMNI_DAILY_TRANS_REQ_LIMIT` | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |

---

## Kiến trúc Code

> **Quy tắc Factory** (boundary, base class, API): xem `conventions.yaml` → Section 3 `design_patterns` → "Factory Design Boundary".
> **Quy tắc đặt tên DB** (table prefix, audit columns): xem `conventions.yaml` → Section 1 `database_naming`.
> Snapshot này chỉ ghi **sự thật** — module nào tồn tại, gọi gì, ở đâu.

### Module/Service chính

| Module | Package/Path | Vai trò | Metadata |
|--------|-------------|---------|----------|
| `ValidateTransactionLimitProcessor` | `transaction.business.financial.module.action.init.processor` | Validate TẤT CẢ hạn mức khi Init (Maker tạo lệnh): HM gói, HM lập lệnh, HM giao dịch | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |
| `PackageServiceTypeLimitFactory` | `transaction.data.module.package_limit.factory.impl` | Read-only cache factory cho `AD_PACKAGE_SERVICE_TYPE_LIMIT` (BaseCrudLocalCacheFactory) | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |
| `CusTransReqCheckFactory` | `transaction.business.financial.module.trans_check.factory.impl` | Write-capable factory cho tracking accumulated amount (BaseCrudDataFactory) | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |
| `DailyTransReqLimitFactory` | `transaction.data.module.daily_trans_req_limit.factory.impl` | Config limit per company, extends BaseCrudLocalCacheFactory | `source:incident-limitadjustment-2026-06-08` `seen:2026-06` `verified:2026-06` `status:active` |
| `transaction` module | Toàn bộ `transaction.*` modules | Chứa các pattern factory, handler, executor, validation chain cho giao dịch tài chính | `source:incident-limitadjustment-2026-06-08` `seen:2026-06` `verified:2026-06` `status:active` |
| `DistributedLockService` | `rle_service.module.transaction.common` | Redis-backed distributed locking cho race condition (key: `rle:lock:limit:{accountNo}`) | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |

### Entry Points quan trọng

| Endpoint/Handler | Class | Mô tả | Metadata |
|-----------------|-------|-------|----------|
| Init Financial TransReq | `BaseInitFinancialTransReqHandler` | Maker tạo lệnh giao dịch tài chính → chain: validate → persist | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |
| Init Nonfinancial TransReq | `BaseInitNonfinancialTransReqHandler` | Maker tạo lệnh phi tài chính (limit setting, etc.) | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |
| NonfinancialTransReq — Config-Driven Behavior | `AD_SERVICE.IS_APPROVAL` + `OMNI_NONFINANCIAL_WORKFLOW_STAGE` | Approval flow config: IS_APPROVAL=true→NONFINANCIAL_APPROVED (Phase=INIT_REQUEST); IS_APPROVAL=false→NONFINANCIAL_UNAPPROVED (Phase=INIT_UNAPPROVED_TRANSACTION). PTXT config: IS_APPROVAL=true→lấy từ METHODS của stage có IS_INITIALIZED=true; IS_APPROVAL=false→lấy từ Customer.methods. Base xử lý: dòng 228 (setNeedApproved), dòng 253 (authMethodModels). | `source:teaching-moment-hp9-2026-06-10` `seen:2026-06` `verified:2026-06` `status:active` |

### Validation Chain — Base Transaction Framework

> **Fact kiến trúc**: Base giao dịch (`BaseInitFinancialTransReqHandler`, `BaseInitNonfinancialTransReqHandler`)
> đã wire sẵn `buildValidationProcessorChain().process(request)` trong `preHandle()`.
> Handler kế thừa base **phải** override `buildValidationProcessorChain()` để compose danh sách processors.
> Đây là constraint kiến trúc của framework, không phải rule tổng quát cho toàn bộ codebase.
> Triết lý đằng sau: xem `author-dna.yaml` HP-1.
> `source:teaching-moment-hp1-2026-06-11` `seen:2026-06` `verified:2026-06` `status:active`

### Validation Chain — Init Financial Transaction

```
BaseInitFinancialTransReqHandler.process()
  → ValidateTransactionLimitProcessor  ← CHECK HẠN MỨC TẠI ĐÂY
    → validatePackageServiceTypeLimit()
      → 1. iDailyTransReqLimitFactory.getModelOrNull(id)  ← HM tùy chỉnh DN
      → 2. Fallback: packageServiceTypeLimitModel.getDailyCusTransReqAmountLimit()  ← HM gói
      → 3. Compare: accumulated + amount > effectiveLimit → throw
    → validatePackageServiceLimit()
      → min/max amount per transaction
  → ValidateFinalApproveFinancialTransactionLimitHandler  ← Virtual limit (race condition)
```

---

## Business Rules Đã Xác Nhận

| Rule | Mô tả | Metadata |
|------|-------|----------|
| BR-LIM-001 | Hạn mức lập lệnh = HM tối đa DN được lập lệnh trong ngày theo serviceType. Nếu DN có HM tùy chỉnh → dùng. Nếu không → fallback về HM gói | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |
| BR-LIM-002 | Race condition chống bằng 3 lớp: Redis Lock (DistributedLockService) → Virtual Limit (increaseVirtualLimit) → Oracle Trigger | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |
| BR-LIM-003 | Khi BO thay đổi gói DN → Kafka event → cleanup HM tùy chỉnh (delete `OMNI_DAILY_TRANS_REQ_LIMIT` records) | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |
| BR-NF-001 | Cài đặt HM lập lệnh = lệnh phi tài chính, đi qua luồng Nonfinancial Maker-Checker trên auth-service | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |
| BR-AUTH-001 | Maker-Checker Separation: Phase Init tuyệt đối KHÔNG mutate state (vd đổi status User). Giữ state ban đầu để không gián đoạn dịch vụ. Chỉ mutate state ở phase ConfirmExecutor. | `source:USER-STATUS-REFACTOR` `seen:2026-06` `verified:2026-06` `status:active` |

---

## Integration & External Systems

| Hệ thống | Loại | Giao thức | Ghi chú | Metadata |
|---------|------|-----------|---------|----------|
| BO (Back Office) | upstream | Kafka | Trigger thay đổi gói, service type, trạng thái DN | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |
| VBG Gateway | downstream | gRPC/REST | Core banking gateway | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |

---

## Non-functional Notes

| Aspect | Mô tả | Metadata |
|--------|-------|----------|
| Caching — LocalCache | `BaseCrudLocalCacheFactory`: Caffeine (in-memory) + Redis. Config TTL qua `evictionSpec()` | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |
| Caching — DataFactory | `BaseCrudDataFactory`: Redis only | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |
| Distributed Lock | Redis-backed via `DistributedLockService`. Key pattern: `rle:lock:limit:{accountNo}` | `source:brainstorm-daily-trans-req-limit` `seen:2026-06` `verified:2026-06` `status:active` |

---

## Cross-reference Index

> Snapshot chỉ chứa sự thật. Khi cần quy tắc hoặc triết lý → xem đúng store tương ứng.

| Topic | Quy tắc → conventions.yaml | Triết lý → author-dna.yaml |
|-------|---------------------------|---------------------------|
| Factory boundary & base class | `design_patterns` → "Factory Design Boundary" + `api_methods` | HP-5 (Factory = cache config only) |
| Handler / Executor pattern | `naming_rules` → Handler/Executor suffix | HP-2 (Template Method), HP-3 (Strategy) |
| Validation chain | — | HP-1 (Chain of Responsibility — need-driven) |
| Database naming | `database_naming` (table prefix, audit columns, PK, CREATED_BY) | — |
| Error handling | `upstream_constraints` + `coding_philosophy` CP-03/04/06/07 | — |
| Code style / nesting | `coding_philosophy` CP-04 | HP-6 (Zero Nesting), HP-7 (No Else) |
| Caching strategy | — (sự thật ở snapshot "Non-functional Notes") | HP-5 |
| Post-processing / events | — (sự thật ở snapshot "Entry Points") | PP-4 (Spring Event) |

---

## Lịch sử cập nhật

| Ticket | Ngày | Hành động | Entries thêm | Entries updated |
|--------|------|-----------|-------------|----------------|
| `brainstorm-daily-trans-req-limit` | 2026-06-04 | Initial snapshot từ brainstorm session | 20+ | 0 |
| `incident-limitadjustment-2026-06-08` | 2026-06-09 | Corrective action: thêm DailyTransReqLimitFactory gold standard, transaction module gold standard, factory base class decision tree | 4 | 0 |
| `teaching-moment-hp1-2026-06-11` | 2026-06-11 | HP-1 clarification: need-driven. Removed SP-6/7/8/9 duplicates (→ CP-03/04/05/10). Thêm Base Transaction Framework fact | 1 | 4 (cross-refs + HP-1) |
| `knowledge-store-cleanup` | 2026-06-15 | Tách đúng vai trò: xóa 10 entries quy tắc/triết lý khỏi snapshot (Factory rules → conventions, HP-1 ref → DNA, DB naming → conventions). Thêm `database_naming` vào conventions.yaml | 0 | 10 (xóa/chuyển) |
| `USER-STATUS-REFACTOR` | 2026-06-16 | Corrective action: Loại bỏ state mutation ở Validation, cập nhật Maker-Checker boundaries. | 1 | 0 |

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
| LLM Default Bias: Bỏ qua tiện ích framework (getModelOrNull, StringUtils), tự viết try/catch rườm rà. | `conventions.yaml` / `author-dna.yaml` | 2 | USER-STATUS-REFACTOR | USER-STATUS-REFACTOR | MEDIUM |
| LLM Default Bias: Tự động sinh Javadoc cho private method, import FQN. | `author-dna.yaml` (Zero-waste) | 2 | USER-STATUS-REFACTOR | USER-STATUS-REFACTOR | MEDIUM |

**Severity levels**: LOW (cosmetic), MEDIUM (workflow issue), HIGH (data integrity risk), CRITICAL (security/data loss)

### Violation Trend

- Tổng số violation đã ghi nhận: 2
- Violation phổ biến nhất: Bỏ qua Author DNA / LLM Default Bias
- Cần xem xét cải thiện rule: Thêm bước "DNA Filtering" bắt buộc trước mọi lệnh output code.

### Quy tắc cập nhật

- Chỉ ghi pattern **đã xảy ra ≥ 2 lần** (không ghi one-off).
- Khi cùng pattern xảy ra lần mới: tăng "Lần xảy ra" và cập nhật "Task gần nhất".
- Không ghi tên user vào đây — chỉ ghi pattern hành vi.
- Định kỳ review: khi có ≥ 5 pattern → xem xét bổ sung rule mới vào RULES.md.
