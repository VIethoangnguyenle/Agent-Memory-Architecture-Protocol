"""Shared fixtures for AMAP CLI tests."""

from pathlib import Path

import pytest

from cli.renderer import create_renderer
from cli.platforms import get_platform


@pytest.fixture
def amap_root() -> Path:
    """Repo root = the AMAP source (this repo)."""
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def jinja_env(amap_root):
    return create_renderer(str(amap_root))


@pytest.fixture
def claude_context():
    """Render context for the claude-code platform, no MCPs."""
    return get_platform("claude-code").build_render_context([], "python")
