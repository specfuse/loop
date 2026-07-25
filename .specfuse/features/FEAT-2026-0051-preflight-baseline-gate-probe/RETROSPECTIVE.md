<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# RETROSPECTIVE — FEAT-2026-0051, pre-flight baseline gate probe

Single-gate feature: three substantive WUs (T01 probe + halt, T02 persistence +
kill-switch, T03 message + evidence) plus this terminal close. Written by
`FEAT-2026-0051/G1-CLOSE`.

## Oracles re-run fresh (close-discipline §1)

Every command below ran **in this close session**, exit code read directly —
nothing inherited from T01/T02/T03's self-report.

| oracle | command | observed |
|--------|---------|----------|
| suite | `python3 -m unittest discover -s tests -q` | `Ran 1327 tests in 52.387s` / `OK (skipped=3)`, exit `0` |
| symbols | `python3 -c "from specfuse.loop.loop import probe_baseline, read_gate_baseline, write_gate_baseline, baseline_probe_enabled, format_preexisting_gate_failure, baseline_evidence_diffstat"` | exit `0` |
| full `code` set | all nine gates from `.specfuse/verification.yml`, run individually | every gate exit `0` (table below) |

The suite's summary goes to stderr and interleaves with an integration test's
own stdout; the run above separated the streams so the `OK` line is read, not
inferred.

### The full `code` set, timed (this is also the probe-cost measurement)

| gate | command | exit | wall-clock |
|---|---|---|---|
| tests | `python3 -m unittest discover -s tests -v` | 0 | 54.9s |
| lint | `ruff check specfuse .specfuse/scripts tests scripts` | 0 | 0.1s |
| security | `bandit -r specfuse .specfuse/scripts -ll` | 0 | 0.5s |
| coverage | `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90` | 0 | 54.7s (`TOTAL 3661 223 94%`) |
| leak-scan | `python3 .specfuse/scripts/leak_scan.py --all` | 0 | 4.5s |
| leak-scan-hook | `bats tests/leak_scan_hook.bats` | 0 | 1.0s |
| sync-scaffold-bats | `bats tests/sync_scaffold.bats` | 0 | 1.4s |
| init-sh-shim-bats | `bats tests/init_sh_shim.bats` | 0 | 1.0s |
| init-skills-bats | `bats tests/init_skills_idempotent.bats` | 0 | 0.2s |
| **total** | | **all 0** | **118.3s** |

Three bats suites first failed under the session sandbox with
`mktemp: mkdtemp failed ... Operation not permitted` — an environment
restriction on temp-dir creation, not a gate failure. Re-run without the
sandbox they pass; the exits above are the un-sandboxed runs.

## Gate 1

### T01 — probe + pre-dispatch halt (`WU-01-baseline-probe-halt.md`)

`probe_baseline()` runs the `code` set through the same `_run_gate_set()` that
`verify()` uses (factored, not copied — the subprocess hang defenses stayed put)
and returns the failing subset. The halt fires at gate entry,
`loop.py:4437-4470`, before the `while True` frontier loop — so it is
structurally impossible for it to run after a WU has been dispatched.

### T02 — persistence, re-probe policy, kill-switch (`WU-02-...`)

`baseline:` is written into gate frontmatter through `write_frontmatter_block`,
the same no-reflow writer scalar gate keys use. Re-probe policy: skip when
`baseline.sha == head_sha`, re-probe otherwise, nothing else invalidates.
`baseline_probe_enabled()` resolves CLI-flag > config-key > default-enabled in
one place.

### T03 — operator-legible message (`WU-03-...`)

