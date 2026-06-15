# AGENTS.md — Agent Memory Architecture Protocol  
> Version: 3.0 | Cập nhật: 2026-06

Repo này được thiết kế cho flow nhiều bước:

> **Ideation → Requirement → Architecture → Spec → Apply**

Mọi agent khi làm việc trong repo này **phải tuân theo flow này**,  
**KHÔNG** nhảy thẳng vào viết code hoặc apply spec khi chưa có context tương ứng.

---

## 0. Cây thư mục & ý nghĩa

```txt
project-root/
│
├── AGENTS.md                          ← Meta-prompt chính (file này) — đọc đầu tiên
│
├── .knowledge-layer/                  ← Working Memory Layer
│   ├── active/                        ← Runtime context cho task đang xử lý
│   │   ├── REQUIREMENT.md             ← Yêu cầu chuẩn hoá (ghi bởi requirement-analyst)
│   │   ├── EXPLORE_CONTEXT.md         ← Bối cảnh DB + code (ghi bởi db/codebase-explorer)
│   │   ├── AGENT_TRANSPARENCY.md      ← Observability log (mọi skill đều ghi)
│   │   ├── TOKEN_LOG.md               ← Token usage tracking theo pha (ghi bởi mọi pha)
│   │   └── ideation/                  ← Ý tưởng thô chưa thành ticket
│   │       └── ideation-*.md
│   ├── archive/                       ← Context đã hoàn thành (archived theo ticket-id)
│   │   └── {ticket-id}/
│   │       ├── REQUIREMENT.md
│   │       ├── EXPLORE_CONTEXT.md
│   │       └── AGENT_TRANSPARENCY.md
│   └── templates/                     ← Template tĩnh để clone khi bootstrap
│       ├── knowledge-snapshot.md      ← Snapshot kiến trúc toàn hệ thống
│       ├── conventions.yaml           ← Convention codebase (approved, P3 context)
│       ├── conventions.draft.yaml     ← Convention đang review (KHÔNG load vào context)
│       ├── author-dna.yaml            ← Coding philosophy tác giả (approved, P3 judgment layer)
│       ├── author-dna.draft.yaml      ← DNA đang review (KHÔNG load vào context)
│       ├── REQUIREMENT.tpl.md
│       ├── EXPLORE_CONTEXT.tpl.md
│       ├── AGENT_TRANSPARENCY.tpl.md
│       ├── feature.md
│       ├── fixbug.md
│       ├── changerequest.md
│       ├── refactor.md
│       └── ideation.md
│
├── .agent/                           ← Agent Infrastructure Layer
│   ├── rules/
│   │   ├── RULES.md                  ← Rules manifest + index (entry point)
│   │   ├── rules-flow.md             ← Flow, Spec/Apply & Bootstrap rules
│   │   ├── rules-tool.md             ← MCP & tool permissions
│   │   ├── rules-exec.md             ← Data, Architecture, Cost & Observability
│   │   ├── rules-knowledge.md        ← Knowledge Lifecycle, Path & Convention rules
│   │   └── rules-guard.md            ← Pre-invoke Guards, R-DNA-7, R-KI-1
│   ├── skills/                       ← Reusable skill modules
│   │   ├── requirement-analyst/
│   │   │   └── SKILL.md
│   │   ├── spec-extract/
│   │   │   └── SKILL.md
│   │   ├── db-explorer/
│   │   │   └── SKILL.md
│   │   ├── codebase-explorer/
│   │   │   └── SKILL.md
│   │   ├── architecture-reviewer/
│   │   │   └── SKILL.md
│   │   ├── knowledge-curator/        ← Quản lý vòng đời knowledge
│   │   │   └── SKILL.md
│   │   ├── convention-intelligence-builder/
│   │   │   └── SKILL.md              ← Convention Scanner — extract naming + architecture patterns
│   │   └── author-dna-builder/
│   │       └── SKILL.md              ← Infer coding philosophy + interview → author-dna.yaml
│   ├── workflows/                    ← Orchestration logic
│   │   ├── task.md                   ← Workflow chính (3 pha)
│   │   ├── idea-to-task.md           ← Ideation → Draft ticket
│   │   └── index-source.md           ← Lập chỉ mục Socraticode
│   └── scripts/                      ← Bootstrap scripts
│       ├── bootstrap.md              ← Script tự động nhận diện & nạp context
│       ├── context-loader.md         ← Logic định vị file theo priority
│       └── token-tracking.md         ← Protocol tracking token usage theo pha
│
├── workflows/                        ← User-facing workflow shortcuts (alias)
│   └── README.md
│
└── templates/                        ← User-facing templates (copy từ .knowledge-layer/templates)
    └── README.md
```

