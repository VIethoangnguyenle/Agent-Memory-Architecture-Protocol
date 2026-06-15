# Danh Sách Skills — Agent Memory Architecture Protocol

> Tài liệu này liệt kê toàn bộ 12 skills trong hệ thống AMAP.  
> Mỗi skill có file riêng biệt, mô tả chi tiết mục tiêu, trigger, quy trình và output.

---

## Tổng quan

| # | Skill | Mô tả ngắn | File |
|---|-------|-------------|------|
| 1 | [requirement-analyst](./01-requirement-analyst.md) | Phân tích ticket/tài liệu → REQUIREMENT.md chuẩn hoá | `01` |
| 2 | [spec-extract](./02-spec-extract.md) | Trích xuất spec từ wiki/Confluence/PRD | `02` |
| 3 | [db-explorer](./03-db-explorer.md) | Khám phá schema, constraint, trigger/procedure | `03` |
| 4 | [codebase-explorer](./04-codebase-explorer.md) | Map REQUIREMENT → module/service/file trong codebase | `04` |
| 5 | [architecture-reviewer](./05-architecture-reviewer.md) | Đánh giá xung đột kiến trúc và rủi ro | `05` |
| 6 | [knowledge-curator](./06-knowledge-curator.md) | Quản lý vòng đời knowledge — archive, rotate, snapshot | `06` |
| 7 | [convention-intelligence-builder](./07-convention-intelligence-builder.md) | Scan naming conventions và design patterns từ codebase | `07` |
| 8 | [author-dna-builder](./08-author-dna-builder.md) | Infer coding philosophy → interview → encode judgment layer | `08` |
| 9 | [spec-validator](./09-spec-validator.md) | Pre-apply gate + AC coverage check + post-apply verify | `09` |
| 10 | [infra-tdd](./10-infra-tdd.md) | Viết Technical Design Document 5 tầng hybrid | `10` |
| 11 | [document-writer](./11-document-writer.md) | Khung chuẩn viết tài liệu kỹ thuật (README, ADR, runbook…) | `11` |
| 12 | [openspec-skills](./12-openspec-skills.md) | OpenSpec Explore + Propose + Archive — quản lý change lifecycle | `12` |

---

## Luồng sử dụng Skills trong Pipeline

```
Ideation → Requirement → Architecture → Spec → Apply
   ↓            ↓              ↓          ↓       ↓
 (không      requirement   db-explorer  openspec  openspec
  skill)     -analyst    + codebase    -propose   -apply
                          -explorer
                        + architecture
                          -reviewer
```

**Lưu ý**: Các skill hoạt động theo thứ tự trong pipeline `/task`. Không gọi skill rời rạc ngoài ngữ cảnh pipeline trừ khi là utility standalone (ví dụ: `/convention-scan`, `/dna-scan`).
