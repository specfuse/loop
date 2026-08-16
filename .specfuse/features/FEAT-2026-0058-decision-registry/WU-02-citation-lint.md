---
id: FEAT-2026-0058/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
produces:
  - specfuse/loop/lint_plan.py
  - tests/test_decision_citation_lint.py
---

# Lint citations and non-restatement

**Objective.** A feature's gate cannot arm while an artifact cites a decision ID
absent from `DECISIONS.md`, or reproduces a decision's statement instead of
citing its ID. ERROR, not WARN.

**Context.** FEAT-2026-0058/T02, gate 1, depends on T01. This is the feature's
enforcement, and `PLAN.md` D1 bounds it deliberately: **reference integrity**
and **non-restatement**, never contradiction detection. Detecting that prose
*contradicts* a registry entry is a semantic judgment that would fire on every
paraphrase or on nothing, and `[FEAT-2026-0071/G1-CLOSE]` names shipping a
partial guard described as a total one as the way unguarded fields stop being
reviewed.

Non-restatement is the load-bearing half: if artifacts may only cite, there is
no second copy to drift. Reference integrity alone would have missed
FEAT-2026-0066's dropped table row entirely.

ERROR severity is earned by measurement, not asserted — `PLAN.md` D2: 66 feature
folders, 6 carrying decisions-prose, 2 live. Both sibling checks in this file
are WARN because their populated tree was already in violation; this one is not.

Lands in `lint_plan.py` beside `check_produces_shape` and
`check_closing_guard_literals`, reusing the walk they already perform.

**Acceptance criteria.**

1. `tests/test_decision_citation_lint.py::TestCitationIntegrity::test_dangling_decision_id_is_an_error`
   fails on HEAD before this unit runs and passes after: an artifact citing an ID
   absent from the feature's `DECISIONS.md` produces an ERROR and a non-zero
   exit.
2. An artifact reproducing a decision's **statement text** instead of citing its
   ID is an ERROR. A test pins the failure this feature was filed for: a WU body
   restating a decision with one clause altered is caught, since that is
   FEAT-2026-0066's dropped-row shape.
3. **A legitimate quotation is not a false positive.** The exemption is
   documented and tested — a close WU quoting a decision while also citing its ID
   passes. An over-eager matcher blocks arming, which is worse than the WARN it
   replaced.
4. `done` and `abandoned` features are exempt as sealed history, the same
   exemption `check_closing_guard_literals` applies, asserted directly.
5. A feature with **no** `DECISIONS.md` is not an error: the registry is opt-in
   per feature, and 60 of 66 folders have none. Only a feature that has one is
   held to it.
6. **The check runs clean over this repository's real tree**, with the
   FEAT-2026-0050 repair merged (see `GATE-01.md`'s precondition). Asserted by a
   test that runs it over `.specfuse/features/` and expects zero errors — the
   satisfiability claim made falsifiable rather than assumed.
7. `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0058-decision-registry`
   exits 0.

**Do not touch.** `.specfuse/templates/DECISIONS.template.md` and the format
parser — T01 owns those; this unit consumes them. `closing_requirements.py`
(D4). The override provenance validation — T03 owns it.

**Verification.** `./scripts/smoke-test.sh` — run unsandboxed.

**Escalation triggers.** Report `status: blocked` if the non-restatement matcher
cannot separate a citation from a restatement without firing on legitimate
quotation — checked by running it over the six decisions-prose PLAN files in the
tree. A matcher that fires on correct prose would make arming fail for the wrong
reason, and shipping it as a WARN to dodge that would be D2 reversed without
saying so.

**Note.** This unit edits `specfuse/loop/lint_plan.py`, which is on the driver's
importable surface. Whichever of T02/T03 runs second halts the run for a driver
restart (FEAT-2026-0075). Expected, not a fault — the conductor re-dispatches a
fresh driver itself since #2321.
