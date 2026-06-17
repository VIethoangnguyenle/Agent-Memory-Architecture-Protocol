# Hybrid Contract DAG Subagent Coding: Design Spec

> Ngay: 2026-06-18  
> Pham vi: Nang cap Pha 3 `/task apply` cua AMAP cho codebase lon, phuc tap.  
> Phu thuoc: SP1a mechanical gate, SP1b coding micro-loop, SP1c outcome loop.  
> Nguon: brainstorming ve AMAP internal product + nhu cau knowledge-first voi Understand-Anything, db-explorer, agent long-term memory.

---

## 1. Bai toan

AMAP hien tai da giai quyet tot cac pha truoc coding:

```txt
Ideation -> Requirement -> Architecture -> Spec
```

O cac pha nay, agent co du thoi gian de doc `REQUIREMENT.md`, `EXPLORE_CONTEXT.md`, `knowledge-snapshot.md`,
`conventions.yaml`, `author-dna.yaml`, codebase graph va database evidence truoc khi ket luan. Voi codebase lon,
day la loi the chinh cua AMAP: **knowledge first**, khong de agent nhay vao code dua tren tri nho hoi thoai.

Van de xay ra o Pha 3:

```txt
Spec -> Apply -> code generation
```

Khi bat dau coding, context bi lap day boi spec, code files, loi compile, diff, class vua sinh, business rule,
contract base class, test failure, wiring config, convention va author DNA. Du agent da brainstorm kien truc dung,
luc generate code no van co the quen `author-dna`, quen convention, dat logic sai layer, tao abstraction thua,
hoac viet class con khong dung contract cua base class vua duoc agent khac sinh.

Day khong phai loi "prompt chua manh". Day la loi kien truc: **judgment layer bi day ra khoi working context dung luc
can nhat**.

Muc tieu cua spec nay la nang cap Pha 3 thanh **Hybrid Contract DAG Subagent Coding**:

```txt
Spec -> Knowledge Pack -> Contract DAG -> Contract Lane -> Parallel Implementation Lane
     -> Integration Lane -> Verification Lane -> Knowledge Curator
```

Thiet ke phai giai quyet rieng case quan trong:

> Agent A sinh base/interface/contract. Agent B/C/D sinh cac class extend/implement contract do. Neu base doi,
> class con phai biet minh stale va re-run/rebase.

## 2. Nguyen tac thiet ke

### 2.1 Knowledge first la gate, khong phai ghi chu

Subagent coding khong duoc tu do "kham pha lai" codebase tu dau. No phai dung tren `Knowledge Pack` da duoc verify boi
cac tang truoc:

- Understand-Anything / Knowledge Graph: module, dependency, call graph, blast radius, entry points.
- `db-explorer`: schema, constraint, trigger, config data, routing logic DB.
- `codebase-explorer`: mapping requirement -> module/service/file.
- `architecture-reviewer`: boundary, risk, blocker, confidence.
- `knowledge-snapshot.md`: su that kien truc dai han.
- `conventions.yaml`: naming, structure, upstream constraints.
- `author-dna.yaml`: hard principles, complexity thresholds, style/judgment layer.
- archive / agent long-term memory: quyet dinh cu va bai hoc tu task tuong tu.

Coding subagent la executor co bien gioi ro. Orchestrator va knowledge layer moi la noi hieu codebase lon.

### 2.2 Task handoff nho, DNA/convention gan dung luc

Moi coding task nhan mot `TASK_HANDOFF` nho, co dinh, gom dung slice can thiet:

```txt
TASK_HANDOFF.<node-id>.md
├── task goal
├── evidence slice tu UA/KG
├── DB/schema slice neu task cham data
├── contract snapshot lien quan
├── author-dna slice bat buoc
├── convention slice bat buoc
├── architecture boundary
├── allowed files
├── read-only files
├── forbidden assumptions
├── expected output
└── validation command/gate
```

`author-dna` va `conventions` khong con la "file da doc tu dau session". Chung la input bat buoc cua tung node
coding, dat ngay canh task de giam drift.

### 2.3 Contract truoc, implementation sau

