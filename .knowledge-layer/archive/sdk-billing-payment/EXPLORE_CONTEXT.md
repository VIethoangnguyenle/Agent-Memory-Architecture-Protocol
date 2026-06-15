# EXPLORE_CONTEXT — UC-BILL-PAYMENT-002 (Thanh toán SDK)
> Ticket: UC-BILL-PAYMENT-002
> Ngày khảo sát: 2026-06-08
> Nguồn: KG MCP (understand-anything) + DB Explorer (db-remote/VBSMEONL) + grep codebase

---

## 1. Database Schema

### 1.1 AD_BILLING_PARTNER — Đối tác thanh toán

| CODE | NAME | IS_ACTIVE |
|------|------|-----------|
| VNPAY | VNPAY | 1 |
| PAYOO | PAYOO | 1 |

> SDK Payment sử dụng partner **VNPAY**.

### 1.2 AD_PAYMENT_GROUP — Nhóm dịch vụ thanh toán

| CODE | SERVICE_CODE | TYPE | PRIORITY | IS_ACTIVE |
|------|-------------|------|----------|-----------|
| ELECTRIC | 00401 | 0 | 1 | 1 |
| WATER | 00402 | 0 | 2 | 1 |
| **SDK_AIRPLANE** | **01701** | **2** | 3 | 1 |
| **SDK_TRAIN** | **01702** | **2** | 4 | 1 |

> **Phát hiện quan trọng**: TYPE=0 là hóa đơn thường (điện/nước), TYPE=2 là SDK (vé máy bay, tàu hỏa). Cần xác nhận code xử lý phân biệt TYPE.

### 1.3 AD_BILLING_PROVIDER_SERVICE — Nhà cung cấp dịch vụ SDK

| CODE | PROVIDER_CODE | GROUP_CODE | PARTNER_CODE | VI_NAME | IS_ACTIVE |
|------|--------------|------------|--------------|---------|-----------|
| 100005 | 00000030 | SDK_AIRPLANE | VNPAY | Máy Bay | 1 |
| 854901 | 854900 | SDK_TRAIN | VNPAY | Ve Tau Hoa | 1 |

> Data cấu hình SDK đã được seed sẵn trong DB. Không cần backfill.

### 1.4 AD_BILLING_PROVIDER — Nhà cung cấp (cần xác nhận)

> [ASSUMPTION] Chưa kiểm tra bảng AD_BILLING_PROVIDER có record tương ứng với PROVIDER_CODE `00000030` (Máy Bay) và `854900` (Tàu Hỏa) hay chưa. Cần verify trước khi apply.

### 1.5 OMNI_BILLING_TRANS_METADATA — Metadata giao dịch

| Column | Type | Nullable | Comment |
|--------|------|----------|---------|
| ID | NUMBER | N | PK |
| TRANSACTION_ID | NUMBER | N | FK → OMNI_TRANSACTION |
| PARTNER_CODE | VARCHAR2 | Y | Mã đối tác (VNPAY/PAYOO) |
| SERVICE_CODE | VARCHAR2 | Y | Mã dịch vụ (00401, 01701...) |
| PROVIDER_CODE | VARCHAR2 | Y | Mã NCC |
| RECIPIENT_CODE | VARCHAR2 | Y | Mã khách hàng |
| AMOUNT | NUMBER | Y | Số tiền |
| PAYMENT_AMOUNT | NUMBER | Y | Số tiền thanh toán |
| TOTAL_AMOUNT | NUMBER | Y | Tổng tiền |
| PAYMENT_TYPE | VARCHAR2 | Y | Loại thanh toán (FULL/PARTIAL) |
| BILL_DATA | CLOB | Y | JSON data hóa đơn |

> Schema hiện tại đã đủ flexible cho SDK. Các field serviceCode, providerCode, recipientCode reuse được.

### 1.6 AD_BILLING_PROVIDER_SERVICE — Schema chi tiết

