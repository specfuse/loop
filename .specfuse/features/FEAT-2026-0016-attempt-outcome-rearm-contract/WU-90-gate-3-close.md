---
id: FEAT-2026-0016/G3-CLOSE
type: close
effort: high
status: done
attempts: 1
planned_cost_usd: 1.50
generated_surfaces: []
verdict: met_locally
duration_seconds: 419.02
cost_usd: 3.586944
input_tokens: 54
output_tokens: 24355
---

# Gate 3 close — terminal: retro + lessons + docs + feature-arc verdict

**Objective.** Terminal close for `FEAT-2026-0016`. Append a
`## Gate 3` section to `RETROSPECTIVE.md` covering T07–T09, extend
the existing `## Cost analysis` table with gate-3 rows (and the
new `### Failure-class breakdown` subsection T07 introduces),
append durable lesson(s) to `.specfuse/LEARNINGS.md`, reconcile
docs/roadmap state with what T09 shipped, and write the terminal
`# Feature-arc verdict` answering "did the attempt_outcome data
layer + re-arm contract + first three consumers land as
designed". Sets `verdict: met` (or `met_locally` /
`partially_met` / `not_met`) on this WU's frontmatter so
`fire_terminal_flips` fires.

**Context.** This is `FEAT-2026-0016/G3-CLOSE`. Terminal gate
close (FEAT-2026-0015 contract; single-WU). Gate 3 shipped: T07
(`### Failure-class breakdown` subsection + driver guard), T08
(`/learnings-suggest` skill — read-only signature clusterer), T09
(methodology.md per-attempt event contract + roadmap-archive of
the merged-in original 0016 scope).

This is the **first close-ceremony that consumes its own data
layer**. T07's guard runs on THIS close WU; T07's helper renders
the breakdown subsection THIS retrospective must contain. The
recursive-dogfood property documented in PLAN.md "Notes" is now
binary-evaluable: gate 3's own retrospective should carry the
breakdown if any non-passing attempt-outcome event landed in
gate-3's scope, and the guard either pass or trip on this very
WU's dispatch. The historical record of which path fires is the
single most load-bearing artifact this close produces.

Reference: `.specfuse/rules/result-contract.md` for the RESULT
block contract. `.specfuse/skills/verification/SKILL.md` for how
to run gates. `.specfuse/templates/WU.template.md` notes on
`close`. `[FEAT-2026-0015/T07]`'s closing-deliverable guards
(`assert_retrospective_exists`,
`assert_retrospective_gate_section`,
`assert_learnings_appended_or_noop`, `assert_doc_or_roadmap_diff`,
`assert_cost_analysis_section`,
`assert_cost_analysis_section_when_met`,
`assert_terminal_flips_fired`) all run on this WU; T07's new
`assert_failure_class_breakdown_when_failures_present` joins
them.

**Acceptance criteria.**

1. **`RETROSPECTIVE.md` extended** with a `## Gate 3` section
   appended to the existing file. Per-WU sub-sections for T07,
   T08, T09: attempts, blockers if any, surprises. The shape
   mirrors the existing `## Gate 1` / `## Gate 2` sections in
   the same file.

2. **`## Cost analysis` section extended with gate-3 rows.** For
   each WU in scope (T07, T08, T09), quote `planned_cost_usd`,
   compute actual from frontmatter `cost_usd`, report delta %.
   Aggregate to gate-3 substantive sub-total, then to feature
   total (across gates 1 + 2 + 3). Reference predicate v1
   criterion 3 (≤ 1.5×) and criterion 4 (≤ 2×) per-WU; variance
   > 50% on any WU requires a one-paragraph rationale citing the
   cause.

3. **`### Failure-class breakdown` subsection present when
   failures occurred.** Per T07's contract, when ANY
   `attempt_outcome` event with `outcome != "passed"` exists in
   gate-3's correlation_id scope, RETROSPECTIVE.md MUST contain
   a `### Failure-class breakdown` subsection under `## Cost
   analysis`. The breakdown is the output of T07's
   `summarize_attempt_failure_classes(feature_dir, gate_n=3)`
   helper, rendered verbatim. If gate-3 had NO non-passing
   attempts, the subsection is omitted; T07's guard correctly
   passes in that case.

4. **Predicate self-check captured.** Run:

   ```bash
   python3 .specfuse/scripts/gate_eval.py backtest FEAT-2026-0016 --gate 3
   ```

   Paste output verbatim into the gate-3 retrospective section.
   Document whether gate 3 auto-closed (if this WU is running,
   it did NOT — auto-close skips the close-WU dispatch). The
   `auto=` verdict + reasons list is the recursive-dogfood
   evidence — gate-3 evaluates the predicate on a feature whose
   data layer the predicate consumes for the first time at
   full payload fidelity (T01 bootstrap-gap notwithstanding;
   gate-1 already documents the gap).

