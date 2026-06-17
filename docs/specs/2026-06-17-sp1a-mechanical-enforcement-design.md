# SP1a — Mechanical Enforcement Layer: Design Spec

> Ngày: 2026-06-17 · Sub-project 1a của chương trình AMAP v4 (tách từ SP1).
> Phụ thuộc: SP0 (đã xong — `.knowledge-layer/long-term/`, `.agent/tools/` reserved).
> Unblock: SP1b (coding micro-loop dùng gate này làm tầng dưới).
> Nguồn: brainstorming 2026-06-16/17 ([AMAP-v3-assessment.md](../AMAP-v3-assessment.md) §4).

---

## 1. Mục tiêu

Biến phần **kiểm-tra-được-bằng-máy** của `author-dna.yaml` + `conventions.yaml` thành một
**gate deterministic** chạy ở git pre-commit của dự án Java đích — để rule cơ học (zero-nesting,
no-else, max-lines, max-branches, naming, javadoc) **không thể bị agent bỏ qua** trong lúc generate code.

Giải trực tiếp triệu chứng W1/W2 (deterministic guardrail chạy bằng prose) và một nửa bệnh Pha 3
("agent không tuân author-dna khi coding").

**Nguyên lý:** DNA (YAML) = source of truth người-đọc-được → Rule Projector sinh ra ruleset
máy-tối-ưu (derived, regenerate khi nguồn đổi, sync-check chống lệch pha). Đồng nhất với nguyên
lý đã áp ở toàn hệ thống.

## 2. Phạm vi

**In scope (SP1a):**
- Định nghĩa schema `mechanically_checkable: bool` + `check_spec` — **hợp đồng giữa producer
  (`author-dna-builder`) và consumer (`rule-projector`)**.
- Cập nhật skill `author-dna-builder` (+ `convention-intelligence-builder` nếu cần) để **EMIT**
  `check_spec` khi sinh DNA lúc setup. (DNA không hand-edit — xem §3.1.)
- Cập nhật **sample** `author-dna.yaml` trong repo để minh hoạ schema mới.
- Rule Projector (`projector.py`): `author-dna.yaml` + `conventions.yaml` → IR JSON trung lập.
  Sàn nền = chiếu cấu trúc (`complexity_thresholds` + naming); `check_spec` là enrichment tuỳ chọn.
- Checkstyle backend (`backends/checkstyle.py`): IR → `checkstyle.generated.xml`.
- IR JSON Schema (`ir_schema.json`) để validate IR.
- git pre-commit hook template + installer cho dự án Java đích.
- Sync-check (DNA↔ruleset không lệch pha).
- Test bằng fixture trong repo AMAP (không cần Java).

**Out of scope (KHÔNG ở SP1a):**
- Coding micro-loop / sequential subagent / extraction review → **SP1b**.
- Qdrant index cho knowledge-snapshot → SP1c / SP3.
- Backend ngôn ngữ khác ngoài Java/Checkstyle → mở rộng sau (IR đã trung lập).
- Rule ngữ nghĩa (HP-1/2/3/5/9/10/11, SOLID) → không chiếu được, để SP1b lo.

## 3. Quyết định đã chốt (brainstorming)

| Quyết định | Chọn |
|---|---|
| Lint engine | **Checkstyle** (phủ trọn rule cơ học của DNA out-of-the-box) |
| Điểm chạy gate | **git pre-commit hook** (portable mọi framework — khớp SP4) |
| Projector output | **Neutral IR (JSON) → Checkstyle backend** (đổi tool/ngôn ngữ sau chỉ thêm backend) |
| Ngôn ngữ Projector | **Python** (YAML→JSON→XML sạch, TDD nhanh; chỉ chạy lúc build/codegen) |
| HP-7 "no else" | **`forbid_else` WARN heuristic** (Checkstyle `Regexp`, không block oan) |
| Vị trí tool | `.agent/tools/rule-projector/` (nhà đã reserve ở SP0) |

### 3.1 Mô hình generation của DNA (ràng buộc nền)

`author-dna.yaml` / `conventions.yaml` trong repo AMAP **chỉ là file mẫu minh hoạ**. Ở dự án thật,
chúng được **build ra lúc setup lần đầu** bởi `author-dna-builder` / `convention-intelligence-builder`
(interview + `/approve-dna`), rồi user duyệt — **và tiếp tục cập nhật theo thời gian** (R-DNA-7
teaching moment, `knowledge-curator` rescan). DNA là **file sống**. Hệ quả cho SP1a:

- **Không hand-edit `check_spec` vào DNA.** Schema mới là **hợp đồng**: producer emit, `rule-projector`
  (consumer) đọc.
