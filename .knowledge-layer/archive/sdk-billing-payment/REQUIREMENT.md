# REQUIREMENT.md — Thanh toán SDK
> Ticket: HAS_DOC_ONLY (chưa có ticket Jira)
> Loại: feature
> Ngày tạo: 2026-06-08
> Tài liệu liên kết:
>   - [SRS_Thanh toán SDK — Vietbank SME OMNI Nội Bộ](https://wiki.servicehub.vn/spaces/Vietbankomninb/pages/962573960/SRS_Thanh+to%C3%A1n+SDK) (v19)
>   - [URD_ Luồng thanh toán SDK — OMNISCB](https://wiki.servicehub.vn/pages/viewpage.action?pageId=411731063) (v20, tham chiếu gốc)

---

## Business Context & Động lực

Khách hàng doanh nghiệp SME sử dụng các SDK hệ sinh thái VNPAY tích hợp trên App Vietbank (vé máy bay, vé tàu hỏa…). Sau khi đặt vé/đặt hàng thành công trên SDK, khách cần thanh toán hóa đơn qua tài khoản ngân hàng Vietbank. Hiện tại App chưa có luồng thanh toán SDK cho phân khúc SME (Maker-Checker), cần xây dựng mới để:

- Mở rộng dịch vụ giá trị gia tăng cho khách hàng doanh nghiệp.
- Tận dụng hạ tầng VNPAY Billing sẵn có.
- Luồng dùng chung cho tất cả SDK (mở rộng giai đoạn sau).

---

## As-is / To-be

### As-is (Hiện tại)

- Luồng thanh toán SDK chỉ tồn tại cho ứng dụng SCB OMNI cá nhân (1 bước xác thực).
- Phân khúc SME chưa có luồng thanh toán SDK riêng với mô hình Maker-Checker.

### To-be (Mong muốn)

- App Vietbank SME có luồng Thanh toán SDK theo mô hình **Maker-Checker** (tạo lệnh → duyệt lệnh).
- Hỗ trợ SDK VNPAY: Vé máy bay (01701), Vé tàu hỏa (01702) — mở rộng thêm SDK trong tương lai.
- Tích hợp VNPAY Billing: truy vấn nợ + gạch nợ.
- Hạch toán qua hệ thống Bank + xử lý đảo tiền khi gạch nợ thất bại.
- Hỗ trợ cả kênh MB (Mobile Banking) và IB (Internet Banking).

---

## Scope

### In-scope

- Luồng **tạo lệnh** thanh toán SDK (Maker): SDK callback → truy vấn nợ → chọn TK nguồn → xác thực → lập lệnh "Chờ duyệt".
- Luồng **duyệt lệnh** (Checker): xem chi tiết → phê duyệt/từ chối → xác thực → hạch toán → gạch nợ → kết quả.
- Luồng **đảo tiền** (reversal): khi hạch toán Bank thành công nhưng gạch nợ VNPAY Billing thất bại.
- 11 màn hình (MH1–MH11) cho cả MB và IB.
- Bảng cấu hình SDK (ProviderCode, ServiceCode, ServiceCodeOmni).
- OTT Routing ID cho push notification.
- Luồng lỗi chi tiết: session timeout, xác thực thất bại, hạn mức không hợp lệ, hạch toán thất bại, gạch nợ thất bại, billing timeout/errors (mã 01–99).

### Out-of-scope

- Phạm vi SDK (màn hình đặt vé, booking flow) — do SDK VNPAY quản lý.
- Onboarding KH mới hoặc đăng ký dịch vụ SDK.
- Đối soát thủ công (chỉ ghi nhận giao dịch cần đối soát, không triển khai quy trình đối soát).
- Non-functional requirements (SRS ghi "--//--" — chưa có).

---

## Yêu cầu nghiệp vụ trích từ tài liệu

### Actor & Use Case

- **Người tạo lệnh (Maker)**: Khách hàng doanh nghiệp — tạo lệnh thanh toán sau khi đặt vé trên SDK.
  - UC: Thanh toán hóa đơn từ SDK VNPAY (UC_BILL_PAYMENT_002).
- **Người duyệt lệnh (Checker)**: Khách hàng doanh nghiệp — phê duyệt hoặc từ chối lệnh thanh toán.
  - UC: Phê duyệt/Từ chối lệnh thanh toán SDK.
- **Server (OMNI)**: Xử lý nghiệp vụ, điều phối luồng giao dịch.
- **SDK VNPAY**: Hiển thị MH đặt vé, trả thông tin thanh toán (ProviderCode, ServiceCode, CustomerCode).
- **VNPAY Billing**: Tra vấn nợ, gạch nợ thanh toán.
- **Hệ thống Bank**: Hạch toán giao dịch, đảo tiền.

### Luồng chính

**Phần 1 — Tạo lệnh (Maker)**
1. Maker đăng nhập App, chọn tính năng SDK, thực hiện đặt vé.
2. Maker nhấn "Thanh toán" trên MH Xác nhận thanh toán SDK.
3. SDK trả thông tin: ProviderCode, ServiceCode, CustomerCode → Client.
4. Client kiểm tra phiên giao dịch (AF-01 nếu hết phiên).
5. Client gửi yêu cầu truy vấn nợ + lấy DS tài khoản nguồn sang Server.
6. Server gọi VNPAY Billing truy vấn nợ + lấy DS TK từ Bank.
7. App hiển thị MH2 Khởi tạo: TK nguồn, thông tin hóa đơn (mã thanh toán, dịch vụ, tổng tiền).
8. Maker chọn TK nguồn → nhấn "Tiếp tục".
9. Server khởi tạo GD → trả PTXT (phương thức xác thực).
10. App hiển thị MH3 Xác nhận giao dịch.
11. Maker nhấn "Tiếp tục" → App hiển thị MH4 Xác thực.
12. Maker nhập mã xác thực.
13. Server xác thực thành công → lưu lệnh trạng thái "Chờ duyệt".
14. App hiển thị MH5 Tạo lệnh thành công.

**Phần 2 — Duyệt lệnh (Checker)**
1. Checker truy cập MH Giao dịch chờ duyệt → chọn lệnh SDK.
2. App hiển thị MH6 Chi tiết lệnh.
3. Checker xem xét → nhấn "Phê duyệt" (hoặc AF-02 Từ chối).
4. App hiển thị MH7 Ý kiến phê duyệt → MH8 Xác nhận GD.
5. Checker nhấn "Tiếp tục" → MH9 Xác thực.
6. Checker xác thực Soft OTP.
7. Server xử lý tuần tự:
   - Bước 1: Kiểm tra hạn mức GD + hạn mức gói.
   - Bước 2: Hạch toán qua Bank (trừ tiền TK nguồn).
   - Bước 3: Gạch nợ qua VNPAY Billing.
8. App hiển thị MH10 Kết quả thành công.
9. Server gửi SMS/Email thông báo cho Maker.

### Luồng lỗi / ngoại lệ

- **AF-01**: Hết phiên/chưa đăng nhập khi nhấn Thanh toán SDK → popup thông báo → đăng nhập lại → quay lại MH Khởi tạo.
- **AF-02**: Checker từ chối lệnh → nhập ý kiến (tùy chọn) → trạng thái "Từ chối" → notify Maker.
- **EF-01**: Xác thực tạo lệnh thất bại → thông báo lỗi + số lần nhập còn lại → vượt giới hạn → thực hiện lại từ đầu.
- **EF-02**: Xác thực duyệt lệnh thất bại → tương tự EF-01.
- **EF-03**: Hạn mức GD/gói không hợp lệ → thông báo lỗi hạn mức.
- **EF-04**: Hạch toán Bank thất bại → trạng thái "Thất bại".
- **EF-05**: Gạch nợ thất bại SAU hạch toán thành công → **Đảo tiền**:
  - Đảo tiền OK → trạng thái "Thất bại", thông báo thử lại.
  - Đảo tiền thất bại → ghi nhận GD đảo tiền thất bại → đối soát thủ công.
  - Đảo tiền timeout → trạng thái "Nghi vấn" → đối soát.
- **EF-06**: Lỗi kết nối VNPAY Billing (bước truy vấn nợ hoặc gạch nợ) → thông báo "Dịch vụ gián đoạn".
- **EF-07**: Hạch toán timeout → đối soát thủ công.

### Quy tắc nghiệp vụ

- **BR-01**: Hạn mức thanh toán tuân theo gói dịch vụ KH doanh nghiệp.
- **BR-02**: TK nguồn phải là TK thanh toán đang hoạt động.
- **BR-03**: Luồng SDK dùng chung cho tất cả SDK trên App (mở rộng theo giai đoạn).
- **BR-04**: Server PHẢI đảo tiền khi gạch nợ thất bại sau hạch toán thành công.
- **BR-05**: Cả Maker và Checker có quyền xem chi tiết GD trong Lịch sử/Quản lý GD.
- **BR-06**: SMS/Email thông báo kết quả gửi cho Maker sau khi duyệt thành công.
- **BR-07**: Xác thực tạo/duyệt lệnh yêu cầu PTXT (Biometric, SMS OTP, Token Key, Soft OTP).
- **BR-08**: GD hạch toán timeout, gạch nợ timeout, đảo tiền timeout → đối soát thủ công.
- **BR-09**: ServiceCode mapping:
  - `01701` = Máy bay
  - `01702` = Tàu hỏa

### Bảng cấu hình SDK

| STT | SDK | Dịch vụ | ProviderCode | ServiceCode (VNPAY) | ServiceType OMNI | ServiceCode OMNI |
|-----|-----|---------|-------------|---------------------|------------------|------------------|
| 1 | Vé máy bay | VNTicketAPI | 00000030 | 100005 | 017 | 01701 |
| 2 | Vé máy bay addon | VNTicketAddon | 804900 | 804904 | 017 | 01701 |
| 3 | Vé tàu hỏa | — | 854900 | 854901 | — | 01702 |

### OTT Routing ID

| ROUTING_ID | GROUP | NAME | Button VN | Button EN |
|-----------|-------|------|-----------|-----------|
| 01701 | G_NOTIFY | Đặt vé máy bay | Đặt vé ngay | Book tickets |
| 01702 | G_NOTIFY | Mua vé tàu hỏa | Đặt vé ngay | Book tickets |

### Danh sách API

| STT | API | Nguồn | Tham khảo |
|-----|-----|-------|-----------|
| 1 | Lấy DS tài khoản nguồn | Bank | APIs THANH TOÁN HÓA ĐƠN (VNPAY) |
| 2 | Hạch toán TTHĐ | Bank | |
| 3 | Đảo tiền | Bank | |
| 4 | Truy vấn nợ | VNPAY Billing | |
| 5 | Gạch nợ | VNPAY Billing | |

### Danh sách mã lỗi Billing

| STT | Nhóm lỗi | Mã Billing | Xử lý |
|-----|----------|------------|-------|
| 1 | NCC/Dịch vụ không hợp lệ | 80–86 | Thông báo "Dữ liệu dịch vụ không hợp lệ" — Lệnh Thất bại — KHÔNG đảo tiền |
| 2 | Dữ liệu đầu vào sai | 07,20,79,87,88,91,97 | Tương tự nhóm 1 — KHÔNG đảo tiền |
| 3 | Mã KH không hợp lệ | 50 | "Mã KH/hóa đơn không hợp lệ" — KHÔNG đảo tiền |
| 4 | Số tiền gạch nợ sai | 89 | "Thông tin thanh toán không hợp lệ" — KHÔNG đảo tiền |
| 5 | VNPAY billing/NCC gián đoạn | 01,05,96,99 | "Dịch vụ gián đoạn" — KHÔNG đảo tiền |
| 6 | Timeout Billing | 08,90 | "Dịch vụ gián đoạn" → đối soát — KHÔNG đảo tiền |

> Ghi chú: Đảo tiền chỉ xảy ra khi hạch toán Bank thành công + gạch nợ VNPAY Billing **thất bại** (không thuộc nhóm mã lỗi 1–6).

---

## Acceptance Criteria

- [ ] AC-01: Maker nhấn "Thanh toán" trên SDK → App hiển thị MH Khởi tạo với thông tin hóa đơn và DS tài khoản nguồn.
- [ ] AC-02: Maker tạo lệnh thành công → lệnh trạng thái "Chờ duyệt", hiển thị MH5 Tạo lệnh thành công.
- [ ] AC-03: Checker phê duyệt → hạch toán Bank + gạch nợ VNPAY Billing thành công → MH10 Kết quả thành công.
- [ ] AC-04: Checker từ chối → trạng thái "Từ chối" + notify Maker.
- [ ] AC-05: Gạch nợ thất bại sau hạch toán thành công → Server đảo tiền tự động.
- [ ] AC-06: Hạch toán/gạch nợ timeout → GD đưa vào đối soát.
- [ ] AC-07: Session hết hạn khi nhấn Thanh toán SDK → popup thông báo → đăng nhập lại → quay lại flow.
- [ ] AC-08: Mã billing lỗi (nhóm 80–99) → hiển thị thông báo tiếng Việt/Anh tương ứng → lệnh Thất bại, KHÔNG đảo tiền.
- [ ] AC-09: Hạn mức GD/gói không hợp lệ → thông báo lỗi hạn mức, không xử lý lệnh.
- [ ] AC-10: Hỗ trợ cả kênh MB và IB với UI spec tương ứng (11 MH).
- [ ] AC-11: OTT push notification routing đúng theo ROUTING_ID (01701/01702).
- [ ] AC-12: ServiceCode OMNI mapping đúng: 01701 (Máy bay), 01702 (Tàu hỏa).

---

## Giả định (Assumptions)

- SDK VNPAY đã tích hợp sẵn trên App Vietbank SME và trả đúng callback với ProviderCode, ServiceCode, CustomerCode.
- Hệ thống Bank đã có API hạch toán, đảo tiền, lấy DS TK sẵn sàng.
- VNPAY Billing API (truy vấn nợ, gạch nợ) đã tồn tại và hoạt động.
- Luồng xác thực (XÁC THỰC) và luồng phê duyệt chung (SRS_FE_Giao dịch chờ duyệt) đã triển khai và có thể tái sử dụng.
- Bảng cấu hình Provider/Service đã được seed trong DB.

---

## Vấn đề yêu cầu (Open Questions)

- **Q-01**: NFR (Non-Functional Requirements) ghi "--//--" trong SRS — cần xác nhận latency target, TPS, availability cho VNPAY Billing integration.
- **Q-02**: Luồng OTT (thanh toán từ push notification) — SRS SME chưa mô tả chi tiết. URD gốc có BF2 cho OTT flow — có áp dụng cho SME không?
- **Q-03**: Rule loại trừ TK nguồn (TR%, NB%, KKH%, CDI%, tài khoản lương, frozen, phong tỏa, đồng chủ sở hữu) — URD gốc mô tả chi tiết nhưng SRS SME không nhắc lại. Confirm apply giống nhau?
- **Q-04**: Mô hình Maker-Checker: có hỗ trợ tự duyệt (Maker = Checker) cho giao dịch nhỏ không? Hay bắt buộc 2 người khác nhau?
- **Q-05**: Phí dịch vụ (Provider Service Fee) — SRS nhắc đến nhưng chưa rõ công thức tính hoặc ai cung cấp (Server hay VNPAY Billing).
- **Q-06**: Cần xác nhận trường `serviceCodeOmni` do SDK trả về hay Server tự map từ ProviderCode + ServiceCode?

---

## Nguồn tài liệu

| # | Tài liệu | URL | Ngày cập nhật | Staleness |
|---|----------|-----|---------------|-----------|
| 1 | SRS_Thanh toán SDK (Vietbank SME OMNI Nội Bộ) | [pageId=962573960](https://wiki.servicehub.vn/spaces/Vietbankomninb/pages/962573960) | v19 (không có metadata ngày rõ) | ⚠️ Không xác định được ngày cập nhật chính xác |
| 2 | URD_ Luồng thanh toán SDK (OMNISCB gốc) | [pageId=411731063](https://wiki.servicehub.vn/pages/viewpage.action?pageId=411731063) | v20 (tạo ~2024-03) | ⚠️ > 24 tháng — tham chiếu pattern chung, không dùng làm source of truth |

---

## Độ tin cậy tài liệu

- **Mức: TRUNG BÌNH**
- **Lý do**:
  - SRS SME khá chi tiết về luồng chính, luồng lỗi, mã billing, màn hình UI spec.
  - Thiếu NFR hoàn toàn.
  - Một số tham chiếu chéo (XÁC THỰC, Giao dịch chờ duyệt) chưa được include nội dung → cần verify thêm.
  - Rule TK nguồn chỉ có trong URD gốc, SRS SME không nhắc lại → risk of gap.
  - Không xác định được ngày cập nhật cuối SRS → có thể stale.

---

## Ghi chú từ tài liệu gốc

- SRS xác nhận Use Case ID: `UC_BILL_PAYMENT_002`.
- Luồng đảo tiền chỉ trigger khi gạch nợ thất bại. Các mã billing lỗi (nhóm 80–99) KHÔNG trigger đảo tiền.
- MH10 Kết quả duyệt lệnh ghi "Thanh toán QR" trong cột loại giao dịch — có thể là lỗi copy paste từ luồng QR, cần verify.
- IB MH6 gạch bỏ (strikethrough) trường "Phí giao dịch" → có thể IB không hiển thị phí.
