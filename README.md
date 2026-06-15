# 🧠 Agent Memory Architecture Protocol (AMAP)

> **Phiên bản 3.0** · Một protocol bộ nhớ và luồng làm việc có cấu trúc, giúp AI coding agent có context xuyên phiên, luồng công việc bắt buộc, và các rào chắn kiến trúc khi làm việc với codebase.

---

## Vấn đề cần giải quyết

Các AI coding agent hiện tại (Copilot, Gemini, Claude, Cursor...) đều mắc chung một vấn đề: **mất trí nhớ giữa các phiên làm việc**.

- Quên quyết định kiến trúc từ cuộc trò chuyện trước
- Nhảy thẳng vào viết code mà không hiểu yêu cầu
- Bỏ qua naming convention và design pattern đã có trong dự án
- Không thể đánh giá tác động (blast radius) khi thay đổi code
- Không có khái niệm "luồng công việc" — chỉ có prompt → response

**AMAP giải quyết điều này** bằng cách cung cấp một protocol có cấu trúc mà bất kỳ AI agent nào cũng có thể tuân theo — cho nó bộ nhớ làm việc, luồng công việc đa pha bắt buộc, và khả năng tích luỹ tri thức qua mỗi phiên.

---

## Cách hoạt động

AMAP áp dụng **luồng 5 pha bắt buộc** cho mọi task:

```
Ideation → Requirement → Architecture → Spec → Apply
    ↓           ↓             ↓           ↓       ↓
 ideation-   REQUIREMENT   EXPLORE      Spec    Thay đổi
 *.md        .md           _CONTEXT     kỹ thuật  code
                           .md
```

Mỗi pha có:
- **Skill chuyên biệt** — module agent cho từng vai trò (Business Analyst, DB Explorer, Code Mapper, Architecture Reviewer...)
- **Quy tắc bắt buộc** — agent không được bỏ qua pha hay nhảy vào code khi chưa có context
- **Artifact bền vững** — tri thức được tích luỹ qua các phiên trong file có cấu trúc
- **Tính minh bạch** — mọi quyết định, tool call, giả định đều được ghi log

---

## Tổng quan Kiến trúc

```
project-root/
│
├── AGENTS.md                          ← Meta-prompt chính (agent đọc file này đầu tiên)
│
├── .knowledge-layer/                  ← Tầng Bộ nhớ Làm việc
│   ├── active/                        ← Context runtime cho task đang xử lý
│   │   ├── REQUIREMENT.md             ← Yêu cầu đã chuẩn hoá
│   │   ├── EXPLORE_CONTEXT.md         ← Kết quả khám phá DB + code
│   │   ├── AGENT_TRANSPARENCY.md      ← Log minh bạch (audit trail)
│   │   ├── TOKEN_LOG.md               ← Theo dõi token theo từng pha
│   │   └── ideation/                  ← Ý tưởng thô chưa thành ticket
│   ├── archive/                       ← Context đã hoàn thành (theo ticket-id)
│   └── templates/                     ← Template cố định + tri thức tích luỹ
│       ├── knowledge-snapshot.md      ← Bản đồ kiến trúc hệ thống (tích luỹ qua mỗi task)
│       ├── conventions.yaml           ← Convention đặt tên + design pattern của dự án
│       ├── author-dna.yaml            ← Triết lý code của tác giả (judgment layer)
│       └── persona.yaml               ← Phong cách tương tác của agent (tuỳ chỉnh per-user)
│
├── .agent/                            ← Tầng Hạ tầng Agent
│   ├── rules/                         ← Rào chắn (flow, tool, data, kiến trúc)
│   │   ├── RULES.md                   ← Manifest quy tắc (entry point)
│   │   ├── rules-flow.md              ← Ràng buộc luồng công việc
│   │   ├── rules-tool.md              ← Quyền truy cập MCP & tool
│   │   ├── rules-exec.md              ← Chi phí, budget & observability
│   │   ├── rules-knowledge.md         ← Vòng đời tri thức & quy ước đường dẫn
│   │   └── rules-guard.md             ← Guard trước khi gọi skill & teaching moments
│   ├── skills/                        ← Các module skill tái sử dụng (12 skills)
│   ├── workflows/                     ← Logic điều phối
│   └── scripts/                       ← Script bootstrap & tiện ích
│
├── workflows/                         ← Shortcut workflow cho người dùng
└── templates/                         ← Shortcut template cho người dùng
```

