# FEAT-2026-0013 Retrospective (v3 — final)

Single-gate feature. One substantive WU (T01) + this combined close
(G1-CLOSE). Goal: eliminate the `OSError: [Errno 39] Directory not
empty: '/tmp/.../.git/objects'` race that `integration_workspace()`
fixtures trigger when Python 3.12's `shutil.rmtree` runs against
in-flight git fds.

Three ship attempts preceded this close. v1 and v2 each shipped with a
single-file fix and each re-failed on Linux CI in a DIFFERENT
`integration_workspace` definition. v3's discovery: the repo carries
FIVE copies of the fixture. v3 centralizes all five into one shared
helper at `tests/_workspace.py` carrying root-cause guards
(`gc.auto=0`, `git rev-parse HEAD` sync barrier, `check=True` on
every git call) + the belt-and-suspenders
`ignore_cleanup_errors=True` ONCE. The five duplicate `def
integration_workspace()` definitions are replaced with
`from tests._workspace import integration_workspace`.

`RETROSPECTIVE-v1.md` and `RETROSPECTIVE-v2.md` preserved in this
folder for audit; this file is the v3 / final close.

## T01 — Audit and fix fd/handle leaks in integration_workspace (v3)

**Outcome.** PASS, ran across three re-arm cycles. Final commit
`5babf50` carries the centralized fix. T01 frontmatter:
`attempts: 2` (final v3-attempt-3 run), `cost_usd: 2.715082`,
`duration_seconds: 1898.807`. v3 attempts 1 and 2 escalated
`blocked_human` on a `ssh-agent unreachable` block in
`tests/test_loop_orchestration.py::_minimal_git_repo` (global git
config carried `commit.gpgsign=true` + `gpg.format=ssh`, ssh-agent
not running inside the dispatched session). The operator disabled
`commit.gpgsign` locally; v3-attempt-3 then completed.

v3-attempt-3 itself ran two attempts. Attempt-1 reported `complete`
but `tests/_workspace.py` showed no diff against `head_before`
(`attempt_outcome: files_changed_mismatch` per `events.jsonl:16`);
the FEAT-2026-0008 `files_changed` diff guard fired, rolled back via
`git reset --hard head_before`, and re-dispatched. Attempt-2 wrote
`tests/_workspace.py` correctly and replaced all five duplicate
definitions with imports.

**Evidence per WU (this v3 run, `events.jsonl:11-17`).**

- `events.jsonl:11` — v3-attempt-1 `task_started 2026-06-12T13:16:33Z`.
- `events.jsonl:12` — v3-attempt-1 `human_escalation`,
  `reason: agent_reported_blocked`, blocked_reason quotes the
  `commit.gpgSign` ssh-agent issue in
  `tests/test_loop_orchestration.py::_minimal_git_repo` (out-of-scope
  for T01 per do-not-touch). Cost $1.742, 697s.
- `events.jsonl:13-14` — v3-attempt-2 `task_started 13:50:40Z`,
  `human_escalation` at `14:21:34Z` for the same ssh-agent block.
  Two attempts, $1.210 + $1.745 = $2.955, 1014s + 841s = 1855s.
- `events.jsonl:15` — v3-attempt-3 `task_started 15:35:13Z` after
  operator disabled `commit.gpgsign` locally
  (commit `7d37159`).
- `events.jsonl:16` — v3-attempt-3 attempt-1 `attempt_outcome:
  files_changed_mismatch`, `unchanged_paths: ["tests/_workspace.py"]`.
  FEAT-2026-0008/T02's `files_changed` diff guard caught a session
  that claimed PASS without writing the new file.
- `events.jsonl:17` — v3-attempt-3 `task_completed`, `attempts: 2`,
  final cost $2.715, 1898s.

Final commit `5babf50` — `feat: Audit and fix fd/handle leaks in
integration_workspace` — touched 6 files:
`tests/_workspace.py` (NEW) + 5 test files replacing their local
`def integration_workspace()` with `from tests._workspace import
integration_workspace`.

**What worked.**

1. **Scope-widened AC enumerated the 5 sites.** v3's WU AC2 named
   each duplicate site by file + line number. The agent did not
   have to grep-and-discover; the spec did the discovery work that
   v2 missed. Result: one diff-shape across 6 files, no scope
   confusion.
2. **`tests/_workspace.py` as the central source of truth.**
   Future race fixes touch one file. The five test files reduce
   to a single import line each. New tests that need an integration
   workspace can simply import the helper.
3. **The FEAT-2026-0008 `files_changed` diff guard caught a hollow
   PASS.** v3-attempt-3 attempt-1 reported `complete` without
   writing `tests/_workspace.py`; the guard rolled back the squash
   and re-dispatched. Without FEAT-2026-0008, the session would
   have committed nothing and `status: done` would have advanced
   the dependency frontier — exactly the failure FEAT-2026-0008
   was built to catch. Live, in-the-wild recursive validation.
