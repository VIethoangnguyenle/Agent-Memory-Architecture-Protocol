# U0 Baseline-Litmus Protocol — Đo outcome AMAP vs Baseline (P1.1)

> **Phiên bản:** 1.0 | **Ngày:** 2026-06-18
> **Loại:** Test/measurement protocol design (không phải feature design)
> **Map roadmap:** P1.1 (TODOS) — nâng U0 từ litmus *process* lên litmus *outcome* bằng cách thêm baseline arm.
> **Tiền đề:** Batch 1 (scaffold hardening) đã merge vào `main`.
> **Deliverable của batch này:** *chỉ* file spec protocol này (đã nhúng rubric + report template). KHÔNG code harness — harness liên tục là UP1, làm sau khi protocol được chứng minh.

---

## 1. Mục tiêu & câu hỏi quyết định

Protocol trả lời **một câu duy nhất, mang tính quyết định thesis**:

> Chạy AMAP full 5 pha có cho ra outcome **tốt hơn đo được** so với một agent baseline (chỉ entry-point native mỏng + ad hoc) trên **cùng một ticket thật** không — và tốn thêm bao nhiêu?

**Tập trung:** câu hỏi của protocol này là **chất lượng output** (diff đúng hơn, ít rework hơn, bắt đúng blast-radius). Đo *IDE-independence* (giá trị có nhất quán giữa các agent không) là **việc khác** — thuộc SP3-portability, có đường validate riêng — **không** gộp vào đây.

**Vì sao cần** (tóm tắt — chi tiết ở roadmap §6/R1 và TODOS P1.1):
- 4 thuộc tính North Star đều là *means*, không *end*. Không cái nào đo trực tiếp "diff đúng hơn, ít rework hơn".
- U0 cũ chỉ đo *process* ("máy có quay không"), không đo *value* ("máy có đáng quay không").
- Không có baseline thì không quy được công: giá trị luôn tương đối.
- Đây là van phải mở trước khi đổ tiền vào SP3-portability / UP2.
- Là phép đo đầu tiên biến *chất lượng* thành thứ quan sát được → nền cho UP1 (regression test cho giá trị).

**Ngoài phạm vi (out of scope):** sửa code framework, build harness/scorer tự động, chạy CI. Mọi friction lộ ra trong lúc chạy được *triage* (xem §9), không fix trong phạm vi này.

---

## 2. Kiến trúc thí nghiệm (A/B, 2 arm)

Mỗi ticket chạy **2 arm trong session hoàn toàn tách rời**:

- **Arm A — AMAP:** full `Ideation → Requirement → Architecture → Spec → Apply`. `active/` reset rỗng (cold-start) để đo cả phần tích luỹ tri thức từ con số 0.
- **Arm B — Baseline:** cùng model/agent, cùng ticket, chỉ có **một file entry-point native *mỏng cố định*** + prompt ad hoc. KHÔNG 5 pha, KHÔNG knowledge hierarchy, KHÔNG mechanical gate.

**Đề bài cấp cho cả 2 arm là *giống hệt nhau*** = tiêu đề + mô tả của issue/PR gốc, **đã giấu phần diff đáp án**. Arm A nhận đề qua `/task`; Arm B nhận đề qua prompt ad hoc.

### 2.1 Định nghĩa "baseline mỏng" (chống strawman)

File entry-point baseline **phải** chứa, và **chỉ** chứa:
- Build/test command của repo.
- Convention đỉnh cao (naming, layering) — mức một dev tử tế sẽ tự viết.
- 1 đoạn (≤ ~150 từ) tóm tắt kiến trúc hệ thống.

File entry-point baseline **không được** chứa:
- Bất kỳ bộ máy AMAP nào (pha, gate, memory hierarchy, rule).
- Gợi ý riêng cho ticket đang test (không "mớm" lời giải).

Nội dung file này **đóng băng trước khi chạy** và **chép nguyên văn vào report** (§ Appendix B) để bên thứ ba review được rằng baseline không bị cố ý làm yếu.

---

## 3. Test target & ground truth (Option A)

