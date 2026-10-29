# Gate 1 review — findings that are never refiled, never false, and carry what a diagnosis needs

Armed 2026-10-17 under `autonomy_default: auto`, after the drafting interview recorded in
`PLAN.md`'s Decisions.

## If you check only three things

1. **The boundary lift is exactly half.** T01 lets the monitor **reopen** a closed finding
   and rewrites `issues.py`'s docstring to say so; nothing in `specfuse/monitor` may ever
   **close** an issue (T01 criterion 4 greps for it). Read the docstring diff, not just the
   test.
2. **No fingerprint moves.** T03's message id and T05's `context`/`observed_at` must not enter
   `fingerprint_artifact`; a moved fingerprint re-files every existing consumer finding as
   new. T03 and T05 each carry a test for it.
3. **One query per check.** Every correlation in T04–T08 is a join or aggregate inside the
   check's existing query, and each query passes `schema_violations`. The Reproduce KQL is
   text in the issue, never executed by the monitor.

## Known advisory

`specfuse lint` WARNs that gate 1 carries 32 acceptance criteria (guideline 20). The
ceremony-proportionality rule put the feature in one gate (8 substantive units, threshold
12); the operator chose one gate knowing both.

## Runtime probe

n/a — no severity flip and no new validation rule (`PLAN.md` §2).
