# Batch 1 Scaffold Hardening — Design Spec

> Ngay: 2026-06-18
> Loai: implementation-ready design for the first roadmap batch
> Scope: TODO audit, P1.2 silent tool-resolution guard, UP3 golden snapshots,
> and P1.3/P2.2 init automation/default cleanup.

## 1. Problem

`TODOS.md` points AMAP in the right direction: validate value, fail early, and
reduce adoption tax before larger portability refactors. The first implementation
batch should protect the scaffold surface before changing it heavily.

The risky surfaces are:

- Tool mapping can fail silently. `BasePlatform.get_tool()` currently returns
  the abstract operation name when a platform does not map it. That can render a
  non-existent tool name into agent instructions while `amap init` still exits
  successfully.
- Platform output is fragile. Recent work changed `.amap`, `.agents`,
  `.claude`, `resolved-config.yaml`, and entry-point rendering repeatedly. A
  small platform regression may only show up after a user installs AMAP.
- `amap init` is not automation-friendly. It prompts interactively and defaults
  to the first platform/language choices, which currently means enter-through
  can install Antigravity + Java by accident.
- `TODOS.md` contains at least one stale item: the init next-steps footer already
  exists and has test coverage.

This batch is deliberately not the full portability registry (`P2.1`/`UP2`) and
not the outcome eval harness (`P1.1`/`UP1`). It creates the guardrails those
larger changes need.

## 2. Goals

1. Update `TODOS.md` so the immediate backlog reflects the current code.
2. Make missing tool mappings impossible to miss during tests or scaffold.
3. Add golden snapshot coverage for platform scaffold outputs.
4. Add non-interactive `amap init` flags and remove unsafe enter-through
   defaults.
5. Keep behavior backwards-compatible for existing interactive users unless a
   choice is genuinely unsafe.

## 3. Non-Goals

- Do not migrate platform definitions to YAML/data registry yet.
- Do not remove legacy `resolved-config.yaml` lookup paths.
- Do not implement `amap migrate`, `--dry-run`, drift detection, or eval
  harnesses in this batch.
- Do not change generated framework prose except where tests reveal an existing
  scaffold correctness issue.

## 4. Approach Options

### Option A — Minimal P1.2 Only

Fix `get_tool()` fallback and add a keyset test. This is small and safe, but it
does not protect the platform output surface or unblock scripted init.

### Option B — Recommended Batch 1

Bundle TODO audit, tool-resolution guards, platform golden snapshots, and init
automation/default cleanup. These touch adjacent scaffold surfaces and reinforce
each other: non-interactive init makes snapshots easier to generate; snapshots
protect the later init and platform refactors; keyset tests prevent silent
adapter drift.

### Option C — Full Portability Refactor Now

Jump directly to capability-based MCP resolution and YAML platform registry.
This addresses the strategic architecture, but it is too much blast radius
before the scaffold surface has snapshot protection.

Recommendation: Option B.

## 5. Design

### 5.1 TODO Audit

`TODOS.md` becomes an active roadmap, not a stale finding dump.

Changes:

- Mark `P3.2 — Next-steps footer sau amap init` as done or move it to a
  completed/stale section, because [cli/commands/init.py](../../../cli/commands/init.py)
  already prints platform-root-aware next steps and [cli/tests/test_init.py](../../../cli/tests/test_init.py)
  asserts them.
- Merge `P1.3 — Init non-interactive` and `P2.2 — default footgun` into one
  Batch 1 work item: "Init automation and safe defaults".
- Promote `UP3 — Golden-snapshot test mỗi platform` into the immediate hardening
  sequence, before major portability refactors.
- Leave `P2.3` framed as canonical write + legacy read/migration warning, not
  immediate deletion of legacy lookup paths.

### 5.2 Tool Mapping Guard

Introduce a single source of truth for abstract tool-operation keys. The source
can live near platform adapters, for example `cli/platforms/base.py`, as
`REQUIRED_TOOL_KEYS`.

Rules:

- Every concrete platform must define exactly the required keyset unless the
  key is explicitly documented as unsupported in a structured `unsupported_tools`
  set.
- `BasePlatform.get_tool()` should raise a clear error for an unmapped required
  operation instead of returning the abstract name silently.
- `build_render_context()` should validate the platform mapping and fail before
  rendering templates if required keys are missing.
- Generic and Codex may map abstract names to themselves intentionally, but that
  is not treated as missing because the mapping is explicit.

Test coverage:

- Unit test: all `PLATFORMS` share the required keyset.
- Unit test: a fake platform missing a key raises a clear exception.
- Regression test: scaffold/render cannot complete when a template requests an
  unknown tool mapping.

### 5.3 Golden Snapshot Tests

