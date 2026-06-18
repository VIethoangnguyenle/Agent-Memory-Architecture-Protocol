"""amap init — Scaffold AMAP framework into a target project."""

import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from cli.platforms import PLATFORMS, get_platform
from cli.renderer import create_renderer
from cli.scaffold import (
    load_manifest,
    scaffold_plugins,
    scaffold_native_skill_exports,
    generate_resolved_config,
    verify_no_unresolved,
    sync_tree,
)


def prompt_single_checkbox(message: str, choices: List[str], default: int = 0) -> str:
    """Interactive single-select prompt displayed as checkbox-style choices.

    The fallback input remains numeric to keep tests and plain terminals
    deterministic.
    """
    print(f"\n{message}")
    for i, choice in enumerate(choices):
        marker = "x" if i == default else " "
        print(f"  [{marker}] [{i + 1}] {choice}")
    while True:
        raw = input(f"\nChọn một mục (1-{len(choices)}) [{default + 1}]: ").strip()
        if not raw:
            return choices[default]
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass
        print(f"  ⚠️  Chọn số từ 1 đến {len(choices)}")


def prompt_multi_checkbox(message: str, choices: List[dict]) -> List[str]:
    """Interactive multi-select prompt displayed as checkbox-style choices."""
    print(f"\n{message}")
    for i, choice in enumerate(choices):
        print(f"  [ ] [{i + 1}] {choice['display']}")
    print("\nNhập số thứ tự, cách bởi dấu phẩy (vd: 1,2) hoặc Enter để bỏ qua:")
    raw = input("> ").strip()
    if not raw:
        return []
    selected = []
    for part in raw.split(","):
        try:
            idx = int(part.strip()) - 1
            if 0 <= idx < len(choices):
                selected.append(choices[idx]["key"])
        except ValueError:
            pass
    return selected


def gather_choices(manifest: dict) -> Tuple[str, List[str], str]:
    """Interactively gather (platform_key, selected_mcps, language)."""
    mcp_capabilities = manifest.get("mcp_capabilities", {})
    languages = manifest.get("languages", ["java", "typescript", "python", "other"])

    platform_keys = list(PLATFORMS.keys())
    platform_choices = [get_platform(k).display_name for k in platform_keys]
    chosen_display = prompt_single_checkbox("Chọn agent platform:", platform_choices)
    platform_key = platform_keys[platform_choices.index(chosen_display)]
    print(f"\n  ✅ Platform: {get_platform(platform_key).display_name}")

    mcp_choices = [{"key": k, "display": v["display"]} for k, v in mcp_capabilities.items()]
    selected_mcps = prompt_multi_checkbox("MCP servers có sẵn:", mcp_choices)
    print(f"  ✅ MCPs: {', '.join(selected_mcps) or 'none'}")

    language = prompt_single_checkbox("Ngôn ngữ chính của project:", languages)
    print(f"  ✅ Language: {language}")
    return platform_key, selected_mcps, language


def run_init(target_dir: str, amap_root: Optional[str] = None) -> None:
    """Main init command — scaffold AMAP into a target project."""
    target = Path(target_dir).resolve()
    amap = Path(amap_root).resolve() if amap_root else Path(__file__).resolve().parent.parent.parent

    print(f"\n  AMAP Framework v3.0 — init")
    print(f"  Target: {target}\n  Source: {amap}")

    manifest = load_manifest(amap)
    platform_key, selected_mcps, language = gather_choices(manifest)
    platform = get_platform(platform_key)

    print(f"\n{'─' * 50}")
    print(f"  Platform:  {platform.display_name}")
    print(f"  MCPs:      {', '.join(selected_mcps) or 'none'}")
    print(f"  Language:  {language}")
    print(f"  Target:    {target}\n{'─' * 50}")
    if input("\nTiến hành scaffold? [Y/n]: ").strip().lower() == "n":
        print("\n❌ Đã huỷ.")
        return

    context = platform.build_render_context(selected_mcps, language)
    jinja_env = create_renderer(str(amap))
    print("\nScaffolding AMAP framework...\n")

    staging = Path(tempfile.mkdtemp(prefix="amap-init-"))
    try:
        stats = scaffold_plugins(
            manifest.get("plugins", []), amap, staging, context, jinja_env,
            manifest.get("mcp_capabilities", {}), selected_mcps,
        )
        scaffold_native_skill_exports(manifest.get("plugins", []), staging, platform)
        offenders = verify_no_unresolved(staging)
        if offenders:
            print("\n  ❌ Init aborted — unresolved template markers in:")
            for p in offenders:
                print(f"     • {p.relative_to(staging)}")
            print("  Target was NOT modified.")
            return
        sync_tree(staging, target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    generate_resolved_config(target, platform, selected_mcps, language)

    total = stats["rendered"] + stats["copied"] + stats["dirs"]
    print(f"\n{'═' * 50}")
    print(f"  Done! AMAP scaffolded for {platform.display_name}")
    print(f"  {total} plugins installed, {stats['skipped']} skipped")
    print(f"{'═' * 50}")
    print("\n  Next steps:")
    print(f"  1. Customize {platform.framework_root}/knowledge/long-term/persona.yaml")
    print("  2. Run /dna-scan to build author DNA")
    print("  3. Start your first task: /task <ticket-or-idea>\n")
