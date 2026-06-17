"""Tests for the shared scaffolding core."""

from cli.scaffold import (
    load_manifest,
    has_capability,
    get_ownership,
    resolve_source_path,
)


def test_get_ownership_defaults_to_framework():
    assert get_ownership({"name": "x"}) == "framework"
    assert get_ownership({"name": "x", "ownership": "user"}) == "user"


def test_load_manifest_has_plugins(amap_root):
    manifest = load_manifest(amap_root)
    assert len(manifest["plugins"]) > 0
    assert "mcp_capabilities" in manifest


def test_has_capability(amap_root):
    manifest = load_manifest(amap_root)
    caps = manifest["mcp_capabilities"]
    assert has_capability(["socraticode"], caps, "code_exploration") is True
    assert has_capability([], caps, "code_exploration") is False


def test_resolve_source_path_maps_skills(amap_root):
    p = resolve_source_path(amap_root, "skills/codebase-explorer/")
    assert p == amap_root / ".agent/skills/codebase-explorer/"
