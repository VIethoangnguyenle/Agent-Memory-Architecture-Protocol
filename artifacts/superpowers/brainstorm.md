## Goal
Giải quyết vấn đề các file `author-dna.yaml` và `conventions.yaml` hiện tại đang chứa các quy tắc quá cụ thể (specific) của một dự án Java/Vietbank (như `ValidationProcessorChain`, `Spring Event`), dẫn đến việc nếu dùng các file này làm template chung cho AMAP framework thì sẽ không phù hợp với các dự án ngôn ngữ/framework khác. Mục tiêu là tách biệt "Template của Framework" và "Dữ liệu cụ thể của dự án".

## Constraints
- AMAP framework phải có khả năng bootstrap (`amap init`) vào bất kỳ dự án nào (Python, Go, Nodejs, v.v.) mà không mang theo rác/nghiệp vụ từ dự án cũ.
- Schema v1.1 phải hỗ trợ cấu trúc chung nhưng data bên trong template phải rỗng hoặc chỉ chứa các nguyên tắc universal (như Clean Code, SOLID).
- Phải phân biệt rõ giữa `author-dna.yaml` dùng để *phát triển chính AMAP* (có thể chứa rule riêng của AMAP) và template dùng để *init dự án mới*.

## Known context
- Các file trong repo AMAP hiện tại đang chứa trực tiếp data của dự án Vietbank SME.
- Khi người dùng cài đặt AMAP vào dự án mới, nếu copy y nguyên file template chứa logic specific thì sẽ gây sai lệch context nghiêm trọng cho Agent.
- Các kỹ năng `author-dna-builder` và `convention-intelligence-builder` được thiết kế để *tự động trích xuất* các quy tắc cụ thể từ codebase đích, nên file template ban đầu không cần thiết phải chứa sẵn các rule cụ thể này.

## Risks
- Nếu template rỗng hoàn toàn, Agent có thể thiếu judgment layer ở giai đoạn đầu (trước khi user chạy `/dna-scan`).
- Việc làm sạch template có thể vô tình xóa mất cấu trúc schema mẫu (ví dụ để user biết cách điền `check_spec`).

## Options (2–4)
1. **Empty Skeleton Templates (Khuyên dùng):** AMAP chỉ cung cấp các file template rỗng chứa đúng cấu trúc schema v1.1 (chỉ có `version: "1.1"`, kèm theo comment hướng dẫn và dictionary trống). Mọi rule cụ thể đều do `author-dna-builder` sinh ra hoặc user tự thêm vào dự án đích.
2. **Universal Baseline Templates:** Cung cấp các template chứa sẵn các rule cực kỳ chung chung (ngôn ngữ độc lập) áp dụng cho mọi project như: "Zero Nesting", "No Else", "SOLID", và để trống các rule liên quan đến architecture/framework.
3. **Language-Specific Profiles:** Xây dựng sẵn các template theo ngôn ngữ (`dna-java.yaml`, `dna-python.yaml`) để `amap init` copy tương ứng. (Rủi ro: khó bảo trì và đi ngược triết lý "scan from codebase" của AMAP).

## Recommendation
**Lựa chọn Option 1 (Empty Skeleton Templates)**.
- **Bước 1:** Làm sạch toàn bộ các rule specific của Vietbank ra khỏi các file template chuẩn bị dùng để init dự án mới. Template chỉ nên là một "Skeleton" chuẩn schema v1.1, kèm theo 1 rule dummy bị comment lại để làm mẫu cho `check_spec`.
- **Bước 2:** Nhờ vào kiến trúc mới, DNA của dự án đích sẽ được xây dựng tự động từ chính dự án đó bằng `/dna-scan` thay vì hardcode.
- File `author-dna.yaml` đang nằm trong `.knowledge-layer/long-term/` của repo AMAP này (dùng để phát triển AMAP) cũng nên được refactor lại thành DNA của việc *viết Python CLI cho AMAP* thay vì chứa logic Java.

## Acceptance criteria
1. Các file template thực sự dùng để `amap init` được làm sạch 100% các logic đặc thù dự án (Java/Spring/Vietbank).
2. Template chỉ chứa cấu trúc schema v1.1 hợp lệ (`version: "1.1"`, dict rỗng + comment ví dụ).
3. Phân tách rõ ràng giữa "AMAP templates" (dùng cho cli init) và "AMAP project's own DNA" (dùng để maintain repo này).
