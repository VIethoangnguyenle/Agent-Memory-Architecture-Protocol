"""Platform registry — discover and load platform definitions."""

from .antigravity import AntigravityPlatform
from .claude_code import ClaudeCodePlatform
from .codex import CodexPlatform
from .generic import GenericPlatform

PLATFORMS = {
    "antigravity": AntigravityPlatform,
    "claude-code": ClaudeCodePlatform,
    "generic": GenericPlatform,
    "codex": CodexPlatform,
}


def get_platform(name: str):
    """Get platform class by name."""
    cls = PLATFORMS.get(name)
    if not cls:
        raise ValueError(f"Unknown platform: {name}. Available: {list(PLATFORMS.keys())}")
    return cls()
