---
id: FEAT-2026-0016/T01
type: implementation
effort: xhigh
status: draft
attempts: 0
planned_cost_usd: 2.50
generated_surfaces: []
produces_driver_helper:
  - emit_attempt_outcome
  - parse_gate_failure_signature
  - extract_failure_excerpt
---

# Complete + standardize `attempt_outcome` event emission across all dispatch outcomes

**Objective.** Ensure every dispatched attempt emits exactly one
`attempt_outcome` event with a uniform payload shape (per PLAN.md
§ "Event payload shape — `attempt_outcome` v1"). Today only some
failure paths emit events; add the missing ones (passed, generic
gate failures, agent-emitted blocked) and standardize the payload
across existing sites.

**Context.** This is `FEAT-2026-0016/T01`. Data-layer foundation
for the per-attempt audit surface — the evidence source for
predicate v2 (future feature), spinning-detector hook (T04, gate 2),
`/gate-status` per-attempt surfacing (T05), close-ceremony failure-
class breakdown (T07).

Reconnaissance done at draft time (verify at execution):
- Existing `attempt_outcome` emissions in `loop.py` (grep
  `'"attempt_outcome"'`):
  - `outcome: zero_token_skip` — emitted (~line 2055)
  - `outcome: smoke_import_failed` — emitted (closing-deliverable
    path)
  - `outcome: closing_deliverable_missing` — emitted
  - `outcome: files_changed_mismatch` — emitted
- Missing emissions:
  - `outcome: passed` — never emitted (PASS branch flush_events
    only writes `task_completed`)
  - `outcome: failed` — never emitted on generic gate failure
    (test/lint/security/coverage); driver buffers `attempt_notes`
    and resets, no event
  - `outcome: blocked` — agent-emitted blocked produces only
    `human_escalation` event, no `attempt_outcome`
  - `outcome: post_pass_invariant_failed` — emitted as
    `attempt_outcome` per FEAT-2026-0017 already; verify payload
    shape matches v1

Reference binding rules:
`.specfuse/rules/result-contract.md`, `.specfuse/rules/never-touch.md`.
The driver owns all git; edit files only.

**§10 helper-duplication pre-flight.** Before authoring:

```bash
# All existing attempt_outcome emission sites
grep -nE '"attempt_outcome"' .specfuse/scripts/loop.py

# Build_event + flush_events helpers (must reuse, do NOT re-implement)
grep -nE '^def (build_event|flush_events)\b' .specfuse/scripts/loop.py

# Existing failure-class extraction (none today; verify nothing collides)
grep -nE 'failure_class|failure_signature|failure_excerpt' .specfuse/scripts/loop.py
```

Every existing `attempt_outcome` emission site MUST be updated to
the standardized payload — do not leave the current shape in place
alongside the new shape (would double the consumer's branching).

**Acceptance criteria.**

1. **New helper — payload constructor.** Add
   `emit_attempt_outcome(wu, attempt: int, outcome: str, usage:
   dict, *, failure_class: str | None = None, failure_signature: str
   | None = None, failure_excerpt: str | None = None,
   files_touched: list[str] | None = None, agent_status: str | None
   = None, agent_blocked_reason: str | None = None) -> dict` to
   `loop.py`. Returns a `build_event("attempt_outcome", wu.wu_id, {...})`
   dict ready to append to `wu_events`. The function:
   - Reads `wu.model`, `wu.effort`, `wu.re_arm_count` (defaults to
     0 if T02 hasn't landed in the same squash — see Escalation #5
     for the bootstrap ordering).
   - Folds `usage` (`duration_seconds`, `cost_usd`, `input_tokens`,
     `output_tokens`, `cache_read_input_tokens`,
     `cache_creation_input_tokens`) into the payload.
   - Defaults `files_touched: []` when None.
   - Returns the event dict; CALLER appends it to `wu_events` and
     `flush_events` runs at the existing flush point. The helper
     does NOT call `flush_events` itself — keeps the
     "one flush per outcome-cycle" invariant intact.

2. **New helper — failure-class derivation from gate stdout.** Add
   `parse_gate_failure_signature(stdout: str) -> tuple[str, str]`
   returning `(failure_class, failure_signature)`. Algorithm:
   - Scan stdout for lines matching the driver's gate-output marker:
     `^### (\w+): FAIL`. The captured group is the gate name.
   - Map gate name → `failure_class`:
     - `tests` → `tests`
     - `lint` → `lint`
     - `security` → `security`
     - `coverage` → `coverage`
     - any other matched gate name → `other`
   - If no `### X: FAIL` marker found: `failure_class = other`,
     `failure_signature = "no_gate_marker"`.
   - For `failure_signature`, scan the lines AFTER the marker (up
     to 50 lines) for the first stable identifier:
     - `tests` → first failing test name (regex
       `^FAIL: (test_\S+)`)
     - `lint` → first ruff rule code (regex `\b([A-Z]\d{3,4})\b`)
     - `security` → first bandit issue id (regex
       `Issue: \[(B\d+)`)
     - `coverage` → first uncovered file (regex
       `^([^\s]+\.py)\s+\d+\s+\d+`)
     - Fallback: first non-empty line, truncated to 100 chars.
   - Both returned values are non-empty strings (use sentinel
     `"unknown"` rather than empty string).

3. **New helper — excerpt extraction.** Add
   `extract_failure_excerpt(stdout: str, max_chars: int = 500) ->
   str`. Returns the last `max_chars` of the stdout's lines that
   contain `FAIL`, `Error`, `Exception`, or `Traceback`. If no such
   lines, returns the last `max_chars` of stdout. Trims to UTF-8
   safe boundary.

4. **Wire `emit_attempt_outcome` into ALL existing emission sites.**
   Each of the four current sites
   (`zero_token_skip`, `smoke_import_failed`,
   `closing_deliverable_missing`, `files_changed_mismatch`) must be
   migrated to use the new helper. The current `build_event(
   "attempt_outcome", ..., {...})` calls are REPLACED with
   `wu_events.append(emit_attempt_outcome(wu, attempt, "...",
   usage_dict, failure_class=..., failure_signature=...,
   failure_excerpt=...))`. Each migration preserves the existing
   site's contextual fields (e.g.
   `closing_deliverable_missing` keeps its `assertion`
   field — add to payload via a new optional kwarg or extras dict;
   spec leaves the exact mechanism to the implementor, but the
   field MUST survive the migration).

