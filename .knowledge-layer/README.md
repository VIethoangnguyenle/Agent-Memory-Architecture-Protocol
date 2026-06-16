# .knowledge-layer — Working Memory cho Agent

> **Setup note**: Sau khi unzip, chạy lệnh sau để đảm bảo 2 file mới được track bởi git:
> ```bash
> git add .knowledge-layer/templates/TOKEN_LOG.tpl.md .agent/procedures/token-tracking.md
> ```


## Mục đích

`.knowledge-layer` là **bộ nhớ làm việc** của agent trong flow:

> **Ideation → Requirement → Architecture → Spec → Apply**

Mọi skill và workflow trong `.agent/` đọc/ghi context thông qua thư mục này.

---

## Cấu trúc

```
.knowledge-layer/
├── README.md                 ← File này
├── templates/                ← Template cố định + knowledge tích luỹ
│   ├── knowledge-snapshot.md ← Tích luỹ qua nhiều task (không reset)
│   ├── ideation.md           ← Template cho file ideation
│   ├── feature.md            ← Checklist cho task feature
│   ├── fixbug.md             ← Checklist cho task fixbug
│   ├── refactor.md           ← Checklist cho task refactor
│   └── changerequest.md      ← Checklist cho change request
└── active/                   ← Context ĐANG DÙNG cho task hiện tại
    ├── REQUIREMENT.md         ← Yêu cầu chuẩn hoá
    ├── EXPLORE_CONTEXT.md     ← Kết quả khám phá DB + code + kiến trúc
    ├── AGENT_TRANSPARENCY.md  ← Audit: nguồn đã đọc, tool đã gọi, cảnh báo
    └── ideation/              ← File ideation cho ý tưởng thô
```

---

## Quy ước path

Tất cả path được quy ước tại `.agent/rules/RULES.md`, section "Path Convention".

Tóm tắt nhanh:

| File | Path đầy đủ |
|------|-------------|
| REQUIREMENT | `.knowledge-layer/active/REQUIREMENT.md` |
| EXPLORE_CONTEXT | `.knowledge-layer/active/EXPLORE_CONTEXT.md` |
| AGENT_TRANSPARENCY | `.knowledge-layer/active/AGENT_TRANSPARENCY.md` |
| Knowledge Snapshot | `.knowledge-layer/long-term/knowledge-snapshot.md` |
| Ideation | `.knowledge-layer/active/ideation/ideation-*.md` |

---

## Lifecycle

1. **Bootstrap**: Workflow `/task` tạo/reset file trong `active/` từ template khi bắt đầu task mới.
2. **Tích luỹ**: Các skill ghi dần vào `active/` qua từng pha.
3. **Kết thúc**: Sau khi apply xong, context trong `active/` có thể được archive hoặc reset.

---

## Git strategy

- `templates/` + `README.md`: **COMMIT** vào git (cấu trúc cố định).
- `active/`: **GITIGNORE** (context tạm, per-session, không nên commit).
