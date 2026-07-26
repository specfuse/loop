---
id: FEAT-2026-0069/T07
type: implementation
status: draft
attempts: 0
planned_cost_usd: 3.50
oracle_env: macos_local
produces:
  - tests/test_derive_monitoring_discovery.py
---

# The N-trigger fixture, and mechanical target-list generation for schedules

**Objective.** Add the fixture whose single deployable carries N triggers, and make
`suggest_checks` generate one `heartbeat` target per discovered schedule — so gate 2's
definition of done becomes a test that either passes or does not.

**Context.** This is `FEAT-2026-0069/T07`, the falsifiable core of gate 2. It depends on
`FEAT-2026-0069/T06`, which re-keys `discover_components` onto deployment evidence and puts
`subscriptions` and `schedules` on the emitted record. `GATE-02.md`'s definition of done:
*`/derive-monitoring`, run against a repo whose single deployable carries N triggers, emits
**1 component with N targets** — not N components.*

Two reasons this fixture is a deliverable and not an afterthought:

- FEAT-2026-0039's Stack A fixture has **one trigger per deployable**, so it structurally
  could not express the N-triggers-per-deployable failure. `.specfuse/LEARNINGS.md`
  `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` promoted the general rule: *a fixture with
  cardinality 1 where the failure needs N is not a small fixture, it is a fixture testing a
  different question — so a WU whose `produces:` includes a fixture must name the
  cardinality the fixture carries.* This one carries **3 subscriptions and 2 schedules**,
  so both trigger kinds have cardinality > 1 and a per-target assertion cannot be satisfied
  by accident.
- After `T06`, discovery derives `subscriptions` and `suggest_checks` already fans them out
  into `dlq` targets one-per-entry (`:108-118`). It does **not** consume `schedules` at all:
  a multi-schedule host still gets one target-less `heartbeat`, so a single silent timer
  among several is still invisible — the exact defect `PLAN.md` opens with. Closing that is
  this WU's substantive change.

**What the acceptance of this WU does and does not prove — read before writing the fixture.**
`PLAN.md`'s gate 2 sketch records the originating issue's claim that every target
coordinate is *mechanically extractable* from real code (subscription names from the
trigger attribute, function names from the `[Function(nameof(...))]` form, cron and IANA
timezone from named constants on the timer classes). **That claim is confirmed only against
a repo outside this tree**, and `RETROSPECTIVE.md` § *What the loop did NOT verify* entry 2
says so. A fixture authored here is evidence that the *algorithm* fans a trigger table into
a target list; it is **not** evidence that real repositories are shaped so a trigger table
can be built without asking the operator. Do not write an acceptance criterion, a docstring,
or a RESULT `evidence:` line that claims otherwise. `FEAT-2026-0069/G2-CLOSE` carries this
as a `## What the loop did NOT verify` entry, and the fixture's own comment must say which
half it proves.

**Acceptance criteria.**

1. `tests/test_derive_monitoring_discovery.py::TestOneDeployableManyTriggers::test_single_deployable_with_n_triggers_yields_one_component_with_n_targets`
   exists and **fails on HEAD before this WU runs** —
   `python3 -m unittest tests.test_derive_monitoring_discovery.TestOneDeployableManyTriggers -v`
   exits non-zero (no such class today). It is also still red **after `T06` alone**, on the
   heartbeat clause of AC3: `T06` gives the `dlq` fan-out but leaves `schedules` unconsumed,
   so the heartbeat check has no `targets` until this WU's AC4 lands. Confirm both by
   running the scoped command before editing.
