---
feature_id: FEAT-2026-0005
gate: 1
---

# Gate 1 retrospective — Combined close for single-gate features

## Summary

Gate 1 had one substantive work unit (T01). It completed in a single attempt with
no escalations, no retries, and no driver interventions. The feature itself
validated its core premise: a trivial change that would previously have cost four
closing dispatches completed cleanly in one.

---

## T01 — Add a `close` WU type that collapses the closing sequence

**Attempt count:** 1
**Cost:** $1.23 USD
**Token breakdown:** 29 input, 21 926 output, 1 972 014 cache-read, 81 430 cache-write
**Elapsed:** ~6 min 49 s (04:20:06 → 04:26:55 UTC)

### What worked

**Minimal, precise scope.** The WU file named exactly four touch points
(`lint_plan.py`, `loop.py`, `WU.template.md`, a new test file) and the agent
stayed within them. No drift into unrelated files.

**Reusing the `plannext` gate set.** Rather than adding a new gate entry to
`verification.yml`, the agent mapped `close → plannext` in `GATES_FOR_TYPE`.
`plannext` already runs `lint_plan.py` on the feature — which is exactly the
post-close structural-integrity check needed. The WU escalation trigger
anticipated this decision; agent chose correctly.

**Closing-check refactor was clean.** The original `lint()` guard
(`closing_found != CLOSING_SEQUENCE`) was replaced by a three-branch conditional:
`close` alone (valid only on single-gate), `CLOSING_SEQUENCE` (always valid), or
anything else (error). The `_CLOSING_TYPES` frozenset cleanly separated
"which types count as closing" from "what sequence they must form," avoiding
a second scan of `types_in_order`.

**CORRELATION_ID_RE updated.** The regex gained the `CLOSE` segment
(`G\d+-(RETRO|LESSONS|DOCS|PLAN|CLOSE)`) so `G1-CLOSE`-style IDs pass
validation. This was a non-obvious side-requirement — the WU spec did not call
it out, but the agent identified and fixed it without prompting.

**Test coverage — three assertions, all present.**
- `test_single_gate_close_passes`: single-gate feature with `close` WU passes lint.
- `test_two_gate_close_rejected`: two-gate feature with `close` WU produces an
  error naming the single-gate constraint.
- `test_four_wu_closing_sequence_still_passes`: uses the live
  `FEAT-2026-0001-health-endpoint` fixture as a regression guard, confirming
  existing four-WU features still lint cleanly.

**Template update was complete.** `WU.template.md` documents the `close` type in
both the frontmatter comment and the prose section, including the production
obligations (RETROSPECTIVE.md, LEARNINGS.md entries, docs/roadmap reconciliation,
terminal verdict) and the single-gate-only constraint.

### What failed

Nothing failed. One attempt, no blocked status, no escalation trigger fired.

### Interaction with the closing-sequence check

The pre-existing check in `lint()` was:

```python
closing_found = [t for t in types_in_order if t in CLOSING_SEQUENCE]
if closing_found != CLOSING_SEQUENCE:
    errs.append(...)
```

`close` was not in `CLOSING_SEQUENCE`, so a feature ending with a `close` WU
would have produced `closing_found == []` and a lint error. The fix introduces
`_CLOSING_TYPES` (`CLOSING_SEQUENCE | {"close"}`) for the collection pass, then
a conditional on `closing_found == ["close"]` before the existing equality check.
Multi-gate features with `close` fall through to the `elif` branch, which produces
an error listing both valid alternatives. The `CLOSING_SEQUENCE` regression path
is unchanged.

The key invariant preserved: **every gate must have a closing block.** The new
branch adds a second valid closing form, it does not weaken the "some closing must
be present" requirement.

### What was missing or ambiguous in the rule / template

**CORRELATION_ID_RE was not called out.** The WU acceptance criteria listed
`lint_plan.py` changes but did not explicitly require the `CLOSE` segment in the
ID regex. The agent inferred it was necessary (a `G1-CLOSE` correlation ID would
otherwise fail validation) and added it. This was correct, but the omission means
future similar additions may miss it if the agent is less attentive. The WU
template or the authoring guide should note: _when adding a new closing WU type,
also update `CORRELATION_ID_RE`_.

**`nonempty_gates_count` definition.** The gate-count check uses
`sum(1 for g in gates if g.get("work_units"))`, which counts gates that have
any WUs, not gates that have closing WUs specifically. For any realistic feature
plan this is correct — a gate with no WUs at all is an authoring error that
other lint rules would catch — but the condition is implicit. No ambiguity
caused a problem here; noted for clarity.

**`close` WU's own verification obligation is asymmetric.** A `close` WU runs
the `plannext` gate set (lint only), not the `doc` gate. The `doc` gate
(`artifact-changed`) checks that the feature directory changed. A `close` WU
definitely changes the directory (it must write RETROSPECTIVE.md, update
LEARNINGS.md, etc.), so it would pass the `doc` gate if it ran. However, the
design choice to reuse `plannext` means the driver never checks whether the
expected artifacts (RETROSPECTIVE.md, LEARNINGS.md entries) actually appeared —
it only checks structural validity. This is a deliberate trade-off (the WU spec
says "prefer reusing the `plannext` set") but worth noting: a `close` WU that
wrote nothing but kept lint passing would pass verification. The obligation rests
on the agent's honesty, not on the gate.

### Lessons for the template / authoring guide

1. Add `CORRELATION_ID_RE` to the checklist when a new closing WU type is
   introduced in `lint_plan.py`.
2. Consider whether the `close` gate set should eventually be its own entry in
   `verification.yml` that combines `artifact-changed` (doc) and `plan-lint`
   (plannext), so both the structural and artifact obligations are mechanically
   verified.
3. The three-test structure (accept single-gate, reject multi-gate, regression
   on four-WU) is a good template for any future linter-guard change.