4. **Cost preserved via frontmatter `historical_*` fields across
   THREE re-arm cycles.** v1, v2, v3-attempts-1+2 costs were all
   summed into `historical_cost_usd: 5.228352` /
   `historical_duration_seconds: 3181.344` on the T01 frontmatter
   before this v3-attempt-3 ran. The audit signal that prior
   failed attempts were preserved, not silently overwritten, is
   queryable from the WU frontmatter alone.

**What failed and why.**

1. **v3-attempts-1 and 2 burned $4.70 / 2552s on a host-config
   block.** The block — global `commit.gpgsign=true` +
   `gpg.format=ssh` without a running ssh-agent — fires inside
   `tests/test_loop_orchestration.py::_minimal_git_repo`. That
   test file is explicitly out of T01's scope per do-not-touch.
   The agent correctly emitted `status: blocked` both times
   rather than scope-creep. Recovery was an operator-side
   `git config --local commit.gpgsign false` (commit `7d37159`)
   to disable signing for the working copy. Lesson:
   global-git-config state can ambush WU dispatch when it differs
   from CI's git environment; document at WU author time.
2. **v3-attempt-3 attempt-1 hollow-PASS'd.** The session
   reported `complete` but did not write the new file. The
   FEAT-2026-0008 guard caught it; this is exactly the recursive
   validation FEAT-2026-0008 was designed for. The deeper lesson:
   the WU spec's AC3 source-presence check WOULD have caught it
   too at agent-side if the agent had reached AC3 before
   reporting — but the agent didn't run AC3 before declaring
   complete. Agent-side ACs and driver-side guards are
   complementary; the guard is the load-bearing safety net.

**Rule/template/boundary missing or ambiguous.**

