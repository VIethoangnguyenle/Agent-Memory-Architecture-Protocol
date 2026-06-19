# Agent Memory — MCP Capability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `agent-memory` an optional, init-selectable MCP capability with clean runtime degrade, and sharpen its documented role as a long-term experiential reference layer.

**Architecture:** Add `agent-memory` to `mcp_capabilities` in the plugin manifest (selection-only — no `requires_capability` gate, since `knowledge-curator` has non-memory duties and stays shipped unconditionally). Absence is handled at runtime via `resolved-config.yaml → mcps`, mirroring the existing KG degrade model. The `gate-check` mcp-status validator is generalized to recognize agent-memory probe/degrade evidence. Doc edits clarify wording.

**Tech Stack:** Python 3.12, pytest, Jinja2, YAML manifest, Markdown rules/procedures.

**Test runner:** `/usr/bin/python3 -m pytest` (the repo venv has no pytest).

---

### Task 1: Register `agent-memory` capability in the manifest

**Files:**
- Modify: `cli/plugin-manifest.yaml` (the `mcp_capabilities` block, ends at the `understand-anything` entry)
- Test: `cli/tests/test_scaffold.py`

- [ ] **Step 1: Write the failing test**

Add to `cli/tests/test_scaffold.py`:

```python
def test_manifest_declares_agent_memory_capability(amap_root):
    manifest = load_manifest(amap_root)
    caps = manifest["mcp_capabilities"]
    assert "agent-memory" in caps
    assert caps["agent-memory"]["provides"] == "memory"


def test_has_capability_recognizes_memory(amap_root):
    manifest = load_manifest(amap_root)
    caps = manifest["mcp_capabilities"]
    assert has_capability(["agent-memory"], caps, "memory") is True
    assert has_capability([], caps, "memory") is False
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `/usr/bin/python3 -m pytest cli/tests/test_scaffold.py::test_manifest_declares_agent_memory_capability cli/tests/test_scaffold.py::test_has_capability_recognizes_memory -v`
Expected: FAIL — `KeyError: 'agent-memory'` / assertion error (capability not present).

- [ ] **Step 3: Add the capability to the manifest**

In `cli/plugin-manifest.yaml`, inside `mcp_capabilities:`, append after the `understand-anything` entry (keep it LAST so existing `1,2,3` index-based selections in tests/snapshots are unaffected):

```yaml
  agent-memory:
    provides: memory
    display: "Agent Memory — Kinh nghiệm dài hạn (Qdrant, tham khảo sau task)"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `/usr/bin/python3 -m pytest cli/tests/test_scaffold.py::test_manifest_declares_agent_memory_capability cli/tests/test_scaffold.py::test_has_capability_recognizes_memory -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cli/plugin-manifest.yaml cli/tests/test_scaffold.py
git commit -m "feat: register agent-memory as a selectable MCP capability"
```

---

### Task 2: Verify init can select agent-memory and record it in resolved-config

No production code change is expected here — `resolve_init_choices`, `_validate_selected_mcps`, and `generate_resolved_config` already operate generically over `mcp_capabilities`. This task adds regression tests proving agent-memory flows end-to-end.

**Files:**
- Test: `cli/tests/test_init.py`

- [ ] **Step 1: Write the failing test**

Add to `cli/tests/test_init.py`:

```python
def test_resolve_init_choices_accepts_agent_memory(amap_root):
    manifest = load_manifest(amap_root)

    platform_key, selected_mcps, language = resolve_init_choices(
        manifest,
        platform_key="generic",
        selected_mcps=["agent-memory"],
        language="python",
        assume_yes=True,
    )

    assert selected_mcps == ["agent-memory"]


def test_run_init_records_agent_memory_in_resolved_config(tmp_path, amap_root):
    from cli.scaffold import load_resolved_config

    target = tmp_path / "proj"
    run_init(
        target_dir=str(target),
        amap_root=str(amap_root),
        platform_key="generic",
        selected_mcps=["agent-memory"],
        language="other",
        assume_yes=True,
    )

    resolved = load_resolved_config(target)
    assert "agent-memory" in resolved["mcps"]
```

