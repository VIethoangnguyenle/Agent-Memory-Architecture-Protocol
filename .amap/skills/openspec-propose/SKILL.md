---
name: openspec-propose
version: '1.0'
description: >
  Propose a new change with all artifacts generated in one step.
  Use when the user wants to quickly describe what they want to build and get a complete proposal with design, specs, and tasks ready for implementation.
  NOT for: exploring ideas/brainstorming (→ openspec-explore),
  validating existing specs (→ spec-validator), writing TDD documents (→ infra-tdd).
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.2.0"
pre_conditions:
  - file: .amap/knowledge/active/REQUIREMENT.md
    condition: not_skeleton
    on_fail: "ABORT — chạy requirement-analyst trước"
  - file: .amap/knowledge/active/EXPLORE_CONTEXT.md
    condition: not_skeleton
    on_fail: "WARN — EXPLORE_CONTEXT thiếu, spec sẽ có Độ tin cậy THẤP"
  - phase: pha-1
    condition: phase_done
    on_fail: "ABORT — Pha 1 chưa hoàn thành (kiểm tra marker `Pha 1 DONE` trong AGENT_TRANSPARENCY)"
---

Propose a new change - create the change and generate all artifacts in one step.

I'll create a change with artifacts:
- proposal.md (what & why)
- design.md (how)
- tasks.md (implementation steps)

When ready to implement, run /opsx:apply

---

## Mục tiêu

- Tạo change proposal hoàn chỉnh với đầy đủ artifacts (proposal, design, tasks) trong một bước duy nhất.
- Chuyển yêu cầu của người dùng thành kế hoạch implementation sẵn sàng apply.

---

## Khi nào sử dụng

- Khi người dùng muốn mô tả nhanh những gì họ muốn xây và nhận được proposal hoàn chỉnh.
- Sau khi đã hoàn thành Pha 1 (requirement + explore) trong `/task`.
- Khi cần sinh spec kỹ thuật cho một thay đổi cụ thể.

---

## Khi nào KHÔNG sử dụng

- Khi cần brainstorm, khám phá ý tưởng (→ openspec-explore).
- Khi cần validate spec đã có (→ spec-validator).
- Khi cần viết TDD 5 tầng (→ infra-tdd).
- Khi cần review kiến trúc (→ architecture-reviewer).

---

## Quy trình

**Input**: The user's request should include a change name (kebab-case) OR a description of what they want to build.

**Steps**

0. **Load knowledge-layer context (nếu tồn tại)**

   Trước khi tạo change, kiểm tra và đọc context từ pipeline `/task`:
   - `.amap/knowledge/active/REQUIREMENT.md` → dùng làm input cho proposal (what & why).
   - `.amap/knowledge/active/EXPLORE_CONTEXT.md` → dùng làm input cho design (how).
   - `.amap/knowledge/long-term/knowledge-snapshot.md` → bối cảnh hệ thống tổng quan.

   Nếu các file này có nội dung (không chỉ là template trống):
   - Dùng chúng để populate `proposal.md`, `design.md` thay vì hỏi user từ đầu.
   - Ghi note trong proposal: "Context loaded from knowledge-layer pipeline".

   Nếu các file trống hoặc không tồn tại:
   - Tiếp tục flow bình thường (hỏi user).

1. **If no clear input provided, ask what they want to build**

   Use the **AskUserQuestion tool** (open-ended, no preset options) to ask:
   > "What change do you want to work on? Describe what you want to build or fix."

   From their description, derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`).

   **IMPORTANT**: Do NOT proceed without understanding what the user wants to build.

2. **Create the change directory**
   ```bash
   openspec new change "<name>"
   ```
   This creates a scaffolded change at `openspec/changes/<name>/` with `.openspec.yaml`.

3. **Get the artifact build order**
   ```bash
   openspec status --change "<name>" --json
   ```
   Parse the JSON to get:
   - `applyRequires`: array of artifact IDs needed before implementation (e.g., `["tasks"]`)
   - `artifacts`: list of all artifacts with their status and dependencies

4. **Create artifacts in sequence until apply-ready**

   Use the **TodoWrite tool** to track progress through the artifacts.

   Loop through artifacts in dependency order (artifacts with no pending dependencies first):

   a. **For each artifact that is `ready` (dependencies satisfied)**:
      - Get instructions:
        ```bash
        openspec instructions <artifact-id> --change "<name>" --json
        ```
      - The instructions JSON includes:
        - `context`: Project background (constraints for you - do NOT include in output)
        - `rules`: Artifact-specific rules (constraints for you - do NOT include in output)
        - `template`: The structure to use for your output file
        - `instruction`: Schema-specific guidance for this artifact type
        - `outputPath`: Where to write the artifact
        - `dependencies`: Completed artifacts to read for context
      - Read any completed dependency files for context
      - Create the artifact file using `template` as the structure
      - Apply `context` and `rules` as constraints - but do NOT copy them into the file
      - Show brief progress: "Created <artifact-id>"

   b. **Continue until all `applyRequires` artifacts are complete**
      - After creating each artifact, re-run `openspec status --change "<name>" --json`
      - Check if every artifact ID in `applyRequires` has `status: "done"` in the artifacts array
      - Stop when all `applyRequires` artifacts are done

   c. **If an artifact requires user input** (unclear context):
      - Use **AskUserQuestion tool** to clarify
      - Then continue with creation

5. **Show final status**
   ```bash
   openspec status --change "<name>"
   ```

## Đầu ra

After completing all artifacts, summarize:
- Change name and location
- List of artifacts created with brief descriptions
- What's ready: "All artifacts created! Ready for implementation."
- Prompt: "Run `/opsx:apply` or ask me to implement to start working on the tasks."

**Artifact Creation Guidelines**

- Follow the `instruction` field from `openspec instructions` for each artifact type
- The schema defines what each artifact should contain - follow it
- Read dependency artifacts for context before creating new ones
- Use `template` as the structure for your output file - fill in its sections
- **IMPORTANT**: `context` and `rules` are constraints for YOU, not content for the file
  - Do NOT copy `<context>`, `<rules>`, `<project_context>` blocks into the artifact
  - These guide what you write, but should never appear in the output

**Guardrails**
- Create ALL artifacts needed for implementation (as defined by schema's `apply.requires`)
- Always read dependency artifacts before creating a new one
- If context is critically unclear, ask the user - but prefer making reasonable decisions to keep momentum
- If a change with that name already exists, ask if user wants to continue it or create a new one
- Verify each artifact file exists after writing before proceeding to next