- **Hợp đồng producer áp dụng cho CẢ đường update, không chỉ setup.** Bất kỳ path nào ghi DNA —
  `author-dna-builder` (setup/rescan) HOẶC R-DNA-7/`knowledge-curator` (teaching moment) — khi thêm/
  sửa một principle cơ học thì PHẢI emit/refresh `check_spec` tương ứng.
- **Projector phải robust khi DNA thiếu `check_spec`.** Sàn nền = chiếu cấu trúc từ
  `complexity_thresholds` + `conventions.naming_patterns` (field generator LUÔN sinh).
  `check_spec` là enrichment tuỳ chọn cho principle thêm (HP-7, javadoc). Thiếu → rớt xuống
  semantic (SP1b lo), KHÔNG vỡ.
- Sample DNA trong repo chỉ cập nhật để **minh hoạ** schema.

### 3.2 Vòng đời regeneration (DNA sống → ruleset luôn tươi)

```
DNA thay đổi (setup | rescan | R-DNA-7 teaching moment)
   │
   ├─ [chủ động] flow ghi DNA gọi `projector.py` regen NGAY
   │            → ruleset mới áp dụng cho code tiếp theo trong cùng session (đóng vòng lặp)
   │
   └─ [backstop] nếu path nào quên regen → git pre-commit sync-check phát hiện
                source_hash lệch → BLOCK: "DNA đổi, chạy rule-projector"
```

- **Chủ động**: R-DNA-7 capture (rules-guard) và `author-dna-builder` rescan, sau khi ghi DNA
  (approved), gọi `projector.py` để regenerate ruleset trong cùng session.
- **Backstop**: sync-check (§8) đảm bảo ruleset KHÔNG BAO GIỜ stale kể cả khi bước chủ động bị bỏ.
- Hai lớp này = "sandwich" cho tính tươi của ruleset, đồng dạng sandwich defense của DNA-RELOAD.

## 4. Kiến trúc & luồng dữ liệu

```
.knowledge-layer/long-term/author-dna.yaml   ┐ (status: approved)
.knowledge-layer/long-term/conventions.yaml  ┘ (status: approved; draft → SKIP)
        │
        ▼
[1] projector.py
      - đọc complexity_thresholds (chiếu trực tiếp)
      - đọc hard_principles/style_preferences có mechanically_checkable: true → check_spec
      - đọc conventions naming_patterns
      - chỉ lấy entry status=approved
        │
        ▼
    IR: rules.json  (+ source_hash = sha256(author-dna.yaml + conventions.yaml))
        │  validate bằng ir_schema.json
        ▼
[2] backends/checkstyle.py  →  checkstyle.generated.xml  (header nhúng source_hash)
        │
        ▼
[3] git pre-commit (ở dự án Java đích, cài bằng install.sh):
      ├─ sync-check: sha hiện tại của DNA == source_hash trong xml? Lệch → BLOCK
      └─ checkstyle -c checkstyle.generated.xml <staged .java> → vi phạm error → BLOCK
```

## 5. Schema mở rộng cho `author-dna.yaml`

### 5.1 Nguồn 1 — `complexity_thresholds` (chiếu trực tiếp, không cần khai báo thêm)

Projector có bảng built-in map các key đã biết → IR:

| key trong DNA | IR rule | severity |
|---|---|---|
| `max_nesting_depth: 1` | `max_if_nesting {max:1}` + `max_for_nesting {max:0}` | error |
| `max_method_branches: 3` | `max_cyclomatic {max:3}` | warning |
| `max_lines_per_method: 30` | `max_method_lines {max:30}` | warning |

### 5.2 Nguồn 2 — `hard_principles` / `style_preferences` (khai báo tường minh)

Mỗi entry **có thể** thêm 2 field. Entry không có `mechanically_checkable: true` → Projector bỏ qua
(coi là semantic, để SP1b lo).

```yaml
- id: HP-6
  name: "Zero Nesting"
  agent_action: REJECT_AND_PROPOSE      # REJECT_* → severity=error; FLAG_* → warning
  mechanically_checkable: true
  check_spec:
    - ir_rule: max_if_nesting
      params: { max: 1, guard_exception: true }
    - ir_rule: max_for_nesting
      params: { max: 0 }

- id: HP-7
  name: "No Else"
  agent_action: REJECT_AND_PROPOSE
  mechanically_checkable: true
  check_spec:
    - ir_rule: forbid_else
      params: { severity_override: warning }   # heuristic → hạ xuống WARN

- id: SP-5
  name: "Javadoc @author/@since"
  mechanically_checkable: true
  check_spec:
    - ir_rule: require_javadoc_tag
      params: { tags: ["@author", "@since"], scope: ["public", "protected"] }
```

