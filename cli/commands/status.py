"""amap status — Show current AMAP configuration in a project.

Reads resolved-config.yaml and reports the current platform, MCPs,
language, and installed skills/workflows.
"""

from pathlib import Path

from cli.scaffold import load_resolved_config


def run_status(target_dir: str) -> None:
    """Show AMAP status for a target project."""
    target = Path(target_dir).resolve()

    # ─── Check for AMAP installation ───
    agents_md = target / "AGENTS.md"

    if not agents_md.exists():
        print(f"\n  ❌ No AMAP installation found in {target}")
        print(f"     Run: amap init --target {target}")
        return

    print()
    print(f"  📁 Project: {target}")
    print()

    # ─── Resolved config ───
    resolved = load_resolved_config(target)
    if resolved is not None:
        platform = resolved.get("platform", "unknown")
        mcps = resolved.get("mcps", [])
        language = resolved.get("language", "unknown")
        version = resolved.get("framework_version", "unknown")

        print(f"  🔧 Framework: AMAP v{version}")
        print(f"  🔌 Platform:  {platform}")
        print(f"  📦 MCPs:      {', '.join(mcps) if mcps else 'none'}")
        print(f"  💬 Language:  {language}")
    else:
        print(f"  ⚠️  No resolved-config.yaml — may be a legacy installation")
        print(f"     Run: amap init --target {target}")

    # ─── Skills ───
    skills_dir = target / ".agent" / "skills"
    if skills_dir.is_dir():
        skills = sorted([d.name for d in skills_dir.iterdir() if d.is_dir()])
        print(f"\n  🧠 Skills ({len(skills)}):")
        for s in skills:
            print(f"     • {s}")

    # ─── Workflows ───
    workflows_dir = target / ".agent" / "workflows"
    if workflows_dir.is_dir():
        wfs = sorted([f.stem for f in workflows_dir.iterdir() if f.is_file() and f.suffix == ".md"])
        print(f"\n  📋 Workflows ({len(wfs)}):")
        for w in wfs:
            print(f"     • /{w}")

    # ─── Knowledge layer ───
    kl_active = target / ".knowledge-layer" / "active"
    kl_archive = target / ".knowledge-layer" / "archive"

    if kl_active.is_dir():
        req = kl_active / "REQUIREMENT.md"
        has_req = req.exists() and req.stat().st_size > 200  # More than just template
        print(f"\n  📋 Active context: {'has content' if has_req else 'empty'}")

    if kl_archive.is_dir():
        tickets = [d.name for d in kl_archive.iterdir() if d.is_dir()]
        print(f"  📦 Archive: {len(tickets)} tickets")

    # ─── Author DNA ───
    dna = target / ".knowledge-layer" / "long-term" / "author-dna.yaml"
    dna_draft = target / ".knowledge-layer" / "long-term" / "author-dna.draft.yaml"
    if dna.exists():
        print(f"  🧬 Author DNA: approved")
    elif dna_draft.exists():
        print(f"  🧬 Author DNA: draft (not yet approved)")
    else:
        print(f"  🧬 Author DNA: not configured")

    print()
