"""Cursor Platform — Cursor IDE agent."""

from .base import BasePlatform


class CursorPlatform(BasePlatform):

    name = "cursor"
    display_name = "Cursor IDE"
    config_entry_point = ".cursorrules"

    tool_mapping = {
        # ── File Operations (built-in) ──
        "read_file":         "read_file",
        "write_file":        "write_to_file",
        "edit_file":         "edit_file",
        "multi_edit_file":   "edit_file",
        "search_text":       "grep_search",
        "list_directory":    "list_dir",

        # ── Terminal (built-in) ──
        "run_command":       "run_terminal_command",
        "command_status":    "run_terminal_command",
        "send_input":        "run_terminal_command",

        # ── Code Exploration (Socraticode — if available) ──
        "search_code":       "codebase_search",
        "index_code":        "codebase_index",
        "code_status":       "codebase_status",
        "get_dependencies":  "codebase_graph_query",
        "trace_flow":        "codebase_flow",
        "find_blast_radius": "codebase_impact",
        "get_symbol":        "codebase_symbol",
        "list_symbols":      "codebase_symbols",
        "graph_stats":       "codebase_graph_stats",
        "graph_build":       "codebase_graph_build",

        # ── Web ──
        "search_web":        "web_search",
        "read_url":          "fetch_url",
    }

    capabilities = {
        "subagent": False,
        "persistent_terminal": False,
        "artifacts": False,
        "image_generation": False,
        "browser": False,
    }

    native_skill_export = {"dir": ".cursor/commands", "strip_frontmatter": True, "flatten": True}

    notes = [
        ".cursorrules is the config entry point",
        "Cursor has limited MCP support — check version",
        "No subagent capability — workflows degrade to sequential",
        "Skills/workflows export to .cursor/commands/ as manual commands — Cursor does "
        "not auto-trigger them from a description the way a real skill picker would",
    ]
