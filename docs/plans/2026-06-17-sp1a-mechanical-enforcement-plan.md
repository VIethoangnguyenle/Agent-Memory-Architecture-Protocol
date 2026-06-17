# SP1a — Mechanical Enforcement Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Rule Projector that turns the mechanically-checkable parts of `author-dna.yaml` + `conventions.yaml` into a Checkstyle ruleset, enforced at git pre-commit, with a sync-check so the ruleset never goes stale as the living DNA evolves.

**Architecture:** Python tool in `.agent/tools/rule-projector/`. Pipeline: `DNA+conventions → IR (neutral JSON) → checkstyle.generated.xml`. Two projection layers — a structural floor (`complexity_thresholds` + naming, always present) and optional `check_spec` enrichment. Tested entirely with YAML→JSON→XML fixtures (no Java needed). The git hook + real Checkstyle run is verified later in the target Java project.

**Tech Stack:** Python 3.11+, PyYAML, jsonschema, pytest. Output consumed by Checkstyle (Java side).

**Spec:** [docs/specs/2026-06-17-sp1a-mechanical-enforcement-design.md](../specs/2026-06-17-sp1a-mechanical-enforcement-design.md)

---

## Conventions

- Work from repo root `/home/zane/Desktop/agent-memory-arch-v3`, on a feature branch `sp1a-mechanical-enforcement` (create it in Task 0).
- All tool code lives under `.agent/tools/rule-projector/`. Run tests with `python -m pytest .agent/tools/rule-projector/tests/ -v`.
- Commit after each task. End commit messages with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

---

## Task 0: Scaffold tool + branch + deps

**Files:**
- Create: `.agent/tools/rule-projector/{requirements.txt, README.md, __init__.py, generated/.gitkeep}`
- Create: `.agent/tools/rule-projector/{backends/__init__.py, tests/__init__.py, tests/fixtures/.gitkeep}`
- Modify: `.gitignore`

- [ ] **Step 1: Branch**

```bash
cd /home/zane/Desktop/agent-memory-arch-v3
git checkout -b sp1a-mechanical-enforcement
```

- [ ] **Step 2: Create dirs + files**

```bash
mkdir -p .agent/tools/rule-projector/backends .agent/tools/rule-projector/tests/fixtures .agent/tools/rule-projector/generated
cd .agent/tools/rule-projector
touch __init__.py backends/__init__.py tests/__init__.py generated/.gitkeep tests/fixtures/.gitkeep
printf 'pyyaml>=6.0\njsonschema>=4.0\npytest>=7.0\n' > requirements.txt
printf '# rule-projector\n\nDNA + conventions → IR (neutral JSON) → checkstyle.generated.xml.\nSee docs/specs/2026-06-17-sp1a-mechanical-enforcement-design.md\n\nRun: `python projector.py --dna <path> --conventions <path> --out generated/`\nTest: `python -m pytest tests/ -v`\n' > README.md
cd -
```

- [ ] **Step 3: gitignore generated output**

Add to `.gitignore` (use Edit tool, append a line):
```
.agent/tools/rule-projector/generated/*
!.agent/tools/rule-projector/generated/.gitkeep
```

- [ ] **Step 4: Verify deps + pytest runs**

> Deps (pyyaml, jsonschema, pytest) are ALREADY installed system-wide in this environment.
> This env is PEP-668 externally-managed — do NOT `pip install` (it errors). If a dep were
> missing, use `pip install <pkg> --break-system-packages` or a venv. `requirements.txt` is
> kept as documentation of deps.

Run:
```bash
python3 -c "import yaml,jsonschema,pytest; print('deps ok')"
python3 -m pytest .agent/tools/rule-projector/tests/ -v
```
Expected: "deps ok"; pytest runs, "no tests ran" (exit code 5) — OK at this stage.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(sp1a): scaffold rule-projector tool + deps

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 1: IR JSON Schema + fixtures

**Files:**
- Create: `.agent/tools/rule-projector/ir_schema.json`
- Create: `.agent/tools/rule-projector/tests/fixtures/{sample-author-dna.yaml, sample-conventions.yaml, expected-ir.json}`
- Create: `.agent/tools/rule-projector/tests/test_schema.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_schema.py`:
```python
import json
from pathlib import Path
import jsonschema

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def _load(p):
    return json.loads((Path(p)).read_text())

def test_expected_ir_validates_against_schema():
    schema = _load(ROOT / "ir_schema.json")
    ir = _load(HERE / "fixtures" / "expected-ir.json")
    jsonschema.validate(ir, schema)  # raises if invalid

def test_unknown_ir_rule_fails_schema():
    schema = _load(ROOT / "ir_schema.json")
    bad = {"version": "1.0", "source_hash": "0"*64, "sources": [], "rules": [
        {"id": "x", "ir_rule": "NOT_A_RULE", "severity": "error", "params": {}}]}
    try:
        jsonschema.validate(bad, schema)
        assert False, "should have raised"
    except jsonschema.ValidationError:
        pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest .agent/tools/rule-projector/tests/test_schema.py -v`
