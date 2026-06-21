# Agent Memory — MCP-only setup (provider boundary)

> Framework-internal guidance. AMAP does **not** bundle, vendor, auto-install, or
> auto-run `agentmemory`. This recipe is for the **end project** that opts into
> the `memory` capability at `amap init`. Source of truth: design spec
> `docs/superpowers/specs/2026-06-21-memory-tool-capability-templating-design.md` §4.

## Why MCP-only (hooks OFF)

`agentmemory connect <agent>` installs **12 auto-capture hooks** that record memory
on every tool use with no gating. That directly conflicts with AMAP's memory
governance (R-Tool-6, M7: one save per task, 3 quality filters, no-PII, top-K
recall, source-of-truth priority). AMAP must own memory governance, so the end
project wires **only the MCP tool surface** and leaves auto-capture off.

## Setup (verify against upstream before use — example)

> Confirm the package name and command at the upstream repo:
> https://github.com/rohitg00/agentmemory

1. Run the standalone MCP shim (no hooks):

   ```
   npx -y @agentmemory/mcp
   ```

2. Or register the MCP server manually in your platform config (example shape):

   ```json
   {
     "mcpServers": {
       "agent-memory": { "command": "npx", "args": ["-y", "@agentmemory/mcp"] }
     }
   }
   ```

## Do NOT

- Do **not** run `agentmemory connect --with-hooks` (installs the 12 auto-capture hooks).
- Do **not** install agentmemory's bundled skills (they overlap `knowledge-curator` / bootstrap).
- Do **not** commit `~/.agentmemory/` state into the repo (it is user-machine-scoped).

## Result

AMAP's `dynamic_memory_*` abstract ops resolve to this server's tools
(`mcp__agent-memory__memory_*` on Claude Code). When `agent-memory` is not selected
at init, all recall/save are skipped per R-Tool-6 degrade and M7 Tầng 0 — AMAP
still works on repo-based knowledge alone.
