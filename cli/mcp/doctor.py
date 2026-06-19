"""MCP doctor status and report generation."""

from dataclasses import dataclass
from pathlib import Path

from cli.mcp.adapters import get_mcp_adapter
from cli.mcp.config import load_mcp_config, selected_server_matches
from cli.scaffold import load_resolved_config


@dataclass(frozen=True)
class DoctorStatus:
    platform: str
    framework_root: str
    selected_mcps: list[str]
    config_path: Path | None
    native_state: str
    matched: list[str]
    missing: list[str]
    bridge_state: str
    recommendation: str


def build_doctor_status(target: Path, home: Path) -> DoctorStatus:
    resolved = load_resolved_config(target)
    if resolved is None:
        raise ValueError(f"No AMAP resolved-config.yaml found under {target}")
    platform = resolved.get("platform", "generic")
    framework_root = resolved.get("framework_root", get_mcp_adapter(platform).framework_root)
    selected = list(resolved.get("mcps") or [])
    adapter = get_mcp_adapter(platform)

    best_config = None
    for candidate in adapter.config_candidates(target, home):
        config = load_mcp_config(candidate)
        if config.valid:
            best_config = config
            break

    if best_config is None:
        return DoctorStatus(
            platform=platform,
            framework_root=framework_root,
            selected_mcps=selected,
            config_path=None,
            native_state="unavailable",
            matched=[],
            missing=selected,
            bridge_state="not-probed",
            recommendation="create or link a valid MCP config with amap doctor mcp --fix",
        )

    matched, missing = selected_server_matches(best_config, selected)
    if matched and not missing:
        native_state = "configured"
    elif matched:
        native_state = "partial"
    else:
        native_state = "unavailable"

    bridge_state = "not-probed"
    return DoctorStatus(
        platform=platform,
        framework_root=framework_root,
        selected_mcps=selected,
        config_path=best_config.path,
        native_state=native_state,
        matched=matched,
        missing=missing,
        bridge_state=bridge_state,
        recommendation="run native MCP in the IDE/CLI and inspect tool availability",
    )


def render_report(status: DoctorStatus) -> str:
    config_path = status.config_path.as_posix() if status.config_path else "none"
    matched = ", ".join(status.matched) if status.matched else "none"
    missing = ", ".join(status.missing) if status.missing else "none"
    selected = ", ".join(status.selected_mcps) if status.selected_mcps else "none"
    return (
        "# MCP Doctor Report\n\n"
        f"- Platform: {status.platform}\n"
        f"- Framework root: {status.framework_root}\n"
        f"- Selected MCPs: {selected}\n"
        f"- Config path: {config_path}\n"
        f"- native: {status.native_state}\n"
        f"- bridge: {status.bridge_state}\n"
        f"- matched: {matched}\n"
        f"- missing: {missing}\n"
        f"- Recommendation: {status.recommendation}\n"
    )


def write_report(target: Path, status: DoctorStatus) -> Path:
    report = target / status.framework_root / "knowledge" / "active" / "mcp-doctor-report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(status), encoding="utf-8")
    return report
