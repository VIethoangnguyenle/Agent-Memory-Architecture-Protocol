# Hybrid Contract DAG Subagent Coding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade AMAP Phase 3 from the current linear micro-loop into a knowledge-first Hybrid Contract DAG flow that supports contract/base generation before parallel child implementation.

**Architecture:** Extend the existing SP1b micro-loop rather than replacing AMAP. Add durable filesystem artifacts for `KNOWLEDGE_PACK`, `CONTRACT_DAG`, contract snapshots, and request protocols; then add pure Python helpers for validation, stale invalidation, write-conflict detection, and handoff assembly. Update Phase 3 docs/procedures/rules so coding agents execute inside knowledge-first boundaries.

**Tech Stack:** Python 3, PyYAML, pytest, Markdown/YAML filesystem contracts, existing `.agent/tools/microloop-orchestrator/` package.

---

## File Structure

Modify these existing files:

- `.agent/tools/microloop-orchestrator/contract.py`  
  Add validators and load/dump helpers for `KNOWLEDGE_PACK`, `CONTRACT_DAG`, `CONTRACT_SNAPSHOT`, `CONTEXT_REQUEST`, `CONTRACT_CHANGE_REQUEST`, and `INTEGRATION_REQUEST`.

- `.agent/tools/microloop-orchestrator/orchestrator.py`  
  Add DAG helpers: node topo-sort, write-conflict detection, parallel batch planning, stale invalidation, knowledge-pack gating, and role-specific handoff assembly.

- `.agent/tools/microloop-orchestrator/tests/test_contract.py`  
  Add schema roundtrip and rejection tests for the new artifacts.

- `.agent/tools/microloop-orchestrator/tests/test_protocol.py`  
  Add DAG helper tests: contract-first ordering, stale invalidation, write-conflict batching, and knowledge gate behavior.

- `.agent/procedures/executor.md`  
  Update executor behavior for role-specific handoffs, contract snapshots, request protocols, and no direct UA/DB/memory access.

- `.agent/procedures/reviewer.md`  
  Update reviewer behavior for verification lane and contract DAG final review.

- `.agent/workflows/task.md`  
  Replace Phase 3 micro-loop description with Hybrid Contract DAG orchestration while keeping pre-apply gates, confirmation, post-apply verify, token logging, and knowledge-curator flow.

- `.agent/skills/spec-validator/SKILL.md`  
  Add contract-version, stale-node, allowed-files, and integration-request coverage checks.

- `.agent/rules/rules-tool.md`  
  Add rule that coding subagents cannot call UA/KG, DB, or agent-memory directly; only the orchestrator may enrich `KNOWLEDGE_PACK`.

- `.agent/rules/rules-exec.md`  
  Add execution-budget language for context requests and parallel leaf batches.

Create these new files:

- `.knowledge-layer/templates/KNOWLEDGE_PACK.tpl.md`
- `.knowledge-layer/templates/CONTRACT_DAG.tpl.md`
- `.knowledge-layer/templates/CONTRACT_SNAPSHOT.tpl.md`
- `.knowledge-layer/templates/CONTEXT_REQUEST.tpl.md`
- `.knowledge-layer/templates/CONTRACT_CHANGE_REQUEST.tpl.md`
- `.knowledge-layer/templates/INTEGRATION_REQUEST.tpl.md`

Do not modify production application code. This is an AMAP framework/protocol change.

---

### Task 1: Add Filesystem Contract Schemas

**Files:**
- Modify: `.agent/tools/microloop-orchestrator/contract.py`
- Modify: `.agent/tools/microloop-orchestrator/tests/test_contract.py`

- [ ] **Step 1: Write failing schema tests**

Append these tests to `.agent/tools/microloop-orchestrator/tests/test_contract.py`:

