# .agent/tools/

Executable tooling cho AMAP.

## rule-projector/ (SP1a — Mechanical Enforcement Layer)

Chiếu phần **kiểm-tra-được-bằng-máy** của `author-dna.yaml` + `conventions.yaml` thành
ruleset Checkstyle, enforce ở git pre-commit của dự án Java đích.

```
author-dna.yaml + conventions.yaml
   → projector.py            → IR (generated/rules.json, neutral JSON)
   → backends/checkstyle.py  → generated/checkstyle.generated.xml
   → hooks/pre-commit.sh (sync-check + checkstyle), cài bằng install.sh
```

- **Run**: `python3 .agent/tools/rule-projector/projector.py --dna <dna> --conventions <conv> --out <dir>`
  rồi `python3 .agent/tools/rule-projector/backends/checkstyle.py --ir <dir>/rules.json --out <dir>/checkstyle.generated.xml`
- **Test**: `python3 -m pytest .agent/tools/rule-projector/tests/ -v`
- **Cài vào dự án Java**: `.agent/tools/rule-projector/install.sh <project_root> <dna_path> <conv_path>`

Chi tiết: [docs/specs/2026-06-17-sp1a-mechanical-enforcement-design.md](../../docs/specs/2026-06-17-sp1a-mechanical-enforcement-design.md)

## microloop-orchestrator/ (SP1b — Coding Micro-loop + Extraction Review)

Viết lại Pha 3 thành vòng lặp subagent tuần tự context-sạch + extraction review (HP-10/11).
Lõi portable: **contract trung lập trên filesystem** + 3 execution tier; orchestrator
platform-agnostic, chỉ `dispatch` là điểm tier-specific.

```
tasks.md → topo-sort → TASK_QUEUE → per-task: TASK_HANDOFF → executor → mechanical gate (SP1a)
   → semantic surface-check → mark done → next ; hết task → extraction review → EXTRACTION_REPORT
```

- **Tier** khai báo ở `.agent/profiles/execution-mode.yaml`: `subagent` (Claude) ·
  `fresh-session` (Cursor/Antigravity) · `inline-reload` (fallback, luôn chạy được).
- **Test**: `python3 -m pytest .agent/tools/microloop-orchestrator/tests/ -v`

Chi tiết: [docs/specs/2026-06-17-sp1b-coding-microloop-design.md](../../docs/specs/2026-06-17-sp1b-coding-microloop-design.md)

## adapters/ — reserved cho SP3 (tool-capability adapter)
## profiles/ — reserved cho SP4 (per-framework setup profile)
