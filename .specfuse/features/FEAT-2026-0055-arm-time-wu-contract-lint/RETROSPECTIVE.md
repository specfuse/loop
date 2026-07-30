# RETROSPECTIVE — FEAT-2026-0055, arm-time WU contract lint

**Verdict: `met_locally`.**

Attempt 1 of this close returned `not_met`: the ERROR leg — `check_produces_boundary`, the
reason this feature exists — was blind to the `**Do not touch.**` bold-preamble form that all
327 work-unit bodies in this repo use, so the motivating deadlock armed clean, while the
continuation lines the extractor *could* see produced 15 false ERRORs across 4 existing
features. T05 was chartered on that finding and has landed.

This close re-ran every oracle and re-executed every rule against fixtures built fresh in this
session. **The finding is fixed.** The deadlock fixture in the canonical body form now ERRORs
and names the guard it preempts; the tree-wide sweep reports **zero ERRORs across 43 feature
folders**, down from 15; the four features that false-ERRORed are clean, with four genuinely
ambiguous boundary matches correctly degraded to advisory WARNs rather than guessed at.

The verdict is `met_locally` rather than `met` for two reasons, both recorded with exact upgrade
conditions in §6: the portfolio success measure is a measurement over a future feature's event
log and cannot be taken here, and the consumer-visible contract changes in §8 are recorded
**awaiting an operator's acknowledgment**, which is a human act this session cannot perform for
them.

---

## Oracles re-run fresh (§1, close-discipline §1)

Every command below was run in this close session against the working tree. Exit codes read
directly from the shell; no work unit's self-report was inherited, including T05's.

| Oracle | Command | Exit | Observed |
|---|---|---|---|
| tests | `python3 -m unittest discover -s tests -v` | **0** | `Ran 1903 tests in 64.451s` / `OK (skipped=3)` |
| lint | `ruff check specfuse .specfuse/scripts tests scripts` | **0** | `All checks passed!` |
| security | `bandit -r specfuse .specfuse/scripts -ll` | **0** | `No issues identified.` (89 low, 0 medium, 0 high) |
| coverage | `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90` | **0** | `Ran 1903 tests` / `OK` / `TOTAL 5617 371 93%` |

### Two environment artifacts, recorded so the next close does not re-diagnose them

Both cost this session a re-run, and neither is a defect in the tree.

1. **The sandbox breaks signed commits in throwaway repos.** The first suite run exited 1 with
   11 errors, every one of them
   `subprocess.CalledProcessError: Command '['git', '-C', '/tmp/…', 'commit', …]' returned
   non-zero exit status 128`. The operator's git config sets `gpg.format=ssh` and
   `commit.gpgsign=true`; the sandbox blocks the ssh-agent socket, so every test that scaffolds
   a temp git repo and commits into it fails. Re-run with the sandbox disabled, the identical
   command exits 0. This reproduces attempt 1's note exactly.
2. **A leaked working directory silently changes the test count.** A second run exited 1 with 6
   errors — `FileNotFoundError: 'pyproject.toml'`, `'specfuse/monitor/cli.py'`, and
   `git branch --show-current` exit 128 — because an earlier `cd` into the fixture directory
   persisted in the shell. Several tests resolve paths relative to cwd, and unittest discovery
   itself dropped modules it could not import, so the suite reported `Ran 1885 tests` instead of
   1903 while still printing a plausible-looking failure list. **A differing total-test count
   between two runs of the same suite is the tell**; the authoritative run above was launched
   with an explicit `cd` to the repo root.

## End-to-end fixture execution — fresh, this session (§2)

Each rule was executed against a fixture built this session under the session temp directory and
run through the real `specfuse-lint` entry point, or through the real `loop` module functions.
No behavior below is argued from reading source. Fixtures carry the full pending-WU section set,
so the produces-class finding is the only issue each one reports.

