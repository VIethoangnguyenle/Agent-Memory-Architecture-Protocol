# adapters/ — Adapter Layer (SP3)

Abstraction layer giữa **skill logic** và **platform capabilities**.

## Cấu trúc

```
adapters/
├── README.md              ← File này
├── capabilities.yaml      ← Định nghĩa abstract operations
├── registry.yaml          ← Active provider selection + detection order
└── providers/             ← Provider configs (1 file / provider)
    ├── kg-mcp.yaml        ← Knowledge Graph MCP (priority 1)
    ├── socraticode.yaml   ← Socraticode MCP (priority 2)
    ├── grep-fallback.yaml ← Grep/file search (priority 3, always available)
    ├── db-remote.yaml     ← Database access
    └── confluence.yaml    ← Document/wiki search
```

## Cách hoạt động

1. **Skills** tham chiếu abstract operations: `code_exploration.search_code(query=...)`
2. **Agent** đọc `registry.yaml` → resolve tới provider cụ thể theo detection order
3. **Provider config** map abstract operation → concrete tool call
4. Agent gọi tool thực tế và ghi provider đã dùng vào AGENT_TRANSPARENCY

## Thêm provider mới

1. Tạo file `providers/<provider-name>.yaml`
2. Map các operations từ capability tương ứng
3. Thêm vào `detection_order` trong `registry.yaml`
4. Agent sẽ auto-detect ở lần gọi tiếp theo

## Quy tắc

- Skills **KHÔNG** hardcode tên tool cụ thể — luôn dùng abstract operations
- Provider config **KHÔNG** chứa logic — chỉ mapping
- Detection chạy **1 lần** đầu phiên, cache kết quả
- Confidence level gắn liền với provider (CAO/TRUNG BÌNH/THẤP)