```python
def test_knowledge_pack_roundtrip(tmp_path):
    kp = {
        "ticket_id": "ABC-1",
        "change_id": "add-payment-processor",
        "confidence": {"overall": "CAO", "code_graph": "CAO", "database": "TRUNG-BINH", "memory": "CAO"},
        "sources": {"requirement": ".knowledge-layer/active/REQUIREMENT.md"},
        "ua_kg": {"graph_status": "available", "entry_points": []},
        "database": {"required": True, "evidence": [{"table": "PAYMENT_CONFIG", "constraints": ["PK_PAYMENT_CONFIG"]}]},
        "architecture": {"boundaries": ["Keep provider logic out of base"], "risks": []},
        "dna": {"hard_principles": ["HP-1"], "complexity_thresholds": {"max_nesting_depth": 3}},
        "conventions": {"relevant_sections": ["naming"]},
        "memory": {"related_decisions": []},
    }
    p = tmp_path / "KNOWLEDGE_PACK.md"
    contract.dump_knowledge_pack(kp, str(p))
    assert contract.load_knowledge_pack(str(p)) == kp


def test_contract_dag_roundtrip_with_stale_status(tmp_path):
    dag = {
        "ticket_id": "ABC-1",
        "spec_path": "openspec/changes/add-payment-processor/",
        "contract_version_counter": 1,
        "nodes": [
            {
                "id": "C1",
                "type": "contract",
                "desc": "Create BasePaymentProcessor",
                "depends_on": [],
                "reads": [],
                "writes": ["src/BasePaymentProcessor.java"],
                "contract_version": "v1",
                "status": "done",
            },
            {
                "id": "L1",
                "type": "leaf",
                "desc": "Create CardPaymentProcessor",
                "depends_on": ["C1"],
                "reads": ["src/BasePaymentProcessor.java"],
                "writes": ["src/CardPaymentProcessor.java"],
                "contract_ref": {"node_id": "C1", "version": "v1"},
                "status": "stale",
            },
        ],
    }
    p = tmp_path / "CONTRACT_DAG.md"
    contract.dump_contract_dag(dag, str(p))
    assert contract.load_contract_dag(str(p)) == dag


def test_contract_snapshot_roundtrip(tmp_path):
    snap = {
        "node_id": "C1",
        "contract_name": "BasePaymentProcessor",
        "contract_version": "v1",
        "source_file": "src/BasePaymentProcessor.java",
        "kind": "abstract_class",
        "constructor": {"dependencies": ["PaymentConfigRepository"]},
        "public_methods": [{"signature": "PaymentResult process(PaymentRequest request)", "behavior": "Template method"}],
        "protected_methods": [{"signature": "ProviderResult executeProvider(PaymentRequest request)", "child_must_implement": True}],
        "invariants": ["Shared validation runs first"],
        "forbidden_overrides": ["process"],
        "extension_rules": ["Child implements provider execution only"],
        "examples": ["ExistingProcessor retry mapping pattern"],
    }
    p = tmp_path / "CONTRACT_SNAPSHOT.C1.md"
    contract.dump_contract_snapshot(snap, str(p))
    assert contract.load_contract_snapshot(str(p)) == snap


def test_request_protocol_roundtrips(tmp_path):
    context_request = {
        "node_id": "L1",
        "request_type": "context",
        "missing": ["Need source of ExistingProcessor retry mapping"],
        "suggested_tools": ["understand-anything.get_node_source"],
        "blocked_reason": "Cannot implement provider-specific config lookup safely",
    }
    contract_change = {
        "node_id": "L1",
        "request_type": "contract_change",
        "contract_ref": {"node_id": "C1", "version": "v1"},
        "problem": "Base class has no protected mapper",
        "proposal": "Add protected mapProviderError(...) hook",
        "impact": {"affected_nodes": ["L1", "L2"]},
    }
    integration_request = {
        "node_id": "L1",
        "request_type": "integration",
        "target_file": "src/PaymentProcessorRegistry.java",
        "requested_change": "Register CardPaymentProcessor for provider=CARD",
        "required_after": "L1",
    }
    cp = tmp_path / "CONTEXT_REQUEST.L1.md"
    hp = tmp_path / "CONTRACT_CHANGE_REQUEST.L1.md"
    ip = tmp_path / "INTEGRATION_REQUEST.L1.md"
    contract.dump_context_request(context_request, str(cp))
    contract.dump_contract_change_request(contract_change, str(hp))
    contract.dump_integration_request(integration_request, str(ip))
    assert contract.load_context_request(str(cp)) == context_request
    assert contract.load_contract_change_request(str(hp)) == contract_change
    assert contract.load_integration_request(str(ip)) == integration_request


def test_contract_dag_rejects_unknown_node_type():
    dag = {
        "ticket_id": "ABC-1",
        "spec_path": "openspec/changes/x/",
        "contract_version_counter": 1,
        "nodes": [{"id": "X1", "type": "magic", "desc": "bad", "depends_on": [], "reads": [], "writes": [], "status": "pending"}],
    }
    import pytest
    with pytest.raises(ValueError, match="bad node type"):
        contract.validate_contract_dag(dag)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest .agent/tools/microloop-orchestrator/tests/test_contract.py -v
```

Expected: FAIL with missing attributes such as `dump_knowledge_pack`.

- [ ] **Step 3: Implement schema helpers**

In `.agent/tools/microloop-orchestrator/contract.py`, add these constants near the existing `VALID_STATUS` declarations:

```python
VALID_NODE_STATUS = {"pending", "in_progress", "done", "blocked", "stale"}
VALID_NODE_TYPE = {"contract", "leaf", "integration", "test", "review"}
VALID_CONFIDENCE = {"CAO", "TRUNG-BINH", "THAP"}
```

Then append these functions after `dump_result`:

```python
def _require_keys(doc, keys, label):
    for key in keys:
        if key not in doc:
            raise ValueError(f"{label} missing key: {key}")
    return doc


def validate_knowledge_pack(kp):
    _require_keys(kp, ("ticket_id", "change_id", "confidence", "sources", "ua_kg", "database",
                       "architecture", "dna", "conventions", "memory"), "knowledge_pack")
    for key in ("overall", "code_graph", "database", "memory"):
        value = kp["confidence"].get(key)
        if value not in VALID_CONFIDENCE:
            raise ValueError(f"bad confidence {key}: {value}")
    return kp


def load_knowledge_pack(path):
    return validate_knowledge_pack(_load(path))


def dump_knowledge_pack(kp, path):
    validate_knowledge_pack(kp)
    _dump(kp, path)


def validate_contract_dag(dag):
    _require_keys(dag, ("ticket_id", "spec_path", "contract_version_counter", "nodes"), "contract_dag")
    ids = {node.get("id") for node in dag["nodes"]}
    for node in dag["nodes"]:
        _require_keys(node, ("id", "type", "desc", "depends_on", "reads", "writes", "status"), "contract_dag node")
        if node["type"] not in VALID_NODE_TYPE:
            raise ValueError(f"bad node type: {node['type']}")
        if node["status"] not in VALID_NODE_STATUS:
            raise ValueError(f"bad node status: {node['status']}")
        for dep_id in node.get("depends_on", []):
            if dep_id not in ids:
                raise ValueError(f"node {node['id']} depends on non-existent node {dep_id}")
    return dag


def load_contract_dag(path):
    return validate_contract_dag(_load(path))


def dump_contract_dag(dag, path):
    validate_contract_dag(dag)
    _dump(dag, path)


def validate_contract_snapshot(snapshot):
    _require_keys(snapshot, ("node_id", "contract_name", "contract_version", "source_file", "kind",
                             "constructor", "public_methods", "protected_methods", "invariants",
                             "forbidden_overrides", "extension_rules", "examples"), "contract_snapshot")
    return snapshot


def load_contract_snapshot(path):
    return validate_contract_snapshot(_load(path))


def dump_contract_snapshot(snapshot, path):
    validate_contract_snapshot(snapshot)
    _dump(snapshot, path)


def validate_context_request(req):
    _require_keys(req, ("node_id", "request_type", "missing", "suggested_tools", "blocked_reason"), "context_request")
    if req["request_type"] != "context":
        raise ValueError(f"bad request_type: {req['request_type']}")
    return req


def load_context_request(path):
    return validate_context_request(_load(path))


def dump_context_request(req, path):
    validate_context_request(req)
    _dump(req, path)


def validate_contract_change_request(req):
    _require_keys(req, ("node_id", "request_type", "contract_ref", "problem", "proposal", "impact"), "contract_change_request")
    if req["request_type"] != "contract_change":
        raise ValueError(f"bad request_type: {req['request_type']}")
    return req


def load_contract_change_request(path):
    return validate_contract_change_request(_load(path))


def dump_contract_change_request(req, path):
    validate_contract_change_request(req)
    _dump(req, path)


def validate_integration_request(req):
    _require_keys(req, ("node_id", "request_type", "target_file", "requested_change", "required_after"), "integration_request")
    if req["request_type"] != "integration":
        raise ValueError(f"bad request_type: {req['request_type']}")
    return req


def load_integration_request(path):
    return validate_integration_request(_load(path))


def dump_integration_request(req, path):
    validate_integration_request(req)
    _dump(req, path)
```