2. `_STACK_C_PATTERNS` / `_STACK_C_TREE` exist, declaring **one** deployable
   (`acme-functions-host`, type `multi-trigger-host`, matching
   `.specfuse/monitoring.yml.example`'s motivating component) whose scope contains **3**
   `subscription`-kind triggers and **2** `schedule`-kind triggers, in the `T06` pattern-table
   contract. Marker vocabulary and names are disjoint from Stack A's and Stack B's, per the
   provider-neutrality posture the module already keeps.
3. The AC1 test asserts, on `_STACK_C_TREE`, all four clauses:
   `len(components) == 1`; the `dlq` check carries exactly **3** targets, each a
   `{subscription, function}` pair from the trigger table; the `heartbeat` check carries
   exactly **2** targets, each a `{name, cron, timezone}` triple from the trigger table; and
   `validate_monitoring` over `render_monitoring_yml`'s output returns **zero** findings.
   The rendered text is written to a `tempfile.TemporaryDirectory()`, matching the module's
   existing hermetic-fixture posture — nothing is committed under `tests/fixtures/`.
4. `suggest_checks` emits `heartbeat` with a `targets` list built one-per-entry from the
   record's `schedules`, each target carrying `name`, `cron`, and `timezone`. A component
   with **no** schedules still gets a target-less `heartbeat` — `targets` is optional on
   `heartbeat` in the validator (`lint_monitoring.py:264`), and inventing a schedule name
   would be fabricating evidence, the same rule that already makes a subscription-less
   consumer get no `dlq` check at all.
5. A negative test asserts AC4's second half:
   `tests/test_derive_monitoring_discovery.py::TestHeartbeatTargetsFromSchedules::test_component_without_schedules_gets_a_targetless_heartbeat`
   — a record with no `schedules` key yields a `heartbeat` check with no `targets` key at
   all (not an empty list; `lint_monitoring.py:296` makes an empty `targets` a finding).
6. Emitted `cron` values are **quoted** in `render_monitoring_yml`'s output, matching
   `.specfuse/monitoring.yml.example:154`. `_miniyaml` parses the unquoted spelling
   correctly — probed by `G1-PLAN` — so this is not a parser fix; it keeps the reference
   implementation's output byte-comparable in spelling with the shipped example a reader is
   told to compare it against. This is the **only** change to `render_monitoring_yml` in
   scope; the nested-`targets` rendering it already does needs nothing.
7. The same scoped tests **pass after this WU's edits** —
   `python3 -m unittest tests.test_derive_monitoring_discovery.TestOneDeployableManyTriggers tests.test_derive_monitoring_discovery.TestHeartbeatTargetsFromSchedules -v`
   exits zero.
8. `_STACK_C_PATTERNS`'s declaration carries a comment naming what this fixture proves and
   what it does not — the wording of the *"What the acceptance of this WU does and does not
   prove"* paragraph above, compressed to two or three lines. The next reader must not be
   able to mistake the fixture for evidence of the extractability claim.
9. `python3 -m unittest discover -s tests -v` exits zero.

**Do not touch.** `discover_components` — `T06` owns the re-key and it is `done` before this
WU runs; if the fixture needs a keying change, that is a `T06` defect and an escalation, not
an edit here. `TestSuggestChecksNeverQueueStalled` (`:524`) and `TestSuggestChecksNeverInvariant`
(`:501`) — a `queue-stalled` stall threshold and an `invariant` query are operator judgement
by definition, so discovery still must never emit either even though `_STACK_C_TREE` is
exactly the shape a `queue-stalled` check is for. `specfuse/loop/lint_monitoring.py` —
`FEAT-2026-0069/T05` owns it in this gate, and this WU needs no validator change: `heartbeat`
already accepts `targets` requiring `name`, with `cron` and `timezone` accepted and opaque.
`.specfuse/monitoring.yml.example` and its packaged copy — gate 1 migrated both and they
already show this exact shape; re-editing them here would put a second author on a settled
surface. The `derive-monitoring` skill prose — that is `FEAT-2026-0069/T08`'s deliverable.
`tests/fixtures/` — this module builds fixtures in-memory and via `tempfile` on purpose.
Gate 1's WU files and `GATE-01.md`. `PLAN.md`'s `status` field. `.git/`, secrets. The driver
owns all git operations — you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set from `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage`, `leak-scan`, `monitoring-example-lint`, `leak-scan-hook`,
`sync-scaffold-bats`, `init-sh-shim-bats`, `init-skills-bats`. Scoped red/green proof:
`python3 -m unittest tests.test_derive_monitoring_discovery.TestOneDeployableManyTriggers -v`.
Symbol check (`/authoring-work-units` §9):
`grep -c "^_STACK_C_PATTERNS\|^_STACK_C_TREE" tests/test_derive_monitoring_discovery.py`
returns `2`.

> Secrets posture (`.specfuse/rules/security-boundaries.md`): every fixture name is an
> `acme-*` placeholder and every timezone is `Etc/UTC`, matching the shipped example. The
> `leak-scan` gate bites on this surface and its pre-commit form is stricter than its CI
> form.
>
> Sandbox note (`.specfuse/LEARNINGS.md` `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`): the
> three `bats` gates call `mktemp -d` in `setup`, which the default session sandbox denies
> (`Operation not permitted`) before any assertion runs. Report which sandbox each gate ran
> under; do not read a sandbox denial as a regression.

**Escalation triggers.** Emit `status: blocked` if AC3's fixture cannot be made to yield one
component with 3 `dlq` targets and 2 `heartbeat` targets — that is gate 2's definition of
done failing, and it must reach the operator as a finding rather than be softened into a
fixture that asserts something weaker. Also block if satisfying AC3's zero-findings clause
requires a change to `specfuse/loop/lint_monitoring.py`: gate 1 shipped that validator with
`heartbeat` targets already accepted, so a validator change here would mean the emitted shape
and the schema disagree — a contract finding, not an implementation detail. Blocked is a
respectable outcome (`result-contract.md` rule 4).
</content>