Base class, interface, abstract class, DTO/schema, enum, public/protected method signature va extension point chay
truoc. Chi khi contract pass gate va duoc freeze thanh `CONTRACT_SNAPSHOT`, leaf implementation moi duoc dispatch.

### 2.4 Parallel chi ap dung cho leaf tasks an toan

Subagent co the chay song song khi:

- khong cung ghi mot file;
- khong sua contract/base da freeze;
- dependency da pass;
- nhan cung `contract_version`;
- conflict surface nam trong allowed boundary;
- integration/wiring shared duoc gom ve mot lane rieng.

### 2.5 Thieu context thi request, khong doan

Neu subagent thay thieu context, no khong duoc suy dien hoac search lung tung. No tra ve `CONTEXT_REQUEST`.
Orchestrator quyet dinh co goi UA/KG, db-explorer, memory recall hay doc source bo sung de cap nhat `Knowledge Pack`.

## 3. Kien truc tong the

```txt
OpenSpec tasks.md
    │
    ▼
Knowledge Pack Builder
    │
    ▼
Contract DAG Builder
    │
    ├── Contract Lane          # sequential
    │       base/interface/schema/DTO/extension point
    │       -> CONTRACT_SNAPSHOT.<node-id>.md
    │
    ├── Implementation Lane    # controlled parallel
    │       child classes/adapters/mappers/repositories
    │       -> TASK_RESULT.<node-id>.md
    │
    ├── Integration Lane       # sequential or locked
    │       DI/wiring/config/registry/migration registration
    │
    └── Verification Lane
            compile/test/spec-validator/extraction review/outcome log
```

Kien truc nay la extension cua SP1b micro-loop. SP1b da co y tuong task queue, handoff, result va extraction review.
Spec nay them:

- `KNOWLEDGE_PACK.md`
- `CONTRACT_DAG.md`
- `CONTRACT_SNAPSHOT.<node-id>.md`
- `TASK_HANDOFF.<node-id>.md`
- `TASK_RESULT.<node-id>.md`
- `CONTEXT_REQUEST.<node-id>.md`
- `CONTRACT_CHANGE_REQUEST.<node-id>.md`
- `INTEGRATION_REQUEST.<node-id>.md`

## 4. Knowledge Pack

`Knowledge Pack` la context nen da duoc verify truoc Pha 3. No khong phai dump toan bo context. No la ban tom tat co
evidence va confidence.

### 4.1 Producer

`Knowledge Pack Builder` doc:

- `.knowledge-layer/active/REQUIREMENT.md`
- `.knowledge-layer/active/EXPLORE_CONTEXT.md`
- `.knowledge-layer/active/AGENT_TRANSPARENCY.md`
- `.knowledge-layer/long-term/knowledge-snapshot.md`
- `.knowledge-layer/long-term/conventions.yaml`
- `.knowledge-layer/long-term/author-dna.yaml`
- OpenSpec artifacts trong `openspec/changes/<change-id>/`
- UA/KG graph neu available
- db-explorer evidence neu task cham data
- agent-memory/archives neu requirement trung module/rule cu

### 4.2 Schema de xuat

```yaml
ticket_id: PROJ-123
change_id: add-payment-processor
confidence:
  overall: CAO
  code_graph: CAO
  database: TRUNG-BINH
  memory: CAO
sources:
  requirement: .knowledge-layer/active/REQUIREMENT.md
  explore_context: .knowledge-layer/active/EXPLORE_CONTEXT.md
  openspec: openspec/changes/add-payment-processor/
ua_kg:
  graph_status: available
  graph_timestamp: "2026-06-18T10:00:00+07:00"
  entry_points:
    - node_id: payment.PaymentController
      path: src/.../PaymentController.java
  blast_radius:
    - node_id: payment.PaymentService
      reason: called by new flow
database:
  required: true
  evidence:
    - table: PAYMENT_CONFIG
      constraints: [PK_PAYMENT_CONFIG]
architecture:
  boundaries:
    - "Do not place provider-specific business rules in shared base processor"
  risks:
    - severity: MEDIUM
      note: "Integration wiring touches shared registry"
dna:
  hard_principles: [HP-1]
  complexity_thresholds:
    max_nesting_depth: 3
    max_lines_per_method: 50
conventions:
  relevant_sections:
    - naming
    - upstream_constraints
memory:
  related_decisions:
    - source: archive/PROJ-010
      summary: "Previous provider adapters used template method in shared base"
```

