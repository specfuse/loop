---
id: FEAT-2026-0101/T02
type: implementation
status: blocked_human
attempts: 0
planned_cost_usd: 2.50
oracle_env: macos_local
produces:
  - specfuse/loop/closing_requirements.py
  - specfuse/loop/lint_closing.py
  - .specfuse/rules/close-discipline.md
  - tests/test_close_records_feature_oracle.py
duration_seconds: 2953.024
cost_usd: 3.957437
input_tokens: 258
output_tokens: 54605
---

# The close re-runs the gate's oracle and records its verdict

**Objective.** Make the gate's `feature_oracle` verdict a required part of the
close's `## Measurements`, so `specfuse lint --closing` fails a close that omits
it and the judge has a binary end-to-end signal to read.

**Context.** FEAT-2026-0101/T02; read `PLAN.md` and T01. The judge already
receives the close's `## Measurements` and not its `## Verdict` or
`## Retrospective` prose (FEAT-2026-0100), so putting the oracle's verdict in
measurements is what delivers this feature's "binary signal for the judge"
benefit **with no judge change**. The closing-section registry lives in
`closing_requirements.py` and the check in `lint_closing.py`; the discipline is
stated in `.specfuse/rules/close-discipline.md` §1, whose fresh-re-run
requirement this sharpens.

**The distinction this encodes.** `[FEAT-2026-0057/G1-CLOSE/feature-oracle-is-a-different-question]`:
re-running every producing unit's own oracle is **not** the feature-level re-run
§1 asks for. Fifteen oracles re-ran green in one close and none could observe
the defect, because none asserted on the path the feature was meant to change. A
close must ask the composite question the units were each too small to ask, and
from now on the gate's `feature_oracle` **is** that question. Update §1 to say
so, rather than adding a parallel rule beside it.

**Scope guard.** A gate that declares no `feature_oracle` must not fail the
closing lint — T03 decides whether an absent declaration is a finding, and it is
only ERROR on an `active` feature. This unit's requirement is conditional on the
declaration existing.

**Acceptance criteria.**

- `tests/test_close_records_feature_oracle.py::test_closing_lint_fails_when_oracle_verdict_absent` fails on HEAD and passes after: a close whose gate declares an oracle but whose `## Measurements` records no verdict for it exits non-zero under `specfuse lint --closing`, naming the oracle.
- `::test_closing_lint_passes_when_verdict_recorded`: the same close with the verdict recorded exits 0.
- `::test_gate_without_oracle_imposes_no_requirement`: a close whose gate declares no `feature_oracle` is unaffected — this is the conditional the scope guard above requires.
- `.specfuse/rules/close-discipline.md` §1 states that the gate's `feature_oracle` is the feature-level re-run, citing `[FEAT-2026-0057/G1-CLOSE/feature-oracle-is-a-different-question]`: `grep -n "feature_oracle" .specfuse/rules/close-discipline.md` returns at least one hit in §1.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `verify()` and the oracle runner (T01 owns them);
`lint_plan.py` (T03); templates, skills, `methodology.md` (T04); `judge.py` —
the judge needs no change and editing it would widen the blast radius on the
one module that decides verdicts; `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus this
gate's `feature_oracle`.

**Escalation triggers.** Emit `status: blocked` if making the requirement
conditional on the declaration cannot be expressed in the closing-section
registry's current shape — a registry that can only express unconditional
sections is a design change, not a judgement call for this unit. Also block if
sharpening §1 would contradict another rule file; name it.
</content>
