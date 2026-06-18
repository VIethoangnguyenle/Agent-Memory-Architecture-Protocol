# decision-gate.md — Quy trình gate dùng chung (4 điểm cắm)

> Mọi gate cùng một hình dạng. Gate kiểm BẰNG CHỨNG trong artifact, không kiểm "đã gọi tool chưa".

## Hình dạng chung
1. Tại điểm quyết định → tra `knowledge/long-term/knowledge-index.yaml` (đã nạp ở bootstrap).
2. Kéo SLICE just-in-time: entry có `applies_to` khớp artifact-type hiện tại.
3. Ghi CHECKPOINT artifact (theo template) chứa bằng chứng bắt buộc.
4. Precondition kiểm checkpoint bằng `gate-check`:
   `python3 {{ platform.framework_root }}/tools/gate-check/cli.py <gate> <file>`
   exit≠0 → on_fail (ABORT/degrade).

## Bốn điểm cắm
| Gate | file kiểm | validator |
|------|-----------|-----------|
| knowledge-before-code | `knowledge/active/KNOWLEDGE_CHECKPOINT.md` | `knowledge-checkpoint` |
| subagent injection | `knowledge/active/TASK_HANDOFF.<node>.md` | `handoff-slice` |
| phase-non-bypass | `knowledge/active/AGENT_TRANSPARENCY.md` | `phase-chain` |
| MCP-probe | dòng MCP-status (bootstrap report / transparency) | `mcp-status` |
