# U0 Baseline-Litmus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vận hành protocol U0 baseline-litmus một lần để ra `litmus-report` đầu tiên — bằng chứng định lượng "AMAP có cải thiện output đủ bù chi phí so với baseline không, và từ size nào".

**Architecture:** Đây là **plan vận hành một measurement protocol**, không phải plan code. Mỗi task tạo ra một *artifact đóng băng* (setup, ticket, baseline file, score, report) và một bước *verify* artifact đạt tiêu chí spec. TDD ceremony ("write failing test") không áp dụng; thay bằng "tạo artifact → kiểm đạt tiêu chí → commit". Chỉ một chỗ có code thật: tính precision/recall tập-file cho M2 (snippet dùng-một-lần, KHÔNG build tool — harness là UP1).

**Tech Stack:** Claude Code (Opus 4.8 cho 2 arm; Haiku 4.5 cho LLM-judge), git, AMAP CLI (`./install.sh` / `amap init`), Python one-liner cho M2.

**Spec nguồn:** [docs/superpowers/specs/2026-06-18-u0-baseline-litmus-design.md](../specs/2026-06-18-u0-baseline-litmus-design.md)

**Reconcile với spec §10:** Spec nói *running* không thuộc deliverable batch. Plan này cố ý mở rộng sang running để validate-first — deliverable của plan = `litmus-report` đầu tiên + bộ input đã đóng băng. Spec (methodology) vẫn là nguồn sự thật; plan chỉ *thực thi* nó.

---

## Artifact structure (mọi thứ commit vào AMAP repo, trừ phần nặng)

```
docs/superpowers/litmus/
├── SETUP.md              ← pre-registration: repo@sha, model versions, decision-rule (frozen), judge model
├── tickets.md            ← 3 ticket: PR#, size + lý do, ground-truth ref, prompt đã-giấu-đáp-án
├── baseline-CLAUDE.md    ← entry-point baseline mỏng, ĐÓNG BĂNG
├── judge-prompt.md       ← prompt chấm bịt-mắt cho LLM-judge (cố định)
├── runs/
│   ├── R1-T1-tiny-baseline.md      ← run log: metrics + diff (name-only) + ghi chú
│   ├── R2-T1-tiny-amap.md
│   ├── R3-T2-standard-amap.md
│   ├── R4-T2-standard-baseline.md
│   ├── R5-T3-complex-baseline.md
│   └── R6-T3-complex-amap.md
├── scores.md             ← M1–M6 mỗi run; tính M2; ref transcript judge
└── litmus-report.md      ← report cuối (theo spec Appendix A) + verdict gradient + break-even + U1 rec + friction triage
```

**KHÔNG commit vào repo:** bản clone repo target (clone ra `/tmp/litmus-*`, tham chiếu bằng `repo@sha`), transcript thô đầy đủ của agent. Lý do: giữ North Star #1 Generic — chỉ commit *bằng chứng đã chắt lọc* của AMAP, không nhét code dự án khác vào framework repo.

- [ ] **Bước chuẩn bị: tạo thư mục + gitignore phần nặng**

```bash
mkdir -p docs/superpowers/litmus/runs
printf '/tmp/litmus-*\n' >> .gitignore
git add docs/superpowers/litmus/.gitignore 2>/dev/null; git add .gitignore
git commit -m "chore(litmus): scaffold litmus artifact dir + ignore clones"
```

---

## Phase 0 — Pre-registration (đóng băng input TRƯỚC khi chạy)

> Mục tiêu phase: chốt mọi tham số *trước* khi thấy bất kỳ con số nào, để verdict không bị rationalize. Hết phase này, mọi thứ ảnh hưởng kết quả đều đóng băng trong git.

### Task 1: Chọn & ghi repo target

**Files:**
- Create: `docs/superpowers/litmus/SETUP.md`

- [ ] **Step 1: Chọn repo theo tiêu chí §3.1 + chống nhiễu R1 (§3.3)**

Tiêu chí bắt buộc (verify từng cái):
- Repo OSS công khai, license cho phép clone.
- Có DB + code thật (vd web app có ORM/migration).
- Lịch sử có PR đã merge, mô tả rõ, có review comments.
- **Chống R1:** ưu tiên repo *vừa phải* (không phải top-10 phổ biến) VÀ chọn được PR **merge sau cutoff model** (model Opus 4.8 cutoff: 2026-01) — để agent ít khả năng đã thấy lời giải.