- [ ] **Step 4: Run contract tests**

Run:

```bash
python3 -m pytest .agent/tools/microloop-orchestrator/tests/test_contract.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .agent/tools/microloop-orchestrator/contract.py .agent/tools/microloop-orchestrator/tests/test_contract.py
git commit -m "feat(microloop): add hybrid contract dag schemas"
```

---

### Task 2: Add Contract DAG Orchestrator Helpers

**Files:**
- Modify: `.agent/tools/microloop-orchestrator/orchestrator.py`
- Modify: `.agent/tools/microloop-orchestrator/tests/test_protocol.py`

- [ ] **Step 1: Write failing protocol tests**

Append these tests to `.agent/tools/microloop-orchestrator/tests/test_protocol.py`:

```python
def test_topo_sort_nodes_orders_contract_before_leaf():
    nodes = [
        {"id": "L1", "type": "leaf", "desc": "child", "depends_on": ["C1"], "reads": [], "writes": ["Child.java"], "status": "pending"},
        {"id": "C1", "type": "contract", "desc": "base", "depends_on": [], "reads": [], "writes": ["Base.java"], "status": "pending"},
    ]
    ordered = orchestrator.topo_sort_nodes(nodes)
    assert [node["id"] for node in ordered] == ["C1", "L1"]


def test_find_write_conflicts_groups_by_path():
    nodes = [
        {"id": "L1", "type": "leaf", "writes": ["Registry.java"]},
        {"id": "L2", "type": "leaf", "writes": ["Registry.java"]},
        {"id": "L3", "type": "leaf", "writes": ["Other.java"]},
    ]
    assert orchestrator.find_write_conflicts(nodes) == {"Registry.java": ["L1", "L2"]}


def test_plan_parallel_batches_keeps_conflicting_writes_separate():
    nodes = [
        {"id": "L1", "type": "leaf", "depends_on": [], "writes": ["Registry.java"], "status": "pending"},
        {"id": "L2", "type": "leaf", "depends_on": [], "writes": ["Registry.java"], "status": "pending"},
        {"id": "L3", "type": "leaf", "depends_on": [], "writes": ["Other.java"], "status": "pending"},
    ]
    batches = orchestrator.plan_parallel_batches(nodes)
    flattened = [node["id"] for batch in batches for node in batch]
    assert flattened == ["L1", "L3", "L2"]
    assert [node["id"] for node in batches[0]] == ["L1", "L3"]
    assert [node["id"] for node in batches[1]] == ["L2"]


def test_invalidate_contract_dependents_marks_stale():
    dag = {
        "nodes": [
            {"id": "C1", "type": "contract", "status": "done", "contract_version": "v2", "depends_on": [], "reads": [], "writes": []},
            {"id": "L1", "type": "leaf", "status": "done", "depends_on": ["C1"], "reads": [], "writes": [], "contract_ref": {"node_id": "C1", "version": "v1"}},
            {"id": "L2", "type": "leaf", "status": "done", "depends_on": ["C1"], "reads": [], "writes": [], "contract_ref": {"node_id": "C1", "version": "v2"}},
        ]
    }
    updated = orchestrator.invalidate_contract_dependents(dag, "C1", "v2")
    statuses = {node["id"]: node["status"] for node in updated["nodes"]}
    assert statuses["L1"] == "stale"
    assert statuses["L2"] == "done"


def test_knowledge_gate_blocks_complex_without_graph():
    kp = {
        "confidence": {"overall": "CAO", "code_graph": "THAP", "database": "CAO", "memory": "CAO"},
        "ua_kg": {"graph_status": "unavailable"},
        "database": {"required": False, "evidence": []},
    }
    result = orchestrator.check_knowledge_gate(kp, complexity="complex", user_override=False)
    assert result["status"] == "BLOCK"
    assert "KG graph unavailable" in result["issues"][0]


def test_build_contract_handoff_includes_dna_convention_and_snapshot():
    task = {"id": "L1", "desc": "Create child", "contract_ref": {"node_id": "C1", "version": "v1"}}
    handoff = orchestrator.build_contract_handoff(
        task=task,
        knowledge_pack={"dna": {"hard_principles": ["HP-1"]}, "conventions": {"relevant_sections": ["naming"]}},
        spec_slice="Implement child",
        snapshot_slice="Payment module",
        contract_snapshot={"node_id": "C1", "contract_version": "v1"},
        written_files=[],
        boundary=["Do not edit BasePaymentProcessor"],
        feedback=None,
    )
    assert handoff["task"]["id"] == "L1"
    assert handoff["dna_slice"]["hard_principles"] == ["HP-1"]
    assert handoff["convention_slice"]["relevant_sections"] == ["naming"]
    assert handoff["contract_snapshot"]["contract_version"] == "v1"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest .agent/tools/microloop-orchestrator/tests/test_protocol.py -v
```

