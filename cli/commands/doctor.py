"""amap doctor - diagnostics for AMAP runtime dependencies."""

from pathlib import Path
from typing import Optional

from cli.mcp.doctor import build_doctor_status, write_report


def run_doctor_mcp(
    target_dir: str,
    fix: bool = False,
    assume_yes: bool = False,
    home: Optional[Path] = None,
) -> None:
    target = Path(target_dir).resolve()
    home_path = home or Path.home()
    status = build_doctor_status(target, home_path)
    report = write_report(target, status)
    print(f"\n  MCP doctor report: {report}")
    print(f"  native: {status.native_state} | bridge: {status.bridge_state}")
    if fix:
        print("  --fix requested, but fix operations are added in the next task.")
