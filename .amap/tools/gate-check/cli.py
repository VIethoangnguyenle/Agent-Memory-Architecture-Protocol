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