Expected: FAIL with missing functions such as `topo_sort_nodes`.

- [ ] **Step 3: Implement DAG helpers**

Append these functions to `.agent/tools/microloop-orchestrator/orchestrator.py` after `run_loop`:

```python
def topo_sort_nodes(nodes):
    """Topo-sort Contract DAG nodes by depends_on, preserving deterministic id order."""
    by_id = {node["id"]: node for node in nodes}
    for node in nodes:
        for dep_id in node.get("depends_on", []):
            if dep_id not in by_id:
                raise ValueError(f"node {node['id']} depends on non-existent node {dep_id}")
    indeg = {node["id"]: len(node.get("depends_on", [])) for node in nodes}
    ready = sorted([node_id for node_id, degree in indeg.items() if degree == 0])
    ordered = []
    while ready:
        node_id = ready.pop(0)
        ordered.append(by_id[node_id])
        for node in nodes:
            if node_id in node.get("depends_on", []):
                indeg[node["id"]] -= 1
                if indeg[node["id"]] == 0:
                    ready.append(node["id"])
        ready.sort()
    if len(ordered) != len(nodes):
        raise ValueError("dependency cycle detected in contract dag")
    return ordered


def find_write_conflicts(nodes):
    """Return paths written by more than one node: {path: [node_id, ...]}."""
    writers = {}
    for node in nodes:
        for path in node.get("writes", []):
            writers.setdefault(path, []).append(node["id"])
    return {path: ids for path, ids in writers.items() if len(ids) > 1}


def plan_parallel_batches(nodes):
    """Plan deterministic batches where no nodes in the same batch write the same file."""
    pending = topo_sort_nodes(nodes)
    batches = []
    while pending:
        batch = []
        used_writes = set()
        remaining = []
        for node in pending:
            writes = set(node.get("writes", []))
            if used_writes.isdisjoint(writes):
                batch.append(node)
                used_writes.update(writes)
            else:
                remaining.append(node)
        batches.append(batch)
        pending = remaining
    return batches


def invalidate_contract_dependents(dag, contract_node_id, new_version):
    """Mark downstream nodes stale when their contract_ref version is older than new_version."""
    for node in dag.get("nodes", []):
        ref = node.get("contract_ref")
        if ref and ref.get("node_id") == contract_node_id and ref.get("version") != new_version:
            node["status"] = "stale"
    return dag


def check_knowledge_gate(knowledge_pack, complexity="standard", user_override=False):
    """Return PASS/BLOCK for Phase 3 knowledge readiness."""
    issues = []
    graph_status = knowledge_pack.get("ua_kg", {}).get("graph_status")
    if complexity == "complex" and graph_status != "available":
        issues.append("KG graph unavailable for complex task")
    database = knowledge_pack.get("database", {})
    if database.get("required") and not database.get("evidence"):
        issues.append("DB evidence missing for data-touching task")
    if issues and not user_override:
        return {"status": "BLOCK", "issues": issues}
    if issues:
        return {"status": "WARN", "issues": issues}
    return {"status": "PASS", "issues": []}


def build_contract_handoff(task, knowledge_pack, spec_slice, snapshot_slice, contract_snapshot,
                           written_files, boundary, feedback=None):
    """Build role-aware TASK_HANDOFF content for Hybrid Contract DAG nodes."""
    return {
        "task": {"id": task["id"], "desc": task["desc"]},
        "dna_slice": knowledge_pack.get("dna", {}),
        "convention_slice": knowledge_pack.get("conventions", {}),
        "spec_slice": spec_slice,
        "snapshot_slice": snapshot_slice,
        "contract_snapshot": contract_snapshot,
        "written_files": written_files,
        "boundary": boundary,
        "feedback": feedback,
    }
```

- [ ] **Step 4: Run protocol tests**

Run:

```bash
python3 -m pytest .agent/tools/microloop-orchestrator/tests/test_protocol.py -v
```

Expected: PASS.

- [ ] **Step 5: Run all microloop tests**

Run:

```bash
python3 -m pytest .agent/tools/microloop-orchestrator/tests/ -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add .agent/tools/microloop-orchestrator/orchestrator.py .agent/tools/microloop-orchestrator/tests/test_protocol.py
git commit -m "feat(microloop): add contract dag orchestration helpers"
```

---

### Task 3: Add Knowledge Pack and DAG Templates

**Files:**
- Create: `.knowledge-layer/templates/KNOWLEDGE_PACK.tpl.md`
- Create: `.knowledge-layer/templates/CONTRACT_DAG.tpl.md`
- Create: `.knowledge-layer/templates/CONTRACT_SNAPSHOT.tpl.md`
- Create: `.knowledge-layer/templates/CONTEXT_REQUEST.tpl.md`
- Create: `.knowledge-layer/templates/CONTRACT_CHANGE_REQUEST.tpl.md`
- Create: `.knowledge-layer/templates/INTEGRATION_REQUEST.tpl.md`

- [ ] **Step 1: Create Knowledge Pack template**

Create `.knowledge-layer/templates/KNOWLEDGE_PACK.tpl.md`:

```yaml
ticket_id: "<ticket-id>"
change_id: "<change-id>"
confidence:
  overall: THAP
  code_graph: THAP
  database: THAP
  memory: THAP
sources:
  requirement: ".knowledge-layer/active/REQUIREMENT.md"
  explore_context: ".knowledge-layer/active/EXPLORE_CONTEXT.md"
  openspec: "openspec/changes/<change-id>/"
ua_kg:
  graph_status: "unavailable"
  graph_timestamp: null
  entry_points: []
  blast_radius: []
database:
  required: false
  evidence: []
architecture:
  boundaries: []
  risks: []
dna:
  hard_principles: []
  complexity_thresholds: {}
conventions:
  relevant_sections: []
memory:
  related_decisions: []
```

