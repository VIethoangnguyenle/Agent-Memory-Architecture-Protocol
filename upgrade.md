# AMAP v3.0 — Critical Upgrade Action Plan

> **Tài liệu này tóm tắt 4 ưu tiên cốt lõi và khẩn cấp nhất để đưa AMAP v3.0 đạt trạng thái Production Ready.**

## 1. 🔴 Khẩn cấp nhất (P0): Litmus Test trên Dự án thực
**"Con voi trong phòng": Chưa chạy End-to-End.**
*   **Vấn đề:** 5/7 core components (bao gồm cả Micro-loop và Mechanical Enforcement) mới chỉ pass "fixture test" (test giả lập trên môi trường tĩnh). Chưa có bằng chứng thực tế chứng minh chúng chạy trơn tru từ đầu đến cuối trên codebase thật của Vietbank SME Omni.
*   **Hành động ngay:** Tạm dừng phát triển tính năng mới. Lấy 1 ticket thật (Standard complexity, có thay đổi DB/Code), chạy full flow từ `Ideation → Apply` để validate toàn bộ pipeline và ghi nhận ma sát.

## 2. 🔴 Trải nghiệm Dev (P1): Workflow Tiering (Phân loại Task)
**Ma sát quá lớn cho task nhỏ.**
*   **Vấn đề:** Hiện tại mọi task (kể cả sửa 1 lỗi typo hay đổi 1 config) đều bị ép chạy qua toàn bộ pipeline 428-dòng (Explore DB → Codebase → Kiến trúc → Opsx Explore → ...). Overhead quá lớn, tốn token và gây nản cho developer, dẫn đến rủi ro dev bypass framework.
*   **Hành động ngay:** Thêm cơ chế phân loại đầu vào ở `/task`:
    *   **Tiny task:** Bỏ qua các bước khám phá nặng (DB/Arch review), cho phép xử lý và commit nhanh.
    *   **Standard/Complex:** Chạy full pipeline như thiết kế hiện tại.

## 3. 🟡 Tính Trung Lập (P2): Dọn dẹp Knowledge Snapshot
**Framework bị ô nhiễm context của Vietbank.**
*   **Vấn đề:** File `knowledge-snapshot.md` nằm trong thư mục của AMAP (repo framework) nhưng lại chứa đầy đủ dữ liệu kiến trúc, database, rule ngân hàng của dự án Vietbank SME. Điều này phá vỡ tính "framework-agnostic". Người dùng clone framework về sẽ bị nhiễu context nghiêm trọng.
*   **Hành động ngay:** Chuyển hết thông tin của Vietbank sang repo đích (`vietbank-sme-omni`). Tại repo AMAP, `knowledge-snapshot.md` chỉ nên là skeleton với ví dụ comment, hoặc mô tả chính kiến trúc của AMAP.

## 4. 🟡 Khả năng Nâng cấp (P3): Cơ chế Schema Migration
**Rủi ro gãy đổ khi cập nhật version mới.**
*   **Vấn đề:** Khi `amap update` được chạy, nếu schema của các file quan trọng như `author-dna.yaml` hay `conventions.yaml` có thêm field mới, các file cũ của user sẽ không tự động nhận field đó (do chính sách user ownership). Agent sẽ bị confusion khi đọc file thiếu field.
*   **Hành động ngay:** Phát triển cơ chế `amap migrate` hoặc thêm logic cảnh báo version trong lệnh update để tự động bổ sung (additive) các field mới vào file của user một cách an toàn.

---
**Verdict:** AMAP là công trình xuất sắc về thiết kế, nhưng cần chứng minh khả năng thực chiến (P0) và giảm bớt sự rườm rà (P1) trước khi có thể áp dụng rộng rãi.