---

## Các khái niệm chính

### 🔧 Skills (Năng lực Module hoá của Agent)

| Skill | Vai trò | Khi nào dùng |
|-------|---------|--------------|
| `requirement-analyst` | Business Analyst — chuẩn hoá yêu cầu thành REQUIREMENT.md | Khi nhận ticket/task mới |
| `spec-extract` | Doc Analyst — trích xuất spec từ wiki/PRD | Khi yêu cầu đến từ tài liệu |
| `db-explorer` | DB Explorer — khám phá schema, constraint, trigger | Khi task chạm tầng dữ liệu |
| `codebase-explorer` | Code Mapper — map yêu cầu → module/file liên quan | Sau khi đã khám phá DB |
| `architecture-reviewer` | Arch Reviewer — phát hiện xung đột & rủi ro kiến trúc | Trước khi sinh spec |
| `knowledge-curator` | Knowledge Manager — archive và tích luỹ tri thức | Sau khi task hoàn thành |
| `convention-intelligence-builder` | Convention Scanner — trích xuất naming pattern | Khi onboard dự án mới |
| `author-dna-builder` | DNA Builder — encode triết lý code của tác giả | Tạo judgment layer cho agent |
| `spec-validator` | Spec Validator — kiểm tra spec trước/sau apply | Trước và sau khi thay đổi code |
| `infra-tdd` | TDD Builder — Technical Design Document 5 tầng | Khi thay đổi ảnh hưởng hạ tầng |
| `document-writer` | Doc Writer — tài liệu kỹ thuật | README, ADR, architecture doc |
| `openspec-*` | Tích hợp OpenSpec — propose, explore, apply, archive | Sinh code từ spec |

### 📋 Workflows (Lệnh điều phối)

| Lệnh | Pha | Mô tả |
|------|-----|-------|
| `/task <ý-tưởng-hoặc-ticket>` | Pha 1 | Hiểu vấn đề, chuẩn hoá yêu cầu, khám phá DB/code/kiến trúc |
| `/task spec <ticket>` | Pha 2 | Sinh spec kỹ thuật chi tiết |
| `/task apply <ticket>` | Pha 3 | Apply spec vào code |
| `/idea-to-task` | Pre-task | Chuyển ideation thô thành draft ticket |
| `/index-source` | Tiện ích | Lập chỉ mục codebase cho tìm kiếm ngữ nghĩa (Socraticode) |
| `/convention-scan` | Tiện ích | Quét và trích xuất convention của codebase |
| `/dna-scan` | Tiện ích | Quét và encode triết lý code của tác giả |

### 🛡️ Rules (Rào chắn)

Hệ thống quy tắc ngăn chặn các lỗi phổ biến của AI agent:

- **Flow Rules** — Agent không được bỏ qua pha hoặc nhảy vào code khi chưa có context
- **Tool Rules** — Truy cập DB chỉ đọc, thay đổi code chỉ qua spec đã duyệt
- **Data Rules** — Không bao giờ log PII, dữ liệu mẫu giới hạn kích thước
- **Architecture Rules** — Độ tin cậy gắn liền với mức độ khám phá thực tế
- **Cost Rules** — Budget token theo pha với cảnh báo tự động
- **Knowledge Rules** — Bắt buộc archive, thứ tự ưu tiên nguồn sự thật
- **Guard Rules** — Kiểm tra trước khi gọi skill, bắt teaching moment, enforce convention

### 🧬 Kho Tri thức Bền vững

