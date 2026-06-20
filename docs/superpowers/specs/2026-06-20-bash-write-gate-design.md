# Bash-Write Gate — Design

> **Date:** 2026-06-20
> **Status:** Approved (design) — ready for implementation plan
> **Lineage:** follow-up to `2026-06-19-decision-gates-followups-design.md` P0 / Residual **C-22**.
> C-22 shipped the runtime write-gate nhưng chỉ phủ `Edit/Write/MultiEdit`. Spec này
> đóng residual **C-22b**: ghi code qua công cụ `Bash`/shell hiện né hoàn toàn gate.

---

## 1. Bối cảnh & vấn đề

Runtime write-gate (`.amap/hooks/write-gate/write_gate.py`) là cơ chế **duy nhất** thực
sự enforce R-Guard-2 (knowledge-before-code) ở mức cơ học. Nó là một PreToolUse hook.

Lỗ hổng: matcher chỉ bắt các công cụ edit của runtime —
`Edit|Write|MultiEdit` (Claude, `.amap/hooks/claude-code/settings.json`),
`apply_patch|Edit|Write` (Codex),
`write_to_file|replace_file_content|multi_replace_file_content` (Antigravity).

Mọi thao tác ghi code qua công cụ **`Bash`/shell** (`tee`, `> file`, `sed -i`, `cp/mv`,
`dd`, `patch`, `git apply`, `prettier --write`, heredoc…) **không kích hoạt hook** →
agent có thể ghi code mà không có `KNOWLEDGE_CHECKPOINT.md` hợp lệ. Chính
`rules-flow.md` (R-Flow-2) đã thừa nhận: *"Residual đã biết: write thô ngoài mọi /task
skill chưa chặn được (cần runtime Write-hook sau)."*

`write_gate.py` đã có sẵn mầm xử lý command (regex patch `*** Add/Update/Delete File:`
trong `_paths_from_patch_command`) nhưng vô hiệu vì `Bash` không nằm trong bất kỳ matcher
nào.

## 2. Threat model & hướng tiếp cận (đã chốt)

- **Threat model:** bypass **vô ý** của agent hợp tác (Claude/Codex/Antigravity) — chúng
  *tình cờ* dùng shell để ghi, không phải kẻ địch cố tình lẩn tránh.
- **Hệ quả:** không cần (và không thể) airtight. Shell là Turing-complete → không một
  parser string nào bắt được 100% đường ghi (`eval`, biến động, script con).
- **Hướng đã chọn:** **Heuristic pre-parse** — mở rộng `write_gate` để nhận diện các
  *idiom ghi phổ biến*, đủ phủ ~95% trường hợp lỡ tay. Hai hướng còn lại (post-hoc git
  revert; hybrid) bị loại cho phạm vi này vì chi phí/UX không tương xứng với threat model.

## 3. Quyết định thiết kế (locked)

| ID | Quyết định | Lý do |
|----|-----------|-------|
| **D1** | Path code phát hiện từ shell dùng **đúng** logic `evaluate_write` như Edit/Write: block nếu thiếu `KNOWLEDGE_CHECKPOINT` hợp lệ. | Parity — một luật cho mọi đường ghi; tái dùng code, không nhân đôi. |
| **D2** | `Bash` không phát hiện đường ghi → **fail-open** (cho qua). Edit/Write không có path vẫn **fail-closed** (giữ nguyên). | Lệnh shell read/exec (`grep`, `ls`, `npm test`) chiếm đa số; chặn chúng sẽ phá UX. Cần `main()` *biết tool name*. |
| **D3** | Có verb ghi nhưng path **không resolve được** (`tee "$X"`, glob động) → **WARN-and-allow** (cho qua + ghi 1 dòng cảnh báo stderr). | Đúng tinh thần heuristic; không chặn mù gây false-positive. |
| **D4** | Formatter/codegen ghi source (`prettier --write`…) | Áp cùng luật D1: chỉ qua nếu có checkpoint hợp lệ (trong `/task apply` thì có). Tradeoff chấp nhận được. |
| **D5** | Chỉ gate path **không bị `git check-ignore`** (nhánh Bash). `coverage/`, `dist/`, `node_modules/`, `.pytest_cache/`… thường gitignored → cho qua. | Tránh false-block test/build artifacts mà **không** hard-code `src/` hay đuôi file (giữ tính generic của framework). Degrade khi không phải git repo: giữ hành vi cũ (non-framework = gate). |

**Phạm vi surgical:** D5 và logic fail-open (D2/D3) chỉ áp cho **nhánh Bash mới**.
`evaluate_write` và hành vi Edit/Write/MultiEdit **giữ nguyên** → toàn bộ test hiện có
xanh.

## 4. Cơ chế

### 4.1 Nhận diện đường ghi — `parse_shell_writes(command)`
Helper mới trả về danh sách path đích, theo tầng:

- **T1 — patch:** `*** Add|Update|Delete File: <path>` (đã có — `_paths_from_patch_command`, giữ nguyên).
- **T2 — redirection:** `> <path>`, `>> <path>`, heredoc `cmd > <path> <<EOF`. Bỏ qua
  `/dev/null`, `/dev/stdout`, `&1`, `&2`.
