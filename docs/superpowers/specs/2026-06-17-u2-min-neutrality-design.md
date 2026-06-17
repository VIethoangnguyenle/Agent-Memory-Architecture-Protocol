# U2-min — Framework Neutrality (dọn dư lượng project + policy file-ownership)

> **Phiên bản:** 1.0 | **Ngày:** 2026-06-17
> **Parent:** [upgrade-roadmap-design](2026-06-17-upgrade-roadmap-design.md) — item **U2-min**
> **Phục vụ North Star:** #1 Generic (chỉ ship quy trình + mindset, không ship nội dung dự án)
> **Vai trò:** gate cho **U0** (litmus phải chạy trên framework sạch để đo trung thực
> knowledge-accumulation từ cold-start). Sinh **policy file-ownership** làm đầu vào cho **U3** (`amap migrate`).

---

## 1. Mục tiêu & phạm vi

Làm repo framework AMAP **trung lập hoàn toàn**: loại bỏ sạch nội dung business của dự án cụ thể
(Vietbank), chốt **policy phân loại file-ownership** để các lệnh `init/update/migrate` đối xử đúng,
và bổ sung **một worked example chung chung** để minh hoạ "skeleton rỗng → khi điền đầy trông thế nào".

**KHÔNG thuộc phạm vi U2-min:**
- Implement `amap migrate` → đó là **U3** (U2-min chỉ *định nghĩa* policy mà migrate tuân theo).
- Tách cấu trúc Core / Project Pack + tool-capability interface → đó là **SP3-portability**.
- Đụng tới logic `init/update` của CLI ngoài việc gitignore — chỉ chỉnh nếu cần để tôn trọng policy.

---

## 2. Hiện trạng (đã kiểm chứng trên repo)

| Hạng mục | Phát hiện |
|---|---|
| `knowledge-snapshot.md` | **Là snapshot Vietbank SME Omni đầy đủ** (215 dòng): tên hệ thống, bảng Oracle (`OMNI_DAILY_TRANS_REQ_LIMIT`...), business rule. Pollution chính. Đang track. |
| `persona.yaml` | **Đang bị track trong git** — trái README (README nói nó được gitignore, mỗi dev một bản). `.gitignore` không phủ. |
| `author-dna.draft.yaml` | Đang track; **vô nghĩa trong dự án hiện tại**. |
| `author-dna.yaml` | Đã skeleton trung lập (chỉ HP-1 "SOLID + Clean Code", không Java/Vietbank). |
| `conventions.yaml` | Đã skeleton rỗng (`class_suffixes: {}`...). |
| `active/` | Đã ổn — có `.gitignore` riêng, không track nội dung runtime. |
| `ABC-123`, `PROJ-456`, `jira.example.com` (trong task.md, context-loader.md, templates) | **Không phải pollution** — placeholder generic, giữ nguyên. |

---

## 3. Thiết kế

### 3.1 Phần 1 — Dọn `long-term/` (loại bỏ Vietbank hoàn toàn)

| File | Hành động |
|---|---|
| `knowledge-snapshot.md` | Loại bỏ Vietbank **hoàn toàn, không backup**. Giữ phần hướng dẫn ("Quy ước Metadata Bắt buộc" — đây là *framework guidance*); bỏ sạch section "Tổng quan Hệ thống / Tầng Database / business rule" của Vietbank. Kết quả = skeleton rỗng kèm ví dụ comment. |
| `author-dna.draft.yaml` | **Xoá hẳn** (vô nghĩa). |
| `persona.yaml` | `git rm --cached` + thêm vào `.gitignore`; giữ `persona.template.yaml` (tracked). Sửa README cho khớp thực tế. |
| `author-dna.yaml` | Giữ skeleton trung lập (verify lần cuối, không content project). |
| `conventions.yaml` | Giữ skeleton rỗng. |

**Nguyên tắc ranh giới:** giữ *hướng dẫn format/metadata* (framework) trong file; bỏ *nội dung business*
(project). Vd phần "Quy ước Metadata" của snapshot → giữ; section "Vietbank SME Omni" → bỏ.

### 3.2 Phần 2 — Worked example: author-dna (SOLID / Clean Code / Design Patterns)

Worked example thu gọn về **đúng một artifact giá trị nhất**: một `author-dna.yaml` đã điền đầy, mã hoá
triết lý code kinh điển — **SOLID, Clean Code, Design Patterns (GoF)**. Đây là "judgment layer" và khó
hình dung nhất khi rỗng → đáng có ví dụ nhất; lại universally relevant (không gắn domain nào).

- **Nội dung:** **chỉ** `author-dna.yaml` — vài Hard Principles / Soft Preferences rút từ SOLID
  (SRP/OCP/LSP/ISP/DIP), Clean Code (hàm nhỏ, tên có ý nghĩa, không side-effect ẩn), Design Patterns
  (khi nào Strategy / Factory / Template Method...). Đúng schema `version: "1.1"`.
- **KHÔNG điền `knowledge-snapshot.md` và `conventions.yaml`** cho example — để **skeleton**. Hai file
  này gắn domain/codebase cụ thể nên không phù hợp làm ví dụ "chung chung".
