---
id: FEAT-2026-0075/T06
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
oracle_env: macos_local
provenance: "`[FEAT-2026-0075/G1-CLOSE-INTERMEDIATE/a-rule-a-human-must-execute-is-not-a-control]` rule (a) names the control verbatim: 'the driver refusing to dispatch a close whose gate contains a work unit that edited the driver after this process started'. RETROSPECTIVE.md gate 1 is the evidence that nothing weaker works — the restart was in bold as REQUIRED, the rule was promoted and quoted, the close carried a blocking criterion, and the restart still did not happen. GATE-02.md's draft-time proposal put this control at arm time keyed on `produces:` declarations; `G1-PLAN` moved it to the squash-diff seam after a 90-gate sweep showed the arm-time scoping was unsatisfiable (41 of 41 driver-editing gates would be refused, 0 compliant gates exist) and after PLAN.md's own scope decision — 'detection keys on the unit's actual squash diff, never on its declarations' — ruled out building a blocking check on author-supplied fields."
produces_driver_helper:
  - specfuse.loop.loop.format_driver_restart_halt
produces:
  - specfuse/loop/loop.py
  - tests/test_driver_restart_halt_wiring.py
generated_surfaces: []
model: sonnet
effort: high
gate_set: code
driver_version: 0.9.3
started_at: 2026-08-07T12:39:59.025188+00:00
duration_seconds: 1504.84
cost_usd: 7.90437
input_tokens: 341
output_tokens: 73367
---

# Halt the run rather than dispatch the next unit into a stale process

**Objective.** Turn gate 1's warning into a control. When a squash lands touching the
driver's importable surface and this gate still has work units to dispatch, the driver
stops the run through `T05`'s sanctioned halt instead of printing a warning and
dispatching anyway. The operator re-runs; the fresh process carries the edited modules;
the close observes the code it was armed to verify.

**This is the whole feature's point of impact, so it is stated once.** Gate 1 shipped
detection, a warning at the exact right moment, a gate-end summary and a new event —
and its own close was dispatched by a process that predated every unit in the gate.
Nothing in gate 1 could have prevented that, because nothing in gate 1 *does* anything.
The immediate warning's window and this halt's window are the same window; the
difference is that the halt does not depend on anyone reading it.

**Context.** This is `FEAT-2026-0075/T06`, gate 2's last substantive unit. `T04`
narrowed `is_driver_module_path` to the importable surface. `T05` built
`format_driver_restart_halt`, `HALT_REASON_DRIVER_RESTART`,
`EXIT_DRIVER_RESTART_REQUIRED`, and the brake at the `for wu in pending` seam. This
unit is the decision to fire.

Read `RETROSPECTIVE.md`, `GATE-02.md` and `GATE-02-REVIEW.md` before editing.

**The seam, which already exists and must not be duplicated.**
`loop.py:6284-6296` is gate 1's `T02` warning site: immediately after `squash_commit`
returns a sha, the diff is resolved through `changed_paths_for_commit` /
`driver_paths_in`, the warning is printed, and the pair is appended to `driver_edits`.
That block already computes everything this unit needs. Set the halt flag there;
**fire** the halt at the `for wu in pending` brake (`loop.py:5846-5856`, beside the
`_should_halt_for_budget` call), so the unit whose squash triggered it finishes its
bookkeeping and reaches a terminal outcome first. Do not add a second
call to `changed_paths_for_commit`, and do not move the detection into
`squash_commit` — `T02`'s criterion 4 forbids that and the reason has not changed.

**Escalation-predicate satisfiability (`planning-discipline.md` §2), stated here and in
`GATE-02.md`.** *What does this halt report on a gate that is already correctly
ordered?* **Zero.** `G1-PLAN` swept all 57 feature folders / 90 gates: **49 gates
contain no unit that edits the driver's importable surface, and in those the flag is
never set and the run is never interrupted.** For the 41 gates that do edit the driver,
one halt is the correct behaviour, not a false positive — a gate that edits the driver
and then keeps dispatching in the same process is the defect. Under `T04`'s narrowing 3
of those 41 stop firing entirely (docs, example configs, a workflow file). The halt
refuses no plan and rejects no work unit; it costs one re-run of a command the operator
already ran.

This is why the halt is keyed on the squash diff and not on the arm-time plan shape.
The arm-time scoping in `GATE-02.md`'s draft-time proposal — "a driver-editing WU
scheduled ahead of a close in the same gate" — reports **41 of 41**, because every gate
in the methodology ends with a close, so no compliant plan can be written. See
`GATE-02-REVIEW.md` § *The §2 answer, and why the arm-time shape was rejected*.

