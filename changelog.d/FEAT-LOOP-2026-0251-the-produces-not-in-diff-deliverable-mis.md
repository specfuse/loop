---
class: changed
trace: FEAT-LOOP-2026-0251
---
The `produces_not_in_diff`, `deliverable_missing` and `no_deliverable_files` refusals now run before the verification gates, so a refused attempt pays for no gate run. An attempt that also would have failed a gate, or `files_changed_mismatch`, is now reported as the deliverable refusal instead
