---
id: FEAT-2026-0053/T06
type: implementation
status: draft
attempts: 0
planned_cost_usd: 3.50
provenance: "RETROSPECTIVE.md Findings section 3 — the predicate's approval path has never run on real input; 43 of 43 real feature directories returned not_evaluable on every class. AC#6 (arm path exercised against a real feature directory, not a hand-built fixture) exists because of that finding."
produces:
  - tests/test_arm_wiring.py
  - docs/dev/auto-arm-recovery.md
produces_driver_helper:
  - autonomy_default dial read at the gate-close flip site in loop.py
  - auto-arm branch invoking apply_arm_transaction inside the existing single bookkeeping commit
oracle_env: macos_local
---

# The dial goes live — read `autonomy_default`, act on the verdict, arm in one commit

**Objective.** Wire the dial and the predicate verdict into the gate-close path
so an `auto` feature with `would_arm: True` arms its next gate in exactly one
bookkeeping commit, and every other combination behaves exactly as today.

**Context.** Correlation ID `FEAT-2026-0053/T06`. Depends on T05 (the arm
transaction module) and consumes T03's `evaluate_arm_predicate` and T04's
existing call sites. This is the unit that makes `auto` mean something: today
`autonomy_default` is written to PLAN frontmatter by `gh_features.py` and
`adopt_feature.py` and read by nothing in the run loop.

**The flip sites, already enumerated (do not re-derive).** T04 wired
`build_arm_predicate_event` into three sites in `specfuse/loop/loop.py`, and
they are not equivalent:

| Flip site | What it is | Arms under `auto`? |
|---|---|---|
| Pre-flight baseline probe failure (`preexisting_gate_failure`) | escalation | **never** |
| Per-gate budget brake (`gate_budget_exceeded`) | escalation | **never** |
| Normal gate completion (all WUs `done`, `gate_reached`) | the arm site | yes, when the predicate says so |

**Escalation always overrides autonomy.** The two escalation sites do not
consult the dial at all — they park at `awaiting_review` with their reason
already in the event, exactly as today. Only the normal-completion site gains a
branch. Each of the three sites already performs exactly one
bookkeeping commit, which is why a single atomic arm needs no refactor of the
close path.

**The arm branch, at the normal-completion site only.** When
`autonomy_default` is `auto` **and** the predicate returns `would_arm: True`:

1. create the revert tag `arm_tag_name(feature_id, N)` at HEAD — *before* any
   write, so the tag is the pre-arm state;
2. apply T05's transaction (draft→pending flips, gate `N` `awaiting_review` →
   `passed`) into the working tree;
3. append the events for this close — the existing `gate_reached` and
   `arm_predicate_evaluated`, plus one `gate_auto_armed` event carrying
   `{gate, tag, armed_wu_ids, predicate_version}`;
4. commit **all of it** — gate file, the flipped WU files, `events.jsonl` — in
   the one already-existing bookkeeping commit at this site, with a message
   naming the arm.

`review` and `supervised` take the existing path unchanged: flip to
`awaiting_review`, commit, print the `/arm-gate` guidance, return. A `would_arm:
False` verdict under `auto` also takes the existing path — the stop class's
reason is already in the `arm_predicate_evaluated` payload, which is what makes
a parked `auto` feature diagnosable.

**New event type, same precedent as T04.** `gate_auto_armed` is not added to
`event.schema.json`'s enum and gets no per-type schema, for the reasons T04
settled and the operator confirmed: `gate_reached` and `attempt_outcome`
already sit outside both surfaces and the driver's emit path never invokes the
validator. The registry gap is FEAT-2026-0060's. **Do not re-block on it.**

**Recovery rule, keyed on the single commit.** Produce
`docs/dev/auto-arm-recovery.md` stating the guarantee and the procedure: the
arm is one commit, so a crash either left it uncommitted (the driver's existing
pre-run `git reset --hard` / refuse-on-dirty path discards it — nothing to do)
or committed in full (reset to `pre-arm/<feature-id>/gate-<N>` to undo exactly
the arm). There is no third state, and that is the property the single commit
buys. Gate 3 folds this into `docs/methodology.md`; gate 2 ships the
operational note, because a mechanism whose failure mode has no documented
recovery is not done.

Binding rules apply by reference: `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`.