Expected: FAIL (ir_schema.json / fixtures missing).

- [ ] **Step 3: Write ir_schema.json**

Create `ir_schema.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["version", "source_hash", "sources", "rules"],
  "additionalProperties": true,
  "properties": {
    "version": {"const": "1.0"},
    "generated_at": {"type": "string"},
    "source_hash": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
    "sources": {"type": "array", "items": {"type": "string"}},
    "rules": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "ir_rule", "severity", "params"],
        "additionalProperties": true,
        "properties": {
          "id": {"type": "string"},
          "ir_rule": {"enum": ["max_if_nesting","max_for_nesting","max_method_lines","max_cyclomatic","forbid_else","naming_regex","require_javadoc_tag"]},
          "severity": {"enum": ["error","warning","info"]},
          "params": {"type": "object"},
          "source_ref": {"type": "string"}
        }
      }
    }
  }
}
```

- [ ] **Step 4: Write fixtures**

Create `tests/fixtures/sample-author-dna.yaml`:
```yaml
meta:
  author: "sample"
  status: approved
complexity_thresholds:
  max_nesting_depth: 1
  max_method_branches: 3
  max_lines_per_method: 30
  confirmed: true
hard_principles:
  - id: HP-6
    name: "Zero Nesting"
    agent_action: REJECT_AND_PROPOSE
    mechanically_checkable: true
    check_spec:
      - ir_rule: max_for_nesting
        params: { max: 0 }
  - id: HP-7
    name: "No Else"
    agent_action: REJECT_AND_PROPOSE
    mechanically_checkable: true
    check_spec:
      - ir_rule: forbid_else
        params: { severity_override: warning }
  - id: HP-5
    name: "Factory boundary"
    agent_action: FLAG_AND_WARN
    mechanically_checkable: false
style_preferences:
  - id: SP-5
    name: "Javadoc tags"
    mechanically_checkable: true
    check_spec:
      - ir_rule: require_javadoc_tag
        params: { tags: ["@author", "@since"], scope: ["public", "protected"] }
```

Create `tests/fixtures/sample-conventions.yaml`:
```yaml
meta:
  status: approved
naming_patterns:
  - target: TypeName
    pattern: "^[A-Z][a-zA-Z0-9]*$"
  - target: MethodName
    pattern: "^[a-z][a-zA-Z0-9]*$"
```

Create `tests/fixtures/expected-ir.json` (note: `generated_at` omitted — tests ignore it; `source_hash` is a fixed 64-char placeholder the projector test will override):
```json
{
  "version": "1.0",
  "source_hash": "0000000000000000000000000000000000000000000000000000000000000000",
  "sources": ["sample-author-dna.yaml", "sample-conventions.yaml"],
  "rules": [
    {"id": "HP-6.max_for_nesting", "ir_rule": "max_for_nesting", "severity": "error", "params": {"max": 0}, "source_ref": "author-dna.yaml#HP-6"},
    {"id": "HP-7.forbid_else", "ir_rule": "forbid_else", "severity": "warning", "params": {"severity_override": "warning"}, "source_ref": "author-dna.yaml#HP-7"},
    {"id": "SP-5.require_javadoc_tag", "ir_rule": "require_javadoc_tag", "severity": "warning", "params": {"tags": ["@author", "@since"], "scope": ["public", "protected"]}, "source_ref": "author-dna.yaml#SP-5"},
    {"id": "threshold.max_if_nesting", "ir_rule": "max_if_nesting", "severity": "error", "params": {"max": 1}, "source_ref": "author-dna.yaml#complexity_thresholds"},
    {"id": "threshold.max_cyclomatic", "ir_rule": "max_cyclomatic", "severity": "warning", "params": {"max": 3}, "source_ref": "author-dna.yaml#complexity_thresholds"},
    {"id": "threshold.max_method_lines", "ir_rule": "max_method_lines", "severity": "warning", "params": {"max": 30}, "source_ref": "author-dna.yaml#complexity_thresholds"},
    {"id": "naming.TypeName", "ir_rule": "naming_regex", "severity": "warning", "params": {"target": "TypeName", "pattern": "^[A-Z][a-zA-Z0-9]*$"}, "source_ref": "conventions.yaml#naming_patterns"},
    {"id": "naming.MethodName", "ir_rule": "naming_regex", "severity": "warning", "params": {"target": "MethodName", "pattern": "^[a-z][a-zA-Z0-9]*$"}, "source_ref": "conventions.yaml#naming_patterns"}
  ]
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest .agent/tools/rule-projector/tests/test_schema.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat(sp1a): IR JSON schema + sample fixtures

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: projector.py — core projection (thresholds + principles + naming)

**Files:**
- Create: `.agent/tools/rule-projector/projector.py`
- Create: `.agent/tools/rule-projector/tests/test_projector.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_projector.py`:
```python
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import projector  # noqa: E402

