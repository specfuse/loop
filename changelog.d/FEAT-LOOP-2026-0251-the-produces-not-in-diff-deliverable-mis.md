---
class: changed
trace: FEAT-LOOP-2026-0251
---
The `produces_not_in_diff`, `deliverable_missing` and `no_deliverable_files` refusals now run before the verification gates, so a refused attempt pays for no gate run. An attempt that also would have failed a gate, `files_changed_mismatch`, the smoke-import check, a closing-deliverable guard or the blocked-verdict check is now reported as the deliverable refusal instead