`format_preexisting_gate_failure()` renders prose, not a stdout dump, and
attaches `baseline_evidence_diffstat()` — resolved through `resolve_base`
(FEAT-2026-0031's mechanism), never a hardcoded `main`.

## End-to-end proofs, run fresh in this session

These are **not** T01/T02/T03's unit tests. A scratch harness
(`e2e_baseline_proof.py`, written outside the repo) stands up a real temp git
repo via the existing `integration_workspace()` fixture, configures a genuinely
failing `code` gate (a command that really exits 1), and invokes the real
`loop.run()`. The probe itself is never stubbed. Only two things are
substituted, neither of them the thing under test: `loop.dispatch` becomes a
**counter**, so "zero work units dispatched" is measured rather than assumed;
and `loop.verify` returns True so the green scenario's WUs finish (the probe
calls `_run_gate_set` directly, not `verify()`, so this cannot mask a probe
run). For the kill-switch scenario `loop.probe_baseline` is wrapped in a
*delegating* counter, so "zero probe runs" is likewise a measurement.

### Red baseline — the brake fires

| measurement | observed |
|---|---|
| `run()` returned | `1` |
| **work units dispatched** | **0** |
| probe runs | 1 |
| `human_escalation` events | 1, `reason: 'preexisting_gate_failure'`, `gate: 1` |
| event payload carries rendered message | yes |
| gate frontmatter after halt | `status: awaiting_review` + `baseline:` block recorded |

Gate file after the halt:

```yaml
gate: 1
status: awaiting_review
baseline:
  sha: ac4b045d72d30b54ebb5034d8f869c233638f60d
  probed_at: 2026-07-25T19:43:30.304258+00:00
  failing:
    - gate: dependency-audit
      failure_class: other
      failure_signature: no_gate_marker
```

The message the operator actually sees, verbatim from stdout — this is the
feature's real deliverable:

```
Gate 1 is blocked: the automated checks it depends on were already failing before this feature touched any file.

Failing check(s) found at gate entry:
  - dependency-audit: other (signature: no_gate_marker)

No work unit caused this failure: the checks were run once, before any work unit was dispatched, and this is what they found. Zero work units were dispatched for this gate.

Proof the feature's tree matches its integration branch (so the failure predates this feature):
git diff main...HEAD --stat: (no differences from 'main')

What to do next:
  1. Fix the failing check(s) on the integration branch — typically with /fix-bug — so this feature's branch inherits the fix on rebase.
  2. Or defer this feature until the integration branch is green.

There is no way to proceed past this halt in this version. A waiver that lets a feature continue against a red baseline is future work tracked as FEAT-2026-0052; it does not exist yet.
```

Judged against the criterion "a human should read it once before this ships":
it names the gate, states the two facts that cost the original operator hours
(no WU caused it; zero were dispatched), carries the base-vs-head proof, offers
only options that exist, and names FEAT-2026-0052 as future work rather than an
available action. One weak line is flagged under *What I'd change*.

**No disagreement with T01's unit tests.** The escalation trigger for this WU
was a brake that passes its own tests but does not stop a real dispatch. The
real dispatch counter read `0`. The brake is not hollow.

### Green baseline — the brake does nothing (escalation-predicate check, PLAN.md §2)

| measurement | green (probe on) | kill-switch (probe off ≡ pre-feature behavior) |
|---|---|---|
| `run()` returned | `0` | `0` |
| work units dispatched | 6 | 6 |
| probe runs | 1 | **0** |
| `human_escalation` events | 0 | 0 |
| gate status after run | `passed` | `passed` |
| `baseline:` in gate file | `failing: []` | **absent** (nothing recorded) |

Run side by side, probe-on-green and probe-disabled are **identical in every
dispatch-visible respect**. The only difference is the `baseline:` record. That
is the escalation-predicate claim — "on a green base tree dispatch proceeds
byte-identically to today" — verified as an A/B at close, not just asserted.

### Kill-switch — zero probe runs