### 3.1 Tiêu chuẩn một target hợp lệ
- Repo **OSS công khai**, license cho phép đọc/clone.
- "Ticket" = một **PR đã merge** có mô tả/issue rõ ràng.
- Ticket có **DB + code thật** (ít nhất với size standard/complex; tiny có thể chỉ code).
- PR có **review comments** (càng tốt — dùng làm tín hiệu rework con người thật đã yêu cầu).

### 3.2 Ground truth
**Ground truth = diff đã merge của PR + review comments của nó.** Đây là "đáp án" con người thật đã duyệt và ship. Mọi metric outcome đo bằng cách so output của agent với ground truth này.

### 3.3 Chống nhiễu R1 (agent đã thấy repo lúc train)
- Ưu tiên PR **merge sau ngày cutoff** của model dùng để chạy.
- Hoặc chọn repo ít nổi nhưng kỷ luật review tốt.
- Ghi `repo@commit_sha`, `PR#`, `merge_date`, `model_version` vào report để tái lập và để người đọc tự đánh giá mức nhiễu.

> Spec **khuyến nghị Option A** làm bản instantiation cụ thể, nhưng định nghĩa theo *tiêu chuẩn target* ở §3.1 nên không khoá cứng vào một repo. Repo + danh sách PR cụ thể chốt ở bước implementation plan.

---

## 4. Chọn ticket (≥3, theo size)

Tối thiểu **3 ticket**, mỗi size một ticket.

| Size | Tín hiệu phân loại |
|---|---|
| **tiny** | 1–2 file, không đụng DB/schema, không ràng buộc kiến trúc |
| **standard** | vài file + 1 module, có đụng data layer |
| **complex** | nhiều module, đụng DB + có ràng buộc kiến trúc / blast-radius rộng |

Mỗi ticket chọn một PR merged thật khớp size. Size được **gán trước khi chạy** dựa trên ground truth (diff merge), không gán theo cảm giác sau.

---

## 5. Run matrix

Chạy trên **một platform** = môi trường chính của dự án: **Claude Code** (entry-point baseline `CLAUDE.md`, framework root `.claude/`).

**Ma trận chạy:** 1 platform × ≥3 ticket (tiny/standard/complex) × 2 arm = **≥6 run**.

> Platform là **tham số**, không phải trục đo. Protocol không Claude-specific — đổi sang agent khác chỉ là đổi entry-point baseline + framework root. Nhưng *so sánh chéo IDE* nằm ngoài phạm vi protocol này (xem §1).

---

## 6. Metrics (đo gì, đo bằng gì)

| # | Metric | Định nghĩa | Cách đo | Hướng tốt |
|---|---|---|---|---|
| M1 | **Correctness / Rework** | output sai/thiếu/thừa so với ground truth → cần làm lại bao nhiêu | LLM-judge rubric (§7.1) + human spot-check | cao = tốt |
| M2 | **Blast-radius** | có đụng đúng tập file cần đụng không | **precision/recall tập-file & vùng-diff vs PR gốc** (cơ học/khách quan) | cao = tốt |
| M3 | **Convention adherence** | hợp naming/pattern/layering của repo | LLM-judge rubric (§7.1) | cao = tốt |
| M4 | **Manual interventions** | số lần người vận hành phải can thiệp (unstuck, sửa hướng) | đếm cơ học (đánh dấu lúc chạy) | thấp = tốt |
| M5 | **Token** | tổng token mỗi arm | đếm cơ học | thấp = tốt |
| M6 | **Wall-clock** | thời gian thực mỗi arm (phút) | đếm cơ học | thấp = tốt |

M1–M3 là **chất lượng outcome**. M4–M6 là **chi phí**. Verdict cân hai nhóm này (§9).

---

## 7. Scoring & rubric (hybrid)

Ba lớp:
1. **Cơ học** (M2, M4, M5, M6): không ai phán xét — đếm/tính trực tiếp. M2 tính precision/recall giữa tập file (và vùng diff) của arm với PR gốc.
2. **LLM-judge bịt mắt** (M1, M3): judge nhận **2 diff đã ẩn nhãn arm** + ground truth + rubric cố định §7.1, chấm theo thang điểm. Bịt mắt để không thiên vị "đây là arm AMAP".
3. **Human spot-check:** người duyệt lại ≥1 ca mỗi size, xác nhận điểm LLM-judge không lệch hệ thống. Nếu lệch → ghi chú và ưu tiên điểm người.

