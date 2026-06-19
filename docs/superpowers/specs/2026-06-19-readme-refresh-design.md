# README Refresh Design

Date: 2026-06-19

## Goal

Rewrite `README.md` so the project feels compelling to new developers without losing technical correctness.

## Direction

Use a developer-first open-source README with a sharper opening:

- Lead with the core thesis: AMAP gives AI coding agents memory, workflow, and guardrails.
- Move quickstart earlier.
- Keep architecture, platform, MCP, workflow, skill, and license facts accurate.
- Avoid unsupported claims such as benchmark numbers or production adoption.
- Keep Vietnamese as the primary language.

## Scope

Modify:

- `README.md`

Allowed cleanup:

- Fix copy-paste-hostile `{framework_root}` examples by showing platform-specific paths.
- Tighten verbose prose.
- Reorder sections for onboarding clarity.

Out of scope:

- CLI behavior changes
- Runtime `.amap` instruction changes
- New claims that require external validation
