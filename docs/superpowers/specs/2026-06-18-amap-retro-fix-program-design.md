# AMAP Retrospective-Fix Program — Design Overview

> Ngày: 2026-06-18
> Trạng thái: APPROVED (brainstorm) — chờ user review file
> Nguồn: phân tích một lần chạy AMAP thật trên codebase ngân hàng (TASK-1 Lock + TASK-2 Unlock/Cancel), 3 phiên, 1305 steps, 10 subagents, 22 corrections.
> Báo cáo gốc: `report/correction_analysis_refined.md`, `report/knowledge_layer_assessment.md`, `report/task_timeline.md`.

Đây là doc **program-overview**: ghi lại chẩn đoán, các nguyên tắc thiết kế, và phân rã thành 5 sub-spec. Mỗi sub-spec có doc design + plan riêng. Bắt đầu bằng sub-spec #1.

---

## 1. Chẩn đoán

> **Code-understanding ổn. Process + Knowledge bị bỏ qua.**
> Gốc rễ: framework đồ sộ nhưng **không fire** — luật/skill/workflow tồn tại dưới dạng *prose mà agent luôn skip*.

Bằng chứng định lượng từ báo cáo:

- **50% corrections (11/22)** xảy ra khi *luật đã có sẵn* vẫn bị vi phạm → vấn đề không phải thiếu luật, mà là luật không vào working-context tại điểm ra quyết định.
- Memory layer: **66 writes / 49 reads**, chỉ **8% reads (4/49)** thực sự guide hành vi trước khi code; còn lại là bootstrap-đọc-rồi-quên hoặc đối chiếu retroactive.
- SubAgent: **10 subagent / 485 steps / 0 knowledge reads** → SP-6 (rule approved) bị vi phạm lặp lại.
- C-22: agent **chủ động bỏ Pha Spec** (OpenSpec) với lý do "tiết kiệm token" → 9 correction cascade mà spec-review đã bắt hết.

Hai loại failure:

| Loại | Mô tả | Sửa ở đâu |
|------|-------|-----------|
| **Infra** | `antigravity-cli` không nạp `mcp_config.json` → UA/SocratiCode = 0 call → brute-force grep 456 lần | Phần *framework* (verify/degrade) ở sub-spec #1 Gate #4; phần *setup* (`amap doctor`) là item kế cận, ngoài chương trình này |
| **Behavioral** | Memory dead-storage, subagent không inherit, agent bypass flow | Toàn bộ chương trình |

## 2. Bốn nguyên tắc thiết kế (tenets)

1. **Decision-point gate** — luật fire *tại điểm ra quyết định*, không phải nhắc một lần ở bootstrap.
2. **Gate-by-evidence, không gate-by-instruction** — không bảo agent "gọi tool X / prefer Y / dùng skill Z" (class lỗi skip); thay vào đó **đòi một artifact mà chỉ hành động đúng mới sinh ra được** (node_id, blast-radius, probe-numbers, checkpoint). Precondition kiểm *nội dung artifact*, không phụ thuộc thiện chí agent.
3. **JIT + bootstrap diet** — bootstrap chỉ nạp *index nhỏ*; body knowledge kéo *đúng slice, đúng lúc*. Nhân bản pattern `skill-index.yaml` (đã có, đã tự gọi là "Bookkeeping Diet") cho knowledge layer.
4. **Net-negative complexity** — mỗi gate thêm vào phải **xoá nhiều prose hơn nó thêm**. Đo bằng số khối CRITICAL-prose-rule + tổng dòng rule/workflow + số skill/workflow: tất cả phải **giảm**.

## 3. Phân rã chương trình (5 sub-spec)