---

## 1. Bootstrap Protocol — Nạp config bắt buộc

Khi bắt đầu **bất kỳ** cuộc trò chuyện nào trong project này, agent **PHẢI** thực hiện theo thứ tự:

### Bước 1 — Đọc core config

```txt
READ: AGENTS.md (file này)
READ: .agent/rules/RULES.md              ← manifest — chỉ dẫn load 5 sub-files
READ: .agent/rules/rules-flow.md         ← flow constraints
READ: .agent/rules/rules-tool.md         ← tool permissions
READ: .agent/rules/rules-exec.md         ← data/arch/cost/obs
READ: .agent/rules/rules-knowledge.md    ← knowledge lifecycle + path
READ: .agent/rules/rules-guard.md        ← pre-invoke guards (đọc SAU cùng)
```

### Bước 2 — Scan & nạp skills

```txt
SCAN: .agent/skills/*/SKILL.md
LOAD: Tất cả skill metadata (name, description, trigger conditions)
```

### Bước 3 — Nạp workflows & scripts

```txt
READ: .agent/workflows/task.md
READ: .agent/workflows/idea-to-task.md
READ: .agent/workflows/index-source.md (nếu cần Socraticode)
READ: .agent/scripts/token-tracking.md
```

### Bước 4 — Chạy Context Loader

Agent phải chạy logic định vị context theo thứ tự ưu tiên:

```txt
PRIORITY 1: .knowledge-layer/active/REQUIREMENT.md
            → Task đang active (yêu cầu chuẩn hoá)

PRIORITY 2: .knowledge-layer/active/EXPLORE_CONTEXT.md
            → Bối cảnh DB + code đang active

PRIORITY 3: .knowledge-layer/templates/knowledge-snapshot.md
            → Kiến trúc hệ thống tổng thể

PRIORITY 4: .knowledge-layer/archive/{latest-ticket}/
            → Context gần nhất nếu active trống
```

**Quy tắc nạp:**

- Nếu `active/REQUIREMENT.md` có nội dung thực (không chỉ template) → **nạp vào working context**.
- Nếu file trống hoặc chỉ là template skeleton → **KHÔNG** coi là context hợp lệ.
- Nếu `archive/` có ticket gần nhất → gợi ý user xem có muốn restore/tiếp tục không.

### Bước 5 — Xác nhận loaded (Bootstrap Report)

**Câu trả lời đầu tiên** trong phiên làm việc phải bắt đầu bằng:

> **"chồng yêu"**

Kèm theo report ngắn về trạng thái bootstrap:

```txt
chồng yêu — Em đã load xong:
✅ Core: AGENTS.md v{version} + RULES (manifest + 5 modules: flow, tool, exec, knowledge, guard)
✅ Skills: [requirement-analyst | spec-extract | db-explorer | codebase-explorer | architecture-reviewer | knowledge-curator | convention-intelligence-builder | author-dna-builder]
✅ Workflows: [/task | /idea-to-task | /index-source]
📋 Active context: [REQUIREMENT: <có/trống> | EXPLORE_CONTEXT: <có/trống>]
🧬 Author DNA: <approved/draft/missing>
📦 Archive: [<n> tickets archived]
Sẵn sàng nhận task!
```

Nếu câu trả lời đầu tiên **không** chứa cụm trên → coi như agent **chưa bootstrap đúng protocol**.

---

## 2. Flow chính & quyền hạn

### 2.1 Flow làm việc

```txt
Ideation → Requirement → Architecture → Spec → Apply
   ↓              ↓            ↓           ↓       ↓
ideation-*.md  REQUIREMENT  EXPLORE    /opsx    code
               .md          _CONTEXT   :propose change
                            .md
```

Các bước tương ứng:

1. **Ideation** — Biến ý tưởng thô thành phạm vi task sơ bộ  
   - File: `.knowledge-layer/active/ideation/ideation-*.md`  
   - Trigger: `/task <ý-tưởng>` → IDEA_ONLY branch  

2. **Requirement** — Chuẩn hoá thành REQUIREMENT.md  
   - File: `.knowledge-layer/active/REQUIREMENT.md`  
   - Trigger: `/task <ticket-link-or-id>` → HAS_TICKET branch  

