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
