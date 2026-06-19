# Decision-Point Gates (Sub-spec #1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make AMAP's process/knowledge rules fire as just-in-time, evidence-checked gates instead of skippable prose — built on testable Python "evidence checkers" plus a bootstrap diet.

**Architecture:** A per-project `knowledge-index.yaml` (generated, not hard-coded) lets bootstrap load an index instead of full knowledge files. Four gates share one shape: at a decision point the agent writes a CHECKPOINT artifact whose required *evidence fields* are validated by a small deterministic Python checker (`gate-check`). Gates attach via the existing `pre_conditions` mechanism (R-Guard-1). Prose rules collapse into these gates.

**Tech Stack:** Python 3.9+ (stdlib + PyYAML, already a dep), pytest. Tests run with `/usr/bin/python3 -m pytest` (the venv has no pytest). Markdown for rules/procedures/templates.

**Spec:** `docs/superpowers/specs/2026-06-18-decision-point-gates-design.md`
**Program:** `docs/superpowers/specs/2026-06-18-amap-retro-fix-program-design.md`
**Branch:** `amap-retro-decision-gates`

**Genericity rule (BẮT BUỘC):** No project-specific values or artifact-type enums in framework source. The index generator must be generic (recursive `applies_to` walk — never hard-code container names like `hard_principles` or artifact types like `Factory`). See spec §3.3.

---

## File Structure

**New Python tools** (mirror existing `.amap/tools/*/` + `tests/` layout):
- `.amap/tools/knowledge-index/generate_index.py` — generate `knowledge-index.yaml` from the project's knowledge files.
- `.amap/tools/knowledge-index/__init__.py`, `.amap/tools/knowledge-index/tests/__init__.py`, `.amap/tools/knowledge-index/tests/test_generate_index.py`
- `.amap/tools/gate-check/gates.py` — pure evidence-validators (no I/O).
- `.amap/tools/gate-check/cli.py` — CLI wrapper returning exit codes.
- `.amap/tools/gate-check/__init__.py`, `.amap/tools/gate-check/tests/__init__.py`, `.amap/tools/gate-check/tests/test_gates.py`

**New prose/templates:**
- `.amap/knowledge/templates/KNOWLEDGE_CHECKPOINT.tpl.md`
- `.amap/procedures/decision-gate.md`