DNA = HERE / "fixtures" / "sample-author-dna.yaml"
CONV = HERE / "fixtures" / "sample-conventions.yaml"

def _norm(rules):
    # compare ignoring order
    return sorted([json.dumps(r, sort_keys=True) for r in rules])

def test_build_ir_matches_expected_rules():
    ir = projector.build_ir(str(DNA), str(CONV))
    expected = json.loads((HERE / "fixtures" / "expected-ir.json").read_text())
    assert _norm(ir["rules"]) == _norm(expected["rules"])

def test_semantic_principle_excluded():
    ir = projector.build_ir(str(DNA), str(CONV))
    ids = [r["id"] for r in ir["rules"]]
    assert not any("HP-5" in i for i in ids)  # mechanically_checkable: false → excluded
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest .agent/tools/rule-projector/tests/test_projector.py -v`
Expected: FAIL (no module `projector`).

- [ ] **Step 3: Write projector.py**

Create `projector.py`:
```python
"""Rule Projector: author-dna.yaml + conventions.yaml -> IR (neutral JSON)."""
import argparse, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
import yaml

IR_VERSION = "1.0"

def _load_yaml(path):
    return yaml.safe_load(Path(path).read_text()) or {}

def _approved(doc):
    meta = doc.get("meta", {}) if isinstance(doc, dict) else {}
    return meta.get("status") == "approved"

def _rule(rid, ir_rule, severity, params, source_ref):
    return {"id": rid, "ir_rule": ir_rule, "severity": severity,
            "params": params, "source_ref": source_ref}

def _severity(agent_action, override=None):
    if override:
        return override
    if agent_action and agent_action.startswith("REJECT"):
        return "error"
    return "warning"

def project_thresholds(thresholds):
    rules = []
    if not thresholds:
        return rules
    ref = "author-dna.yaml#complexity_thresholds"
    if "max_nesting_depth" in thresholds:
        rules.append(_rule("threshold.max_if_nesting", "max_if_nesting", "error",
                           {"max": thresholds["max_nesting_depth"]}, ref))
    if "max_method_branches" in thresholds:
        rules.append(_rule("threshold.max_cyclomatic", "max_cyclomatic", "warning",
                           {"max": thresholds["max_method_branches"]}, ref))
    if "max_lines_per_method" in thresholds:
        rules.append(_rule("threshold.max_method_lines", "max_method_lines", "warning",
                           {"max": thresholds["max_lines_per_method"]}, ref))
    return rules

def project_principles(principles):
    rules = []
    for p in principles or []:
        if not p.get("mechanically_checkable"):
            continue
        pid = p.get("id", "UNKNOWN")
        sev = _severity(p.get("agent_action"))
        for spec in p.get("check_spec", []):
            params = dict(spec.get("params", {}))
            override = params.get("severity_override")
            rules.append(_rule(f"{pid}.{spec['ir_rule']}", spec["ir_rule"],
                              _severity(p.get("agent_action"), override),
                              params, f"author-dna.yaml#{pid}"))
    return rules

def project_naming(conventions):
    rules = []
    for n in (conventions.get("naming_patterns") or []):
        target = n["target"]
        rules.append(_rule(f"naming.{target}", "naming_regex", "warning",
                          {"target": target, "pattern": n["pattern"]},
                          "conventions.yaml#naming_patterns"))
    return rules

def _dedupe(rules):
    seen, out = set(), []
    for r in rules:
        key = (r["ir_rule"], r["params"].get("target"))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out

def compute_source_hash(paths):
    h = hashlib.sha256()
    for p in paths:
        h.update(Path(p).read_bytes())
    return h.hexdigest()

