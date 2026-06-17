"""amap update — re-render framework files, preserve user files.

Renders into a temp staging dir, verifies zero unresolved markers, then
syncs framework files over the target. Aborts without touching the target
if anything fails.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Optional

from cli.platforms import PLATFORMS, get_platform
from cli.renderer import create_renderer
from cli.scaffold import (
    load_manifest,
    load_resolved_config,
    scaffold_plugins,
    verify_no_unresolved,
    sync_tree,
    generate_resolved_config,
)


def run_update(target_dir: str, amap_root: Optional[str] = None, reconfigure: bool = False) -> None:
    """Re-render framework files into an existing AMAP project."""
    target = Path(target_dir).resolve()
    amap = Path(amap_root).resolve() if amap_root else Path(__file__).resolve().parent.parent.parent

    resolved = load_resolved_config(target)
    if resolved is None:
        print(f"\n  ❌ No AMAP installation found in {target}")
        print(f"     Run: amap init --target {target}")
        return

    manifest = load_manifest(amap)

    if reconfigure:
        from cli.commands.init import gather_choices
        print("\n  AMAP update — reconfigure\n")
        platform_key, selected_mcps, language = gather_choices(manifest)
    else:
        platform_key = resolved.get("platform", "generic")
        selected_mcps = resolved.get("mcps", [])
        language = resolved.get("language", "other")

    platform = get_platform(platform_key)
    context = platform.build_render_context(selected_mcps, language)
    jinja_env = create_renderer(str(amap))

    print(f"\n  Updating AMAP ({platform.display_name})...\n")
    staging = Path(tempfile.mkdtemp(prefix="amap-update-"))
    try:
        scaffold_plugins(
            manifest.get("plugins", []), amap, staging, context, jinja_env,
            manifest.get("mcp_capabilities", {}), selected_mcps,
            only_framework=True,
        )
        offenders = verify_no_unresolved(staging)
        if offenders:
            print("\n  ❌ Update aborted — unresolved template markers in:")
            for p in offenders:
                print(f"     • {p.relative_to(staging)}")
            print("  Target was NOT modified.")
            return
        count = sync_tree(staging, target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    if reconfigure:
        generate_resolved_config(target, platform_key, selected_mcps, language)
        # Remove stale entry-point files left by the previous platform.
        current_entry = platform.config_entry_point
        for key in PLATFORMS:
            other_entry = get_platform(key).config_entry_point
            if other_entry != current_entry:
                stale = target / other_entry
                if stale.exists():
                    stale.unlink()
                    print(f"  🗑️  Removed stale entry point: {other_entry}")

    print(f"\n  ✅ Updated {count} framework files. User files preserved.\n")