### 7.1 Rubric (nhúng — chạy tay được ngay)

**M1 — Correctness / Rework** (thang 0–4, so với ground truth):

| Điểm | Mô tả |
|---|---|
| 4 | Khớp ý định ground truth; không cần rework; không bug rõ |
| 3 | Đúng hướng, sai vài chi tiết nhỏ; rework nhẹ |
| 2 | Giải đúng một phần; thiếu nhánh/case quan trọng; rework đáng kể |
| 1 | Sai hướng phần lớn; rework nặng gần như viết lại |
| 0 | Không chạy / sai hoàn toàn / lạc đề |

**M3 — Convention adherence** (thang 0–4, so với convention repo):

| Điểm | Mô tả |
|---|---|
| 4 | Theo sát naming/layering/pattern của repo, không lệch |
| 3 | Theo phần lớn; 1–2 lệch nhỏ |
| 2 | Lệch vài chỗ thấy rõ (naming hoặc layering) |
| 1 | Lệch nhiều; không giống style repo |
| 0 | Bỏ qua convention hoàn toàn |

**M2 — Blast-radius** (cơ học): với `F_arm` = tập file arm sửa, `F_truth` = tập file PR gốc sửa:
- `precision = |F_arm ∩ F_truth| / |F_arm|` (đụng có đúng chỗ không — phạt đụng thừa)
- `recall = |F_arm ∩ F_truth| / |F_truth|` (có bắt đủ chỗ cần đụng không — phạt bỏ sót)

Ghi cả hai; báo cáo F1 nếu muốn một số.

**Judge bịt mắt — quy tắc:** mỗi cặp (ticket × platform), trộn ngẫu nhiên thứ tự 2 diff, gắn nhãn "Output X" / "Output Y", judge không biết cái nào là AMAP. Map ngược nhãn sau khi chấm xong.

---

## 8. Kiểm soát nhiễu (confounders)

| Nhiễu | Xử lý |
|---|---|
| Rò context giữa 2 arm | **Session tách rời hoàn toàn** mỗi arm; không tái dùng hội thoại |
| Thứ tự arm thiên vị | **Counterbalance** thứ tự A/B giữa các ticket |
| Judge thiên vị nhãn AMAP | **Bịt mắt** judge (§7.1) |
| R1 — agent đã thấy repo | PR merge sau cutoff / repo ít nổi; ghi `merge_date` + `model_version` (§3.3) |
| Baseline bị làm yếu (strawman) | Nội dung entry-point baseline **đóng băng + chép vào report** (§2.1, Appendix B) |
| Knowledge-snapshot mớm sẵn cho Arm A | Arm A chạy `active/` rỗng; nếu `long-term/` có sẵn nội dung của repo target thì cũng reset về skeleton để cold-start trung thực |

**Bắt buộc ghi để tái lập mỗi run:** model version, `repo@commit_sha`, `PR#`, `merge_date`, thứ tự arm, nội dung entry-point baseline.

---

## 9. Verdict rule + triage

### 9.1 Decision rule (pre-registered — chốt TRƯỚC khi chạy, đánh giá THEO SIZE)

Để tránh rationalize sau khi thấy số, chốt trước quy tắc (ngưỡng chỉnh được ở bước plan, nhưng **đóng băng trước khi chạy**). Quy tắc áp dụng **cho từng size riêng** (tiny/standard/complex), vì giá trị AMAP kỳ vọng tăng theo độ phức tạp task:

- **AMAP "đáng" ở một size** nếu: median(M1) cải thiện **≥ 1 điểm** *hoặc* recall(M2) cao hơn rõ rệt so với baseline, **VÀ** overhead token (M5) trong giới hạn chấp nhận (đề xuất: ≤ 3× baseline).
- **AMAP "không đáng" ở một size** nếu: chất lượng (M1–M3) ngang/thua baseline dù tốn thêm token/thời gian. *(Kỳ vọng trước: tiny rơi vào nhóm này — đó là tín hiệu hợp lệ, không phải điểm trừ.)*
- **"Mờ"** nếu hỗn hợp → thêm ticket cùng size (§5) rồi đánh giá lại.

