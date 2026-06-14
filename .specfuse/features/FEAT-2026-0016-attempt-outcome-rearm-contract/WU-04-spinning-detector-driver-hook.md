---
id: FEAT-2026-0016/T04
type: implementation
effort: high
status: draft
attempts: 0
planned_cost_usd: 2.00
generated_surfaces: []
produces_driver_helper:
  - detect_spinning_signature_repeat
---

# Spinning-detector active driver hook on repeated `failure_signature`

**Objective.** Halt a WU to `blocked_human` BEFORE attempt N+1
dispatches when attempt N's `attempt_outcome` event carries the same
`(failure_class, failure_signature)` pair as attempt N-1's. Emits a
`human_escalation` event with reason `spinning_signature_repeat`
carrying the repeated signature. Eliminates this session's
operator-monitor-plus-manual-TaskStop intervention pattern.

**Context.** This is `FEAT-2026-0016/T04`. Consumer #1 of the
attempt_outcome data layer landed in gate 1 (T01). Per-attempt
signal now exists in `events.jsonl`; T04 turns the operator's
manual "I see attempt 2 failed with the same `### tests: FAIL` as
attempt 1, stop the run" pattern into an automatic driver halt.

Today's spinning-shape detection (loop.py line ~2624 `for-else`)
fires only after `MAX_ATTEMPTS` (3) exhaust. T04 narrows the
shape: when the SAME failure recurs, three attempts buy nothing —
halt at the repeat.

Reference binding rules:
`.specfuse/rules/result-contract.md`, `.specfuse/rules/never-touch.md`.
Driver owns all git; edit files only.

**§10 helper-duplication pre-flight.** Before authoring:

```bash
# Existing spinning / repeat-detection symbols (must not collide)
grep -nE 'spinning|signature_repeat|prior_signature|prev_failure' .specfuse/scripts/loop.py

# Existing failed-branch emission site (the insertion point)
grep -nE 'emit_attempt_outcome\([^)]*"failed"' .specfuse/scripts/loop.py

# Existing human_escalation reasons (taxonomy)
grep -oE '"reason": "[a-z_]+"' .specfuse/scripts/loop.py | sort -u

# Existing per-WU attempt loop (the surrounding scope)
grep -nE 'for attempt in range\(1, MAX_ATTEMPTS' .specfuse/scripts/loop.py

# Confirm T01's parse_gate_failure_signature shape (signature comparability)
grep -nE '^def parse_gate_failure_signature' .specfuse/scripts/loop.py
```

If a reserved-but-unimplemented `spinning_signature_repeat` reason
or `prior_signature` field already exists, name and reconcile —
don't quietly duplicate.

**Acceptance criteria.**

1. **New helper — repeat detection.** Add
   `detect_spinning_signature_repeat(current: tuple[str | None,
   str | None], prior: tuple[str | None, str | None] | None) ->
   bool` to `loop.py`. Returns `True` iff `prior is not None` AND
   both elements of `current` are non-null AND `current == prior`.
   Returns `False` when `prior is None` (first failed attempt has
   nothing to compare against). Returns `False` when either
   element of `current` is `None` (a `failure_class is None` or
   `failure_signature is None` cannot be matched). Pure function;
   no side effects.