- **T3 — lệnh ghi có đích rõ:**
  - `tee [-a] <path>...`
  - `sed -i[suffix] ... <path>`
  - `cp <...> <dest>`, `mv <...> <dest>` (đích = arg cuối)
  - `dd of=<path>`
  - `git apply <...>`, `git checkout -- <path>`, `git restore <path>`
  - formatter ghi tại chỗ: `prettier --write <path>`, `gofmt -w <path>`, `ruff ... --fix <path>`, `black <path>`

Path động (chứa `$`, `` ` ``, `*`, `?`, `$(`) → đánh dấu *unresolved* → D3 (warn-allow).

### 4.2 Phân loại & định tuyến (trong `main()`, biết tool name)
```
targets = extract_target_paths(payload)          # gồm cả parse_shell_writes cho command
if tool là shell (Bash/shell/run_command):
    targets = [p for p in targets if not _git_ignored(project_root, p)]   # D5
    nếu targets rỗng → ALLOW (D2/D3)
else:                                              # Edit/Write/MultiEdit/apply_patch
    nếu targets rỗng → BLOCK "Unable to identify target path"  (giữ nguyên)
decision = first failing evaluate_write(target) else ALLOW   # D1
```
- `_git_ignored(root, path)`: chạy `git check-ignore -q <path>` tại `root`; True nếu
  ignored. Không phải git repo / git lỗi → coi như **không** ignored (degrade về hành vi
  cũ: vẫn gate non-framework).
- `extract_target_paths` mở rộng: nhánh command gọi `parse_shell_writes` (thay vì chỉ
  `_paths_from_patch_command`).

### 4.3 Tool-awareness
`main()` đọc tool name từ `payload["tool_name"]` hoặc `payload["toolCall"]["name"]` để
phân biệt shell vs edit-tool. Tập tên shell theo runtime (xác minh khi plan):
Claude `Bash`; Codex `shell`/`local_shell`; Antigravity `run_command`.

## 5. Phạm vi thay đổi (files)

- **`.amap/hooks/write-gate/write_gate.py`** — thêm `parse_shell_writes()`,
  `_git_ignored()`; `main()` tool-aware + lọc gitignore (D5) + fail-open shell (D2/D3);
  `extract_target_paths` gọi `parse_shell_writes`. `evaluate_write` **không đổi**.
- **`.amap/hooks/claude-code/settings.json`** — matcher `Edit|Write|MultiEdit` → `+Bash`.
- **`.amap/hooks/codex/hooks.json`** — thêm tool shell của Codex vào matcher.
- **`.amap/hooks/antigravity/hooks.json`** — thêm tool command của Antigravity vào matcher.
- **`.amap/hooks/write-gate/tests/test_write_gate.py`** — case cho từng idiom (§7).
- **(Kiểm khi plan)** `cli/tests/snapshots/*.txt` nếu nội dung settings/hooks nằm trong
  snapshot scaffold → refresh.

> Không đụng `cli/` capability/scaffold filtering — capability `write_gate_hook` đã có từ
> C-22; spec này chỉ mở rộng nội dung hook, không thêm platform mới.

## 6. Phi mục tiêu (YAGNI)

- Không bắt `eval`, lệnh dựng động, script con tự ghi (đó là hướng post-hoc git — bị loại).
- Không sandbox / không filesystem-level interception.
- Không đổi hành vi gate của Edit/Write/MultiEdit.
- Không thêm gitignore-awareness cho nhánh Edit/Write (giữ surgical).

## 7. Test plan / Acceptance criteria

**BLOCK (no checkpoint):**
- `tee src/App.java`, `echo x > src/App.java`, `sed -i 's/a/b/' src/App.java`,
  `cp /tmp/x src/App.java`, `dd of=src/App.java`.

**ALLOW:**
- Cùng các lệnh trên khi `KNOWLEDGE_CHECKPOINT.md` hợp lệ tồn tại (D1).
- Read/exec không ghi: `grep -r foo src`, `ls`, `npm test`, `python -m pytest` (D2 fail-open).
- Ghi framework artifact: `tee .amap/knowledge/...`, `> openspec/changes/x/spec.md` (exempt).
- Ghi path gitignored: `> coverage/lcov.info`, `> dist/bundle.js` (D5).

**WARN-and-allow:**
- `tee "$DYN"`, `sed -i ... $FILE` (D3 — path unresolved).

**Regression:** toàn bộ test Edit/Write/MultiEdit/apply_patch hiện có vẫn PASS.

**Exit condition:** một fixture chứng minh `tee <code-path>` **không** có
`KNOWLEDGE_CHECKPOINT` hợp lệ bị block ở mức runtime hook (exit 2 cho Claude;
`permissionDecision: deny` cho Codex; `decision: deny` cho Antigravity), trong khi
`grep`/ghi-gitignored được cho qua.

## 8. Residual đã biết (ghi nhận, không xử lý ở đây)

- `eval`/biến động/script con vẫn lọt — chấp nhận theo threat model. Nếu sau này cần bảo
  đảm cứng → mở sub-spec "post-hoc git safety net" (hướng B đã khảo sát).
- Các gate khác (`phase-chain`, `handoff-slice`, `node-checkpoint`, R-Apply-1 confirm,
  R-DNA-7) vẫn ở mức "trên giấy" — thuộc các mục #2–#6 của audit 2026-06-20, spec riêng.
