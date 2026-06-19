import json

import yaml

from cli.commands.doctor import run_doctor_mcp


def write_resolved(target, platform="antigravity", mcps=None):
    root = ".agents" if platform in ("antigravity", "codex") else ".claude"
    path = target / root / "resolved-config.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(
        yaml.dump({"resolved": {
            "platform": platform,
            "framework_root": root,
            "mcps": mcps or ["socraticode"],
            "language": "python",
        }}),
        encoding="utf-8",
    )
    return path


def test_doctor_writes_report_for_missing_native_config(tmp_path):
    target = tmp_path / "proj"
    home = tmp_path / "home"
    write_resolved(target)

    run_doctor_mcp(str(target), fix=False, assume_yes=False, home=home)

    report = target / ".agents" / "knowledge" / "active" / "mcp-doctor-report.md"
    text = report.read_text(encoding="utf-8")
    assert "Platform: antigravity" in text
    assert "socraticode" in text
    assert "native: unavailable" in text


def test_doctor_matches_selected_server_in_existing_config(tmp_path):
    target = tmp_path / "proj"
    home = tmp_path / "home"
    write_resolved(target, mcps=["socraticode", "db-remote"])
    cfg = target / ".agents" / "mcp_config.json"
    cfg.write_text(json.dumps({"mcpServers": {"socraticode": {"command": "npx"}}}), encoding="utf-8")

    run_doctor_mcp(str(target), fix=False, assume_yes=False, home=home)

    text = (target / ".agents" / "knowledge" / "active" / "mcp-doctor-report.md").read_text(encoding="utf-8")
    assert "matched: socraticode" in text
    assert "missing: db-remote" in text
