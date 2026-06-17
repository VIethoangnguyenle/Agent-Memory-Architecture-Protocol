from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import extraction  # noqa: E402

# A and B share 6 method lines, differ only in the last; class lines also differ.
# Jaccard = 6 / 10 = 0.6 — above the 0.5 cluster threshold.
A = "public class Xa {\n  validate();\n  enrich();\n  transform();\n  route();\n  persist();\n  log();\n  audit();\n}"
B = "public class Xb {\n  validate();\n  enrich();\n  transform();\n  route();\n  persist();\n  log();\n  notify();\n}"
C = "public class Zz {\n  totallyDifferent();\n  unrelated();\n}"

def test_similarity_high_for_near_duplicates():
    assert extraction.similarity(A, B) >= 0.5

def test_similarity_low_for_unrelated():
    assert extraction.similarity(A, C) < 0.3

def test_find_clusters_groups_duplicates():
    files = [
        {"path": "Xa.java", "content": A},
        {"path": "Xb.java", "content": B},
        {"path": "Zz.java", "content": C},
    ]
    clusters = extraction.find_clusters(files, threshold=0.5)
    paths = sorted([f["path"] for c in clusters for f in c])
    assert "Xa.java" in paths and "Xb.java" in paths
    assert len(clusters) == 1  # only the duplicate pair clusters

def test_build_report_flags_template_method():
    files = [{"path": "Xa.java", "content": A}, {"path": "Xb.java", "content": B}]
    report = extraction.build_report(files, threshold=0.5)
    assert report["verdict"] in ("FLAG", "CLEAN")
    assert report["verdict"] == "FLAG"
    assert "Template Method" in report["clusters"][0]["suggestion"]