**Quy ước severity:** `agent_action` bắt đầu `REJECT_` → `error` (BLOCK commit); `FLAG_` → `warning`;
`params.severity_override` thắng nếu có.

### 5.3 `conventions.yaml` → naming

`naming_patterns[]` (status=approved) → IR `naming_regex { target: TypeName|MethodName|..., pattern: <regex> }`.

## 6. IR (Intermediate Representation)

`rules.json`:
```json
{
  "version": "1.0",
  "generated_at": "<ISO8601>",
  "source_hash": "<sha256 của author-dna.yaml + conventions.yaml đã nối>",
  "sources": [".knowledge-layer/long-term/author-dna.yaml",
              ".knowledge-layer/long-term/conventions.yaml"],
  "rules": [
    {"id": "HP-6.if", "ir_rule": "max_if_nesting", "severity": "error",
     "params": {"max": 1, "guard_exception": true}, "source_ref": "author-dna.yaml#HP-6"},
    {"id": "threshold.method_lines", "ir_rule": "max_method_lines", "severity": "warning",
     "params": {"max": 30}, "source_ref": "author-dna.yaml#complexity_thresholds"}
  ]
}
```

`ir_schema.json` (JSON Schema draft 2020-12) validate: `version`, `source_hash`, `rules[]` với
`id`, `ir_rule` (enum các rule hỗ trợ), `severity` (enum error|warning|info), `params` (object),
`source_ref`.

**Danh sách `ir_rule` hỗ trợ ở SP1a** (enum đóng — backend lạ rule sẽ ERROR, không drop âm thầm):
`max_if_nesting`, `max_for_nesting`, `max_method_lines`, `max_cyclomatic`, `forbid_else`,
`naming_regex`, `require_javadoc_tag`.

## 7. Checkstyle backend — bảng mapping

| IR rule | Checkstyle module | Ghi chú |
|---|---|---|
| `max_if_nesting` | `NestedIfDepth` (`max`) | `guard_exception` → Checkstyle tính guard clause là 0, khớp sẵn |
| `max_for_nesting` | `NestedForDepth` (`max`) | |
| `max_method_lines` | `MethodLength` (`max`, `countEmpty=false`) | |
| `max_cyclomatic` | `CyclomaticComplexity` (`max`) | xấp xỉ "branches" |
| `forbid_else` | `Regexp` (`format="\\}\\s*else"`, `illegalPattern=true`) | **heuristic WARN** |
| `naming_regex` | `TypeName`/`MethodName`/`MemberName`/`ConstantName` (`format`) | chọn module theo `target` |
| `require_javadoc_tag` | `RegexpSingleline` cho từng tag + `JavadocMethod`/`JavadocType` scope | đảm bảo có @author/@since |

Backend sinh `checkstyle.generated.xml` chuẩn DTD Checkstyle, mỗi module gắn comment
`<!-- from: author-dna.yaml#HP-6 -->` để trace ngược.

## 8. git hook + installer (cho dự án Java đích)

**`hooks/pre-commit.sh`** (template):
```sh
#!/bin/sh
# 1. Sync-check
CUR=$(cat <dna> <conventions> | sha256sum | cut -d' ' -f1)
EMB=$(grep -o 'source_hash=[a-f0-9]*' checkstyle.generated.xml | cut -d= -f2)
[ "$CUR" != "$EMB" ] && { echo "⛔ DNA đổi nhưng ruleset chưa regen — chạy rule-projector"; exit 1; }
# 2. Checkstyle trên file .java staged
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.java$')
[ -n "$FILES" ] && checkstyle -c checkstyle.generated.xml $FILES || exit 0
```

**`install.sh`**: copy `pre-commit.sh` vào `.git/hooks/`, set +x; sinh ruleset lần đầu;
ghi đường dẫn DNA/conventions (configurable cho dự án đích). Idempotent.

> Trong repo AMAP (không có Java), installer chỉ verify cú pháp + sinh fixture-based output.
> Việc Checkstyle chạy thật verify ở dự án Springboot đích.

## 9. File layout

```
.agent/tools/rule-projector/
├── projector.py              # đọc DNA+conventions → IR (entrypoint CLI)
├── backends/
│   ├── __init__.py
│   └── checkstyle.py         # IR → checkstyle.generated.xml
├── ir_schema.json            # JSON Schema cho IR
├── hooks/pre-commit.sh       # template hook cho dự án Java
├── install.sh                # cài hook + sinh ruleset vào target project
├── generated/                # output (gitignored trong AMAP; ở target project commit kèm)
│   └── .gitkeep
├── tests/
│   ├── fixtures/
│   │   ├── sample-author-dna.yaml
│   │   ├── sample-conventions.yaml
│   │   ├── expected-ir.json
│   │   └── expected-checkstyle.xml
│   └── test_projector.py
├── requirements.txt          # pyyaml, jsonschema
└── README.md
```