Add snapshot tests for scaffold output shape, focused on stable structure rather
than every byte of every rendered file.

The snapshot should include:

- Relative file tree for each platform: `antigravity`, `codex`, `claude-code`,
  and `generic`.
- Key rendered files exist under the expected framework root.
- Entry-point file is correct: `AGENTS.md` for Antigravity/Codex/Generic,
  `CLAUDE.md` for Claude Code.
- `resolved-config.yaml` lives under the platform framework root.
- No unresolved Jinja markers remain in rendered text files.
- No active `.amap/` references leak into `.agents`/`.claude` platform outputs
  except explicitly documented legacy/source-repo references.

Implementation shape:

- Add a helper in tests that runs `run_init()` non-interactively into a temp
  project and returns a sorted relative tree.
- Store expected snapshots as text fixtures under `cli/tests/snapshots/`, one
  file per platform.
- Keep snapshots structural. Avoid including generated temp paths, timestamps,
  or entire file contents.

Snapshot update policy:

- Snapshot changes are allowed only when platform output intentionally changes.
- The diff should be reviewed like API surface change, because this is the user
  install layout.

### 5.4 Init Automation and Safe Defaults

Extend the CLI parser and `run_init()` path to accept explicit choices:

- `--platform <key>`
- `--mcp <key>` repeatable or comma-separated
- `--language <language>`
- `--yes`

Behavior:

- If all required choices are provided and `--yes` is set, `amap init` runs with
  no prompts.
- If some choices are missing, interactive prompts ask only for missing values.
- Invalid platform, MCP, or language values fail with a clear message before
  staging files.
- `--yes` without enough choices should fail instead of silently choosing
  defaults.
- Interactive mode should no longer default to Antigravity + Java by accident.
  Platform selection has no default: pressing Enter without a platform keeps
  prompting. Language defaults to `other`, because it is safer than silently
  assuming Java. MCP selection remains optional and defaults to none.

Testing:

- Direct `run_init()` tests pass explicit options to avoid monkeypatching
  input.
- CLI parser tests cover `--platform`, `--mcp`, `--language`, and `--yes`.
- Existing interactive tests remain valid, adjusted only for the changed safe
  defaults/order.

### 5.5 Error Handling

All new failure modes should fail before modifying the target project.

- Invalid init options: print/raise a clear validation error and do not create
  target files.
- Missing tool mapping: raise a clear platform validation error naming platform
  and missing abstract keys.
- Snapshot mismatch: normal pytest assertion failure with a tree diff.
- Stale TODO item: docs-only update; no runtime behavior.

### 5.6 Data Flow

Init flow after this batch:

1. CLI parses target/source plus optional platform/MCP/language/yes flags.
2. `run_init()` loads manifest.
3. Choice resolution validates explicit values and prompts only when needed.
4. Platform builds render context; platform mapping validation runs here.
5. Scaffold renders into staging.
6. Existing unresolved-marker verification runs.
7. Staging syncs into target only after validation passes.
8. Tests compare the resulting structural tree against snapshots.

## 6. Implementation Boundaries

Likely touched files:

- `TODOS.md`
- `cli/amap.py`
- `cli/commands/init.py`
- `cli/platforms/base.py`
- `cli/platforms/*.py`
- `cli/scaffold.py` only if render-context validation needs a scaffold hook
- `cli/tests/test_platforms.py`
- `cli/tests/test_init.py`
- `cli/tests/test_scaffold.py`
- `cli/tests/snapshots/*.txt`

Avoid touching framework rule/skill/workflow prose unless a test exposes a
real unresolved marker or wrong path.

## 7. Verification

Minimum commands:

```bash
python -m pytest cli/tests/test_platforms.py cli/tests/test_init.py cli/tests/test_scaffold.py -q
python -m pytest cli/tests -q
```

Manual smoke checks:

```bash
python -m cli.amap init --target /tmp/amap-smoke --platform generic --language other --yes
python -m cli.amap init --target /tmp/amap-smoke-codex --platform codex --mcp socraticode --language python --yes
```

Expected:

- Both commands finish without interactive input.
- Generated trees match platform roots.
- No unresolved template markers remain.

## 8. Decisions

1. Interactive platform selection has no default. Empty input is invalid until
   the user chooses a platform number.
2. Interactive language selection defaults to `other`.
3. Golden snapshots store the full normalized relative file tree for each
   platform. They do not store file contents, absolute paths, temp paths, or
   timestamps.

## 9. Success Criteria

- `TODOS.md` no longer treats implemented next-step footer work as pending.
- Missing platform tool mappings fail in tests and before scaffold writes to the
  target.
- Each platform has structural snapshot coverage.
- `amap init` can run non-interactively with explicit flags.
- Existing interactive init remains usable.
- The full CLI test suite passes.
