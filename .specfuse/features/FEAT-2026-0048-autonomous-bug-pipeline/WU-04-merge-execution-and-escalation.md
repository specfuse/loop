---
id: FEAT-2026-0048/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.50
oracle_env: macos_local
produces:
  - specfuse/loop/bug_lane_run.py
  - tests/test_bug_lane_run.py
produces_driver_helper: run_bug_lane, pr_ci_conclusion
model: sonnet
effort: medium
gate_set: code
driver_version: 0.10.0
started_at: 2026-08-10T05:56:04.808638+00:00
duration_seconds: 1174.629
cost_usd: 3.597465
input_tokens: 102
output_tokens: 43432
---

# Run the lane end to end: fix → PR → guarded merge, with escalation on refusal

**Objective.** Create `specfuse/loop/bug_lane_run.py` exposing
`run_bug_lane(...)`: take a lane input, invoke headless `/fix-bug`, and — only
if the dial is `on` and every guardrail passes — merge the resulting PR;
otherwise label it with the declining reason and leave it open. Escalate
refusals and failures via the FEAT-2026-0046 contract.

**Context.** Correlation ID `FEAT-2026-0048/T04`. Depends on
`FEAT-2026-0048/T03`. Last WU of a strictly serial gate, and **the only unit in
this feature that performs an irreversible outward action.** Every guardrail it
consults exists before it runs; that ordering is the point of the serial graph.

**Call the shipped mechanisms; fork nothing.**

- headless `/fix-bug` invocation: `monitor/autofix_invoke.build_invocation`,
  outcome classification: `classify_outcome`, valid outcomes: `OUTCOMES`
  (`refused`, `could_not_proceed`, `completed`)
- the finding→fix orchestration precedent to follow: `monitor/autofix_run.run_autofix`
- the eligibility predicate: `loop/bug_lane.evaluate_merge_guardrails`
- cap state and intake: `loop/bug_lane_state.GitHubMergeCapState`,
  `triaged_bug_intake`, `record_merge`
- the dial and limits: `loop/agent_policy.resolve_bug_automerge`, `bug_lane_limits`
- escalation: `loop/escalation.emit_escalation(correlation_id, *, category,
  repo, done_so_far, issue_summary, decision_needed, why_not_auto, options,
  recommendation, assignee=..., runner=...)` — note `options` is a list of
  `(label, pros, cons)` tuples and **at least two are required**

**The one mechanism that does not exist yet.** The roadmap row's "on CI green"
assumes a readable CI conclusion per PR; this repo has no wrapper for it. Build
the thinnest possible one — `pr_ci_conclusion(runner, repo, pr_number) -> str`
over `gh pr checks` — returning a bare conclusion string. It must return a
non-`"success"` value (not raise) when the conclusion cannot be read, so T02's
fail-closed guardrail declines rather than the process crashing.

**Merge is conditional on two independent things, and both must hold:** the dial
`resolve_bug_automerge()` is `True`, **and**
`evaluate_merge_guardrails(...).eligible` is `True`. The dial alone never
merges. Write the code so the guardrail call cannot be skipped when the dial is
on — a single `if dial and decision.eligible:` with no other merge call site in
the module.

**On any declining path the PR stays open.** Label it with the declining
reason and stop. Do not close it, do not retry, do not re-invoke `/fix-bug`. A
green, ready-to-merge PR awaiting a human is the dial-off outcome anyway, so a
guardrail failure costs nothing but the merge.

**Flag-scope table** (`.specfuse/rules/planning-discipline.md` §3). The flag is
`rules.bugs.automerge`, read via `resolve_bug_automerge()`:

