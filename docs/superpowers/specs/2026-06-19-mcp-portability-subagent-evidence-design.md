# MCP Portability + Subagent Evidence Layer

**Date:** 2026-06-19
**Status:** Design approved for written spec

## Problem

AMAP currently records selected MCP servers in `resolved-config.yaml` and renders
platform-specific tool names, but that does not prove the runtime has actually injected
those MCP tools into the agent session.

The concrete failure came from an Antigravity CLI dogfood run:

- Antigravity IDE had MCP tools because it could read its MCP config.
- Antigravity CLI did not expose any MCP tools because its app-data config path was
  missing or empty.
- Subagents also had no usable MCP access, so code exploration fell back to repeated
  grep despite MCP servers being alive.
- The write gate rejected Antigravity CLI write payloads because its target path parser
  did not recognize `TargetFile`.

This is not only an Antigravity problem. Codex, Claude Code, and Antigravity each have
different MCP config locations, tool-surface behavior, and subagent inheritance semantics.
AMAP needs a portable capability contract: configured MCPs must be probed, failures must
degrade explicitly, and subagents must receive evidence from the orchestrator instead of
assuming they can independently call MCP.

## Goals

1. Support the three primary AMAP runtimes: Codex, Claude Code, and Antigravity.
2. Add `amap doctor mcp` to validate platform MCP config, native MCP injection, and a
   bridge fallback path.
3. Ship a controlled MCP bridge derived from `mcp_universal_client.py`, scoped as a
   diagnostic and fallback adapter, not as a replacement runtime.
4. Make setup safe: `amap init/update` may render bridge tooling, but config edits happen
   only under `amap doctor mcp --fix` or explicit interactive confirmation.
5. Make subagent execution evidence-driven: subagents can request more context, and the
   orchestrator must review their output before accepting code.
6. Fix the Antigravity write-gate target extraction gap for `TargetFile`.

## Non-Goals

- Do not implement or host any new MCP server.
- Do not replace native MCP support in Codex, Claude Code, or Antigravity.
- Do not silently rewrite user config files or create symlinks during `amap init`.
- Do not assume subagents always inherit MCP tools, even when platform docs say they can.
- Do not refactor unrelated AMAP workflows beyond the MCP, subagent, and write-gate touch
  points required by this design.

## Sources And Prior Art

This design follows existing multi-agent patterns, but turns them into auditable AMAP
artifacts:

- Claude Code subagents use separate context and configurable tool access:
  <https://code.claude.com/docs/en/sub-agents>
- Codex subagents use parent/orchestrator dispatch and result collection:
  <https://developers.openai.com/codex/subagents>
- LangChain multi-agent docs frame subagents as tools and emphasize context engineering:
  <https://docs.langchain.com/oss/python/langchain/multi-agent>
- Microsoft Agent Framework documents supervisor, handoff, and agent-as-tool orchestration:
  <https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/>

AMAP's contribution is to make the handoff, context request, evidence checkpoint, and
orchestrator review concrete file contracts that work across runtimes.

## Chosen Approach

Use a platform-neutral MCP evidence contract with per-platform adapters.

```
resolved-config.yaml
  -> platform MCP adapter
  -> native MCP config discovery
  -> native MCP probe
  -> bridge fallback probe
  -> mcp-doctor-report.md
  -> bootstrap MCP-status evidence or degrade
```

Native MCP remains the preferred path. The bridge is used only when native MCP is absent,
not injected, or probe-failing, and only with an evidence line that records why the bridge
path was used.

## Alternatives Considered

### A. MCP Doctor + Bridge Fallback (chosen)

`amap doctor mcp` validates config and probes native MCP first. It probes the bridge only
as fallback. This is slightly more work than a symlink fix, but it gives deterministic
evidence and works across Codex, Claude Code, and Antigravity.

### B. Bridge As First-Class MCP Runtime

AMAP could instruct agents to call every MCP server through `run_command` and the bridge.
This would make Antigravity CLI work even when native injection fails, but it increases
permission risk, leaks more detail into shell commands, and bypasses platform-native tool
approval semantics. It is too broad for a framework default.

### C. Config Copy/Symlink Only

AMAP could copy or symlink the IDE MCP config into the CLI config path. This is fast for
one Antigravity failure mode, but it does not prove tool injection, does not help Codex or
Claude Code systematically, and does not solve subagent evidence gaps.

## Platform Contract

Each platform adapter has the same responsibilities:

1. Report the framework root and native config candidates.
2. Load and validate platform config files without exposing secrets in logs.
3. Compare configured MCP server keys against `resolved-config.yaml`.
4. Probe native MCP availability where the runtime exposes tools.
5. Probe bridge fallback against the resolved server definitions.
6. Return a normalized status object for reporting and gates.