- [ ] **Step 2: Run the tests**

Run: `/usr/bin/python3 -m pytest cli/tests/test_init.py::test_resolve_init_choices_accepts_agent_memory cli/tests/test_init.py::test_run_init_records_agent_memory_in_resolved_config -v`
Expected: PASS immediately (Task 1 already added the capability; the init plumbing is generic). If `test_resolve_init_choices_accepts_agent_memory` fails with "Unknown MCP server(s)", confirm Task 1's manifest edit is present.

- [ ] **Step 3: Commit**

```bash
git add cli/tests/test_init.py
git commit -m "test: cover agent-memory init selection and resolved-config recording"
```

---

### Task 3: Teach the mcp-status gate to accept agent-memory evidence

`validate_mcp_status` currently accepts only KG probe numbers (`nodes=`/`edges=`) or the KG degrade line. A project that selects ONLY agent-memory would emit neither, so the gate would wrongly fail. Add memory probe + memory degrade patterns.

**Files:**
- Modify: `.amap/tools/gate-check/gates.py:22-23` (regex block) and `.amap/tools/gate-check/gates.py:49-52` (`validate_mcp_status`)
- Test: `.amap/tools/gate-check/tests/test_gates.py`

- [ ] **Step 1: Write the failing test**

Add to `.amap/tools/gate-check/tests/test_gates.py`:

```python
def test_mcp_status_accepts_agent_memory_probe_and_degrade():
    assert g.validate_mcp_status("agent-memory: healthy").ok is True
    assert g.validate_mcp_status(
        "agent-memory unavailable — skip recall/save"
    ).ok is True
    # A bare label with no health word or degrade is still invalid.
    assert g.validate_mcp_status("agent-memory").ok is False
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py::test_mcp_status_accepts_agent_memory_probe_and_degrade -v`
Expected: FAIL — the first two assertions return `ok is False` (no nodes/edges, no KG-degrade match).

- [ ] **Step 3: Add the memory patterns**

In `.amap/tools/gate-check/gates.py`, after the `_NUMBERS` definition (line 23), add:

```python
# Agent-memory MCP evidence: either a health probe ("agent-memory: healthy")
# or the compact degrade line ("agent-memory unavailable — skip recall/save").
_MEMORY_OK = re.compile(r"agent-memory.{0,20}(healthy|ok|ready)", re.IGNORECASE)
_MEMORY_DEGRADE = re.compile(
    r"agent-memory unavailable.{0,40}(skip|recall|save)", re.IGNORECASE
)
```

Then change `validate_mcp_status` (lines 49-52) to:

```python
def validate_mcp_status(text: str) -> Result:
    if (
        _NUMBERS.search(text)
        or _DEGRADE.search(text)
        or _MEMORY_OK.search(text)
        or _MEMORY_DEGRADE.search(text)
    ):
        return Result(True)
    return Result(False, "MCP status lacks probe numbers and degrade line ('Runtime Ready' alone is invalid)")
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `/usr/bin/python3 -m pytest .amap/tools/gate-check/tests/test_gates.py -v`
Expected: PASS (new test + all existing mcp_status tests stay green).

- [ ] **Step 5: Commit**

```bash
git add .amap/tools/gate-check/gates.py .amap/tools/gate-check/tests/test_gates.py
git commit -m "feat: accept agent-memory probe/degrade in mcp-status gate"
```

---

### Task 4: Sharpen R-Tool-6 role wording

**Files:**
- Modify: `.amap/rules/rules-tool.md:44-50`

- [ ] **Step 1: Replace the opening definition**

In `.amap/rules/rules-tool.md`, replace lines 46-48:

```
Các tool MCP `agent-memory` chỉ là **lớp truy xuất phụ**.
Chúng bổ sung — không bao giờ thay thế — Bootstrap Protocol, thứ tự ưu tiên context-loader P1→P4,
hay `knowledge-snapshot.md` với tư cách nguồn sự thật chính thức.
```

with:

```
`agent-memory` là **lớp kinh nghiệm dài hạn** — những gì agent đã đúc kết và lưu lên
Qdrant *sau* các task trước. Dữ liệu mang tính **tham khảo/advisory** ("trước đây TỪNG
làm thế nào"), **không phải kiến thức chính** về hệ thống hiện tại.
Nó bổ sung — không bao giờ thay thế — Bootstrap Protocol, thứ tự ưu tiên context-loader
P1→P4, hay `knowledge-snapshot.md` với tư cách nguồn sự thật chính thức.
Khi mâu thuẫn với kiến thức chính (`knowledge-snapshot.md`, db-explorer, KG),
**kiến thức chính thắng tuyệt đối**.
```

- [ ] **Step 2: Verify the edit**

Run: `/usr/bin/grep -n "lớp kinh nghiệm dài hạn" .amap/rules/rules-tool.md`
Expected: one match in the R-Tool-6 section. The phrase "lớp truy xuất phụ" should no longer be the opening sentence (confirm with `/usr/bin/grep -c "lớp truy xuất phụ" .amap/rules/rules-tool.md` → expect 0, unless it appears elsewhere intentionally).

- [ ] **Step 3: Commit**

```bash
git add .amap/rules/rules-tool.md
git commit -m "docs: clarify agent-memory as long-term experiential reference layer"
```

---

### Task 5: Add runtime degrade branch to R-Tool-6

**Files:**
- Modify: `.amap/rules/rules-tool.md` (the "Xử lý xung đột" / write-path guard area, around lines 72-89)

- [ ] **Step 1: Insert the degrade clause**

In `.amap/rules/rules-tool.md`, immediately before the `#### Bảo vệ đường ghi (Write-path guard)` heading, insert:

```markdown
#### Degrade khi agent-memory không cấu hình

Nếu `resolved-config.yaml → mcps` KHÔNG chứa `agent-memory`:
- Mọi `memory_smart_search` / `memory_recall` bị **bỏ qua** — KHÔNG gọi, KHÔNG bịa kết quả.
- Ghi vào `AGENT_TRANSPARENCY.md`: `agent-memory unavailable — skip recall/save`.
- M7 post-task push (xem `knowledge-curator`) tự bỏ qua ở Tầng 0 (pre-check).

Đây là degrade-không-bịa, đồng dạng mô hình KG (`KG unavailable — grep fallback, MEDIUM`).
```

- [ ] **Step 2: Verify the edit**

Run: `/usr/bin/grep -n "Degrade khi agent-memory" .amap/rules/rules-tool.md`
Expected: one match, positioned before "Bảo vệ đường ghi".

- [ ] **Step 3: Commit**

```bash
git add .amap/rules/rules-tool.md
git commit -m "docs: add agent-memory runtime degrade branch to R-Tool-6"
```

---

### Task 6: Extend the bootstrap MCP probe to cover agent-memory

**Files:**
- Modify: `.amap/procedures/bootstrap.md:166-172` (the "MCP probe bắt buộc" note)

- [ ] **Step 1: Add the agent-memory probe instruction**

In `.amap/procedures/bootstrap.md`, inside the `> **MCP probe bắt buộc:**` block, after the KG sentence and before the closing `Không có MCP nào trong config → ...` sentence, add:

```
>   Nếu `resolved-config.yaml` khai báo `agent-memory` → probe `memory_health` và ghi
>   `🔌 MCP: agent-memory: healthy` (hoặc trạng thái thật). Probe fail/absent → ghi dòng
>   degrade `agent-memory unavailable — skip recall/save`.
```

- [ ] **Step 2: Verify the edit**

Run: `/usr/bin/grep -n "memory_health" .amap/procedures/bootstrap.md`
Expected: one match in the MCP probe note.

- [ ] **Step 3: Commit**

```bash
git add .amap/procedures/bootstrap.md
git commit -m "docs: probe agent-memory health in bootstrap MCP report"
```

---

### Task 7: Add Tầng 0 (pre-check) to the M7 memory-push reference

**Files:**
- Modify: `.amap/skills/knowledge-curator/references/m7-memory-push.md:10-13` (just before "### Tầng 1 — Gate")

- [ ] **Step 1: Insert the pre-check tier**

In `.amap/skills/knowledge-curator/references/m7-memory-push.md`, after the line `Trước khi gọi \`memory_save\`, curator PHẢI đi qua 3 tầng:` and before `### Tầng 1 — Gate (CÓ nên lưu không?)`, insert:

```markdown
### Tầng 0 — Pre-check (agent-memory có cấu hình không?)

Đọc `resolved-config.yaml → mcps`. Nếu KHÔNG chứa `agent-memory`:
→ Bỏ qua toàn bộ memory push, ghi vào AGENT_TRANSPARENCY: `[M7-SKIP] agent-memory chưa cấu hình`.
→ KHÔNG gọi `memory_smart_search` hay `memory_save`.

Nếu có `agent-memory` → tiếp sang Tầng 1.
```

- [ ] **Step 2: Verify the edit**

Run: `/usr/bin/grep -n "Tầng 0" .amap/skills/knowledge-curator/references/m7-memory-push.md`
Expected: one match, before "Tầng 1 — Gate".

- [ ] **Step 3: Commit**

```bash
git add .amap/skills/knowledge-curator/references/m7-memory-push.md
git commit -m "docs: gate M7 memory push on agent-memory being configured"
```

---

### Task 8: Note memory-budget applies only when agent-memory is available

**Files:**
- Modify: `.amap/rules/rules-exec.md:75`

- [ ] **Step 1: Add the conditional note**

In `.amap/rules/rules-exec.md`, change line 75 from:

```
- **Memory budget** — áp dụng cho `memory_smart_search` + `memory_recall`:
```

to:

```
- **Memory budget** — áp dụng cho `memory_smart_search` + `memory_recall` (chỉ khi `agent-memory` có trong `resolved-config.yaml → mcps`; nếu không, mọi memory call bị skip theo R-Tool-6):
```

- [ ] **Step 2: Verify the edit**

Run: `/usr/bin/grep -n "chỉ khi .agent-memory" .amap/rules/rules-exec.md`
Expected: one match on the memory-budget line.

- [ ] **Step 3: Commit**

```bash
git add .amap/rules/rules-exec.md
git commit -m "docs: scope memory budget to configured agent-memory"
```

---

### Task 9: Full verification

- [ ] **Step 1: Run the entire test suite**

Run: `/usr/bin/python3 -m pytest cli/tests .amap/tools/gate-check/tests -q`
Expected: all PASS, including the snapshot tests (no file-tree changes, since the capability is selection-only).

- [ ] **Step 2: Confirm a clean generic init still works**

Run: `/usr/bin/python3 -m pytest cli/tests/test_snapshots.py -q`
Expected: PASS — snapshots unchanged.

- [ ] **Step 3: Final review commit (if any test fixtures changed)**

```bash
git add -A
git commit -m "test: verify agent-memory capability end-to-end" || echo "nothing to commit"
```

---

## Self-Review

**Spec coverage:**
- Spec Phần 1 (wording) → Task 4.
- Spec Phần 2 (capability model / init-selectable) → Tasks 1, 2.
- Spec Phần 3 (runtime degrade: bootstrap, R-Tool-6, M7, rules-exec, gate-check) → Tasks 3, 5, 6, 7, 8.
- Spec Phần 4 (testing) → Tasks 1-3 tests + Task 9. Spec's "update snapshots if changed" resolves to "no change needed" because the capability is selection-only (no plugin gated by it), confirmed in Task 9 Step 2.

**Placeholder scan:** No TBD/TODO; every code/doc step shows exact content and exact verify commands.

**Type/name consistency:** Capability slug `memory` and MCP key `agent-memory` used consistently across manifest (Task 1), gate regex `_MEMORY_OK`/`_MEMORY_DEGRADE` (Task 3), and degrade string `agent-memory unavailable — skip recall/save` used identically in Tasks 3, 5, 6. The healthy line `agent-memory: healthy` matches the `_MEMORY_OK` pattern in Task 3.
