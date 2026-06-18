"""Tests for platform adapter definitions."""

from cli.platforms.generic import GenericPlatform


def test_generic_platform_has_no_native_skill_export():
    assert GenericPlatform().native_skill_export is None