### 2a. Deadlock fixture (T02's ERROR rule, T05's fix) — **passes** (attempt 1: failed)

Fixture: a `pending` WU declaring `produces: src/main/java/Reconciler.java` whose Do-not-touch
section forbids `src/main/**`, written in the canonical body form the shipped template
prescribes — the exact FEAT-2026-0066/T04 shape and the exact text that exited 0 in attempt 1:

```markdown
**Do not touch.** `src/main/**` (T03 owns it); other features' folders; `.git/`.
```

Result — `specfuse-lint $TMPDIR/fx/fx-deadlock`:

```
FAIL — 1 issue(s) in /tmp/…/fx-deadlock:
  - ERROR: WU-04-deadlock.md: FEAT-2026-0099/T04 declares produces path
    'src/main/java/Reconciler.java', which its own Do-not-touch section forbids via
    'src/main/**'. This is a structural deadlock — assert_produces_in_diff would refuse it
    after a full dispatch attempt. Drop the path from produces, narrow the Do-not-touch
    pattern, or add an explicit 'except' carve-out. See FEAT-2026-0066/T04, FEAT-2026-0070.
LINT_EXIT=1
```

The rule fires on the bold-preamble form, exits non-zero, and names `assert_produces_in_diff` —
the post-attempt guard it preempts, as the FEAT-2026-0070 rule requires. This is the criterion
attempt 1 recorded as `LINT_EXIT=0` / no ERROR.

### 2b. Delivered-path fixture (T01's WARN rule) — **passes**

Fixture: a `done` WU declaring `produces: src/main/resources/reconcileListProperty.mustache` and
a `pending` WU re-declaring the same path.

```
WARN: WU-04-redeclares.md: FEAT-2026-0098/T04 declares produces path
'src/main/resources/reconcileListProperty.mustache', but done WU FEAT-2026-0098/T03
(WU-03-delivers.md) already delivered it. Drop the path, or state the incremental edit
this WU makes to it in the body.
OK — /tmp/…/fx-delivered is structurally valid.
LINT_EXIT=0
```

Both WUs named, the authoring response stated, WARN-only (exit 0) as specified. This is where
the WARN rule is verified: the gate's own text notes the T01/T02 self-WARN is unobservable at
close time, and directs the check here instead.

### 2c. Unified literal/glob semantics (T03) — **passes**

A dispatch-shaped fixture repo with a real WU file loaded through `loop.load_wu`, real non-empty
files on disk, and a `git diff --name-only`-shaped touched list. Both guards called with the
same `WorkUnit`, cwd at the fixture repo root:

```
loaded WU produces = ['src/main/resources/*.mustache']
assert_declared_deliverables: (True, '')
assert_produces_in_diff:     (True, '')
```

One declaration form, both gates. Negative observations (each rule seen refusing a purpose-built
bad input, per verification-discipline §3):

```
NEG glob-no-match declared: (False, 'declared deliverable glob matched no existing non-empty
                                     file: src/main/resources/*.java')
NEG glob-no-match in-diff:  (False, "declared produces path(s) not in this WU's squash diff:
                                     src/main/resources/*.java")
NEG directory:              (False, 'declared deliverable is a directory: src/main/resources —
                                     directories are not valid produces: entries under the
                                     unified literal/glob contract …')
NEG literal-untouched:      (False, "declared produces path(s) not in this WU's squash diff:
                                     src/main/resources/pojo.mustache")
```

The glob requires ≥1 existing match on both sides; a declared-but-untouched literal is caught by
the diff gate; the directory form is refused with a message naming the unified contract rather
than silently passing one gate and failing the other.

### 2d. Prose handoff (T04) — **passes**

`grep "passes presence and fails diff" .specfuse/templates/WU.template.md` returns nothing; the
template, `arm-gate`, and `authoring-work-units` point at `specfuse-lint`. Attempt 1 accepted
this prose as accurate about T01 and T03 but flagged it as over-promising on the boundary check.
With §2a and §3 now green, the prose describes behavior the lint actually has, and the caveat
attempt 1 attached to §8.4 is discharged.

## Satisfiability sweep (§3) — **passes**; attempt 1 reported 15 ERRORs

`specfuse-lint` over every feature folder in this repo. The gate requires zero ERROR findings.

```
=== SWEEP: features=43  features_with_ERROR=0  crashes=1  produces_class_WARN_features=2
```

**43 feature folders, zero ERROR findings.** The four features that false-ERRORed in attempt 1
are individually clean:

| Feature | ERRORs, attempt 1 | ERRORs, now |
|---|---|---|
| `FEAT-2026-0023-lifecycle-integration-test` | 3 | **0** |
| `FEAT-2026-0024-hashed-denylist-leak-guard` | 7 | **0** |
| `FEAT-2026-0069-monitoring-check-targets` | 3 | **0** |
| `FEAT-2026-0070-terminal-flip-contract` | 2 | **0** |

**Expected WARNs, enumerated.** Four produces-class WARNs fire tree-wide, across two features.
All four are the boundary rule's deliberate degradation — T05's "ERROR only on certainty" design
— where a `produces:` path does match a Do-not-touch pattern but the boundary's wording makes
its scope ambiguous without semantic judgment the lint does not have:

| Feature / WU | Produces path | Matching pattern |
|---|---|---|
| `FEAT-2026-0069/T03` | `tests/test_derive_monitoring_discovery.py` | `tests/test_derive_monitoring_discovery.py` |
| `FEAT-2026-0069/T08` | `.specfuse/skills/derive-monitoring/SKILL.md` | `.specfuse/skills/derive-monitoring/*` |
| `FEAT-2026-0069/T08` | `.specfuse/skills/derive-monitoring/PROMPT.md` | `.specfuse/skills/derive-monitoring/*` |
| `FEAT-2026-0070/T03` | `.specfuse/skills/accept-hedged-close/SKILL.md` | `.specfuse/skills/accept-hedged-close/SKILL.md` |

Each ends `Confirm by hand before arming, or reword the boundary to name the protected surface
unambiguously.` These are advisory and do not change any exit code. Both features are `done`, so
nothing is gated on them; the WARNs are exactly the arm-time signal the rule exists to give, on
WUs that would have been worth a second look at arm time.

The gate's own text records that WARNs fire on dispatchable WUs only and that a feature whose
WUs are all `done` produces none of the *satisfiability* WARN by design — that class does not
appear in this sweep, and is verified on the fresh 2b fixture instead.

**One folder the lint cannot evaluate, pre-existing and unrelated.**
`FEAT-2026-0020-public-readiness-prep` exits 1 with
`MiniYAMLError: line 14: not a 'key: value' line — got '<!--'` — an HTML comment inside a WU's
frontmatter, raised from `specfuse/loop/_miniyaml.py`, code this feature did not touch. It
contributes zero ERROR findings because the lint never gets far enough to produce any. Recorded
here so it is not rediscovered as this feature's doing; it is a separate defect and remains
open.

## This feature's own lint status (§4)

```
specfuse-lint .specfuse/features/FEAT-2026-0055-arm-time-wu-contract-lint
OK — … is structurally valid.
SELF_EXIT=0
```

Attempt 1 flagged this as weak evidence, since this feature's WU bodies all use the bold form
the boundary check was then blind to. That caveat is now discharged: per §2a the check reads the
bold form, so exit 0 here means the check inspected these five bodies and found no deadlock.

## Cost analysis (§5)

Two planned figures exist and both are reconciled. The gate was drafted at **$22.00** (T01–T04
plus a $5.00 close); T05 was chartered mid-gate on attempt 1's `not_met`, raising `PLAN.md`
`planned_cost_usd` to **$27.00** against a `GATE-01.md` `cost_budget_usd` of $32.00. Actuals are
from `events.jsonl` `attempt_outcome` payloads.

| WU | Planned | Actual | Attempts | Delta |
|---|---|---|---|---|
| T01 produces-satisfiability WARN | $5.00 | $1.132481 | 1 | −$3.87 |
| T02 boundary-consistency ERROR | $4.00 | $1.374473 | 1 | −$2.63 |
| T03 unify produces semantics | $5.00 | $1.037655 | 1 | −$3.96 |
| T04 surfacing + folklore deletion | $3.00 | $0.675363 | 1 | −$2.32 |
| **Original implementation subtotal** | **$17.00** | **$4.219972** | 4 | **−$12.78 (−75%)** |
| T05 boundary-extraction fix (unplanned at draft) | $5.00 | $5.664788 | 1 | +$0.66 (+13%) |
| G1-CLOSE attempt 1 (`not_met`) | — | $5.417419 | 1 | rework |
| G1-CLOSE attempt 2 (this session) | $5.00 | recorded by the driver at `task_completed` | 1 | — |
| **Feature total** | **$27.00** (draft: $22.00) | **$15.302179 + this close** | | under budget |

**Delta named.** The headline number is favourable and the shape underneath it is not. The four
originally-planned implementation WUs came in at **25% of estimate**, uniformly (−72% to −79%
each) — a systematic over-estimate for "add a `check_*` function plus fixture tests to an
existing lint module", not four independent lucky runs. But the feature did not finish at $4.22:
it finished at **$15.30 plus this close**, because the money moved from where it was budgeted to
where it was not. T05 ($5.66) and the discarded first close ($5.42) are **$11.08 of pure
rework** — 72% of everything spent so far — and neither existed in the plan.

The under-run was therefore the warning, not the win. Four first-attempt passes on a feature
whose entire subject is *rules that must actually fire* is precisely the shape where the gates
are measuring the wrong thing: every fixture was authored in the ATX form the rule could see, so
the suite was green and the rule was inert on the real corpus. The cheap implementation and the
expensive rework are the same fact observed twice.

Estimating note for the next feature of this class: T05 — the WU that fixed a known, localised
defect with its fixture set already enumerated in a retrospective — landed within 13% of its
$5.00 estimate, while the four exploratory WUs missed by 75%. Well-specified repair work
estimates well; "add a new rule to an existing module" is currently over-estimated by ~4×.

### Failure-class breakdown

All six `attempt_outcome` events in `events.jsonl` carry `"outcome": "passed"`,
`"failure_class": null`, `"failure_signature": null`, and `re_arm_count: 0`. **Zero non-passing
attempts, and the number is misleading.** The close attempt that returned `not_met` is recorded
as a `passed` attempt: the driver's verification gates passed on it, and the verdict is a
separate field. So $11.08 of rework — a whole extra implementation WU and a discarded close —
is invisible to any analysis that groups by `failure_class`. There is no failure class to break
down precisely because the defect was caught by a close's judgment rather than by a gate. See §9
for the promoted lesson.

## What the loop did NOT verify (§6)

1. **Portfolio measure — zero produces-class refusals downstream.** *Criterion (PLAN.md
   Notes, verbatim):* "Portfolio success measure (verified downstream, not here):
   `produces_not_in_diff` / `no_deliverable_files` / `deliverable_missing` attempts at zero on
   the next generator-class feature run under a driver carrying this feature."
   *Why unverifiable here:* it is a measurement over a future feature's `events.jsonl`; no such
   run exists.
   *Exact re-run condition:* after the next generator-class feature completes gate 1 under a
   driver carrying this branch, grep that feature's `events.jsonl` for `failure_class` in
   {`produces_not_in_diff`, `no_deliverable_files`, `deliverable_missing`}; zero occurrences
   upgrades this entry. Unlike attempt 1, this measure is now **meaningful for the boundary
   class** — §2a and §3 show the ERROR rule firing on real WU body shapes, so a zero count
   would be evidence rather than an artifact of a dead rule.

2. **Operator acknowledgment of the consumer-visible contract changes.** *Criterion (this WU,
   verbatim):* "Consumer-visible contract changes enumerated, blocked on operator
   acknowledgment (§3): the widened `assert_declared_deliverables` semantics (T03), the template
   `produces` note, and the skill-prose changes. Not `n/a`."
   *Why unverifiable here:* the enumeration is complete in §8 and is verified. The
   acknowledgment is a human act on changes that reach every consumer of the scaffold, and per
   `operator-escalation.md` an agent that drafts the human's own acknowledgment has removed the
   signature it was collecting. This session cannot supply it.
   *Exact re-run condition:* an operator reads §8 and acknowledges the five changes — via
   `/accept-hedged-close` on this feature, which records their reason and re-checks the verdict
   through the driver's `--recheck-verdict` primitive. That upgrades this entry and, with entry
   1 still outstanding, is the intended path from `met_locally` to a terminal close.

Two entries against 10 acceptance criteria (20%) — under both the ">2 entries" and the ">30% of
criteria" thresholds, so single-gate sizing is **not** flagged on this axis. §7 says what should
change anyway, and note that entry 2 is structural to any feature with consumer-visible surface
rather than a symptom of this gate's size.

## What I'd change (§7)

- **Test the shape the template actually ships.** T02's fixtures were authored with
  `## Do not touch` ATX headings while every real WU — and the template T04 edits in the same
  gate — uses `**Do not touch.**`. The suite was green and the rule was inert. A rule whose
  input is a document shape must have at least one fixture copied verbatim from the shipped
  template, not hand-written in a shape that happens to parse. *(Promoted, §9.)*
- **Require the motivating case as a fixture, by construction.** This feature was chartered on
  one concrete incident (FEAT-2026-0066/T04). Reproducing that incident's *actual body text* as
  a fixture and asserting the rule fires would have failed T02 immediately. "Fixture tests
  cover: the T04 shape" was in T02's acceptance criteria and was satisfied by a paraphrase of
  the shape, not the shape. *(Promoted, §9.)*
- **Make the sweep an implementation-WU gate, not a close-time criterion.** T02's own acceptance
  criteria required the zero-ERROR sweep and said "Any ERROR on an existing feature → stop,
  escalate". T02 reported `passed`. Whatever T02 ran, it was not the sweep. The sweep is a
  one-line command with a countable output and belongs in `verification.yml` as a gate the
  driver executes, where an agent's self-report cannot stand in for it. **Still not done** —
  T05 re-ran the sweep as a WU criterion and this close re-ran it again, both as self-reported
  observations. This remains the single highest-value follow-up from the feature. *(Promoted,
  §9.)*
- **Do not write close-time criteria that depend on mid-dispatch state.** Attempt 1's "T01/T02
  overlap WARN must appear in the sweep" criterion was unsatisfiable the moment T02 flipped to
  `done`. This close's WU corrected it — verify the WARN rule on a fresh fixture, do not require
  it in the sweep — and the corrected form was satisfiable and satisfied (§2b). Worth noting as
  the working example: the fix for an impossible criterion is to relocate the observation to a
  surface that still exists at the time the criterion is read.
- **A `not_met` close should not be silent in cost analysis.** The rework this feature paid for
  is invisible in the failure-class breakdown because a close whose gates pass but whose verdict
  is `not_met` is recorded as `outcome: passed`. Any portfolio-level cost analysis that groups
  by failure class will under-count this shape systematically. *(Promoted, §9.)*

## Consumer-visible contract changes (§8) — awaiting operator acknowledgment

These reach every consumer of the scaffold, not only this repo. **Not `n/a`.** This list is
recorded for a human to acknowledge; the terminal flips stay withheld until then. Attempt 1's
list is carried forward with its statuses corrected against this session's evidence.

1. **`assert_declared_deliverables` accepts globs (T03, `specfuse/loop/loop.py`).** Previously
   literal-path existence only. Now a `produces:` entry containing `*`, `?`, or `[` is satisfied
   by ≥1 existing non-empty match. **Widening** — every previously-passing declaration still
   passes. Consumer impact: WU authors on any Specfuse project may now declare glob deliverables
   that satisfy both gates.
2. **Directory `produces:` entries are now refused outright (T03).** Previously a directory
   silently passed the presence gate and then failed `assert_produces_in_diff` at squash time.
   Now it is refused with a message naming the unified contract. **Behavior change, not a pure
   widening**: a WU that declared a directory previously reached the diff gate and failed there;
   it now fails earlier with a different message. Any downstream project with a directory in a
   `produces:` list sees a new refusal text.
3. **`WU.template.md` `produces` note rewritten (T04, `.specfuse/templates/`, mirrored to
   `specfuse/loop/data/templates/`).** The literal-vs-glob warning block is deleted and replaced
   by a one-line statement of the unified contract. Every project that scaffolds a WU from the
   template gets the new text; projects that copied the old warning into existing WUs keep stale
   prose that is now wrong in the direction of being over-cautious.
4. **Skill prose (T04, `plugins/specfuse/skills/`, mirrored to `.specfuse/skills/`).**
   `authoring-work-units` now points at `specfuse-lint`'s satisfiability/boundary checks as the
   arm-time verification; `arm-gate` step 3 gains a "run `specfuse-lint` before walking drafts"
   line. **Attempt 1's caveat is withdrawn.** It warned that the prose promised a boundary check
   that was blind and noisy; §2a and §3 show the check now fires on the real body shape with
   zero false ERRORs tree-wide, so the prose describes behavior the tool has.
5. **New lint findings (T01, T02, T05, `specfuse/loop/lint_plan.py`, `_wu_sections.py`).**
   `specfuse-lint` gains a WARN class and an ERROR class, and the shared section slicer
   `slice_wu_section` now returns label-line content for the bold-preamble form. **Two effects
   an operator should weigh separately.** *(a)* The ERROR class changes `specfuse-lint`'s exit
   code to 1 on a feature carrying a genuine deadlock — any consumer CI running `specfuse-lint`
   in a blocking position will start failing on such features. Attempt 1 flagged this as
   dangerous because of 15 false positives; that count is now zero across 43 features (§3), so
   the exit-code change is believed safe, but it is still an exit-code change on a tool
   consumers may run in CI. *(b)* `slice_wu_section` is shared. Its behavior changed for the
   bold-preamble form, so any other caller of that helper now sees label-line content it did not
   see before. The full suite is green (§1), which is the evidence that no existing caller
   regressed.

## Lessons (§9)

Promoted to `.specfuse/LEARNINGS.md` — two entries from attempt 1 (document-shape fixtures; the
self-reported cross-corpus sweep), plus two from this attempt (degrade-to-WARN over guessing;
`not_met` closes are invisible to failure-class analysis). Not `nothing generalizes`.

## Recommended disposition (§10)

Accept the hedged close. The defect attempt 1 found is fixed and re-verified from scratch rather
than inherited: the ERROR leg fires on the canonical body form, the sweep is at zero across 43
features, and the four previously-false-ERRORing features are clean with their genuinely
ambiguous cases degraded to advisory WARNs. Both open items in §6 are structural rather than
unfinished work — one is a measurement over a run that has not happened, the other is an
operator signature this session is forbidden to forge.

The path forward is `/accept-hedged-close` on this feature, which collects the operator's own
acknowledgment of §8 and re-checks the verdict through the driver. The one follow-up worth
scheduling as real work is §7's third bullet: promote the tree-wide sweep from a criterion an
agent reports to a gate the driver runs.
