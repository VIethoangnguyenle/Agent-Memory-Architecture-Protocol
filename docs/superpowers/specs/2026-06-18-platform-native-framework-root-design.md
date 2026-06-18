# Platform-Native Framework Root Design

> Date: 2026-06-18
> Status: Approved for planning
> Source: `report-dual-directory-issue.md`

## 1. Problem

`amap init` currently writes AMAP's canonical runtime tree into `.amap/`, then mirrors skills and workflows into a platform-native discovery folder such as `.agents/skills/` or `.claude/skills/`.

For Antigravity and Codex this creates two project dot-directories:

```txt
project/
├── .amap/      # canonical AMAP runtime
└── .agents/    # native skill mirror
```

This is confusing and violates the desired platform behavior. The selected platform should receive AMAP directly in the directory it natively understands. The issue is not limited to `skills/`; the full AMAP runtime must move together:

```txt
knowledge/
rules/
skills/
workflows/
procedures/
tools/
profiles/
resolved-config.yaml
```

## 2. Goals

1. Make each supported platform use exactly one canonical AMAP framework root.
2. Ensure Antigravity and Codex installs do not create `.amap/`.
3. Ensure Claude Code installs do not create `.amap/`.
4. Keep Generic installs on `.amap/`.
5. Remove the need for native skill mirroring on platforms whose canonical root is already native.
6. Improve `amap init` selection UX with checkbox-style prompts:
   - platform/IDE: single-select
   - language: single-select
   - MCP servers: multi-select

## 3. Non-Goals

- No application-code changes in target projects.
- No migration of existing user-authored knowledge files without an explicit update or migration command.
- No Cursor redesign in this change. Cursor is out of scope until its preferred native directory model is re-evaluated.
- No change to AMAP's source repository layout. The source repo may continue storing template content under `.amap/`.

## 4. Platform Matrix

| Platform | Canonical framework root | Entry point | Native loading behavior |
|----------|---------------------------|-------------|--------------------------|
| Antigravity | `.agents/` | `AGENTS.md` | Skills live directly in `.agents/skills/` |
| Codex | `.agents/` | `AGENTS.md` | Skills live directly in `.agents/skills/` |
| Claude Code | `.claude/` | `CLAUDE.md` | Skills live directly in `.claude/skills/` |
| Generic | `.amap/` | `AGENTS.md` | No native loading; AMAP fallback root |

Cursor is intentionally excluded from this matrix for this change.

## 5. Architecture

### 5.1 Platform Model

Add `framework_root` to `BasePlatform`.

```python
class BasePlatform:
    @property
    def framework_root(self) -> str:
        return ".amap"
```

Overrides:

```txt
AntigravityPlatform.framework_root = ".agents"
CodexPlatform.framework_root = ".agents"
ClaudeCodePlatform.framework_root = ".claude"
GenericPlatform.framework_root = ".amap"
```

`BasePlatform.build_render_context()` must expose:

```yaml
platform:
  framework_root: <value>
```

### 5.2 Manifest Output Paths

`cli/plugin-manifest.yaml` becomes platform-root aware.

Before:

```yaml
output: .amap/rules/RULES.md
```

After:

```yaml
output: "{{ platform.framework_root }}/rules/RULES.md"
```

This applies to every AMAP runtime subtree:

```txt
rules/
skills/
workflows/
procedures/
tools/
knowledge/templates/
knowledge/active/
knowledge/long-term/
profiles/
resolved-config.yaml
```

The source side remains unchanged. `SOURCE_MAP` can continue resolving source content from the AMAP repo's `.amap/...` directories.

### 5.3 Resolved Config

`generate_resolved_config()` must write to:

```txt
target / platform.framework_root / "resolved-config.yaml"
```

The resolved config should include the framework root:

```yaml
resolved:
  platform: antigravity
  framework_root: .agents
  mcps: [...]
  language: python
  framework_version: "3.0"
```

`load_resolved_config()` must support current and legacy locations:

1. `.agents/resolved-config.yaml`
2. `.claude/resolved-config.yaml`
3. `.amap/resolved-config.yaml`

If more than one exists, prefer the config whose `resolved.platform` maps to its expected `framework_root`. If ambiguity remains, prefer the newest platform-native config and report a warning in status/update output.

### 5.4 Native Skill Export

For Antigravity, Codex, and Claude Code, `native_skill_export` should be `None` because skills are no longer mirrored. They are scaffolded directly into the platform root:

```txt
.agents/skills/<skill>/SKILL.md
.claude/skills/<skill>/SKILL.md
```

`scaffold_native_skill_exports()` can remain for future platforms that need a true secondary export path, but it should not run for the three platform-native roots in this design.

### 5.5 Rendered Framework Content

All framework prose and executable instructions must use `{{ platform.framework_root }}` instead of hardcoded `.amap` paths.

Examples:

```diff
- READ: .amap/rules/RULES.md
+ READ: {{ platform.framework_root }}/rules/RULES.md

- python3 .amap/tools/skill-lint/validate_skills.py
+ python3 {{ platform.framework_root }}/tools/skill-lint/validate_skills.py
```

This includes:

- `AGENTS.md`
- `.amap/rules/*.md`
- `.amap/skills/**/*.md`
- `.amap/workflows/*.md`
- `.amap/procedures/*.md`
- `.amap/knowledge/templates/*.md`
- `.amap/tools/**/*.md`
- `.amap/profiles/*.yaml`
- `README.md`
- ownership and install docs

Legacy `.amap` may appear only in migration documentation or source-repo explanations, not as the active runtime path for Antigravity, Codex, or Claude Code.

