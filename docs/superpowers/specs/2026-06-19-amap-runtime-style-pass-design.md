# AMAP Runtime Style Pass Design

Date: 2026-06-19

## Goal

Clean up the writing style of `.amap/` runtime files so the framework can be cloned into other projects with portable, professional, action-oriented instructions.

The pass must preserve behavior. It must not change rule meaning, phase order, command names, tool calls, file paths, preconditions, abort/warn behavior, output markers, or required artifacts.

## Problem

Several `.amap/` files mix runtime instructions with explanatory or retrospective rationale. Examples include references to specific incidents, prior observed failures, or long explanations of why a rule exists.

This is useful for human design history, but weak for runtime prompts:

- It adds tokens to files agents read during bootstrap or skill execution.
- It can bury the actionable rule under prose.
- It makes cloneable framework files feel project- or history-specific.
- It may imply that a shared rule depends on a past local incident rather than on a stable operating constraint.

## Scope

Primary scope:

- `.amap/rules/*.md`
- `.amap/procedures/*.md`
- `.amap/workflows/*.md`
- `.amap/skills/*/SKILL.md`, excluding OpenSpec skill packages

Secondary scope, only when directly referenced by a runtime skill:

- `.amap/skills/*/references/*.md`
- `.amap/skills/*/assets/*.md`
- `.amap/knowledge/templates/*.md`

Out of scope:

- `docs/`
- `README.md`
- Historical plans and assessments
- Behavior changes to tools, hooks, or CLI code
- OpenSpec skill packages:
  - `.amap/skills/openspec-explore/`
  - `.amap/skills/openspec-propose/`
  - `.amap/skills/openspec-archive-change/`

## Style Rules

Runtime files should prefer concise operational language:

```md
### [CRITICAL] R-X: Rule Name

When:
- ...

Do:
1. ...
2. ...

Abort if:
- ...

Log:
- `[MARKER] ...`
```

Rationale policy:

- Remove retrospective rationale from runtime files.
- Replace incident-specific rationale with stable operating constraints when needed.
- Keep rationale only when it directly changes execution behavior.
- Prefer one sentence over a paragraph.
- Do not include dates, incident IDs, "previously", "observed before", or similar historical framing in shared runtime rules.

Allowed examples:

- "This prevents stale draft knowledge from being used for reasoning."
- "This keeps generated code tied to approved project knowledge."

Disallowed examples:

- "Incident 2026-06-08..."
- "A class of failures was observed..."
- "Previously this section..."
- Long explanations that do not affect what the agent must do.

## Semantic Preservation Rules

The edit pass must not change:

- Rule IDs and severity labels such as `[CRITICAL]` or `[REFERENCE]`.
- Required phase order and workflow gates.
- Required commands and tool paths.
- Abort, warn, confirm, and logging requirements.
- Marker strings written to `AGENT_TRANSPARENCY`.
- File ownership and framework path templates.
- Frontmatter, trigger conditions, and preconditions.

If a sentence contains both behavior and rationale, split it and keep only the behavior.

## Review Method

Use search-driven edits:

1. Find retrospective/rationale-heavy phrases in `.amap/`.
2. Classify each hit as one of:
   - Keep: operational field or user-facing reason placeholder.
   - Rewrite: behavior is valid but wording is too historical.
   - Remove: pure rationale, no runtime behavior.
3. Edit only the relevant sentences or small surrounding paragraphs.
4. Re-scan for banned historical framing.

## Verification

Run:

```bash
rg -n "Incident|incident|trước đây|đã quan sát|sự cố|học được|previous|observed before|learned" .amap
python3 .amap/tools/skill-lint/validate_skills.py
python3 -m pytest cli/tests/test_render.py cli/tests/test_scaffold.py cli/tests/test_snapshots.py
```

Expected result:

- No unintended historical/runtime rationale remains in `.amap/`.
- Skill lint passes.
- Render/scaffold/snapshot tests pass or only fail for intentional snapshot changes caused by wording updates.

## Implementation Boundary

This design authorizes a style-only pass. Any discovered behavior issue, broken rule, or inconsistent workflow requirement should be reported separately unless fixing it is necessary to preserve the existing meaning after a wording edit.