| Kho | Mục đích | Tích luỹ? |
|-----|----------|-----------|
| `knowledge-snapshot.md` | Bản đồ kiến trúc hệ thống (bảng, module, entry point, business rule) | ✅ Có — tích luỹ sau mỗi task |
| `conventions.yaml` | Convention đặt tên, design pattern, upstream constraint | ✅ Có — cập nhật sau mỗi lần scan |
| `author-dna.yaml` | Triết lý và sở thích code của tác giả | ✅ Có — làm giàu qua teaching moments |
| `archive/{ticket-id}/` | Snapshot đầy đủ của context đã hoàn thành | ✅ Có — tăng theo mỗi task xong |

---

## Bắt đầu nhanh

### 1. Clone và tích hợp vào dự án

```bash
# Clone protocol
git clone https://github.com/VIethoangnguyenle/Agent-Memory-Architecture-Protocol.git

# Copy các file protocol vào dự án hiện có
cp -r Agent-Memory-Architecture-Protocol/.agent your-project/.agent
cp -r Agent-Memory-Architecture-Protocol/.knowledge-layer your-project/.knowledge-layer
cp Agent-Memory-Architecture-Protocol/AGENTS.md your-project/AGENTS.md
```

### 2. Tuỳ chỉnh persona (tuỳ chọn)

```bash
cd your-project
cp .knowledge-layer/templates/persona.template.yaml .knowledge-layer/templates/persona.yaml
# Sửa persona.yaml theo phong cách tương tác mong muốn
```

### 3. Bắt đầu sử dụng với AI agent

Agent sẽ đọc `AGENTS.md` ở root và tự động bootstrap. Ở tin nhắn đầu tiên, agent sẽ:

1. Đọc `AGENTS.md` + toàn bộ rules
2. Quét và nạp tất cả skills
3. Nạp workflows và scripts
4. Kiểm tra context đang active
5. Báo cáo trạng thái bootstrap

Sau đó bắt đầu làm việc:

```
# Bắt đầu với ý tưởng mới
/task Thêm giới hạn số lệnh giao dịch mỗi ngày theo nhân viên

# Bắt đầu với ticket có sẵn
/task https://jira.example.com/browse/ABC-123

# Sinh spec kỹ thuật
/task spec ABC-123

# Apply spec vào code
/task apply ABC-123
```

---

## Tương thích với các AI Agent

AMAP hoạt động với bất kỳ AI coding agent nào có thể đọc file dự án:

| AI Tool | Entry Point | Cách thiết lập |
|---------|-------------|----------------|
| **Gemini CLI / Jules** | `AGENTS.md` (native) | ✅ Hoạt động ngay |
| **Google Antigravity** | User Rules | ✅ Hoạt động ngay |
| **Claude Code** | `CLAUDE.md` | Tạo `CLAUDE.md` trỏ về `AGENTS.md` |
| **Cursor** | `.cursorrules` | Tạo `.cursorrules` trỏ về `AGENTS.md` |
| **GitHub Copilot** | `.github/copilot-instructions.md` | Tạo file trỏ về `AGENTS.md` |
| **Windsurf** | `.windsurfrules` | Tạo file trỏ về `AGENTS.md` |

### Tích hợp MCP Server (Tuỳ chọn)

AMAP được thiết kế để hoạt động với các MCP server sau khi có sẵn:

| MCP Server | Mục đích |
|------------|----------|
| **Socraticode** | Tìm kiếm ngữ nghĩa code, dependency graph, phân tích symbol |
| **Confluence** | Trích xuất tài liệu từ wiki/PRD |
| **db-remote** | Khám phá database schema (chỉ đọc) |

---

## Nguyên tắc Thiết kế

1. **Luồng trước tự do** — Các pha có cấu trúc ngăn việc code vội vàng
2. **Kiến trúc dựa trên bằng chứng** — Khám phá DB và code trước khi đề xuất thay đổi
3. **Tích luỹ tri thức** — Mỗi task làm agent thông minh hơn cho task tiếp theo
4. **Con người luôn trong vòng lặp** — Quyết định quan trọng luôn cần xác nhận của người dùng
5. **Minh bạch mặc định** — Mọi hành động của agent đều được log và có thể audit
6. **Enforce convention** — Naming và design pattern được mã hoá thành file, không dựa vào trí nhớ
7. **Bắt teaching moment** — Khi người dùng sửa agent, bài học được ghi lại vĩnh viễn

