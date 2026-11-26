---
class: changed
trace: FEAT-LOOP-2026-0251
---
The `produces_not_in_diff`, `deliverable_missing` and `no_deliverable_files` refusals now run before the verification gates, so a refused attempt pays for no gate run. An attempt that also would have failed a gate, `files_changed_mismatch`, the smoke-import check, a closing-deliverable guard, the blocked-verdict check, the squash commit or any other check that runs after the agent session is now reported as the deliverable refusal instead. By default such an attempt keeps its working tree (`defaults.retain_on_guard_refusal`), even where the other refusal would have reset it