### 4.3 Apply gate lien quan knowledge

Voi task complexity `complex`, Pha 3 khong nen bat dau neu:

- UA/KG graph unavailable hoac qua cu, tru khi user override ro rang;
- task cham DB nhung khong co db-explorer evidence;
- `author-dna.yaml` hoac `conventions.yaml` missing/draft;
- `EXPLORE_CONTEXT.md` la skeleton;
- architecture-reviewer co BLOCKER chua resolve.

Neu user override, `AGENT_TRANSPARENCY.md` phai ghi ro confidence ha xuong `THAP` hoac `TRUNG-BINH` va ly do.

## 5. Contract DAG

`Contract DAG` la graph tu OpenSpec `tasks.md`, co bo sung loai node, dependency, file boundary va contract version.

### 5.1 Node types

| Type | Muc dich | Parallel? |
|---|---|---|
| `contract` | base/interface/abstract class/DTO/schema/public contract | Khong, mac dinh sequential |
| `leaf` | class con/adapter/mapper/repository implementation | Co, neu khong conflict writes |
| `integration` | DI/wiring/registry/config/migration registration | Mac dinh khong |
| `test` | unit/integration/spec tests | Co, sau implementation |
| `review` | extraction review, architecture post-check | Khong |

### 5.2 Schema de xuat

```yaml
ticket_id: PROJ-123
spec_path: openspec/changes/add-payment-processor/
contract_version_counter: 3
nodes:
  - id: C1
    type: contract
    desc: "Create BasePaymentProcessor"
    depends_on: []
    reads:
      - src/.../ExistingProcessor.java
    writes:
      - src/.../BasePaymentProcessor.java
    contract_version: v1
    status: done
    gate_history: []

  - id: L1
    type: leaf
    desc: "Create CardPaymentProcessor extends BasePaymentProcessor"
    depends_on: [C1]
    reads:
      - src/.../BasePaymentProcessor.java
    writes:
      - src/.../CardPaymentProcessor.java
    contract_ref:
      node_id: C1
      version: v1
    status: pending

  - id: I1
    type: integration
    desc: "Register processors in PaymentProcessorRegistry"
    depends_on: [L1, L2]
    writes:
      - src/.../PaymentProcessorRegistry.java
    status: pending
```

### 5.3 Stale invalidation

Neu node `contract` thay doi sau khi da freeze:

1. Tang `contract_version`.
2. Mark tat ca node phu thuoc contract cu thanh `stale`.
3. Xoa hoac invalidate `TASK_RESULT` cua node stale.
4. Rebuild `TASK_HANDOFF` voi snapshot moi.
5. Resume tu node stale dau tien co dependency pass.

Khong cho leaf agent tu sua contract. Leaf agent chi duoc tra `CONTRACT_CHANGE_REQUEST`.

## 6. Subagent roles

### 6.1 Planning Orchestrator

Khong viet code. Trach nhiem:

- doc OpenSpec `tasks.md`;
- doc `Knowledge Pack`;
- build `Contract DAG`;
- xac dinh node type va dependency;
- xac dinh allowed/read-only files;
- tinh parallel batches;
- dispatch subagent theo execution mode.

### 6.2 Contract Agent

Chay truoc, gan nhu tuan tu. Sinh/sua:

- interface;
- abstract/base class;
- DTO/schema;
- enum/error code;
- public/protected method signature;
- extension point;
- template method skeleton neu can.

Output bat buoc:

- code changes;
- `CONTRACT_SNAPSHOT.<node-id>.md`;
- self-check ve invariants, allowed overrides, forbidden overrides.

### 6.3 Implementation Agent

Chay sau khi contract pass. Co the song song theo batch. Sinh/sua:

- class extend base;
- implementation class;
- adapter;
- mapper;
- repository implementation;
- provider-specific strategy.

Khong duoc:

- sua base/interface da freeze;
- sua shared registry/config;
- them dependency moi ngoai spec;
- bo qua contract_version;
- tu goi UA/db/memory.