---

## Vòng đời Tri thức

```
┌─────────────────────────────────────────────────────────┐
│                    Task đang Active                     │
│                                                         │
│   REQUIREMENT.md ──→ EXPLORE_CONTEXT.md ──→ SPEC       │
│        ↓                    ↓                  ↓        │
│   requirement-        db-explorer +       openspec-     │
│   analyst             codebase-explorer   propose       │
│                             ↓                           │
│                    architecture-reviewer                │
└───────────────────────────┬─────────────────────────────┘
                            │ Task hoàn thành
                            ▼
┌─────────────────────────────────────────────────────────┐
│               knowledge-curator                         │
│                                                         │
│   1. Archive active/ → archive/{ticket-id}/             │
│   2. Cập nhật knowledge-snapshot.md với phát hiện mới   │
│   3. Reset active/ về template skeleton                 │
│   4. Đánh dấu nếu convention cần quét lại              │
└─────────────────────────────────────────────────────────┘
```

---

## Ví dụ: Bootstrap Report trông như thế nào

Khi agent bắt đầu làm việc trong dự án có AMAP, nó sẽ tạo báo cáo bootstrap:

```
✅ Core: AGENTS.md v3.0 + RULES (manifest + 5 modules: flow, tool, exec, knowledge, guard)
✅ Skills: [requirement-analyst | spec-extract | db-explorer | codebase-explorer |
           architecture-reviewer | knowledge-curator | convention-intelligence-builder |
           author-dna-builder | spec-validator | infra-tdd]
✅ Workflows: [/task | /idea-to-task | /index-source]
📋 Active context: [REQUIREMENT: trống | EXPLORE_CONTEXT: trống]
🧬 Author DNA: approved
📦 Archive: [3 tickets archived]
Sẵn sàng nhận task!
```

---

## Câu hỏi thường gặp

### Có thể dùng cho dự án private/enterprise không?

Có. AMAP là tầng protocol — không chứa code ứng dụng. Copy `.agent/` và `.knowledge-layer/` vào repo private của bạn rồi tuỳ chỉnh `knowledge-snapshot.md` theo kiến trúc hệ thống của bạn.

### AMAP có thay thế AI tool hiện tại không?

Không. AMAP bổ sung cấu trúc cho AI tool hiện có. AI agent (Gemini, Claude, Cursor...) đọc các file protocol và tuân theo luồng — nó không thay thế agent.

### Nếu AI agent không hỗ trợ AGENTS.md thì sao?

Tạo file pointer cho tool cụ thể (xem bảng [Tương thích](#tương-thích-với-các-ai-agent)). File pointer chỉ cần trỏ agent về `AGENTS.md` để đọc hướng dẫn đầy đủ.

### Làm sao ngăn rò rỉ dữ liệu nhạy cảm?

AMAP có quy tắc dữ liệu sẵn (R-Data-1, R-Data-2) cấm agent log PII hoặc credential vào bất kỳ file context nào. Thư mục `active/` được gitignore mặc định.

### Nhiều thành viên trong team có dùng chung được không?

Có. File `persona.yaml` được gitignore — mỗi developer có phong cách tương tác riêng. Tri thức chung (`knowledge-snapshot.md`, `conventions.yaml`, `author-dna.yaml`) được commit và version-controlled.

---

## Đóng góp

Dự án đang được phát triển tích cực. Hoan nghênh mọi đóng góp:

1. Fork repository
2. Tạo feature branch
3. Gửi pull request với mô tả rõ ràng

---

## Giấy phép

MIT License — xem [LICENSE](LICENSE) để biết chi tiết.

---

<p align="center">
  <i>Xây dựng với ❤️ cho AI-assisted software engineering</i>
</p>