Cách làm: duyệt vài repo ứng viên trên GitHub, kiểm "Pull requests → Closed/Merged", tìm repo có ≥3 PR merged sau 2026-01 đủ 3 mức độ. Ghi lựa chọn — KHÔNG để trống.

- [ ] **Step 2: Clone ra ngoài repo + chốt commit SHA**

```bash
git clone <repo-url> /tmp/litmus-target
cd /tmp/litmus-target && git rev-parse HEAD   # ghi SHA này
```

- [ ] **Step 3: Ghi vào SETUP.md**

```markdown
# Litmus SETUP — pre-registered <YYYY-MM-DD>

## Target
- Repo: <org/name> (<url>)
- Pinned commit (base để checkout trước mỗi run): <sha>
- License: <...>
- R1 note: PR chọn merge sau 2026-01 (model cutoff). Mức phổ biến repo: <thấp/vừa>.

## Models (đóng băng)
- Hai arm: claude-opus-4-8 (CÙNG model cho cả AMAP và baseline — yêu cầu công bằng)
- LLM-judge: claude-haiku-4-5-20251001 (model rẻ). Fallback nếu spot-check lệch: claude-sonnet-4-6.
```

- [ ] **Step 4: Verify + commit**

Verify: SETUP.md có đủ repo URL, SHA, license, model. Không còn `<...>` ở mục Target/Models.

```bash
git add docs/superpowers/litmus/SETUP.md
git commit -m "docs(litmus): pre-register target repo + models"
```

### Task 2: Chọn & ghi 3 ticket (tiny/standard/complex)

**Files:**
- Create: `docs/superpowers/litmus/tickets.md`

- [ ] **Step 1: Chọn 3 PR merged khớp size (theo §4)**

Gán size theo ground truth (diff merge), không theo cảm giác:
- tiny: 1–2 file, không đụng DB/schema.
- standard: vài file + 1 module, có đụng data layer.
- complex: nhiều module, đụng DB + ràng buộc kiến trúc / blast-radius rộng.

- [ ] **Step 2: Với mỗi ticket, soạn "đề bài đã giấu đáp án"**

Đề = tiêu đề + mô tả issue/PR, **cắt bỏ mọi gợi ý lời giải/diff**. Đây là prompt y hệt cấp cho cả 2 arm.

- [ ] **Step 3: Ghi vào tickets.md**

```markdown
# Litmus Tickets — pre-registered

## T1 — tiny
- PR: #<n> (<url>), merged <date>
- Size lý do: <vd "1 file, không đụng DB">
- Ground truth: diff merge của PR (file set: `<a.py, b.py>`); review comments: <tóm tắt cái reviewer bắt>
- PROMPT (giấu đáp án):
  > <đề bài>

## T2 — standard
  <như trên>

## T3 — complex
  <như trên>
```

- [ ] **Step 4: Verify + commit**

Verify từng ticket: (a) size khớp tiêu chí, (b) prompt KHÔNG lộ lời giải (đọc lại, đảm bảo không nhắc tên hàm/file đáp án), (c) có ground-truth file-set ghi sẵn (cần cho M2).

```bash
git add docs/superpowers/litmus/tickets.md
git commit -m "docs(litmus): pre-register 3 tickets (tiny/standard/complex)"
```

### Task 3: Soạn & đóng băng baseline entry-point

**Files:**
- Create: `docs/superpowers/litmus/baseline-CLAUDE.md`

- [ ] **Step 1: Viết baseline mỏng theo §2.1**

Chỉ chứa 3 thứ, viết *tử tế* (chống strawman). KHÔNG chứa bộ máy AMAP, KHÔNG gợi ý ticket.

```markdown
# CLAUDE.md (baseline — frozen for litmus)

## Build / Test
- <lệnh build>
- <lệnh chạy test>

## Conventions
- Naming: <quy ước repo>
- Layering: <vd "validation ở service layer, không ở handler">

## Architecture (≤150 từ)
<tóm tắt kiến trúc hệ thống lấy từ README/docs repo target>
```

- [ ] **Step 2: Verify "không bị làm yếu" + "không có AMAP"**

