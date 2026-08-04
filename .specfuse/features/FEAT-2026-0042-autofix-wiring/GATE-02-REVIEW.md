---
gate: 2
open_questions:
  - "The live run's target: T06 plants the trivial bug in a throwaway clone rather than in this repository's working tree, so nothing buggy is ever committed to the feature branch. The cost is that the fired session works a clone whose branch is not the driver's — confirm that is the isolation you want, or say you would rather the target be a committed, permanently-documented scratch fixture."
  - "T06's pull request base branch is left to the session. A PR based on the default branch carries both the planted bug and its fix; a PR based on the scratch target branch carries only the fix. Both get closed unmerged, so neither is unsafe — but if you care which the residue report shows, say so before arming."
  - "T06 at $8.00 is the least-anchored estimate in the feature: no work unit in this repo has launched a nested headless session and waited for it. If the real number is 2x, gate 2's $29.50 budget halts mid-gate. Raising the budget hides the miscalibration; leaving it surfaces it. Left as drafted, deliberately."
  - "The firing entry point is `python3 -m specfuse.monitor.autofix_run`, deliberately NOT a subcommand of `specfuse-monitor run` (T05's flag-scope table, row two). That means nothing fires on a schedule — a human or a later feature has to call it. Confirm that is the intended reach for this gate, or say the harvest-cycle wiring belongs here rather than in a follow-up."
  - "T04 builds its own `claude -p` argv rather than importing the driver's dispatch path. That is a deliberate decoupling (a bug-fix launch should not live inside the surface that runs every work unit) at the price of a second place that knows the invocation shape. If you would rather it be shared, that is a change to a gate-1-owned boundary and should be decided now, not mid-attempt."
---

# Gate 2 review — the dial goes live

Written by `FEAT-2026-0042/G1-PLAN` at the gate-1 → gate-2 boundary. This file
supports the human read that arms gate 2. Gate 2 is the gate where this feature stops
being a decision layer and starts opening pull requests, so the read is worth doing
attentively.

---

## Gate 1 summary, and the one thing that changed since the retrospective

Gate 1 shipped the decision layer and fired nothing — its success condition, not a
shortfall. Three implementation work units, all first-attempt passes, $5.55 actual
against $11.50 planned.

| WU | Deliverable | Gate 2 consumes it as |
| --- | --- | --- |
| T01 | `specfuse/monitor/autofix.py` | `decide()` — the FIRE / ROUTE_TO_HUMAN / DECLINE call T05 makes |
| T02 | `specfuse/monitor/autofix_state.py`, `specfuse/loop/labels.py` | `record_attempt`, `GitHubAutofixState`, `AUTOFIX_FAILED_LABEL` |
| T03 | `plugins/specfuse/skills/fix-bug/SKILL.md` | the closed three-outcome contract T04 classifies against |

**The retrospective's one open defect is closed, and the arming read should not act on
the stale text.** `RETROSPECTIVE.md` records
`tests/test_fix_bug_headless.py::test_interactive_sections_unchanged_only_additions`
as permanently red — it compared the working tree against a moving `HEAD`, so the
commit that landed T03 invalidated it — and states plainly that "gate 2 must not be
armed on a red suite." That test was replaced after the retrospective was written.
The suite is green now, verified fresh by this work unit rather than assumed:

```
$ python3 -m unittest discover -s tests
Ran 2106 tests in 80.546s
OK (skipped=3)
exit=0
```

That is also this gate's baseline, and the §4 probe below is read against it.

## §4 runtime probe — required for this gate, and it found something

Gate 1 answered §4 "not applicable" because no default changed and nothing fired.
Inheriting that answer would have been a defect: gate 2 introduces firing behaviour
behind a dial that is currently inert, which is the exact case the rule exists for.

**What was probed.** `.specfuse/monitoring.yml.example`'s `web-api` component flipped
from `autofix: "off"` to `autofix: "on"`, then the full oracle — not a subset — run
against it.

```
PROBE_BEGIN monitoring-example-lint
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
exit=0
PROBE_END monitoring-example-lint
```

```
PROBE_BEGIN tests (full oracle, dial flipped to "on")
$ python3 -m unittest discover -s tests
======================================================================
FAIL: test_package_data_matches_canonical (test_scaffold_data_in_sync.TestScaffoldDataInSync.test_package_data_matches_canonical)
Each tracked file in specfuse/loop/data/ must byte-match .specfuse/.
----------------------------------------------------------------------
AssertionError: Scaffold data out of sync with canonical sources.
Run: scripts/sync-scaffold.sh

Diffs:
  content differs: monitoring.yml.example

----------------------------------------------------------------------
Ran 2106 tests in 80.403s

FAILED (failures=1, skipped=3)
exit=1
PROBE_END tests
```

**The failure list, which is the point of the probe.** Exactly one test fails that
passes on the identical baseline run above:
`test_scaffold_data_in_sync.TestScaffoldDataInSync.test_package_data_matches_canonical`.

**Reading it.** Two findings, and the second is the one that changed the drafts.