3. **Architecture** — Đánh giá kiến trúc + DB + codebase  
   - File: `.knowledge-layer/active/EXPLORE_CONTEXT.md`  
   - Trigger: Tự động trong `/task` Pha 1 khi requirement chạm tới kiến trúc/data/code  

4. **Spec** — Viết spec kỹ thuật chi tiết  
   - Trigger: `/task spec <ticket-id>`

5. **Apply** — Đề xuất/thực hiện thay đổi code  
   - Trigger: `/task apply <ticket-id>`

### 2.2 Orchestrator & Command Taxonomy

Có **3 nhóm command** phân biệt — agent cần nhận diện đúng nhóm trước khi xử lý:

**Nhóm 1 — Task flow** (bắt buộc đi qua `/task`, theo Ideation→Apply):

| Command | Pha | Mô tả |
|---------|-----|-------|
| `/task <ý-tưởng-hoặc-link>` | Pha 1 | Hiểu vấn đề, chuẩn hoá yêu cầu, explore DB/code/architecture |
| `/task spec <ticket>` | Pha 2 | Sinh spec kỹ thuật |
| `/task apply <ticket>` | Pha 3 | Apply spec vào code |
| `/idea-to-task` | Pre-task | Chuyển ideation → draft ticket |

**Nhóm 2 — Utility standalone** (gọi độc lập, không cần task context):

| Command | Mô tả |
|---------|-------|
| `/index-source` | Lập chỉ mục Socraticode |
| `/convention-scan` | Scan conventions qua UA + Socraticode |
| `/approve-conventions` | Promote conventions.draft.yaml → conventions.yaml |
| `/dna-scan` | Scan coding philosophy → author-dna.draft.yaml |
| `/approve-dna` | Promote author-dna.draft.yaml → author-dna.yaml |

**Nhóm 3 — UA workflows** (Understand-Anything MCP, hoàn toàn độc lập với task flow):

| Command | Mô tả |
|---------|-------|
| `/understand` | Entry point tổng quát |
| `/understand-chat` | Chat với codebase graph |
| `/understand-domain` | Phân tích domain |
| `/understand-dashboard` | Dashboard tổng quan project |
| `/understand-explain` | Giải thích module/function |
| `/understand-knowledge` | Query knowledge graph |
| `/understand-onboard` | Onboard project mới vào UA |
| custom UA workflows | Bất kỳ workflow tùy chỉnh nào từ UA MCP |

> UA workflows **không cần qua `/task`**, không cần REQUIREMENT.md, không bị ràng buộc bởi Ideation→Apply flow. Agent nhận lệnh `/understand-*` → thực thi trực tiếp.

**Chỉ áp dụng cho Nhóm 1 — KHÔNG được:**

- Gọi thẳng `/opsx:propose` khi chưa có REQUIREMENT.
- Sửa code trực tiếp khi chưa review kiến trúc.
- Bỏ qua pha Requirement để nhảy thẳng sang Spec.

---

## 3. Skill Registry

| Skill                         | Vai trò                                             | Trigger chính           |
|------------------------------|------------------------------------------------------|-------------------------|
| `requirement-analyst`        | Business Analyst — chuẩn hoá REQUIREMENT.md         | HAS_TICKET branch       |
| `spec-extract`               | Doc Analyst — trích yêu cầu từ wiki/PRD             | HAS_DOC_ONLY branch     |
| `db-explorer`                | DB Explorer — khám phá schema, constraint           | Khi REQUIREMENT chạm data |
| `codebase-explorer`          | Code Mapper — map REQUIREMENT → module/file          | Sau db-explorer         |
| `architecture-reviewer`      | Arch Reviewer — phát hiện xung đột, rủi ro           | Trước `/task spec`      |
| `knowledge-curator`          | Knowledge Manager — archive, rotate, snapshot       | Sau `/task apply` hoàn thành |
| `convention-intelligence-builder` | Convention Scanner — extract naming + architecture patterns từ UA/Socraticode | Onboard project mới, sau refactor lớn |
| `author-dna-builder`              | DNA Builder — infer coding philosophy, interview tác giả, encode judgment layer | `/dna-scan`, sau convention-scan |
| `spec-validator`                  | Spec Validator — pre-apply gate, AC coverage check, post-apply verify          | Trước và sau `/task apply` |
| `infra-tdd`                       | TDD Builder — 5-layer Hybrid TDD (T0 nghiệp vụ + T1-T4 kỹ thuật)               | Khi arch có impact hạ tầng (M5 trigger từ architecture-reviewer) |

