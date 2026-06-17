---
ticket_id: "<!-- ABC-123 -->"
archived_at: "<!-- 2026-MM-DD HH:mm +07 -->"
status: "<!-- completed | stashed | cancelled -->"
phase_at_archive: "<!-- phase_state từ AGENT_TRANSPARENCY.md -->"
task_type: "<!-- feature | fixbug | refactor | changerequest -->"
---

# ARCHIVE_META — {ticket_id}

## Summary

<!-- 1-2 câu: task làm gì, output chính là gì -->

## Flags

```yaml
conv_rescan_required: false   # true nếu task_type=refactor — R-Conv-5
dna_revalidation_suggested: false  # true nếu ≥2 refactor tasks kể từ last DNA scan — L5
violations_tracked: 0         # số violation patterns ghi nhận trong phiên — M3
calibration_status: "no-data" # done | no-data | pending — M6 TOKEN_LOG calibration
spec_validator_result: "n/a"  # pass | block | n/a — M1
```

## Token Estimate

```yaml
pha_1: "~Xk tokens"
pha_2: "~Xk tokens"
pha_3: "~Xk tokens"
total: "~Xk tokens"
# Nguồn: TOKEN_LOG.md — xem file đầy đủ trong archive này
```

## Stash Note

<!-- Chỉ điền khi status=stashed -->
<!-- stash_reason: -->
<!-- hot_swap_ticket: -->