| Column | Type | Nullable | Comment |
|--------|------|----------|---------|
| ID | NUMBER | N | PK |
| CODE | VARCHAR2 | N | Mã dịch vụ |
| PARTNER_CODE | VARCHAR2 | N | Mã đối tác |
| PROVIDER_CODE | VARCHAR2 | N | Mã nhà cung cấp |
| VI_NAME | VARCHAR2 | N | Tên dịch vụ (VI) |
| EN_NAME | VARCHAR2 | N | Tên dịch vụ (EN) |
| GROUP_CODE | VARCHAR2 | N | Mã nhóm → AD_PAYMENT_GROUP |
| VI_SERVICE_TITLE | VARCHAR2 | Y | Tiêu đề dịch vụ NCC |
| VI_CUSTOMER_CODE_TITLE | VARCHAR2 | Y | Tiêu đề ô nhập mã KH |
| AUTO_PAYMENT | NUMBER | Y | Cho phép thanh toán tự động |
| DISTRICT_CODE | VARCHAR2 | Y | Mã quận huyện |
| CITY_CODE | VARCHAR2 | Y | Mã tỉnh thành |
| IS_ACTIVE | NUMBER | Y | Trạng thái |
| PROVIDER_ID | NUMBER | N | FK → AD_BILLING_PROVIDER |

---

## 2. Codebase Mapping

### 2.1 Module/Service liên quan

```
payment-service/module/billing/
├── controller/
│   ├── IBillingPaymentController.java        ← Interface: /check-bill, /init
│   ├── AppBillingPaymentController.java      ← App channel
│   └── WebBillingPaymentController.java      ← Web channel
├── handler/
│   ├── InitBillingPaymentHandler.java        ← Khởi tạo GD billing
│   ├── CheckBillHandler.java                 ← Truy vấn hóa đơn
│   └── confirm_executor/
│       ├── BillingPaymentConfirmExecutor.java ← Executor confirm (delegates)
│       ├── BillingPaymentBatchConfirmExecutor.java ← Batch confirm
│       └── delegate/
│           ├── IPaymentConfirmExecutorDelegate.java  ← Interface + revert logic
│           ├── BasePaymentConfirmExecutorDelegate.java ← Base: collectOnBehalf → payment → revert
│           ├── IBillingPaymentConfirmExecutorDelegate.java ← Billing-specific interface
│           └── impl/
│               └── BillingPaymentConfirmExecutorDelegate.java ← Impl: VNPAY + PAYOO routing
├── enumerate/
│   ├── BillingFinancialServiceDefinition.java ← ⚠️ CHỈ CÓ ELECTRIC + WATER
│   ├── BillingError.java                      ← Mã lỗi billing (600000-600007)
│   └── VnpayTrace.java                       ← Counter cho traceNo
├── entity/
│   └── BillingTransMetadataEntity.java        ← Entity → OMNI_BILLING_TRANS_METADATA
├── factory/
│   ├── ICheckBillClientDataFactory.java       ← Cache bill data
│   └── impl/BillingTransMetadataFactory.java  ← Metadata persistence
└── model/
    ├── BillingTransMetadataModel.java         ← Metadata model
    └── BillInfo.java                          ← Bill info + toVnpayBillInfo()

client_gateway/payment-gateway/
├── vnpay/
│   ├── IVnpayBillingClient.java               ← Interface
│   ├── impl/VnpayBillingClient.java           ← Impl: getBill(), payBill()
│   ├── constant/VnpayPaymentConstants.java    ← Error codes, config keys
│   └── model/billing/
│       ├── request/VnpayGetBillRequest.java
│       ├── request/VnpayPayBillRequest.java
│       └── response/VnpayGetBillResponse.java
└── payoo/
    └── IPayooPaymentClient.java               ← Payoo client (không liên quan SDK)
```

### 2.2 Entry Points

| Handler/Endpoint | Class | HTTP Method | Path |
|-----------------|-------|-------------|------|
| Truy vấn hóa đơn | IBillingPaymentController | POST | /check-bill |
| Khởi tạo thanh toán | IBillingPaymentController | POST | /init |
| Confirm (Approve) | BaseFinancialTransactionConfirmExecutor | Internal | via Approval flow |

### 2.3 Key Components (với node_id cho downstream skill)

