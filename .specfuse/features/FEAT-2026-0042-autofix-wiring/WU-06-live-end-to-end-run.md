---
id: FEAT-2026-0042/T06
type: implementation
status: done
attempts: 1
planned_cost_usd: 8.00
unsandboxed: true
unsandboxed_rationale: "The whole point of this work unit is that the firing path reaches a real repository: it makes live `gh` calls (create/view/label/close an issue, view/close a pull request) and launches a real headless `fix-bug` session. `gh` fails inside the command sandbox with an invalid-token error and a TLS certificate failure — LEARNINGS [FEAT-2026-0014/T01/gh-claudeP-broken], corrected 2026-08-03 by FEAT-2026-0041/G1-CLOSE, whose T04 ran unsandboxed and completed a full live round-trip on attempt 1. The escape is confined to this single work unit; T04 and T05 are sandboxed, stub-verified, and forbidden from writing `gh` calls."
produces:
  - tests/test_autofix_live.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-08-04T02:31:08.430717+00:00
duration_seconds: 1226.046
cost_usd: 5.233972
input_tokens: 166
output_tokens: 49581
---

# The live run: fire the dial for real against a disposable target

**Objective.** Prove the firing wiring works end to end against a real repository —
a scratch issue this work unit creates describing a bug it plants in a throwaway
clone, T05's wiring firing on it, a real branch and a real pull request produced, and
every object cleaned up in the same run.

**Context.** Correlation ID `FEAT-2026-0042/T06`. Read `PLAN.md`, `GATE-02.md`,
`GATE-02-REVIEW.md`, and `RETROSPECTIVE.md` first, then
`.specfuse/features/FEAT-2026-0041-diagnose-issue-skill/WU-04-live-gh-roundtrip.md` —
this work unit copies that one's posture deliberately, and reading it is cheaper than
rediscovering why. This is the work unit carrying `unsandboxed: true`; the rationale
is in its frontmatter and the driver refuses the flag without one.

**Run the `gh` and `claude` commands unsandboxed.** If a `gh` call returns
`The token in GH_TOKEN is invalid` or `tls: failed to verify certificate`, you are
sandboxed — that is the artifact `LEARNINGS [FEAT-2026-0014/T01/gh-claudeP-broken]`
describes, **not** a broken feature and not a reason to weaken an acceptance
criterion. Re-run the command unsandboxed.

**Do not trust your own summary of a command's result.** Per
`LEARNINGS [FEAT-2026-0014/T01/preflight-must-dump-raw]`, dump raw stdout and stderr
between unforgeable `PROBE_BEGIN` / `PROBE_END` markers and quote them in the result,
with exit codes. A classification of an external tool's behaviour is not evidence
when the raw output exists.

## The safety floor — carried forward, not re-decidable here