5. **`.specfuse/LEARNINGS.md` appended** with ≥ 1 durable lesson
   from this feature's terminal close (or an explicit
   `[FEAT-2026-0016/G3-CLOSE] nothing generalizes — feature ran
   on-plan` note). Lessons must be phrased as rules that would
   change how a future WU is written or executed. Strong
   candidates:
   - Data-layer-first-then-consumers feature shape: T01–T03
     (data) shipped clean in gate 1; T04–T06 (consumers) then
     T07–T09 (close-ceremony/skills/docs) shipped clean in
     gates 2/3 — quantify whether the upfront contract
     investment paid off vs. mixing data + consumers in one
     gate.
   - Bootstrap-gap pattern recurrence: T01's own events lacked
     the new payload it shipped (driver dispatching T01 ran old
     code). Confirms `[FEAT-2026-0006/G1-CLOSE]` pattern — worth
     promoting if not already in LEARNINGS.
   - Failure-class taxonomy stability across the feature's own
     gate-2 + gate-3 attempts: if the taxonomy held at v1
     without extensions, that's worth recording so future
     features know not to extend it lightly.

6. **Roadmap row reconciliation.** `.specfuse/roadmap.md`
   FEAT-2026-0016 row's Detail cell was updated by T09 to
   point at `roadmap-archive.md#feat-2026-0016`. The Status
   cell is auto-flipped to `done` by `fire_terminal_flips` IF
   `verdict: met` (or `met_locally`) sets on this WU's
   frontmatter. Manual edit of the Status cell is NOT
   required — confirm the driver fires it post-pass.

7. **Docs/roadmap diff guard satisfied.**
   `assert_doc_or_roadmap_diff` (FEAT-2026-0015/T07) requires
   the close-WU's commit (or the cumulative gate-3 diff range)
   to touch either `docs/` or `roadmap.md`. T09 already touched
   `docs/methodology.md` + `.specfuse/roadmap.md` +
   `.specfuse/roadmap-archive.md`; this close WU's commit
   touches RETROSPECTIVE.md + LEARNINGS.md + this WU's own
   frontmatter (verdict). Confirm the guard's scope before
   declaring complete — if it requires THIS WU's commit
   specifically to touch docs/roadmap, add a minimal
   methodology.md edit (cross-link from the new §3 subsection
   to this feature's RETROSPECTIVE.md for the first recursive
   dogfood data point) to satisfy it.

8. **`# Feature-arc verdict` section written** in
   RETROSPECTIVE.md with the verdict (met / met_locally /
   partially_met / not_met) + one-sentence rationale anchored to
   PLAN.md's `roadmap_goal`. Verdict semantics for this
   feature:
   - **met** — `attempt_outcome` emission landed across all
     dispatch outcomes; re-arm WU-frontmatter contract +
     driver fold landed; first three consumers (T04
     spinning-detector, T05 `/gate-status` per-attempt, T06
     `/unblock-wu` rationale) ship; close-ceremony
     `### Failure-class breakdown` (T07) + `/learnings-suggest`
     skill (T08) + docs (T09) ship; predicate v1 reads
     `events.jsonl` directly via no consumer touching driver
     stdout.
   - **met_locally** — same as `met` but with a known
     scope-deferred item explicitly documented (e.g.
     predicate v2 deferred per PLAN.md "Scope OUT").
   - **partially_met** — data layer shipped but one or more
     consumers (T04 / T05 / T06 / T07 / T08) did NOT, OR shipped
     but is degraded.
   - **not_met** — `attempt_outcome` emission has gaps the
     consumers cannot work around.

9. **`verdict:` set in this WU's frontmatter** (driver-required
   for `fire_terminal_flips`). Per FEAT-2026-0015/G2-CLOSE
   LEARNINGS, write `verdict: met` (or other) to THIS file's
   frontmatter directly — `fire_terminal_flips` reads it
   post-squash.

10. **Existence check** before declaring complete:

    ```bash
    FD=.specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract

    # a. RETROSPECTIVE.md exists with gate-3 section
    test -s $FD/RETROSPECTIVE.md
    grep -qE '^## Gate 3\b' $FD/RETROSPECTIVE.md

    # b. Cost analysis covers gate 3
    grep -qE '^## Cost analysis' $FD/RETROSPECTIVE.md
    grep -qE '(T07|T08|T09|gate 3|Gate 3)' $FD/RETROSPECTIVE.md

    # c. Failure-class breakdown subsection iff non-passing attempts exist
    python3 - <<'PY'
    import json, pathlib, sys
    fd = pathlib.Path(".specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract")
    events = fd / "events.jsonl"
    # Find gate-3 WU IDs from PLAN.md graph
    plan = (fd / "PLAN.md").read_text()
    import re
    gate3_block = re.search(r"- gate: 3\b.*?(?=\n  - gate:|\n## |\Z)", plan, re.DOTALL).group(0)
    ids = set(re.findall(r"id: (FEAT-2026-0016/\S+)", gate3_block))
    non_passing = 0
    for line in events.read_text().splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("event_type") != "attempt_outcome":
            continue
        if e.get("correlation_id") not in ids:
            continue
        if e.get("payload", {}).get("outcome") != "passed":
            non_passing += 1
    retro = (fd / "RETROSPECTIVE.md").read_text()
    has_heading = bool(re.search(r"^### Failure-class breakdown\b", retro, re.MULTILINE))
    if non_passing > 0 and not has_heading:
        print(f"FAIL: {non_passing} non-passing gate-3 attempt(s) but no breakdown heading")
        sys.exit(1)
    print(f"ok: non_passing={non_passing} heading_present={has_heading}")
    PY

    # d. Predicate self-check output captured
    grep -q 'predicate=v1' $FD/RETROSPECTIVE.md

    # e. Feature-arc verdict section present
    grep -qE '^# Feature-arc verdict' $FD/RETROSPECTIVE.md

    # f. LEARNINGS appended OR explicit no-op note
    { git diff HEAD .specfuse/LEARNINGS.md | grep -qE '^\+- \*?\*?\[FEAT-2026-0016/G3'; } || \
      grep -q 'nothing generalizes — feature ran on-plan' $FD/RETROSPECTIVE.md

    # g. verdict written to this WU's frontmatter
    grep -qE '^verdict: (met|met_locally|partially_met|not_met)' $FD/WU-90-gate-3-close.md

    # h. Working-tree diff touches RETROSPECTIVE.md (combined diff+untracked)
    { git diff --name-only HEAD; git ls-files --others --exclude-standard; } | \
      grep -qx "$FD/RETROSPECTIVE.md"
    ```

    If any check fails, emit `status: blocked`. RETROSPECTIVE-only
    frontmatter flips reproduce the documented hollow-pass shape.