### 5.6 Install, Update, and Status

`install.sh` must detect existing installs in both legacy and platform-native roots:

```txt
.agents/resolved-config.yaml
.claude/resolved-config.yaml
.amap/resolved-config.yaml
```

`amap update` must read the existing resolved config, derive the expected `framework_root`, and render into that root. Reconfigure must move to the newly selected platform root.

`amap status` must derive all paths from the resolved platform root:

```txt
{framework_root}/skills
{framework_root}/workflows
{framework_root}/knowledge
{framework_root}/resolved-config.yaml
```

Status output should warn when a legacy `.amap/` remains beside a platform-native root.

## 6. Init Selection UX

Replace number-entry prompts with checkbox-style selection helpers.

### 6.1 Single-Select Checkbox

Used for platform/IDE and language.

Behavior:

- exactly one option is selected
- arrow keys or numeric fallback can move selection
- Enter confirms
- terminal fallback may accept a number, but the displayed UI should still communicate single selection

Example:

```txt
Choose agent platform:
[x] Antigravity
[ ] Claude Code
[ ] Codex
[ ] Generic
```

### 6.2 Multi-Select Checkbox

Used for MCP servers.

Behavior:

- zero or more options may be selected
- Space toggles an option
- Enter confirms
- terminal fallback may accept comma-separated numbers

Example:

```txt
MCP servers:
[x] Socraticode
[ ] Confluence
[x] DB Remote
[ ] Understand Anything
```

Language remains single-select because each target project has one primary language.

## 7. Validation

### 7.1 Init Invariants

Antigravity:

```bash
test ! -e "$TARGET/.amap"
test -e "$TARGET/.agents/resolved-config.yaml"
test -e "$TARGET/.agents/skills/requirement-analyst/SKILL.md"
test -e "$TARGET/.agents/knowledge/long-term/author-dna.yaml"
```

Codex:

```bash
test ! -e "$TARGET/.amap"
test -e "$TARGET/.agents/resolved-config.yaml"
test -e "$TARGET/.agents/skills/requirement-analyst/SKILL.md"
```

Claude Code:

```bash
test ! -e "$TARGET/.amap"
test -e "$TARGET/.claude/resolved-config.yaml"
test -e "$TARGET/.claude/skills/requirement-analyst/SKILL.md"
test -e "$TARGET/CLAUDE.md"
```

Generic:

```bash
test -e "$TARGET/.amap/resolved-config.yaml"
test -e "$TARGET/.amap/skills/requirement-analyst/SKILL.md"
test -e "$TARGET/AGENTS.md"
```

### 7.2 Rendered Path Gate

For Antigravity, Codex, and Claude Code staging output:

```bash
grep -R "\.amap/" "$STAGING"
```

Allowed matches must be limited to migration or legacy documentation. Any active bootstrap path, command, precondition, or workflow instruction containing `.amap/` is a failure.

### 7.3 Tests

Update or add tests for:

- platform `framework_root` values
- render context includes `platform.framework_root`
- manifest renders output under the selected root
- Antigravity init creates `.agents` and not `.amap`
- Codex init creates `.agents` and not `.amap`
- Claude init creates `.claude` and not `.amap`
- Generic init still creates `.amap`
- `load_resolved_config()` finds `.agents`, `.claude`, and legacy `.amap`
- `status` reports skills, workflows, context, archive, and author DNA from the selected root
- `update --reconfigure` writes the newly selected platform root and warns when a stale legacy `.amap` remains
- checkbox prompt helpers support single-select and multi-select behavior, with deterministic fallback tests

## 8. Migration Behavior

Fresh installs must never create `.amap` for Antigravity, Codex, or Claude Code.

Existing installs may already contain `.amap`. This design chooses a conservative migration policy:

1. `load_resolved_config()` can read legacy `.amap/resolved-config.yaml`.
2. `amap update` and `amap update --reconfigure` render the selected platform's canonical root.
3. If legacy `.amap/` still exists beside `.agents/` or `.claude/`, commands print a warning with the exact path and explain that it is legacy.
4. Commands do not delete `.amap/` automatically, because it may contain user-authored knowledge or local edits.
5. A destructive cleanup command or `--migrate-root` flag can be designed later as a separate change.

## 9. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Missed hardcoded `.amap` path in rendered files | High | rendered path gate plus targeted tests |
| Accidental deletion of user knowledge during migration | High | warning-only legacy policy; never delete ambiguous `.amap` silently |
| Source repo layout confused with target layout | Medium | document that `SOURCE_MAP` remains source-only |
| Claude root assumptions are wrong | Medium | validate against Claude Code skill loading behavior before implementation |
| Checkbox prompt breaks non-interactive tests | Medium | keep deterministic fallback and test prompt helpers directly |

## 10. Acceptance Criteria

1. Antigravity init creates `.agents/` with all AMAP runtime folders and does not create `.amap/`.
2. Codex init creates `.agents/` with all AMAP runtime folders and does not create `.amap/`.
3. Claude Code init creates `.claude/` with all AMAP runtime folders and does not create `.amap/`.
4. Generic init keeps `.amap/` behavior.
5. No platform-native root relies on a mirrored `native_skill_export` for core AMAP skills.
6. `AGENTS.md` and `CLAUDE.md` rendered instructions point to the selected `platform.framework_root`.
7. `install.sh`, `amap update`, and `amap status` work with platform-native resolved-config locations.
8. Platform and language selection use single-select checkbox-style UX.
9. MCP selection uses multi-select checkbox-style UX.
10. Tests cover the platform matrix and no-`.amap` invariant for Antigravity, Codex, and Claude Code.
