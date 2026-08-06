---
id: FEAT-2026-0056/T06
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
oracle_env: macos_local
model: sonnet
effort: medium
human_only: true
produces_driver_helper:
  - specfuse.loop.lint_closing.check_criteria_state_well_formed
produces:
  - tests/test_lint_closing_criteria_pristine.py
generated_surfaces: []
gate_set: code
driver_version: 0.9.3
started_at: 2026-08-06T02:10:54.310255+00:00
duration_seconds: 746.265
cost_usd: 2.205899
input_tokens: 4228
output_tokens: 15682
---

# Stop a freshly seeded criteria artifact from failing its own lint

**Objective.** Narrow `check_criteria_state_well_formed` so a **pristine** seeded
entry — one no close has annotated yet — is not a finding, while every partially
annotated entry and every `broad` carry-forward stays exactly as blocking as T03
shipped it.

**Context.** This is `FEAT-2026-0056/T06`, gate 2. Read `PLAN.md`, `GATE-02.md`,
`RETROSPECTIVE.md` § *Finding 2* in this folder, and `.specfuse/rules/close-discipline.md`
§5 before editing.

Gate 1 composed two individually correct units into a blocking defect. T02's
criterion 6 requires every seeded entry to omit `kind:`; T03's criterion 6 requires
a missing `kind:` to be exactly one blocking finding. Gate 1's close seeded this
feature's own gate-1 artifact through the real entrypoint and linted it untouched:

```
$ python3 .specfuse/scripts/lint_plan.py <temp copy of this feature folder> --closing
FAIL — 42 unmet closing requirement(s):
  - close-intermediate-f: T01#1: missing kind: — would fail check_criteria_state_well_formed after squash
  - close-intermediate-f: T01#2: missing kind: — would fail check_criteria_state_well_formed after squash
  ... (41 × close-intermediate-f, one per seeded criterion)
```

So from the moment a driver carrying T02 is running, **every** `close` and
`close-intermediate` dispatch in this repo starts with a red
`specfuse-lint --closing` and stays red until the close hand-annotates a `kind:` and
a `state:` for every acceptance criterion of every substantive work unit in its
gate. Gate 1 shipped no mechanism to fill them in. A feature whose purpose is to make
closes cheaper currently makes every close more expensive, and the feature's own
`G2-CLOSE` would inherit the same red.

`PLAN.md`'s escalation-predicate analysis asked what the rule reports on an input in
its intended **final** state and correctly answered *zero*. Nothing asked what it
reports on the **initial** state the driver itself creates, and that is the state
every close now begins in. This unit answers the second half.

**Why the pristine-skip and not the two alternatives.** Gate 1's retrospective named
three shapes and left the choice to the operator; `GATE-02-REVIEW.md` records that
choice and its reasoning, and it is open to veto at arming. In short:

- *Seed entries with a `kind` the close may correct* is rejected: `close-discipline.md`
  §5 states that `kind` and `state` are written by the close that ran the oracle and
  are **never inferred by a reader**. Seeding a guess violates the contract this
  feature just documented, one gate after documenting it.
- *Give the close a helper that fills the artifact from the oracles it already ran*
  is rejected for this gate: the driver cannot know which oracle proved which
  criterion — that mapping is exactly the judgement the close makes.
- *Narrow the requirement so it fires only once a close has begun recording* is what
  this unit builds, at the **entry** level rather than the `applies_when` level. T03's
  escalation triggers put changing `applies_when` dispatch out of scope for good
  reason, and the entry-level skip needs no registry change.

**Pristine is defined structurally, not by intent.** An entry is pristine iff
`state == "unverified"` **and** `kind is None` **and** `oracle is None` — byte for
byte what `_precreate_criteria_state_stub` writes and nothing else. Any deviation
means a close touched the entry, and a touched entry is this requirement's concern
again. In particular `state: pass` with `kind` absent is **not** pristine and remains
one finding.

