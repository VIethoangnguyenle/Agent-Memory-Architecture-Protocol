"""Base platform definition — abstract interface for all agent platforms."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BasePlatform(ABC):
    """Each platform provides tool mapping + config format + capabilities.

    A platform represents a specific AI agent runtime environment
    (Antigravity, Claude Code, Cursor, etc.) and defines how
    abstract AMAP operations map to concrete tool calls.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Platform identifier (e.g., 'antigravity', 'claude-code')."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name (e.g., 'Google Antigravity')."""

    @property
    @abstractmethod
    def config_entry_point(self) -> str:
        """File the platform reads as system prompt / agent config.

        Antigravity: AGENTS.md (loaded via user_rules)
        Claude Code: CLAUDE.md
        Cursor: .cursorrules
        """

    @property
    @abstractmethod
    def tool_mapping(self) -> Dict[str, str]:
        """Map abstract operation → concrete tool name.

        Keys are abstract operations used in Jinja2 templates.
        Values are the exact tool names for this platform.
        """

    @property
    def capabilities(self) -> Dict[str, bool]:
        """Platform-specific capabilities."""
        return {
            "subagent": False,
            "persistent_terminal": False,
            "artifacts": False,
            "image_generation": False,
            "browser": False,
        }

    @property
    def mcp_tool_prefix(self) -> str:
        """How this platform prefixes MCP tool names.

        Antigravity: 'mcp_<server>_<tool>'
        Claude Code: 'mcp__<server>__<tool>'
        """
        return ""

    @property
    def native_skill_export(self) -> Optional[dict]:
        """Where (if anywhere) this platform natively auto-discovers skills.

        None = no native discovery; skills/workflows are reachable only via
        bootstrap.md's manual PHASE 1 self-registration (works on every
        platform, including this one).

        dir: root directory; the skill/workflow name is appended automatically.
        strip_frontmatter: True means export as a flat <name>.md with YAML
          frontmatter removed — pre_conditions (if any) are re-rendered into
          the body as a checklist instead of being silently dropped (see
          export_as_flat_command in cli/scaffold.py).
        flatten: True means output is <dir>/<name>.md (no subfolder); False
          means <dir>/<name>/SKILL.md.
        """
        return None

    @property
    def notes(self) -> List[str]:
        """Platform-specific notes shown during init."""
        return []

    def get_tool(self, abstract_name: str) -> str:
        """Resolve abstract operation to concrete tool name.

        Returns the abstract name itself if no mapping exists
        (graceful degradation).
        """
        return self.tool_mapping.get(abstract_name, abstract_name)

    def build_render_context(self, mcps: List[str], language: str) -> dict:
        """Build the full Jinja2 render context for this platform."""
        return {
            "platform": {
                "name": self.name,
                "display_name": self.display_name,
                "config_entry_point": self.config_entry_point,
            },
            "tools": self.tool_mapping,
            "capabilities": self.capabilities,
            "mcps": mcps,
            "language": language,
            "framework_version": "3.0",
        }
