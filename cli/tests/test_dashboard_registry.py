"""Tests for the dashboard project registry."""

from cli.dashboard import registry


def test_register_adds_absolute_path(tmp_path):
    reg = tmp_path / "projects.yaml"
    proj = tmp_path / "projA"
    proj.mkdir()

    added = registry.register(reg, str(proj))

    assert added is True
    assert registry.load(reg) == [str(proj.resolve())]


def test_register_is_idempotent(tmp_path):
    reg = tmp_path / "projects.yaml"
    proj = tmp_path / "projA"
    proj.mkdir()

    assert registry.register(reg, str(proj)) is True
    assert registry.register(reg, str(proj)) is False
    assert registry.load(reg) == [str(proj.resolve())]


def test_unregister_removes(tmp_path):
    reg = tmp_path / "projects.yaml"
    proj = tmp_path / "projA"
    proj.mkdir()
    registry.register(reg, str(proj))

    assert registry.unregister(reg, str(proj)) is True
    assert registry.load(reg) == []


def test_unregister_absent_returns_false(tmp_path):
    reg = tmp_path / "projects.yaml"
    assert registry.unregister(reg, str(tmp_path / "nope")) is False


def test_prune_missing_drops_deleted_dirs(tmp_path):
    reg = tmp_path / "projects.yaml"
    gone = tmp_path / "gone"
    gone.mkdir()
    registry.register(reg, str(gone))
    gone.rmdir()

    removed = registry.prune_missing(reg)

    assert removed == [str(gone.resolve())]
    assert registry.load(reg) == []


def test_load_missing_file_returns_empty(tmp_path):
    assert registry.load(tmp_path / "does-not-exist.yaml") == []


def test_load_malformed_returns_empty(tmp_path):
    reg = tmp_path / "projects.yaml"
    reg.write_text("{ not: valid: yaml:", encoding="utf-8")
    assert registry.load(reg) == []