## 10. Test strategy (TDD trong repo AMAP, không cần Java)

- **Unit (projector):** `sample-author-dna.yaml` + `sample-conventions.yaml` → assert IR khớp
  `expected-ir.json` (trừ `generated_at`).
- **Unit (backend):** `expected-ir.json` → assert XML khớp `expected-checkstyle.xml` (normalize whitespace).
- **Schema:** IR sinh ra validate pass `ir_schema.json`; IR có `ir_rule` lạ → validate FAIL.
- **Sync-check:** sửa `sample-author-dna.yaml` → `source_hash` đổi → hook script phát hiện lệch (test bằng shell).
- **Severity mapping:** entry `REJECT_*` → `error`; `FLAG_*` → `warning`; `severity_override` thắng.
- **Skip draft:** entry/conventions `status != approved` → KHÔNG vào IR.

## 11. Verification (định nghĩa "done")

1. `python projector.py` trên fixture sinh IR validate pass `ir_schema.json`.
2. `pytest tests/` xanh toàn bộ (projector + backend + schema + severity + skip-draft).
3. `expected-checkstyle.xml` parse được bằng parser XML chuẩn (well-formed, đúng DTD Checkstyle).
4. Sync-check: đổi 1 byte trong `sample-author-dna.yaml` mà không regen → `pre-commit.sh` exit 1.
5. `forbid_else` sinh đúng module `Regexp` severity=warning.
6. Mọi module trong XML có comment `from: <source_ref>` trace ngược về DNA.
7. Chạy projector trên **sample** `author-dna.yaml` (đã minh hoạ `check_spec`) → sinh ruleset không lỗi.
8. Chạy projector trên DNA **không có** `check_spec` (chỉ có `complexity_thresholds` + naming) →
   vẫn sinh ruleset hợp lệ từ sàn nền cấu trúc (robust khi thiếu enrichment).
9. `author-dna-builder` + `knowledge-curator` SKILL.md có chỉ thị: sau khi ghi DNA approved →
   gọi `projector.py` regen ruleset (vòng đời §3.2 — đường chủ động).

## 12. Thay đổi file ngoài tool

- **`.agent/skills/author-dna-builder/SKILL.md`** (+ references): dạy generator **EMIT**
  `mechanically_checkable` + `check_spec` cho principle nó nhận diện là cơ học (vd nesting,
  no-else, javadoc, thresholds). Đây là phần "producer" của hợp đồng schema (§3.1). Bổ sung
  bảng "principle → ir_rule" để generator tra cứu khi sinh DNA.
- **Đường update DNA** (`rules-guard` R-DNA-7 + `knowledge-curator`): khi capture teaching moment
  thêm/sửa principle cơ học → emit/refresh `check_spec` VÀ gọi `projector.py` regen ruleset
  (vòng đời §3.2). Cập nhật chỉ thị trong các skill/rule tương ứng.
- **Sample** `.knowledge-layer/long-term/author-dna.yaml`: cập nhật để **minh hoạ** schema mới
  (HP-6, HP-7, SP-5 + thresholds đã có `check_spec`). Chỉ là ví dụ — KHÔNG phải DNA dự án thật.
- `.gitignore` (repo AMAP): thêm `.agent/tools/rule-projector/generated/*` (trừ `.gitkeep`).
- `.agent/tools/README.md`: cập nhật trỏ tới `rule-projector/`.
- (Tuỳ chọn) `convention-intelligence-builder`: nếu naming_patterns cần field projection thêm.

## 13. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|---|---|
| `forbid_else` heuristic false-positive (vd chuỗi `} else` trong comment/string) | Để WARN không BLOCK; ghi rõ là heuristic; SP1b semantic check bù |
| Checkstyle `NestedIfDepth` đếm guard clause khác kỳ vọng HP-6 | Test với fixture Java mẫu ở target project; tinh chỉnh param |
| Thêm runtime Python vào dự án Java | Chỉ chạy lúc build/codegen, không vào app; document trong install.sh |
| DNA dùng `ir_rule` chưa hỗ trợ | Enum đóng trong schema → ERROR sớm, không drop âm thầm |
| Sync-check bị bypass (hook không cài) | install.sh là bước bắt buộc; CI backstop (ngoài SP1a) verify lại |

## 14. Không phá vỡ điều gì

- Không sửa logic skill/workflow/rule hiện có.
- `author-dna.yaml` chỉ **thêm** field optional — entry cũ không có `check_spec` vẫn hợp lệ.
- Gate chỉ chạy ở dự án Java đích; repo AMAP không bị ảnh hưởng runtime.
