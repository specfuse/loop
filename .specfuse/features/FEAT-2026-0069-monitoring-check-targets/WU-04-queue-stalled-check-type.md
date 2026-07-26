---
id: FEAT-2026-0069/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
produces:
  - specfuse/loop/lint_monitoring.py
  - .specfuse/monitoring.yml.example
  - specfuse/loop/data/monitoring.yml.example
  - docs/concepts/monitoring-schema.md
  - tests/test_lint_monitoring.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.4.0
started_at: 2026-07-26T18:07:32.565461+00:00
duration_seconds: 449.024
cost_usd: 1.210959
input_tokens: 6751
output_tokens: 11837
---

# Add the `queue-stalled` check type

**Objective.** Add `queue-stalled` to the neutral check-type set, with `targets` required
from birth, so that a wedged consumer — invisible today to `dlq`, `heartbeat`, and
`invariant` alike — becomes expressible (issue #247).

**Context.** This is `FEAT-2026-0069/T04`. Read `PLAN.md` in this folder for the axis
distinction and the scope boundary.

The gap this closes: a consumer that has stopped consuming produces **no** dead-lettered
message (nothing failed — nothing was attempted), **no** missed heartbeat (the host
process is alive and reporting), and **no** error log. It is invisible to every existing
check type. It is also invisible to `invariant`, and the reason is structural rather than
incidental: queue depth is a **broker** coordinate, and `invariant` runs a telemetry
query. A telemetry query cannot see it.

`targets` are required on `queue-stalled` **from birth**. A wedged consumer on a
20-subscription host raises the identical "which one" question that motivated this whole
feature; shipping the new type permissive would repeat, in the same release, the exact
mistake the release is correcting. There is no back-compat argument against it either —
nothing in the world carries a `queue-stalled` check yet.

**The coupling that shapes this WU** (enumerated in `PLAN.md`'s §10 note): two existing
tests bind the enum to two documents.

```
tests/test_monitoring_example.py:59   assertEqual(seen_types, set(CHECK_TYPES))
tests/test_monitoring_example.py:94   assertEqual(documented_types, set(CHECK_TYPES))
```

The first asserts the shipped example exercises **every** member of `CHECK_TYPES`; the
second asserts the docs table documents every member. So adding one enum member turns
both red instantly. **This WU is therefore atomic: enum + example block + docs row in one
pass.** It cannot be split, and attempting to split it leaves the tree red between
commits — which the driver cannot squash.

Remember both example copies are byte-identical and must move together
(`.specfuse/monitoring.yml.example` and `specfuse/loop/data/monitoring.yml.example`).

Binding rules in `.specfuse/rules/` apply.

**Acceptance criteria.**

1. `tests/test_lint_monitoring.py::TestQueueStalled::test_queue_stalled_is_a_known_check_type`
   exists and **fails on HEAD before this WU's edits** — the type is not in `CHECK_TYPES`,
   so a config using it produces an unknown-check-type finding.
2. After this WU's edits that test passes.
3. A `queue-stalled` check **without** `targets` produces exactly one finding, and the
   finding names both `subscription` and `function` as the required coordinates — same
   inline-fix discipline as T03's AC3.
4. A `queue-stalled` target missing either coordinate produces exactly one finding naming
   the missing one. One test per coordinate.
5. The stall threshold coordinate is accepted and **not interpreted** — the schema does not
   parse or bound it, following the `invariant.query` precedent exactly. A test asserts an
   absurd threshold value still validates, so a later WU cannot quietly add range
   checking to this layer.
6. **Coupling A is satisfied inside this WU:** `tests/test_monitoring_example.py`'s
   existing assertions at `:59` and `:94` both pass, because the example gains a
   `queue-stalled` block and the docs table gains its row in the same change. Confirmed at
   draft time via `grep -rn "CHECK_TYPES" tests/` → `test_monitoring_example.py:17,59,94`.
7. The example's `queue-stalled` block lands on the multi-trigger host component T02
   added, with ≥ 1 target, placeholders only (`acme-*`). Its inline comment states what
   this check catches that `dlq` and `heartbeat` do not.
8. `docs/concepts/monitoring-schema.md`'s check-type table gains a `queue-stalled` row
   naming its required fields, and the prose states the broker-vs-telemetry reason
   `invariant` cannot cover it. Without that sentence the new type reads as redundant
   with `invariant` and a future author will try to collapse them.
9. `suggest_checks()` in `tests/test_derive_monitoring_discovery.py` **never** emits
   `queue-stalled` — a stall threshold is operator judgement, the same class as
   `invariant.query`. Assert it in the same shape as the existing
   `TestSuggestChecksNeverInvariant`.
10. `cmp .specfuse/monitoring.yml.example specfuse/loop/data/monitoring.yml.example` exits 0.
11. `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` exits 0.
12. `tests/test_monitoring_fenced_blocks.py` passes.
13. Coverage stays ≥ 90%.

**Do not touch.**

- `discover_components()` and `_STACK_A_PATTERNS` — gate 2.
- The `targets` validation machinery T01 built and T03 tightened, beyond adding
  `queue-stalled` to the set of types that require targets. This WU adds a type; it does
  not redesign the axis.
- `.git/`, secrets. The driver owns all git operations. See
  `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` must all pass, plus the
`cmp` in AC10 and the CLI exit check in AC11.

**Escalation triggers.** Emit `status: blocked` if:

- A neutral spelling for the stall threshold cannot be found without naming a broker
  vendor. The whole check-type set is neutral by construction and this type must not be
  the one that breaks it.
- `queue-stalled`'s semantics turn out to overlap `dlq` so completely that it is not a
  distinct check. **That finding is worth more than a forced implementation** — it closes
  #247 as won't-fix with a reason, and a schema with one fewer redundant type is a better
  outcome than a schema with one more. Say what the overlap is.
- Adding the enum member breaks a test you cannot attribute to Coupling A. That means
  another surface encodes the type lexicon and `PLAN.md`'s §10 enumeration was incomplete
  — report the surface so the enumeration rule gets the correction.

Blocked is a respectable outcome (`result-contract.md` rule 4).
