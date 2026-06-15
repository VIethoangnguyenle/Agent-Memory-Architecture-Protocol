# 🧠 Agent Memory Architecture Protocol (AMAP)

> **Version 3.0** · A structured memory and workflow protocol that gives AI coding agents persistent context, enforced workflows, and architectural guardrails across coding sessions.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## The Problem

AI coding agents (Copilot, Gemini, Claude, Cursor, etc.) suffer from **session amnesia**:

- They forget architectural decisions between conversations
- They jump straight to code without understanding requirements
- They ignore existing naming conventions and design patterns
- They can't trace the impact of changes across a codebase
- They have no concept of "workflow" — just prompt → response

**AMAP solves this** by providing a structured protocol that any AI agent can follow, giving it working memory, enforced multi-phase workflows, and persistent knowledge accumulation.

---

## How It Works

AMAP enforces a **5-phase workflow** for every task:

```
Ideation → Requirement → Architecture → Spec → Apply
    ↓           ↓             ↓           ↓       ↓
 ideation-   REQUIREMENT   EXPLORE     Technical  Code
 *.md        .md           _CONTEXT    Spec       Changes
                           .md
```

Each phase has:
- **Dedicated skills** — specialized agent modules for each role (Business Analyst, DB Explorer, Code Mapper, Architecture Reviewer, etc.)
- **Enforced rules** — agents cannot skip phases or jump to code without context
- **Persistent artifacts** — knowledge accumulates across sessions in structured files
- **Observability** — every decision, tool call, and assumption is logged

---

## Architecture Overview

```
project-root/
│
├── AGENTS.md                          ← Meta-prompt (agents read this first)
│
├── .knowledge-layer/                  ← Working Memory Layer
│   ├── active/                        ← Runtime context for current task
│   │   ├── REQUIREMENT.md             ← Standardized requirements
│   │   ├── EXPLORE_CONTEXT.md         ← DB + codebase exploration results
│   │   ├── AGENT_TRANSPARENCY.md      ← Observability log (audit trail)
│   │   ├── TOKEN_LOG.md               ← Token usage tracking per phase
│   │   └── ideation/                  ← Raw ideas before they become tickets
│   ├── archive/                       ← Completed task contexts (by ticket-id)
│   └── templates/                     ← Static templates + accumulated knowledge
│       ├── knowledge-snapshot.md      ← System architecture (grows over time)
│       ├── conventions.yaml           ← Codebase naming/design conventions
│       ├── author-dna.yaml            ← Author's coding philosophy (judgment layer)
│       └── persona.yaml               ← Agent interaction style (per-user)
│
├── .agent/                            ← Agent Infrastructure Layer
│   ├── rules/                         ← Guardrails (flow, tool, data, architecture)
│   │   ├── RULES.md                   ← Rules manifest (entry point)
│   │   ├── rules-flow.md              ← Workflow constraints
│   │   ├── rules-tool.md              ← MCP & tool permissions
│   │   ├── rules-exec.md              ← Cost, budget & observability
│   │   ├── rules-knowledge.md         ← Knowledge lifecycle & path conventions
│   │   └── rules-guard.md             ← Pre-invoke guards & teaching moments
│   ├── skills/                        ← Reusable skill modules (12 skills)
│   ├── workflows/                     ← Orchestration logic
│   └── scripts/                       ← Bootstrap & utility scripts
│
├── workflows/                         ← User-facing workflow shortcuts
└── templates/                         ← User-facing template shortcuts
```

---

## Key Concepts

### 🔧 Skills (Modular Agent Capabilities)

| Skill | Role | When Used |
|-------|------|-----------|
| `requirement-analyst` | Business Analyst — standardizes requirements | When a ticket/task is received |
| `spec-extract` | Doc Analyst — extracts specs from wiki/PRD | When requirements come from documents |
| `db-explorer` | DB Explorer — discovers schema, constraints | When task touches data layer |
| `codebase-explorer` | Code Mapper — maps requirements → modules/files | After DB exploration |
| `architecture-reviewer` | Arch Reviewer — detects conflicts & risks | Before generating specs |
| `knowledge-curator` | Knowledge Manager — archives & accumulates knowledge | After task completion |
| `convention-intelligence-builder` | Convention Scanner — extracts naming patterns | On project onboarding |
| `author-dna-builder` | DNA Builder — encodes author's coding philosophy | Captures design preferences |
| `spec-validator` | Spec Validator — pre/post-apply verification | Before and after code changes |
| `infra-tdd` | TDD Builder — 5-layer Technical Design Document | For infrastructure-impacting changes |
| `document-writer` | Doc Writer — technical documentation | README, ADR, architecture docs |
| `openspec-*` | OpenSpec integration — propose, explore, apply, archive | Spec-driven code generation |