**Modified prose:**
- `.amap/procedures/bootstrap.md` (diet)
- `.amap/rules/rules-guard.md` (Gate #1), `.amap/rules/rules-flow.md` (Gate #3), `.amap/rules/rules-tool.md` (Gate #2, #4)
- `.amap/knowledge/templates/KNOWLEDGE_PACK.tpl.md` (Gate #2 slice section)

**Measurement:**
- `.amap/tools/gate-check/complexity.py` + test — count `[CRITICAL]` blocks & rule lines for net-negative.

---

## Task 1: knowledge-index generator (YAML stores)

**Files:**
- Create: `.amap/tools/knowledge-index/__init__.py` (empty)
- Create: `.amap/tools/knowledge-index/tests/__init__.py` (empty)
- Create: `.amap/tools/knowledge-index/generate_index.py`
- Test: `.amap/tools/knowledge-index/tests/test_generate_index.py`

- [ ] **Step 1: Write the failing test**

```python
# .amap/tools/knowledge-index/tests/test_generate_index.py
import importlib.util
from pathlib import Path

MOD = Path(__file__).resolve().parents[1] / "generate_index.py"
spec = importlib.util.spec_from_file_location("generate_index", MOD)
gi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gi)


def test_walk_extracts_entries_with_applies_to():
    tree = {
        "hard_principles": {
            "HP-1": {"name": "SOLID", "applies_to": ["Service"], "mechanically_checkable": False},
        },
        "style_preferences": {
            "SP-6": {"name": "staircase fields", "applies_to": ["Constructor"], "mechanically_checkable": True},
        },
        "noise": {"meta": {"status": "approved"}},  # no applies_to → ignored
    }
    entries = gi.walk_entries(tree, store="author-dna")
    ids = {e["id"]: e for e in entries}
    assert set(ids) == {"HP-1", "SP-6"}
    assert ids["HP-1"] == {
        "id": "HP-1", "store": "author-dna", "title": "SOLID",
        "applies_to": ["Service"], "mechanically_checkable": False,
    }
    assert ids["SP-6"]["mechanically_checkable"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest .amap/tools/knowledge-index/tests/test_generate_index.py -v`
Expected: FAIL — `generate_index.py` does not exist / `walk_entries` undefined.

- [ ] **Step 3: Write minimal implementation**

```python
# .amap/tools/knowledge-index/generate_index.py
"""Generate knowledge-index.yaml from a project's knowledge files.

GENERIC: never hard-codes container names or artifact types. Any dict node
that carries an 'applies_to' key becomes an index entry, keyed by its parent
key. See spec §3.3.
"""
import sys
from pathlib import Path

import yaml


def walk_entries(node, store, _key=None):
    """Recursively yield index entries for dicts that carry 'applies_to'."""
    out = []
    if isinstance(node, dict):
        if "applies_to" in node and _key is not None:
            out.append({
                "id": node.get("id", _key),
                "store": store,
                "title": node.get("name") or node.get("title") or _key,
                "applies_to": list(node.get("applies_to") or []),
                "mechanically_checkable": bool(node.get("mechanically_checkable", False)),
            })
        else:
            for k, v in node.items():
                out.extend(walk_entries(v, store, _key=k))
    elif isinstance(node, list):
        for item in node:
            out.extend(walk_entries(item, store, _key=_key))
    return out


def build_index(dna_path, conventions_path):
    entries = []
    for path, store in ((dna_path, "author-dna"), (conventions_path, "conventions")):
        p = Path(path)
        if p.is_file():
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            entries.extend(walk_entries(data, store))
    return entries


def main(argv=None):
    argv = argv or sys.argv[1:]
    long_term = Path(argv[0]) if argv else Path(__file__).resolve().parents[2] / "knowledge" / "long-term"
    entries = build_index(long_term / "author-dna.yaml", long_term / "conventions.yaml")
    out_file = long_term / "knowledge-index.yaml"
    header = "# TỰ ĐỘNG TẠO BỞI generate_index.py — KHÔNG CHỈNH SỬA THỦ CÔNG\n"
    out_file.write_text(header + yaml.safe_dump({"entries": entries}, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"Generated {out_file} with {len(entries)} entries.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/bin/python3 -m pytest .amap/tools/knowledge-index/tests/test_generate_index.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/tools/knowledge-index/
git commit -m "feat(knowledge-index): generic applies_to-walk generator"
```

---

## Task 2: knowledge-index — build from real files + snapshot headings

**Files:**
- Modify: `.amap/tools/knowledge-index/generate_index.py` (add `index_snapshot`)
- Test: `.amap/tools/knowledge-index/tests/test_generate_index.py` (add cases)

- [ ] **Step 1: Write the failing test**

```python
def test_index_snapshot_headings(tmp_path):
    snap = tmp_path / "knowledge-snapshot.md"
    snap.write_text(
        "# Snapshot\n"
        "### User Status Module <!-- applies_to: Handler, Executor -->\n"
        "blah\n"
        "### Untagged Module\n",
        encoding="utf-8",
    )
    entries = gi.index_snapshot(snap)
    assert {"id": "User Status Module", "store": "snapshot",
            "title": "User Status Module", "applies_to": ["Handler", "Executor"],
            "mechanically_checkable": False} in entries
    untagged = [e for e in entries if e["id"] == "Untagged Module"][0]
    assert untagged["applies_to"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest .amap/tools/knowledge-index/tests/test_generate_index.py::test_index_snapshot_headings -v`
Expected: FAIL — `index_snapshot` undefined.

- [ ] **Step 3: Write minimal implementation**

```python
# add to generate_index.py
import re

_HEADING = re.compile(r"^#{2,3}\s+(.*?)\s*(?:<!--\s*applies_to:\s*(.*?)\s*-->)?\s*$")


def index_snapshot(snapshot_path):
    p = Path(snapshot_path)
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        m = _HEADING.match(line)
        if not m:
            continue
        title = m.group(1).strip()
        applies = [t.strip() for t in (m.group(2) or "").split(",") if t.strip()]
        out.append({"id": title, "store": "snapshot", "title": title,
                    "applies_to": applies, "mechanically_checkable": False})
    return out
```

Then wire it into `build_index` (add a `snapshot_path` param, default `long_term / "knowledge-snapshot.md"`, and `entries.extend(index_snapshot(snapshot_path))`), and pass it from `main`.

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/bin/python3 -m pytest .amap/tools/knowledge-index/tests/ -v`
Expected: PASS (both tests).

- [ ] **Step 5: Commit**

```bash
git add .amap/tools/knowledge-index/
git commit -m "feat(knowledge-index): index snapshot headings with optional applies_to"
```

---

## Task 3: gate-check evidence validators

The deterministic core of gate-by-evidence. Pure functions, no I/O.

**Files:**
- Create: `.amap/tools/gate-check/__init__.py`, `.amap/tools/gate-check/tests/__init__.py` (empty)
- Create: `.amap/tools/gate-check/gates.py`
- Test: `.amap/tools/gate-check/tests/test_gates.py`

- [ ] **Step 1: Write the failing test**

```python
# .amap/tools/gate-check/tests/test_gates.py
import importlib.util
from pathlib import Path

MOD = Path(__file__).resolve().parents[1] / "gates.py"
spec = importlib.util.spec_from_file_location("gates", MOD)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def test_knowledge_checkpoint_needs_ruleid_and_evidence():
    bad = "## Applicable DNA/Conventions\n(nothing)\n"
    ok_graph = "## DNA\nSP-6 staircase\n## Codebase\nnode_id: svc.UserService#42\nblast-radius: 3 nodes\n"
    ok_degrade = "## DNA\nSP-6\n## Codebase\nKG unavailable — grep fallback, MEDIUM\n"
    assert g.validate_knowledge_checkpoint(bad).ok is False
    assert g.validate_knowledge_checkpoint(ok_graph).ok is True
    assert g.validate_knowledge_checkpoint(ok_degrade).ok is True


def test_mcp_status_needs_numbers_or_degrade():
    assert g.validate_mcp_status("MCP: Runtime Ready").ok is False
    assert g.validate_mcp_status("KG: nodes=1240 edges=5530 freshness=2026-06-18").ok is True
    assert g.validate_mcp_status("KG unavailable — grep fallback, MEDIUM").ok is True


def test_phase_chain_requires_ordered_markers():
    done = "Pha 1 DONE\nPha 2 DONE (spec: openspec/changes/x/)\nPha 3 DONE"
    skipped = "Pha 1 DONE\nPha 3 DONE"
    assert g.validate_phase_chain(done).ok is True
    assert g.validate_phase_chain(skipped).ok is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -v`
Expected: FAIL — `gates.py` missing.

- [ ] **Step 3: Write minimal implementation**

```python
# .amap/tools/gate-check/gates.py
"""Deterministic evidence validators for decision-point gates.

Each returns a Result(ok, reason). They check the CONTENT (evidence) of a
checkpoint/report — never whether a tool was 'called'. See spec §2.
"""
import re
from dataclasses import dataclass


@dataclass
class Result:
    ok: bool
    reason: str = ""


_RULE_ID = re.compile(r"\b[A-Z]{2,3}-\d+\b")              # e.g. SP-6, HP-12, IW-05
_NODE_ID = re.compile(r"\bnode_id\s*[:=]", re.IGNORECASE)
_BLAST = re.compile(r"blast-radius", re.IGNORECASE)
_DEGRADE = re.compile(r"KG unavailable.*MEDIUM", re.IGNORECASE)
_NUMBERS = re.compile(r"(nodes?|edges?)\s*[:=]\s*\d+", re.IGNORECASE)


def validate_knowledge_checkpoint(text: str) -> Result:
    if not _RULE_ID.search(text):
        return Result(False, "no rule-id (e.g. SP-6) cited")
    has_facts = bool(_NODE_ID.search(text) and _BLAST.search(text))
    if has_facts or _DEGRADE.search(text):
        return Result(True)
    return Result(False, "missing codebase evidence (node_id+blast-radius) or degrade line")


def validate_mcp_status(text: str) -> Result:
    if _NUMBERS.search(text) or _DEGRADE.search(text):
        return Result(True)
    return Result(False, "MCP status lacks probe numbers and degrade line ('Runtime Ready' alone is invalid)")


def validate_phase_chain(text: str) -> Result:
    seen = [n for n in (1, 2, 3) if re.search(rf"Pha\s*{n}\s*DONE", text)]
    if seen and seen == list(range(1, max(seen) + 1)):
        return Result(True)
    return Result(False, f"phase markers not contiguous from 1: found {seen}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/tools/gate-check/
git commit -m "feat(gate-check): evidence validators for knowledge/mcp/phase gates"
```

---

## Task 4: gate-check CLI + handoff-slice validator

**Files:**
- Modify: `.amap/tools/gate-check/gates.py` (add `validate_handoff_slice`)
- Create: `.amap/tools/gate-check/cli.py`
- Test: `.amap/tools/gate-check/tests/test_gates.py` (add cases)

- [ ] **Step 1: Write the failing test**

```python
def test_handoff_slice_requires_applicable_section_with_ruleids():
    empty = "# Handoff\n## Task\ndo X\n"
    filled = "# Handoff\n## Applicable DNA/Conventions\n- SP-6: staircase\n- IW-05: config-driven\n"
    assert g.validate_handoff_slice(empty).ok is False
    assert g.validate_handoff_slice(filled).ok is True


def test_cli_returns_nonzero_on_invalid(tmp_path):
    import importlib.util
    cli_mod = Path(__file__).resolve().parents[1] / "cli.py"
    spec2 = importlib.util.spec_from_file_location("cli", cli_mod)
    cli = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(cli)
    f = tmp_path / "chk.md"
    f.write_text("nothing useful", encoding="utf-8")
    assert cli.main(["knowledge-checkpoint", str(f)]) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -v`
Expected: FAIL — `validate_handoff_slice` / `cli.py` missing.

- [ ] **Step 3: Write minimal implementation**

Add to `gates.py`:

```python
def validate_handoff_slice(text: str) -> Result:
    m = re.search(r"##\s+Applicable DNA/Conventions\s*\n(.*)", text, re.DOTALL)
    if not m or not _RULE_ID.search(m.group(1)):
        return Result(False, "handoff missing non-empty 'Applicable DNA/Conventions' with rule-ids")
    return Result(True)
```

Create `cli.py`:

```python
# .amap/tools/gate-check/cli.py
"""CLI: gate-check <gate> <file>  → exit 0 (pass) / 1 (fail)."""
import sys
from pathlib import Path

VALIDATORS = {
    "knowledge-checkpoint": "validate_knowledge_checkpoint",
    "mcp-status": "validate_mcp_status",
    "phase-chain": "validate_phase_chain",
    "handoff-slice": "validate_handoff_slice",
}


def _load_gates():
    import importlib.util
    mod = Path(__file__).resolve().parent / "gates.py"
    spec = importlib.util.spec_from_file_location("gates", mod)
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    return g


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) != 2 or argv[0] not in VALIDATORS:
        print(f"usage: gate-check {{{'|'.join(VALIDATORS)}}} <file>", file=sys.stderr)
        return 2
    g = _load_gates()
    text = Path(argv[1]).read_text(encoding="utf-8")
    res = getattr(g, VALIDATORS[argv[0]])(text)
    print(("PASS" if res.ok else f"FAIL — {res.reason}"))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/ -v`
Expected: PASS (all gate-check tests).

- [ ] **Step 5: Commit**

```bash
git add .amap/tools/gate-check/
git commit -m "feat(gate-check): handoff-slice validator + CLI"
```

---

## Task 5: KNOWLEDGE_CHECKPOINT template + decision-gate procedure

**Files:**
- Create: `.amap/knowledge/templates/KNOWLEDGE_CHECKPOINT.tpl.md`
- Create: `.amap/procedures/decision-gate.md`
- Test: `.amap/tools/gate-check/tests/test_template_roundtrip.py`

- [ ] **Step 1: Write the failing test**

```python
# .amap/tools/gate-check/tests/test_template_roundtrip.py
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]   # .amap/
MOD = ROOT / "tools" / "gate-check" / "gates.py"
spec = importlib.util.spec_from_file_location("gates", MOD)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

TPL = ROOT / "knowledge" / "templates" / "KNOWLEDGE_CHECKPOINT.tpl.md"


def test_blank_template_fails_validator():
    # An unfilled checkpoint MUST NOT pass — proves the gate has teeth.
    assert g.validate_knowledge_checkpoint(TPL.read_text(encoding="utf-8")).ok is False


def test_template_has_required_sections():
    text = TPL.read_text(encoding="utf-8")
    assert "Applicable DNA/Conventions" in text
    assert "Codebase evidence" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_template_roundtrip.py -v`
Expected: FAIL — template file missing.

- [ ] **Step 3: Create the template + procedure**

`.amap/knowledge/templates/KNOWLEDGE_CHECKPOINT.tpl.md`:

```markdown
# KNOWLEDGE CHECKPOINT — {{ artifact_name }}

> Sinh trước khi tạo/sửa artifact. Gate đọc file này. Skeleton = INVALID (gate ABORT).

## Applicable DNA/Conventions
<!-- TODO: liệt kê rule-id khớp applies_to của artifact (vd SP-6, IW-05) + constraint chính -->

## Codebase evidence
<!-- TODO: node_id của component reuse được + blast-radius (find_impact);
     HOẶC nếu KG không có: ghi đúng dòng "KG unavailable — grep fallback, MEDIUM" -->
```

`.amap/procedures/decision-gate.md`:

```markdown
# decision-gate.md — Quy trình gate dùng chung (4 điểm cắm)

> Mọi gate cùng một hình dạng. Gate kiểm BẰNG CHỨNG trong artifact, không kiểm "đã gọi tool chưa".

## Hình dạng chung
1. Tại điểm quyết định → tra `knowledge/long-term/knowledge-index.yaml` (đã nạp ở bootstrap).
2. Kéo SLICE just-in-time: entry có `applies_to` khớp artifact-type hiện tại.
3. Ghi CHECKPOINT artifact (theo template) chứa bằng chứng bắt buộc.
4. Precondition kiểm checkpoint bằng `gate-check`:
   `python3 {{ platform.framework_root }}/tools/gate-check/cli.py <gate> <file>`
   exit≠0 → on_fail (ABORT/degrade).

## Bốn điểm cắm
| Gate | file kiểm | validator |
|------|-----------|-----------|
| knowledge-before-code | `knowledge/active/KNOWLEDGE_CHECKPOINT.md` | `knowledge-checkpoint` |
| subagent injection | `knowledge/active/TASK_HANDOFF.<node>.md` | `handoff-slice` |
| phase-non-bypass | `knowledge/active/AGENT_TRANSPARENCY.md` | `phase-chain` |
| MCP-probe | dòng MCP-status (bootstrap report / transparency) | `mcp-status` |
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_template_roundtrip.py -v`
Expected: PASS — blank template fails the validator (gate has teeth); required sections present.

- [ ] **Step 5: Commit**

```bash
git add .amap/knowledge/templates/KNOWLEDGE_CHECKPOINT.tpl.md .amap/procedures/decision-gate.md .amap/tools/gate-check/tests/test_template_roundtrip.py
git commit -m "feat(gate): KNOWLEDGE_CHECKPOINT template + shared decision-gate procedure"
```

---

## Task 6: Bootstrap diet

**Files:**
- Modify: `.amap/procedures/bootstrap.md` (PHASE 3 table rows for dna/conventions/snapshot; PHASE 5 mandate)
- Test: `.amap/tools/gate-check/tests/test_bootstrap_diet.py`

- [ ] **Step 1: Write the failing test**

```python
# .amap/tools/gate-check/tests/test_bootstrap_diet.py
from pathlib import Path

BOOT = Path(__file__).resolve().parents[3] / "procedures" / "bootstrap.md"


def test_bootstrap_loads_index_not_full_knowledge():
    text = BOOT.read_text(encoding="utf-8")
    assert "knowledge-index.yaml" in text                      # diet loads the index
    assert "đọc TẤT CẢ" not in text and "tất cả entries" not in text  # eager mandate removed
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_bootstrap_diet.py -v`
Expected: FAIL — `knowledge-index.yaml` not referenced; eager mandate still present.

- [ ] **Step 3: Edit bootstrap.md**

In PHASE 3 table (`bootstrap.md` §PHASE 3), replace the three P2 rows that load full `conventions.yaml` / `author-dna.yaml` / `knowledge-snapshot.md` bodies with a single row:

```
| P2 | `{{ platform.framework_root }}/knowledge/long-term/knowledge-index.yaml` | Luôn nạp nếu tồn tại | **WARN** — chạy knowledge-index generator; gate sẽ kéo slice JIT |
```

In PHASE 5 (the "Bắt buộc sau khi nạp" block), delete the mandate "agent PHẢI đọc tất cả entries `confirmed: true` trước khi nhận lệnh code" and replace the report line with:

```
> - `knowledge-index.yaml` đã nạp → report ghi `🧠 Knowledge-index: loaded — {n} entries`.
>   Body của từng entry KHÔNG nạp ở bootstrap; kéo JIT tại decision-gate (xem `procedures/decision-gate.md`).
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_bootstrap_diet.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/procedures/bootstrap.md .amap/tools/gate-check/tests/test_bootstrap_diet.py
git commit -m "refactor(bootstrap): diet — load knowledge-index, drop eager full-file load"
```

---

## Task 7: Gate #1 — knowledge-before-code (collapse R-Guard-2, generic-ise)

**Files:**
- Modify: `.amap/rules/rules-guard.md` (R-Guard-2)
- Test: `.amap/tools/gate-check/tests/test_rule_collapse.py`

- [ ] **Step 1: Write the failing test**

```python
# .amap/tools/gate-check/tests/test_rule_collapse.py
from pathlib import Path

RULES = Path(__file__).resolve().parents[3] / "rules"


def test_guard2_is_evidence_gate_and_generic():
    text = (RULES / "rules-guard.md").read_text(encoding="utf-8")
    # collapsed to the shared gate, references the checkpoint artifact
    assert "KNOWLEDGE_CHECKPOINT" in text
    assert "decision-gate" in text
    # generic-ised: no hard-coded artifact-type enum in the rule
    assert "Chứa `Factory`" not in text
    assert "Chứa `Service`" not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_rule_collapse.py::test_guard2_is_evidence_gate_and_generic -v`
Expected: FAIL — R-Guard-2 still the prose checklist with `Factory`/`Service` names.

- [ ] **Step 3: Edit rules-guard.md**

Replace the body of R-Guard-2 (the numbered prose checklist that names `Factory`/`Service`/`Repository`) with:

```markdown
### [CRITICAL] R-Guard-2: Knowledge-before-code gate (evidence-based)

Trước khi tạo/sửa bất kỳ artifact nào, agent PHẢI sinh
`knowledge/active/KNOWLEDGE_CHECKPOINT.md` (theo template) và pass gate:

`python3 {{ platform.framework_root }}/tools/gate-check/cli.py knowledge-checkpoint <file>`

- Slice knowledge lấy từ `knowledge-index.yaml` theo `applies_to` khớp artifact-type
  hiện tại (artifact-type là tag do project định nghĩa — KHÔNG enum cứng).
- Checkpoint phải có: rule-id áp dụng + (node_id reuse-được + blast-radius) HOẶC dòng degrade.
- Gate FAIL → **ABORT**, không được viết code. Chi tiết: `procedures/decision-gate.md`.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_rule_collapse.py::test_guard2_is_evidence_gate_and_generic -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/rules/rules-guard.md .amap/tools/gate-check/tests/test_rule_collapse.py
git commit -m "refactor(R-Guard-2): collapse to evidence gate, generic-ise artifact types"
```

---

## Task 8: Gate #2 — subagent injection (collapse R-Tool-8)

**Files:**
- Modify: `.amap/rules/rules-tool.md` (R-Tool-8)
- Modify: `.amap/knowledge/templates/KNOWLEDGE_PACK.tpl.md` (add slice section)
- Test: `.amap/tools/gate-check/tests/test_rule_collapse.py` (add case)

- [ ] **Step 1: Write the failing test**

```python
def test_rtool8_dispatch_gate():
    text = (RULES / "rules-tool.md").read_text(encoding="utf-8")
    assert "handoff-slice" in text                     # references the gate validator
    assert "Applicable DNA/Conventions" in text         # required slice section
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_rule_collapse.py::test_rtool8_dispatch_gate -v`
Expected: FAIL.

- [ ] **Step 3: Edit rules-tool.md + KNOWLEDGE_PACK.tpl.md**

Replace R-Tool-8 body with a dispatch-gate:

```markdown
### [CRITICAL] R-Tool-8: Subagent dispatch gate — inject knowledge slice

Orchestrator KHÔNG được `invoke_subagent` cho tới khi `TASK_HANDOFF.<node-id>.md`
chứa section `## Applicable DNA/Conventions` (slice từ knowledge-index theo
artifact-type của node) và pass:

`python3 {{ platform.framework_root }}/tools/gate-check/cli.py handoff-slice <file>`

- Slice nhúng INLINE vào prompt subagent (subagent KHÔNG tự đọc knowledge/gọi UA).
- Output subagent kèm node-checkpoint ghi rule-id đã áp dụng; linter cơ học (sub-spec #2)
  gác cửa cuối cho rule `mechanically_checkable`.
- Thiếu slice trong khi chạy → subagent ghi `CONTEXT_REQUEST.<node-id>.md`, KHÔNG tự explore.
```

Append to `KNOWLEDGE_PACK.tpl.md`:

```markdown

## Applicable DNA/Conventions
<!-- Orchestrator nhét slice rule-id khớp applies_to của node vào đây trước khi dispatch -->
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_rule_collapse.py::test_rtool8_dispatch_gate -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/rules/rules-tool.md .amap/knowledge/templates/KNOWLEDGE_PACK.tpl.md .amap/tools/gate-check/tests/test_rule_collapse.py
git commit -m "refactor(R-Tool-8): subagent dispatch gate with mandatory knowledge slice"
```

---

## Task 9: Gate #3 — phase-non-bypass (collapse R-Flow-1/2/3)

**Files:**
- Modify: `.amap/rules/rules-flow.md` (R-Flow-2 + a completion gate)
- Test: `.amap/tools/gate-check/tests/test_rule_collapse.py` (add case)

- [ ] **Step 1: Write the failing test**

```python
def test_rflow_phase_gate():
    text = (RULES / "rules-flow.md").read_text(encoding="utf-8")
    assert "phase-chain" in text                         # completion gate validator
    assert "phase_done(spec)" in text or "phase_done: spec" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_rule_collapse.py::test_rflow_phase_gate -v`
Expected: FAIL.

- [ ] **Step 3: Edit rules-flow.md**

Under R-Flow-2 add an apply-entry precondition + completion gate (and trim the now-redundant prose of R-Flow-1/R-Flow-3 into a one-line pointer):

```markdown
### [CRITICAL] R-Flow-2: Phase gate (entry + completion)

- **Apply-entry:** `/task apply` có precondition `phase_done(spec)` + spec artifact tại
  `openspec/changes/<id>/`. Thiếu → ABORT. Lý do "scope rõ nên bỏ spec" KHÔNG hợp lệ —
  spec artifact là bắt buộc, không phải phán đoán agent.
- **Completion:** KHÔNG phát "Done" tới khi phase-chain pass:
  `python3 {{ platform.framework_root }}/tools/gate-check/cli.py phase-chain knowledge/active/AGENT_TRANSPARENCY.md`
  (kiểm marker `Pha 1/2/3 DONE` liên tục từ 1). Build-pass/bookkeeping thuộc sub-spec #3.
- Residual đã biết: write thô ngoài mọi /task skill chưa chặn được (future runtime hook).
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_rule_collapse.py::test_rflow_phase_gate -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/rules/rules-flow.md .amap/tools/gate-check/tests/test_rule_collapse.py
git commit -m "refactor(R-Flow): phase entry + completion gate via phase-chain validator"
```

---

## Task 10: Gate #4 — MCP-probe (collapse R-Tool-4/5/5b + R-Adapter-2)

**Files:**
- Modify: `.amap/rules/rules-tool.md` (R-Tool-4/5/5b, R-Adapter-2)
- Modify: `.amap/procedures/bootstrap.md` (PHASE 5 MCP-status from probe)
- Test: `.amap/tools/gate-check/tests/test_rule_collapse.py` (add case)

- [ ] **Step 1: Write the failing test**

```python
def test_rtool_mcp_probe_collapse():
    text = (RULES / "rules-tool.md").read_text(encoding="utf-8")
    assert "mcp-status" in text                          # probe gate validator
    assert "Runtime Ready" not in text or "rỗng = invalid" in text
    assert "secondary" not in text                       # removed skippable preference prose
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_rule_collapse.py::test_rtool_mcp_probe_collapse -v`
Expected: FAIL — old R-Tool-4/5/5b prose (incl. "secondary") still present.

- [ ] **Step 3: Edit rules-tool.md + bootstrap.md**

Replace R-Tool-4 + R-Tool-5 + R-Tool-5b + R-Adapter-2 with a single rule:

```markdown
### [CRITICAL] R-Tool-5: Codebase-knowledge via MCP — evidence gate

- MCP-status (bootstrap + transparency) hợp lệ CHỈ KHI nhúng số thật từ probe
  (`get_graph_stats`/`list_projects`: nodes/edges/freshness). "Runtime Ready" rỗng = invalid.
  Pass: `python3 {{ platform.framework_root }}/tools/gate-check/cli.py mcp-status <file>`.
- Khi cần codebase-facts: bằng chứng trong KNOWLEDGE_CHECKPOINT (node_id + blast-radius)
  tự khắc buộc dùng KG tools; KG không có → dòng degrade "KG unavailable — grep fallback, MEDIUM"
  + hạ confidence kiến trúc. KHÔNG bịa kết quả tool không khả dụng.
- (Infra: thiếu mcp_config.json theo runtime là việc của `amap doctor`, ngoài rule này.)
```

In `bootstrap.md` PHASE 5, change the MCP/report so the MCP-status line must carry probe numbers (or the degrade line) — point to the `mcp-status` gate.

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_rule_collapse.py::test_rtool_mcp_probe_collapse -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/rules/rules-tool.md .amap/procedures/bootstrap.md .amap/tools/gate-check/tests/test_rule_collapse.py
git commit -m "refactor(R-Tool): collapse UA/KG rules to one MCP-probe evidence gate"
```

---

## Task 11: Net-negative measurement + golden snapshots + full suite

**Files:**
- Create: `.amap/tools/gate-check/complexity.py`
- Test: `.amap/tools/gate-check/tests/test_complexity.py`
- Modify: golden snapshots if `amap init` output changed (see `cli/tests/test_snapshots.py`)

- [ ] **Step 1: Write the failing test**

```python
# .amap/tools/gate-check/tests/test_complexity.py
import importlib.util
from pathlib import Path

MOD = Path(__file__).resolve().parents[1] / "complexity.py"
spec = importlib.util.spec_from_file_location("complexity", MOD)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def test_counts_critical_blocks(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("### [CRITICAL] A\nx\n### [CRITICAL] B\ny\n### [REFERENCE] C\n", encoding="utf-8")
    assert c.count_critical_blocks([f]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_complexity.py -v`
Expected: FAIL — `complexity.py` missing.

- [ ] **Step 3: Implement complexity.py**

```python
# .amap/tools/gate-check/complexity.py
"""Count [CRITICAL] rule blocks across rule files — for net-negative tracking."""
import re
import sys
from pathlib import Path

_CRIT = re.compile(r"^#{2,4}\s*\[CRITICAL\]", re.MULTILINE)


def count_critical_blocks(files):
    return sum(len(_CRIT.findall(Path(f).read_text(encoding="utf-8"))) for f in files)


def main(argv=None):
    argv = argv or sys.argv[1:]
    files = [Path(p) for p in argv] or sorted((Path(__file__).resolve().parents[2] / "rules").glob("*.md"))
    print(f"[CRITICAL] blocks: {count_critical_blocks(files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test + measure before/after + update snapshots**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_complexity.py -v`
Expected: PASS.

Record the count and confirm net-negative vs baseline (program doc §4 says collapse ≥9 prose blocks):

Run: `/usr/bin/python3 .amap/tools/gate-check/complexity.py`
Expected: fewer `[CRITICAL]` blocks than at branch start (compare with `git show main:.amap/rules` if needed).

If `amap init` output changed (templates/rules), regenerate golden snapshots:

Run: `/usr/bin/python3 -m pytest cli/tests/test_snapshots.py -v`
If snapshots fail due to intended changes, update per that test's regeneration mechanism, then re-run.

- [ ] **Step 5: Run the FULL suite + commit**

Run: `/usr/bin/python3 -m pytest cli/tests .amap/tools -q`
Expected: all PASS.

```bash
git add .amap/tools/gate-check/complexity.py .amap/tools/gate-check/tests/test_complexity.py cli/tests/
git commit -m "feat(gate-check): net-negative complexity counter + refresh snapshots"
```

---

## Regression fixtures (proves the original failures are caught)

These assert the historical corrections (C-10, C-22) now fail their gates. Add to `test_gates.py`.

- [ ] **C-10 (subagent SP-6):** a handoff missing the slice fails `validate_handoff_slice`:

```python
def test_c10_handoff_without_sp6_slice_blocks_dispatch():
    handoff = "# Handoff\n## Task\nwrite UnlockUserConfirmExecutor\n"
    assert g.validate_handoff_slice(handoff).ok is False
```

- [ ] **C-22 (skipped spec):** transparency with Pha 1 then Pha 3 (spec skipped) fails `validate_phase_chain`:

```python
def test_c22_skipped_spec_blocks_completion():
    transparency = "Pha 1 DONE\nPha 3 DONE"
    assert g.validate_phase_chain(transparency).ok is False
```

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -v` → PASS. Commit.

---

## Done criteria (maps to spec §1 success criteria)

1. Bootstrap loads `knowledge-index.yaml`, not full bodies (Task 6 test).
2. Four gates each have a validator + a "missing evidence → fail" test (Tasks 3,4 + regression).
3. ≥9 `[CRITICAL]` prose blocks collapsed; `complexity.py` shows net-negative (Task 11).
4. C-10 and C-22 regression fixtures pass (Regression section).
5. Full suite green: `/usr/bin/python3 -m pytest cli/tests .amap/tools -q`.
