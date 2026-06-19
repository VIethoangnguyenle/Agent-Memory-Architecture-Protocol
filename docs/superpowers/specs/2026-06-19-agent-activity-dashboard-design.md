# Agent Activity Dashboard — Design

> Ngày: 2026-06-19
> Trạng thái: design đã chốt, scope rút về vertical slice P0–P2 (sau gstack `/plan-eng-review`)
> Eng-review verdict: CLEARED (SCOPE_REDUCED) — 3 issues, 0 critical gap

---

## 1. Vấn đề

Khi một platform (đặc biệt **Antigravity**) đẻ subagent, subagent chạy ngầm và người
dùng **không thấy** nó đã chạy được bao nhiêu, đang ở pha nào, hay đang gọi tool gì.
Codex/Claude CLI cũng thiếu một góc nhìn thống nhất. Cần một lớp **observability** đọc
trạng thái run và hiển thị tiến độ — đích đến là một **web dashboard realtime**, quan sát
**nhiều project/run song song**.

## 2. Insight nền tảng

Dữ liệu tiến độ **đã được agent ghi ra file** theo một *neutral filesystem contract* — nên
một lớp **đọc + tổng hợp + hiển thị** giải quyết được vấn đề, đồng nhất cho mọi platform
(Antigravity / Claude / Codex đều ghi cùng bộ file):

| Nguồn | File | Cho biết |
|-------|------|----------|
| Phase / ticket | `knowledge/active/AGENT_TRANSPARENCY.md` (YAML frontmatter) | `phase_state`, `ticket_id` |
| Tiến độ task | `knowledge/active/microloop/TASK_QUEUE.md` (**YAML**) | x/N task + status |
| Token | `knowledge/active/TOKEN_LOG.md` (markdown table) | token theo pha *(best-effort)* |
| Tool-call (P5+) | `~/.amap/runs/<slug>/ACTIVITY_LOG.jsonl` | timeline tool-call |

## 3. Kiến trúc (4 đơn vị tách bạch)

```
┌──────────────────────────── amap dashboard (1 process) ─────────────────────────┐
│  Registry ──► Reader ──► Server ──► Web UI                                        │
│  liệt kê run   parse →    push      progress bar + (P6) tool-call timeline        │
│                RunState                                                            │
└───────────────────────────────────────────────────────────────────────────────┘
        ▲ đọc (read-only, neutral)
        │
   project: {framework_root}/knowledge/active/   (contract files, in-project, đã gitignore, được archive)
   central: ~/.amap/runs/<slug>/                 (observability mới — KHÔNG vào cây project)
   central: ~/.amap/projects.yaml                (registry các project)
```

**Quyết định data-location (chốt):** contract files giữ nguyên in-project (đã gitignore
trong `.amap/knowledge/active/.gitignore`, là knowledge được archive). Dữ liệu observability
**mới** (`ACTIVITY_LOG.jsonl`, state dashboard) đưa ra `~/.amap/runs/<slug>/` để **footprint
trong project = 0**.

### `RunState` (Reader trả ra)
```
RunState:
  slug, project_path, ticket_id, phase_state, updated_at, stale: bool
  tasks: [{id, desc, status}]   →  tasks_done / tasks_total  →  progress %
  active_task
  tokens: {total_est, by_phase} | None        # nullable: parse markdown table dễ vỡ
  recent_activity: [{ts, tool, summary, status, duration}]   # P5+ từ ACTIVITY_LOG
```
Thuần logic, không biết HTTP, unit-test bằng fixtures.

## 4. Tái dùng (KHÔNG rebuild — từ eng-review)

| Nhu cầu | Code đã có | Hành động |
|---------|-----------|-----------|
| Parse TASK_QUEUE | `contract.load_queue` / `validate_queue` ([contract.py](../../../.amap/tools/microloop-orchestrator/contract.py)) | **reuse** (DRY) |
| Resolve project → root | `load_resolved_config` + `get_platform().framework_root` ([scaffold.py](../../../cli/scaffold.py)) | **reuse** |
| Pattern lệnh CLI | [status.py](../../../cli/commands/status.py) | mirror |
| Console script `amap` | đã khai báo trong `pyproject.toml` | P0 tận dụng |
| YAML | `pyyaml` (dep sẵn có) | frontmatter + registry, **không thêm dep** ở slice |
| Hook plumbing (P5) | [write_gate.py](../../../.amap/hooks/write-gate/write_gate.py) | template cho `activity_log.py` |

## 5. Scope — vertical slice trước (eng-review SCOPE_REDUCED)

Lý do rút scope: **toàn bộ dashboard dựa trên giả định "contract files cập nhật LIVE trong
lúc subagent chạy ngầm".** Nếu Antigravity chỉ flush ở cuối pha (hoặc LLM quên ghi), thì
realtime server + UI + hook trở nên vô dụng. → Verify giả định bằng chi phí nhỏ nhất trước.

