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
