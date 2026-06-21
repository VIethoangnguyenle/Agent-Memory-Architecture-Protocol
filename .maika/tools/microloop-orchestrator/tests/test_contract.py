from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import contract  # noqa: E402

def test_queue_roundtrip(tmp_path):
    q = {
        "ticket_id": "ABC-1",
        "spec_path": "openspec/changes/abc-1/",
        "execution_mode": "inline-reload",
        "tasks": [
            {"id": "T1", "desc": "base", "depends_on": [], "status": "pending", "retries": 0},
        ],
    }
    p = tmp_path / "TASK_QUEUE.md"
    contract.dump_queue(q, str(p))
    loaded = contract.load_queue(str(p))
    assert loaded == q

def test_queue_validate_rejects_bad_status(tmp_path):
    q = {"ticket_id": "X", "spec_path": "p", "execution_mode": "inline-reload",
         "tasks": [{"id": "T1", "desc": "d", "depends_on": [], "status": "nope", "retries": 0}]}
    import pytest
    with pytest.raises(ValueError):
        contract.validate_queue(q)

def test_handoff_roundtrip(tmp_path):
    h = {
        "task": {"id": "T2", "desc": "XaHandler extends BaseXHandler"},
        "dna_slice": {"hard_principles": ["HP-6"], "complexity_thresholds": {}, "style": []},
        "spec_slice": "implement XaHandler",
        "snapshot_slice": "Validation Chain section",
        "written_files": [{"path": "BaseXHandler.java", "summary": "template method"}],
        "boundary": ["do not touch YyyService"],
        "feedback": None,
    }
    p = tmp_path / "TASK_HANDOFF.md"
    contract.dump_handoff(h, str(p))
    assert contract.load_handoff(str(p)) == h

def test_result_roundtrip(tmp_path):
    r = {
        "task_id": "T2",
        "changed_files": [{"path": "XaHandler.java", "change_type": "NEW", "summary": "extends base"}],
        "gate_status": "PASS",
        "gate_violations": [],
        "self_flagged": [],
    }
    p = tmp_path / "TASK_RESULT.md"
    contract.dump_result(r, str(p))
    assert contract.load_result(str(p)) == r

def test_knowledge_pack_roundtrip(tmp_path):
    kp = {
        "ticket_id": "ABC-1",
        "change_id": "add-payment-processor",
        "confidence": {"overall": "CAO", "code_graph": "CAO", "database": "TRUNG-BINH", "memory": "CAO"},
        "sources": {"requirement": ".maika/knowledge/active/REQUIREMENT.md"},
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


def test_contract_dag_rejects_duplicate_node_id():
    dag = {
        "ticket_id": "ABC-1",
        "spec_path": "openspec/changes/x/",
        "contract_version_counter": 1,
        "nodes": [
            {"id": "C1", "type": "contract", "desc": "first", "depends_on": [], "reads": [], "writes": [], "status": "pending"},
            {"id": "C1", "type": "leaf", "desc": "duplicate", "depends_on": [], "reads": [], "writes": [], "status": "pending"},
        ],
    }
    import pytest
    with pytest.raises(ValueError, match="duplicate node id"):
        contract.validate_contract_dag(dag)


def test_contract_dag_rejects_cycle():
    dag = {
        "ticket_id": "ABC-1",
        "spec_path": "openspec/changes/x/",
        "contract_version_counter": 1,
        "nodes": [
            {"id": "C1", "type": "contract", "desc": "base", "depends_on": ["L1"], "reads": [], "writes": [], "status": "pending"},
            {"id": "L1", "type": "leaf", "desc": "child", "depends_on": ["C1"], "reads": [], "writes": [], "status": "pending"},
        ],
    }
    import pytest
    with pytest.raises(ValueError, match="dependency cycle"):
        contract.validate_contract_dag(dag)
