"""Deterministic evidence validators for decision-point gates.

Each returns a Result(ok, reason). They check the CONTENT (evidence) of a
checkpoint/report — never whether a tool was 'called'. See spec §2.
"""
import re
from dataclasses import dataclass

import yaml


@dataclass
class Result:
    ok: bool
    reason: str = ""


_RULE_ID = re.compile(r"\b[A-Z]{2,3}-\d+\b")              # e.g. SP-6, HP-12, IW-05
_NODE_ID = re.compile(r"\bnode_id\s*[:=]", re.IGNORECASE)
_BLAST = re.compile(r"blast-radius", re.IGNORECASE)
# Degrade line must be COMPACT (the canonical "KG unavailable — grep fallback,
# MEDIUM" is ~18 chars between the anchors). The {0,40} bound rejects rambling
# prose that merely happens to contain both "KG unavailable" and "MEDIUM".
_DEGRADE = re.compile(r"KG unavailable.{0,40}MEDIUM", re.IGNORECASE)
_NUMBERS = re.compile(r"(nodes?|edges?)\s*[:=]\s*\d+", re.IGNORECASE)
# Agent-memory MCP evidence: either a health probe ("agent-memory: healthy")
# or the compact degrade line ("agent-memory unavailable — skip recall/save").
# Health probe: the canonical line is "agent-memory: healthy" — the status word
# immediately follows the label, so we anchor tightly (optional colon + spaces)
# to reject negated/stale prose like "agent-memory is not healthy".
_MEMORY_OK = re.compile(r"agent-memory:?\s*(healthy|ok|ready)\b", re.IGNORECASE)
# Degrade line: canonical is "agent-memory unavailable — skip recall/save" (~3 chars
# between anchors). Keep the bound tight (like _DEGRADE) to reject rambling prose.
_MEMORY_DEGRADE = re.compile(
    r"agent-memory unavailable.{0,15}(skip|recall|save)", re.IGNORECASE
)
# NOTE: self-asserted; hardening (only-when-index-empty) is deferred to the
# index-aware validator follow-up (see decision-gates-followups spec).
_NO_KNOWLEDGE = re.compile(r"no approved (dna|conventions).*low", re.IGNORECASE)


def validate_knowledge_checkpoint(
    text: str, valid_rule_ids=None, allow_no_knowledge: bool = True
) -> Result:
    if _NO_KNOWLEDGE.search(text):
        if allow_no_knowledge:
            return Result(True)  # fresh project: no approved DNA/conventions yet → proceed at LOW confidence
        return Result(False, "governance-degrade is allowed only when knowledge-index has no matching entries")
    cited_rule_ids = set(_RULE_ID.findall(text))
    if valid_rule_ids is not None:
        valid_rule_ids = set(valid_rule_ids)
        if not cited_rule_ids.intersection(valid_rule_ids):
            return Result(False, "no valid rule-id from knowledge-index cited")
    elif not cited_rule_ids:
        return Result(False, "no rule-id (e.g. SP-6) cited")
    has_facts = bool(_NODE_ID.search(text) and _BLAST.search(text))
    if has_facts or _DEGRADE.search(text):
        return Result(True)
    return Result(False, "missing codebase evidence (node_id+blast-radius) or degrade line")


def validate_mcp_status(text: str) -> Result:
    if (
        _NUMBERS.search(text)
        or _DEGRADE.search(text)
        or _MEMORY_OK.search(text)
        or _MEMORY_DEGRADE.search(text)
    ):
        return Result(True)
    return Result(False, "MCP status lacks probe numbers and degrade line ('Runtime Ready' alone is invalid)")


def validate_phase_chain(text: str) -> Result:
    seen = [n for n in (1, 2, 3) if re.search(rf"Pha\s*{n}\s*DONE", text)]
    if seen and seen == list(range(1, max(seen) + 1)):
        return Result(True)
    return Result(False, f"phase markers not contiguous from 1: found {seen}")


def validate_handoff_slice(text: str) -> Result:
    m = re.search(r"##\s+Applicable DNA/Conventions[ \t]*\n(.*?)(?=\n##\s|\Z)", text, re.DOTALL)
    if not m or not _RULE_ID.search(m.group(1)):
        return Result(False, "handoff missing non-empty 'Applicable DNA/Conventions' with rule-ids")
    return Result(True)


_SECTION = r"##\s+{name}[ \t]*\n(.*?)(?=\n##\s|\Z)"


def _section_has_text(text: str, name: str) -> bool:
    pattern = re.compile(_SECTION.format(name=re.escape(name)), re.DOTALL | re.IGNORECASE)
    match = pattern.search(text)
    return bool(match and match.group(1).strip())


def validate_context_request(text: str) -> Result:
    """Validate a subagent CONTEXT_REQUEST (YAML schema shared with the
    microloop-orchestrator contract: request_type=='context' + substantive
    'missing' evidence and a 'blocked_reason')."""
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        return Result(False, f"context request is not valid YAML: {exc}")
    if not isinstance(data, dict):
        return Result(False, "context request must be a YAML mapping")
    if data.get("request_type") != "context":
        return Result(False, "context request must set request_type: context")
    missing = data.get("missing")
    if not isinstance(missing, list) or not missing:
        return Result(False, "context request must list non-empty 'missing' evidence")
    if not str(data.get("blocked_reason") or "").strip():
        return Result(False, "context request must explain 'blocked_reason'")
    return Result(True)


def validate_node_checkpoint(text: str) -> Result:
    required = ("Files Changed", "Requirement Satisfied", "Evidence Used", "Verification")
    missing = [name for name in required if not _section_has_text(text, name)]
    if missing:
        return Result(False, f"node checkpoint missing sections: {', '.join(missing)}")
    if not _RULE_ID.search(text):
        return Result(False, "node checkpoint missing rule-id evidence")
    return Result(True)