| Component | node_id | Vai trò |
|-----------|---------|---------|
| IBillingPaymentController | `class:payment-service/.../IBillingPaymentController.java::IBillingPaymentController` | Controller interface |
| InitBillingPaymentHandler | `class:payment-service/.../InitBillingPaymentHandler.java::InitBillingPaymentHandler` | Init handler |
| CheckBillHandler | `class:payment-service/.../CheckBillHandler.java::CheckBillHandler` | Check bill handler |
| BillingPaymentConfirmExecutor | `class:payment-service/.../BillingPaymentConfirmExecutor.java::BillingPaymentConfirmExecutor` | Confirm executor |
| BasePaymentConfirmExecutorDelegate | `class:payment-service/.../BasePaymentConfirmExecutorDelegate.java::BasePaymentConfirmExecutorDelegate` | Base delegate (collectOnBehalf + revert) |
| BillingPaymentConfirmExecutorDelegate | `file:payment-service/.../delegate/impl/BillingPaymentConfirmExecutorDelegate.java` | Impl delegate (VNPAY/PAYOO routing) |
| BillingFinancialServiceDefinition | `file:payment-service/.../BillingFinancialServiceDefinition.java` | Service code enum |
| VnpayBillingClient | `class:client_gateway/.../VnpayBillingClient.java::VnpayBillingClient` | VNPAY API client |
| BillingTransMetadataEntity | `file:payment-service/.../BillingTransMetadataEntity.java` | Metadata entity |
| BillingError | `file:payment-service/.../BillingError.java` | Error codes |

---

## 3. Enum & Constants quan trọng

### 3.1 BillingFinancialServiceDefinition (⚠️ CẦN SỬA)

```java
// HIỆN TẠI — chỉ có billing thường
ELECTRIC_BILLING("004", "00401"),
WATER_BILLING("004", "00402"),

// CẦN THÊM — cho SDK Payment
// SDK_AIRPLANE_BILLING("017", "01701"),
// SDK_TRAIN_BILLING("017", "01702"),
```

### 3.2 PaymentPartner Enum

```java
VNPAY, PAYOO  // SDK dùng VNPAY
```

### 3.3 PaymentType Enum

```java
FULL_PAYMENT, PARTIAL_PAYMENT  // Logic amount khác nhau trong onVnpayBillingPayment()
```

### 3.4 VNPAY_NOT_REVERT_ERROR_CODES

```java
List.of("08", "90")  // Mã lỗi VNPAY KHÔNG đảo tiền → status = TRANSACTION_PENDING
```

### 3.5 BillingError (600xxx)

| Code | Constant | Mô tả |
|------|----------|-------|
| 600000 | BILLING_PARTNER_NOT_FOUND | Partner không tồn tại |
| 600001 | BILLING_PROVIDER_NOT_FOUND | Provider không tồn tại |
| 600002 | BILLING_PROVIDER_SERVICE_NOT_FOUND | Service không tồn tại |
| 600003 | BILLING_BILL_NOT_FOUND | Hóa đơn không tồn tại |
| 600004 | BILLING_CUSTOMER_CODE_REQUIRED | Thiếu mã khách hàng |
| 600005 | BILLING_AMOUNT_INVALID | Số tiền không hợp lệ |
| 600006 | BILLING_WAITING_TIMEOUT | Chờ hóa đơn timeout |
| 600007 | BILLING_WAITING_EXISTED | Đã có GD chờ xử lý |

### 3.6 TransactionStatus (từ revert flow)

| Status | Điều kiện |
|--------|-----------|
| TRANSACTION_SUCCESS | payBill() thành công |
| TRANSACTION_TIMEOUT | CLIENT_CONNECTION_TIMEOUT từ VNPAY |
| TRANSACTION_REVERT_TIMEOUT | Đảo tiền bị timeout |
| TRANSACTION_REVERT_FAILED | Đảo tiền thất bại |
| TRANSACTION_PENDING | Lỗi thuộc NOT_REVERT codes (08, 90) |
| TRANSACTION_FAILED | Lỗi khác → đã revert thành công |

---

## 4. Luồng nghiệp vụ (Confirm Flow) — Đã xác minh từ code

