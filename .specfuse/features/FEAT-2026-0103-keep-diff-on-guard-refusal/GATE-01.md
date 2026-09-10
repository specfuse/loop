---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_guard_repair_e2e -v"
cost_budget_usd: 40.00
---

# Gate 1 — a guard refusal keeps the tree and the next attempt repairs it

## Definition of done

A work unit whose attempt passes verification but is refused by a bookkeeping
guard keeps its working tree; the next attempt is dispatched with the guard's
exact complaint and the retained diff, and its squash carries both the original
work and the repair. A RESULT block that names an untouched path outside the
unit's `produces:` is repaired by the driver without a dispatch.

The `feature_oracle` above is that claim, executable. It is **red on the tree
this gate starts from** (the module does not exist), and T01 — the walking
skeleton — is what makes it green. It drives `loop.run()` with a stubbed
dispatch: attempt 1 writes the unit's deliverable and declares one extra path it
never touched (`files_changed_mismatch`); the oracle asserts the guard fired,
that attempt 2's prompt carries the guard's complaint and the retained diff, that
the deliverable was still on disk when attempt 2 started, and that the unit
passed on attempt 2 with one squash commit holding attempt 1's file.

Also required for the gate to close:

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation reflects what was actually built.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

This is the feature's terminal gate, so its closing sequence is a single `close`
unit and the terminal verdict is written by a fresh judge session, not by the
close itself.

## The four sites and the one switch

| guard | outcome | site today | after T01 |
| --- | --- | --- | --- |
| `assert_declared_deliverables` | `deliverable_missing` | reset | retain |
| `assert_implementation_touched_files` | `no_deliverable_files` | reset | retain |
| `resolve_produces_refusal` | `produces_not_in_diff` | reset | retain |
| `verify_files_changed` | `files_changed_mismatch` | reset | retain (T03: auto-repair when no deliverable is involved) |

`verification.yml` → `defaults: retain_on_guard_refusal: false` restores the
reset at all four sites. Absent, the switch is on. Nothing else in the attempt
loop reads it.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4).** T01 flips a default
  (retain, where today's default is reset). Before arming, the operator ran the
  driver's own suite on the tree this gate starts from; the flag-scope table is
  the one above, and the probe list is "every test that asserts a reset after a
  guard refusal" — T01's acceptance criterion 4 names the modules that must keep
  passing unchanged, so a test that encodes today's reset is a finding to
  surface, not to rewrite silently.
- **Flag-scope table (§3).** The table above is it. The headline claim
  ("repair, do not restart") holds only at those four sites.
- **Escalation-predicate satisfiability (§2).** No check is raised; PLAN.md
  records zero.

## Reflection notes

<Written by the human at review time.>