### Sub-project 1 — Contract dashboard

| Phase | Nội dung | Done khi… |
|-------|----------|-----------|
| **P0** | `amap` thành lệnh terminal: mở rộng `install.sh` chạy `pip install -e .` vào `.venv` + symlink `amap` → `~/.local/bin` | `amap --version` chạy trong shell mới |
| **P1** | Registry: `~/.amap/projects.yaml` + `register`/`unregister`/`list` + auto-add cwd + dedup | register `.` → `list` thấy nó (test tmp) |
| **P2** | Reader (contract-only): reuse `contract.load_queue` + `load_resolved_config` → `RunState`, token nullable, xử lý file thiếu/hỏng không crash | unit test parse fixture ra RunState đúng |
| **P2.5** | **Validation gate**: chạy 1 run Antigravity thật, xác nhận contract files cập nhật live (mtime đổi mid-run) | quan sát được file đổi trong lúc subagent chạy |

→ Sau P2.5: nếu giả định đúng → tiếp Sub-project 1 phần server; nếu sai → rethink phần realtime.

| Phase | Nội dung | Done khi… |
|-------|----------|-----------|
| **P3** | Server + UI: serve `index.html` + kênh push, push 1 lần khi connect; card progress/phase/task/token | mở browser thấy state thật |
| **P4** | Realtime: file-watcher (poll mtime ~300ms) → push khi đổi | sửa TASK_QUEUE → UI đổi <1s, không refresh tay |

### Sub-project 2 — Activity capture (tool-call level)

| Phase | Nội dung | Done khi… |
|-------|----------|-----------|
| **P5** | `activity_log.py` hook (mẫu `write_gate.py`) + wire **Claude Code trước** → ghi `~/.amap/runs/<slug>/ACTIVITY_LOG.jsonl`; Reader thêm `recent_activity` | chạy 1 action → thấy dòng tool-call trong log |
| **P6** | Timeline tool-call realtime trong UI + mở rộng hook sang Antigravity/Codex; verify caveat per-platform | timeline tool-call chảy realtime trên browser |

Activity depth (đã chốt): **timeline tên tool + tóm tắt tham số** (vd path cho read/write,
câu lệnh cho bash) — không mirror toàn bộ I/O.

## 6. Quyết định đang treo (parked)

- **Transport SSE vs WebSocket** (quyết ở đầu P3): luồng dữ liệu thuần server→browser một
  chiều, đúng với **SSE** (zero dep, stdlib `http.server`, auto-reconnect). User muốn "socket";
  nếu nghĩa là "realtime push, không polling" thì SSE đủ. WebSocket (dep `websockets`) chỉ
  cần nếu sau này UI phải gửi lệnh ngược về server. **Xác nhận lại khi tới P3.**

## 7. Caveat phải verify thực tế (Sub-project 2)

- Matcher bắt-tất-cả-tool trên Antigravity/Codex (write-gate chỉ match tool ghi).
- Có `PostToolUse` không (cần cho duration/result).
- Subagent chạy ngầm (tier fresh-session) có kích hoạt cùng hook không.

## 8. Test plan (slice P0–P2, mục tiêu 100% — 11 path)

```
[+] cli/dashboard/registry.py
  register(): add | dedup | auto-add cwd        unregister(): remove + remove-missing
  list(): empty → [] (no crash)
[+] cli/dashboard/reader.py
  read_run(): all-present → full | TASK_QUEUE missing → tasks=None
            | AGENT_TRANSPARENCY missing → phase=None | TOKEN_LOG unparseable → tokens=None
            | no active run → idle | malformed YAML → catch + stale flag (KHÔNG crash)
  progress_pct(): 0 tasks → 0% (guard div-by-zero)
```
Tất cả thuần logic → unit test với fixtures, theo pattern `test_snapshots.py` / `test_status.py`.
Hai path dễ quên: **div-by-zero (0 task)** và **malformed YAML** (nếu không catch → CLI crash).

## 9. NOT in scope (deferred)

- Server + web UI (P3–P4) — gated sau validation gate P2.5.
- Activity hook + `ACTIVITY_LOG.jsonl` + timeline (P5–P6) — sub-project riêng, cần verify per-platform.
- Live multi-project watching — registry lưu multi, watching là P4.
- Token table parsing — nullable, không build parser markdown ở slice.
- Publish PyPI / pipx — chỉ symlink local qua install.sh.

## 10. Failure modes (slice)

| Codepath | Cách hỏng | Test? | Error handling | User thấy |
|----------|-----------|-------|----------------|-----------|
| Reader / active dir thiếu | partial/empty | ✅ | trả idle/null | "no active run" |
| TASK_QUEUE hỏng | `validate_queue` raise | ✅ | **phải catch** → stale | run đánh dấu stale (nếu không catch → crash) |
| progress_pct 0 task | div-by-zero | ✅ | guard | 0% |

Không có silent-failure critical gap **với điều kiện** catch-and-null được implement + test.
