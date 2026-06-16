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

## adapters/ — reserved cho SP3 (tool-capability adapter)
## profiles/ — reserved cho SP4 (per-framework setup profile)