| # | Sub-spec | Cơ chế sửa | Cluster / correction | Đơn giản hoá kèm theo |
|---|----------|-----------|----------------------|------------------------|
| **1** | **Decision-point gates (spine)** — bootstrap diet + knowledge-index + 4 gate (knowledge-before-code, subagent injection, phase-non-bypass, MCP-probe) | B (precondition artifact) + chọn lọc C (probe, build) | Cluster A, C-22 (S-1), MCP false-ready, C-04/C-11 một phần | Collapse ~9 khối prose (R-Guard-2, R-Flow-1/2/3, R-Tool-4/5/5b, R-Adapter-2, R-Tool-8) |
| **2** | **Mechanical style enforcement** — encode SP/HP/CP `mechanically_checkable`, chạy `rule-projector` → checkstyle/linter, cắm vào verify gate | C (đã có `tools/rule-projector`) | Cluster D: C-10 (SP-6), C-20 (FQN/spacing), C-21 (super), C-09 | Bỏ SP-format prose khỏi luật, đẩy sang linter |
| **3** | **Verification & bookkeeping gate** — chặn "Done" tới khi build pass + AGENT_TRANSPARENCY/TOKEN_LOG ghi + POST-PHASE SELF-CHECK | B + build thật | Cluster E: C-06/07/08/12 | Gom các nhắc-verify rải rác → 1 gate |
| **4** | **Knowledge capture correctness** — enforce R-DNA-7 teaching-moment capture *trong phiên* + phân loại DNA/conventions/snapshot | B (capture gate) | C-13/C-17 (lặp vì chưa encode), C-18 (sai store), L-1..L-5 | Gom R-DNA-7 + classifier thành 1 luồng |
| **5** | **Model-driven consolidation** — normalize TẤT CẢ skill/workflow về gate model (`pre_conditions`/`outputs` load-bearing) + audit merge/xoá cái không fire | Refactor, đo net-negative | Toàn cục (P-6, độ phức tạp) | Đây *là* "refactor toàn bộ" — dẫn dắt bởi model của #1 |

## 4. Baseline phức tạp (để đo net-negative)

Đo tại HEAD hiện tại (`.amap/`):

- **6 rule files** ≈ 689 dòng (`rules-exec` 129, `rules-flow` 95, `rules-guard` 111, `rules-knowledge` 137, `RULES` 53, `rules-tool` 164).
- **14 skills**, **13 workflows** (riêng `task.md` 453 dòng).
- `procedures/`: `bootstrap.md` 197, `context-loader.md` 385.
- `meta-prompt.md` 373.

**Success criterion toàn chương trình:** số khối `[CRITICAL]` prose-rule và tổng dòng rule + số skill/workflow phải **giảm** so với baseline này, trong khi mọi gate fire-được (test ở từng sub-spec).

## 5. Thứ tự thực thi

```
#1 (spine, định nghĩa gate model)
   ├─ #2 (mechanical style)   ┐ có thể song song sau #1
   ├─ #3 (verify/bookkeeping) ┘
   ├─ #4 (capture correctness)
   └─ #5 (consolidation) — cần model của #1 đã tồn tại để normalize toàn bộ về đó
```

`#1` trước tiên: đòn bẩy cao nhất, định nghĩa gate model + knowledge-index mà mọi sub-spec sau dùng lại. `#5` cuối cùng vì không thể normalize-to-model trước khi model tồn tại.

## 6. Ranh giới / Non-goals

- **Không** đập-đi-xây-lại (greenfield) skill/workflow — refactor phải traceable về finding/tenet và giữ golden-snapshot (`amap init` per-platform, từ Batch 1/UP3) xanh.
- **Không** sửa infra `mcp_config.json` của runtime trong chương trình này (đó là `amap doctor`/install-time, item kế cận).
- **Không** thêm runtime-hook chặn-Write (selective-C đầy đủ) cho phase-gate — đánh đổi portability; ghi là "future optional hook".
- Sub-spec #1 **không** ôm formatting (#2), build-verify (#3), capture (#4), hay full-consolidation (#5).

## 7. Liên kết

- Sub-spec #1 design: `docs/superpowers/specs/2026-06-18-decision-point-gates-design.md`
- Báo cáo nguồn: `report/`
