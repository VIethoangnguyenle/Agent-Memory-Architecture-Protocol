"""Shared fixtures for Maika CLI tests."""

from pathlib import Path

import pytest

from cli.renderer import create_renderer
from cli.platforms import get_platform


@pytest.fixture
def maika_root() -> Path:
    """Repo root = the Maika source (this repo)."""
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def jinja_env(maika_root):
    return create_renderer(str(maika_root))


@pytest.fixture
def claude_context():
    """Render context for the claude-code platform, no MCPs."""
    return get_platform("claude-code").build_render_context([], "python")
