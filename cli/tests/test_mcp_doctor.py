import json

import yaml

from cli.commands.doctor import run_doctor_mcp
from cli.mcp.doctor import build_doctor_status


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
    assert "bridge: not-probed" in text


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
    assert "native: partial" in text
    assert "bridge: not-probed" in text


def test_build_doctor_status_marks_partial_native_state_for_partial_match(tmp_path):
    target = tmp_path / "proj"
    home = tmp_path / "home"
    write_resolved(target, mcps=["socraticode", "db-remote"])
    cfg = target / ".agents" / "mcp_config.json"
    cfg.write_text(json.dumps({"mcpServers": {"socraticode": {"command": "npx"}}}), encoding="utf-8")

    status = build_doctor_status(target, home)

    assert status.native_state == "partial"
    assert status.bridge_state == "not-probed"


def test_build_doctor_status_marks_missing_config_as_unavailable_and_not_probed(tmp_path):
    target = tmp_path / "proj"
    home = tmp_path / "home"
    write_resolved(target)

    status = build_doctor_status(target, home)

    assert status.native_state == "unavailable"
    assert status.bridge_state == "not-probed"


def test_doctor_report_redacts_secrets_in_matched_server_config(tmp_path):
    target = tmp_path / "proj"
    home = tmp_path / "home"
    write_resolved(target, mcps=["socraticode"])
    cfg = target / ".agents" / "mcp_config.json"
    cfg.write_text(
        json.dumps({"mcpServers": {"socraticode": {"command": "npx", "env": {"TOKEN": "supersecret"}}}}),
        encoding="utf-8",
    )

    run_doctor_mcp(str(target), fix=False, assume_yes=False, home=home)

    text = (target / ".agents" / "knowledge" / "active" / "mcp-doctor-report.md").read_text(encoding="utf-8")
    assert "npx" in text            # non-secret detail is shown
    assert "<redacted>" in text     # env value is redacted
    assert "supersecret" not in text


def test_doctor_reports_friendly_error_when_not_amap_project(tmp_path, capsys):
    target = tmp_path / "not-amap"
    target.mkdir()

    run_doctor_mcp(str(target), fix=False, assume_yes=False, home=tmp_path / "home")

    out = capsys.readouterr().out
    assert "resolved-config" in out


def test_doctor_fix_copies_known_good_antigravity_ide_config(tmp_path):
    target = tmp_path / "proj"
    home = tmp_path / "home"
    write_resolved(target, platform="antigravity", mcps=["socraticode"])
    source = home / ".gemini" / "antigravity" / "mcp_config.json"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps({"mcpServers": {"socraticode": {"command": "npx"}}}), encoding="utf-8")

    run_doctor_mcp(str(target), fix=True, assume_yes=True, home=home)

    dest = home / ".gemini" / "antigravity-cli" / "mcp_config.json"
    assert dest.exists()
    assert json.loads(dest.read_text(encoding="utf-8"))["mcpServers"]["socraticode"]["command"] == "npx"


def test_doctor_fix_backs_up_existing_non_empty_destination(tmp_path):
    target = tmp_path / "proj"
    home = tmp_path / "home"
    write_resolved(target, platform="antigravity", mcps=["socraticode"])
    source = home / ".gemini" / "antigravity" / "mcp_config.json"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps({"mcpServers": {"socraticode": {"command": "npx"}}}), encoding="utf-8")
    dest = home / ".gemini" / "antigravity-cli" / "mcp_config.json"
    dest.parent.mkdir(parents=True)
    dest.write_text(json.dumps({"mcpServers": {"old": {"command": "old"}}}), encoding="utf-8")

    run_doctor_mcp(str(target), fix=True, assume_yes=True, home=home)

    assert (dest.parent / "mcp_config.json.bak").exists()
    assert "old" in (dest.parent / "mcp_config.json.bak").read_text(encoding="utf-8")