1. **No runtime behaviour changes at all.** No test anywhere asserts anything about a
   component whose dial is `"on"`, because as of gate 1 there is still no consumer —
   `grep -rn "autofix" specfuse/ | grep "\.py:"` outside the two autofix modules
   returns only docstring and registry references in `diagnosis.py`,
   `labels.py`, and `lint_monitoring.py`. The validator accepts `"on"` and nothing
   acts on it. So **100% of gate 2's behaviour change is the new caller**, not the
   dial — which is why T05's flag-scope table matters more than the dial's own scope.
2. **`.specfuse/monitoring.yml.example` is byte-compared against
   `specfuse/loop/data/monitoring.yml.example`.** Any work unit that edits the shipped
   example goes red until `scripts/sync-scaffold.sh` runs. This is a shipped-scaffold
   surface: flipping the example's dial would change the default every downstream
   project inherits on its next upgrade — far outside this feature's scope.
   **This is why T06 writes its `autofix: "on"` config to a temporary file** and why
   both example copies are named in T05's and T06's *Do not touch*. Without the probe
   this would have surfaced as a red suite inside a live-run attempt, which is the
   expensive way to learn it.

The flip was reverted and the revert verified: `diff .specfuse/monitoring.yml.example
specfuse/loop/data/monitoring.yml.example` reports the files identical, and all four
`autofix:` values in the example read `"off"`.

**What it does not show.** The probe cannot exercise the firing path, because the
firing path does not exist until T05 lands. It bounds the dial's reach and enumerates
the test surface an edit to the example would break; it is not evidence that firing
works. That evidence is T06's job, and it is the reason T06 exists.

## §2 satisfiability — re-answered per criterion, not inherited

Gate 1 was satisfiable by construction: nothing fired, so every criterion was a unit
test. Gate 2's criteria meet a real repository, so each was checked against what a
dispatched session can actually do.

| Criterion class | Satisfiable? | Why |
| --- | --- | --- |
| T04 — outcome classification, prompt contents, closed outcome set | yes | Pure functions over strings; the outcome set is read from the shipped `SKILL.md`, so the test cannot drift from the contract. No `gh`, sandboxed. |
| T05 — decision routing, call ordering, label mapping | yes | Injected runner and injected invoker; every assertion is about calls made on stubs. No `gh`, sandboxed. |
| T05 criterion 6 — "the harvest cycle gains no caller" | yes, and scoped | A grep of one named file (`specfuse/monitor/cli.py`), not a repo-wide scan. Per `authoring-work-units` §2, a repo-wide grep would trip on unrelated pre-existing state. |
| T06 criteria 2–6, 8, 9 — live `gh`, fired run, attempt marker, cleanup, residue | yes, **unsandboxed only** | `gh` fails inside the sandbox with an invalid-token error and a TLS failure. `FEAT-2026-0041/T04` ran unsandboxed and completed a full live round-trip on attempt 1, so this is a demonstrated capability, not a hope. |
| T06 criterion 7 — "a pull request exists" | **not by construction** | It holds only if the fired run reaches `completed`. `refused` and `could_not_proceed` are legitimate outcomes of a correctly-working mechanism. Stated as such in the draft and routed to an escalation trigger; the close hedges rather than the WU pretending. |
| Fix correctness | **never — and not written** | Inherent, per gate 1's retrospective. No criterion of that shape appears in any gate-2 draft. Belongs in the close's `## What the loop did NOT verify`. |
| Coverage ≥ 90% on the new modules | yes | Both new modules are pure-composition code with injected seams; `test_autofix_predicate.py` and `test_autofix_state.py` already demonstrate the shape at this coverage bar. |

The unsatisfiable shape this gate was most at risk of authoring — "the automated fix
produces a correct patch" — was checked for and is absent from all three drafts.

## §3 flag-scope table — now applicable

`PLAN.md` recorded §3 as not applicable, correctly, for a gate that adds no consumer.
Gate 2 adds the first one, so the table lives in `WU-05-autofix-firing-wiring.md`.
The row the arming read should linger on:

> `specfuse-monitor run` — the harvest cycle — is **not gated, because it is
> deliberately not wired.** A routine harvest that could launch a fix is a far wider
> blast radius than this gate can verify, and it would fire on findings nobody read.

Check that against this gate's headline claim. "The dial goes live" is true in the
sense that a component at `"on"` can now be fired at; it is **not** true in the sense
that anything fires on its own. If you want the headline to mean the latter, that is
a different gate, and the fourth open question above is where to say so.

## What gate 2 does

Three substantive work units plus the pre-declared terminal close. T04 → T05 → T06 is
a real dependency chain: T05 calls T04's invoker, T06 fires T05's wiring for real.

| WU | What | Sandbox | $ |
| --- | --- | --- | ---: |
| T04 | `specfuse/monitor/autofix_invoke.py` — build the headless `fix-bug` call, classify its result into T03's closed three-outcome set. Fails closed to `could_not_proceed`. | sandboxed | 4.00 |
| T05 | `specfuse/monitor/autofix_run.py` — the wiring: read the diagnosis, `decide`, record **before** firing, invoke, label. Own entry point. Carries the §3 table. | sandboxed | 4.50 |
| T06 | The live run — scratch issue, bug planted in a throwaway clone, real fire, real PR, cleanup in the same session, residue reported. | **`unsandboxed: true`** | 8.00 |
| G2-CLOSE | Terminal close: retrospective, lessons, docs, contract list, verdict. | sandboxed | 5.00 |

