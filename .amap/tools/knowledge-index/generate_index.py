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
