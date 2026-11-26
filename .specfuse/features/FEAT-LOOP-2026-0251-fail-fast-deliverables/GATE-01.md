---
gate: 1
status: awaiting_review
feature_oracle: "python3 -m unittest tests.test_fail_fast_deliverables -v -b"
cost_budget_usd: 14.00
broad_run:
  tree: 07bbf72d1e7af3c1a03af605f40e5563dc3a18db:0ec7c6da6e74f0b56753f09657b654a6d289b91b:12064a6191eeb830a9826d911a8543fbaba3da75:1335b4a33bdabb0f79b5cefbbb3a895f1a6070d9:20d5146c893abcac47015a30987b44b2a3dc7c03:27968248a450a842ccd187b7dce0fb0ded934866:287efde8f90320baffac08f5f3287b9456a65cb9:2e29b2f7e073a0cbe290f01d3b397e1cdd10c81c:42796ea0e0a6c03811b0e4bc9dbd3b5ee62dd2e4:4acc6dfc5e8cece358c167d876515eba4a39a500:56ae45adcc17a1292977c436fd195ef8c61cc9e4:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:91772e5b1214def7917a34e770c1485cd953efe3:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d74b7d113b844e84f0009098f576fd28477f072d:e3b0de29b81a6c8e0abeacb3898519b98014b9ef:fa2f4f88657587b6e3b560977858810846b1d366
  ran_at: 2026-11-26T16:51:24.463202+00:00
  ok: true
  failing: []
---

# Gate 1 — a missing deliverable is refused before any verification gate runs

## Definition of done

**Stated as an outcome.** In temporary feature folders, with a stubbed agent session that
leaves a known diff and a `verify_fn` that counts its calls:

1. **`produces_not_in_diff` early.** An attempt whose diff leaves a declared `produces:` path
   untouched, with no `produces_unchanged:` / `produces_amended:` in its RESULT, ends
   `produces_not_in_diff` with `verify_fn` called zero times, `verify_seconds: 0` and no
   `gate_result` events. The same unit with the path changed calls `verify_fn` once and passes.
2. **Presence early.** `deliverable_missing` (a declared path absent or empty) and
   `no_deliverable_files` (the diff names only the unit file and events) are likewise refused
   with `verify_fn` never called.
3. **Opt-out.** With `defaults.fail_fast_deliverables: false`, each of the three cases calls
   `verify_fn` before refusing, with the same outcome and failure class as today.
4. **Tree and note.** An early refusal keeps or resets the tree per
   `defaults.retain_on_guard_refusal`, as the late refusal does; its retry note states that
   verification did not run and lists the paths this attempt changed (or says it changed
   none).
5. **Arm-time warning.** `specfuse lint` prints a WARN for a dispatchable unit whose `produces:`
   path appears nowhere in its body, by full path or file name, and stays silent when it does.
6. **Nothing else changes.** Every existing test of the three guards passes unchanged, apart
   from assertions on the order of `verify` and the guard, and edits forced by moving code into
   a shared helper or by new lint wording that a text-matching assertion picks up. No such edit
   removes or weakens an assertion, and each is named in the close. *(Widened 2026-11-26 by the
   operator after the first close, #3609.)*

**Precedence when two refusals apply** *(stated 2026-11-26 by the operator after the first
close, #3608; widened after the second close, #3610).* Under the default order a deliverable
refusal (`produces_not_in_diff`, `deliverable_missing`, `no_deliverable_files`) takes
precedence over every check that runs after the agent session: the verification gates and
the later guards, including `files_changed_mismatch`, `smoke_import_failed`, the
blocked-verdict guard and the closing-deliverable guards. An attempt that trips a
deliverable refusal and one of those checks records the deliverable refusal, and the other
check runs only on a later attempt, once the deliverable is fixed. With
`fail_fast_deliverables: false` the old order and its outcomes hold. The
`files_changed_mismatch` pair is asserted on both sides by
`TestProducesNotInDiffEarly.test_deliverable_refusal_outranks_files_changed_mismatch`.
Clause 3's "same outcome and failure class" applies to inputs that trip only one refusal.

One side effect follows and is accepted. The early refusal keeps or resets the tree per
`defaults.retain_on_guard_refusal` (clause 4), so by default it keeps the tree. The
smoke-import and closing-deliverable refusals it now outranks always reset it. On an input
that trips both, the next attempt therefore starts from the kept tree, not a clean one.

The `feature_oracle` proves 1–5. It is red on the current tree; `FEAT-LOOP-2026-0251/T01` is the
walking skeleton that creates `tests/test_fail_fast_deliverables.py` and turns clause 1 green,
with every other class `unittest.skip` naming its owner (T02–T04). A skip surviving to the close
is a hollow oracle.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **One decision, two call sites.** The early and late checks call the same helper; a
  duplicated condition is a defect.
- **Positive controls.** Clause 1 pairs a refused attempt with a passing one; clause 3 pairs
  the opt-out with the default; clause 5 pairs a mentioned path with an unmentioned one.
- **Counted, not inferred.** "Verification did not run" is asserted by a call counter on
  `verify_fn`, never by timing.
- **Expected self-halt.** `loop.py` and `lint_plan.py` are judge surfaces; acknowledge the stop
  with your own reason and `/unblock-wu`.

## Reflection notes

<Written by the human at review time.>