```
Approve Request
    │
    ▼
BillingPaymentConfirmExecutor.onConfirmedTransaction()
    │
    ▼ (delegate)
BasePaymentConfirmExecutorDelegate.onConfirmedTransaction()
    │
    ├─→ 1. collectOnBehalf(transactionModel)
    │       → VBG: Trích nợ TK nguồn + ghi có TK thu hộ
    │       → Trả về: transactionReference, transactionId
    │
    ├─→ 2. onExecutePayment(transactionModel)  ← abstract
    │       │
    │       ▼ (impl: BillingPaymentConfirmExecutorDelegate)
    │       ├── if VNPAY → onVnpayBillingPayment()
    │       │       → Build VnpayPayBillRequest (traceNo, serviceCode, providerCode...)
    │       │       → iVnpayBillingClient.payBill(request, socketTimeout)
    │       │       → Return status = TRANSACTION_SUCCESS
    │       │
    │       └── if PAYOO → onPayooBillingPayment()
    │               → iPayooPaymentClient.payBill(...)
    │               → Return status = TRANSACTION_SUCCESS
    │
    └─→ 3. catch Exception → onRevertTransaction()
            → if isNotRevertTransaction(e) → SKIP (status = PENDING)
            → else → VBG revertTransaction (hoàn tiền TK nguồn)
```

---

## 5. Phát hiện quan trọng & Gap Analysis

### 5.1 GAP-1: BillingFinancialServiceDefinition thiếu SDK entries (BLOCKER)

**Hiện trạng**: Enum chỉ có `ELECTRIC_BILLING("004", "00401")` và `WATER_BILLING("004", "00402")`.

**Hệ quả**: `InitBillingPaymentHandler.fromServiceCode()` sẽ throw `ErrorCode.UNSUPPORTED` khi nhận serviceCode `01701` hoặc `01702`.

**Fix**: Thêm 2 enum values mới:
```java
SDK_AIRPLANE_BILLING("017", "01701"),
SDK_TRAIN_BILLING("017", "01702"),
```

### 5.2 GAP-2: Logic TYPE=2 (SDK) vs TYPE=0 (Billing thường)

**Hiện trạng**: AD_PAYMENT_GROUP phân biệt SDK (TYPE=2) và billing thường (TYPE=0). Cần xác nhận xem code trong `InitBillingPaymentHandler` hoặc `CheckBillHandler` có xử lý phân biệt TYPE hay không.

**Rủi ro**: TRUNG BÌNH — SDK flow có thể cần validation khác (ví dụ: không cần check-bill trước khi thanh toán nếu là vé tàu/máy bay).

### 5.3 CONFIRM: VnpayBillingClient đã sẵn sàng

**getBill()** và **payBill()** đều là generic — không bind cứng vào ELECTRIC/WATER. SDK requests chỉ cần truyền đúng serviceCode/providerCode.

### 5.4 CONFIRM: Reversal logic đã có sẵn

`BasePaymentConfirmExecutorDelegate.onRevertTransaction()` hoạt động cho mọi billing type, kể cả SDK. Không cần modify.

### 5.5 CONFIRM: BillingTransMetadataEntity reuse được

Schema `OMNI_BILLING_TRANS_METADATA` đủ flexible, các field serviceCode/providerCode/recipientCode không bị ràng buộc vào billing thường.

### 5.6 INFO: AD_BILLING_PROVIDER cần verify

Cần kiểm tra bảng `AD_BILLING_PROVIDER` có record với PROVIDER_CODE tương ứng (00000030 cho Máy Bay, 854900 cho Tàu Hỏa) hay chưa. Nếu chưa → cần INSERT trước khi deploy.

---

## 6. Độ tin cậy

| Dimension | Level | Ghi chú |
|-----------|-------|---------|
| DB Schema | CAO | Đã query trực tiếp VBSMEONL |
| Codebase mapping | CAO | KG + grep + source verify |
| Luồng nghiệp vụ | CAO | Đã trace toàn bộ confirm flow |
| Gap analysis | TRUNG BÌNH | Chưa verify logic TYPE=2 trong handler |
| KG freshness | THẤP | Graph VERY_STALE (48 files changed) |
