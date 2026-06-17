# AMAP Installer — Design Spec

> **Date**: 2026-06-17
> **Status**: Approved (design)
> **Base**: `b226424` + uncommitted SP3' CLI migration (`cli/`, `pyproject.toml`)
> **Model**: OpenSpec / Understand-Anything style — a *tool repo* that injects AMAP into a target project.

---

## 1. Goal & Context

This repo (`agent-memory-arch-v3`) is an **installer tool**, not a self-running agent environment. The intended flow:

1. User clones this repo somewhere.
2. User runs `./install.sh /path/to/project`.
3. Installer asks for IDE/platform (Antigravity, Claude Code, Cursor, …), MCP servers, and primary language.
4. It renders the AMAP framework (workflows, skills, rules, procedures) into the target project, with tool names already resolved for the chosen platform.

Running the installer again on a project that already has AMAP **updates** the framework safely without destroying user customizations.

The big architectural direction is **settled**: build-time CLI resolution (not the deleted runtime adapter layer). The runtime adapter approach was mismatched with this distribution model. Templates in source (`{{ tools.X }}`) are accepted as normal template-authoring reality, not a defect.

### Scope of this spec

- `install.sh` thin wrapper over the existing Python CLI.
- New `amap update` (and `update --reconfigure`) command with init/update separation.
- Manifest-driven file ownership (framework vs user).
- Two **safety-critical** fixes: atomic update writes, and no-silent-swallow of template errors.
- Pytest suite covering init/update/render/reconfigure.

### Out of scope (separate spec later)

- Dead code cleanup in `generate_resolved_config`.
- `.gitignore` for `__pycache__` / `*.egg-info`.
- npx/Node distribution variant.
- Improving readability of templatized source files.
- "Add only missing files" into user-owned directories on update.

---

## 2. `install.sh` (thin wrapper, repo root)

```
./install.sh /path/to/project
```

Behavior:

1. Check `python3` (>= 3.8) is available. If missing → clear error message, exit non-zero.
2. Create a `.venv` **inside the AMAP repo** on first run; install `jinja2` + `pyyaml` into it. Does **not** touch the user's system Python (no `--break-system-packages`).
3. Detect target state:
   - If `$TARGET/.agent/resolved-config.yaml` exists → invoke `amap update --target "$TARGET"`.
   - Otherwise → invoke `amap init --target "$TARGET"`.
4. All interactive prompts (platform/MCP/language) happen inside the existing Python CLI.

`install.sh` adds no business logic — it only bootstraps the environment and routes to init vs update.

---

## 3. CLI Command Surface

| Command | Role |
|---|---|
| `amap init --target DIR` | (existing) Fresh interactive scaffold. |
| `amap update --target DIR` | **(new)** Re-render `framework` files from the stored `resolved-config`; preserve `user` files. No re-prompting. |
| `amap update --reconfigure` | **(new)** Re-prompt platform/MCP/language, rewrite `resolved-config`, re-render tool names for the new platform; still preserve `user` files. This is the "switch IDE (Claude → Antigravity)" path. |
| `amap status --target DIR` | (existing) Diagnostics. |

---

## 4. File Ownership Model (manifest-driven — approach ①)

Add an `ownership` field to each plugin in `cli/plugin-manifest.yaml`:

- `ownership: framework` (**default** when omitted) → `update` always re-renders / overwrites.
- `ownership: user` → written only by `init` when absent; `update` **never** touches it.

User-owned plugins:

- `.knowledge-layer/long-term/` — persona.yaml, author DNA.
- `.knowledge-layer/active/` — scanned conventions.

`resolved-config.yaml` is managed directly by the CLI (not a plugin) and is rewritten only on `--reconfigure`.

Default-to-`framework` preserves the current behavior of all existing plugins; only the knowledge-layer user directories are marked `user`.

---

## 5. Safety Fix #1 — Atomic `update` writes

`update` renders into a **temporary staging directory first**, then verifies **zero unresolved `{{ ` markers remain** across the rendered output, and only then syncs (overwrites) framework files into the target.

If any render step fails or the marker check finds leftovers → **abort without touching the target**. This prevents the disaster of overwriting good framework files with broken/half-rendered content.

`init` writes into a fresh/empty target, so per-file fail-loud (Safety Fix #2) is sufficient there; the staging step is specifically required for `update` because it overwrites existing files.

---

## 6. Safety Fix #2 — No silent swallow of template errors

Current code swallows everything: `except (UnicodeDecodeError, Exception)` in [init.py:272](../../../cli/commands/init.py#L272) and [renderer.py:145](../../../cli/renderer.py#L145). A malformed Jinja template silently falls through to a plain copy, shipping unrendered `{{ }}` with no warning.

Fix:

- `UnicodeDecodeError` → fall back to binary copy (intended behavior, keep).
- Jinja `TemplateError` / `TemplateSyntaxError` → **propagate**, print which file failed, exit non-zero. Never silently copy an unrendered template.

---

## 7. Testing (pytest, under `cli/tests/`)

- **render**: `render_string` produces correct tool names per platform (Claude Code `mcp__socraticode__codebase_search`, `Read`, `Bash`; Antigravity `mcp_socraticode_codebase_search`); a malformed template raises rather than swallows.
- **init**: scaffold into a temp dir → expected files exist, zero `{{ ` markers, capability gating skips the correct plugins (no MCP → skips `db-explorer`, `codebase-explorer`, `workflow-index-source`).
- **update**: init → modify one `user` file (persona.yaml) and one `framework` file (a skill) → run `update` → user file is byte-for-byte unchanged, framework file is re-rendered (overwritten), zero `{{ ` markers.
- **reconfigure**: init for Claude Code → `update --reconfigure` to Antigravity → tool names change in framework files, user files preserved, `resolved-config` updated.

---

## 8. Known Limitation (accepted)

For an `ownership: user` directory, if a future framework version adds a *new template file* to it, `update` will not bring it across (the whole directory is skipped). "Add only missing files" is deferred to a future enhancement to keep update logic simple and safe.
