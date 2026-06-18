"""Claude Code Platform — Anthropic Claude Code agent."""

from .base import BasePlatform


class ClaudeCodePlatform(BasePlatform):

    name = "claude-code"
    display_name = "Anthropic Claude Code"
    config_entry_point = "CLAUDE.md"
    framework_root = ".claude"
    native_skill_export = None

    tool_mapping = {
        # ── File Operations ──
        "read_file":         "Read",
        "write_file":        "Write",
        "edit_file":         "Edit",
        "multi_edit_file":   "MultiEdit",
        "search_text":       "Grep",
        "list_directory":    "LS",

        # ── Terminal ──
        "run_command":       "Bash",
        "command_status":    "Bash",
        "send_input":        "Bash",

        # ── Code Exploration (Socraticode — if available) ──
        "search_code":       "mcp__socraticode__codebase_search",
        "index_code":        "mcp__socraticode__codebase_index",
        "code_status":       "mcp__socraticode__codebase_status",
        "get_dependencies":  "mcp__socraticode__codebase_graph_query",
        "trace_flow":        "mcp__socraticode__codebase_flow",
        "find_blast_radius": "mcp__socraticode__codebase_impact",
        "get_symbol":        "mcp__socraticode__codebase_symbol",
        "list_symbols":      "mcp__socraticode__codebase_symbols",
        "graph_stats":       "mcp__socraticode__codebase_graph_stats",
        "graph_build":       "mcp__socraticode__codebase_graph_build",

        # ── Document Search (Confluence — if available) ──
        "search_docs":       "mcp__confluence__search",
        "get_page":          "mcp__confluence__get_page",
        "list_spaces":       "mcp__confluence__list_spaces",
        "get_space_pages":   "mcp__confluence__get_space_pages",

        # ── Web ──
        "search_web":        "WebSearch",
        "read_url":          "WebFetch",
    }

    capabilities = {
        "subagent": True,       # Claude Code has Task tool
        "persistent_terminal": True,
        "artifacts": False,     # No artifact system like Antigravity
        "image_generation": False,
        "browser": False,
    }

    mcp_tool_prefix = "mcp__"

    notes = [
        "CLAUDE.md is the config entry point",
        "AMAP runtime scaffolds into .claude/",
        "MCP tools use double underscore prefix: mcp__<server>__<tool>",
        "Claude Code uses Task tool for subagent delegation",
    ]
