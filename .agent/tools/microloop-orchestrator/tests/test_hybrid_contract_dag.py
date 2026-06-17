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
