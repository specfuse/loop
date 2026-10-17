# Gate 1 review — a diagnosed finding carries a severity that orders autofix

Armed 2026-10-17 under `autonomy_default: auto`; decisions in `PLAN.md` were taken as
recommended ("take your recommendations").

## If you check only three things

1. **Old diagnoses still parse.** A marker without `severity`, and one with an unknown
   value, read as absent and never raise (T01 criterion 2); a marker rendered without
   severity is byte-identical to before.
2. **Autofix eligibility is untouched.** T03 only reorders what the provider already
   advertises; `specfuse/monitor/autofix.py` has no diff.
3. **Findings stay out of the bug lane.** T04's guard: a finding with a `severity:`
   label is still not advertised by the bug lane.

## Runtime probe

n/a — no severity flip of a validation rule.
