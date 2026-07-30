---
id: FEAT-2026-0053/T07
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
human_only: true
provenance: "RETROSPECTIVE.md, Consumer-visible contract changes item 3 — gate 2 flips open_questions to blocking under auto only; that is the severity flip and it needs its own satisfiability answer and runtime probe. AC#5 (a malformed review file must park, not raise) comes from this feature's own G1-PLAN warn census, which hit MiniYAMLError on one of 43 real feature folders."
produces:
  - specfuse/loop/arm_eval.py
  - tests/test_arm_eval_lint_class.py
oracle_env: macos_local
---

# Contract-field lint warns become blocking — under `auto` only

**Objective.** Turn the warn-only plan-next contract lint into an eighth,
veto-only stop class in the arm predicate, so an `auto` feature whose plan-next
output violates the contract parks for a human instead of arming.

**Context.** Correlation ID `FEAT-2026-0053/T07`. Depends on T06 (the arm
branch that consumes the verdict). T02 shipped `lint_plan_next_draft`
(`specfuse/loop/lint_plan.py`) as WARN-only: it checks that
`GATE-{N+1}-REVIEW.md` frontmatter carries an explicit `open_questions:` list,
and that each `draft` WU has a well-formed correlation ID, a positive
`planned_cost_usd`, a valid `type`, five non-empty mandatory sections, and a
declared driver-helper symbol when its body mentions driver wiring. Nothing
blocks today.

**This WU is a severity flip and is marked `human_only: true`** — a human reads
it at the arming checkpoint before it dispatches, and
`.specfuse/rules/planning-discipline.md` §4's runtime probe is a precondition
of arming this gate at all (see `GATE-02-REVIEW.md`).

**Shape of the flip: an eighth predicate class, not a lint exit-code change.**
Add `plan_next_lint` to `specfuse/loop/arm_eval.py` alongside the existing
seven, and to `VETO_CLASSES`. It calls `lint_plan_next_draft(feature_dir,
just_closed_gate)` and fires when the returned warn list is non-empty, with the
findings in its `reason`. The lint's own CLI exit code is **not** changed and
no other caller's behavior changes — `lint_plan.py` keeps printing WARNs and
exiting 0 for everyone. "Blocking" here means precisely one thing: *the arm does
not happen and the feature parks at `awaiting_review` with the finding list
readable in the event.*

**The incremental edit to an already-delivered file.** `specfuse/loop/arm_eval.py`
was delivered `done` by T03 and appears in this WU's `produces:` anyway, so the
plan lint warns about it by design. The warning is expected and the edit is
narrow, stated here so the reviewer does not have to infer it: **T07 adds one
class function plus its `CLASS_NAMES` and `VETO_CLASSES` entries, and changes
nothing about the existing seven classes, the dataclasses, the constants, or
`_format_decision`.** The path stays in `produces:` because the driver's
in-diff gate is the strongest available guarantee that this WU actually touched
the predicate rather than only adding tests.

Three properties make this the right shape:

- **Veto-only.** A lint finding is derived from model-authored output, so under
  this feature's organizing principle it may only subtract. It can never
  contribute to an approval.
- **Scoped to the feature being armed, under `auto` only.** A `review` or
  `supervised` feature is unaffected in behavior; the class still evaluates and
  still appears in the shadow trail, which is how the trail stays free.
- **Consumer-visible, and to be enumerated at gate 2's close.** The
  `arm_predicate_evaluated` payload's `classes` map gains a key, and
  `CLASS_NAMES` / `VETO_CLASSES` are published constants. That is an addition,
  not a removal, but it belongs in the close's contract-change list.

## Escalation-predicate satisfiability (`.specfuse/rules/planning-discipline.md` §2)

> **What does this rule report on an input already in its intended final state?**

**Zero.** A plan-next output in its intended final state is one where
`GATE-{N+1}-REVIEW.md` carries an explicit `open_questions:` list (`[]` counts —
the contract requires the field, not a non-empty value) and every `draft` WU
carries a well-formed ID, a positive `planned_cost_usd`, a valid `type`, five
non-empty mandatory sections, and `produces_driver_helper` when its body names
driver wiring. Every check in the set is satisfiable by an author who knows the
contract, and each is satisfiable *simultaneously* — none of them trades against
another, which is the failure mode §2 exists to catch (`ERROR` on a rule whose
correct input still trips it).