- [ ] **Step 2: Create Contract DAG template**

Create `.knowledge-layer/templates/CONTRACT_DAG.tpl.md`:

```yaml
ticket_id: "<ticket-id>"
spec_path: "openspec/changes/<change-id>/"
contract_version_counter: 0
nodes: []
```

- [ ] **Step 3: Create Contract Snapshot template**

Create `.knowledge-layer/templates/CONTRACT_SNAPSHOT.tpl.md`:

```yaml
node_id: "<contract-node-id>"
contract_name: "<ContractName>"
contract_version: "v1"
source_file: "<path>"
kind: "abstract_class"
constructor:
  dependencies: []
public_methods: []
protected_methods: []
invariants: []
forbidden_overrides: []
extension_rules: []
examples: []
```

- [ ] **Step 4: Create request templates**

Create `.knowledge-layer/templates/CONTEXT_REQUEST.tpl.md`:

```yaml
node_id: "<node-id>"
request_type: "context"
missing: []
suggested_tools: []
blocked_reason: ""
```

Create `.knowledge-layer/templates/CONTRACT_CHANGE_REQUEST.tpl.md`:

```yaml
node_id: "<node-id>"
request_type: "contract_change"
contract_ref:
  node_id: "<contract-node-id>"
  version: "v1"
problem: ""
proposal: ""
impact:
  affected_nodes: []
```

Create `.knowledge-layer/templates/INTEGRATION_REQUEST.tpl.md`:

```yaml
node_id: "<node-id>"
request_type: "integration"
target_file: "<path>"
requested_change: ""
required_after: "<node-id>"
```

- [ ] **Step 5: Validate templates with existing schema helpers**

Run this Python one-liner:

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, ".agent/tools/microloop-orchestrator")
import contract
contract.load_knowledge_pack(".knowledge-layer/templates/KNOWLEDGE_PACK.tpl.md")
contract.load_contract_dag(".knowledge-layer/templates/CONTRACT_DAG.tpl.md")
contract.load_contract_snapshot(".knowledge-layer/templates/CONTRACT_SNAPSHOT.tpl.md")
contract.load_context_request(".knowledge-layer/templates/CONTEXT_REQUEST.tpl.md")
contract.load_contract_change_request(".knowledge-layer/templates/CONTRACT_CHANGE_REQUEST.tpl.md")
contract.load_integration_request(".knowledge-layer/templates/INTEGRATION_REQUEST.tpl.md")
print("templates ok")
PY
```

Expected: `templates ok`.

- [ ] **Step 6: Commit**

```bash
git add .knowledge-layer/templates/KNOWLEDGE_PACK.tpl.md .knowledge-layer/templates/CONTRACT_DAG.tpl.md .knowledge-layer/templates/CONTRACT_SNAPSHOT.tpl.md .knowledge-layer/templates/CONTEXT_REQUEST.tpl.md .knowledge-layer/templates/CONTRACT_CHANGE_REQUEST.tpl.md .knowledge-layer/templates/INTEGRATION_REQUEST.tpl.md
git commit -m "feat(knowledge): add hybrid contract dag templates"
```

---

### Task 4: Update Executor and Reviewer Procedures

**Files:**
- Modify: `.agent/procedures/executor.md`
- Modify: `.agent/procedures/reviewer.md`

- [ ] **Step 1: Replace executor procedure**

Replace the full content of `.agent/procedures/executor.md` with:

```markdown
# Procedure: Executor (one Hybrid Contract DAG node)

> Consumed by the agent acting as a role-specific coding executor. Input: a `TASK_HANDOFF.<node-id>.md` path.
> Output: `TASK_RESULT.<node-id>.md`, or one request artifact when blocked.

1. Read the TASK_HANDOFF at the given path. Note: task, dna_slice, convention_slice,
   spec_slice, snapshot_slice, contract_snapshot, written_files, boundary, feedback.
2. Read actual existing files from disk for every path listed in `written_files`,
   `contract_snapshot.source_file`, and task read-only files. Do not rely on summaries alone.
3. Execute only the assigned node:
   - Contract node: write/update the contract file and produce `CONTRACT_SNAPSHOT.<node-id>.md`.
   - Leaf node: implement only the child/adapter/mapper/repository file allowed by the handoff.
   - Integration node: apply queued `INTEGRATION_REQUEST` entries to shared wiring files.
   - Test node: add or update tests described by the handoff.
4. Obey hard boundaries:
   - Do not call UA/KG, DB, or agent-memory tools directly.
   - Do not edit files outside `allowed_files`.
   - Do not edit frozen contract/base files from a leaf node.
   - Do not edit shared wiring files from a leaf node.
   - Do not introduce dependencies that are absent from the spec or handoff.
5. If context is missing, stop and write `CONTEXT_REQUEST.<node-id>.md`.
6. If a leaf node needs the contract changed, stop and write `CONTRACT_CHANGE_REQUEST.<node-id>.md`.
7. If a leaf node needs registry/config/wiring, write `INTEGRATION_REQUEST.<node-id>.md`
   and continue only if the feature code itself can be completed without editing the shared file.
8. Write changed files to disk.
9. Write `TASK_RESULT.<node-id>.md` with: task_id, changed_files, gate_status set to `PENDING`,
   gate_violations as `[]`, and self_flagged for any unresolved concern.
10. Stop. The orchestrator owns gate execution, retries, stale invalidation, and task advancement.
```

- [ ] **Step 2: Replace reviewer procedure**

Replace the full content of `.agent/procedures/reviewer.md` with:

```markdown
# Procedure: Reviewer (Hybrid Contract DAG verification lane)

