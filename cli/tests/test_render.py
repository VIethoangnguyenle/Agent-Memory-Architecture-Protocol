"""Tests for the Jinja2 renderer."""

import pytest
from jinja2 import TemplateSyntaxError

from cli.renderer import (
    create_renderer,
    render_string,
    copy_and_render_directory,
)


def test_render_string_resolves_tool_names(jinja_env, claude_context):
    out = render_string(jinja_env, "use {{ tools.read_file }}", claude_context)
    assert out == "use Read"


def test_malformed_template_raises_not_swallowed(jinja_env, claude_context):
    # Unclosed tag must raise, never silently pass through.
    with pytest.raises(TemplateSyntaxError):
        render_string(jinja_env, "broken {{ tools.read_file ", claude_context)


def test_directory_render_propagates_template_errors(tmp_path, jinja_env, claude_context):
    src = tmp_path / "src"
    src.mkdir()
    (src / "good.md").write_text("ok {{ tools.read_file }}", encoding="utf-8")
    (src / "bad.md").write_text("broken {{ tools.read_file ", encoding="utf-8")
    dst = tmp_path / "dst"
    with pytest.raises(TemplateSyntaxError):
        copy_and_render_directory(jinja_env, src, dst, claude_context)
