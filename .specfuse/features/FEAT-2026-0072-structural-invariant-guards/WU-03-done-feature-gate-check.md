---
id: FEAT-2026-0072/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
produces:
  - specfuse/loop/lint_plan.py
  - tests/test_done_feature_gates.py
produces_driver_helper:
  - check_done_feature_gates
---

# Refuse a done feature whose gates are not passed — and reconcile the three that aren't

**Objective.** Add a `lint_plan` check that a `status: done` feature has every
gate `passed`, carry the two legitimate exclusions by ID and reason, and reconcile
the two features that genuinely completed — all in this one work unit, because the
check is unsatisfiable until the tree is corrected.

**Context.** Correlation ID `FEAT-2026-0072/T03`. Independent of T01 and T02 — a
different surface, no shared code.

`lint_plan` validates feature dirs, PLAN frontmatter, and the gate/WU graph, but
`grep -n 'status.*done' specfuse/loop/lint_plan.py | grep -i gate` returns nothing:
no check relates a feature's `done` status to its gates. So three features drifted
in June and July and nothing complained until an unrelated skill swept the repo
(#287).

**The check and the reconciliation must land together.** This is the load-bearing
sequencing decision. A new blocking error that fires three times on the tree it
ships into is unsatisfiable in the `planning-discipline.md` §2 sense — and under
the preflight baseline probe, a red base gate halts the next feature's run before
any work unit dispatches. Adding the check in one WU and cleaning up in another
would leave an intermediate state that is red by construction.

**The three findings, and what each needs — they are not the same.**

- **`FEAT-2026-0007-dispatch-cost-controls`**, `GATE-02` at `awaiting_review`.
  Genuinely completed; it used the **legacy four-WU closing sequence**
  (`G2-RETRO` / `G2-LESSONS` / `G2-DOCS` / `G2-PLAN`) with no `close` WU, so
  `fire_terminal_flips` — which runs for close-type WUs — never had anything to
  fire from. **Flip its gate to `passed`.**
- **`FEAT-2026-0008-driver-completeness-guard`**, `GATE-01` at `awaiting_review`.
  Genuinely completed; its `close` WU is `done` but carries no `verdict` field
  because the verdict contract did not exist yet. Both features predate the
  terminal-flip machinery (FEAT-2026-0015, -0017, -0018). **Flip its gate to
  `passed`.**
- **`FEAT-2026-0036-adopt-ruff-016`**, `GATE-01` at `open`, close WU still
  `pending`. The roadmap records it was "executed directly" as a config-only fix
  after a loop run on a flawed plan blocked — the close ceremony deliberately
  never ran. **Do not flip it.** Flipping would assert a ceremony that did not
  happen. **Exclude it by ID with that reason inline.**

**The other exclusion, which must not be skipped.**
`FEAT-2026-0001-health-endpoint` is `status: done` with **both** gates `open`, and
that is correct: the roadmap reserves it as the bundled worked-example fixture,
"the self-demonstrating reference installation a target project copies via
`init.sh`" — a template never executed and never to be. Without this exclusion the
check fires on a correct tree, and the likely "fix" is someone mutating a shipped
fixture to satisfy a linter.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_done_feature_gates.py::TestDoneFeatureGates::test_done_feature_with_unpassed_gate_is_reported`
   exists and **fails on HEAD before this WU runs** (the test file does not yet
   exist, which counts as red).
2. `lint_plan` reports an error for a feature whose PLAN frontmatter is
   `status: done` and any of whose `GATE-NN.md` files is not `status: passed`,
   naming the feature and the offending gate file.
3. The check ignores `GATE-NN-REVIEW.md` artifacts, which carry no `status`
   frontmatter and are not gate files.
4. A feature at any status other than `done` is not subject to the check.
5. An exclusion mapping keyed by feature ID exists, containing exactly
   `FEAT-2026-0001-health-endpoint` and `FEAT-2026-0036-adopt-ruff-016`, each with
   a non-empty inline reason string.
6. A test asserts every exclusion entry carries a non-empty reason.
7. A test asserts no exclusion names a feature directory that does not exist — a
   stale opt-out is its own drift.
8. `FEAT-2026-0007-dispatch-cost-controls/GATE-02.md` reads `status: passed`.
9. `FEAT-2026-0008-driver-completeness-guard/GATE-01.md` reads `status: passed`.
10. `FEAT-2026-0036-adopt-ruff-016/GATE-01.md` is **unchanged** — still
    `status: open`, excluded rather than flipped.
11. Running `lint_plan` across **every** directory under `.specfuse/features/`
    produces zero findings from this new check — the sweep, not a sample.
12. `python3 -m pytest tests/test_done_feature_gates.py -q` exits zero after this
    WU's edits (the same file named in criterion 1).
13. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0072-structural-invariant-guards`
    exits zero — this feature's own folder still lints clean.

**Do not touch.** Any WU file inside FEAT-2026-0007, -0008, or -0036 — this WU
flips two gate files and nothing else in those folders. `PLAN.md` status of any
existing feature. Files owned by T01 or T02. Generated directories, secrets,
`.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set: `tests`, `lint`, `security`, `coverage`
(≥90%), `leak-scan`. Plus the scoped red/green run in criteria 1 and 12, and
**criterion 11's tree-wide sweep** — a criterion scoped to a sample rather than a
sweep is exactly what cost `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` three attempts
and an escalation; assert zero findings across every feature directory, not a
representative one.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
the tree-wide sweep in criterion 11 finds a feature beyond the three named here —
report it, do not silently add an exclusion; flipping 0007 or 0008 to `passed`
turns out to require touching anything besides the gate file's `status` field; or
`lint_plan`'s existing error-collection shape cannot carry this check without
restructuring the linter. If `specfuse/loop/lint_plan.py` is absent from the files
you edited, emit `status: blocked` — do not claim complete.