Auto-merge belongs to [FEAT-2026-0048](../../roadmap.md#feat-2026-0048) and is
**impossible in this feature**. No work unit in this gate may merge a pull request,
enable auto-merge, or push to a protected branch. The ceiling is an unwanted PR on a
branch. A work unit that believes it needs to widen this is an escalation to the
operator, not a judgement call.

This is the work unit where that floor stops being theoretical. A pull request will
exist and it will be closeable in one command. Close it. Do not merge it.

## Blast radius, deliberately bounded

**The planted bug never enters this repository's working tree.** Clone this
repository into a temporary directory and plant the bug *there*. The driver owns this
branch and every commit on it; a headless `fix-bug` session branching, committing, and
pushing inside the driver's own working tree would corrupt the bookkeeping the driver
depends on. The clone is the isolation, and it is not optional.

**The target is planted, not found.** Firing against a real finding is not this gate's
job. The bug is trivial and disposable by construction, so the pull request it
produces is disposable too — which is the only reason a live fire is safe here at all.

**Everything created is named after this work unit.** The scratch issue's title and
body, and every branch this run creates, carry `FEAT-2026-0042/T06`, so a stray object
left by a killed attempt is unambiguously identifiable as test residue rather than a
real finding or someone's work.

**Why this work unit is larger than its siblings.** Setup, fire, verify, and cleanup
cannot be split across work units: each dispatch is a fresh session, and a second
session would inherit live GitHub objects it did not create, with no reliable way to
tell them from residue. One session owns the whole lifecycle, including the cleanup.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `operator-escalation.md`.

## What this work unit does NOT assert

**Not that the fix is correct.** `RETROSPECTIVE.md` records fix correctness as an
inherent limit of this feature, not a gap to close: nothing here asserts a generated
patch is right, and a criterion of that shape must not be written. This work unit
asserts the *mechanism* ran — the decision fired, the attempt was recorded, a session
launched, an outcome came back, a pull request exists — and nothing about the quality
of what is inside the pull request.

**Red-test exempt** (`authoring-work-units` §12): this work unit introduces no
production behaviour — T04 and T05 already shipped all of it, each with its own red
test. Its deliverable is a skip-guarded live harness, and its real oracle is raw
command output quoted in the result, not a red→green transition. A red test here
would assert against GitHub state that does not exist until the run creates it.

**Not that `completed` is the only acceptable outcome.** `refused` is a normal,
expected result of a fired run: `fix-bug`'s refusal paths are a second guardrail
behind T01's predicate, and the retrospective says so plainly. Criterion 6 is met by
any of the three outcomes. Criterion 7 is met only by `completed` — and if the run
does not reach it, that is reported honestly under the escalation triggers below,
never engineered around by re-planting an easier bug.

**Acceptance criteria.**

1. `tests/test_autofix_live.py` exists and carries the live run as a test that
   **skips explicitly** when `gh` is unavailable or unauthenticated — a named skip,
   not a silent pass. A test that vacuously passes without reaching GitHub is the
   failure mode this work unit exists to remove.
2. **Live preflight, raw evidence.** Run `gh auth status`. Dump raw stdout+stderr
   between `PROBE_BEGIN` / `PROBE_END` markers and quote it in the result with its
   exit code. It must show `Logged in to github.com`.
3. **The planted bug lives only in a throwaway clone.** Clone this repository into a
   temporary directory, plant a trivial, obviously-wrong, self-contained defect there,
   and confirm no file in this repository's own working tree carries it — quote
   `git -C <clone> status --short` from inside the clone and name the temporary path.
4. **The scratch issue.** Create an issue in this repository whose title and body name
   `FEAT-2026-0042/T06` and describe the planted bug, and post a diagnosis comment on
   it whose `confidence` is above T01's threshold and whose `fix_scope` is `small`,
   rendered through `specfuse/monitor/diagnosis.py` rather than hand-written. Quote
   the raw output of each `gh` call and report the issue number.
5. **The fired run.** Run T05's wiring against that issue with a monitoring config
   written to a temporary file that sets the component's `autofix` to `"on"`, with the
   clone as the working directory. Quote the run's raw stdout+stderr between markers.
   The shipped `.specfuse/monitoring.yml.example` stays at `"off"` and is not edited.
6. **The mechanism ran.** After the run, the attempt marker is present on the scratch
   issue — quote raw `gh issue view --json body` — and the run returned one of the
   three named outcomes. Name which one it returned.
7. **On `completed`: a real pull request exists, and the safety floor held.** Name the
   branch and the pull-request number, and quote raw `gh pr view` output showing its
   state. State explicitly that the pull request was **not merged**, that auto-merge
   was **not enabled**, and that nothing was pushed to a protected branch.
8. **Cleanup, in the same run.** Close the pull request, delete every branch this run
   created, and close the scratch issue. Quote the raw output of each command, and
   report every object's number and final state in the result whether or not its
   cleanup succeeded, so a human can find what survived.
9. **Residue reported, not removed.** If a scratch issue, branch, or pull request from
   a prior attempt of this work unit is still open, name it in the result rather than
   silently closing it — a killed attempt leaving residue is information about attempt
   behaviour, not litter to hide.
10. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
    `leak-scan`.

**Do not touch.** `specfuse/monitor/autofix.py`, `specfuse/monitor/autofix_state.py`,
`specfuse/monitor/autofix_invoke.py`, and `specfuse/monitor/autofix_run.py` — T01,
T02, T04, and T05 own them; this work unit is a consumer proving the wiring holds
live, not a place to fix it, and a defect found here is an escalation.
`plugins/specfuse/skills/fix-bug/SKILL.md` and its vendored copy under
`.specfuse/skills/fix-bug/` — T03 owns them. `.specfuse/monitoring.yml.example` and
`specfuse/loop/data/monitoring.yml.example` — the shipped default stays `"off"`; the
run uses a temporary config file, and the two copies are byte-compared by
`tests/test_scaffold_data_in_sync.py`, so an edit to either goes red. Any issue,
branch, or pull request in this repository other than the scratch objects this work
unit creates — no comments, no edits, no closes on real work. This repository's own
working tree, except `tests/test_autofix_live.py`: the planted bug lives only in the
temporary clone. The driver owns all git in this repository and this session never
runs `git` against this working tree — `git` inside the throwaway clone is this work
unit's own subject and is expressly permitted there.

**Verification.** The `code` gate set in `.specfuse/verification.yml` — every gate in
that set: `tests`, `lint`, `security`, `coverage` (≥90%), `leak-scan`. Beyond the
gates, criteria 2 through 8 are the real oracle: raw command output quoted in the
result, with exit codes. A green suite with a skipped live test is **not** this work
unit passing — criterion 1's skip exists for other environments, and this run must
actually reach GitHub and actually launch a session.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: `gh`
fails unsandboxed with a real authentication or permission error, as opposed to the
sandbox artifact, which you must retry unsandboxed before concluding anything; the
account lacks permission to create an issue, push a branch, or open a pull request in
this repository; the headless session cannot be launched at all — report the raw
failure and block, because a stubbed live run is worth less than no live run, since it
would read as live evidence; the fired run returns `refused` or `could_not_proceed`,
which satisfies criterion 6 but leaves criterion 7 unmet — report the outcome with its
raw output and block, rather than re-planting an easier bug until a run happens to
reach `completed`; or cleanup cannot complete, in which case name every surviving
object by number. Do **not** weaken any acceptance criterion to make this work unit
green — its entire value is being the one place this feature's firing path is not a
stub. Do **not** merge the pull request, enable auto-merge, or push to a protected
branch under any circumstance: that is FEAT-2026-0048's territory and an escalation to
the operator, not a judgement call available to this session.