1. **Scope-discovery for cross-cutting fixture races.** v1 and v2
   each fixed one of five integration_workspace copies and shipped
   on a single-site oracle ("the 50× macOS-local audit was clean
   for THIS test"). Each shipped fix re-failed on a DIFFERENT
   `integration_workspace` site. The methodology lacked a "audit
   all sites that match this pattern" requirement before the WU
   author considered the fix shaped right. v3's spec added the
   enumeration explicitly. This becomes a durable LEARNINGS entry
   below.
2. **Host-config preflight.** No skill / driver code today warns
   the operator that the dispatched agent will fail on a global
   git config state. The `/wrap-feature` skill could add a
   `git config --get commit.gpgsign` preflight before push, but
   the v3 cost shows this matters at DISPATCH time, not just
   push time. Durable LEARNINGS entry below.

## 50× recursive audit (macOS local)

The WU spec's literal command:

```
for i in $(seq 1 50); do .venv/bin/python3 -m unittest tests.test_driver_integration -q 2>&1 | tail -1; done | sort | uniq -c
```

Literal output from this close session, post-T01-v3-squash on HEAD
`5babf50`:

```
  50 Inconsistency: terminal gate closed without close ceremony flipping PLAN.md to `done`. Inspect RETROSPECTIVE.md / events.jsonl. Likely fix: manually flip PLAN.md `status: active -> done`, then `/wrap-feature`.
```

One distinct line, count 50 — uniform behavior across all 50 runs.

**Reading the output.** Per the durable LEARNINGS entry on
`tail -1` oracle fragility (`[FEAT-2026-0013/G1-CLOSE]`), this line
is NOT a test failure. It is stdout from `loop.py`'s gate-status
path, emitted by an `integration_workspace` sub-test that runs the
driver as a subprocess and whose driver output arrives on the
parent's stdout AFTER unittest's `OK` / `FAILED` summary line.
`tail -1` therefore picks up driver chatter, not the unittest
verdict. The shape matches v1 and v2 audits exactly — no
regression, no new failure mode.

**Truth via exit code** (the durable oracle per the LEARNINGS
entry on tail-1 fragility):

```
PASS:50 FAIL:0
```

50 of 50 unittest invocations exited 0. No `FAILED`, no `ERROR`,
no `OSError: Directory not empty`. The integration suite ran 50
times back-to-back on macOS with no leaked fds, no rmtree race.

**Interpretation.** AC2 intent satisfied in substance — a single
distinct line across 50 iterations + 50× exit 0 confirms no race
hit on macOS. The literal `tail -1` output is cosmetic spec drift
documented since v1 close.

**v1 LESSON (durable, twice-burned): this audit alone is
INSUFFICIENT.** v1 passed it 50/50 and failed on Linux ext4 CI
runner `27412918877`. v2 passed it 50/50 + a 50× Linux Docker
probe and failed on Linux CI runner `27417616885` in a DIFFERENT
`integration_workspace` definition (scope-discovery miss). The
50× macOS-local audit is NECESSARY but NOT SUFFICIENT evidence
that the goal is met. The FINAL oracle is the operator-side Linux
Docker probe (`scripts/check-linux-race.sh`) run pre-push at the
`/wrap-feature` step PLUS the CI run on the pushed branch — AND
the CI run must exercise the suite as a whole, not just one test
file, because v2's failure surfaced in a different test file
from v1's.

## v1 cost reconciliation

Per WU frontmatter (preserved across THREE re-arm cycles in
`historical_*` fields):

- `WU-01-audit-and-fix-fd-leaks.md`:
  `historical_cost_usd: 5.228352`,
  `historical_duration_seconds: 3181.344`,
  `historical_input_tokens: 134`,
  `historical_output_tokens: 120510`.

  This sum decomposes as: v1 T01 ($0.327 / 362s) + v2 T01
  ($0.205 / 266s) + v3-attempt-1 T01 ($1.742 / 697s) +
  v3-attempt-2 T01 ($2.955 / 1855s) = $5.229 / 3180s — matches
  to rounding.

- `WU-90-close.md`:
  `historical_cost_usd: 3.736543`,
  `historical_duration_seconds: 1017.459`,
  `historical_input_tokens: 63`,
  `historical_output_tokens: 26776`.

  Decomposes as: v1 G1-CLOSE ($1.887 / 582s) + v2 G1-CLOSE
  ($1.850 / 435s) = $3.737 / 1017s — matches.

Historical sub-total (v1 + v2 + v3 blocked attempts):
`$8.964895`, `4198.803s`.

v3-attempt-3 this run (final, completing values from
`events.jsonl:11-17`):

- T01 v3-attempt-3: `cost_usd: 2.715082`,
  `duration_seconds: 1898.807` (`events.jsonl:17`).
- G1-CLOSE v3-attempt-3: accrues this session — final values
  appear in `events.jsonl` after `task_completed` fires.

v3 cumulative total (v1 + v2 + v3 blocked + v3 final) =
`$8.964895 + $2.715082 + G1-CLOSE-final` ≈ `$11.68` baseline plus
this session's G1-CLOSE accrual. The audit signal — that the cost
of failed attempts was preserved, not silently overwritten on
re-arm — is queryable directly from the `historical_*` fields in
each WU's frontmatter; no information loss across three re-arm
boundaries.

The reconciliation also documents that the methodology's cost of
chasing a Linux-CI race from a macOS workstation, with imperfect
scope-discovery, is non-trivial — ~$12 to land a 6-file change.
The cost lives mostly in (a) two rounds of "ship + Linux CI
re-fails + re-arm" cycles, and (b) two v3 dispatches burned on
host-config (ssh-agent gpg) before recovery.

## Recovery from prior drift

Three documented drifts across this feature's three ship attempts:

1. **v1's `tail -1 | sort | uniq -c` oracle drift.** Documented at
   v1 close in LEARNINGS `[FEAT-2026-0013/G1-CLOSE]` (oracle
   fragility). v2 reused the literal command intentionally to
   test whether the lesson had been internalized — it had. v3
   reuses again; the lesson held a second time.
2. **v1's wrong-environment oracle.** Documented at v2 close in
   LEARNINGS `[FEAT-2026-0013/G1-CLOSE]` (oracle environment must
   match goal environment) + `[FEAT-2026-0013/G1-CLOSE]`
   (script-parity ≠ environment-parity). v3 honors both: a Linux
   Docker probe + post-push CI run remain the load-bearing
   verifications. v2's evidence proved the Docker probe alone is
   still insufficient when scope discovery is partial — adds the
   new lesson below.
3. **v2's scope-discovery miss.** v2 fixed `test_driver_
   integration` but four other `integration_workspace`
   definitions remained unfixed. The Linux CI re-fail surfaced
   the gap. Promotes to a durable LEARNINGS entry below
   (centralize-or-enumerate fixture patterns).

# Feature-arc verdict

**Met locally; field-confirmation pending operator action.**

`roadmap_goal` from PLAN.md:

> Eliminate the fd-leak race in `integration_workspace()` so the
> integration-test path is deterministic on Python 3.12 CI runners
> (no `OSError: Directory not empty` flakes).

## Evidence for goal-met (local, macOS)

The 50× recursive audit (this v3 close session, post-T01-v3-squash
on HEAD `5babf50`) shows 50 of 50 unittest invocations exit 0. No
`OSError: Directory not empty` fires, no `FAILED` line, no `ERROR`
line, no test-process crash. Literal `tail -1 | sort | uniq -c`
output:

```
  50 Inconsistency: terminal gate closed without close ceremony flipping PLAN.md to `done`. Inspect RETROSPECTIVE.md / events.jsonl. Likely fix: manually flip PLAN.md `status: active -> done`, then `/wrap-feature`.
```

One distinct line, 50 occurrences — matches v1's and v2's audit
shape (the `tail -1` line is driver chatter from an inner
integration test, documented in LEARNINGS). Exit-code count:
`PASS:50 FAIL:0`. All three guards present and centralized in
`tests/_workspace.py` (`gc.auto=0` + sync barrier +
`ignore_cleanup_errors=True`); all five test files now import the
single shared definition.

## v1 LESSON explicitly invoked: local-audit is NECESSARY but NOT SUFFICIENT

v1 passed this exact audit 50/50 on macOS local and THEN the same
race fired on Linux CI runner `27412918877` (PR #9). v2 passed it
50/50 + passed a 50× Linux Docker probe + THEN the same race fired
on Linux CI runner `27417616885` in a DIFFERENT integration_workspace
definition. macOS APFS hides cleanup races that Linux ext4 surfaces;
local 50× audit on a SINGLE test file cannot generalize to
suite-wide Linux CI behavior. A clean 50× macOS audit is NOT
evidence about Linux CI behavior. The verdict CANNOT claim
Linux-CI determinism on local evidence alone.

## FINAL oracle (operator-responsibility)

Two evidence sources outside this close session establish
Linux-environment determinism:

1. **`scripts/check-linux-race.sh`** — a Linux Docker probe that
   runs the integration suite in a Linux container, surfacing the
   ext4-specific race the macOS-local audit cannot see. The
   operator MUST run this pre-push at the `/wrap-feature` step
   (step 4 or 5 per skill spec). Exit-0 with clean iteration
   summary on the FULL suite (not just `test_driver_integration`)
   is REQUIRED before push. v2's failure proved that running the
   probe on a single test file is insufficient — the probe must
   exercise the SAME suite shape CI runs.
2. **CI run on the pushed branch.** GitHub Actions runs the
   integration suite on the actual Linux runner shape that fired
   v1 and v2's failures. A clean run on the post-push CI is the
   only environment-true field test. The operator's responsibility
   ends here; if the race fires again, recovery is a new feature
   (FEAT-2026-0015), not a re-arm of this one.

The verdict is `goal met locally, awaiting operator Linux-probe
+ CI confirmation`. If `scripts/check-linux-race.sh` (on the FULL
suite, not just one test) fires the race in Docker, recovery is to
re-arm T01 (NOT this close) with a sharper scope of fixture audit.
If post-push CI fires the race despite the Docker probe passing on
the FULL suite, the probe itself is insufficient at a level the
methodology cannot easily close (kernel-version-specific or
container-runtime-specific behavior) and v3-recovery work expands
to either a CI-environment-specific fix or an
`integration_workspace` API redesign.

## Recommended operator next step

Run `/wrap-feature`. At the Linux Docker probe step:

1. Invoke `scripts/check-linux-race.sh` against the FULL test
   suite (not just `test_driver_integration` — v2's failure
   surfaced in `test_loop_files_changed_guard`).
2. Confirm exit-0 with 50/50 clean iterations across all
   integration-workspace-using tests.
3. If green: push.
4. If post-push CI green: field-confirmed.
5. If either red: do NOT merge PR; either re-arm T01 with a
   sharper fixture-audit AC or file FEAT-2026-0015 with the
   failing test name + fresh Linux traceback + a hypothesis on
   what the centralized helper does not cover.

## Reconciliation with prior roadmap state

`.specfuse/roadmap.md` shows FEAT-2026-0013 as `status: done`
(table row, line 31) AND `**Status: done.**` in the detail block
(line 595). The detail block's narrative currently describes v1's
fix at HEAD `2a9e2aa` ("T01 audited `integration_workspace` and
applied two coupled fixes in one attempt"). This narrative is no
longer the ship state: v1, v2 each shipped and re-failed; v3 is
the actual ship, at HEAD `5babf50`, with a centralized helper at
`tests/_workspace.py` and 5 test files importing it.

Per escalation trigger 2 in WU-90 ("If roadmap.md already shows
this feature as done... do not overwrite — read the existing
state, reconcile in the verdict, and stop"), this RETROSPECTIVE
records the reconciliation: the table row's `done` status is
correct in shape but the detail block's narrative is two ship
attempts stale. v3's true state lives in this file and in commit
`5babf50`; the roadmap detail block describes the v1 attempt that
failed Linux CI. A future doc-cleanup WU (or operator amendment
at `/wrap-feature`) may update the detail block to cite HEAD
`5babf50` and the centralized helper; this close ceremony does
not overwrite per the escalation rule.