`no_baseline_probe=True` with a red gate still configured: `probe_baseline` was
invoked **0 times**, all 6 WUs dispatched, `run()` returned `0`, and the gate
file carries no `baseline:` key (existing records are left untouched, not
cleared — matching T02's flag-scope table). The switch disables the probe and
nothing else; `verify()` remains every WU's exit oracle.

Config-key precedence, exercised directly:

| `--no-baseline-probe` | `verification.yml` | `baseline_probe_enabled()` |
|---|---|---|
| false | `{}` | `True` (default) |
| false | `baseline_probe: false` | `False` |
| false | `baseline_probe: true` | `True` |
| **true** | `baseline_probe: true` | **`False`** (CLI wins) |
| true | `{}` | `False` |

### Resume-skip policy — measured directly

The policy never fired in production during this feature (see *Retrospective*
below), so it was measured here against the real `gate_baseline_check` with a
real gate file and a delegating, counting `probe_baseline`:

| entry | sha | probe runs (cumulative) | `freshly_probed` |
|---|---|---|---|
| 1 | A | 1 | `True` |
| 2 | A (unchanged) | **1** | `False` |
| 3 | B (moved) | 2 | `True` |
| 4 | half-written `baseline:` block | 3 | `True` |

A second entry at an unchanged sha costs **zero** gate runs and still returns
the green record `[]` — distinguishable from never-probed. A moved sha
re-probes. A malformed block reads as `None` and re-probes rather than crashing.
`cost_budget_usd: 32.00` survived all three writes byte-identically, confirming
the no-reflow writer.

### Degraded-evidence path

`baseline_evidence_diffstat({"base": "no/such/ref"})` returns `None` (never
raises), and the rendered message still halts at 1018 characters carrying the
explicit `base-tree comparison unavailable` line. Evidence collection cannot
become the reason a halt fails to fire.

## Retrospective

**Did the probe fire on this repo's own gates during the feature? No — and the
PLAN's self-hosting note was wrong about why it would.** PLAN.md's Notes
predicted that "from T01 onward the driver dispatching this feature's own
remaining WUs executes the probe code T01 just wrote." It did not, and could
not. Two independent reasons:

1. Python loads `loop.py` once at process start. `events.jsonl` shows one
   continuous driver process — T02 started 0.017s after T01 completed, T03
   0.018s after T02, this close 0.019s after T03 — so every WU ran against the
   `loop.py` that existed at 19:07:08, before T01 wrote a line.
2. The probe fires at **gate entry**, before the frontier loop. Gate 1's entry
   happened once, at the start of the run. Even a hot-reloading driver would
   have passed that point already.

The observable confirmation: `GATE-01.md` carries no `baseline:` key, and
`events.jsonl` carries no `human_escalation`. A green probe *writes*
`failing: []`, so an absent key is positive evidence the probe never ran here.

This is benign — the hazard the note worried about never materialized — but it
means the self-hosting case is **not** evidence for the feature, and the
`--no-baseline-probe` recovery path was never needed. The first real self-hosted
probe will happen on the next driver invocation against this repo, which will
load the new `loop.py` at process start and probe gate entry for whatever
feature runs next.

**What one probe run costs.** 118.3s against this repo's `code` set, measured
above. It is 92.6% two gates: `tests` (54.9s) and `coverage` (54.7s), which are
the same 1327-test suite run twice — once bare, once under `coverage`. The
other seven gates together cost 8.7s.

**Does that change the once-per-gate-entry decision? No.** Three ways of sizing
it, all pointing the same direction:

- Against this gate's own dispatch wall-clock — 1782.9s of agent time across
  T01/T02/T03 — one probe is **6.6%**, paid once.
- On resume it is **0s**. The re-probe policy makes repeated entries at an
  unchanged sha free, and the driver is resumed constantly.
- The probe spends **no model tokens at all**. It runs gate commands, dispatches
  no agent, and bills nothing. Its price is CPU-seconds; what it prevents is
  *billed* model time — the downstream incident PLAN.md cites burned ~$8 across
  two WUs against a failure neither could fix.

118 CPU-seconds against a full attempt budget of billed agent sessions is not a
close call, so the escalation trigger about probe cost changing the design
decision did **not** fire.

**Did the resume-skip policy behave? Yes, but only under direct measurement**
(table above) — never in production, because the probe never ran in production.

**Cost discipline held.** All three implementation WUs passed on attempt 1 with
zero blocks, zero re-arms, and no spinning. The serialized T01→T02→T03 chain
(all three edit the same escalation site) produced no merge friction.

## What I'd change

1. **The failure-signature line is the message's weakest sentence.** The red
   proof rendered `- dependency-audit: other (signature: no_gate_marker)`.
   `no_gate_marker` is `parse_gate_failure_signature`'s honest sentinel for
   output carrying no recognizable marker — pre-existing behavior (commit
   `0517507`, predating this feature), not something T01–T03 introduced. But
   this feature is the first surface that shows that sentinel **to a non-expert
   operator**, and "signature: no_gate_marker" is precisely the bare internal
   symbol T03's own criteria said not to lead with. The fix is small and the
   predicate already exists: `_is_noninformative_signature()` (`loop.py:690`)
   already knows when a signature carries no content. When it does, the message
   should say so in plain English — "this check produced no recognizable
   failure marker; see the gate's own output" — instead of printing the
   sentinel. Recorded as a follow-up, not fixed here (this WU writes only its
   close record).

2. **The probe pays for the same test suite twice.** 92.6% of probe cost is
   `tests` + `coverage` running the same 1327 tests. A probe that ran only the
   coverage gate would measure the same suite plus the floor at roughly half the
   wall-clock — but it would silently narrow *what is probed*, which is the
   wrong trade for a brake. The honest version is a per-project note that probe
   cost is dominated by whichever gates duplicate work, and that this is a
   `verification.yml` authoring concern, not a driver one. FEAT-2026-0052 should
   size the ratchet against this number rather than re-deriving it.

3. **Self-hosting notes should reason about process start, not file mtime.**
   The PLAN's hazard note was written as if editing `loop.py` changes the
   running driver's behavior. It does not. Any future feature that modifies
   driver control flow should state the hazard as "takes effect on the *next*
   driver invocation," which is both accurate and a different (smaller) risk.

## Lessons

Promoted to `.specfuse/LEARNINGS.md` (three entries):

1. **"Probe the oracle before trusting it as an oracle" generalizes well beyond
   gate sets — yes.** The invariant is not about gates; it is about any exit
   oracle whose verdict can change without the repo changing. Dependency audits
   are canonical, but the same shape covers a linter release adding a rule, a
   compiler bump, a license scanner, a network-dependent fixture, and any
   acceptance criterion asserting on a regenerated artifact. Wherever an oracle
   is externally fed, measure it once against the *unchanged base tree* before
   attributing any failure to a work unit. This is the executable form of the
   existing `[FEAT-2026-0007/G1-LESSONS]` family — those said "don't make a
   tool's own report the acceptance oracle"; this one says what to do instead
   when you have no choice but to depend on one.

2. **The measured probe cost does not change the once-per-gate-entry
   decision**, and the number is worth recording so 0052 does not re-derive it:
   118s, 93% of it duplicated test execution, 0 model tokens, 0s on resume.

3. **A driver change to dispatch control flow does not take effect for the run
   that writes it.** Worth a rule because it cuts both ways: it defuses
   self-hosting *hazards*, and it also invalidates self-hosting as *evidence*.

## Docs

**No doc was touched by this WU** — its Do-not-touch scopes it to its own close
record.

The criterion asked whether `docs/methodology.md` needs `preexisting_gate_failure`
documented "alongside the other escalation reasons." **The premise does not
hold:** `docs/` documents no escalation reason strings at all. Grepping
`gate_budget_exceeded`, `spinning_signature_repeat`, `agent_reported_blocked`,
and `human_escalation` across `docs/` returns zero hits, while `loop.py` emits
eight distinct reasons. There is no list for this one to join.

Two genuine doc gaps found instead, both recorded as follow-ups:

1. **`docs/methodology.md` §6 "The gate cycle"** (lines 234–256) numbers the
   cycle Plan → Execute → Close → Review-and-arm. The probe inserts a step
   *before* Execute: a gate can now terminate at entry having dispatched
   nothing, which §6's four steps cannot currently express. That is the right
   place for this halt, and it is a structural gap rather than a missing enum
   value.
2. **`.specfuse/verification.yml.example`** documents no `baseline_probe` key.
   Downstream projects copy that example; as it stands they get no signal the
   project-level opt-out exists.

## Cost analysis

| | planned | actual | delta |
|---|---|---|---|
| T01 | $6.00 | $1.830919 | −$4.169 |
| T02 | $5.00 | $3.753671 | −$1.246 |
| T03 | $4.00 | $1.576671 | −$2.423 |
| **implementation subtotal** | **$15.00** | **$7.161261** | **−$7.838739 (47.7% of planned)** |
| G1-CLOSE (this WU) | $6.00 | in flight at write time | — |
| **feature total** | **$21.00** | ≥ $7.161261 | — |

`planned_cost_usd` reconciles exactly: PLAN.md declares `21.00`, and the per-WU
sum (6 + 5 + 4 + 6) is `21.00` — no `lint_plan.py` cost-delta WARN. Gate 1's
`cost_budget_usd` is `32.00`, so the per-gate brake had ~$25 of headroom and
never came close to firing.

**Delta named:** the three implementation WUs came in at **47.7% of plan**,
$7.84 under. The cause is legible rather than lucky — each WU passed on attempt
1, so the plan's implicit allowance for retries went unspent. Assuming this
close lands near its $6.00 plan, the feature finishes around $13.2 against
$21.00 (≈37% under). The estimate was conservative in the right direction; a
plan that had budgeted for zero retries would have had no slack when the brake
under construction misbehaved.

Wall-clock for comparison: T01 471.8s, T02 825.3s, T03 485.8s = 1782.9s
(29m43s) for gate 1's implementation work.

## What the loop did NOT verify

1. **The feature's actual value — a real project hitting a genuinely red
   baseline.** *Why:* the red proof above used a synthetic gate command
   (`sys.exit(1)`), which proves the *mechanism* (halt fires, zero dispatched,
   baseline recorded, message renders) but not the *premise* that real
   externally-fed gates go red on unchanged trees. That premise rests on the
   downstream incident PLAN.md cites, which happened before this feature
   existed. *Where it actually happens:* the first downstream project whose
   `code` set goes red between gate entries — the halt either saves an attempt
   budget or it fires on something it should not have.
2. **The probe running against this repo's own real gates, in the driver.**
   *Why:* it never ran during this feature (see *Retrospective*). The 118.3s
   figure is the `code` set timed by hand in this session, which is the same
   commands in the same order but not the same call path. *Where:* the next
   driver invocation against this repo.
3. **Multi-gate re-probe.** PLAN.md's Notes state the probe fires at *every*
   gate's entry, not only gate 1. *Why:* this is a single-gate feature; a second
   gate entry never existed to observe. *Where:* the first multi-gate feature
   run after this lands, or a dedicated test if 0052 needs it sooner.
4. **The `verification.yml` `baseline_probe:` opt-out end-to-end.** *Why:* the
   precedence table above exercises `baseline_probe_enabled()` directly and
   T02's unit test covers the config key, but the CLI flag is the path driven
   through the full `run()` here; the config key was not. *Where:* T02's unit
   test today; a downstream project setting the key permanently.
5. **The halt observed by a human who did not write it.** *Why:* the criterion
   asks that a human read the message once before this ships; this close can
   quote it verbatim but cannot perform the reading. *Where:* the gate review /
   PR review this close hands off to.

## Consumer-visible contract changes (close-discipline §3)

Four additions. All four are additive — nothing is removed or renamed — but all
four are surfaces downstream projects and the scaffold linter observe, so they
are enumerated explicitly rather than dismissed as `n/a`. **This list is
submitted for human acknowledgment at gate review; it is not self-acknowledged.**

| # | surface | change | additive? | evidence |
|---|---|---|---|---|
| 1 | `human_escalation` event payload | new `reason` string `preexisting_gate_failure` (joins 7 existing) | yes — a new value in an existing field; no consumer reading a known reason is affected | red-proof event: `reason: 'preexisting_gate_failure'`, `gate: 1`, `failing_gates`, `message` |
| 2 | gate frontmatter (`GATE-NN.md`) | new `baseline:` block (`sha`, `probed_at`, `failing[]`) | yes — written only by the probe; **verified not to break the scaffold linter** | `lint_plan.py` on a feature whose gate file carries a `baseline:` block → `OK — structurally valid`, exit `0` |
| 3 | driver CLI | new `--no-baseline-probe` flag | yes — opt-in; absent flag preserves default-enabled behavior | precedence table above; kill-switch proof, 0 probe runs |
| 4 | `.specfuse/verification.yml` | new `baseline_probe:` key | yes — absent key reads as `True` (`cfg.get("baseline_probe", True)`), so existing config files are unaffected | precedence table row 1: `cfg={}` → `enabled=True` |

Consumers that observe these: downstream projects reading `events.jsonl`
(reason 1), any tool parsing gate frontmatter (2), operators and CI invoking
the driver (3), and every project's `verification.yml` (4). Surface 2 carried
the only real breakage risk — an unknown key rejected by the linter — and it
was tested rather than assumed.

**Not changed, deliberately:** `verify()`'s `(ok, report)` contract, its
pass/fail semantics, the per-gate cost-budget brake, and spinning detection.
The kill-switch weakens no gate; every WU is still gated on the full `code` set.
This is the row that distinguishes `--no-baseline-probe` from the
`--ignore-security`-style mute flag issue #234 rejected.

## Follow-ups

1. Plain-English rendering when `_is_noninformative_signature()` is true, so
   the operator message never leads with `no_gate_marker` (*What I'd change* 1).
2. `docs/methodology.md` §6 — express a gate that terminates at entry having
   dispatched nothing (*Docs* 1).
3. `.specfuse/verification.yml.example` — document the `baseline_probe:` key
   (*Docs* 2).
4. FEAT-2026-0052 (already planned) — the baseline-delta ratchet and the
   waiver, now designable against the real numbers in this record rather than
   blind, which was the stated reason for the split.

## Terminal verdict — `met`

Every acceptance criterion of this close was satisfied in-session. The six
required sections exist. The oracles were re-run fresh with exit codes read
directly (1327 tests `OK`; the six-symbol import exit `0`; all nine `code`
gates exit `0`). The red-baseline proof ran end-to-end against a real temp repo
and a really-failing gate, with dispatch **measured** at zero and the message
quoted verbatim; it agrees with T01's unit tests rather than contradicting
them, so the hollow-pass escalation trigger did not fire. The green-baseline
no-op was verified as a direct A/B against the probe-disabled path and is
identical in every dispatch-visible respect. The kill-switch produced zero
probe runs. Cost is reconciled with its delta named. The deferred list is
enumerated with why and where — including the entry the WU predicted, that the
probe's value can only be proven downstream. The contract-change list is a real
four-row enumeration, not an `n/a`, with the linter-risk row tested.

The probe-cost escalation trigger also did not fire: 118.3s, 6.6% of this
gate's dispatch wall-clock, 0s on resume, 0 model tokens — which does not
change the once-per-gate-entry decision.

Hence `met` rather than `met_locally`: nothing in this close's own criteria was
left unverifiable in this environment. The five entries under *What the loop
did NOT verify* are downstream-observation and future-gate items, none of which
is this feature's own oracle, and this feature's oracle ran green here.
