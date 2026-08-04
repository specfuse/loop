# Retrospective — FEAT-2026-0034, Roadmap link-integrity lint

Correlation ID `FEAT-2026-0034/G1-CLOSE`. Single terminal gate, so this document is
the feature's whole retrospective.

## Gate 1

### What shipped

| Deliverable | Owner | What it is |
|---|---|---|
| `specfuse/loop/lint_roadmap.py` | T01 | Loads `.specfuse/roadmap.md` + `.specfuse/roadmap-archive.md` as **one** link graph and returns `Finding(severity, file, line, message)` for four invariants plus one WARN. Never raises. |
| `tests/test_lint_roadmap.py` | T01 | 13 tests: the bidirectional-ref case, one per invariant, both uniqueness directions, both orphan-WARN polarities, the non-`blocked` Blocked-by WARN asymmetry, three malformed-input cases, the no-`loop.py`-import assertion, and a real-tree cleanliness assertion. |
| `.specfuse/scripts/roadmap_link_gate.py` | T02 | Thin entry point. Owns exit codes and output shape only. ERROR → exit 1; WARN → printed, exit 0. |
| `tests/test_roadmap_link_gate.py` | T02 | Exit-code split, per-finding output shape, clean-tree summary line. |
| `.specfuse/verification.yml` | T02 | New `roadmap-link-gate` entry in the `code` set, with the WARN-does-not-fail rationale in a comment. |

The four invariants, as built: **blocked-by presence and resolution** (every `blocked`
row's detail section carries a `**Blocked by.**` block with ≥1 resolvable link; the
inverse — a Blocked-by block on a non-`blocked` row — is a WARN, deliberately
asymmetric); **ref resolution in both directions** (each `#feat-…` ref checked against
the anchor set of the file it *names*, bare `#…` same-file, with the correct cross-file
form named in the message because the repair is a prefix rewrite); **anchor adjacency**;
**cross-file ID uniqueness**. Plus a WARN for a `—` Detail cell whose detail section
exists.

### The tree was made clean before the first WU ran — so the red tests are fixtures

This is the single most misreadable fact about this feature, and it is recorded here so
nobody concludes the lint "found nothing because there was never anything to find."

Two live violations existed at drafting time, both produced hours earlier by
FEAT-2026-0041's archive run, and rotting in *opposite* directions from that one run:

```
roadmap-archive.md:53   [FEAT-2026-0074](#feat-2026-0074)         -> anchor lives in roadmap.md
roadmap-archive.md:235  [FEAT-2026-0041](roadmap.md#feat-2026-…)  -> anchor moved INTO the archive
```

They were repaired in a commit **ahead of** this feature, deliberately, so the gate's
"exits 0 on this tree" criterion was satisfiable on arrival rather than red on day one —
the shape that cost FEAT-2026-0060 two blocked attempts. The consequence is that every
red-before test in this feature is driven by a **purpose-built two-file fixture**, not by
live rot. That is the correct trade, but it means the suite's green does not by itself
prove the checker fires on real archiver output. This close closed that gap separately —
see "The archiver defect" below.

### What went right

Two WUs, two attempts, zero failures, zero re-arms, and both WUs came in **under**
estimate (T01 $2.21 vs $4.00; T02 $1.17 vs $3.50). The cause is legible and not luck:
the four invariants were checked by hand before the feature was drafted, so `PLAN.md`
could state the exact inherited state (30 anchors in `roadmap.md`, 39 in the archive,
zero duplicates, all four `blocked` rows carrying a Blocked-by block) and both WU bodies
could name the bidirectional trap explicitly instead of leaving it to be rediscovered.
Neither agent spent an attempt discovering the problem the feature was about.

### What was harder than planned

Nothing blocked. The one real surprise was factual rather than procedural: the archiver
defect this feature exists to catch is **not the shape the roadmap row said it was**. See
below.

## Cost analysis

`events.jsonl` is authoritative. Every `attempt_outcome` payload in it:

| WU | Attempts | Outcome | `cost_usd` (events) | `cost_usd` (frontmatter) | Planned |
|---|---|---|---|---|---|
| `FEAT-2026-0034/T01` | 1 | passed | 2.2107318 | 2.210732 | 4.00 |
| `FEAT-2026-0034/T02` | 1 | passed | 1.1694435 | 1.169444 | 3.50 |
| `FEAT-2026-0034/G1-CLOSE` | 1 (in flight) | — | *not yet written* | *not yet written* | 5.00 |

**Reconciliation.** The two `done` WUs reconcile exactly: each frontmatter `cost_usd` is
its `attempt_outcome` value rounded to six decimals. No gap.

**Actual, as a lower bound: $3.38** (2.2107318 + 1.1694435 = 3.3801753). This is a lower
bound rather than a total for a structural reason, not a missing-data one: the driver
appends this close WU's `attempt_outcome` *after* the session ends, so the close's own
cost cannot appear in a file the close itself is writing. The gap is exactly one WU's
cost — `G1-CLOSE`, planned $5.00 — and it is recoverable from `events.jsonl` after the
squash.

