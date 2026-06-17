# Claude Handoff — Hybrid Contract DAG Subagent Coding

> Date: 2026-06-18  
> Repo: `/home/zane/Desktop/agent-memory-arch-v3`  
> Branch: `main`  
> Purpose: Continue implementing Hybrid Contract DAG Subagent Coding after Codex quota interruption.

---

## 1. Must-Read Context

Read these files first, in order:

1. `AGENTS.md`
2. `.agent/rules/RULES.md`
3. `.agent/rules/rules-flow.md`
4. `.agent/rules/rules-tool.md`
5. `.agent/rules/rules-exec.md`
6. `.agent/rules/rules-knowledge.md`
7. `.agent/rules/rules-guard.md`
8. `docs/superpowers/specs/2026-06-18-hybrid-contract-dag-subagent-design.md`
9. `docs/superpowers/plans/2026-06-18-hybrid-contract-dag-subagent.md`

The user explicitly chose:

- Build directly on `main`, no isolated worktree.
- Execution approach: Subagent-Driven.
- Product context: AMAP is an internal product for large, complex codebases.
- Core architectural priority: **knowledge-first** using Understand-Anything/KG, `db-explorer`, and agent long-term memory before coding.

Important design principle:

> Coding subagents are executors, not architecture explorers. They must receive verified slices from `KNOWLEDGE_PACK`; if context is missing, they write a request artifact instead of guessing.

---

## 2. Current Git State

Latest relevant commits already made:

```txt
e9f1280 fix(microloop): reject invalid contract dag topology
e4ff24f feat(microloop): add hybrid contract dag schemas
1ec5dd9 docs(plan): implement hybrid contract dag subagent coding
122d308 docs(spec): design hybrid contract dag subagent coding
```

As of handoff, full microloop tests pass:

```bash
python3 -m pytest .agent/tools/microloop-orchestrator/tests/ -v
```

Observed result:

```txt
49 passed in 0.11s
```

Run this before continuing:

```bash
git status --short
git log --oneline -8
python3 -m pytest .agent/tools/microloop-orchestrator/tests/ -v
```

Expected before Codex spawned Task 2 worker: clean tree and 49 tests passing. At the moment this handoff was written,
there is a partial Task 2 RED-state edit in `test_protocol.py`; see section 4.

---

## 3. Completed Work

### Completed: Design Spec

File:

- `docs/superpowers/specs/2026-06-18-hybrid-contract-dag-subagent-design.md`

Commit:

```txt
122d308 docs(spec): design hybrid contract dag subagent coding
```

### Completed: Implementation Plan

File:

- `docs/superpowers/plans/2026-06-18-hybrid-contract-dag-subagent.md`

Commit:

```txt
1ec5dd9 docs(plan): implement hybrid contract dag subagent coding
```

### Completed: Plan Task 1 — Filesystem Contract Schemas

Files changed:

- `.agent/tools/microloop-orchestrator/contract.py`
- `.agent/tools/microloop-orchestrator/tests/test_contract.py`

Commits:

```txt
e4ff24f feat(microloop): add hybrid contract dag schemas
e9f1280 fix(microloop): reject invalid contract dag topology
```

Task 1 review history:

- Spec compliance review: approved.
- Code quality review initially requested fixes:
  - reject duplicate Contract DAG node IDs;
  - reject dependency cycles.
- Fix commit `e9f1280` addressed both.
- Re-review approved.

Current Task 1 test evidence:

```txt
test_contract.py: 11 passed
full microloop suite: 49 passed
```

---

## 4. In Progress / Potentially Abandoned Work

Codex spawned a worker for Plan Task 2 just before quota interruption:

- Worker nickname: Dewey
- Agent id: `019ed6af-3b8a-7e83-b131-35380e90a806`
- Assigned task: Plan Task 2, Contract DAG Orchestrator Helpers
- Owned files:
  - `.agent/tools/microloop-orchestrator/orchestrator.py`
  - `.agent/tools/microloop-orchestrator/tests/test_protocol.py`

The wait was interrupted after about 15 seconds. Some work landed in the working tree, but no Task 2 commit was observed.

Current partial Task 2 state:

- Modified file: `.agent/tools/microloop-orchestrator/tests/test_protocol.py`
- Change: the six Task 2 tests from the plan were appended.
- No corresponding implementation in `orchestrator.py` has been confirmed.
- This is a valid TDD RED state; continue by running the Task 2 test command and implementing the missing helpers.

Before continuing, check:

```bash
git status --short
git log --oneline -8
```

