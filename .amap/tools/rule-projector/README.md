# rule-projector

DNA + conventions -> IR (neutral JSON) -> checkstyle.generated.xml.
See docs/specs/2026-06-17-sp1a-mechanical-enforcement-design.md

Run: `python3 projector.py --dna <path> --conventions <path> --out generated/`
Test: `python3 -m pytest tests/ -v`
