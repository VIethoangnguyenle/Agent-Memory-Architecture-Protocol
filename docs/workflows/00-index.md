# Danh Sách Workflows — Agent Memory Architecture Protocol

> Tài liệu này liệt kê toàn bộ 7 workflows trong hệ thống AMAP.

---

## Tổng quan

| # | Workflow | Command | Mô tả |
|---|----------|---------|--------|
| 1 | [Task Orchestrator](./01-task.md) | `/task` | Workflow chính 3 pha: Hiểu → Spec → Apply |
| 2 | [Idea to Task](./02-idea-to-task.md) | `/idea-to-task` | Chuyển ideation → draft ticket |
| 3 | [Index Source](./03-index-source.md) | `/index-source` | Lập chỉ mục Socraticode |
| 4 | [Approve Conventions](./04-approve-conventions.md) | `/approve-conventions` | Promote conventions.draft.yaml → approved |
| 5 | [OpenSpec Explore](./05-opsx-explore.md) | `/opsx:explore` | Thinking partner — khám phá ý tưởng |
| 6 | [OpenSpec Propose](./06-opsx-propose.md) | `/opsx:propose` | Tạo change + sinh artifacts |
| 7 | [OpenSpec Apply + Archive](./07-opsx-apply-archive.md) | `/opsx:apply` `/opsx:archive` | Implement tasks + archive change |

---

## Phân nhóm

### Nhóm 1 — Task Flow (bắt buộc qua `/task`)

```
/task <ý-tưởng> → Pha 1: Hiểu vấn đề
/task spec      → Pha 2: Sinh spec (OpenSpec propose)
/task apply     → Pha 3: Apply spec vào code
```

### Nhóm 2 — Utility Standalone

```
/idea-to-task       → Pre-task: Ideation → draft ticket
/index-source       → Lập chỉ mục Socraticode
/approve-conventions → Commit conventions.yaml
/convention-scan    → Scan conventions
/dna-scan           → Scan coding philosophy
/approve-dna        → Commit author-dna.yaml
```

### Nhóm 3 — OpenSpec Actions (trên change cụ thể)

```
/opsx:explore  → Thinking partner
/opsx:propose  → Sinh artifacts
/opsx:apply    → Implement tasks
/opsx:archive  → Archive change
```