| Platform | Framework root | Native config candidates | Bridge role |
|----------|----------------|--------------------------|-------------|
| Antigravity | `.agents/` | `.agents/mcp_config.json`, `~/.gemini/antigravity-cli/mcp_config.json`, `~/.gemini/antigravity/mcp_config.json`, `~/.gemini/config/mcp_config.json` | Important CLI fallback and diagnostic path |
| Claude Code | `.claude/` | project `.mcp.json`, user Claude config locations supported by the CLI | Diagnostic and fallback path; native MCP preferred |
| Codex | `.agents/` plus `.codex/` hooks | project/user Codex config containing `mcp_servers` | Diagnostic and fallback path; native MCP preferred |

The exact user-level Codex and Claude config paths should live in adapter constants and be
covered by tests. If a path changes in a future runtime, only the adapter changes.

## Setup Flow

`amap init` and `amap update` remain scaffold/render operations:

1. Render the selected platform runtime.
2. Render `resolved-config.yaml`.
3. Render `tools/mcp-bridge/mcp_client.py` for platforms that support shell execution.
4. Render platform hook/config files already managed by AMAP.
5. Print a next-step hint when MCPs are selected: run `amap doctor mcp`.

`amap doctor mcp` performs diagnostics:

1. Detect the platform from `resolved-config.yaml`.
2. Discover native MCP config candidates through the adapter.
3. Validate JSON/TOML shape and selected server keys.
4. Probe native MCP availability when possible.
5. Probe bridge fallback using `initialize`, `tools/list`, and one lightweight tool probe
   per selected server when a safe probe is known.
6. Write `{framework_root}/knowledge/active/mcp-doctor-report.md`.
7. Print a concise summary and recommended fix.

`amap doctor mcp --fix` may edit config after confirmation or non-interactive opt-in:

- create missing parent directories,
- copy or symlink a known-good config into the platform CLI config path,
- create a workspace config file when the platform supports it,
- never overwrite a non-empty config without backup and confirmation.

## MCP Bridge

The bridge is a small Python client, not a new AMAP runtime.

Recommended path after scaffold:

```
{framework_root}/tools/mcp-bridge/mcp_client.py
```

Responsibilities:

- Accept an explicit config path or server definition from `amap doctor mcp`.
- Support stdio MCP servers.
- Support HTTP/SSE MCP servers.
- Call `initialize`.
- Call `tools/list`.
- Call `tools/call`.
- Return normalized JSON with status, server, tool, result, and error fields.

Constraints:

- Do not scan arbitrary home-directory paths inside the bridge. Discovery belongs to the
  platform adapter.
- Do not print secrets, headers, tokens, or raw environment values.
- Do not execute write-capable MCP tools by default.
- Do not become the default route when native MCP is healthy.
- Every runtime rule that allows bridge use must require a transparency entry explaining
  why native MCP was unavailable.

## MCP Evidence And Degrade

Bootstrap and exploration rules should treat MCP status as evidence, not as a declaration.

Valid MCP status lines must contain one of:

- native probe evidence, such as project name plus node/edge counts for code graph MCPs,
- bridge probe evidence, clearly marked as fallback,
- a degrade line, such as `KG unavailable - grep fallback, MEDIUM`,
- an agent-memory degrade line, such as `agent-memory unavailable - skip recall/save`.

Invalid examples:

- `MCP: Runtime Ready`
- `MCP configured`
- `MCP selected in resolved-config.yaml`

`resolved-config.yaml` says what AMAP intended to use. The probe report says what the
runtime can actually use.

## Subagent Evidence Loop

Subagents are treated as bounded workers. The orchestrator owns context enrichment, MCP
probing, review, and final acceptance.

### Dispatch

Before dispatching a subagent, the orchestrator creates:

```
{framework_root}/knowledge/active/TASK_HANDOFF.<node-id>.md
```

The handoff contains:

- task objective and scope,
- files or modules in scope,
- applicable DNA/conventions/snapshot slices,
- MCP/KG/DB/doc evidence already gathered,
- constraints and non-goals,
- expected output format,
- required tests or verification.

### Context Request

If the subagent lacks evidence, it stops and writes:

```
{framework_root}/knowledge/active/CONTEXT_REQUEST.<node-id>.md
```

The request contains:

- missing evidence,
- why it blocks safe work,
- requested probe or file read,
- expected shape of the answer.

The subagent should not guess and should not be the first actor to probe MCP. The
orchestrator reads the request, enriches context, updates the handoff, and re-dispatches or
resumes the task.

### Worker Output

When the subagent completes, it returns a proposal plus:

```
{framework_root}/knowledge/active/NODE_CHECKPOINT.<node-id>.md
```

The checkpoint contains:

- files changed or proposed,
- requirement satisfied,
- rule IDs and conventions applied,
- evidence used,
- tests run or reason tests were not run,
- known risks.

### Orchestrator Review Gate

The orchestrator must review subagent output before accepting it:

1. Verify `NODE_CHECKPOINT.<node-id>.md` exists and is not skeletal.
2. Verify it references evidence from the handoff or later orchestrator enrichment.
3. Review the diff or patch proposal for correctness, scope, and missing tests.
4. Run applicable tests or record why they cannot run.
5. Accept, request revision, or reject.