2. **Wire the detector into the `outcome == "failed"` branch.** In
   the per-WU attempt loop in `run()` (around loop.py line ~2602
   today), augment the `outcome == "failed"` branch:
   - BEFORE the existing `attempt_notes.append((attempt, payload))`
     and the `reset_preserving_events` call, compute
     `(_fc, _fs)` (the parser is already called there) and
     check `detect_spinning_signature_repeat((_fc, _fs),
     prior_failure_signature)`.
   - Maintain `prior_failure_signature: tuple[str | None, str | None] | None`
     as a local in the per-WU scope, initialized to `None` at the
     top of the WU's attempt loop, set to `(_fc, _fs)` at the end
     of the `outcome == "failed"` branch (after any halt check).
   - If the detector returns `True`, perform the SAME halt sequence
     the agent-reported-blocked branch (line ~2424 today) performs:
     reset tree, set WU status to `blocked_human`, write cost,
     emit the `attempt_outcome` event already being emitted (DO
     NOT skip — the event captures attempt N's spend), emit a
     `human_escalation` event with payload:
     ```python
     {
         "reason": "spinning_signature_repeat",
         "failure_class": _fc,
         "failure_signature": _fs,
         "attempts": attempt,
         "attempts_usage": attempts_usage,
     }
     ```
     flush events, `commit_bookkeeping`, set `blocked = True`,
     `break` out of the attempt loop.

3. **Orthogonality with zero-token spin shape.** The existing
   `for-else` zero-token detection (line ~2624) distinguishes
   `all_attempts_zero_token` from `spinning_detected` by checking
   `all(o == "zero_token" for o in attempt_outcomes)`. T04 must
   NOT collide:
   - The zero-token outcome branch does NOT call
     `parse_gate_failure_signature` (its event carries no
     `failure_class` / `failure_signature` — they're absent or
     None in `emit_attempt_outcome(... "zero_token_skip", ...)`).
   - The repeat detector defends by returning `False` when either
     `failure_class` or `failure_signature` is `None` (AC1).
   - A run of `[zero_token, zero_token, failed]` therefore CANNOT
     trip the repeat-halt (first two updates would not advance
     `prior_failure_signature`). A run of `[failed(sig=A),
     failed(sig=A)]` trips at attempt 2.
   - A run of `[failed(sig=A), zero_token, failed(sig=A)]`: after
     attempt 1, `prior_failure_signature = (cls, A)`. Attempt 2
     is zero_token — does NOT update prior. Attempt 3 fires with
     `(cls, A)` and trips. This is correct behavior:
     intervening zero_tokens don't reset the repeat clock.

4. **Reason string locked.** The `human_escalation.payload.reason`
   value is the literal string `spinning_signature_repeat`.
   Documented in this WU; downstream consumers (`/gate-status`,
   future predicate-v2, dashboards) filter on the exact string.

5. **The repeat-halt fires on attempt 2 at the earliest.** A single
   `failed` attempt is NOT a repeat — `prior_failure_signature is
   None` after the first failed attempt is processed; the second
   failed attempt with the same signature is the trigger. This
   keeps the `MAX_ATTEMPTS=3` budget intact for non-repeating
   failures (a `[failed(A), failed(B), failed(A)]` shape runs the
   full 3 and falls through to the existing for-else
   `spinning_detected` path).

6. **Compatibility with `re_arm` cycles.** When a WU is re-armed,
   the attempt counter resets (per `/unblock-wu`); the
   `prior_failure_signature` local is in the per-WU dispatch
   scope and reinitializes per dispatch. Re-arming after a
   `spinning_signature_repeat` halt produces a fresh attempt-loop
   that compares against nothing on attempt 1 (correct — the
   re-arm reason may have fixed the underlying cause).

7. **Symbol-existence checks** before declaring complete:

   ```bash
   # a. Helper present
   test "$(grep -cE '^def detect_spinning_signature_repeat\b' .specfuse/scripts/loop.py)" = "1"

   # b. Helper importable
   (cd .specfuse/scripts && python3 -c "from loop import detect_spinning_signature_repeat")

   # c. Hook wired at the failed-branch insertion point
   grep -qE 'detect_spinning_signature_repeat\(' .specfuse/scripts/loop.py

   # d. Reason string present at exactly the spinning-halt site
   grep -qE '"reason": "spinning_signature_repeat"' .specfuse/scripts/loop.py

   # e. Working-tree diff touches loop.py (combined diff+untracked per
   #    LEARNINGS [driver/files_changed-guard]).
   { git diff --name-only HEAD; git ls-files --others --exclude-standard; } | grep -qx '.specfuse/scripts/loop.py'

   # f. No collision with prior partial implementation
   test "$(grep -cE '^def detect_spinning_signature_repeat\b' .specfuse/scripts/loop.py)" = "1"
   ```

   Any check failing → `status: blocked` naming the failure. Do
   NOT flip frontmatter as substitute.

**Do not touch.** Files this WU may edit:
- `.specfuse/scripts/loop.py` (additions + one hook in the
  per-WU attempt loop's `outcome == "failed"` branch only)

No edits to: T01's `emit_attempt_outcome` /
`parse_gate_failure_signature` / `extract_failure_excerpt`
surfaces (re-use as-is), T02's cumulative-fold helpers, the
zero-token spin shape detection in the for-else, `validate-event.py`,
`gate_eval.py`, `lint_plan.py`, skills, tests for other features,
other features, secrets, `.git/`. Driver owns all git; edit files
only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in
`.specfuse/verification.yml` (tests, lint, security, coverage) +
AC7 symbol-existence + import checks. Add at least two unit tests
to `tests/test_attempt_outcome_emission.py`:
- `test_detect_spinning_signature_repeat_true_on_match` — pass
  `current=("tests", "test_foo")`, `prior=("tests", "test_foo")`,
  expect `True`.
- `test_detect_spinning_signature_repeat_false_on_none_prior` —
  pass `current=("tests", "test_foo")`, `prior=None`, expect
  `False`.
- `test_detect_spinning_signature_repeat_false_on_null_element` —
  pass `current=(None, "test_foo")` or `current=("tests", None)`,
  expect `False` (defends orthogonality with zero-token spin).

**Escalation triggers.**

1. **Completeness.** AC7 (a) returns anything other than `1` or
   AC7 (b) `ImportError` → `status: blocked`. Helper missing.
   Per `[FEAT-2026-0007/G1-LESSONS]` — frontmatter-flip-only is
   the documented hollow-pass shape; refuse it explicitly.
2. **Failure-signature comparability gap.** If the §10 pre-flight
   surfaces a case where `parse_gate_failure_signature` returns
   `(failure_class, failure_signature)` for two unrelated failures
   that compare equal (e.g. both `("other", "no_gate_marker")`
   from different root-cause failures — see events.jsonl line 11:
   `### plan-lint: FAIL` mismatched the `\w+` regex), the spinning
   detector will trip falsely. Name the gap in RESULT and emit
   `status: blocked` — operator decides whether to extend T01's
   parser (separate WU) or accept the conservative behavior
   (false-positive halts as a cost cheaper than three-attempt
   waste).
3. **Hook placement ambiguity.** If wiring the detector inside the
   `outcome == "failed"` branch requires reordering existing
   `emit_attempt_outcome` / `flush_events` /
   `reset_preserving_events` calls in a way that risks losing the
   event on the halt path (the event MUST flush before the
   `commit_bookkeeping` returns; otherwise the attempt's data is
   lost), name the ordering concern and emit `status: blocked`.
4. **Backward compatibility with legacy events.** Existing
   events.jsonl entries from features that ran on pre-T01 driver
   have no `failure_signature` on per-attempt records. The
   per-WU `prior_failure_signature` local is per-dispatch (not
   read from history) so legacy data does not affect the hook.
   If implementation reads history instead, emit `status: blocked`
   — that's a different design.