> Consumed by the agent acting as final verification reviewer. Input: `CONTRACT_DAG.md`,
> `EXTRACTION_INPUT.md`, all `TASK_RESULT.<node-id>.md`, and all `CONTRACT_SNAPSHOT.<node-id>.md`.
> Output: `EXTRACTION_REPORT.md`.

1. Read `CONTRACT_DAG.md` and verify there are no nodes with status `pending`, `in_progress`,
   `blocked`, or `stale`.
2. Read every `TASK_RESULT.<node-id>.md`. Verify changed files match each node's allowed write boundary.
3. Read every `CONTRACT_SNAPSHOT.<node-id>.md`. Verify leaf nodes reference the current contract version.
4. Read `EXTRACTION_INPUT.md` — the complete set of new/changed files, not a top-k slice.
5. Enumerate sibling classes:
   - If a code-graph capability is available, query it for siblings.
   - Otherwise, group changed files by business essence using disk-fallback.
6. For each group with high logic overlap, flag a Template Method opportunity:
   - shared steps in base;
   - child-specific abstract/protected hooks;
   - files affected;
   - risk if ignored.
7. Write `EXTRACTION_REPORT.md` with verdict `CLEAN` or `FLAG`, clusters, contract-version findings,
   boundary findings, and suggested follow-up.
8. HP-10/HP-11 style findings are recommendations. Do not auto-refactor and do not block archive
   unless the orchestrator or spec-validator has a hard failure.
```

- [ ] **Step 3: Verify docs contain required protocol phrases**

Run:

```bash
rg -n "CONTEXT_REQUEST|CONTRACT_CHANGE_REQUEST|INTEGRATION_REQUEST|contract_snapshot|Do not call UA" .agent/procedures/executor.md .agent/procedures/reviewer.md
```

Expected: matches in executor and reviewer files.

- [ ] **Step 4: Commit**

```bash
git add .agent/procedures/executor.md .agent/procedures/reviewer.md
git commit -m "docs(procedures): define hybrid contract dag executor roles"
```

---

### Task 5: Update Phase 3 Workflow

**Files:**
- Modify: `.agent/workflows/task.md`

- [ ] **Step 1: Edit Phase 3 micro-loop section**

In `.agent/workflows/task.md`, replace the current Phase 3 step `5. Khi user đồng ý — **Orchestrate micro-loop (SP1b)**` block with this text:

```markdown
5. Khi user đồng ý — **Orchestrate Hybrid Contract DAG micro-loop (SP1d)**:
   a. Build `KNOWLEDGE_PACK.md` from REQUIREMENT, EXPLORE_CONTEXT, knowledge-snapshot,
      conventions, author-dna, OpenSpec artifacts, UA/KG evidence, db-explorer evidence, and relevant archive/memory.
      - If task complexity = `complex` and KG graph is unavailable/stale: BLOCK unless user explicitly overrides.
      - If task touches DB and db-explorer evidence is missing: BLOCK and request db-explorer.
      - Record confidence and overrides in AGENT_TRANSPARENCY.
   b. Build `CONTRACT_DAG.md` from OpenSpec `tasks.md`:
      - `contract` nodes: base/interface/abstract class/DTO/schema/public contract.
      - `leaf` nodes: child classes/adapters/mappers/repository implementations.
      - `integration` nodes: DI/wiring/registry/config/migration registration.
      - `test` nodes: unit/integration/spec tests.
      - `review` nodes: extraction/verification.
   c. Run Contract Lane sequentially:
      - Assemble `TASK_HANDOFF.<node-id>.md` with Knowledge Pack slice, DNA slice, convention slice,
        architecture boundary, allowed/read-only files, and feedback if retrying.
      - Dispatch executor by `.agent/profiles/execution-mode.yaml`.
      - Run mechanical gate + semantic surface-check.
      - On PASS, generate/freeze `CONTRACT_SNAPSHOT.<node-id>.md` with contract_version.
      - On FAIL after max retries, mark node `blocked` and stop for user decision.
   d. Run Implementation Lane in safe parallel batches:
      - Only nodes with dependencies done and no write conflicts can share a batch.
      - Leaf nodes receive `contract_snapshot` and `contract_version`.
      - Leaf nodes cannot edit frozen contract/base files or shared wiring files.
      - Missing context produces `CONTEXT_REQUEST.<node-id>.md`; orchestrator enriches Knowledge Pack and resumes.
      - Missing contract hook produces `CONTRACT_CHANGE_REQUEST.<node-id>.md`; if accepted, rerun Contract Lane,
        increment contract_version, and mark downstream nodes stale.
      - Wiring needs produce `INTEGRATION_REQUEST.<node-id>.md`.
   e. Run Integration Lane:
      - Integration Agent is the only executor allowed to edit shared registry/config/wiring files.
      - It consumes all `INTEGRATION_REQUEST.*.md` files and applies deterministic, grouped changes.
   f. Run Verification Lane:
      - Ensure no nodes remain `pending`, `in_progress`, `blocked`, or `stale`.
      - Run compile/typecheck/tests when available.
      - Run spec-validator post checks, including contract_version and allowed-file checks.
      - Run extraction review against all changed files and present `EXTRACTION_REPORT.md` to user.
   g. Persist state in `.knowledge-layer/active/microloop/` so Pha 3 can resume after session truncation.
```

- [ ] **Step 2: Update Pha 3 post-phase self-check**

In the Phase 3 post-phase self-check list, add these checklist items before knowledge-curator archive:

```markdown
   - `[ ]` KNOWLEDGE_PACK.md exists and confidence/override status is recorded.
   - `[ ]` CONTRACT_DAG.md has no `pending` / `in_progress` / `blocked` / `stale` nodes.
   - `[ ]` Every leaf node with `contract_ref` uses the current `contract_version`.
   - `[ ]` All `CONTEXT_REQUEST`, `CONTRACT_CHANGE_REQUEST`, and `INTEGRATION_REQUEST` files are resolved or explicitly documented.