### 📋 Workflows (Orchestration Commands)

| Command | Phase | Description |
|---------|-------|-------------|
| `/task <idea-or-ticket>` | Phase 1 | Understand the problem, standardize requirements, explore DB/code/architecture |
| `/task spec <ticket>` | Phase 2 | Generate technical specification |
| `/task apply <ticket>` | Phase 3 | Apply specification to code |
| `/idea-to-task` | Pre-task | Convert raw ideation into a draft ticket |
| `/index-source` | Utility | Index codebase for semantic search (via Socraticode) |
| `/convention-scan` | Utility | Scan and extract codebase conventions |
| `/dna-scan` | Utility | Scan and encode author's coding philosophy |

### 🛡️ Rules (Guardrails)

The rule system prevents common AI agent failures:

- **Flow Rules** — Agents cannot skip phases or jump to code without context
- **Tool Rules** — DB access is read-only, code changes only through approved specs
- **Data Rules** — PII is never logged, sample data is size-limited
- **Architecture Rules** — Confidence levels tied to exploration completeness
- **Cost Rules** — Token budgets per phase with automatic warnings
- **Knowledge Rules** — Mandatory archiving, source-of-truth hierarchy
- **Guard Rules** — Pre-invoke checks, teaching moment capture, convention enforcement

### 🧬 Persistent Knowledge Stores

| Store | Purpose | Grows Over Time? |
|-------|---------|-----------------|
| `knowledge-snapshot.md` | System architecture map (tables, modules, entry points, business rules) | ✅ Yes — accumulates after every task |
| `conventions.yaml` | Naming conventions, design patterns, upstream constraints | ✅ Yes — updated after convention scans |
| `author-dna.yaml` | Author's coding philosophy and design preferences | ✅ Yes — enriched via teaching moments |
| `archive/{ticket-id}/` | Complete context snapshots of finished tasks | ✅ Yes — grows with each completed task |

---

## Quick Start

### 1. Clone and integrate into your project

```bash
# Clone the protocol
git clone https://github.com/VIethoangnguyenle/Agent-Memory-Architecture-Protocol.git

# Copy the protocol files into your existing project
cp -r Agent-Memory-Architecture-Protocol/.agent your-project/.agent
cp -r Agent-Memory-Architecture-Protocol/.knowledge-layer your-project/.knowledge-layer
cp Agent-Memory-Architecture-Protocol/AGENTS.md your-project/AGENTS.md
```

### 2. Customize your persona (optional)

```bash
cd your-project
cp .knowledge-layer/templates/persona.template.yaml .knowledge-layer/templates/persona.yaml
# Edit persona.yaml to customize how the agent interacts with you
```

### 3. Start using with your AI agent

The agent reads `AGENTS.md` at the root and bootstraps automatically. On first message, the agent will:

1. Read `AGENTS.md` + all rules
2. Scan and load all skills
3. Load workflows and scripts
4. Check for active context
5. Report bootstrap status

Then you can start working:

```
# Start with a new idea
/task Add daily transaction limit per employee

# Start with an existing ticket
/task https://jira.example.com/browse/ABC-123

# Generate technical spec
/task spec ABC-123

# Apply spec to code
/task apply ABC-123
```

---

## Agent Compatibility

AMAP works with any AI coding agent that reads project files. Here's how each tool discovers it:

