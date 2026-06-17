"""Extraction review (HP-10/11) disk-fallback: group new files by content similarity,
flag clusters as Template Method candidates. No UA graph, no vector top-k (spec §8)."""


def _lines(text):
    return {ln.strip() for ln in text.splitlines() if len(ln.strip()) >= 4}


def similarity(a, b):
    la, lb = _lines(a), _lines(b)
    if not la or not lb:
        return 0.0
    return len(la & lb) / len(la | lb)


def find_clusters(files, threshold=0.7):
    """Union near-duplicate files into clusters. Returns list of clusters (each a list of files)."""
    parent = list(range(len(files)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            if similarity(files[i]["content"], files[j]["content"]) >= threshold:
                parent[find(i)] = find(j)
    groups = {}
    for i, f in enumerate(files):
        groups.setdefault(find(i), []).append(f)
    return [g for g in groups.values() if len(g) > 1]


def build_report(files, threshold=0.7):
    clusters = find_clusters(files, threshold)
    return {
        "verdict": "FLAG" if clusters else "CLEAN",
        "clusters": [
            {
                "files": [f["path"] for f in c],
                "suggestion": "Extract Template Method: base class holds shared steps, "
                              "abstract methods for the differing step (HP-10/HP-11).",
            }
            for c in clusters
        ],
    }
