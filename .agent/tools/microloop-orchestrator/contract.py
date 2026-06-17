"""Micro-loop contract: load/dump/validate the 5 filesystem artifacts.

Artifacts are YAML documents embedded as the body of a .md file (front-matter
style is avoided; the file IS the yaml). Keeps SP1a's dict-based simplicity.
"""
import yaml
from pathlib import Path

VALID_STATUS = {"pending", "in_progress", "done", "blocked"}
VALID_MODE = {"subagent", "fresh-session", "inline-reload"}
VALID_NODE_STATUS = {"pending", "in_progress", "done", "blocked", "stale"}
VALID_NODE_TYPE = {"contract", "leaf", "integration", "test", "review"}
VALID_CONFIDENCE = {"CAO", "TRUNG-BINH", "THAP"}


def _load(path):
    return yaml.safe_load(Path(path).read_text()) or {}


def _dump(doc, path):
    Path(path).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))


def validate_queue(q):
    for key in ("ticket_id", "spec_path", "execution_mode", "tasks"):
        if key not in q:
            raise ValueError(f"queue missing key: {key}")
    if q["execution_mode"] not in VALID_MODE:
        raise ValueError(f"bad execution_mode: {q['execution_mode']}")
    for t in q["tasks"]:
        if t.get("status") not in VALID_STATUS:
            raise ValueError(f"bad task status: {t.get('status')}")
    return q


def load_queue(path):
    return validate_queue(_load(path))


def dump_queue(q, path):
    validate_queue(q)
    _dump(q, path)


def validate_handoff(h):
    for key in ("task", "dna_slice", "spec_slice", "snapshot_slice", "written_files", "boundary"):
        if key not in h:
            raise ValueError(f"handoff missing key: {key}")
    return h


def load_handoff(path):
    return validate_handoff(_load(path))


def dump_handoff(h, path):
    validate_handoff(h)
    _dump(h, path)


def validate_result(r):
    for key in ("task_id", "changed_files", "gate_status"):
        if key not in r:
            raise ValueError(f"result missing key: {key}")
    return r


def load_result(path):
    return validate_result(_load(path))


def dump_result(r, path):
    validate_result(r)
    _dump(r, path)


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