### 9.2 Cấu trúc verdict — gradient theo size + break-even

Verdict KHÔNG phải một câu yes/no chung, mà là **gradient giá trị theo size** (mỗi ticket một size):

| Size | ΔM1 | ΔM2(recall) | ΔM3 | ΔM5(token) | Đáng? |
|------|-----|-------------|-----|------------|-------|
| tiny | | | | | |
| standard | | | | | |
| complex | | | | | |

Output chính = **break-even point**: *size nhỏ nhất mà AMAP bắt đầu "đáng".*

**Đây là input trực tiếp cho U1 — workflow tiering:** size **dưới** break-even nên tier bỏ bớt explore nặng (chạy nhẹ như baseline); size **từ** break-even trở lên giữ full pipeline. Nhờ vậy ngay cả kết quả "tiny không đáng" cũng thành bằng chứng định lượng cho chỗ cắt tier, thay vì đoán.

### 9.3 Triage friction (kế thừa U0)
Mỗi điểm ma sát quan sát được trong lúc chạy phân loại **một** trong ba nhãn, để chặn rework vô hạn:
- `(U1-tiering)` — do thiếu phân tầng task.
- `(patch-SP1)` — bug/khựng của bộ máy hiện tại, tách thành patch riêng.
- `(issue-mới)` — vấn đề mới, mở issue theo dõi.

Không fix friction trong phạm vi protocol này.

---

## 10. Deliverable & ranh giới với UP1

- **Deliverable P1.1 (batch này):** *chỉ* file spec protocol này — gồm rubric (§7.1) + report template (Appendix A) nhúng sẵn, chạy tay được ngay.
- **`litmus-report`** là output khi *chạy* protocol (việc làm tay, tốn thời gian thật), **không** phải sản phẩm của batch này.
- **Ranh giới với UP1:** P1.1 dừng ở protocol + lần chạy tay đầu tiên. **UP1** mới biến rubric đã-được-chứng-minh thành **harness tái lập + scorer (LLM-judge tự động) + cắm CI**. Không có P1.1 thì UP1 không có nền đã validate.

---

## Appendix A — Report template (điền khi chạy)

```
# Litmus Report — <ngày>

## Setup (tái lập)
- Model version: <...>
- Repo target: <repo@commit_sha>
- Tickets: T1 <PR#,size>, T2 <PR#,size>, T3 <PR#,size>
- Merge dates: <...>  (so với model cutoff: <...>)
- Decision rule (frozen): <copy §9.1>

## Per-run results
| Ticket | Size | Arm | M1 | M2(P/R) | M3 | M4 | M5(tok) | M6(min) |
|--------|------|-----|----|---------|----|----|---------|---------|
| T1 | tiny | AMAP | | | | | | |
| T1 | tiny | baseline | | | | | | |
| ... (mọi tổ hợp ticket×arm) | | | | | | | | |

## Verdict — gradient theo size
| Ticket | Size | ΔM1 | ΔM2(recall) | ΔM3 | ΔM5(token) | ΔM6 | Đáng? |
|--------|------|-----|-------------|-----|------------|-----|-------|
| T1 | tiny | | | | | | |
| T2 | standard | | | | | | |
| T3 | complex | | | | | | |

- **Break-even point** (size nhỏ nhất AMAP "đáng"): <...>
- **Khuyến nghị U1 tiering:** size < break-even → tier nhẹ; size ≥ break-even → full pipeline.

## Friction log (triaged)
- <điểm ma sát> → (U1-tiering | patch-SP1 | issue-mới)

## Spot-check (human)
- <ca đã kiểm + có lệch judge không>
```

## Appendix B — Baseline entry-point (đóng băng, chép nguyên văn khi chạy)

```
# <CLAUDE.md hoặc AGENTS.md baseline — nội dung mỏng cố định>
# Build/test: <...>
# Conventions: <naming, layering>
# Architecture (≤150 từ): <...>
```