5. **Add `attempt_outcome` emission on PASS.** In the post-squash
   branch (between `commit_bookkeeping(squash)` and
   `done_ids.add(wu.wu_id)`), insert:

   ```python
   wu_events.append(emit_attempt_outcome(
       wu, attempt, "passed",
       attempts_usage[-1],  # the just-completed attempt's usage dict
       failure_class=None,
       failure_signature=None,
       failure_excerpt=None,
       files_touched=git_diff_names(head_before, sha),  # see AC7
       agent_status="complete",
       agent_blocked_reason=None,
   ))
   ```

   This is the LOAD-BEARING add: predicate v2 (future) reads
   `outcome == "passed"` as the positive signal; without this event,
   predicate v1's check 7 false positive persists indefinitely.

6. **Add `attempt_outcome` emission on FAIL (generic gate
   failure).** In the `outcome == "failed"` branch where the driver
   currently buffers `attempt_notes` and calls
   `reset_preserving_events`, insert BEFORE the reset:

   ```python
   fc, fs = parse_gate_failure_signature(payload)  # payload = gate stdout
   ex = extract_failure_excerpt(payload)
   wu_events.append(emit_attempt_outcome(
       wu, attempt, "failed",
       attempts_usage[-1],
       failure_class=fc,
       failure_signature=fs,
       failure_excerpt=ex,
       files_touched=git_diff_names(head_before, "HEAD"),
       agent_status="complete",
       agent_blocked_reason=None,
   ))
   flush_events(events_path, wu_events)
   ```

   Note: `flush_events` is called here (mirroring the existing
   pattern at other failure-emission sites) so the event survives
   the subsequent `git reset --hard`.

7. **Add `attempt_outcome` emission on BLOCKED.** In the
   `outcome == "blocked"` branch (where agent emitted RESULT
   `status: blocked`), insert before the existing
   `human_escalation` event emission:

   ```python
   wu_events.append(emit_attempt_outcome(
       wu, attempt, "blocked",
       attempts_usage[-1],
       failure_class=None,
       failure_signature=None,
       failure_excerpt=None,
       files_touched=git_diff_names(head_before, "HEAD"),
       agent_status="blocked",
       agent_blocked_reason=payload,  # the agent's blocked_reason string
   ))
   ```

   The two events (`attempt_outcome` + `human_escalation`) at the
   blocked path are intentional: attempt_outcome captures
   per-attempt data, human_escalation marks the escalation moment.
   Consumers branch on `event_type`.