**Flag-scope table** (`.specfuse/rules/planning-discipline.md` §3). The
behavior flag is `autonomy_default: auto`. The feature's headline claim is *"an
`auto` feature arms its next gate without a human"* — not *"an `auto` feature
runs unattended to completion"*.

| Code path | Gated by flag? | Why |
|---|---|---|
| Normal gate-completion flip site | yes | the only site that can arm |
| Pre-flight baseline-probe failure site | no | escalation overrides autonomy — always parks |
| Per-gate budget-brake site | no | escalation overrides autonomy — always parks |
| Blocked-WU halt (`MAX_ATTEMPTS` escalation) | no | gate never reaches the flip; nothing to arm |
| Draft-detected arm check at gate entry (`return 2`) | no | reached only when a gate was left unarmed; the arm happens at the *previous* gate's close |
| Terminal-flip machinery (`fire_terminal_flips`) | no | terminal gate has no next gate to arm; feature-completion flips are unchanged |
| Merge / PR | no | merge stays human without exception (PLAN.md scope boundary) |
| Next gate's execution in the same process | no | the driver runs one gate per invocation; an armed gate executes on the next invocation. Run-to-drain is FEAT-2026-0049 |

**Acceptance criteria.**

1. `tests/test_arm_wiring.py::TestAutoArm::test_auto_feature_arms_next_gate_in_one_commit`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist — red).
2. With `autonomy_default: auto` and a predicate verdict of `would_arm: True`,
   closing gate `N` leaves: every gate-`N+1` draft WU at `status: pending`, gate
   `N` at `status: passed`, and the tag `pre-arm/<feature-id>/gate-<N>` present
   — all of the file changes in **exactly one** commit, asserted by counting the
   commits the close produced and reading that commit's changed-path list.
3. With `autonomy_default: review` (and separately `supervised`), the same
   verdict changes nothing: gate `N` is `awaiting_review`, gate `N+1`'s WUs are
   still `draft`, and no `pre-arm/*` tag exists.
4. With `autonomy_default: auto` and `would_arm: False`, the feature parks at
   `awaiting_review` and the firing stop class's reason is present in the
   emitted `arm_predicate_evaluated` payload.
5. Both escalation flip sites park at `awaiting_review` under
   `autonomy_default: auto` **even when the predicate would arm** — one test per
   site, asserting no status flip on any gate-`N+1` WU and no `pre-arm/*` tag.
6. The auto-arm path is exercised at least once against a **real** feature
   directory — a copy of an actual `.specfuse/features/FEAT-*` folder with a
   real `PLAN.baseline.json`, real WU frontmatter, and a real `events.jsonl` —
   not a hand-built fixture. See this WU's `provenance`.
7. `docs/dev/auto-arm-recovery.md` exists, states the one-commit atomicity
   guarantee, and gives the exact reset-to-tag command for the committed-arm
   case.
8. `tests/test_arm_wiring.py::TestAutoArm::test_auto_feature_arms_next_gate_in_one_commit`
   **passes after this WU's edits**, and `python3 -m unittest tests.test_arm_wiring -v`
   exits 0.

**Do not touch.** `specfuse/loop/arm_txn.py` and `specfuse/loop/arm_eval.py`
beyond importing them — transaction logic is T05's, evaluation logic is T03's;
if wiring reveals a defect in either, block rather than patch it here. The
contract-field lint severity (T07). `FEATURE-REVIEW.md` accumulation (T08) and
LEARNINGS staging (T09) — this WU arms; those two write the human-read
surfaces. The two escalation flip sites, beyond the tests asserting they still
park. Merge and PR behavior. Generated directories, secrets, `.git/`. The
driver owns all git — you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` set in `.specfuse/verification.yml`. Scoped
iteration run: `python3 -m unittest tests.test_arm_wiring -v`. Do **not** run
`validate-event.py` over the emitted `gate_auto_armed` event — that type is
absent from the envelope enum by design (see Context), so the check fails for a
reason unrelated to this WU, exactly as it does today for `gate_reached`.
Assert the payload's keys and types in the test instead.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
the normal-completion flip site cannot carry the arm inside its existing single
bookkeeping commit without restructuring the close path (a refactor is a
different unit — name the specific obstruction); or the dial read finds
`autonomy_default` consumed somewhere in the run loop that this WU's flag-scope
table does not list (the table is the claim; a path it does not cover is a
scope mismatch, not a detail). The per-type event-schema registry gap is
**resolved and out of scope** — do not block on it.
