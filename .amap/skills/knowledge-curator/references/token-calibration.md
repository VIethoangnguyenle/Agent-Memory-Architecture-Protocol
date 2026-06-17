# [M6] TOKEN_LOG Calibration

> Reference file — extracted from SKILL.md for progressive disclosure.

## Mục tiêu

Cải thiện độ chính xác của TOKEN_LOG.md theo thời gian bằng cách so sánh estimate với actual usage (nếu biết).

## Calibration Workflow

```
FUNCTION calibrate_token_estimates(ticket_id):
  INPUT: ticket_id — ticket vừa hoàn thành

  1. Đọc archive/{ticket_id}/TOKEN_LOG.md:
     - Lấy các estimate: Pha 1, Pha 2, Pha 3, TỔNG

  2. Nếu model API trả về actual token count (vd: Claude usage metadata):
     - So sánh: estimate vs actual cho từng pha
     - Tính ratio: actual / estimate

  3. Cập nhật calibration note vào .amap/knowledge/templates/TOKEN_LOG.tpl.md:
     - Section "Calibration History":
       | ticket_id | pha | estimate | actual | ratio | note |
     - Ghi average ratio sau 3+ tickets

  4. Nếu average ratio > 1.5 (estimate thấp hơn actual 50%+):
     → WARN: "TOKEN estimate đang thấp hơn thực tế. Cân nhắc nhân hệ số 1.5x."
     → Ghi vào AGENT_TRANSPARENCY: "[M6-CALIBRATE] Hệ số calibration: {ratio}x"

  5. Nếu không có actual data:
     → Bỏ qua calibration lần này, ghi note "no-actual-data"
```

## Token Estimate Guidelines (Calibrated)

Dùng khi không có actual data:

| Activity | Estimate (tokens) |
|----------|-------------------|
| Đọc REQUIREMENT.md (đầy đủ) | ~1,500–3,000 |
| Đọc EXPLORE_CONTEXT.md (đầy đủ) | ~2,000–5,000 |
| Đọc knowledge-snapshot.md (filtered) | ~1,000–4,000 |
| 1 KG tool call (query + result) | ~500–1,500 |
| 1 UA call | ~2,000–5,000 |
| Ghi REQUIREMENT.md | ~1,000–2,000 |
| Ghi EXPLORE_CONTEXT.md | ~1,500–3,000 |
| Sinh spec (openspec-propose) | ~3,000–8,000 |
| 1 file apply (small) | ~500–2,000 |
| 1 file apply (medium/large) | ~2,000–8,000 |

**Quy tắc estimate tổng**:
- Cộng tất cả activities trong pha.
- Thêm 20% overhead cho system prompt + tool call boilerplate.
- Nếu calibration ratio > 1.0: nhân thêm ratio đó.

## Cập nhật TOKEN_LOG trong Archive

Khi `archive_active_context()` chạy:
- Copy TOKEN_LOG.md vào archive (đã có trong STEPS).
- Sau khi calibrate (nếu có actual data): cập nhật bản archive với actual numbers.
- Ghi `calibration_status: done | no-data | pending` vào ARCHIVE_META.md.