```bash
# KHÔNG được khớp bất cứ thứ gì thuộc bộ máy AMAP:
/usr/bin/grep -iE 'ideation|requirement|architecture-review|knowledge-snapshot|mechanical gate|/task|5 pha|5-phase' docs/superpowers/litmus/baseline-CLAUDE.md && echo "FAIL: baseline leaked AMAP machinery" || echo "OK: clean baseline"
```
Expected: `OK: clean baseline`

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/litmus/baseline-CLAUDE.md
git commit -m "docs(litmus): freeze thin baseline entry-point"
```

### Task 4: Đóng băng decision rule + judge prompt

**Files:**
- Modify: `docs/superpowers/litmus/SETUP.md` (thêm mục Decision rule)
- Create: `docs/superpowers/litmus/judge-prompt.md`

- [ ] **Step 1: Thêm decision-rule (frozen, theo §9.1) vào SETUP.md**

```markdown
## Decision rule (FROZEN — đánh giá theo từng size)
AMAP "đáng" ở một size nếu:
- median(M1) cải thiện ≥ 1 điểm (thang 0–4)  HOẶC  recall(M2) cao hơn ≥ 0.25 so với baseline,
- VÀ overhead token (M5) ≤ 3× baseline.
Ngược lại "không đáng". Hỗn hợp → "mờ" → thêm ticket cùng size.
Output verdict = gradient theo size + break-even point (size nhỏ nhất "đáng") → feed U1 tiering.
```

- [ ] **Step 2: Viết judge-prompt.md (chấm bịt mắt, theo §7.1)**

```markdown
# Blinded LLM-judge prompt (M1, M3) — chạy bằng claude-haiku-4-5-20251001

Bạn là giám khảo trung lập. Dưới đây là (1) đề bài, (2) GROUND TRUTH (diff con người đã merge + review),
(3) hai output "Output X" và "Output Y" (KHÔNG biết cái nào của hệ nào). Chấm MỖI output độc lập.

## Đề bài
<paste prompt ticket>

## Ground truth
<paste diff merge + tóm tắt review comments>

## Output X
<paste diff arm X>

## Output Y
<paste diff arm Y>

## Chấm (mỗi output)
M1 Correctness/Rework (0–4): 4=khớp ý định ground truth, không rework; 3=đúng hướng, sai chi tiết nhỏ;
2=đúng một phần, thiếu case quan trọng; 1=sai hướng phần lớn; 0=không chạy/lạc đề.
M3 Convention (0–4): 4=theo sát naming/layering repo; 3=lệch nhỏ; 2=lệch thấy rõ; 1=lệch nhiều; 0=bỏ qua.

