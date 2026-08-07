---
id: FEAT-2026-0075/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.00
oracle_env: macos_local
provenance: "RETROSPECTIVE.md gate 1 §4, the finding the close was forbidden from repairing: `T03`'s own `files_touched` included `specfuse/loop/data/schemas/driver-event.schema.json`, which the `specfuse/loop/` prefix flags as a driver-module edit even though a JSON data file is read from disk at runtime and never enters `sys.modules`. The close states plainly that gate 1 is warn-only so the false positive costs only noise, and that gate 2 must narrow the predicate before building anything blocking on it. This WU is that narrowing, and it is scheduled first in gate 2 because T06 turns the same predicate into a process halt."
produces_driver_helper:
  - specfuse.loop.driver_edit.is_driver_module_path
produces:
  - specfuse/loop/driver_edit.py
  - tests/test_driver_module_surface.py
generated_surfaces: []
model: sonnet
effort: medium
gate_set: code
---

# Narrow driver-staleness detection to the importable surface

**Objective.** Make `specfuse/loop/driver_edit.py`'s predicate mean what its own
docstring already claims — "the driver's own importable surface" — by excluding paths
that cannot be cached in `sys.modules`, so that T06 can build a process halt on it
without halting a run over a documentation or schema edit.

**Incremental edit to an existing file.** `specfuse/loop/driver_edit.py` appears in
this unit's `produces:` even though `T01` created it: this WU narrows the predicate
**in place**, replacing the bare prefix match with an importable-surface test and
adding `is_driver_module_path`. The path is declared rather than dropped because the
unit does modify that file, and `PLAN.md`'s single-detector constraint requires the
narrowing land here rather than in a second module.

**Context.** This is `FEAT-2026-0075/T04`, gate 2's first unit. `T01` built
`driver_edit.py` with `DRIVER_MODULE_PREFIXES = ("specfuse/loop/",)` and two bare
`str.startswith` predicates. Gate 1 is warn-only, so the prefix being broader than the
claim cost only a spurious line. Gate 2 converts the same predicate into a halt, and a
halt over `specfuse/loop/data/docs/methodology.md` is a run stopped for no reason.

Read `RETROSPECTIVE.md` § *4. The warning's negative case — and a design finding for
gate 2*, `GATE-02.md`, and `GATE-02-REVIEW.md` before editing.

**The measured false-positive rate, so this is not scoped from intuition.**
`G1-PLAN` swept all 57 feature folders in `.specfuse/features/` (90 gates), matching
each work unit's declared `produces:` against the current prefix:

```
gates flagged by BROAD prefix specfuse/loop/  : 41
gates flagged by NARROW (.py, excl data/)     : 38
gates flagged ONLY by broad (false positives) : 3
  FEAT-2026-0039 gate 2 — data/rules/design-for-diagnosis.md,
                          data/monitoring.overrides.yml.example,
                          data/monitoring-secrets-checklist.md
  FEAT-2026-0040 gate 3 — data/workflows/specfuse-monitor.yml
  FEAT-2026-0053 gate 3 — data/docs/methodology.md,
                          data/docs/concepts/autonomy-stop-classes.md,
                          data/docs/concepts/adopting-auto-mode.md
```

Three gates in the repository's history — 7.3% of all hits — are pure false positives:
docs, example configs and a workflow file, none of which is importable. Under T06 each
would have halted a run.

**Existing-mechanism search (`planning-discipline.md` §1).** Commands run by `G1-PLAN`:
`grep -n "DRIVER_MODULE_PREFIXES\|startswith" specfuse/loop/driver_edit.py` and
`find specfuse/loop/data -name "*.py" | wc -l`. Verdict: **found the mechanism,
narrowing it in place — no new module and no second predicate.** `driver_edit.py` is
the one detector; `arm_eval.py`'s `JUDGE_PATHS` also lists `specfuse/loop/`, but that
tuple answers a different question (which surfaces may a drafted WU touch) and is
deliberately left alone — see `GATE-02-REVIEW.md` § *What was rejected*. `find` returns
**0** `.py` files under `specfuse/loop/data/`, so the two conditions below do not
overlap today; both are still stated, because a scaffold payload `.py` under `data/` is
a plausible future and would otherwise silently re-open the false positive.

**The rule.** A path is a driver-module path when **all** of:

1. it starts with a prefix in `DRIVER_MODULE_PREFIXES`, **and**
2. it ends in `.py`, **and**
3. it does not start with a prefix in the new `DRIVER_DATA_PREFIXES`
   (`("specfuse/loop/data/",)`).