| AI Tool | Entry Point | How to Set Up |
|---------|-------------|---------------|
| **Gemini CLI / Jules** | `AGENTS.md` (native) | ✅ Works out of the box |
| **Google Antigravity** | User Rules | ✅ Works out of the box |
| **Claude Code** | `CLAUDE.md` | Create `CLAUDE.md` pointing to `AGENTS.md` |
| **Cursor** | `.cursorrules` | Create `.cursorrules` pointing to `AGENTS.md` |
| **GitHub Copilot** | `.github/copilot-instructions.md` | Create instructions file pointing to `AGENTS.md` |
| **Windsurf** | `.windsurfrules` | Create rules file pointing to `AGENTS.md` |
| **Perplexity / AI Search** | `README.md` | ✅ This file provides the overview |

### MCP Server Integrations (Optional)

AMAP is designed to work with these MCP servers when available:

| MCP Server | Purpose |
|------------|---------|
| **Socraticode** | Semantic code search, dependency graphs, symbol analysis |
| **Confluence** | Wiki/PRD document extraction |
| **db-remote** | Database schema exploration (read-only) |

---

## Design Principles

1. **Flow over freestyle** — Structured phases prevent premature coding
2. **Evidence-based architecture** — Explore DB and code before proposing changes
3. **Knowledge accumulation** — Every task makes the agent smarter for the next one
4. **Human in the loop** — Critical decisions always require user confirmation
5. **Observability by default** — Every agent action is logged and auditable
6. **Convention enforcement** — Naming and design patterns are codified, not memorized
7. **Teaching moments** — When a user corrects the agent, the lesson is captured permanently

---

## The Knowledge Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│                    Active Task                          │
│                                                         │
│   REQUIREMENT.md ──→ EXPLORE_CONTEXT.md ──→ SPEC       │
│        ↓                    ↓                  ↓        │
│   requirement-        db-explorer +       openspec-     │
│   analyst             codebase-explorer   propose       │
│                             ↓                           │
│                    architecture-reviewer                │
└───────────────────────────┬─────────────────────────────┘
                            │ Task Complete
                            ▼
┌─────────────────────────────────────────────────────────┐
│               knowledge-curator                         │
│                                                         │
│   1. Archive active/ → archive/{ticket-id}/             │
│   2. Update knowledge-snapshot.md with new findings     │
│   3. Reset active/ to template skeleton                 │
│   4. Flag if conventions need re-scanning               │
└─────────────────────────────────────────────────────────┘
```

---

## Example: What a Bootstrap Report Looks Like

When an agent first starts working in a project with AMAP, it produces a bootstrap report:

```
✅ Core: AGENTS.md v3.0 + RULES (manifest + 5 modules: flow, tool, exec, knowledge, guard)
✅ Skills: [requirement-analyst | spec-extract | db-explorer | codebase-explorer |
           architecture-reviewer | knowledge-curator | convention-intelligence-builder |
           author-dna-builder | spec-validator | infra-tdd]
✅ Workflows: [/task | /idea-to-task | /index-source]
📋 Active context: [REQUIREMENT: empty | EXPLORE_CONTEXT: empty]
🧬 Author DNA: approved
📦 Archive: [3 tickets archived]
Ready!
```

---

## FAQ

### Can I use this with a private/enterprise codebase?

Yes. AMAP is a protocol layer — it doesn't contain any application code. Copy the `.agent/` and `.knowledge-layer/` directories into your private repo and customize `knowledge-snapshot.md` with your system's architecture.

### Does this replace my existing AI tool?

No. AMAP enhances your existing AI tool by giving it structure. Your AI agent (Gemini, Claude, Cursor, etc.) reads the protocol files and follows the workflow — it doesn't replace the agent itself.

### What if my AI agent doesn't support AGENTS.md?

Create a pointer file for your specific tool (see [Agent Compatibility](#agent-compatibility) table). The pointer file just tells the agent to read `AGENTS.md` for full instructions.

### How do I prevent sensitive data from leaking?

AMAP has built-in data rules (R-Data-1, R-Data-2) that prohibit agents from logging PII or credentials into any context file. The `active/` directory is gitignored by default.

### Can multiple team members use this?

Yes. The `persona.yaml` file is gitignored — each developer has their own interaction style. Shared knowledge (`knowledge-snapshot.md`, `conventions.yaml`, `author-dna.yaml`) is committed and version-controlled.

---

## Contributing

This project is in active development. Contributions are welcome:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with a clear description

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <i>Built with ❤️ for AI-assisted software engineering</i>
</p>
