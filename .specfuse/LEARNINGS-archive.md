---
project: specfuse-loop
---

# Archived LEARNINGS

Entries retired from `.specfuse/LEARNINGS.md` by `/learnings-curate` because they
were duplicated, superseded, or promoted into `.specfuse/rules/*.md`. Kept for
provenance — planning sessions do NOT load this file. Retirement reason and date
travel with each entry. Nothing here is authoritative; `.specfuse/LEARNINGS.md`
and `.specfuse/rules/*.md` are.

## Retired entries

### Curated 2026-08-11

- [FEAT-2026-0013/G1-CLOSE] Global git config can ambush WU
  dispatch. A developer machine carrying `commit.gpgsign=true` +
  `gpg.format=ssh` GLOBALLY (the default for some setups) will
  fail any `git commit` inside a dispatched agent session when no
  ssh-agent is reachable in the session's environment. The failure
  surfaces as `gpg failed to sign the data` / exit 128 inside any
  test fixture that runs `git commit`, including
  `_minimal_git_repo()` helpers. The agent — correctly — emits
  `status: blocked` rather than scope-creep into the test file,
  burning a dispatch cycle. Recovery is an operator-side
  `git config --local commit.gpgsign false` (working-copy only;
  preserves the global setting for the operator's own commits).
  FEAT-2026-0013 v3-attempts-1 and 2 burned $4.70 / 2552s on this
  block before the operator disabled it locally. Rule: every WU
  spec that requires `git commit` inside a temp-repo test fixture
  MUST also (a) set `commit.gpgSign=false` on the temp repo
  (`git -C <root> config commit.gpgSign false` right after
  `git init`), AND (b) document in the feature folder's PLAN.md or
  RETROSPECTIVE.md that the operator must verify
  `git config --get commit.gpgsign` returns `false` or empty in
  the repo's working copy BEFORE the first dispatch. The skill-side
  remedy is to extend `init.sh` or `/wrap-feature` with a preflight
  check on the operator's global gpg config; until that lands, this
  is a known dispatch-time foot-gun.
  _Retired: Merged into one entry carrying all 4 tags._

- [FEAT-2026-0040/G2-CLOSE-INTERMEDIATE] **A test fixture that builds a throwaway git repo
  must pin every commit-affecting setting, not just identity — otherwise it inherits the
  host operator's global config and fails for reasons that have nothing to do with the
  code under test.** `tests/test_autosync_no_cwd_leak.py` sets `user.name` and `user.email`
  on its temp repos and stops there, so each `git commit` inherited a global
  `commit.gpgsign = true` with `gpg.format = ssh`, and the signing agent socket is
  unreachable from a sandboxed session: `error: Couldn't get agent socket?` /
  `fatal: failed to write commit object`, exit 128, three errors in an otherwise green
  1753-test run. Confirmed by re-running the same module under
  `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false` → OK. This
  is a **different** failure from the already-recorded `mktemp`/sandbox one: that is the
  executor lacking a filesystem privilege, this is host configuration leaking into a
  fixture, and the two need different fixes. Rule: a fixture repo pins `commit.gpgsign`
  and `tag.gpgsign` to false alongside identity; and a close that meets a red gate checks
  whether the failing command reads *ambient host config* before recording the exit code
  as a regression.
  _Retired: Merged into one entry carrying all 4 tags._

- [FEAT-2026-0041/G1-CLOSE/sandbox-git-temp-repo-errors] **The `git commit` exit-128 errors in
  `test_lint_closing.py` and `test_autosync_no_cwd_leak.py` are a command-sandbox
  artifact, not a regression — stop re-diagnosing them.** Signature: 11 errors,
  every traceback ending `subprocess.CalledProcessError: Command '['git', '-C',
  '/tmp/.../tmpXXXXXXXX', 'commit', ...]' returned non-zero exit status 128` in a
  throwaway temp repo. Three consecutive WUs of one feature each spent attention
  independently establishing this. Rule: when a sandboxed suite reports errors whose
  tracebacks are all `git` subprocess calls against temp directories, re-run just
  those modules unsandboxed (`python3 -m unittest tests.test_lint_closing
  tests.test_autosync_no_cwd_leak` → `Ran 11 tests ... OK`) and quote that as the
  evidence, rather than bisecting the change under test. These two modules are safe
  to run unsandboxed: both operate exclusively inside `TemporaryDirectory` repos and
  `chdir` back on exit. Applies to any suite mixing real-`git` fixtures with a
  sandboxed gate run.
  _Retired: Merged into one entry carrying all 4 tags._

- [FEAT-2026-0059/G1-CLOSE/signing-agent-in-sandbox] **A command sandbox that denies the
  commit-signing agent socket turns every test that builds a scratch git repository red,
  with an error that names neither the sandbox nor the test.** Five tests failed with
  `error: Couldn't get agent socket?` / `fatal: failed to write commit object` /
  `returned non-zero exit status 128` from a `git commit` inside a temp-dir fixture —
  because commit signing is configured globally and the signing agent's unix socket is
  outside the sandbox, not because anything under test was broken. All five passed
  unsandboxed. Rule for any session obliged to re-run oracles fresh: before reporting a
  red, reproduce the failing primitive in isolation (`git init` + `git commit` in a temp
  dir) — a sandbox-caused failure reproduces there with zero test code involved, and the
  distinction between "the suite is red" and "the environment is red" is worth the ten
  seconds every time. Sibling trap, in the opposite direction
  ([FEAT-2026-0042/G2-CLOSE/live-tests-fire-when-unsandboxed]): the unsandboxed re-run
  that fixes these false reds is also the run where credential-gated live tests stop
  skipping and reach the real external system. Both are the same underlying fact — the
  sandbox boundary silently changes which tests are meaningful — and a close that
  re-runs oracles crosses it in both directions.
  _Retired: Merged into one entry carrying all 4 tags._

- [FEAT-2026-0051/G1-CLOSE] A driver change to dispatch control flow does NOT take effect for
  the run that writes it: Python loads the driver module once at process start, and
  gate-entry code has already executed before the first WU is dispatched. This cuts both
  ways, so state it explicitly in any self-hosting hazard note. It defuses the hazard — a WU
  editing the dispatch path cannot break the run dispatching it — and it equally invalidates
  self-hosting as EVIDENCE: a feature cannot cite "it ran against our own gates" when the
  probe it added never executed. Phrase such notes as "takes effect on the NEXT driver
  invocation," and plan a separate observation point if the self-hosted run is meant to be
  part of the acceptance evidence.
  _Retired: Merged into one entry carrying all 3 tags._

- [FEAT-2026-0053/G1-CLOSE] **A work unit that wires new code into the driver cannot be
  verified by the driver run that wired it — so a gate whose definition of done asserts driver
  runtime behavior must name its observation point, and an absent signal must never be read as
  a false claim.** The driver imports `loop.py` once at process start. Edits a work unit lands
  mid-run are dead code for the remainder of that invocation, including for every closing unit
  that follows. Gate 1 wired two call sites into `run()` (a baseline write at first dispatch, an
  `arm_predicate_evaluated` emit at every `awaiting_review` flip) and neither could fire in the
  run that landed them: `PLAN.baseline.json` existed in 0 of 43 feature directories at close
  time, which is the corroborating tell that the running process predated the edit. The trap is
  not the deferral — it is the inference the gate file had already written down: *"No event =
  the claim is false — do not arm; escalate."* That reads a stale-process artifact as a defect
  and escalates a working mechanism. Rule: when a definition-of-done criterion asserts runtime
  behavior of the driver itself, write the observation point into the criterion at drafting
  ("verified at the next driver invocation", "verified by the human at the arming checkpoint"),
  and phrase any absence check to disambiguate first — did a process launched *after* the
  commit run this path? Only then is silence evidence.
  _Retired: Merged into one entry carrying all 3 tags._

- [FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart] **A work unit that edits the
  driver has no effect on anything the same driver process dispatches afterwards —
  including the close work unit armed to verify it. Restart the driver between the
  wiring unit and its proof, or the proof measures the old code.** Observed here in
  its most expensive form: T04 wired the pre-dispatch hook into `execute_unit_attempt`
  correctly, in one attempt, with eight passing tests; the very next unit dispatched
  was the close designed to read the injected output, and its prompt carried none.
  Timestamps were decisive — the driver process imported `specfuse/loop/loop.py` at
  13:30:46 UTC (matching `GATE-01.md`'s `baseline.probed_at` to the second), T04's
  session began at 13:35:25 and ran 1413s, and the close began at 13:58:59. Python
  caches modules in `sys.modules` at first import, so the `execute_unit_attempt` in
  memory was the pre-T04 function object with no call site at all. **A deferred import
  inside the new code does not save you** — deferral moves the *callee's* import to
  call time, but the call site lives in the stale caller and is never reached. Nothing
  in the gate can catch this: unit tests, symbol imports, and close-time probes all
  run in fresh interpreters and all report the new behaviour correctly, which is
  precisely why the disagreement reads as a mystery instead of an obvious staleness
  bug. Rules. (a) When any work unit's `produces:` names a driver module, plan a
  driver restart before the unit that verifies it — treat "restart the loop" as a step
  in the gate, not an operator afterthought. (b) A close that cannot explain why a
  driver behaviour it can reproduce in-process did not happen in its own dispatch
  should check the driver process's start time (`ps -eo pid,lstart,command`) against
  the wiring unit's `started_at` before writing anything else. (c) This is the
  self-hosting form of the harness-migration hazard already in this file: there, a WU
  editing `verification.yml` or the test loader breaks its siblings' oracles; here, a
  WU editing the dispatch path silently fails to reach them.
  _Retired: Merged into one entry carrying all 3 tags._

