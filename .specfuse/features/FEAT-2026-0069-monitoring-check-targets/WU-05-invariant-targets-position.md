---
id: FEAT-2026-0069/T05
type: implementation
status: draft
attempts: 0
planned_cost_usd: 2.00
oracle_env: macos_local
produces:
  - specfuse/loop/lint_monitoring.py
  - tests/test_lint_monitoring.py
  - docs/concepts/monitoring-schema.md
---

# Decide `invariant`'s `targets` position, and correct the stale `_check_targets` docstring

**Objective.** Turn the `invariant` × `targets` fall-through gate 1 shipped by accident
into a decision with a test behind it, and correct the `_check_targets` docstring T04
made wrong.

**Context.** This is `FEAT-2026-0069/T05`, gate 2's one work unit that is independent of
the discovery re-key (`depends_on: []`). It is the "residual staleness this close
deliberately did not fix"
item from `RETROSPECTIVE.md` (§ *What I'd change*), which routed both fixes here on
purpose: a `close` WU editing shipped source is the pattern that makes closes
untrustworthy, so gate 1's close recorded them and left them.

Two facts from gate 1, both verifiable in `specfuse/loop/lint_monitoring.py`:

1. **`invariant` permits `targets` with no required coordinates** — not by decision, but
   because it appears in neither `_TARGET_REQUIRED_FIELDS` (`lint_monitoring.py:260-264`)
   nor `_TARGETLESS_CHECK_TYPES` (`:266`), so `_check_targets` falls through to
   "permitted, nothing required." No WU criterion in gate 1 names it, the docs table has
   no `invariant` row for `targets`, and `RETROSPECTIVE.md` flags it in the
   consumer-visible contract-change table as item 6, *"never an explicit decision."*
2. **`_check_targets`'s docstring says `targets` "is required only for `dlq`"**
   (`lint_monitoring.py:275-279`). T04 then made `targets` required on `queue-stalled`
   too (`:236-242`), so the docstring is wrong. `docs/concepts/monitoring-schema.md` was
   rewritten by gate 1's close to state the matrix authoritatively and no longer defers to
   that docstring, so no reader is currently routed to the wrong text — but the wrong text
   is still there.

**The position this WU implements, and why.** `invariant` **must not carry `targets`** —
add it to `_TARGETLESS_CHECK_TYPES`. The reason is the one `PLAN.md`'s existing-mechanism
search already records: `targets` is the *generalization of `fingerprint_by`*, and
`invariant` is the one check type that already carries `fingerprint_by` as a required
field (`lint_monitoring.py:243-249`). Permitting both on the same check gives that check
two competing enumeration keys, and FEAT-2026-0040's fingerprint model — which `PLAN.md`
binds to include the target key — would have to reconcile them with nothing in the schema
saying which wins. Enumeration for `invariant` goes through `fingerprint_by`; that is
what it is for.

This is the cheapest moment to take that position: gate 1's permissive fall-through has
never been merged or released, so no consumer has ever seen it. Rejecting later, after a
release, would be a breaking change; rejecting now is a decision. The reverse ordering is
always available — a rejected field can be permitted later without breaking anyone.

**`Red-test exempt`: not claimed.** AC1 names a genuinely red test.

**Acceptance criteria.**

1. `tests/test_lint_monitoring.py::TestInvariantTargetsRejected::test_invariant_check_carrying_targets_is_a_finding`
   exists and **fails on HEAD before this WU runs** —
   `python3 -m unittest tests.test_lint_monitoring.TestInvariantTargetsRejected -v` exits
   non-zero (today the test file has no such class, which counts as red; and the current
   validator emits **zero** findings for an `invariant` check carrying `targets`, so the
   assertion would fail even if the class existed).
2. `invariant` is a member of `_TARGETLESS_CHECK_TYPES` in
   `specfuse/loop/lint_monitoring.py`, so an `invariant` check carrying `targets` produces
   the finding `'invariant' check must not carry 'targets'`.
3. The same scoped test **passes after this WU's edits** —
   `python3 -m unittest tests.test_lint_monitoring.TestInvariantTargetsRejected -v` exits
   zero.
4. A companion positive test asserts an `invariant` check **without** `targets` and with
   both `query` and `fingerprint_by` still validates clean (zero findings) — the
   satisfiability check `planning-discipline.md` §2 requires for a permissive→blocking
   flip. Name it
   `tests/test_lint_monitoring.py::TestInvariantTargetsRejected::test_invariant_without_targets_still_validates_clean`.
5. `_check_targets`'s docstring in `specfuse/loop/lint_monitoring.py` no longer says
   `targets` is required only for `dlq`. It names both required-`targets` types (`dlq`,
   `queue-stalled`) and both rejected types as they stand after AC2 (`error-logs`,
   `http-5xx`, `invariant`). `grep -n "required only for" specfuse/loop/lint_monitoring.py`
   returns zero hits.
6. `docs/concepts/monitoring-schema.md`'s check-targets matrix carries an explicit
   `invariant` row reading *must not* carry `targets`, with the one-line reason from the
   Context above (`fingerprint_by` is already that check type's enumeration key).
7. `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` exits
   zero — the shipped example's `invariant` check is target-less today
   (`.specfuse/monitoring.yml.example:113-115`, and the only other `type: invariant` in
   the tree is its packaged copy `specfuse/loop/data/monitoring.yml.example:113`), so this
   flip must not turn the repo's own `monitoring-example-lint` gate red. **Re-run
   `grep -rn "type: invariant" -A6 .specfuse specfuse plugins docs` before editing the
   validator**; if any surface carries `targets` on an `invariant` check, see the
   escalation triggers.
8. `python3 -m unittest discover -s tests -v` exits zero — in particular
   `tests/test_monitoring_fenced_blocks.py`, which extracts every ```yaml block from the
   declared surfaces and runs each through the validator, must stay green.

**Do not touch.** `_TARGET_REQUIRED_FIELDS` — `invariant` gets no required coordinates,
it gets no `targets` at all; adding a coordinate there would be the *other* position, not
this one. The `dlq` / `queue-stalled` / `heartbeat` / `error-logs` / `http-5xx` rows of
either lookup table — gate 1 decided each of those with a test and this WU does not
relitigate them. `tests/test_derive_monitoring_discovery.py` — that file is
`FEAT-2026-0069/T06`'s and `T07`'s deliverable in this same gate, and nothing here needs
it. Gate 1's WU files and `GATE-01.md`. `PLAN.md`'s `status` field. `.git/`, secrets. The
driver owns all git operations — you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set from `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage`, `leak-scan`, `monitoring-example-lint`, `leak-scan-hook`,
`sync-scaffold-bats`, `init-sh-shim-bats`, `init-skills-bats`. Scoped red/green proof:
`python3 -m unittest tests.test_lint_monitoring.TestInvariantTargetsRejected -v`. Symbol
check (`/authoring-work-units` §9):
`python3 -c "from specfuse.loop.lint_monitoring import _TARGETLESS_CHECK_TYPES; assert 'invariant' in _TARGETLESS_CHECK_TYPES"`.

> Sandbox note (`.specfuse/LEARNINGS.md` `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`): the
> three `bats` gates call `mktemp -d` in `setup`, which the default session sandbox
> denies (`Operation not permitted`) before any assertion runs. Report which sandbox each
> gate ran under; do not read a sandbox denial as a regression.

**Escalation triggers.** Emit `status: blocked` if AC7's pre-check shows any shipped
surface already carries `targets` on an `invariant` check — that would make this flip
unsatisfiable on a correct tree (`planning-discipline.md` §2) and needs a migrate step
first, exactly the expand → migrate → contract failure gate 1 paid $5.26 to learn. Also
block if a human reviewer's `GATE-02-REVIEW.md` decision recorded the *permissive*
position instead: this WU implements rejection, and silently implementing the opposite of
an armed decision is worse than halting. Blocked is a respectable outcome
(`result-contract.md` rule 4).
</content>