| Code path | Gated by flag? | Why |
|---|---|---|
| `run_bug_lane` — merge call | **yes** | The only merge site. Requires dial `on` *and* all six guardrails eligible. |
| `run_bug_lane` — `/fix-bug` invocation | no | The fix runs at both settings. The dial governs merging, never whether work happens. |
| `run_bug_lane` — PR creation | no | `/fix-bug` opens the PR at both settings; dial `off` simply leaves it for a human. |
| `run_bug_lane` — guardrail evaluation | no | Evaluated at both settings so the reason label is always accurate. The dial cannot skip the check. |
| `run_bug_lane` — escalation on refusal | no | Refusals escalate at both settings; silence is the failure mode FEAT-2026-0046 exists to remove. |
| `bug_lane_state.record_merge` | yes | Only reached after an actual merge, so the cap counts merges, not attempts. |
| Feature gate review, `features.gate_review` | no | Different lane, different dial. This flag does not reach features and must not be made to. |
| `monitoring.yml`'s `autofix` / `diagnose` dials | no | Different pipeline (FEAT-2026-0041/0042), own dials. |

**Headline claim checked against the table:** the roadmap says "the dial opens
the gate, never removes the guardrails." The table supports exactly that — the
dial gates one call site, and the guardrail evaluation is ungated.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because the
module does not exist.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_bug_lane_run.py::TestRunBugLane::test_dial_off_never_merges`
   exists and **fails on HEAD before this WU runs**.
2. `specfuse/loop/bug_lane_run.py` defines
   `run_bug_lane(runner, repo, issue_number, *, working_dir=".", policy_path=None)`
   returning a result object naming the outcome and, when no merge happened, the
   declining reason.
3. **Dial off never merges.** A test asserts that with
   `rules.bugs.automerge: off` and all six guardrails satisfied, no merge
   command reaches the runner.
4. **Guardrails cannot be bypassed by the dial.** A test asserts that with the
   dial `on` and exactly one guardrail failing, no merge command reaches the
   runner — repeated for each of the six guardrails.
5. A test asserts the module contains exactly **one** call site that issues a
   merge, and that it is reached only under `dial and decision.eligible`.
6. `pr_ci_conclusion(runner, repo, pr_number) -> str` exists and returns a
   non-`"success"` string rather than raising when the conclusion is missing,
   malformed, or the command fails. A test covers all three.
7. On a declining path the PR is labeled with the guardrail's reason constant
   and left **open** — a test asserts no close command and no re-invocation
   reaches the runner.
8. A `/fix-bug` outcome of `refused` or `could_not_proceed` (per
   `autofix_invoke.OUTCOMES`) calls `escalation.emit_escalation` with
   `category`, at least two `(label, pros, cons)` options, and a
   `recommendation`. A test asserts the call happens and that the escalation is
   emitted at **both** dial settings.
9. A test asserts `emit_escalation` is called with this WU's correlation ID
   shape so its idempotency (one issue per correlation ID) holds across repeated
   runs.
10. After a successful merge, `bug_lane_state.record_merge` is called exactly
    once, so the daily cap counts merges rather than attempts. A test asserts it
    is **not** called on any declining path.
11. Every GitHub interaction goes through the injected `runner`; a test
    exercises the full happy path and every declining path with a fake runner
    and no network.
12. `python3 -m unittest tests.test_bug_lane_run -v` exits zero after this WU's
    edits.
13. `python3 -c "from specfuse.loop.bug_lane_run import run_bug_lane, pr_ci_conclusion"`
    exits zero.

**Do not touch.** `specfuse/loop/bug_lane.py` — T02 owns the predicate; if a
guardrail seems wrong, report it rather than weakening it here.
`specfuse/loop/bug_lane_state.py` — T03 owns it. `specfuse/loop/arm_eval.py`.
`specfuse/monitor/autofix*.py` — call them, do not modify them.
`.specfuse/agent-policy.yml` — the live dial stays `off`; this WU must not flip
it. `.specfuse/skills/fix-bug/` — no refusal path is weakened or removed.
`.specfuse/roadmap.md`. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, `agent-policy-example-lint`.
Plus the scoped red/green run in criteria 1 and 12 and the symbol check in 13.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`gh pr checks` output cannot be parsed into a single conclusion reliably enough
to gate a merge on — an unreliable CI read is a reason to stop, not to guess;
`emit_escalation`'s signature differs from this WU's Context; or any acceptance
criterion here would require making a merge reachable on a path the flag-scope
table marks ungated. **Never** widen the merge condition to make a test pass. If
`specfuse/loop/bug_lane_run.py` is absent from the files you edited, emit
`status: blocked` — do not claim complete.