```

- [ ] **Step 3: Verify workflow references new artifacts**

Run:

```bash
rg -n "Hybrid Contract DAG|KNOWLEDGE_PACK|CONTRACT_DAG|CONTRACT_SNAPSHOT|CONTEXT_REQUEST|CONTRACT_CHANGE_REQUEST|INTEGRATION_REQUEST" .agent/workflows/task.md
```

Expected: all artifact names are present.

- [ ] **Step 4: Commit**

```bash
git add .agent/workflows/task.md
git commit -m "docs(workflow): upgrade apply phase to hybrid contract dag"
```

---

### Task 6: Update Spec Validator Skill

**Files:**
- Modify: `.agent/skills/spec-validator/SKILL.md`

- [ ] **Step 1: Add Hybrid Contract DAG validation subsection**

In `.agent/skills/spec-validator/SKILL.md`, after section `3.3 post_apply_verify`, add:

```markdown
### 3.4 `post_apply_contract_dag_check(contract_dag_path, changed_files)`

```
INPUT:
  contract_dag_path — .knowledge-layer/active/microloop/CONTRACT_DAG.md
  changed_files     — danh sách file đã thay đổi

STEPS:
1. Đọc CONTRACT_DAG.md.
2. Fail nếu còn node status `pending`, `in_progress`, `blocked`, hoặc `stale`.
3. Với mỗi node:
   - Kiểm tra changed_files của node nằm trong `writes`.
   - Nếu node type = `leaf`, kiểm tra node không ghi file thuộc contract/base.
   - Nếu node có `contract_ref`, kiểm tra version bằng contract node hiện tại.
4. Đọc các request artifact nếu tồn tại:
   - CONTEXT_REQUEST.*.md
   - CONTRACT_CHANGE_REQUEST.*.md
   - INTEGRATION_REQUEST.*.md
5. Fail nếu request chưa được resolved hoặc chưa được ghi rõ trong AGENT_TRANSPARENCY.

RESULT:
  → PASS: DAG hoàn tất, không stale, không boundary violation.
  → BLOCK: có node chưa xong, stale, contract_version mismatch, hoặc unresolved request.

Ghi vào AGENT_TRANSPARENCY:
  "[CONTRACT-DAG-CHECK] {PASS|BLOCK} — {issues}"
```
```

- [ ] **Step 2: Update integration section**

In section `4. Tích hợp với /task apply`, update the flow block to include:

```markdown
  ↓
Hybrid Contract DAG micro-loop
  ↓
spec-validator.post_apply_contract_dag_check()
  ↓
spec-validator.post_apply_verify()
```

- [ ] **Step 3: Update outputs**

In `## Đầu ra`, add this bullet:

```markdown
- **Kết quả Contract DAG check**: `PASS` hoặc `BLOCK` — xác nhận không còn stale node, contract mismatch, hoặc unresolved request.
```

- [ ] **Step 4: Run skill lint**

Run:

```bash
python3 .agent/tools/skill-lint/validate_skills.py
```

Expected: `spec-validator` remains `PASS`, total `14/14 skills PASS`.

- [ ] **Step 5: Commit**

```bash
git add .agent/skills/spec-validator/SKILL.md
git commit -m "docs(spec-validator): add contract dag post-apply checks"
```

---

### Task 7: Update Tool and Execution Rules

**Files:**
- Modify: `.agent/rules/rules-tool.md`
- Modify: `.agent/rules/rules-exec.md`

- [ ] **Step 1: Add subagent tool boundary rule**

In `.agent/rules/rules-tool.md`, after `R-Tool-6`, add:

```markdown
### [CRITICAL] R-Tool-8: Coding subagents không tự enrich context

Trong Pha 3 Hybrid Contract DAG:

- Coding subagents chỉ được đọc `TASK_HANDOFF.<node-id>.md`, files được handoff cho phép, và artifacts cùng node.
- Coding subagents KHÔNG được gọi trực tiếp:
  - Understand-Anything / KG tools
  - db-explorer / DB tools
  - agent-memory tools
  - Socraticode search như nguồn khám phá chính
- Nếu thiếu context, subagent PHẢI ghi `CONTEXT_REQUEST.<node-id>.md`.
- Chỉ orchestrator được quyền enrich `KNOWLEDGE_PACK.md`, và mọi enrichment phải ghi vào AGENT_TRANSPARENCY.

Lý do: codebase lớn cần knowledge-first evidence đã verify; executor không được tự suy đoán hoặc mở rộng blast radius.
```

- [ ] **Step 2: Add execution budget rule**

In `.agent/rules/rules-exec.md`, after `R-Exec-3`, add:

```markdown
### [CRITICAL] R-Exec-3b: Hybrid Contract DAG context-request budget

Trong Pha 3 Hybrid Contract DAG:

- Mỗi node được tối đa 2 `CONTEXT_REQUEST` vòng enrich trước khi hardstop.
- Mỗi node được tối đa 2 contract/gate retry trước khi chuyển `blocked`.
- Parallel leaf batch chỉ hợp lệ khi:
  - mọi dependency đã `done`;
  - không có write conflict;
  - không node nào dùng stale contract_version;
  - integration/shared wiring được gom về Integration Lane.
- Khi đạt hardstop, orchestrator ghi vào AGENT_TRANSPARENCY:
  `[HCD-BLOCKED] node={node_id} reason={reason} requests={n} retries={n}`
  và hỏi user quyết định.
```

- [ ] **Step 3: Verify rules are discoverable**

Run:

```bash
rg -n "R-Tool-8|R-Exec-3b|CONTEXT_REQUEST|Hybrid Contract DAG" .agent/rules/rules-tool.md .agent/rules/rules-exec.md
```

Expected: both new rule IDs are present.

- [ ] **Step 4: Commit**