Subagent output is not final merely because the subagent completed.

## Write-Gate Fix

The write-gate target parser must support Antigravity CLI payloads that use `TargetFile`.

`extract_target_paths()` should recognize `TargetFile` in both:

- `toolCall.args.TargetFile`
- `tool_input.TargetFile`

Regression tests should cover Antigravity `write_to_file` or `replace_file_content`
payloads using `TargetFile`.

## Data Model

### MCP Doctor Status

The doctor can use an internal normalized object shaped like:

```yaml
platform: antigravity
framework_root: .agents
selected_mcps:
  - socraticode
native_config:
  path: ~/.gemini/antigravity-cli/mcp_config.json
  exists: true
  valid: true
  matched_servers:
    - socraticode
native_probe:
  status: unavailable
  reason: "runtime did not expose selected MCP tools"
bridge_probe:
  status: healthy
  server: socraticode
  tools_listed: true
  evidence: "codebase_status returned indexed project"
recommendation: "native unavailable; bridge fallback allowed with transparency"
```

The report file may be Markdown, but the diagnostic core should return structured data so
tests do not depend on fragile prose.

### Subagent Artifacts

Artifact names are keyed by node/task ID:

- `TASK_HANDOFF.<node-id>.md`
- `CONTEXT_REQUEST.<node-id>.md`
- `NODE_CHECKPOINT.<node-id>.md`

The ID can come from the microloop orchestrator node ID, a generated slug, or the current
task ID. The implementation plan should pick one source and keep it stable.

## Error Handling

- Missing native config: report missing path and suggest platform-specific fix.
- Empty config: report as invalid and do not treat it as configured.
- Malformed config: show parse error without dumping secrets.
- Selected MCP not present in config: report mismatch and mark selected MCP unavailable.
- Native tool not injected: mark native unavailable and try bridge.
- Bridge init failure: mark bridge unavailable and write degrade line.
- Bridge `tools/list` succeeds but safe probe is unknown: report `tools/list` evidence only
  and avoid unsafe tool calls.
- Subagent missing evidence: require `CONTEXT_REQUEST` rather than allowing speculative
  implementation.
- Subagent output missing checkpoint: reject at orchestrator review.

## Security And Permissions

- Bridge calls must redact headers, tokens, and environment values in logs.
- Config writes require `--fix` or explicit confirmation.
- Existing non-empty config files must be backed up before replacement.
- DB or write-capable MCP tools should default to read-only probes only.
- Shell bridge commands must avoid embedding secrets in command text where possible.
- Reports should include server keys and statuses, not secret material.

## Testing Strategy

### Unit Tests

- Adapter config discovery for Antigravity, Claude Code, and Codex.
- Config parsing for JSON and TOML shapes used by supported runtimes.
- Selected MCP mismatch detection.
- Bridge client request building for stdio and HTTP/SSE without real servers.
- Bridge response parsing for JSON-RPC and SSE data lines.
- Write-gate extraction for `TargetFile`.
- Subagent artifact validators for handoff, context request, and checkpoint.

### Integration-Style Tests

- `amap init --platform antigravity --mcp socraticode` renders bridge tooling and does not
  edit user home config.
- `amap doctor mcp` against fixture configs writes `mcp-doctor-report.md`.
- `amap doctor mcp --fix` creates a config only in a temp home/workspace fixture.
- Native probe unavailable plus bridge healthy produces a bridge fallback evidence status.
- Native and bridge unavailable produces a degrade status.

### Snapshot Tests

Update scaffold snapshots only for expected new files:

- `{framework_root}/tools/mcp-bridge/mcp_client.py`
- any doctor report template if one is scaffolded
- platform rule text that references bridge fallback or subagent evidence artifacts

## Success Criteria

- `amap init/update` renders MCP bridge tooling without mutating user MCP config.
- `amap doctor mcp` reports native, bridge, and degrade states for Codex, Claude Code, and
  Antigravity fixtures.
- `amap doctor mcp --fix` only writes config with explicit opt-in and preserves backups.
- Bootstrap no longer treats selected MCPs as proof of availability.
- Subagents have a formal path to request missing context.
- Orchestrator review is required before accepting subagent output.
- Antigravity `TargetFile` write payloads are parsed by the write gate.
- Tests cover the adapter, bridge, doctor, write-gate, and subagent artifact contracts.

## Implementation Boundaries

The implementation plan should split this design into small commits:

1. Add platform MCP adapter contracts and fixtures.
2. Add bridge client tool and tests.
3. Add `amap doctor mcp` report-only mode.
4. Add safe `--fix` behavior.
5. Wire scaffold output for bridge tooling.
6. Add runtime rule/procedure text for evidence and degrade.
7. Add subagent artifact contracts and validators.
8. Patch write-gate `TargetFile` extraction.
9. Update snapshots and README/docs.

No implementation should start until this spec is reviewed and accepted.