def build_ir(dna_path, conventions_path):
    dna = _load_yaml(dna_path)
    conv = _load_yaml(conventions_path)
    rules = []
    rules += project_principles(dna.get("hard_principles"))
    rules += project_principles(dna.get("style_preferences"))
    rules += project_thresholds(dna.get("complexity_thresholds"))
    if _approved(conv):
        rules += project_naming(conv)
    rules = _dedupe(rules)
    return {
        "version": IR_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_hash": compute_source_hash([dna_path, conventions_path]),
        "sources": [Path(dna_path).name, Path(conventions_path).name],
        "rules": rules,
    }

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dna", required=True)
    ap.add_argument("--conventions", required=True)
    ap.add_argument("--out", default="generated")
    args = ap.parse_args(argv)
    ir = build_ir(args.dna, args.conventions)
    out = Path(args.out) / "rules.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ir, indent=2, ensure_ascii=False))
    print(f"IR written: {out} ({len(ir['rules'])} rules)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

> Note: `complexity_thresholds` has `confirmed: true` but no `status`; it is projected unconditionally (it lives inside the approved DNA doc). `conventions` naming is gated on `_approved(conv)`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest .agent/tools/rule-projector/tests/ -v`
Expected: all passed (schema + projector).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(sp1a): projector core — thresholds + check_spec + naming projection

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: projector — robustness (skip-draft, missing check_spec floor)

**Files:**
- Modify: `.agent/tools/rule-projector/tests/test_projector.py` (add tests)
- Create: `.agent/tools/rule-projector/tests/fixtures/bare-author-dna.yaml`

- [ ] **Step 1: Write failing tests + bare fixture**

Create `tests/fixtures/bare-author-dna.yaml` (NO check_spec — only structural floor):
```yaml
meta:
  status: approved
complexity_thresholds:
  max_nesting_depth: 1
  max_lines_per_method: 30
hard_principles:
  - id: HP-1
    name: "Some semantic principle"
    agent_action: FLAG_AND_WARN
```

Append to `tests/test_projector.py`:
```python
def test_bare_dna_still_projects_floor():
    bare = HERE / "fixtures" / "bare-author-dna.yaml"
    ir = projector.build_ir(str(bare), str(CONV))
    irules = {r["ir_rule"] for r in ir["rules"]}
    assert "max_if_nesting" in irules        # from thresholds floor
    assert "max_method_lines" in irules
    assert "naming_regex" in irules
    # no check_spec principles → none of those rules
    assert "forbid_else" not in irules

def test_draft_conventions_skipped():
    import tempfile, textwrap
    draft = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
    draft.write(textwrap.dedent('''
        meta:
          status: draft
        naming_patterns:
          - target: TypeName
            pattern: "^X.*$"
    '''))
    draft.close()
    ir = projector.build_ir(str(DNA), draft.name)
    assert not any(r["ir_rule"] == "naming_regex" for r in ir["rules"])
```

- [ ] **Step 2: Run to verify pass (logic already supports it)**

Run: `python -m pytest .agent/tools/rule-projector/tests/test_projector.py -v`
Expected: all passed (the Task-2 code already handles floor + draft-skip; these tests lock that behavior).

If any FAIL, fix `projector.py` until green (do not weaken the test).

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "test(sp1a): lock floor-projection + draft-skip robustness

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: backends/checkstyle.py — IR → checkstyle.generated.xml

**Files:**
- Create: `.agent/tools/rule-projector/backends/checkstyle.py`
- Create: `.agent/tools/rule-projector/tests/fixtures/expected-checkstyle.xml`
- Create: `.agent/tools/rule-projector/tests/test_checkstyle.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_checkstyle.py`:
```python
import json, sys, re
from pathlib import Path
import xml.dom.minidom as minidom

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from backends import checkstyle  # noqa: E402

def _norm(xml_str):
    # normalize whitespace for comparison
    return re.sub(r">\s+<", "><", xml_str.strip())

def test_ir_renders_wellformed_xml():
    ir = json.loads((HERE / "fixtures" / "expected-ir.json").read_text())
    xml = checkstyle.ir_to_checkstyle(ir)
    minidom.parseString(xml)  # raises if not well-formed

def test_forbid_else_is_regexp_warning():
    ir = {"version":"1.0","source_hash":"0"*64,"sources":[],"rules":[
        {"id":"HP-7.forbid_else","ir_rule":"forbid_else","severity":"warning","params":{},"source_ref":"author-dna.yaml#HP-7"}]}
    xml = checkstyle.ir_to_checkstyle(ir)
    assert "Regexp" in xml
    assert 'severity="warning"' in xml

def test_source_hash_embedded_in_header():
    ir = {"version":"1.0","source_hash":"abc123","sources":[],"rules":[]}
    xml = checkstyle.ir_to_checkstyle(ir)
    assert "source_hash=abc123" in xml

def test_nesting_maps_to_nestedifdepth():
    ir = {"version":"1.0","source_hash":"0"*64,"sources":[],"rules":[
        {"id":"t","ir_rule":"max_if_nesting","severity":"error","params":{"max":1},"source_ref":"x"}]}
    xml = checkstyle.ir_to_checkstyle(ir)
    assert "NestedIfDepth" in xml
    assert 'value="1"' in xml
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest .agent/tools/rule-projector/tests/test_checkstyle.py -v`
Expected: FAIL (no module `backends.checkstyle`).

- [ ] **Step 3: Write backends/checkstyle.py**

Create `backends/checkstyle.py`:
```python
"""IR -> Checkstyle config XML."""
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Maps a TreeWalker target to the Checkstyle module that lives under TreeWalker.
_NAMING_MODULES = {"TypeName", "MethodName", "MemberName", "ConstantName",
                   "LocalVariableName", "ParameterName"}

def _module(parent, name):
    return ET.SubElement(parent, "module", {"name": name})

def _prop(mod, name, value):
    ET.SubElement(mod, "property", {"name": name, "value": str(value)})

def _emit_rule(tw, rule):
    ir = rule["ir_rule"]
    p = rule.get("params", {})
    sev = rule["severity"]
    src = rule.get("source_ref", "")
    tw.append(ET.Comment(f" from: {src} ({rule['id']}) "))
    if ir == "max_if_nesting":
        m = _module(tw, "NestedIfDepth"); _prop(m, "max", p.get("max", 1)); _prop(m, "severity", sev)
    elif ir == "max_for_nesting":
        m = _module(tw, "NestedForDepth"); _prop(m, "max", p.get("max", 0)); _prop(m, "severity", sev)
    elif ir == "max_method_lines":
        m = _module(tw, "MethodLength"); _prop(m, "max", p.get("max", 30)); _prop(m, "countEmpty", "false"); _prop(m, "severity", sev)
    elif ir == "max_cyclomatic":
        m = _module(tw, "CyclomaticComplexity"); _prop(m, "max", p.get("max", 3)); _prop(m, "severity", sev)
    elif ir == "forbid_else":
        m = _module(tw, "Regexp"); _prop(m, "format", r"\}\s*else"); _prop(m, "illegalPattern", "true"); _prop(m, "severity", sev)
    elif ir == "naming_regex":
        target = p.get("target", "TypeName")
        if target not in _NAMING_MODULES:
            raise ValueError(f"Unsupported naming target: {target}")
        m = _module(tw, target); _prop(m, "format", p["pattern"]); _prop(m, "severity", sev)
    elif ir == "require_javadoc_tag":
        for tag in p.get("tags", []):
            m = _module(tw, "Regexp"); _prop(m, "format", tag); _prop(m, "illegalPattern", "false"); _prop(m, "severity", sev)
    else:
        raise ValueError(f"Unsupported ir_rule for checkstyle backend: {ir}")

def ir_to_checkstyle(ir):
    root = ET.Element("module", {"name": "Checker"})
    root.insert(0, ET.Comment(f" GENERATED by rule-projector — DO NOT EDIT. source_hash={ir.get('source_hash','')} "))
    tw = _module(root, "TreeWalker")
    for rule in ir.get("rules", []):
        _emit_rule(tw, rule)
    raw = ET.tostring(root, encoding="unicode")
    pretty = minidom.parseString(raw).toprettyxml(indent="  ")
    # prepend Checkstyle DOCTYPE
    body = pretty.split("?>", 1)[1].lstrip()
    return ('<?xml version="1.0"?>\n'
            '<!DOCTYPE module PUBLIC '
            '"-//Checkstyle//DTD Checkstyle Configuration 1.3//EN" '
            '"https://checkstyle.org/dtds/configuration_1_3.dtd">\n' + body)

def main(argv=None):
    import argparse, json
    from pathlib import Path
    ap = argparse.ArgumentParser()
    ap.add_argument("--ir", required=True)
    ap.add_argument("--out", default="generated/checkstyle.generated.xml")
    args = ap.parse_args(argv)
    ir = json.loads(Path(args.ir).read_text())
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(ir_to_checkstyle(ir))
    print(f"checkstyle written: {args.out}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
```

- [ ] **Step 4: Generate the expected-checkstyle.xml fixture**

Run (capture real output as the golden fixture, then eyeball it):
```bash
cd .agent/tools/rule-projector
python -c "import json,sys; sys.path.insert(0,'.'); from backends import checkstyle; print(checkstyle.ir_to_checkstyle(json.load(open('tests/fixtures/expected-ir.json'))))" > tests/fixtures/expected-checkstyle.xml
cat tests/fixtures/expected-checkstyle.xml
cd -
```
Verify by eye: contains `NestedIfDepth value="1"`, `NestedForDepth`, `MethodLength`, `CyclomaticComplexity`, `Regexp` (else + javadoc tags), `TypeName`/`MethodName`, trace comments, and the `source_hash=` header.

- [ ] **Step 5: Add a golden-file test**

Append to `tests/test_checkstyle.py`:
```python
def test_matches_golden_fixture():
    ir = json.loads((HERE / "fixtures" / "expected-ir.json").read_text())
    xml = checkstyle.ir_to_checkstyle(ir)
    golden = (HERE / "fixtures" / "expected-checkstyle.xml").read_text()
    assert _norm(xml) == _norm(golden)
```

- [ ] **Step 6: Run all tests**

Run: `python -m pytest .agent/tools/rule-projector/tests/ -v`
Expected: all passed.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "feat(sp1a): checkstyle backend — IR to checkstyle.generated.xml + golden test

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: git hook + installer + sync-check

**Files:**
- Create: `.agent/tools/rule-projector/hooks/pre-commit.sh`
- Create: `.agent/tools/rule-projector/install.sh`
- Create: `.agent/tools/rule-projector/tests/test_sync_check.py`

- [ ] **Step 1: Write the failing test (sync-check behavior)**

Create `tests/test_sync_check.py`:
```python
import subprocess, sys, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def _gen(tmp_path, dna, conv):
    sys.path.insert(0, str(ROOT))
    import projector
    from backends import checkstyle
    ir = projector.build_ir(str(dna), str(conv))
    (tmp_path / "rules.json").write_text(json.dumps(ir))
    xml = checkstyle.ir_to_checkstyle(ir)
    (tmp_path / "checkstyle.generated.xml").write_text(xml)
    return ir["source_hash"]

def test_sync_check_detects_stale(tmp_path):
    dna = HERE / "fixtures" / "sample-author-dna.yaml"
    conv = HERE / "fixtures" / "sample-conventions.yaml"
    emitted = _gen(tmp_path, dna, conv)
    xml = (tmp_path / "checkstyle.generated.xml").read_text()
    assert f"source_hash={emitted}" in xml
    # simulate DNA change: recompute hash from a mutated copy
    import projector
    mutated = tmp_path / "mutated-dna.yaml"
    mutated.write_text(dna.read_text() + "\n# changed\n")
    new_hash = projector.compute_source_hash([str(mutated), str(conv)])
    assert new_hash != emitted  # stale would be detected by the hook
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest .agent/tools/rule-projector/tests/test_sync_check.py -v`
Expected: FAIL until `compute_source_hash` import path resolves — actually it should PASS using existing projector; if it fails, fix the import. (This test pins the contract the hook relies on.)

- [ ] **Step 3: Write hooks/pre-commit.sh**

Create `hooks/pre-commit.sh`:
```sh
#!/bin/sh
# AMAP rule-projector pre-commit gate. Installed by install.sh into target Java project.
# Config via env (set by install.sh): DNA_PATH, CONV_PATH, RULESET_PATH
set -e
: "${DNA_PATH:?DNA_PATH not set}"
: "${CONV_PATH:?CONV_PATH not set}"
: "${RULESET_PATH:?RULESET_PATH not set}"

# 1. Sync-check
CUR=$(cat "$DNA_PATH" "$CONV_PATH" | sha256sum | cut -d' ' -f1)
EMB=$(grep -o 'source_hash=[a-f0-9]*' "$RULESET_PATH" | head -1 | cut -d= -f2)
if [ "$CUR" != "$EMB" ]; then
  echo "⛔ DNA/conventions changed but ruleset is stale."
  echo "   Run: python .agent/tools/rule-projector/projector.py --dna \"$DNA_PATH\" --conventions \"$CONV_PATH\" --out generated/"
  echo "   then regenerate checkstyle and commit the ruleset."
  exit 1
fi

# 2. Checkstyle on staged Java files
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.java$' || true)
if [ -n "$FILES" ]; then
  if ! command -v checkstyle >/dev/null 2>&1; then
    echo "⚠ checkstyle CLI not found — skipping mechanical lint (install checkstyle to enforce)."
    exit 0
  fi
  checkstyle -c "$RULESET_PATH" $FILES
fi
exit 0
```

- [ ] **Step 4: Write install.sh**

Create `install.sh`:
```sh
#!/bin/sh
# Install the AMAP mechanical-enforcement pre-commit hook into a target Java project.
# Usage: install.sh <project_root> <dna_path> <conv_path>
set -e
PROJECT_ROOT="${1:?usage: install.sh <project_root> <dna_path> <conv_path>}"
DNA_PATH="${2:?dna_path required}"
CONV_PATH="${3:?conv_path required}"
HERE=$(cd "$(dirname "$0")" && pwd)
RULESET_PATH="$PROJECT_ROOT/.agent/tools/rule-projector/generated/checkstyle.generated.xml"

# 1. Generate ruleset
python "$HERE/projector.py" --dna "$DNA_PATH" --conventions "$CONV_PATH" --out "$PROJECT_ROOT/.agent/tools/rule-projector/generated"
python "$HERE/backends/checkstyle.py" --ir "$PROJECT_ROOT/.agent/tools/rule-projector/generated/rules.json" --out "$RULESET_PATH"

# 2. Install hook with config baked in
HOOK="$PROJECT_ROOT/.git/hooks/pre-commit"
{
  echo "#!/bin/sh"
  echo "export DNA_PATH='$DNA_PATH'"
  echo "export CONV_PATH='$CONV_PATH'"
  echo "export RULESET_PATH='$RULESET_PATH'"
  echo "exec sh '$HERE/hooks/pre-commit.sh'"
} > "$HOOK"
chmod +x "$HOOK"
echo "Installed pre-commit hook -> $HOOK"
```

- [ ] **Step 5: Make scripts executable + shellcheck syntax**

Run:
```bash
chmod +x .agent/tools/rule-projector/hooks/pre-commit.sh .agent/tools/rule-projector/install.sh
sh -n .agent/tools/rule-projector/hooks/pre-commit.sh && echo "pre-commit.sh syntax OK"
sh -n .agent/tools/rule-projector/install.sh && echo "install.sh syntax OK"
python -m pytest .agent/tools/rule-projector/tests/ -v
```
Expected: both "syntax OK"; all pytest passed.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat(sp1a): pre-commit hook + installer + sync-check

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Teach author-dna-builder to emit check_spec (producer side)

**Files:**
- Modify: `.agent/skills/author-dna-builder/SKILL.md`
- Create: `.agent/skills/author-dna-builder/references/check-spec-mapping.md`

- [ ] **Step 1: Add the principle→ir_rule mapping reference**

Create `.agent/skills/author-dna-builder/references/check-spec-mapping.md` documenting, for the generator, WHICH principles are mechanizable and the `check_spec` to emit. Include this table verbatim:

```markdown
# check_spec emission guide (producer side of SP1a contract)

When generating author-dna.yaml, for each principle that is mechanically checkable,
emit `mechanically_checkable: true` + `check_spec`. Supported ir_rules (SP1a):

| Principle pattern | ir_rule | params |
|---|---|---|
| "no/zero nested for" | max_for_nesting | { max: 0 } |
| "no/zero nested if beyond depth N" | max_if_nesting | { max: N, guard_exception: true } |
| "no else / guard clause only" | forbid_else | { severity_override: warning } |
| "method must be <= N lines" | (covered by complexity_thresholds.max_lines_per_method) | — |
| "max N branches/cyclomatic" | (covered by complexity_thresholds.max_method_branches) | — |
| "javadoc must have @author/@since" | require_javadoc_tag | { tags: [...], scope: [public, protected] } |
| naming rules | (emit in conventions.yaml naming_patterns) | — |

Principles WITHOUT a clean mechanical mapping (CoR, Template Method, Strategy, Factory
boundary, SOLID, config-driven, extraction) → set `mechanically_checkable: false`.
These stay semantic and are enforced by SP1b (subagent), not the linter.

After writing/updating approved DNA, regenerate the ruleset (see SP1a §3.2):
`python .agent/tools/rule-projector/projector.py --dna <dna> --conventions <conv> --out generated/`
then the checkstyle backend.
```

- [ ] **Step 2: Reference it from SKILL.md**

In `.agent/skills/author-dna-builder/SKILL.md`, add a subsection (use Edit tool) under the DNA-emission section stating: when emitting `hard_principles`/`style_preferences`, consult `references/check-spec-mapping.md` and emit `mechanically_checkable` + `check_spec` for mechanizable principles; after approval, trigger ruleset regeneration. Keep the existing style.

- [ ] **Step 3: Verify reference is wired**

Run:
```bash
grep -n "check-spec-mapping" .agent/skills/author-dna-builder/SKILL.md && echo "wired" || echo "FAIL"
```
Expected: prints a line + `wired`.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat(sp1a): teach author-dna-builder to emit check_spec (producer contract)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Wire regeneration into the living-DNA update path

**Files:**
- Modify: `.agent/rules/rules-guard.md` (R-DNA-7), `.agent/skills/knowledge-curator/SKILL.md`

- [ ] **Step 1: Add regen step to R-DNA-7**

In `.agent/rules/rules-guard.md`, in R-DNA-7 (teaching moment capture), after the "write to author-dna.yaml, confirmed: true" step, add (Edit tool): when the captured principle is mechanically checkable, also emit `check_spec` (per `author-dna-builder/references/check-spec-mapping.md`) and run the rule-projector to regenerate the ruleset in-session (SP1a §3.2 active path).

- [ ] **Step 2: Add regen step to knowledge-curator**

In `.agent/skills/knowledge-curator/SKILL.md`, where it updates DNA/snapshot, add a note: after any approved DNA change, call `projector.py` to regenerate the ruleset; the pre-commit sync-check is the backstop.

- [ ] **Step 3: Verify**

Run:
```bash
grep -n "rule-projector\|projector.py" .agent/rules/rules-guard.md .agent/skills/knowledge-curator/SKILL.md && echo "wired" || echo "FAIL"
```
Expected: prints matching lines + `wired`.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat(sp1a): wire ruleset regeneration into R-DNA-7 + knowledge-curator update path

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Update sample DNA to illustrate schema + final verification

**Files:**
- Modify: `.knowledge-layer/long-term/author-dna.yaml`, `.agent/tools/README.md`

- [ ] **Step 1: Add check_spec to the real sample DNA (illustrative)**

In `.knowledge-layer/long-term/author-dna.yaml` (use Edit tool), add `mechanically_checkable: true` + `check_spec` to the principles that map cleanly:
- HP-6 (Zero Nesting): `check_spec: [{ir_rule: max_for_nesting, params: {max: 0}}]`
- HP-7 (No Else): `check_spec: [{ir_rule: forbid_else, params: {severity_override: warning}}]`
- SP-5 (Javadoc): `check_spec: [{ir_rule: require_javadoc_tag, params: {tags: ["@author","@since"], scope: ["public","protected"]}}]`

Leave semantic principles (HP-1/2/3/5/8/9/10/11) as-is (they default to not mechanically_checkable). Do NOT change any principle's wording — only add the two metadata fields.

- [ ] **Step 2: Run projector against the REAL sample DNA**

Run:
```bash
python .agent/tools/rule-projector/projector.py \
  --dna .knowledge-layer/long-term/author-dna.yaml \
  --conventions .knowledge-layer/long-term/conventions.yaml \
  --out .agent/tools/rule-projector/generated
python .agent/tools/rule-projector/backends/checkstyle.py \
  --ir .agent/tools/rule-projector/generated/rules.json \
  --out .agent/tools/rule-projector/generated/checkstyle.generated.xml
echo "=== generated rules ==="; python -c "import json;print(len(json.load(open('.agent/tools/rule-projector/generated/rules.json'))['rules']),'rules')"
python -c "import xml.dom.minidom as m; m.parse('.agent/tools/rule-projector/generated/checkstyle.generated.xml'); print('XML well-formed')"
```
Expected: prints N rules and "XML well-formed". (Output is gitignored — this is a smoke test.)

- [ ] **Step 3: Update .agent/tools/README.md**

Replace the placeholder content of `.agent/tools/README.md` to point at `rule-projector/` and summarize its purpose (DNA→IR→checkstyle, run/test commands).

- [ ] **Step 4: Full verification gate (spec §11)**

Run:
```bash
echo "=== 2. all tests ==="; python -m pytest .agent/tools/rule-projector/tests/ -v
echo "=== 1,3. schema validates generated IR ==="; python -c "import json,jsonschema; s=json.load(open('.agent/tools/rule-projector/ir_schema.json')); ir=json.load(open('.agent/tools/rule-projector/generated/rules.json')); jsonschema.validate(ir,s); print('IR valid')"
echo "=== 5. forbid_else warning ==="; grep -A2 'from: author-dna.yaml#HP-7' .agent/tools/rule-projector/generated/checkstyle.generated.xml | grep -q 'Regexp' && echo OK
echo "=== 6. trace comments ==="; grep -c 'from: author-dna.yaml' .agent/tools/rule-projector/generated/checkstyle.generated.xml
echo "=== 9. skills wired ==="; grep -lq "projector.py" .agent/rules/rules-guard.md && grep -lq "projector.py" .agent/skills/knowledge-curator/SKILL.md && echo "regen wired"
```
Expected: tests pass; "IR valid"; "OK"; trace-comment count > 0; "regen wired".

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(sp1a): illustrate check_spec in sample DNA + tools README + final verify

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review (run when writing the plan)

**Spec coverage:**
- §2 schema + check_spec → Task 1 (schema), Task 6/8 (emission + sample) ✓
- §3.1 robust-when-missing → Task 3 ✓
- §3.2 regeneration lifecycle → Task 7 (R-DNA-7 + curator) ✓
- §5 thresholds/principles/severity → Task 2 ✓
- §6 IR + source_hash + enum → Task 1 (schema), Task 2 (hash) ✓
- §7 checkstyle mapping table → Task 4 ✓
- §8 hook + installer + sync-check → Task 5 ✓
- §9 file layout → Task 0 ✓
- §10 test strategy → Tasks 1-5 (TDD throughout) ✓
- §11 verification gates → Task 8 Step 4 ✓
- §12 author-dna-builder + sample + gitignore + README → Tasks 0,6,8 ✓

**Placeholder scan:** No TBD/TODO; every code step has runnable code; every test step has assertions. ✓

**Type/name consistency:** `build_ir`, `project_thresholds/principles/naming`, `compute_source_hash`, `ir_to_checkstyle`, `_emit_rule` used consistently across Tasks 2-5. IR `ir_rule` enum identical in schema (Task 1), projector (Task 2), checkstyle backend (Task 4). severity values error/warning consistent. ✓
