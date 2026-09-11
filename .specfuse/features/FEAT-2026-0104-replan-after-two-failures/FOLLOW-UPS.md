# Follow-ups

Filed by the judge for gate 2. Each entry is the judge's own words.

### T07 (part 3 of the six-part framing)

**Tracked as #3305.**

Part 3 ("What decision is needed, and why") of the spin-out brief is not delivered in full — it is a hardcoded stub that defers to another internal work unit and leaks an internal WU ID into operator-facing text: `"A person needs to decide how this unit proceeds. (Full decision text is FEAT-2026-0104/T07's; this brief only guarantees the decision point exists.)"` (specfuse/loop/loop.py:3145-3148, unconditional in both the `offers_replan` and non-`offers_replan` branches). `.specfuse/rules/operator-escalation.md` requires part 3 "Always in full," and forbids assuming the reader "has read the work unit" — an internal FEAT/T-ID referencing this same gate's own work unit fails that bar. The gate's `feature_oracle` and `test_spinout_brief_replan_option` never assert on part 3's content, so no oracle catches it.

- command: `grep -n "Full decision text is" specfuse/loop/loop.py`
- exit: 0 (match found at line 3147, confirming the stub ships in the built code, not just the diff)

---

## Discharge record — close attempt 2

Appended by the re-close, below the judge's entry and without editing it: the
judge's words above are the record of what was found and they stand as written.

**#3305 is discharged in tree.** Part 3 of `format_spinout_escalation_brief`
now states the decision, why no automatic move remains, and what stays blocked
until one is made; it names no internal work-unit ID. Verified by executed
command in the close session, not by reading the diff:

- `grep -n "Full decision text is" specfuse/loop/loop.py` — exit 1, no match
  (the inverse of the grep in the entry above, which exited 0 at line 3147).
- A real `loop.run()` driven to attempt exhaustion renders the corrected part 3;
  the brief is pasted verbatim in `RETROSPECTIVE.md` § "The brief, as a real
  `loop.run()` produces it".
- The gap that let it ship now has an oracle:
  `tests.test_spinout_brief_replan_option.SpinoutBriefEveryPartHasContent`
  asserts every part is at least 40 characters, that no part leaks an
  implementing work-unit ID, and that part 3 states the decision, the reason and
  the consequence. `python3 -m unittest tests.test_spinout_brief_replan_option
  -v -b` — exit 0, Ran 6.

Closing the GitHub issue is a bookkeeping step outside this session's scope —
the close edits files and runs no `git` or `gh`. Full account in
`RETROSPECTIVE.md` § "The defect this close found, and what happened to it".

### Documentation and roadmap status reflect what was actually built

**Tracked as #3306.**

PLAN.md and roadmap.md still record `status: active` for FEAT-2026-0104, and GATE-02.md still records `status: open`, even though the close bundle (RETROSPECTIVE.md, commit `bf2fba5 feat: Close the feature`) treats this as the feature's terminal close. Comparably closed features in this repo (e.g. FEAT-2026-0001) carry `status: done` in PLAN.md once closed. The gate's own definition of done requires "Documentation and roadmap status reflect what was actually built," and it does not.

- command: `grep -n "^status:" .specfuse/features/FEAT-2026-0104-replan-after-two-failures/PLAN.md .specfuse/features/FEAT-2026-0104-replan-after-two-failures/GATE-02.md`
- exit: 0 (output: `PLAN.md:10:status: active`, `GATE-02.md:3:status: open`)

---

## Filed by close dispatch 3

Appended below the earlier entries without editing them. The judge's words above
are the record of what each earlier dispatch found and they stand as written.

### Part 3 of the escalation brief claims an exhausted attempt budget at nine of the ten sites T10 widened it to

**Tracked as #3308.**

**Criterion (verbatim, `GATE-02.md` § "Definition of done").** "After a work unit
escalates with `blocked_human`, the operator-facing brief presents re-planning
the remaining gate as its default option, inside the six-part framing
`.specfuse/rules/operator-escalation.md` requires."

**What is wrong.** Part 3 of `format_spinout_escalation_brief` asserts
unconditionally that "every attempt its budget allowed has been dispatched and
has failed". Part 4, four lines below in the same function, gates the identical
claim on `reason in ("spinning_detected", "all_attempts_zero_token")` — the only
two reasons for which it is true. T10 widened the render from that single
attempt-exhaustion site to all ten per-unit escalation sites without widening
part 3's conditional, so at the other nine the brief states a false fact about
the attempt record and contradicts its own part 1.
`.specfuse/rules/operator-escalation.md` requires part 3 "always in full" and
requires every claim to be traceable to an artifact; a claim the attempt record
contradicts is not traceable to one, it is refuted by one.

**Evidence — executed in the close session, not read off the diff.**

- A real `loop.run()` driven to an `agent_reported_blocked` escalation (the
  corpus's most common per-unit reason at 22.2%), on a unit declaring
  `max_attempts: 3`, using the harness from
  `tests/test_brief_covers_every_unit_escalation.py`. The `human_escalation`
  event's `message` renders part 1 as "was dispatched 1 time(s): attempt 1:
  blocked" and part 3 as "every attempt its budget allowed has been dispatched
  and has failed". One attempt of three was dispatched.
- `sed -n '3154,3181p' specfuse/loop/loop.py` — exit 0. Shows part 3's clause as
  an unconditional f-string and part 4's identical claim wrapped in the
  two-reason conditional.
- The AST walk T10's own test uses, re-run over `specfuse/loop/loop.py` in this
  session: ten `human_escalation` `build_event` calls keyed on a unit's own
  `wu_id`, of which exactly one (`loop.py:11227`, the attempt-exhaustion
  `for-else`) is a site where the budget is genuinely exhausted.
- `.venv/bin/python -m unittest tests.test_spinout_brief_replan_option -v -b` —
  exit 0, Ran 6; and
  `.venv/bin/python -m unittest tests.test_brief_covers_every_unit_escalation -v -b`
  — exit 0, Ran 3. Both green. Neither asserts on the truth of part 3's claim,
  which is why nothing caught this.

**Why the close did not fix it.** The fix is an implementation change with its
own oracle. This close work unit's `gate_set` is `plannext`, whose whole narrow
tier is `lint_plan.py`, so a driver edit made in this session would be verified
by a document linter and nothing else.

**Re-run condition that discharges this.** Part 3's exhaustion clause becomes
conditional on the same test part 4 already applies — `wu_max_attempts` is
already in scope at that point in the function — and renders something true for
the other nine reasons. Plus a test that drives a real `loop.run()` to a
non-exhaustion escalation and asserts that part 3's statement about the attempt
record agrees with part 1's, so the two cannot drift apart again. Discharged
when that test is green and a real `agent_reported_blocked` run renders a part 3
whose claim matches the unit's actual attempt count.