8. **`git_diff_names` helper.** Add
   `git_diff_names(head_before: str, head_after: str) -> list[str]`
   that runs `git diff --name-only <before> <after>` and returns
   the path list (or empty list on git error). Used by AC5/AC6/AC7
   to populate `files_touched`. Handles the case where
   `head_after == "HEAD"` (working tree) by including untracked
   files via `git ls-files --others --exclude-standard` — per
   `[driver/files_changed-guard]` LEARNINGS.

9. **Bootstrap-gap documentation.** Per
   `[FEAT-2026-0006/G1-CLOSE]` LEARNINGS, this WU's own
   `attempt_outcome` events will lack the standardized payload
   fields (the driver dispatching T01 runs OLD code, pre-this-
   commit). The first WU with the full new shape is T02. Add a
   one-line comment in the helper docstring:
   `# T01's own events lack standardized payload; bootstrap gap`.

10. **Symbol-existence checks** before declaring complete:

    ```bash
    # a. All four new helpers present
    test "$(grep -cE '^def (emit_attempt_outcome|parse_gate_failure_signature|extract_failure_excerpt|git_diff_names)\b' .specfuse/scripts/loop.py)" = "4"

    # b. Helpers importable
    (cd .specfuse/scripts && python3 -c "from loop import emit_attempt_outcome, parse_gate_failure_signature, extract_failure_excerpt, git_diff_names")

    # c. PASS branch emits attempt_outcome (search for "passed" outcome string)
    grep -qE 'emit_attempt_outcome\([^)]*"passed"' .specfuse/scripts/loop.py

    # d. FAILED branch emits attempt_outcome
    grep -qE 'emit_attempt_outcome\([^)]*"failed"' .specfuse/scripts/loop.py

    # e. BLOCKED branch emits attempt_outcome
    grep -qE 'emit_attempt_outcome\([^)]*"blocked"' .specfuse/scripts/loop.py

    # f. All four existing sites migrated (no raw build_event("attempt_outcome"... calls remain)
    test "$(grep -cE 'build_event\("attempt_outcome"' .specfuse/scripts/loop.py)" = "0"

    # g. Working-tree diff actually touches loop.py
    git diff --name-only HEAD | grep -qx '.specfuse/scripts/loop.py'
    ```

    Any check failing → `status: blocked` naming the failure. Do
    NOT flip frontmatter as substitute.

**Do not touch.** Files this WU may edit:
- `.specfuse/scripts/loop.py` (additions + migration of 4 existing
  emission sites)

No edits to: T02's surfaces (WU frontmatter fields, WU template),
T03's tests (T03 owns), `validate-event.py`, `gate_eval.py`,
`lint_plan.py`, other features, secrets, `.git/`. Driver owns all
git; edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in
`.specfuse/verification.yml` (tests, lint, security, coverage).
Plus AC10 symbol-existence + import checks. T03 will add the
behavior tests; T01's verification stops at "code compiles +
existing tests still pass + new symbols exist".

**Escalation triggers.**

1. **Completeness.** AC10 (a) returns anything other than `4` →
   `status: blocked`. Helpers missing. Per
   `[FEAT-2026-0007/G1-LESSONS]` + `[FEAT-2026-0017/T01
   prior_attempts]` — frontmatter-flip-only is the documented
   hollow-pass shape; refuse it explicitly.
2. **Migration scope ambiguity.** If a fifth existing
   `attempt_outcome` emission site is discovered during the §10
   pre-flight that wasn't in this WU's spec, emit `status: blocked`
   with the site location. Do NOT silently migrate it — the spec
   needs to cover it explicitly so the standardized payload's
   contextual fields are preserved.
3. **Failure-class taxonomy collision.** If
   `parse_gate_failure_signature` encounters a gate name in
   stdout (`### <name>: FAIL`) that doesn't map to any of the
   spec'd classes (and isn't `other`-bucket-able cleanly), surface
   the name and emit `status: blocked` — operator decides whether
   to extend the taxonomy or accept `other`.
4. **`files_touched` performance.** If `git diff --name-only`
   becomes a hot-path issue (large diffs), do NOT silently
   skip the call. Emit `status: blocked` with the timing
   evidence; the cost-of-correctness tradeoff is operator's call.
5. **T02 dependency in `re_arm_count` field.** AC1's helper reads
   `wu.re_arm_count` — but T02 lands the field. If T01 dispatches
   BEFORE T02 (PLAN.md depends_on shows T01 and T02 are
   independent, so the driver may dispatch either first), the
   helper must default `re_arm_count` to 0 via `getattr(wu,
   "re_arm_count", 0)`. Confirm this defaulting works regardless
   of which WU lands first. If the dispatch order forces a
   coordination bug, emit `status: blocked` proposing a
   dependency edge from T01 to T02 (or vice versa).