### 6.4 Integration Agent

Chay sau implementation. Day la agent duy nhat duoc sua shared wiring files:

- DI module;
- route registry;
- config binding;
- migration registration;
- feature toggle wiring;
- service registry.

Leaf agents gui `INTEGRATION_REQUEST`; Integration Agent gom request de tranh conflict.

### 6.5 Verification Agent

Khong viet feature code. Trach nhiem:

- compile/typecheck/test;
- spec-validator pre/post checks;
- convention/DNA mechanical gate;
- architecture boundary post-check;
- extraction review;
- outcome log;
- feedback dung node neu fail.

## 7. Contract Snapshot

`CONTRACT_SNAPSHOT` la artifact quan trong nhat de giai quyet base/child dependency.

### 7.1 Noi dung bat buoc

```yaml
node_id: C1
contract_name: BasePaymentProcessor
contract_version: v1
source_file: src/.../BasePaymentProcessor.java
kind: abstract_class
constructor:
  dependencies:
    - PaymentConfigRepository
    - Clock
public_methods:
  - signature: "PaymentResult process(PaymentRequest request)"
    behavior: "Template method. Final if language allows."
protected_methods:
  - signature: "ProviderResult executeProvider(PaymentRequest request)"
    child_must_implement: true
  - signature: "void validateRequest(PaymentRequest request)"
    child_may_override: false
invariants:
  - "Shared validation runs before provider-specific execution"
  - "Audit record is emitted exactly once"
forbidden_overrides:
  - process
extension_rules:
  - "Child classes implement provider-specific execution only"
  - "Child classes must not read database configuration directly"
examples:
  - "ExistingProcessor shows retry mapping pattern"
```

### 7.2 Gate truoc khi freeze

Contract chi duoc freeze khi:

- compile/typecheck toi thieu pass neu kha dung;
- convention gate pass;
- DNA gate pass ve complexity/boundary/abstraction;
- architecture mini-check khong phat hien boundary violation;
- snapshot extractor thanh cong;
- public/protected methods ro nghia;
- invariants khong mau thuan spec.

## 8. Request protocols

### 8.1 Context Request

Khi subagent thieu context:

```yaml
node_id: L1
request_type: context
missing:
  - "Need source of ExistingProcessor retry mapping"
  - "Need DB constraint for provider config uniqueness"
suggested_tools:
  - understand-anything.get_node_source
  - db-explorer
blocked_reason: "Cannot implement provider-specific config lookup safely"
```

Orchestrator xu ly request, cap nhat `Knowledge Pack`, rebuild handoff va resume node.

### 8.2 Contract Change Request

Khi leaf thay contract thieu:

```yaml
node_id: L1
request_type: contract_change
contract_ref: { node_id: C1, version: v1 }
problem: "Base class has no protected mapper for provider error codes"
proposal: "Add protected mapProviderError(...) hook"
impact:
  affected_nodes: [L1, L2]
```

Orchestrator quyet dinh:

- reject va yeu cau leaf code theo contract hien tai;
- reopen Contract Agent de tao `v2`;
- mark downstream stale va re-run.

### 8.3 Integration Request

Leaf khong sua shared wiring. No gui:

```yaml
node_id: L1
request_type: integration
target_file: src/.../PaymentProcessorRegistry.java
requested_change: "Register CardPaymentProcessor for provider=CARD"
required_after: L1
```

Integration Agent gom cac request va sua mot lan.

## 9. Gates

### 9.1 Knowledge gate

Truoc khi coding:

- `Knowledge Pack` ton tai;
- confidence hop le voi complexity;
- DB evidence co neu task cham data;
- architecture BLOCKER da resolve;
- active requirement/explore context khong skeleton;
- DNA/conventions approved va du slice relevant.

### 9.2 Contract gate

Sau moi contract node:

- compile/typecheck toi thieu;
- convention + DNA gate;
- architecture mini-check;
- snapshot generated;
- no forbidden dependency;
- no oversized method/class theo threshold co san.

### 9.3 Leaf implementation gate

Sau moi leaf node:

- chi sua allowed files;
- khong sua contract/base;
- `contract_version` match;
- compile/typecheck hoac syntax check;
- no DNA/convention violation;
- no new abstraction ngoai spec;
- self-flagged assumptions empty hoac da duoc resolve.

### 9.4 Integration gate

Sau integration node:

- gom du `INTEGRATION_REQUEST`;
- khong duplicate registration;
- config/registry order deterministic;
- test/compile pass neu co;
- no unrelated wiring changes.

### 9.5 Verification gate

Cuoi Pha 3:

- all nodes `done`;
- no node `blocked` hoac `stale`;
- compile/test/spec-validator pass hoac co override ro rang;
- extraction review da trinh user;
- `AGENT_TRANSPARENCY.md` va `TOKEN_LOG.md` cap nhat;
- outcome log ghi neu SP1c enabled;
- chi sau do moi goi `knowledge-curator`.

## 10. State va resume

Layout de xuat:

```txt
.knowledge-layer/active/microloop/
├── KNOWLEDGE_PACK.md
├── CONTRACT_DAG.md
├── CONTRACT_SNAPSHOT.C1.md
├── TASK_QUEUE.md
├── TASK_HANDOFF.L1.md
├── TASK_RESULT.L1.md
├── CONTEXT_REQUEST.L1.md
├── CONTRACT_CHANGE_REQUEST.L1.md
├── INTEGRATION_REQUEST.L1.md
└── EXTRACTION_REPORT.md
```

Resume behavior:

1. Bootstrap doc `AGENT_TRANSPARENCY.md`.
2. Neu dang Pha 3, doc `CONTRACT_DAG.md` va `TASK_QUEUE.md`.
3. Node `done` giu nguyen.
4. Node `in_progress` tu session truoc chuyen ve `pending` neu chua co result hop le.
5. Node phu thuoc contract version cu chuyen thanh `stale`.
6. Rebuild handoff cho node pending/stale dau tien co dependency pass.
7. Tiep tuc theo execution mode hien tai.

State nam tren filesystem, khong nam trong context hoi thoai.

## 11. Tich hop vao AMAP hien tai

### 11.1 Khong thay flow chinh

Giu nguyen:

```txt
Ideation -> Requirement -> Architecture -> Spec -> Apply
```

Giu OpenSpec Pha 2 va knowledge-first Pha 1. Chi nang cap Pha 3.

### 11.2 Thay doi can co

| File/khu vuc | Thay doi |
|---|---|
| `.agent/workflows/task.md` Pha 3 | Thay micro-loop don bang Hybrid Contract DAG micro-loop |
| `.agent/tools/microloop-orchestrator/` | Them Knowledge Pack, Contract DAG, request protocols, stale invalidation |
| `.agent/procedures/executor.md` | Cap nhat executor theo role-specific handoff |
| `.agent/procedures/reviewer.md` | Cap nhat verification/extraction role |
| `.agent/profiles/execution-mode.yaml` | Giu 3 tier: `subagent`, `fresh-session`, `inline-reload` |
| `.agent/skills/spec-validator/SKILL.md` | Them checks contract_version, stale node, integration request coverage |
| `.agent/rules/rules-tool.md` | Lam ro subagent khong tu goi UA/db/memory; orchestrator moi duoc bo sung Knowledge Pack |
| `.agent/rules/rules-exec.md` | Them budget cho context request va parallel batch |
| `.knowledge-layer/templates/` | Them templates cho Knowledge Pack, Contract DAG, request files |

### 11.3 Execution mode

`inline-reload` van la fallback hop le, nhung voi internal product/codebase lon nen uu tien:

1. `subagent` neu platform co isolation that;
2. `fresh-session` neu IDE ho tro session moi;
3. `inline-reload` chi dung khi khong co cach khac, va phai dua `author-dna`/convention slice vao handoff sat task.

## 12. Error handling

