# README Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `README.md` into a more compelling developer-first README while preserving factual accuracy.

**Architecture:** This is a single-document content rewrite. The README keeps the existing product facts, supported platforms, install flow, skills/workflows, MCP integrations, FAQ, and license, but presents them in a stronger order.

**Tech Stack:** Markdown, shell validation.

---

### Task 1: Rewrite README

**Files:**
- Modify: `README.md`

- [x] **Step 1: Replace README with refreshed structure**

Use sections: hero, why AMAP, quickstart, mental model, architecture, skills/workflows/rules, knowledge lifecycle, compatibility, MCP, design principles, FAQ, contributing, license.

- [x] **Step 2: Validate factual anchors**

Keep install command, platform roots, MCP capabilities, and skill/workflow names aligned with repo files.

- [x] **Step 3: Run lightweight verification**

Run Markdown/link/fact scans and focused tests if needed.