If no new Task 2 commit exists after `e9f1280`, continue from the partial RED tests already in
`test_protocol.py`. If a Task 2 commit exists, review it against the plan before proceeding.

---

## 5. Next Task To Continue

Continue from:

```txt
Task 2: Add Contract DAG Orchestrator Helpers
```

Plan file:

```txt
docs/superpowers/plans/2026-06-18-hybrid-contract-dag-subagent.md
```

Task 2 owned files:

- `.agent/tools/microloop-orchestrator/orchestrator.py`
- `.agent/tools/microloop-orchestrator/tests/test_protocol.py`

Task 2 required helpers:

- `topo_sort_nodes(nodes)`
- `find_write_conflicts(nodes)`
- `plan_parallel_batches(nodes)`
- `invalidate_contract_dependents(dag, contract_node_id, new_version)`
- `check_knowledge_gate(knowledge_pack, complexity="standard", user_override=False)`
- `build_contract_handoff(...)`

Task 2 required tests are fully written in the plan. Follow TDD:

1. Confirm the failing tests are already appended to `test_protocol.py`. If they are missing, append them from the plan.
2. Run:

   ```bash
   python3 -m pytest .agent/tools/microloop-orchestrator/tests/test_protocol.py -v
   ```

   Expected red: missing helper functions.

3. Implement helpers in `orchestrator.py`.
4. Run:

   ```bash
   python3 -m pytest .agent/tools/microloop-orchestrator/tests/test_protocol.py -v
   python3 -m pytest .agent/tools/microloop-orchestrator/tests/ -v
   ```

5. Commit:

   ```bash
   git add .agent/tools/microloop-orchestrator/orchestrator.py .agent/tools/microloop-orchestrator/tests/test_protocol.py
   git commit -m "feat(microloop): add contract dag orchestration helpers"
   ```

After Task 2, run spec compliance and code quality review before moving to Task 3.

---

## 6. Remaining Plan Tasks

After Task 2, continue with:

```txt
Task 3: Add Knowledge Pack and DAG templates
Task 4: Update executor and reviewer procedures
Task 5: Update Phase 3 workflow
Task 6: Update spec-validator skill
Task 7: Update tool and execution rules
Task 8: Add end-to-end fixture tests
Task 9: Final documentation and verification
```

Follow the plan exactly unless tests reveal a necessary small correction.

Use frequent commits, one task per commit unless a reviewer requests a fix commit.

---

## 7. Required Verification Gates

At minimum after each coding task:

```bash
python3 -m pytest .agent/tools/microloop-orchestrator/tests/ -v
git diff --check
```

After any skill docs change:

```bash
python3 .agent/tools/skill-lint/validate_skills.py
```

Final verification from Task 9:

```bash
python3 -m pytest .agent/tools/microloop-orchestrator/tests/ -v
python3 .agent/tools/skill-lint/validate_skills.py
git diff --check
rg -n "KNOWLEDGE_PACK|CONTRACT_DAG|CONTRACT_SNAPSHOT|CONTEXT_REQUEST|CONTRACT_CHANGE_REQUEST|INTEGRATION_REQUEST|R-Tool-8|R-Exec-3b" .agent .knowledge-layer/templates docs/superpowers/specs/2026-06-18-hybrid-contract-dag-subagent-design.md
```

Expected final state:

- microloop tests pass;
- skill lint reports all skills pass;
- diff check clean;
- all new artifacts/rules discoverable;
- git working tree clean after final commit.

---

## 8. Design Rules To Preserve

Do not weaken these decisions:

- AMAP remains knowledge-first.
- Subagents do not call UA/KG, DB, Socraticode, or agent-memory directly in Phase 3.
- Missing context becomes `CONTEXT_REQUEST`, not guessing.
- Leaf agents cannot edit frozen contract/base files.
- Leaf agents cannot edit shared wiring/config files.
- Shared wiring/config goes through Integration Lane.
- Contract changes create `CONTRACT_CHANGE_REQUEST`; accepted changes increment contract version and mark downstream nodes stale.
- Filesystem artifacts are durable state for resume.
- `inline-reload` remains supported as fallback; real subagent support is an optimization, not a requirement.

---

## 9. Suggested First Message To User

Use this shape:

```txt
chồng yêu — Claude đã nhận handoff. Tôi sẽ tiếp tục từ Task 2 của plan Hybrid Contract DAG, kiểm tra git/test baseline trước, rồi triển khai theo TDD và commit từng task.
```

Then run the baseline commands in section 2.