Trả JSON: {"X":{"M1":_,"M3":_,"reason":""},"Y":{"M1":_,"M3":_,"reason":""}}
```

- [ ] **Step 3: Verify + commit**

Verify: SETUP có decision-rule không còn `<...>`; judge-prompt có đủ rubric M1/M3 + định dạng JSON.

```bash
git add docs/superpowers/litmus/SETUP.md docs/superpowers/litmus/judge-prompt.md
git commit -m "docs(litmus): freeze decision rule + blinded judge prompt"
```

---

## Phase 1 — Vận hành ≥6 run

> Mỗi run chạy trong **một clone tươi** của repo target (đảm bảo cô lập tuyệt đối giữa các arm/run). Lịch chạy **counterbalance** thứ tự arm giữa các ticket.

**Lịch chạy (đóng băng):**

| Run | Ticket | Size | Arm | Thứ tự trong ticket |
|---|---|---|---|---|
| R1 | T1 | tiny | baseline | 1st |
| R2 | T1 | tiny | AMAP | 2nd |
| R3 | T2 | standard | AMAP | 1st |
| R4 | T2 | standard | baseline | 2nd |
| R5 | T3 | complex | baseline | 1st |
| R6 | T3 | complex | AMAP | 2nd |

### Task 5: Quy trình chạy một run (template áp cho R1–R6)

> Đây là quy trình *giống hệt* cho cả 6 run; chỉ khác tham số (ticket/arm) theo bảng trên. Thực thi 6 lần, mỗi lần tạo một file `runs/R<n>-...md`.

**Files (mỗi run):**
- Create: `docs/superpowers/litmus/runs/R<n>-<ticket>-<size>-<arm>.md`

- [ ] **Step 1: Clone tươi + checkout base SHA**

```bash
rm -rf /tmp/litmus-run && git clone <repo-url> /tmp/litmus-run
cd /tmp/litmus-run && git checkout <sha-từ-SETUP>
```

- [ ] **Step 2: Dựng đúng arm**

*Nếu arm = baseline:*
```bash
cp <amap-repo>/docs/superpowers/litmus/baseline-CLAUDE.md /tmp/litmus-run/CLAUDE.md
```
*Nếu arm = AMAP:*
```bash
cd <amap-repo> && ./install.sh /tmp/litmus-run    # init platform=claude-code
# reset active/ về rỗng (cold-start, theo §2 + §8):
rm -rf /tmp/litmus-run/.claude/knowledge/active/* 2>/dev/null
# nếu long-term có sẵn nội dung repo target → reset về skeleton template
```

- [ ] **Step 3: Chạy, ghi mốc thời gian + đếm can thiệp**

- Mở session Claude Code **tươi** (Opus 4.8) trong `/tmp/litmus-run`.
- baseline: dán thẳng PROMPT ticket (ad hoc). AMAP: chạy `/task <PROMPT ticket>` và đi hết 5 pha tới apply.
- Ghi `start_ts`, `end_ts`. Mỗi lần phải can thiệp tay (unstuck/sửa hướng) → +1 vào M4.

- [ ] **Step 4: Thu artifact + metric**

```bash
cd /tmp/litmus-run
git add -A && git diff --cached --name-only      # → file-set (cho M2)
git diff --cached > /tmp/run-diff.patch           # → diff để judge chấm
```
Lấy **token** từ Claude Code usage của session (M5); tính **wall-clock** = end−start (M6).

- [ ] **Step 5: Ghi run log + commit**

```markdown
# R<n> — <ticket> <size> <arm>

- Base: <repo@sha> | Model: claude-opus-4-8 | Ngày: <...>
- M4 interventions: <n>
- M5 token: <n>
- M6 wall-clock (phút): <n>
- File-set đụng: <a.py, b.py>
- Diff: dán hoặc tham chiếu (KHÔNG commit clone; dán patch gọn nếu nhỏ)
- Ghi chú ma sát (cho friction log): <agent khựng ở đâu / gate bắn đúng-sai>
```

```bash
git add docs/superpowers/litmus/runs/R<n>-<...>.md
git commit -m "test(litmus): run R<n> <ticket>/<arm> result"
```

- [ ] **Step 6: Lặp Step 1–5 cho đủ R1..R6 theo bảng lịch chạy**

Verify hết phase: có đủ 6 file trong `runs/`, mỗi file có đủ M4/M5/M6 + file-set.

---

## Phase 2 — Chấm điểm

### Task 6: Tính M2 (blast-radius, cơ học) cho 6 run

**Files:**
- Create: `docs/superpowers/litmus/scores.md`

- [ ] **Step 1: Với mỗi run, tính precision/recall tập-file vs ground truth**

Snippet dùng-một-lần (KHÔNG commit thành tool):
```bash
python3 - <<'PY'
arm   = {"a.py","b.py"}          # file-set của run (Step 4 Phase 1)
truth = {"a.py","b.py","t.py"}   # ground-truth file-set (tickets.md)
inter = arm & truth
print("precision", len(inter)/len(arm) if arm else 0)
print("recall",    len(inter)/len(truth) if truth else 0)
PY
```

- [ ] **Step 2: Ghi M2 (P/R) mỗi run vào scores.md.** Commit.

```bash
git add docs/superpowers/litmus/scores.md
git commit -m "test(litmus): M2 blast-radius precision/recall"
```

### Task 7: Chấm M1/M3 bằng LLM-judge bịt mắt

- [ ] **Step 1: Ghép cặp + bịt mắt mỗi (ticket)**

Với mỗi ticket: lấy diff AMAP + diff baseline, **trộn ngẫu nhiên** gán "Output X"/"Output Y", ghi lại map thật (giấu khỏi judge).

- [ ] **Step 2: Chạy judge bằng model rẻ**

Dùng `judge-prompt.md`, model `claude-haiku-4-5-20251001`. Thu JSON điểm M1/M3 cho X và Y.

- [ ] **Step 3: Map ngược nhãn → ghi M1/M3 thật mỗi arm vào scores.md.** Commit.

```bash
git add docs/superpowers/litmus/scores.md
git commit -m "test(litmus): M1/M3 blinded LLM-judge scores"
```

### Task 8: Human spot-check

- [ ] **Step 1: Tự chấm tay ≥1 ticket (ưu tiên ticket complex)** theo cùng rubric §7.1.

- [ ] **Step 2: So với điểm judge.** Lệch ≤1 điểm → giữ điểm judge. Lệch >1 điểm hệ thống → ghi chú, đổi judge sang `claude-sonnet-4-6` (fallback SETUP) và chấm lại ticket đó.

- [ ] **Step 3: Ghi kết luận spot-check vào scores.md.** Commit.

```bash
git add docs/superpowers/litmus/scores.md
git commit -m "test(litmus): human spot-check vs judge"
```

---

## Phase 3 — Verdict & report

### Task 9: Lập litmus-report (gradient theo size + break-even)

**Files:**
- Create: `docs/superpowers/litmus/litmus-report.md`

- [ ] **Step 1: Điền report theo template spec Appendix A**

Gồm: Setup (repo@sha, models, decision-rule frozen), bảng per-run (mọi ticket×arm, M1–M6), bảng **Verdict gradient theo size** (tiny/standard/complex: ΔM1, ΔM2 recall, ΔM3, ΔM5, Đáng?).

- [ ] **Step 2: Áp decision rule (frozen) cho từng size → xác định break-even**

```markdown
## Verdict — gradient theo size
| Size | ΔM1 | ΔM2(recall) | ΔM3 | ΔM5(token) | Đáng? |
|------|-----|------------|-----|-----------|-------|
| tiny |  |  |  |  |  |
| standard |  |  |  |  |  |
| complex |  |  |  |  |  |

- Break-even point (size nhỏ nhất "đáng"): <...>
- Khuyến nghị U1 tiering: size < break-even → tier nhẹ; ≥ break-even → full pipeline.
```

- [ ] **Step 3: Friction log đã triage (theo §9.3)**

Gom ghi-chú-ma-sát từ 6 run; mỗi điểm gán đúng MỘT nhãn: `(U1-tiering)` / `(patch-SP1)` / `(issue-mới)`. KHÔNG fix trong phạm vi này.

- [ ] **Step 4: Verify coverage + commit**

Verify: report trả lời được cả 2 — (a) AMAP đáng từ size nào, (b) friction đã triage hết. Không còn `<...>` ở Verdict.

```bash
git add docs/superpowers/litmus/litmus-report.md
git commit -m "docs(litmus): first litmus-report — verdict gradient + break-even"
```

### Task 10: Cập nhật TODOS + handoff

**Files:**
- Modify: `TODOS.md` (P1.1 → trạng thái + link report), `TODOS2.md` (handoff Batch 2 → done)

- [ ] **Step 1: Đánh dấu P1.1 done, link `litmus-report.md`, ghi verdict 1 dòng** vào TODOS.md và TODOS2.md.

- [ ] **Step 2: Ghi "next" theo verdict:** nếu thesis đúng → mở UP1 (harness) + dùng break-even cho U1; nếu không đáng → office-hours xoay hướng.

- [ ] **Step 3: Commit.**

```bash
git add TODOS.md TODOS2.md
git commit -m "docs(todo): close P1.1 with litmus verdict, set next step"
```

---

## Self-Review (đã chạy)

**1. Spec coverage:**
- §2 A/B 2 arm + cold-start → Task 5 Step 2–3. ✅
- §2.1 baseline mỏng chống strawman → Task 3 + grep verify. ✅
- §3 target + ground truth + R1 → Task 1. ✅
- §4 3 ticket theo size → Task 2. ✅
- §5 ma trận ≥6 run / 1 platform → Phase 1 bảng lịch chạy. ✅
- §6 metrics M1–M6 → M2 Task 6, M4/M5/M6 Task 5 Step 4, M1/M3 Task 7. ✅
- §7 hybrid scoring + rubric → Task 6 (cơ học), Task 7 (judge bịt mắt), Task 8 (spot-check). ✅
- §8 confounders (session tách, counterbalance, blind, record) → clone tươi mỗi run, bảng lịch, Task 7 Step 1, SETUP. ✅
- §9 verdict gradient + break-even + triage → Task 9. ✅
- §10 không build harness → đã nêu rõ; M2 dùng snippet dùng-một-lần. ✅

**2. Placeholder scan:** Các `<...>` còn lại đều là *ô điền dữ liệu thật khi chạy* (SHA, PR#, số đo) — không phải logic bị bỏ trống. Mọi quyết định (model, decision-rule, lịch chạy, rubric, judge prompt) đều cụ thể. ✅

**3. Type consistency:** Tên metric M1–M6, tên file `runs/R<n>-...`, model id (`claude-opus-4-8`, `claude-haiku-4-5-20251001`, `claude-sonnet-4-6`) nhất quán xuyên các task. ✅