```bash
git add .agent/rules/rules-tool.md .agent/rules/rules-exec.md
git commit -m "docs(rules): add hybrid contract dag boundaries"
```

---

### Task 8: Add End-to-End Fixture Tests

**Files:**
- Create: `.agent/tools/microloop-orchestrator/tests/test_hybrid_contract_dag.py`

- [ ] **Step 1: Create fixture tests**

Create `.agent/tools/microloop-orchestrator/tests/test_hybrid_contract_dag.py`:

```python
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

import orchestrator  # noqa: E402


def _nodes():
    return [
        {
            "id": "C1",
            "type": "contract",
            "desc": "Create BasePaymentProcessor",
            "depends_on": [],
            "reads": [],
            "writes": ["src/BasePaymentProcessor.java"],
            "contract_version": "v1",
            "status": "pending",
        },
        {
            "id": "L1",
            "type": "leaf",
            "desc": "Create CardPaymentProcessor",
            "depends_on": ["C1"],
            "reads": ["src/BasePaymentProcessor.java"],
            "writes": ["src/CardPaymentProcessor.java"],
            "contract_ref": {"node_id": "C1", "version": "v1"},
            "status": "pending",
        },
        {
            "id": "L2",
            "type": "leaf",
            "desc": "Create BankPaymentProcessor",
            "depends_on": ["C1"],
            "reads": ["src/BasePaymentProcessor.java"],
            "writes": ["src/BankPaymentProcessor.java"],
            "contract_ref": {"node_id": "C1", "version": "v1"},
            "status": "pending",
        },
        {
            "id": "I1",
            "type": "integration",
            "desc": "Register processors",
            "depends_on": ["L1", "L2"],
            "reads": [],
            "writes": ["src/PaymentProcessorRegistry.java"],
            "status": "pending",
        },
    ]


def test_contract_dag_orders_base_children_then_integration():
    ordered = orchestrator.topo_sort_nodes(_nodes())
    assert [node["id"] for node in ordered] == ["C1", "L1", "L2", "I1"]


def test_leaf_nodes_can_share_parallel_batch_after_contract():
    leaf_nodes = [node for node in _nodes() if node["type"] == "leaf"]
    batches = orchestrator.plan_parallel_batches(leaf_nodes)
    assert len(batches) == 1
    assert [node["id"] for node in batches[0]] == ["L1", "L2"]


def test_integration_waits_for_leaf_nodes():
    nodes = _nodes()
    integration = [node for node in nodes if node["id"] == "I1"][0]
    assert integration["depends_on"] == ["L1", "L2"]


def test_contract_change_marks_all_old_children_stale():
    dag = {"nodes": _nodes()}
    dag["nodes"][0]["contract_version"] = "v2"
    updated = orchestrator.invalidate_contract_dependents(dag, "C1", "v2")
    statuses = {node["id"]: node["status"] for node in updated["nodes"]}
    assert statuses["L1"] == "stale"
    assert statuses["L2"] == "stale"
    assert statuses["I1"] == "pending"
```

- [ ] **Step 2: Run new fixture test**

Run:

```bash
python3 -m pytest .agent/tools/microloop-orchestrator/tests/test_hybrid_contract_dag.py -v
```

Expected: PASS.

- [ ] **Step 3: Run all microloop tests**

Run:

```bash
python3 -m pytest .agent/tools/microloop-orchestrator/tests/ -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add .agent/tools/microloop-orchestrator/tests/test_hybrid_contract_dag.py
git commit -m "test(microloop): cover hybrid contract dag fixture"
```

---

### Task 9: Final Documentation and Verification

**Files:**
- Modify only if needed after previous tasks: `docs/superpowers/specs/2026-06-18-hybrid-contract-dag-subagent-design.md`

- [ ] **Step 1: Run all relevant tests**

Run:

```bash
python3 -m pytest .agent/tools/microloop-orchestrator/tests/ -v
python3 .agent/tools/skill-lint/validate_skills.py
git diff --check
```

Expected:

- all microloop tests pass;
- skill lint reports `14/14 skills PASS`;
- `git diff --check` prints no errors.

- [ ] **Step 2: Verify design coverage**

Run:

```bash
rg -n "KNOWLEDGE_PACK|CONTRACT_DAG|CONTRACT_SNAPSHOT|CONTEXT_REQUEST|CONTRACT_CHANGE_REQUEST|INTEGRATION_REQUEST|R-Tool-8|R-Exec-3b" .agent .knowledge-layer/templates docs/superpowers/specs/2026-06-18-hybrid-contract-dag-subagent-design.md
```

Expected: each artifact and rule ID appears in implementation files or templates.

- [ ] **Step 3: Inspect final git state**

Run:

```bash
git status --short
git log --oneline -8
```

Expected: working tree clean after the final commit, with task commits visible.

- [ ] **Step 4: Commit any final doc adjustments**

If Step 1 or Step 2 required documentation fixes, commit them:

```bash
git add docs/superpowers/specs/2026-06-18-hybrid-contract-dag-subagent-design.md
git commit -m "docs(spec): align hybrid contract dag implementation details"
```

If no documentation fixes were needed, do not create an empty commit.

---

## Self-Review Notes

Spec coverage:

- Knowledge-first gate is covered by Tasks 2, 3, 5, and 7.
- Contract DAG artifacts are covered by Tasks 1, 2, 3, and 8.
- Base/child contract versioning and stale invalidation are covered by Tasks 2 and 8.
- Context, contract-change, and integration request protocols are covered by Tasks 1, 3, 4, 5, and 7.
- Subagent boundaries are covered by Tasks 4 and 7.
- Spec-validator and final verification gates are covered by Tasks 6 and 9.

Implementation boundaries:

- The plan does not replace AMAP flow.
- The plan does not require real subagent support to pass tests.
- The plan keeps `inline-reload` as fallback while preserving filesystem state.
