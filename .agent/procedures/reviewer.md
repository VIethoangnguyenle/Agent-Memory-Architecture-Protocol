# Procedure: Reviewer (extraction review, once per ticket)

> Consumed by the agent acting as extraction reviewer. Input: EXTRACTION_INPUT.md
> (ALL new/changed files). Output: EXTRACTION_REPORT.md. HP-10/11.

1. Read EXTRACTION_INPUT.md — the COMPLETE set of new files (not a top-k slice).
2. Enumerate sibling classes:
   - If a code-graph capability (UA graph) is available, query it for siblings.
   - Otherwise (disk-fallback), group the files yourself by BUSINESS ESSENCE
     (HP-11 — not by action name).
3. For each group with ≥70% logic overlap, flag a Template Method opportunity
   (HP-10): base class holds shared steps, abstract methods for the differing step.
4. Write EXTRACTION_REPORT.md: verdict (FLAG|CLEAN), clusters (files + suggestion).
5. HP-10/11 are FLAG_AND_WARN — present as recommendation. Do NOT auto-refactor or
   block. The user decides.
