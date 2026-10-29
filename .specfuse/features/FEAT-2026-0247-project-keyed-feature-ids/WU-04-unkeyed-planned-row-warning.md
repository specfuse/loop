---
id: FEAT-2026-0247/T04
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 1.50
produces:
  - specfuse/loop/lint_roadmap.py
  - tests/test_lint_roadmap_unkeyed_rows.py
  - tests/test_keyed_feature_ids_end_to_end.py
---

# T04 — with a key set, an unkeyed planned row draws a WARN

**Objective.** A repo that adopted a key is told when a new feature was still allocated
the old way, without anything firing on its legacy history.

**Context.** `FEAT-2026-0247/T04`. This unit **edits** `lint_roadmap.py` and the oracle
module T01 created. When `layout.get(ids.key)` is set, every roadmap row whose status is
`planned` and whose ID has no key produces one `warn` finding naming the ID and the
configured key, and pointing at `python3 -m specfuse.loop.ids migrate --planned-only`.
Rows of any other status are exempt. No key configured: no finding, ever (PLAN.md
§ Escalation-predicate satisfiability).

Un-skip the oracle's clause-5 class.

**Acceptance criteria.**

1. `tests/test_lint_roadmap_unkeyed_rows.py`: fires on an unkeyed `planned` row with a
   key set (positive control); silent for the same row with no key; silent for unkeyed
   `done`, `active`, `abandoned`, `blocked`, `deferred` rows with a key; silent for a
   keyed `planned` row. The firing case fails before, passes after. The finding is
   `warn`, never `error`.
2. `lint_roadmap` over this repository (no key) reports no new finding.

**Do not touch.** Every other lint_roadmap invariant. `ids.py`. The migrate command
(T05) beyond naming it in the message.

**Verification.** The narrow tier for `implementation`.

**Escalation triggers.** If the roadmap table's status column cannot be read without
re-parsing logic another invariant already owns, reuse that parse; a second row parser
is a finding.
