## Goal
Dọn dẹp và chuẩn hóa các file template cấu hình DNA (`author-dna.yaml`, `conventions.yaml`) để tách bạch hoàn toàn phần khung chung của AMAP Framework (v1.1) khỏi các logic nghiệp vụ đặc thù dự án (như Java, Vietbank). Đảm bảo AMAP có thể `amap init` sạch sẽ vào bất kỳ dự án nào mà không mang theo rác từ dự án cũ.

## Assumptions
- Các file nằm trong `.knowledge-layer/long-term/` của repo AMAP chính là các template được `cli/scaffold` sử dụng để copy sang dự án đích.
- Dự án mới sẽ dựa vào quá trình `/dna-scan` hoặc maintainer tự điền để xây dựng DNA thay vì nhận sẵn một bộ DNA cứng nhắc từ framework.

## Plan

**Step 1: Làm sạch và chuẩn hóa Template `author-dna.yaml`**
- **Files**: `.knowledge-layer/long-term/author-dna.yaml`, `.knowledge-layer/long-term/author-dna.draft.yaml`
- **Change**: 
  - Khai báo `version: "1.1"` ở đầu file.
  - Chuyển `hard_principles` và `style_preferences` sang định dạng Dictionary.
  - Xóa toàn bộ các rule chứa code Java/Vietbank (như HP-1, HP-2, SP-1...).
  - Giữ lại 1-2 rule cực kỳ Universal (ví dụ: Zero Nesting, SOLID) nhưng viết dưới dạng ngôn ngữ độc lập, hoặc để 1 rule dummy làm ví dụ mẫu cho việc viết `check_spec`.
- **Verify**: Kiểm tra cú pháp YAML hợp lệ.

**Step 2: Làm sạch và chuẩn hóa Template `conventions.yaml`**
- **Files**: `.knowledge-layer/long-term/conventions.yaml`
- **Change**: 
  - Tương tự, cập nhật lên `version: "1.1"` và cấu trúc Dictionary.
  - Xóa bỏ các naming pattern liên quan trực tiếp đến Spring Boot / Java / Omni.
  - Để lại dictionary rỗng kèm comment giải thích cách dùng `/convention-scan` để tạo rule mới.
- **Verify**: Kiểm tra cú pháp YAML hợp lệ.

**Step 3: Cập nhật hướng dẫn Onboarding cho dự án mới**
- **Files**: `AGENTS.md` (hoặc các file hướng dẫn cài đặt nếu có).
- **Change**: Thêm hướng dẫn rõ ràng: Sau khi chạy `amap init`, người dùng PHẢI chạy lệnh `/dna-scan` và `/convention-scan` để Agent quét dự án và xây dựng DNA thực tế, vì template mặc định sẽ ở dạng "Skeleton rỗng".
- **Verify**: Xác nhận file markdown không có syntax error.

## Risks & mitigations
- **Risk**: Việc làm rỗng template khiến user mới bối rối không biết cách viết `check_spec` hoặc các thuộc tính của rule.
- **Mitigation**: Cố ý để lại ít nhất 1 rule "Universal" hoặc 1 rule bị comment lại (dummy rule) làm tài liệu tham khảo sống bên trong YAML.

## Rollback plan
- Hủy bỏ các thay đổi bằng `git checkout -- .knowledge-layer/long-term/` và revert markdown files.