- **Vị trí:** `docs/examples/author-dna-cleancode.yaml` — chỉ là tài liệu tham khảo; có header comment
  giải thích "author-dna đã điền đầy trông thế nào".
- **Ship:** framework-owned (re-render khi update). **KHÔNG** copy vào project đích khi `amap init`.
  README trỏ tới nó như "ví dụ author-dna".

### 3.3 Phần 3 — Policy file-ownership + bảng phân loại

Deliverable cốt lõi: định nghĩa nhóm sở hữu của mọi file, để `init/update/migrate` đối xử đúng.

| Nhóm | Hành vi khi `update` | Gồm |
|---|---|---|
| **Framework-owned** | Re-render/ghi đè (SoT = repo AMAP) | `.agent/{rules,skills,workflows,procedures,tools}`, `AGENTS.md`, entry-point file, `.knowledge-layer/templates/`, `docs/examples/` |
| **Seeded-then-user-owned** | Seed skeleton khi `init`; **giữ nguyên** khi `update`; **`migrate` backfill schema additive** | `.knowledge-layer/long-term/{author-dna.yaml, conventions.yaml, knowledge-snapshot.md}` |
| **Per-dev (gitignored)** | Không track; seed từ `*.template`/skeleton khi init | `persona.yaml`, `.knowledge-layer/active/*` (runtime) |
| **Generated (gitignored)** | Tái sinh khi init/reconfigure/build; không sửa tay | `rule-projector/generated/*`, `__pycache__`, `resolved-config.yaml` |

---

## 4. Invariant cứng — Ba file sống (author-dna / knowledge-snapshot / conventions)

> **Ba file `author-dna.yaml`, `knowledge-snapshot.md`, `conventions.yaml` là TÀI LIỆU SỐNG, tiến hoá
> theo thời gian trong dự án chính** — `knowledge-curator` cập nhật snapshot sau mỗi task; DNA giàu lên
> qua teaching moment (R-DNA-7); conventions cập nhật khi rescan.

Hệ quả bắt buộc, mọi lệnh CLI phải tôn trọng:

1. **Bản chất kép.** Trong repo AMAP = *skeleton framework-owned*. Trong project user = *user-owned đang
   tiến hoá*. Hai bản **decoupled**.
2. **Seed một lần.** Framework chỉ seed skeleton khi `amap init`. Từ đó bản của user tiến hoá độc lập.
3. **`update` TUYỆT ĐỐI KHÔNG ghi đè** ba file này trong project user.
4. **`migrate` (U3) chỉ ADDITIVE schema** — thêm field thiếu kèm default, **không bao giờ chạm
   content/giá trị** mà user/agent đã tích luỹ.
5. **Version stamp tách biệt content:** schema có version riêng (đã có `version: "1.1"` trong DNA/conventions);
   migrate so version để biết field nào cần backfill, không suy luận từ content.

> ⚠️ Đây là điểm dễ gây mất dữ liệu nhất khi nâng cấp version. Policy này là *hợp đồng* mà U3 phải tuân.

---

## 5. Exit criteria (Definition of Done)

- [ ] 0 nội dung business project (Vietbank) trong mọi file framework-owned.
- [ ] `knowledge-snapshot.md` = skeleton (chỉ hướng dẫn metadata + ví dụ comment).
- [ ] `author-dna.draft.yaml` đã xoá.
- [ ] `persona.yaml` đã `git rm --cached` + có trong `.gitignore`; `persona.template.yaml` còn track.
- [ ] README khớp thực tế (persona gitignored).
- [ ] `docs/examples/author-dna-cleancode.yaml` — author-dna đã điền đầy theo SOLID/Clean Code/Design Patterns; knowledge-snapshot & conventions của example để skeleton.
- [ ] File policy file-ownership tồn tại (bảng §3.3 + invariant §4) — versioned, là hợp đồng cho U3.
- [ ] Verify: `grep -riE "vietbank|sme omni|OMNI_|teller"` trên framework-owned files → 0 kết quả.

---

## 6. Rủi ro & quyết định

| # | Vấn đề | Xử lý |
|---|---|---|
| R1 | Xoá nhầm *framework guidance* khi dọn snapshot | Ranh giới rõ §3.1: giữ phần "Quy ước Metadata", chỉ bỏ section business |
| R2 | Worked example bị copy nhầm vào project user | Đặt ở `docs/examples/` (không phải `.knowledge-layer/`); init không đụng `docs/` |
| R3 | `persona.yaml` đang track → `git rm --cached` mất bản local của dev | Chỉ untrack (giữ file trên đĩa); cảnh báo trong commit message |
| R4 | Policy lệch với hành vi CLI thực tế hiện tại | U2-min chỉ *định nghĩa* policy; nếu CLI vi phạm, ghi nhận làm việc cho U3/sau, không sửa CLI trong U2-min trừ gitignore |

---

## 7. Bước tiếp theo

Sau khi spec này được duyệt → dùng skill **writing-plans** dựng implementation plan cho U2-min
(các bước: dọn long-term → fix gitignore/persona → tạo worked example → viết policy doc → verify).
U2-min hoàn tất sẽ **mở khoá U0** (litmus trên framework sạch).