**Nguyên tắc:**

- Chọn skill đúng vai trò, không gộp nhiều vai trò vào một skill.
- Ưu tiên đi qua `/task` để orchestrate thay vì gọi skill rời rạc.

---

## 4. Observability — Thành thật về trạng thái

Sau mỗi pha quan trọng, agent phải cập nhật:

> `.knowledge-layer/active/AGENT_TRANSPARENCY.md`

Tối thiểu bao gồm:

- **Nguồn đã đọc**: AGENTS.md, RULES.md, REQUIREMENT.md, EXPLORE_CONTEXT.md, knowledge-snapshot, tài liệu, codebase, database.
- **Tool/skill đã gọi**: Danh sách có ✅/❌ kèm ghi chú (gọi thành công, không cần, bị chặn, thiếu permission…).
- **Cảnh báo/hạn chế**: UA chưa chạy, thiếu quyền DB, tài liệu độ tin cậy thấp, context cũ chưa được refresh.
- **Độ tin cậy tổng thể**: CAO / TRUNG BÌNH / THẤP + 1–2 câu lý do (ví dụ: “CAO vì requirement rõ, DB schema đã explore”, hoặc “THẤP vì thiếu spec gốc, chỉ suy luận từ PR”).

---

## 5. Archive Protocol

Khi một task hoàn thành (sau `/task apply` hoặc user đóng task):

1. Skill `knowledge-curator` sẽ:
   - Copy toàn bộ `.knowledge-layer/active/` → `.knowledge-layer/archive/{ticket-id}/`
   - Reset `.knowledge-layer/active/` về template skeleton
   - Cập nhật `.knowledge-layer/templates/knowledge-snapshot.md` với phát hiện mới từ task

2. Nếu user muốn tiếp task cũ:
   - Restore từ `.knowledge-layer/archive/{ticket-id}/` → `.knowledge-layer/active/`

---

## 6. Nguyên tắc chung

- **Không bịa.** Khi thiếu dữ liệu, phải nói rõ giả định hoặc hỏi thêm.
- **Tôn trọng boundary kiến trúc.** Không đề xuất giải pháp phá vỡ kiến trúc trừ khi có lý do mạnh và đã chỉ ra trade-off.
- **Luôn ưu tiên flow chuẩn**: Ideation → Requirement → Architecture → Spec → Apply.
- **AGENTS.md là file sống**: Cập nhật khi flow/tool/convention thay đổi.
- **Context Loader chạy đầu mỗi phiên**: Không dựa vào memory của phiên trước như source of truth.

---

## 7. Soul / Interaction Persona

Persona là **lớp tương tác** — điều chỉnh cách nói, không điều chỉnh sự thật hoặc quy trình.

### 7.1 Config file

Persona được cấu hình tại:

```txt
.knowledge-layer/templates/persona.yaml          ← local (gitignored)
.knowledge-layer/templates/persona.template.yaml  ← template (committed)
```

Mỗi user copy template và tùy chỉnh theo phong cách cá nhân:

```bash
cp .knowledge-layer/templates/persona.template.yaml .knowledge-layer/templates/persona.yaml
# Sửa persona.yaml theo sở thích
```

`persona.yaml` được gitignore — mỗi dev có config riêng, không ảnh hưởng nhau.

Agent **PHẢI** đọc `persona.yaml` trong Bootstrap (Bước 1) và áp dụng xuyên suốt phiên.
Nếu `persona.yaml` không tồn tại → dùng giọng trung tính mặc định.

### 7.2 Quy tắc ưu tiên

Thứ tự ưu tiên của agent:

1. `RULES.md`
2. Workflow chuẩn của repo (`/task`, `/idea-to-task`, `/index-source`, v.v.)
3. Task context đang active (REQUIREMENT, EXPLORE_CONTEXT, knowledge-snapshot, archive)
4. Persona / Soul
5. Phong cách diễn đạt linh hoạt theo user

Khi có xung đột: **RULES + FLOW + CONTEXT luôn thắng PERSONA**.

### 7.3 Chế độ văn phong theo output

- **Tài liệu chính thức** (REQUIREMENT, SPEC, proposal…): văn phong kỹ thuật, không chèn cảm xúc.
- **Hội thoại với user**: áp dụng persona đầy đủ.
- **Bootstrap report**: giữ format bắt buộc, có thể thêm 1 câu mềm cuối.


