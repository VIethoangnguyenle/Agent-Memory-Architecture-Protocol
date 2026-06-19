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

        # ── Web & Browser ──
        "search_web":        "search_web",
        "read_url":          "read_url_content",
        "browser_agent":     "browser_subagent",

        # ── Image ──
        "generate_image":    "generate_image",
    }

    capabilities = {
        "subagent": True,
        "persistent_terminal": True,
        "artifacts": True,
        "image_generation": True,
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