**This narrows a blocking check, so `planning-discipline.md` §4 binds.** The runtime
probe is an arming precondition recorded in `GATE-02.md` § *Arming discipline*; it is
not this session's to self-report as sufficient. `human_only: true` is set on this WU
for the same reason.

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`,
`verification-discipline.md`.

**Acceptance criteria.**

1. `tests/test_lint_closing_criteria_pristine.py::test_pristine_seeded_entry_is_not_a_finding`
   exists and **fails on HEAD before this WU's edits**. Record the failing output in
   the RESULT block before editing production code. A new file, not an edit to T03's
   `tests/test_lint_closing_criteria.py` — see criterion 6 and *Do not touch*.
2. `check_criteria_state_well_formed` returns **zero** findings for an artifact whose
   every entry has `state: unverified`, no `kind:`, and no `oracle:` — asserted for
   an artifact holding more than one such entry.
3. It returns **exactly one** finding for an entry with `state: pass` and no `kind:`
   — annotation begun, kind missing.
4. It returns **exactly one** finding for an entry with `state: unverified`, no
   `kind:`, and an `oracle:` present — annotation begun, kind missing.
5. It returns **exactly one** finding for a `broad` entry with `state: pass` whose
   `attempt:` differs from the current attempt. This is T03's criterion 8 and the
   feature's soundness contract; a narrowing that weakens it fails this WU.
6. T03's `tests/test_lint_closing_criteria.py` is **unedited** and still passes
   whole: `python3 -m unittest tests.test_lint_closing_criteria -v` exits 0 and
   reports the same test count as the same command on HEAD. Record both counts. The
   narrowing must be delivered without deleting or relaxing a T03 assertion; if one
   has to go, that is a contract change and an escalation, not a test edit.
7. **Initial-state probe.** Seed a scratch copy of a real feature folder through the
   real `loop._precreate_criteria_state_stub`, then lint it: the finding count
   attributable to `close-l` / `close-intermediate-f` is **zero** after this WU, where
   it is **41** on HEAD for this feature's gate 1. Paste both numbers and the command.
8. **Positive control.** In that same scratch copy, annotate one entry with
   `- **kind:** \`bogus\`` and re-lint: exactly one finding naming that entry's
   `criterion_id` appears. Paste it. A sweep that cannot distinguish "correctly
   silent" from "not running" has measured nothing —
   `[FEAT-2026-0056/G1-CLOSE-INTERMEDIATE/console-script-is-not-the-tree]` rule (b).
9. **Corpus sweep, from source.** `for d in .specfuse/features/*/; do python3 .specfuse/scripts/lint_plan.py "$d" --closing; done`
   reports no finding attributable to `close-l` or `close-intermediate-f`. Use the
   `.specfuse/scripts/` shim, **not** the installed `specfuse-lint` console script —
   that script resolves `specfuse.loop` from `site-packages`, not from the working
   tree, and gate 1's sweep measured the wrong program because of it.
10. The `close-l` and `close-intermediate-f` records in
    `specfuse/loop/closing_requirements.py` still carry
    `applies_when="criteria_artifact_present"` and
    `enforced_by="check_criteria_state_well_formed"` — the narrowing lives in the
    check, not in the registry. Assert by import, not by reading.
11. `python3 -c "from specfuse.loop.lint_closing import check_criteria_state_well_formed"`
    exits 0.
12. The test named in criterion 1 **passes** after this WU's edits.

**Do not touch.** `tests/test_lint_closing_criteria.py` — T03's, and criterion 6 is
an assertion that it is unedited, not a licence to adjust it. The requirement records
in `specfuse/loop/closing_requirements.py` stay as T03 declared them (criterion 10 is
likewise an assertion about them). `_precreate_criteria_state_stub` — the seeded
shape is T02's contract and this unit adapts the reader to it, not the writer to the
reader. `ORACLE_KINDS` and `CRITERION_STATES` (T01's; read them, do not re-list the
values in `lint_closing.py` — T03's criterion 9 still binds).
`build_reverification_worklist` (T07's scope). `.specfuse/verification.yml`.
`.specfuse/rules/` and `.specfuse/templates/`. `GATE-01.md` and gate 1's work units.
Any other feature's folder under `.specfuse/features/`, including any criteria
artifact belonging to one — criterion 7's probe runs against a **scratch copy**, never
in place. Generated directories, secrets, `.git/`. The driver owns all git operations
— you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage` (`--fail-under=90`), `leak-scan`, `event-type-gate`. In addition
run criterion 11's symbol-existence check verbatim, and criteria 7, 8, and 9 with their
full output pasted — not summarized. Criterion 1's red observation must be recorded
before production edits.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
criterion 5 cannot be kept true alongside criterion 2, meaning the pristine-skip
cannot be expressed without weakening the `broad` carry-forward refusal — that is a
design change to the feature's soundness contract and an operator decision, not
something to reconcile inside this WU; criterion 9's sweep returns a finding
attributable to `close-l` / `close-intermediate-f` on a feature this unit did not
touch; criterion 8's positive control produces **no** finding, meaning the check is
not running at all and criteria 7 and 9 have measured nothing; or the pristine-skip
would require changing how `applies_when` is dispatched for the existing values.