**Flag-scope table (`planning-discipline.md` §3).** This unit introduces **no** behavior
flag, deliberately. The table is stated so the absence is a decision on file:

| Code path | Gated by flag? | Why |
|---|---|---|
| squash-site detection (`loop.py:6284-6296`) | no | already unconditional in gate 1; a flag here would restore the pre-gate-1 silence |
| the halt brake at `for wu in pending` | no | an opt-out is a control a human can forget, which is the exact failure `[…/a-rule-a-human-must-execute-is-not-a-control]` names |
| `--dry-run` runs | not gated — suppressed | dry runs dispatch nothing, so there is no stale dispatch to prevent (criterion 6) |
| last-unit-in-gate case | not gated — suppressed | nothing remains to dispatch; the gate-end `T03` summary already covers it (criterion 5) |

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `correlation-ids.md`, `planning-discipline.md`.

**Acceptance criteria.**

1. `tests/test_driver_restart_halt_wiring.py::test_driver_edit_halts_before_next_dispatch`
   exists and **fails on HEAD before this WU's edits**. Paste the failing output in the
   RESULT block before editing production code.
2. **Seam test, not formatter test.** The test drives the real outcome path with a stub
   reporting a squash diff touching `specfuse/loop/loop.py`, with at least one further
   unit pending in the gate, and asserts: the run returns
   `EXIT_DRIVER_RESTART_REQUIRED`, the next unit was **never dispatched**, and the halt
   message reached the driver's output. Asserting only on `format_driver_restart_halt`
   does not satisfy this criterion — the seam is what this feature exists to get right.
3. The halt fires from the `for wu in pending` brake, not from inside the squash block
   and not from inside `squash_commit`. `grep -n 'format_driver_restart_halt' specfuse/loop/loop.py`
   shows no match inside `squash_commit`'s body. Paste the grep.
4. The unit whose squash set the flag reaches its terminal outcome first: its status is
   `done` and its `task_completed` event is present, asserted after the halt.
5. **A driver edit by the gate's final unit does not halt.** With no further unit
   pending, the run completes normally, the gate flips to `awaiting_review`, and `T03`'s
   gate-completion summary is what reports the staleness. Asserted through the same
   harness.
6. **`--dry-run` never halts.** Asserted through the same harness.
7. **The negative case, through the same harness:** a unit whose squash diff touches no
   driver-module path leaves the run uninterrupted and every subsequent unit dispatched.
8. `T02`'s existing immediate warning still prints at the squash site. The halt is
   additive; removing the warning would delete the only signal a `--dry-run` or
   final-unit case still gets.
9. `changed_paths_for_commit` is called exactly once per squash:
   `grep -n 'changed_paths_for_commit' specfuse/loop/loop.py` shows one call site. Paste
   the grep.
10. **Runtime probe (`planning-discipline.md` §4), pasted in full.** Re-run
    `G1-PLAN`'s 90-gate sweep against the shipped code and report, for each of the 90
    gates, whether this halt would fire and how many times. A gate with no
    driver-module edit reporting a halt is a mis-scoped predicate and blocks this unit.
11. The full `code` gate set passes, including `coverage report --fail-under=90`.

**Do not touch.** `specfuse/loop/driver_edit.py` — `T04`'s; import it, do not extend it.
`specfuse/loop/arm_eval.py` — gate 2 deliberately leaves the arm-time surface alone; see
`GATE-02-REVIEW.md`. The `T03` gate-completion summary and its event emission —
criterion 5 depends on it being unchanged. `format_driver_restart_halt`'s signature and
the halt mechanics — `T05`'s; call them, do not redesign them.
`.specfuse/verification.yml`. `.specfuse/rules/` and `.specfuse/templates/`.
`GATE-01.md` and gate 1's work units. Any other feature's folder under
`.specfuse/features/`. Generated directories, secrets, `.git/`. The driver owns all git
operations — you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage` (`--fail-under=90`), `leak-scan`, `event-type-gate`. In addition
run criterion 3's and criterion 9's greps verbatim and criterion 10's sweep, pasting all
three outputs. Do **not** report the running driver's in-situ behaviour as evidence —
this session's process predates your edits by construction. The in-situ observation
belongs to `G2-CLOSE` after the restart `GATE-02.md` requires.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
criterion 2's seam cannot be asserted because the outcome path cannot be driven with a
stub, which would mean the wiring is unverifiable; criterion 10's sweep reports a halt
on any of the 49 gates with no driver-module edit, which means the §2 satisfiability
answer in `GATE-02.md` is wrong and the halt must be re-scoped before it ships rather
than softened here; halting between units loses the squash of the unit that triggered
it (criterion 4 red); or firing the halt requires `--dry-run` runs to take a different
code path through `squash_commit`.