| Tinh huong | Xu ly |
|---|---|
| KG unavailable voi task complex | Block hoac user override; confidence ha xuong |
| DB evidence thieu voi task cham data | Block Pha 3, yeu cau db-explorer |
| Contract gate fail | Retry toi da 2 lan; van fail thi node `blocked` |
| Leaf can sua contract | Tao `CONTRACT_CHANGE_REQUEST`, khong tu sua |
| Contract version doi | Mark downstream `stale` |
| Shared wiring conflict | Doi sang `INTEGRATION_REQUEST`; chi Integration Agent sua |
| Subagent thieu context | Tao `CONTEXT_REQUEST`; orchestrator bo sung Knowledge Pack |
| Test fail sau integration | Verification Agent route feedback ve node lien quan |
| Session truncate | Resume tu filesystem state |

## 13. Testing strategy

### 13.1 Unit tests

- topo-sort theo node type va dependency;
- detect write conflicts de tinh parallel batch;
- stale invalidation khi contract version doi;
- validate `Knowledge Pack` schema;
- validate `Contract Snapshot` schema;
- validate request protocols;
- ensure leaf cannot write contract files;
- ensure integration files chi duoc sua boi integration node.

### 13.2 Fixture tests

Tao fixture spec co:

- 1 base class;
- 2 child implementations;
- 1 shared registry;
- 2 unit tests.

Expected:

- base chay truoc;
- 2 child co the song song;
- registry chay sau child;
- neu base doi `v1 -> v2`, child nodes stale;
- request protocol khong lam mat state;
- final verification pass.

### 13.3 Regression tests cho context drift

Test handoff phai luon chua:

- `author-dna slice`;
- `convention slice`;
- `contract snapshot` neu node co contract_ref;
- `Knowledge Pack` evidence slice;
- allowed/read-only file boundary.

## 14. Non-goals

- Khong thiet ke full multi-agent marketplace.
- Khong cho subagent tu do truy cap DB/KG/memory.
- Khong thay OpenSpec Pha 2.
- Khong yeu cau moi platform phai co subagent real.
- Khong giai quyet conflict merge tong quat ngoai boundary cua task graph.
- Khong tu dong refactor theo extraction review khi user chua approve.

## 15. Rollout plan de xuat

1. **SP1d-1: Contract DAG artifacts**
   - Them schema + templates + validator cho `KNOWLEDGE_PACK`, `CONTRACT_DAG`, `CONTRACT_SNAPSHOT`.

2. **SP1d-2: Orchestrator upgrade**
   - Mo rong microloop-orchestrator de build DAG, batch leaf nodes, stale invalidation.

3. **SP1d-3: Request protocols**
   - Them `CONTEXT_REQUEST`, `CONTRACT_CHANGE_REQUEST`, `INTEGRATION_REQUEST`.

4. **SP1d-4: Workflow integration**
   - Cap nhat `.agent/workflows/task.md` Pha 3 va procedures executor/reviewer.

5. **SP1d-5: Gate integration**
   - Cap nhat spec-validator va tests cho contract_version, allowed files, integration ownership.

6. **SP1d-6: Docs and examples**
   - Them worked example cho base + child + integration registry.

## 16. Open questions da chot mac dinh

| Cau hoi | Quyet dinh mac dinh |
|---|---|
| Co cho leaf agent sua base neu thay thieu hook? | Khong. Tao `CONTRACT_CHANGE_REQUEST`. |
| Co cho subagent goi UA/db/memory truc tiep? | Khong. Orchestrator bo sung `Knowledge Pack`. |
| Co parallel contract nodes khong? | Mac dinh khong; chi cho phep neu khong co dependency va khong shared API. |
| Shared wiring ai sua? | Integration Agent duy nhat. |
| KG unavailable co block khong? | Block voi task complex, override phai ghi transparency/confidence. |
| Inline reload co con dung duoc khong? | Co, nhung la fallback; state va handoff van bat buoc. |

## 17. Success criteria

Thiet ke thanh cong khi:

- Pha 3 khong con phu thuoc agent "nho" author-dna/convention tu dau session.
- Base/interface contract duoc freeze va versioned truoc khi child implementation chay.
- Child implementation stale khi contract doi.
- Subagent thieu context thi request thay vi doan.
- Shared wiring khong bi nhieu agent sua cung luc.
- Codebase lon van giu knowledge-first: UA/KG, db-explorer, long-term memory la nguon evidence truoc coding.
- Workflow van portable giua `subagent`, `fresh-session`, `inline-reload`.
- State resume duoc sau session truncate.