The empirical grounding, recorded by `[FEAT-2026-0053/G1-PLAN]` at drafting:
`lint_plan_next_draft` was run over all 43 feature folders in this repo across
gates 0–5, producing **26 findings**. Twenty-five are the same finding — a
`GATE-NN-REVIEW.md` with no `open_questions:` field — on features drafted
*before* T02 existed, every one of them at `autonomy_default: review`. None is
an input in its intended final state under the new contract, and none is ever
evaluated by this class, because the class only runs on the feature being
armed. Gate 2's own drafted output, written to the contract, reports **zero**.

The 26th finding is not a warn at all and is the reason for AC#5 below: one
feature folder's review file raised `MiniYAMLError` out of the frontmatter
reader instead of returning a finding. A raise is not a verdict.

Binding rules apply by reference: `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`.

**Flag-scope table** (`.specfuse/rules/planning-discipline.md` §3). The behavior
flag is `autonomy_default: auto`; the claim is *"the contract-field lint blocks
under `auto`"*.

| Code path | Gated by flag? | Why |
|---|---|---|
| The arm branch's consumption of the `plan_next_lint` verdict | yes | only an `auto` feature can be refused an arm it would otherwise get |
| `plan_next_lint` evaluation itself | no | evaluates on every close so the shadow trail is free — evaluating is not acting |
| `lint_plan.py` CLI exit code | no | unchanged for every caller; still WARN + exit 0 |
| `lint_plan_next_draft`'s check set | no | this WU changes severity, not content — a new check is a different unit |
| Pre-commit hooks / CI lint invocations | no | they call the CLI, whose behavior is unchanged |
| `review` / `supervised` features | no | no arm to refuse; the class appears in their events and changes nothing |

**Acceptance criteria.**

1. `tests/test_arm_eval_lint_class.py::TestPlanNextLintClass::test_findings_block_arm_under_auto`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist — red).
2. `plan_next_lint` is present in `CLASS_NAMES` and in `VETO_CLASSES` in
   `specfuse/loop/arm_eval.py`, verified by
   `python3 -c "from specfuse.loop.arm_eval import CLASS_NAMES, VETO_CLASSES; assert 'plan_next_lint' in CLASS_NAMES and 'plan_next_lint' in VETO_CLASSES"`.
3. A feature whose plan-next output carries findings evaluates to
   `would_arm: False` with `plan_next_lint` fired and every finding string
   present in the class `reason`.
4. A feature whose plan-next output is clean evaluates `plan_next_lint` as
   clean and does not, by itself, prevent `would_arm: True`.
5. A `GATE-{N+1}-REVIEW.md` whose frontmatter cannot be parsed produces a
   **fired** `plan_next_lint` verdict naming the parse failure — not a raised
   exception. The evaluation must not crash the close path, matching T04's
   `evaluation_error` degradation precedent.
6. `lint_plan.py`'s CLI behavior is unchanged: running
   `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0053-auto-mode --just-closed-gate 1`
   still prints WARNs (if any) and exits 0.
7. Running the new class over **every** feature folder in
   `.specfuse/features/` completes without a single raised exception, and the
   resulting fired/clean tally is recorded in the RESULT block. This is the
   §4 runtime probe re-run as a regression check, not a substitute for the
   probe the human runs before arming.
8. `tests/test_arm_eval_lint_class.py::TestPlanNextLintClass::test_findings_block_arm_under_auto`
   **passes after this WU's edits**, and both
   `python3 -m unittest tests.test_arm_eval_lint_class -v` and
   `python3 -m unittest tests.test_arm_eval -v` exit 0 — the pre-existing
   19-case suite must not regress.

**Do not touch.** The check *content* of `lint_plan_next_draft` — this WU
changes severity, not what is checked; adding, removing, or loosening a check
here would make the satisfiability answer above false. The CLI exit code of
`lint_plan.py`. The other seven predicate classes and their reasons. The
arm branch itself (T06). `FEATURE-REVIEW.md` accumulation (T08) and LEARNINGS
staging (T09). Historical feature folders — the 25 legacy findings are evidence,
not a migration backlog, and back-filling `open_questions:` into closed features
is explicitly out of scope. Generated directories, secrets, `.git/`. The driver
owns all git — you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` set in `.specfuse/verification.yml`. Scoped
iteration runs: `python3 -m unittest tests.test_arm_eval_lint_class -v` and
`python3 -m unittest tests.test_arm_eval -v`. Plus the symbol assertion in
criterion 2 and the corpus sweep in criterion 7.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
any check in `lint_plan_next_draft`'s set turns out to fire on a
correctly-authored plan-next output — that makes the satisfiability answer above
false, and §2 says stop and redesign rather than arm; or if satisfying two
checks in the set requires mutually exclusive authoring. If `plan_next_lint` is
absent from `CLASS_NAMES` in the files you edited, emit `status: blocked` — do
not claim complete.
