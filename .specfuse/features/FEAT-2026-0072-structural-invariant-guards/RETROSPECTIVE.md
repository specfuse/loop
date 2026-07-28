<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0072, Structural-invariant guards

**Correlation ID.** `FEAT-2026-0072/G1-CLOSE`. Single terminal gate, three
substantive work units, one close. Verdict recorded in this WU's frontmatter:
**`met_locally`** — every criterion below is verified by a fresh run in this
session except the human acknowledgment that close-discipline §3 requires for the
consumer-visible contract-change list, which no human has yet given. The follow-up
record is in [What the loop did NOT verify](#what-the-loop-did-not-verify).

## What shipped

Three defects (#257, #284, #287) shared one shape: a surface the repo declares
about itself, that nothing checks, drifting silently until something unrelated
stumbles over it. #257 was already fixed; this feature generalised its guard shape
to the other two.

- **T01 — `tests/test_skill_discovery_links.py`.** Asserts the forward direction
  completely (every directory under `.specfuse/skills/` has a `.claude/skills/`
  entry that is a symlink resolving to it) and filters the reverse to links
  resolving inside `.specfuse/skills/`. Carries an `_INTENTIONALLY_UNLINKED`
  mapping, empty as shipped, with tests that every entry would need a non-empty
  reason and that no entry names an absent skill.
- **T02 — `scripts/sync-scaffold.sh` creates the links it documented.** The script
  referenced the symlink contract in two comments (lines 24 and 96) and created
  nothing. It now creates missing forward links only: an existing entry is left
  byte-identical, and the seven entries resolving outside `.specfuse/skills/`
  (operator tooling) are neither modified nor removed. Shipped with
  `tests/sync_scaffold_symlinks.bats` and its `verification.yml` gate entry, which
  #257's guard required in the same WU.
- **T03 — `check_done_feature_gates` in `specfuse/loop/lint_plan.py`.** A blocking
  error when a `status: done` feature has any `GATE-NN.md` not `status: passed`,
  skipping `GATE-NN-REVIEW.md` artifacts. Two exclusions by ID with inline
  reasons (`FEAT-2026-0001-health-endpoint`, the bundled fixture;
  `FEAT-2026-0036-adopt-ruff-016`, whose close ceremony deliberately never ran),
  plus the reconciliation in the same work unit — `FEAT-2026-0007`/`GATE-02` and
  `FEAT-2026-0008`/`GATE-01` flipped `awaiting_review` → `passed`.

The check and its reconciliation landing in one work unit was the load-bearing
sequencing decision, and it held: a new blocking error that fires three times on
the tree it ships into is unsatisfiable under `planning-discipline.md` §2, and
under the preflight baseline probe a red base gate halts the *next* feature's run
before any work unit dispatches.

## Oracles re-run fresh

Every command below was run in this close session against the working tree, exit
codes read directly. No producing WU's self-report is inherited.

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | `python3 -m pytest tests/test_skill_discovery_links.py -q` | `0` | 4 passed |
| 2 | `python3 -m pytest tests/test_done_feature_gates.py -q` | `0` | 8 passed |
| 3 | `python3 -m pytest tests/test_bats_suites_gated.py -q` | `0` | 4 passed |
| 4 | `bats tests/sync_scaffold_symlinks.bats` | `0` | 4/4 ok |
| 5 | `bats tests/sync_scaffold.bats` | `0` | 5/5 ok |
| 6 | `shellcheck scripts/sync-scaffold.sh` | `0` | clean |
| 7 | `bash -n scripts/sync-scaffold.sh` | `0` | parses |
| 8 | `python3 .specfuse/scripts/lint_plan.py <dir>` over all 39 dirs under `.specfuse/features/` (T03 criterion 11) | `0` × 38, `1` × 1 | zero findings from the new check; the one non-zero is a pre-existing crash unrelated to it — see below |
| 9 | `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0072-structural-invariant-guards` (`plannext` gate) | `0` | structurally valid |

**Oracles 4 and 5 required the sandbox disabled.** Both failed first with
`mktemp: mkdtemp failed on …: Operation not permitted` — the execution sandbox
denying temp-directory creation, which is exactly the environment condition T02's
escalation triggers named. Overriding `TMPDIR` to a writable path did not help
(bats resolves its own). Both suites root every path in `$TESTDIR` via the
`REPO_ROOT` env override and mutate no real-repo file, which was confirmed by
reading `tests/sync_scaffold_symlinks.bats` before re-running. They pass cleanly
outside the sandbox. **This is a live hazard for the driver's own verification
run**, since both suites are declared gates (`sync-scaffold-bats`,
`sync-scaffold-symlinks-bats`) — a driver invoked under the same sandbox will see
five and four spurious failures that say nothing about the code.

### The tree-wide sweep found a pre-existing linter crash

`FEAT-2026-0020-public-readiness-prep` exits `1` — not from the new check, but
from an unhandled `MiniYAMLError` in `read_frontmatter`:

```
specfuse.loop._miniyaml.MiniYAMLError: line 14: not a `key: value` line — got '<!--'
```

Two of its work-unit files, `WU-03-security-and-conduct.md` and
`WU-07-leak-scan-wiring.md`, lost their closing `---` frontmatter fence when a
long `completed_note:` was added out-of-loop on 2026-06-16, so the parser runs off
the end of the frontmatter into the body. Pre-existing, untouched by this feature,
and outside this WU's boundary to fix (`lint_plan.py` is T03's file; this WU
closes the gate, it does not patch the work).

It matters here for one reason: `check_done_feature_gates` is called at
`lint_plan.py:893`, *after* the work-unit loop that crashes at line 670, so for
that one feature the CLI sweep never reached the new check. Rather than infer the
result, the check was called directly on that directory:

```
FEAT-2026-0020 plan status = 'done'
check_done_feature_gates(FEAT-2026-0020) -> []
```

Zero findings — the feature has both gates at `passed`. **T03 criterion 11 holds
across all 39 directories**, 38 through the CLI and one through a direct call to
the check.

The deeper observation is that this is a *fourth* instance of this feature's own
shape: `lint_plan` declares that it validates WU frontmatter, and on malformed
frontmatter it crashes instead of reporting — so every check after the crash point
is silently skipped for that feature, and the exit code says "lint failed" without
distinguishing "found a problem" from "could not look". Recorded as a lesson and
worth an issue; not fixed here.

## The check does not fire on the feature that introduced it

Acceptance criterion 6, verified explicitly rather than assumed. The feature
directory was copied to a temp tree, `PLAN.md` set to `status: done` and
`GATE-01.md` to `status: passed` — the exact state `fire_terminal_flips` produces
— and `check_done_feature_gates` run against it:

```
B) simulated post-flip: plan='done' gate='passed'
B) excluded by ID? False
B) check_done_feature_gates -> []
```

Zero findings, and **not because of an exclusion** — this feature is deliberately
absent from `DONE_FEATURE_GATE_EXCLUSIONS`, so it passes on merit. The flip
ordering is correct: the driver flips the gate to `passed` and the PLAN to `done`
together, and there is no intermediate state the check observes.

Per `verification-discipline.md` §3, a rule that fires on nothing passes every
test, so the same run included a negative control — the same tree with the gate
left at `open`:

```
C) negative control: plan='done' gate='open'
C) check_done_feature_gates -> ["FEAT-2026-0072-structural-invariant-guards:
    PLAN.md status is 'done' but GATE-01.md is status: 'open', not 'passed'"]
```

The check is live, and it names the feature and the offending gate file.

## Consumer-visible contract changes

Enumerated per close-discipline §3, across T01–T03. This is **not**
`n/a — no consumer-visible contract change`: there is one breaking entry.

**1. New blocking `lint_plan` error — `check_done_feature_gates` (breaking, headline).**
`python3 .specfuse/scripts/lint_plan.py <feature_dir>` now exits non-zero for a
feature whose `PLAN.md` reads `status: done` while any of its `GATE-NN.md` files
is not `status: passed`. **Any downstream project that upgrades its scaffold and
has a done feature with an unclosed gate will start failing its plan-lint gate on
the first run after upgrade, with no code change of its own.** That is not a
hypothetical shape — it is precisely the state three features in *this* repo were
in, undetected, for weeks, and this repo is the one that wrote the machinery. A
downstream project with a legacy four-WU closing sequence (no `close` WU, so
`fire_terminal_flips` never had anything to fire from) or a close WU predating the
verdict contract is the likely case.

The remedy for a downstream hit is the same reconciliation T03 performed: flip
gates that genuinely completed to `passed`, and exclude by ID with a written
reason any whose close ceremony deliberately never ran. **The exclusion mapping is
a module-level constant in `specfuse/loop/lint_plan.py`, not project-local
configuration** — a downstream project cannot add its own exclusion without
patching vendored driver source. That is a real sharp edge and is named as a
follow-up below rather than papered over.

**2. `scripts/sync-scaffold.sh` now writes to `.claude/skills/` (additive,
behavioural).** An operator script that previously only copied files into
`specfuse/loop/data/` now also creates symlinks in a directory it never touched.
It creates only missing forward links, never replaces or re-points an existing
entry, and never touches entries resolving outside `.specfuse/skills/`. It also
honours a new `REPO_ROOT` environment override (previously the repo root was
derived solely from the script's own location) — added for test rooting, but it is
a live input any caller can now set, and setting it wrongly points every write at
the wrong tree.

**3. New declared gate — `sync-scaffold-symlinks-bats` in `.specfuse/verification.yml`
(additive).** `bats tests/sync_scaffold_symlinks.bats` joins the gate set, so
`bats` is now required wherever that gate runs. This repo's own file; downstream
projects are unaffected until they adopt it.

**4. New driver helper — `check_done_feature_gates` (additive).** Declared in
T03's `produces_driver_helper` frontmatter. Public in the sense that it is
importable from `specfuse.loop.lint_plan`; no existing signature changed.

**5. Two gate files reconciled (data, not contract).**
`FEAT-2026-0007/GATE-02.md` and `FEAT-2026-0008/GATE-01.md` moved
`awaiting_review` → `passed`. `FEAT-2026-0036/GATE-01.md` was deliberately left at
`open` and excluded by ID.

**No removals and no renames** across T01–T03.

**Human acknowledgment: not given.** close-discipline §3 requires this list to be
acknowledged by a human, and that is why the verdict is hedged rather than `met`.
Per `operator-escalation.md`, the acknowledgment text must come from the operator
— it is deliberately not drafted here.

## Cost analysis

`planned_cost_usd` in `PLAN.md` is **$14.00**; `GATE-01.md` carries a
`cost_budget_usd` of $19.00 (the plan sum plus one re-attempt of the largest WU,
per `planning-discipline.md` §5). Actuals are read from `events.jsonl`
`task_completed` payloads.

| WU | Planned | Actual | Attempts | Delta |
|---|---|---|---|---|
| T01 — skill-symlink guard | $2.50 | $0.556725 | 1 | **−$1.94** |
| T02 — sync creates symlinks | $3.00 | $0.623554 | 1 | **−$2.38** |
| T03 — done-feature gate check | $3.50 | $1.325495 | 1 | **−$2.17** |
| **Substantive subtotal** | **$9.00** | **$2.505774** | 3 | **−$6.49 (72% under)** |
| G1-CLOSE (this WU) | $5.00 | recorded by the driver on completion | 1 | not yet known |
| **Feature total** | **$14.00** | **$2.505774 + close** | 4 | — |

**The named delta: the three substantive work units came in $6.49 under plan, 28%
of their combined estimate, every one first-try.** Against the $19.00 gate budget
the feature has spent 13% before the close.

Two things explain the gap, and they are different in kind. **The estimates were
drafted for `opus` and the driver dispatched `sonnet`** at `effort: medium` for all
three — visible in each `attempt_outcome` payload. That is most of it. The rest is
that all three work units were genuinely well-scoped: the traps were found at
draft time (the asymmetric symlink set, the two exclusions, the check-and-
reconcile-together sequencing), so no work unit discovered its own scope mid-
attempt. That is the planning-discipline §2 and §4 work paying out, and it is the
part worth repeating.

The under-run is **not** evidence the floors in `planning-discipline.md` §5 are
too high. Those floors are for `plan-next` and `close` work units; these three are
`implementation`. And a 158-WU distribution is not revised by three observations
from one feature — that is exactly the outlier-generalisation failure §5's own
provenance note calls out.

### Failure-class breakdown

**No failed attempts.** All three substantive work units passed on attempt 1
(`outcome: passed`, `failure_class: null`, `failure_signature: null` in every
`attempt_outcome` event), and the gate recorded no re-arms (`re_arm_count: 0`
throughout). There are no failure classes to break down. The section is present
because acceptance criterion 10 is conditional on failures existing, and a
recorded "none" is cheaper to read than an absent heading is to interpret.

## What the loop did NOT verify

**Three entries.** Each names the criterion, why it could not be settled here, and
the exact condition that upgrades it. This is also the hedged-verdict follow-up
record required by close-discipline §2.

**D1 — Human acknowledgment of the consumer-visible contract-change list.**
*Criterion, verbatim (close obligation 3 / close-discipline §3):* "The close
enumerates every consumer-visible addition, removal, or rename … and **blocks on
explicit human acknowledgment of the list**."
*Why not verifiable here:* an agent cannot supply the acknowledgment it is
collecting — `operator-escalation.md` names writing the human's own justification
for them as one of the three failures that rule exists to prevent. The list itself
is complete and above; only the signature is missing, and the human cannot sign a
list that has not been written, which is why this WU wrote it and hedged rather
than emitting `blocked` with nothing to read.
*Exact condition that upgrades to `met`:* the operator reads
[Consumer-visible contract changes](#consumer-visible-contract-changes),
acknowledges entry 1 (the new blocking `lint_plan` error) in their own words, and
runs `/accept-hedged-close FEAT-2026-0072`, which records their reason and
re-checks the verdict through the driver's `--recheck-verdict` primitive so the
terminal flips fire through their one owner.

**D2 — The downstream-upgrade impact of the new blocking error.**
*Criterion, verbatim (close obligation 3):* "a downstream project whose tree has a
done feature with an unclosed gate will start failing its plan-lint gate on
upgrade."
*Why not verifiable here:* no work unit in this feature touches a downstream
project, and no such project is reachable from this repo. The claim is verified
*in principle* — the negative control above shows the check firing on exactly that
input shape — but not against a real consumer tree, and the sharp edge it implies
(the exclusion mapping is a module constant, so a downstream project with a
legitimate exclusion must patch vendored source) is unverified as a lived
experience.
*Exact condition that upgrades to `met`:* run `specfuse upgrade --dry-run` against
a target project holding at least one `done` feature with a non-`passed` gate, and
record whether its plan-lint gate fails and whether the operator can express the
exclusion without editing `specfuse/loop/lint_plan.py`. If they cannot, that is a
follow-up feature (project-local exclusions in `.specfuse/`), not a close fix.

**D3 — `sync-scaffold.sh`'s link-creation path against the real repository tree.**
*Criteria, verbatim (T02, 2–5):* "creates a symlink for it whose resolved target
is that directory" / "leaves that entry byte-identical" / "is neither modified nor
removed" / "a second consecutive run creates nothing and exits zero."
*Why not verifiable here:* all four are verified, and green, but **only against a
bats fixture tree** with `REPO_ROOT` overridden to a temp directory. On the live
tree the create-branch is unreachable: `.specfuse/skills/` holds 23 directories,
`.claude/skills/` holds 30 entries — 23 resolving inside `.specfuse/skills/` and 7
operator-tooling links resolving outside — so every forward link already exists
and the script reports "no missing links". This WU is also forbidden from
modifying that tree to create the gap. The invariant holding on the real tree is
confirmed by oracle 1; the script's *behaviour* on the real tree when a link is
genuinely missing is not.
*Exact condition that upgrades to `met`:* the next skill added to
`.specfuse/skills/` without a hand-made link — run `scripts/sync-scaffold.sh` and
confirm it creates that one link, leaves the 7 external entries untouched, and
that `python3 -m pytest tests/test_skill_discovery_links.py -q` exits zero
afterwards. This is a natural-occurrence check, not a task to schedule.

Three entries exceeds the two-entry threshold criterion 3 sets, so the gate-sizing
flag is raised under [What I'd change](#what-id-change) — with the attribution
tested rather than assumed, per `[FEAT-2026-0046/G1-CLOSE]`.

For scale: the gate carried **44 acceptance criteria** (T01 9, T02 12, T03 13,
close 10). Three deferrals is 6.8% — well under the 30% arm of the same threshold.

## What worked

- **Copying a proven guard's shape without importing its code.**
  `tests/test_bats_suites_gated.py` (#257) supplied the pattern — assert forward
  completely, filter the reverse, carry an explicit opt-out whose entries require
  a written reason — and both new guards follow it while sharing no code. Two
  checks over unrelated surfaces sharing a helper would have coupled them for no
  gain. The shape transferred; the code did not need to.
- **Naming both traps in `PLAN.md` before dispatch.** The asymmetric symlink set
  and the two done-feature exclusions are each the difference between a check that
  works and a check that fires on a correct tree. Both were written down at draft
  time, and neither work unit spent an attempt rediscovering them.
- **Landing T03's check and its reconciliation in one work unit.** The
  intermediate state — check shipped, tree still dirty — would have been red by
  construction and, under the preflight baseline probe, would have halted the next
  feature before any work unit dispatched.
- **The precedent guard doing its job on this feature's own work.** #257's check
  required `tests/sync_scaffold_symlinks.bats` to be registered in
  `verification.yml` in the same WU that added it. T02 was authored knowing that
  and did it, so the guard never had to fail to be useful.

## What I'd change

**Gate sizing — flagged by the threshold, and the attribution does not hold.**
Criterion 3's rule fires: three deferrals exceeds two. Per
`[FEAT-2026-0046/G1-CLOSE]`, a threshold that flags a cause obliges this close to
say whether the cause actually explains the observation. **It does not.** None of
the three deferrals would have closed under a two-gate split:

- **D1** is a human-in-the-loop step by construction. More gates means more
  acknowledgment points, not fewer un-acknowledged ones.
- **D2** needs a downstream project's tree. No gate count in *this* repo produces
  one; it needs a different work unit, in a different repo, with a real consumer.
- **D3** is a declared scope boundary — the bats tests operate on fixture trees by
  design, and T02's "Do not touch" explicitly forbids touching the live
  `.claude/skills/`. A second gate would have reproduced that boundary unchanged.

The single terminal gate was correctly sized: three independent work units, under
the ceremony-proportionality threshold, all first-try green, 72% under budget. The
alternative that would actually close D2 is a follow-up feature exercising the new
error against a real downstream upgrade — not a re-sliced gate here.

**Make the exclusion mapping project-local.** `DONE_FEATURE_GATE_EXCLUSIONS` being
a module constant in vendored driver source is the one design decision in this
feature I would revisit. It is right for this repo, where the two exclusions are
facts about this repo's own history. It is wrong for a downstream project, which
must patch driver source to declare a legitimate exclusion of its own — and a
patched vendored file is erased by the next `specfuse upgrade`. Worth an issue.

**Fix `lint_plan`'s crash-instead-of-report on malformed WU frontmatter.** Found
by this close's sweep (above). One feature's unterminated frontmatter fence
silently skips every check after the parse point, including the one this feature
shipped, and the exit code cannot distinguish "found a problem" from "could not
look". Worth an issue; the two affected work-unit files in
`FEAT-2026-0020-public-readiness-prep` need their closing `---` restored.

**Estimate against the model that will actually be dispatched.** The 72% under-run
is mostly `opus` estimates meeting `sonnet` execution. Not a problem — but a plan
whose numbers are off by 3–4× on every line is not being read as a budget by
anyone, which is how a real over-run stops being visible.

## Issues resolved

- **#284** — skill discovery links: asserted by T01, created by T02.
- **#287** — done features with unclosed gates: refused by T03, and the three
  offending features reconciled.
- **#257** — already fixed before this feature; its guard is the shape both new
  guards copy, and it gated this feature's own new bats suite.

## Lessons

Generalizable rules appended to `.specfuse/LEARNINGS.md` under
`[FEAT-2026-0072/G1-CLOSE]`. Feature-specific observations stay here.

## Hedged verdict accepted

**Accepted verdict:** `met_locally`

**Operator reason (verbatim):** accepted, downstream projects hitting this can reconcile the same way we did

**Recorded:** 2026-07-28T15:37:07Z

**Acknowledgment of the consumer-visible contract-change list (D1).** The operator
read the enumeration and acknowledged entry 1 — the new blocking `lint_plan` error
`check_done_feature_gates` — in their own words above. That is the signature D1 was
withheld for, and it discharges D1 and nothing else.

Accepting a hedge means shipping with known-open items, not pretending they are
done. All three entries from `## What the loop did NOT verify` are carried forward
below verbatim in substance. D1 is discharged by this acceptance; **D2 and D3 ship
open.**

### D1 — Human acknowledgment of the contract-change list — DISCHARGED

The close could not supply the acknowledgment it was collecting;
`operator-escalation.md` names writing the human's own justification for them as
one of the three failures that rule exists to prevent. The close wrote the list and
hedged rather than emitting `blocked` with nothing to read, which was the right
call. The operator's reason above is the missing signature.

### D2 — Downstream-upgrade impact of the new blocking error — OPEN

Carried forward. No work unit touched a downstream project and none is reachable
from this repo, so the claim that a consumer with a `done` feature and a
non-`passed` gate starts failing plan-lint on upgrade is verified in principle by
a negative control, not against a real consumer tree. *Re-run condition, verbatim:*
run `specfuse upgrade --dry-run` against a target project holding at least one
`done` feature with a non-`passed` gate, and record whether its plan-lint gate
fails and whether the operator can express an exclusion without editing
`specfuse/loop/lint_plan.py`.

**The sharp edge inside D2 is not discharged by this acceptance.** The exclusion
mapping is a module-level constant, so a downstream project cannot add a legitimate
exclusion without patching vendored driver source. The operator's accepted remedy
is that downstream projects reconcile as this repo did — flip gates that genuinely
completed, exclude by ID those whose close ceremony deliberately never ran — which
covers the reconciliation but not the case of an exclusion a consumer needs
permanently. Project-local exclusions in `.specfuse/` remain a candidate follow-up
feature.

### D3 — `sync-scaffold.sh`'s link-creation path on the real tree — OPEN

Carried forward. All four T02 criteria are green, but only against a bats fixture
tree with `REPO_ROOT` overridden to a temp directory. On the live tree every
forward link already exists (23 skill directories, 23 matching links, plus 7
operator-tooling links resolving outside `.specfuse/skills/`), so the create
branch is unreachable, and the WU was forbidden from deleting one to manufacture
the gap. *Re-run condition, verbatim:* the next skill added to
`.specfuse/skills/` without a hand-made link — run `scripts/sync-scaffold.sh`,
confirm it creates that one link, leaves the 7 external entries untouched, and that
`python3 -m pytest tests/test_skill_discovery_links.py -q` exits zero afterwards.
A natural-occurrence check, not a task to schedule.

Neither D2 nor D3 is discharged by this acceptance.
