"""Guard: operational Maika templates must not hardcode provider memory tool names.

Concrete memory tool names belong ONLY in cli/platforms/ mappings, the provider
setup recipe, fixed degrade/status strings, and historical docs (see C-27 spec
§5 Phần 5). Operational rules/skills/procedures/workflows must reference memory
via {{ tools.dynamic_memory_* }} so the provider stays swappable.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
Maika = REPO_ROOT / ".maika"
OPERATIONAL_DIRS = ("rules", "skills", "procedures", "workflows")

# \b word-boundary => the abstract op `dynamic_memory_save` (preceded by `_`)
# is NOT matched; only standalone provider tool names are.
LITERAL = re.compile(
    r"\bmemory_(?:smart_search|recall|sessions|audit|health|save|governance_delete)\b"
)


def test_no_hardcoded_memory_tool_names_in_operational_templates():
    offenders = []
    for sub in OPERATIONAL_DIRS:
        base = Maika / sub
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if LITERAL.search(line):
                    rel = path.relative_to(REPO_ROOT)
                    offenders.append(f"{rel}:{lineno}: {line.strip()}")
    assert offenders == [], (
        "Hardcoded provider memory tool names found in operational templates "
        "(use {{ tools.dynamic_memory_* }} instead):\n" + "\n".join(offenders)
    )
