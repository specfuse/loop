---
id: FEAT-2026-0053/T05
type: implementation
status: draft
attempts: 0
planned_cost_usd: 3.50
produces:
  - specfuse/loop/arm_txn.py
  - tests/test_arm_txn.py
---

# Arm transaction — the pure module behind a one-commit arm

**Objective.** Produce `specfuse/loop/arm_txn.py`: a pure, side-effect-scoped
module that computes and applies the complete set of file writes an arm
consists of, so the caller can commit all of them in exactly one bookkeeping
commit.

**Context.** Correlation ID `FEAT-2026-0053/T05`. Gate 2 makes `auto` real: when
the arm predicate (`specfuse/loop/arm_eval.py`, T03) returns `would_arm: True`
on an `auto` feature, the driver arms the next gate itself instead of parking
for a human. **The load-bearing property of that arm is atomicity** — a crash
partway through must never leave a feature half-armed (some drafts flipped to
`pending`, the gate still `awaiting_review`, or the reverse). The design
answer is a single commit containing every write, and this WU produces the
piece that makes a single commit possible: one function that returns the whole
write set, and one that applies it.

This WU deliberately mirrors the T03 → T04 split that gate 1 proved out: the
decision/computation lives in a pure module with its own focused test suite,
and the driver wiring is a separate unit (T06). Keeping git out of this module
is what makes it testable — **this module performs no git operations at all**,
not even tag creation. It returns the tag *name* as a string; T06 creates the
tag and owns the commit.

An arm consists of exactly these writes:

- every gate-`N+1` work-unit file whose `status` is `draft` flips to `pending`;
- the just-closed gate `N`'s gate file flips `awaiting_review` → `passed`;
- `events.jsonl` (appended by the caller, but part of the same write set so the
  caller commits it together).

The revert point is a tag placed at HEAD *before* the arm commit, named
`pre-arm/<feature-id>/gate-<N>`. Because the tag precedes the commit, an
operator who wants the pre-arm state back resets to the tag and loses exactly
the arm and nothing else.

Binding rules apply by reference: `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_arm_txn.py::TestPlanArmTransaction::test_plan_lists_draft_wus_and_gate_file`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist — red).
2. `specfuse/loop/arm_txn.py` exposes `plan_arm_transaction(feature_dir,
   just_closed_gate)` returning a structure that carries: the list of gate-`N+1`
   WU file paths currently at `status: draft`, the gate-`N` file path, the tag
   name, and a single deduplicated `paths` list containing every file the arm
   writes. A symbol check passes:
   `python3 -c "from specfuse.loop.arm_txn import plan_arm_transaction, apply_arm_transaction, arm_tag_name"`.
3. `arm_tag_name(feature_id, gate)` returns exactly
   `pre-arm/<feature-id>/gate-<N>` — asserted against the literal string
   `pre-arm/FEAT-2026-0053/gate-1` for that input.
4. `apply_arm_transaction(txn)` flips every listed draft WU's `status` to
   `pending` and the gate-`N` file's `status` from `awaiting_review` to
   `passed`, and changes no other frontmatter field and no body text on any
   file it touches.
5. `apply_arm_transaction` is idempotent: a second call against the
   already-applied state writes nothing and reports an empty applied-path list.
6. A transaction planned when gate `N+1` holds zero `draft` WUs (already armed,
   or no such gate) reports empty, and `apply_arm_transaction` on it writes
   nothing — an empty arm must never produce a commit.
7. The module performs no git operations: `grep -nE "subprocess|\\bgit\\(" specfuse/loop/arm_txn.py`
   produces no output.
8. `tests/test_arm_txn.py` covers criteria 2–7 with at least one case each, and
   `python3 -m unittest tests.test_arm_txn -v` exits 0 — including the criterion-1
   test, now green.

**Do not touch.** `specfuse/loop/arm_eval.py` and `specfuse/loop/plan_baseline.py`
— this module consumes neither's internals and must not modify either; if
building this reveals a defect in one, block rather than patch it here. The
driver's close/arm control flow — that is T06's, and editing it here breaks the
module/wiring split this WU exists to preserve. The contract-field lint — T07.
Generated directories, secrets, `.git/`. The driver owns all git — you edit
files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` set in `.specfuse/verification.yml`. Scoped
iteration run: `python3 -m unittest tests.test_arm_txn -v`. Plus the explicit
symbol-existence check in criterion 2 and the no-git grep in criterion 7 — the
`code` set cannot detect a missing symbol that no test imports, and cannot
detect git creeping into a module that is supposed to stay pure.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
the gate-`N+1` WU files cannot be flipped without also rewriting body content
(a frontmatter writer that reserializes and reorders the whole file is not an
acceptable implementation of criterion 4 — the arm commit must be readable as a
status flip and nothing else); or if `specfuse/loop/arm_txn.py` is absent from
the files you edited when you would otherwise report complete — do not claim
complete without the module.
