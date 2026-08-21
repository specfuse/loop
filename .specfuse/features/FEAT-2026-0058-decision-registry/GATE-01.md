---
gate: 1
status: open
cost_budget_usd: 20.00
baseline:
  sha: 0e6ff1a66dc9327826727be9cacc638de34fce45
  probed_at: 2026-08-21T11:59:27.257469+00:00
  failing: []
---

# Gate 1 — decisions cite, they do not restate

A feature's decisions live in `DECISIONS.md`; every other artifact cites them by
ID. A gate cannot arm while a citation dangles, while an artifact restates a
decision instead of citing it, or while an override sits unsigned.

## Definition of done

- Every implementation work unit in this gate is `done`.
- `DECISIONS.md` has a documented format — decision ID, statement, owner, a
  bounded `status`, provenance link, and the override provenance fields — with a
  template a drafting session can fill.
- This feature's own decisions (D1–D4 in `PLAN.md`) are in its `DECISIONS.md`:
  the format's first real consumer is the feature that defines it.
- `specfuse lint` fails a feature whose artifact cites a decision ID absent from
  the registry, and fails one whose artifact reproduces a decision's statement
  instead of citing its ID. ERROR, not WARN — and the tree passes.
- `specfuse lint` fails a decision at `overridden-pending-signoff` that lacks
  `overridden_from`, `signed_off_by`, or `signed_off_at`.
- `done` and `abandoned` features are exempt as sealed history, the same
  exemption `check_closing_guard_literals` already applies.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are staged to `LEARNINGS-pending.md` — this feature is
  `autonomy_default: auto`, where `close-i` forbids writing
  `.specfuse/LEARNINGS.md` directly.

## Precondition — the repair lands first

`PLAN.md` D2: FEAT-2026-0050's D1–D3 prose is converted to a `DECISIONS.md` in
**its own PR, merged before this gate runs**. A feature that both repairs and
checks cannot demonstrate its checker ever fires
(`[FEAT-2026-0034/G1-CLOSE/hand-check-the-invariants-before-automating-them]`).

If this gate is dispatched with that repair unmerged, T02 will find the tree
already clean for the wrong reason — no feature cites anything yet — and its
ERROR-on-a-populated-tree claim becomes unfalsifiable. Check before arming.

## Out of scope for this gate

- Contradiction detection between artifact prose and a registry entry (D1).
- The close ceremony's contract-change enumeration (D4).
- Migrating any feature other than FEAT-2026-0050.

## Arming discipline

Before arming, check — and record the result in the gate review:

- **Runtime probe.** Run the non-restatement matcher by hand over the six
  decisions-prose PLAN files in the tree. `[FEAT-2026-0034/G1-CLOSE]` is
  explicit that this is what decides whether the gate's headline criterion is
  satisfiable on arrival, and it is cheaper than one blocked attempt.
- **Flag scope.** This feature introduces no flag. If T02 grows one to stage the
  ERROR, the introducing WU carries the flag-scope table.
- **Predicate check.** `driver_edit.is_driver_module_path` against every path
  declared in `produces:`. T02 and T03 both edit `specfuse/loop/lint_plan.py`,
  which **is** on the driver's importable surface — so the second of them to run
  halts this run for a driver restart (FEAT-2026-0075). That is expected, not a
  fault: the conductor re-dispatches a fresh driver itself since #2321. Note it
  at arming so the halt is not read as a failure.