**Do not touch.** Files this WU may edit:
- `RETROSPECTIVE.md` (append `## Gate 3` + verdict section;
  extend `## Cost analysis` table + the
  `### Failure-class breakdown` subsection when applicable)
- `.specfuse/LEARNINGS.md` (append-only)
- This WU's own frontmatter (`verdict: ...` field only — required
  for `fire_terminal_flips`)
- `docs/methodology.md` minimal edit (one paragraph or
  cross-link only) iff AC7's `assert_doc_or_roadmap_diff` scope
  requires THIS WU's commit to touch docs/roadmap.

No edits to: `loop.py`, `gate_eval.py`, `lint_plan.py`,
T07/T08/T09 surfaces (already shipped — `### Failure-class
breakdown` is RENDERED here, not re-implemented; `/learnings-suggest`
SKILL.md is final; methodology.md additions from T09 stand
unchanged unless AC7 forces a one-line cross-link),
`.specfuse/roadmap.md` (driver flips Status cell on
fire_terminal_flips), PLAN.md, GATE-NN.md status
(driver-flipped), other features, secrets, `.git/`. Driver owns
all git. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set in
`.specfuse/verification.yml` (close type → plannext). Plus AC10
existence checks. Plus `[FEAT-2026-0015/T07]` closing-deliverable
guards (`assert_retrospective_exists`,
`assert_retrospective_gate_section`,
`assert_learnings_appended_or_noop`, `assert_doc_or_roadmap_diff`,
`assert_cost_analysis_section`,
`assert_cost_analysis_section_when_met`,
`assert_terminal_flips_fired`). Plus T07's new
`assert_failure_class_breakdown_when_failures_present` — the
first guard execution against THIS feature's own retrospective is
the recursive-dogfood smoke test for T07.

**Escalation triggers.**

1. **Cost-analysis ambiguity.** If a WU's `cost_usd` /
   `planned_cost_usd` field disagrees with events.jsonl summed
   over its attempts (data drift between frontmatter and the
   per-attempt log), emit `status: blocked` naming the
   discrepancy.
2. **No-op vs nothing-generalizes ambiguity.** If gate 3 ran
   genuinely on-plan with no surprises, prefer the explicit
   "nothing generalizes" note over an invented lesson. Do not
   pad LEARNINGS with rules that don't trace to a real failure
   mode.
3. **Verdict ambiguity.** If a deliverable shipped but is
   degraded (T07's guard wired but skipped on one close shape,
   T08's skill ships but the `--min-wus` flag isn't documented),
   use `met_locally` or `partially_met` not `met`. Per
   FEAT-2026-0015/G2-CLOSE LEARNINGS, a hedged verdict on a
   terminal close prevents silent shipping of a half-feature.
4. **Compound retrospective scope.** Do NOT re-evaluate gate-1
   or gate-2 outcomes — those sections are sealed by their own
   close WUs. Gate 3 retrospective covers gate 3 only + the
   terminal feature-arc verdict.
5. **Recursive-dogfood guard misfire.** If T07's guard
   (`assert_failure_class_breakdown_when_failures_present`)
   reports a failure that is incorrect (e.g. the heading IS
   present but the regex misses it), the methodology-honest
   response is `status: blocked` naming the guard bug, not
   `status: complete` with the heading rewritten to placate
   the regex. The guard is the contract; if it's wrong, that's
   a T07 spec issue surfacing post-ship.
6. **T07-helper unavailability.** If T07's
   `summarize_attempt_failure_classes` helper is absent or
   raises when called for gate-3 scope, do NOT hand-author the
   breakdown table from events.jsonl — emit `status: blocked`.
   The helper is the contract; rendering by hand fakes the
   recursive-dogfood evidence.