**Exactly one work unit escapes the sandbox**, and its rationale names why. T04 and
T05 are stub-verified and their escalation triggers forbid writing a `gh` call that
reaches a real repository; T06's *Do not touch* forbids every issue, branch, and pull
request except the scratch objects it creates itself.

### Two design decisions worth rejecting at arming if you disagree

**Record the attempt before invoking, not after.** `record_attempt` is idempotent and
exists to enforce one fix run per fingerprint. Invoke-then-record loses the marker
whenever a session is killed mid-run — which is not hypothetical, since this feature's
own gate 1 lost a T03 attempt to an infra kill that emitted no outcome event at all.
Recording first can at worst cost one fingerprint a run it never got; recording last
can cost a repository a retry storm. T05's criterion 3 asserts the *order*, not just
that both happened.

**`ROUTE_TO_HUMAN` does not record an attempt.** Routing is not a spent fix run.
Recording one would permanently bar a finding a human might later decide is worth
fixing — the fingerprint would read as already-attempted forever.

## Cross-repo contracts (`authoring-work-units` §8)

Every value in these drafts that lives in another system, checked against its
authoritative source rather than invented. §8 exists because this blind spot is
systematic in `plan-next` drafts, not random.

| Value | Authoritative source | Status |
| --- | --- | --- |
| `auto-fix-attempted-failed` | `specfuse/loop/labels.py:90` via `autofix_state.AUTOFIX_FAILED_LABEL` | **checked** — registered; T05 criterion 5 forbids the literal and requires the constant (issue #300) |
| `monitoring-finding` | `specfuse/monitor/issues.py:54` (`FINDING_LABEL`) | **checked** — read by `find_finding_issue`, which the state layer already uses |
| `refused` / `could_not_proceed` / `completed` | `plugins/specfuse/skills/fix-bug/SKILL.md`, `## Headless mode` | **checked** — T04 criterion 3 reads them from that file rather than restating them, so drift fails the test |
| `<!-- specfuse:autofix-attempt fingerprint=… at=… -->` | `specfuse/monitor/autofix_state.py` | **checked** — T06 criterion 6 asserts this marker, not a re-spelled one |
| `<!-- specfuse:finding fingerprint=… -->` | `specfuse/monitor/issues.py:60` | **checked** — T05 reads the fingerprint through `issues.py`; inventing a second marker is an escalation trigger |
| `components:` as a **list** of dicts vs `decide()`'s name-keyed mapping | `.specfuse/monitoring.yml.example` vs `specfuse/monitor/autofix.py` | **checked** — they genuinely disagree; T05 owns the adaptation and the WU says so, so it is not rediscovered mid-attempt |
| `claude -p --model … --effort …`, prompt on stdin | the loop driver's own dispatch constant | **checked** — T04 builds its own copy deliberately; see open question five |
| `gh issue create/view/edit/close`, `gh pr view/close` | `gh` itself | **unchecked by construction** — T06's live run is the check, and its raw output is the evidence |

## The safety floor, and where it is actually enforced

Auto-merge belongs to [FEAT-2026-0048](../../roadmap.md#feat-2026-0048) and is
impossible in this feature. No drafted work unit merges a pull request, enables
auto-merge, or pushes to a protected branch. The floor is restated verbatim in
`GATE-02.md` and in all three drafts.

Restating is not enforcing. Four places actually hold it:

1. **T04's prompt** must carry the prohibition as literal text (criterion 4) — the
   headless session reads that prompt and nothing else.
2. **T05's criterion 7** greps its own module for `pr merge`, `--auto`, `--admin`, and
   `push` and requires no such call.
3. **T06's criterion 7** requires the result to state explicitly that the pull request
   was not merged, auto-merge was not enabled, and nothing reached a protected branch.
4. **T06's escalation triggers** name merging as an operator escalation, not a
   judgement call available to the session.

The worst outcome the drafted gate can produce is an unwanted pull request on a
branch — cheap to close, nothing on a protected branch, nothing in production.

## Arming checklist

- [ ] Read the five `open_questions` above. Question one (clone vs committed fixture)
      and question four (harvest-cycle wiring) are the two that change what gets built.
- [ ] Confirm T06's `unsandboxed: true` rationale is one you accept, and that you are
      comfortable with a real pull request appearing in this repository and being
      closed unmerged in the same run.
- [ ] Check this gate's headline claim against T05's flag-scope table — specifically
      that nothing fires on a schedule.
- [ ] Accept or revise `cost_budget_usd: 29.50`; T06's $8.00 is the unanchored number.
- [ ] Flip the three drafts to `pending` and `GATE-01.md` to `passed`.

## Reflection notes

<Written by the human at review time.>
