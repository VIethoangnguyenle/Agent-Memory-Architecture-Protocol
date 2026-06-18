"""Codex Platform — OpenAI Codex CLI agent."""

from .base import BasePlatform


class CodexPlatform(BasePlatform):

    name = "codex"
    display_name = "OpenAI Codex CLI"
    config_entry_point = "AGENTS.md"

    native_skill_export = {"dir": ".agents/skills", "strip_frontmatter": False, "flatten": False}

    tool_mapping = {
        # Codex CLI does not publicly document its internal tool names the
        # way Claude Code/Antigravity do — keep abstract passthrough (same
        # approach as GenericPlatform) rather than inventing concrete names.
        "read_file":         "read_file",
        "write_file":        "write_file",
        "edit_file":         "edit_file",
        "multi_edit_file":   "multi_edit_file",
        "search_text":       "search_text",
        "list_directory":    "list_directory",
        "run_command":       "run_command",
        "command_status":    "command_status",
        "send_input":        "send_input",
        "search_code":       "search_code",
        "index_code":        "index_code",
        "code_status":       "code_status",
        "get_dependencies":  "get_dependencies",
        "trace_flow":        "trace_flow",
        "find_blast_radius": "find_blast_radius",
        "get_symbol":        "get_symbol",
        "list_symbols":      "list_symbols",
        "graph_stats":       "graph_stats",
        "graph_build":       "graph_build",
        "search_docs":       "search_docs",
        "get_page":          "get_page",
        "list_spaces":       "list_spaces",
        "search_web":        "search_web",
        "read_url":          "read_url",
    }

    notes = [
        "AGENTS.md is the config entry point (developers.openai.com/codex/guides/agents-md)",
        "tool_mapping is abstract passthrough — Codex CLI's internal tool names are not "
        "publicly documented; map manually if your AMAP skills need concrete tool calls",
        "Skills/workflows export to .agents/skills/ — the open agent-skills standard, "
        "shared with Antigravity",
    ]
