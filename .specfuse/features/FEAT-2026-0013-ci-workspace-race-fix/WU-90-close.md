---
id: FEAT-2026-0013/G1-CLOSE
type: close
model: claude-opus-4-7
effort: high
status: pending
attempts: 0
# Cost preserved from v1 (2026-06-12, closed methodologically with macOS-local
# 50× audit; CI on Linux subsequently failed → re-armed).
historical_cost_usd: 1.886625
historical_duration_seconds: 582.178
historical_input_tokens: 32
historical_output_tokens: 12204
---

# Gate 1 close — combined closing ceremony

**Objective.** Close this single-gate feature in one session: write
the retrospective, promote durable lessons, reconcile docs and
roadmap, write the terminal feature-arc verdict — the union of the
four classic closing ceremonies (`close` type, valid here because the
feature has exactly one gate).

**Context.** This is `FEAT-2026-0013/G1-CLOSE`. Read this feature's
`events.jsonl` (the gate slice), the gate's commits, the root
`.specfuse/LEARNINGS.md`, and PLAN.md's `roadmap_goal`. Single-gate,
so no next gate to forward-design. Reference the binding rules under
`.specfuse/rules/`; honor `result-contract.md`, `never-touch.md`.
The driver owns all git.

The whole point of this feature was to eliminate the
integration_workspace fd-leak race. The close ceremony has a special
oracle responsibility: **re-run the 50× audit ONE MORE TIME from the
close session** to confirm the fix held after T01's squash committed
to HEAD. A single failure here invalidates the feature-arc verdict.

**Acceptance criteria.**
1. `RETROSPECTIVE.md` exists in this feature folder: T01's outcome,
   what worked, what failed and why, attempt count, and any
   rule/template/boundary missing or ambiguous. Cite specific
   `events.jsonl` evidence per WU.
2. **Local recursive audit (weak oracle).** The retrospective
   includes a section `## 50× recursive audit (macOS local)` that
   runs and reports the FULL output of:
   `for i in $(seq 1 50); do .venv/bin/python3 -m unittest tests.test_driver_integration -q 2>&1 | tail -1; done | sort | uniq -c`
   Expected: exactly one line of the form `  50 OK`. **v1 LESSON
   (durable):** this audit alone is INSUFFICIENT — v1 passed it
   50/50 and still failed on Linux CI. The verdict MUST explicitly
   state local audit is necessary-but-not-sufficient and that the
   FINAL oracle is the operator-side Linux Docker probe
   (`scripts/check-linux-race.sh`) run pre-push at `/wrap-feature`
   step 4 (or 5) PLUS the CI run on the pushed branch.
3. **v1 cost reconciliation.** The retrospective includes a section
   `## v1 cost reconciliation` quoting the `historical_cost_usd` /
   `historical_duration_seconds` fields from both WUs' frontmatter
   and stating the v2 cumulative total = v1 cost + this run's cost.
   This is the audit signal that prior failed attempts were
   preserved, not silently overwritten.
4. Durable, generalizable lessons appended to the root
   `.specfuse/LEARNINGS.md`, tagged `FEAT-2026-0013/G1-CLOSE`.
   Feature-specific noise stays in `RETROSPECTIVE.md`. **Required
   lessons from v1**: (a) "test fixtures using subprocess +
   TemporaryDirectory on Py 3.12 must disable git background gc +
   add a sync barrier before teardown — AND set
   `ignore_cleanup_errors=True` as belt-and-suspenders for
   Linux-only surfaces"; (b) "oracle environment must match goal
   environment — a 50× macOS-local audit is NOT evidence about
   Linux CI behavior; use `scripts/check-linux-race.sh` Docker
   probe for Linux-targeted verifications"; (c) "script-parity ≠
   environment-parity — pre-push hooks running once on developer
   machines cannot catch races that are deterministic-on-CI". If
   these are already there from v1, skip; otherwise append.
5. Docs and roadmap reconciled: this feature's row in
   `.specfuse/roadmap.md` reflects `status: done` (assuming AC2
   AC3 passed). The detail section's `**Status: planned.**` line
   in the roadmap detail block — if present — is updated to
   `**Status: done.**`. The `PLAN.md status:` field flips to
   `done` in this WU — the close ceremony owns this flip, not a
   follow-on commit.
6. A `# Feature-arc verdict` section is appended to
   `RETROSPECTIVE.md` stating whether `roadmap_goal` is met. The
   verdict MUST: (a) cite AC 2's macOS-local audit output verbatim,
   (b) explicitly state that local audit alone is NECESSARY but
   NOT SUFFICIENT (per v1 LESSON), (c) name the operator-side
   Linux Docker probe + CI run as the FINAL oracle that the
   operator is responsible for invoking at `/wrap-feature`, (d)
   if even one of the 50 local runs failed, the verdict must
   explicitly say the goal is NOT met and recommend the recovery
   action (re-arm WU-01, file FEAT-2026-0015, etc.).

**Do not touch.** Source code (`tests/`, `loop.py`, etc.) — this is
a closing unit, it does not change behavior. Other WU files,
generated directories, secrets, `.git/`. You write `RETROSPECTIVE.md`,
append to `LEARNINGS.md`, update `roadmap.md`, flip `PLAN.md` status —
nothing else.

**Verification.** The `plannext` gate set in
`.specfuse/verification.yml` (`lint_plan.py` on this feature —
structural validity preserved). Plus the `doc` gates (file exists /
something changed).

**Escalation triggers.**
1. **50× audit reveals a failure.** If AC 2's audit shows even one
   `FAILED` or `ERROR` line, do NOT write the verdict as "goal met".
   Write the retrospective honestly, append no LEARNINGS (the lesson
   isn't durable until the fix actually works), and emit
   `status: blocked` with a `blocked_reason` naming the failed test.
   Recovery requires a follow-on WU or new feature.
2. **Conflicting roadmap state.** If `roadmap.md` already shows this
   feature as `done` (e.g. another close path raced this one), do
   not overwrite — read the existing state, reconcile in the verdict,
   and stop.