**Against plan.** $3.38 of $12.50 in WU estimates (27%) with the close still to land;
even if the close hits its full $5.00 estimate the feature lands near $8.38, about 67% of
the WU sum and 48% of the $17.50 gate budget. The $17.50 budget carried defensive padding
for one re-attempt of the largest WU (the closing-WU retry defect, issue #260); no
re-attempt was consumed, so that padding went unused.

**Reading the underrun honestly.** Both implementation WUs ran on `sonnet` at `medium`
effort against estimates sized for harder work. Estimates for a *sibling gate script over
a repo-scoped corpus* — this is the third such feature, after `event_type_gate.py`
(FEAT-2026-0060) and `arm_sweep_gate.py` (FEAT-2026-0063) — should come down; the shape is
now well-precedented and the last three have all landed under estimate.

### Failure-class breakdown

(no non-passing attempts in scope)

## Deferred verification

Every acceptance criterion in T01, T02, and this close was verified in-loop by an
executed command in the session that claimed it. There is one deferred item, and it is
deferred by nature rather than by omission:

| Criterion | Why not verified in-loop | Where it actually gets checked |
|---|---|---|
| "The gate exits 0 on this tree" holds *after* a live archive run, not just before one | The driver's `auto_archive_feature` runs on the next feature to reach `done`/`abandoned` — a state no WU in this feature can reach for another feature. This close simulated it (see below) but did not perform a live archive. | The `code` gate set on the first CI run after the next `/roadmap-archive` or driver auto-archive. That run is the feature's real first test. |

## What the loop did NOT verify

1. **ADR approval state — deliberately, and this is correct.** A `**Blocked by.**` ADR
   link is validated for *existence* (a file on disk, or a well-formed URL), never for
   whether the ADR was accepted. FEAT-2026-0011 has sat `blocked` on an unapproved
   ADR-0002 all week and passes this lint cleanly. Approval state is not machine-readable
   in this repo today and is not inferred. **This is not a gap for someone to close** —
   closing it would require an ADR status convention that does not exist, and inventing
   one inside a link linter would be scope creep. Recorded so it does not read as an
   oversight.

2. **The lint had not met a live archive run's fresh output.** As shipped by T01 and T02,
   every red test ran against a hand-built fixture and every green run ran against a tree
   that had been repaired by hand first. Neither proves the checker fires on what the
   *producer* actually emits.

   This close narrowed that gap but did not eliminate it. In-session, `auto_archive_feature`
   was driven over a **temp-directory copy** of the real `roadmap.md` + `roadmap-archive.md`
   for all 9 `done` features that still carry an inline detail section, linting before and
   after each run. Result: baseline 0 errors / 8 warnings; 7 of 9 archives introduced no
   new error; **2 of 9 introduced 2 new ERROR findings each, one in each ref direction** —
   the exact bidirectional shape the feature was built for. The lint caught all four.

   What remains unverified: a *live* archive performed by the driver on the real tree,
   under a real close, with the resulting `code` gate run in CI. The simulation used the
   real producer and real input but a copied tree.

3. **Nothing beyond the above.** The full suite's 11 sandbox errors were resolved rather
   than deferred, and the resolution is recorded here because the shape recurs.
   `python3 -m unittest discover -s tests` reports `Ran 2141 tests … FAILED (errors=11,
   skipped=5)` under the command sandbox; every traceback is a `git commit` inside a
   throwaway `$TMPDIR` repo, failing `error: Couldn't get agent socket?` →
   `fatal: failed to write commit object` because the sandbox blocks the commit-signing
   agent socket. All 11 live in `tests/test_lint_closing.py` and
   `tests/test_autosync_no_cwd_leak.py`; none touch `lint_roadmap` or the roadmap gate.
   Per `LEARNINGS [FEAT-2026-0041/G1-CLOSE/sandbox-git-temp-repo-errors]`, which vets both
   modules as `TemporaryDirectory`-only with no live reach, they were re-run unsandboxed:
   `python3 -m unittest tests.test_lint_closing tests.test_autosync_no_cwd_leak` →
   `Ran 11 tests in 1.035s / OK`. The rest of the suite was **not** unsandboxed, on purpose
   — this repo carries live-reach tests whose skip guard is the sandbox itself
   (`LEARNINGS [FEAT-2026-0042/G2-CLOSE/live-tests-fire-when-unsandboxed]`), and a close
   that unsandboxes the whole discovery run has previously created real issues on the live
   repository. Scoping the unsandboxed re-run to the two named modules gets the evidence
   without the blast radius.

## The archiver defect — outstanding, and not the shape the plan said

**Status: live, unfixed, and deliberately out of scope for this feature.** The roadmap row
is explicit that a failing check on the next archive run *is* the durable fix, and that
repairing rot instances by hand is not. This feature ships the check. Whoever fixes
`auto_archive_feature` now does it with a failing gate in hand. That is the design, not
unfinished work.

**But the shape has changed since the 2026-07-30 audit, and the close is where that gets
corrected.** `PLAN.md`, `GATE-01.md`, and this WU's body all assert that
`auto_archive_feature` "produces rot shapes 3 and 4 on every run" — stray/misattached
anchors and cross-file duplicate IDs. Driving the real function over a copied tree for all
9 archivable features produced **zero** anchor-adjacency errors and **zero** duplicate-ID
errors. Reading `specfuse/loop/loop.py`'s `auto_archive_feature` explains why: Step 2's
section regex now stops its lookahead at `<a id="` (so the *next* feature's anchor is no
longer dragged into the archive), and Step 5 separately strips the archived feature's own
preceding anchor. Both repairs are commented in place. Shapes 3 and 4 appear to have been
fixed between the audit and this feature.

What is still live is **shape 1, bidirectional ref rot**: the archiver moves a detail
section between files and does not rewrite the refs pointing at it, or the refs inside it.
Reproduced, exact findings:

```
archive FEAT-2026-0039 →
  ERROR roadmap.md:928          ref '#feat-2026-0039' does not resolve —
                                anchor is in roadmap-archive.md; rewrite to 'roadmap-archive.md#feat-2026-0039'
  ERROR roadmap-archive.md:230  ref 'roadmap.md#feat-2026-0039' does not resolve —
                                anchor is in roadmap-archive.md; rewrite to '#feat-2026-0039'

archive FEAT-2026-0069 →
  ERROR roadmap-archive.md:49   ref '#feat-2026-0039' does not resolve —
                                anchor is in roadmap.md; rewrite to 'roadmap.md#feat-2026-0039'
  ERROR roadmap-archive.md:244  ref 'roadmap.md#feat-2026-0069' does not resolve —
                                anchor is in roadmap-archive.md; rewrite to '#feat-2026-0069'
```

Both directions, from single archive runs — the bidirectionality `PLAN.md` predicted,
arriving through a different mechanism than it named. The mechanical fix in
`auto_archive_feature` is a two-way ref rewrite after the section moves: every
`#<archived-id>` remaining in `roadmap.md` becomes `roadmap-archive.md#<archived-id>`, and
every `roadmap.md#<id>` carried inside the moved section is re-resolved against the anchor
set of the file it lands in. That is a bug fix on the archiver, one branch and one PR, not
a feature — and it is now covered by a check that will fail loudly the moment it regresses.

## Consumer-visible contract changes

Per `close-discipline.md` §3, enumerated for explicit human acknowledgment. Three, and the
second is the one that matters to downstream projects.

1. **New shipped module: `specfuse/loop/lint_roadmap.py`.** Public surface:
   `lint_roadmap(repo_root: Path) -> list[Finding]`, the frozen `Finding` dataclass
   (`severity`, `file`, `line`, `message`), and the `SEVERITY_ERROR` / `SEVERITY_WARN`
   constants. Purely additive — nothing was removed or renamed. It ships in the package
   (not repo-internal hygiene) because every Specfuse project has a roadmap and archives
   features, so every one of them grows this rot.

2. **⚠️ A new gate every downstream project inherits on upgrade.** The `roadmap-link-gate`
   entry lands in `.specfuse/verification.yml`'s `code` set. **A downstream project whose
   roadmap already carries ERROR-severity rot starts failing a gate it did not previously
   have, on its next upgrade.** That is the intended behaviour — the rot is real and was
   invisible — but it is a breaking change in the "was green, now red" sense, and it
   arrives without the project having done anything. Mitigations already in place: the
   WARN classes (a Blocked-by block on a non-`blocked` row, an orphan detail section) print
   but deliberately do **not** fail the gate, so a merely-untidy roadmap stays green; and
   every ERROR message names the mechanical repair, which for the common ref-rot case is a
   prefix rewrite. This is the item this close asks a human to acknowledge explicitly.

3. **New operator-runnable script: `.specfuse/scripts/roadmap_link_gate.py`.** Exit 0 = no
   ERROR findings; exit 1 = ≥1 ERROR. Errors on stderr, warnings and the summary line on
   stdout. Runnable by hand outside the gate.

## Lessons promoted to `.specfuse/LEARNINGS.md`

Two entries, both tagged `[FEAT-2026-0034/G1-CLOSE]`:

- **Check the invariants by hand before drafting the feature that automates them.** This
  was assessed as the WU suggested, and it generalizes: it is the operational recipe for
  `planning-discipline.md` §2's satisfiability question, it is what let both WUs come in
  under estimate, and it is what made "the gate exits 0 on this tree" a satisfiable
  criterion rather than a day-one red.

- **Re-verify the producer's *current* behaviour before a close repeats the audit that
  motivated the feature.** The stronger lesson, and the one this feature would not have
  found without driving the real function: the defect had been half-fixed underneath a
  months-old audit, and three planning documents carried the stale shape forward
  unchallenged.
