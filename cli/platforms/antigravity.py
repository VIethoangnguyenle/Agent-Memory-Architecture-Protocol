"""Antigravity Platform — Google Antigravity (Gemini-based agent)."""

from .base import BasePlatform


class AntigravityPlatform(BasePlatform):

    name = "antigravity"
    display_name = "Google Antigravity (Gemini)"
    config_entry_point = "AGENTS.md"
    framework_root = ".agents"
    native_skill_export = None

    tool_mapping = {
        # ── File Operations ──
        "read_file":         "view_file",
        "write_file":        "write_to_file",
        "edit_file":         "replace_file_content",
        "multi_edit_file":   "multi_replace_file_content",
        "search_text":       "grep_search",
        "list_directory":    "list_dir",

        # ── Terminal ──
        "run_command":       "run_command",
        "command_status":    "command_status",
        "send_input":        "send_command_input",

        # ── Code Exploration (Socraticode) ──
        "search_code":       "mcp_socraticode_codebase_search",
        "index_code":        "mcp_socraticode_codebase_index",
        "code_status":       "mcp_socraticode_codebase_status",
        "get_dependencies":  "mcp_socraticode_codebase_graph_query",
        "trace_flow":        "mcp_socraticode_codebase_flow",
        "find_blast_radius": "mcp_socraticode_codebase_impact",
        "get_symbol":        "mcp_socraticode_codebase_symbol",
        "list_symbols":      "mcp_socraticode_codebase_symbols",
        "graph_stats":       "mcp_socraticode_codebase_graph_stats",
        "graph_build":       "mcp_socraticode_codebase_graph_build",

        # ── Document Search (Confluence) ──
        "search_docs":       "mcp_confluence-servicehub_confluence_search",
        "get_page":          "mcp_confluence-servicehub_confluence_get_page",
        "list_spaces":       "mcp_confluence-servicehub_confluence_list_spaces",
        "get_space_pages":   "mcp_confluence-servicehub_confluence_get_space_pages",

        # ── Database (db_access MCP — server-level reference) ──
        "db_query":          "db-remote",

        # ── Web & Browser ──
        "search_web":        "search_web",
        "read_url":          "read_url_content",
        "browser_agent":     "browser_subagent",

        # ── Image ──
        "generate_image":    "generate_image",

        # ── Dynamic Memory (agent-memory MCP — tool-level; optional at runtime) ──
        "dynamic_memory_search":   "mcp_agent-memory_memory_smart_search",
        "dynamic_memory_recall":   "mcp_agent-memory_memory_recall",
        "dynamic_memory_sessions": "mcp_agent-memory_memory_sessions",
        "dynamic_memory_audit":    "mcp_agent-memory_memory_audit",
        "dynamic_memory_health":   "mcp_agent-memory_memory_health",
        "dynamic_memory_save":     "mcp_agent-memory_memory_save",
        "dynamic_memory_forget":   "mcp_agent-memory_memory_governance_delete",
    }

    capabilities = {
        "subagent": True,
        "artifacts": True,
        "browser": True,
        "write_gate_hook": True,
    }

    mcp_tool_prefix = "mcp_"

    notes = [
        "AGENTS.md is loaded via user_rules in Antigravity config",
        "AMAP runtime scaffolds into .agents/",
        "MCP tools use prefix: mcp_<server>_<tool>",
        "Supports browser_subagent for visual tasks",
    ]