Condition 3 is redundant with 2 today and is stated anyway, for the reason above.

**One predicate, two callers.** `diff_edits_driver` and `driver_paths_in` must both
delegate to the new `is_driver_module_path`; they must not each re-implement the rule.
A second copy of the rule is how a narrowing gets applied on one path and not the
other, and T06 uses `driver_paths_in` while T02's existing call site uses both.

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `correlation-ids.md`, `planning-discipline.md`.

**Acceptance criteria.**

1. `tests/test_driver_module_surface.py::test_data_path_is_not_a_driver_module`
   exists and **fails on HEAD before this WU's edits** — it asserts
   `diff_edits_driver(["specfuse/loop/data/schemas/driver-event.schema.json"])` is
   `False`, which is `True` today. Paste the failing output in the RESULT block before
   editing production code.
2. `specfuse/loop/driver_edit.py` exports `is_driver_module_path(path) -> bool`
   implementing the three-condition rule above, and exports
   `DRIVER_DATA_PREFIXES = ("specfuse/loop/data/",)`.
3. `diff_edits_driver` and `driver_paths_in` both delegate to
   `is_driver_module_path`. `grep -n "startswith" specfuse/loop/driver_edit.py` shows
   the prefix comparisons occurring **only** inside `is_driver_module_path`. Paste the
   grep.
4. Positive cases still detected, each asserted separately:
   `specfuse/loop/loop.py`, `specfuse/loop/driver_edit.py`, `specfuse/loop/arm_eval.py`.
5. Negative cases now silent, each asserted separately:
   `specfuse/loop/data/schemas/driver-event.schema.json`,
   `specfuse/loop/data/docs/methodology.md`,
   `specfuse/loop/data/templates/WU.template.md`,
   `specfuse/loop/data/monitoring.yml.example`, and a hypothetical
   `specfuse/loop/data/scaffold_payload.py` (condition 3's reason for existing —
   assert it is `False` even though it ends in `.py`).
6. `driver_edit.py` stays pure apart from `changed_paths_for_commit`: `is_driver_module_path`
   performs no I/O and no filesystem existence check. The predicate answers a question
   about path *shape*, not about what is on disk — a deleted or renamed module is still
   a driver edit.
7. The module remains free of a `specfuse.loop.loop` import (T01's no-cycle property):
   `grep -n "specfuse.loop.loop" specfuse/loop/driver_edit.py` shows only the docstring
   line. Paste the grep.
8. `python3 -c "from specfuse.loop.driver_edit import is_driver_module_path, DRIVER_DATA_PREFIXES"`
   exits 0.
9. **The sweep is re-run against the real narrowed code**, not against `G1-PLAN`'s
   offline reimplementation, and its output is pasted: the counts must come out
   41 broad / 38 narrow / 3 false-positive-only, or the discrepancy must be explained.
   This is `planning-discipline.md` §4's runtime probe for this unit and it is
   `GATE-02.md`'s recorded arming precondition.
10. Any gate-1 test that asserts the old broad behaviour is updated rather than
    deleted, and the RESULT names each such test and what changed about it.
11. The full `code` gate set passes, including `coverage report --fail-under=90`.

**Do not touch.** `specfuse/loop/arm_eval.py` — its `JUDGE_PATHS` tuple answers a
different question and gate 2 deliberately leaves it alone. `specfuse/loop/loop.py` —
T06's surface; this unit changes the predicate, not any call site. The gate-completion
summary and event emission. `.specfuse/verification.yml`. `.specfuse/rules/` and
`.specfuse/templates/`. `GATE-01.md` and gate 1's work units. Any other feature's
folder under `.specfuse/features/`. Generated directories, secrets, `.git/`. The driver
owns all git operations — you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage` (`--fail-under=90`), `leak-scan`, `event-type-gate`. In addition
run criterion 3's and criterion 7's greps verbatim, criterion 8's symbol-existence
check, and criterion 9's sweep, pasting all four outputs. Do **not** report the running
driver's in-situ behaviour as evidence — this session's process predates your edits by
construction.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
narrowing turns a gate-1 test red in a way that cannot be resolved by updating that
test's expectation (which would mean gate 1 asserted the broad behaviour as a
contract, not as an accident, and the narrowing needs an operator decision); criterion
9's re-run disagrees with the 41/38/3 counts by more than the explanations you can
evidence, since T06 and `GATE-02.md`'s §2 answer both rest on those numbers; or
`is_driver_module_path` cannot be made the single site of the prefix comparison without
changing `changed_paths_for_commit`'s signature.
