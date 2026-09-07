---
id: FEAT-2026-0101/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
oracle_env: macos_local
produces:
  - specfuse/loop/lint_plan.py
  - tests/test_lint_feature_oracle_declared.py
---

# Refuse a gate that declares no oracle — ERROR when active, WARN otherwise

**Objective.** Add `lint_feature_oracle_declared`: a gate carrying no
`feature_oracle` is an ERROR when its feature is `active`, a WARN when it is
`planned` / `blocked` / `deferred`, and skipped when the gate is `passed` or the
feature is `done` / `abandoned`.

**Context.** FEAT-2026-0101/T03; read `PLAN.md`, especially its
Escalation-predicate-satisfiability section, which measured this rule against
the real corpus before it was drafted. Sibling rules to match in shape:
`lint_ac_observable` (ERROR with escape hatches) and
`lint_gate_proportionality` (WARN, because the judgement is an authoring one).
`lint_plan.py` already skips sealed WUs, so the skip vocabulary exists.

**The graduation is the whole design, and it is not negotiable downward.**
Scoping ERROR to "any non-`passed` gate in a non-`done` feature" — the obvious
first shape — fires on four correct inputs today and is therefore an
unsatisfiable predicate (`planning-discipline.md` §2). Graduating by **feature
status** makes the rule report zero ERRORs on the corpus as it stands and become
blocking exactly when a feature is picked up, which is the moment its author is
thinking about it. Do not "simplify" it back to a flat ERROR.

**The sweep is a command, not a claim.** `[FEAT-2026-0055/G1-CLOSE]`: a
criterion of the form "rule R reports zero findings over corpus C" must be
executed and counted, never reported as an agent's observation. One WU asserted
such a sweep and passed; the close ran it and found 15 ERRORs across 4 features.

**Acceptance criteria.**

- `tests/test_lint_feature_oracle_declared.py::test_active_feature_missing_oracle_is_error` fails on HEAD and passes after: a gate with no `feature_oracle` in an `active` feature reports ERROR naming the gate file.
- `::test_planned_feature_missing_oracle_is_warn`: the same gate in a `planned` feature reports WARN, not ERROR. Cover `blocked` and `deferred` in the same test or siblings.
- `::test_passed_gate_and_done_feature_are_skipped`: neither reports anything.
- `::test_declared_oracle_reports_nothing`: a gate carrying a non-empty `feature_oracle` is clean at every feature status.
- Corpus sweep, run as a command with counted output and pasted into the RESULT block: over every feature folder the rule reports **zero ERRORs** and **exactly four WARNs** — `FEAT-2026-0052/GATE-01`, `FEAT-2026-0081/GATE-01`, `FEAT-2026-0081/GATE-02`, `FEAT-2026-0082/GATE-01`. Any ERROR, or a WARN set that differs from those four, means the scoping is wrong — stop and escalate rather than adjusting the expected list.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `verify()` and the oracle runner (T01); the closing lint
(T02); templates, skills, `methodology.md` (T04); the four WARN-ing gate files
themselves — retrofitting them is explicitly out of scope in `PLAN.md` and would
make the sweep vacuous; `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus this
gate's `feature_oracle`.

**Escalation triggers.** Emit `status: blocked` if the sweep reports any ERROR
or a WARN set other than the four named above — that is the satisfiability
predicate failing, and the response is a diagnosis, not a widened skip list.
Also block if `lint_plan.py` has no access to the owning feature's status at the
point the gate is checked; threading it in may be right, but it changes the
lint's inputs and is an operator call.
</content>
