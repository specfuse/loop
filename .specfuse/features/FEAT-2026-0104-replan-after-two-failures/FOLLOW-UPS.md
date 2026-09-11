# Follow-ups

Filed by the judge for gate 2. Each entry is the judge's own words.

### T07 (part 3 of the six-part framing)

**Tracked as #3305.**

Part 3 ("What decision is needed, and why") of the spin-out brief is not delivered in full — it is a hardcoded stub that defers to another internal work unit and leaks an internal WU ID into operator-facing text: `"A person needs to decide how this unit proceeds. (Full decision text is FEAT-2026-0104/T07's; this brief only guarantees the decision point exists.)"` (specfuse/loop/loop.py:3145-3148, unconditional in both the `offers_replan` and non-`offers_replan` branches). `.specfuse/rules/operator-escalation.md` requires part 3 "Always in full," and forbids assuming the reader "has read the work unit" — an internal FEAT/T-ID referencing this same gate's own work unit fails that bar. The gate's `feature_oracle` and `test_spinout_brief_replan_option` never assert on part 3's content, so no oracle catches it.

- command: `grep -n "Full decision text is" specfuse/loop/loop.py`
- exit: 0 (match found at line 3147, confirming the stub ships in the built code, not just the diff)
