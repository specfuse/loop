# FEAT-2026-0113 — Triage assigns a severity

## Gate 1

**What the gate set out to prove.** A triage marker carrying a `severity=` field
parses, **and** every marker shape already written in the wild parses exactly as
it does today, with no write path changed anywhere. The risk being retired: the
published marker's reader was positionally anchored
(`category=(?P<category>\S+) confidence=(?P<confidence>\S+) -->`), so a third
field would not have been merely ignored — the regex would have failed to match
at all, every new marker would have scanned as untriaged, and the triage label
would have been reapplied on every run.

Three units ran: T01 replaced the anchored regex with a marker shell plus a
`key=value` field scan and added `parse_marker_fields`; T01H (inserted mid-gate)
made `parse_marker` fail closed on a marker missing a field; T02 assembled the
corpus that proves the reader against every shape the repository actually ships.
All three are `status: done`. Measurements for every claim below are in
`## Measurements`; cost is reconciled in `## Cost analysis`. Per-criterion oracle,
kind and state for all 19 acceptance criteria are in `GATE-01-CRITERIA.md`.

### The load-bearing question: did any marker shape in the wild regress?

**No. Zero shapes that the old regex parsed are unparsed or differently parsed by
the new scan.** This is the answer that licenses gate 2 to start writing the new
shape, so it was measured rather than argued:

- Every `<!-- specfuse:triage … -->` literal in every tracked file in the
  repository was swept — not only `tests/`, which is all T02's corpus covers.
  **15 distinct literals.** Six of them are parseable by the old anchored regex.
  For all six, the old regex and the current reader return the **identical**
  `(category, confidence)` tuple. Divergences: **0**.
- The generated shapes were checked separately: `render_marker` over the full
  `CATEGORIES` × `CONFIDENCES` cross-product (5 × 2 = 10 markers), old regex vs.
  new reader. Mismatches: **0**. The round trip is not merely present, it is
  unchanged.
- The forward-compatible three-field shape behaves as designed: the old regex
  does not match it at all; the current reader returns `('bug', 'high')` from
  `parse_marker` and `{'category': 'bug', 'confidence': 'high', 'severity':
  'critical'}` from `parse_marker_fields`.
- `render_marker`'s output is byte-identical to before the gate, by string
  equality, and the only file changed under `specfuse/` is `triage.py`
  (23 insertions / 6 deletions), with `apply_triage` and every other write path
  absent from the diff.

The escalation trigger in this unit's body — "if a real marker shape regressed,
stop and escalate rather than closing green" — did not fire.

**But a regression did occur inside the gate, in the opposite direction, and it
is the most important thing gate 1 learned.** T01's tolerant reader turned three
shapes the old regex had safely *rejected* — `category=bug` with no
`confidence`, `confidence=` empty, `category=` empty — from `None` into a raised
`KeyError`. That is fail-**open**, not fail-closed, and `parse_marker` is called
on every open issue by five modules, so one malformed marker would have raised
out of an entire sweep. The malformed literal was already in the tree
(`tests/test_agent_invoke_usage.py:83`). Reproduced fresh in this close by
loading each gate commit's `triage.py` as a module:

| Tree | `category=bug confidence=high severity=critical` | `category=bug` | `category=bug confidence=` |
|---|---|---|---|
| before T01 | `None` | `None` | `None` |
| after T01 | `('bug','high')` | **`RAISED KeyError`** | **`RAISED KeyError`** |
| after T01H (HEAD) | `('bug','high')` | `None` | `None` |

T02 found it, obeyed its Do-not-touch clause and escalated instead of patching a
sibling's code. T01H carried the fix as its own dispatched, verified unit. The
boundary is what produced the correct escalation; that is the mechanism working,
not a cost of it.

### Per-criterion result

All 19 criteria across T01 (7), T01H (6) and T02 (6) are `state: pass`, each
against an oracle re-run fresh in this session. `GATE-01-CRITERIA.md` carries the
oracle command, `kind`, `state`, proving SHA and attempt for each; the summary:

| Unit | Criteria | Result | Proved by |
|---|---|---|---|
| T01 | #1–#7 | 7/7 pass | historical replay for the red-before claim; `test_marker_dual_shape` for the green-after; the source diff for "no caller edited" |
| T01H | #1–#6 | 6/6 pass | historical replay showing `KeyError` at T01's tree and `None` at T01H's; `FailsClosed` cases; additive-only test diff |
| T02 | #1–#6 | 6/6 pass | `MarkerCorpus` + `RoundTrip` cases, corroborated by a repository-wide sweep wider than the test's own corpus |

Every `kind` is `narrow`: each oracle is a named test nodeid, a named module
list, a countable grep over a fixed file set, or a bounded diff. The full suite,
coverage and the `tier: broad` gates are the driver's once-per-gate broad run and
are cited below, not re-run here.

### Deferred verification

`(nothing — every acceptance criterion was verified in-loop)`

All 19 criteria were verified in this session against a command with an observed
exit code. Two things are worth stating alongside that, because neither is a
deferred criterion and neither should be mistaken for one:

- **"In the wild" is proxied by this repository's literals, by design.** T02's
  own escalation trigger forbids a network call or a live `gh` query, and the
  corpus is correspondingly built from tracked files. This close widened the
  sweep from `tests/` to every tracked file and still found nothing new, but no
  gate-1 oracle reads a real issue body in a consumer repository. That residual
  risk is carried, not deferred: gate 3's backfill mode is the first surface that
  reads already-marked issues, and it is where a live-corpus check belongs.
- **The broad tier ran, and it was the driver that ran it.** Per the dispatch
  contract this session ran no full suite, no coverage and no `tier: broad`
  gate. `broad_run_result` for gate 1 recorded `ok: true`, `failing: []` at
  `2026-09-18T00:48:19Z`, on the tree pinned in `GATE-01.md`'s `broad_run:`
  block. Cited, not re-run.

### Consumer-visible contract changes

One addition, no removal, no rename, no behaviour change to anything a consumer
already depends on:

- **`added`** — `specfuse.loop.triage.parse_marker_fields(body)`, returning every
  `key=value` field the triage marker carries as a `dict`, or `None` when the
  body carries no marker. `specfuse/loop/triage.py` declares no `__all__`, so the
  function is importable and therefore a public surface.

Everything that could have been a contract change explicitly is not one: the
emitted marker format is byte-identical (`render_marker` asserted by string
equality), `parse_marker`'s signature and `(category, confidence)` return type
are unchanged, and no `severity:*` label or marker field is written anywhere.
`CHANGELOG.md` gains no entry from this gate — the addition is a helper with no
consumer until gate 2 writes the new shape, and the feature's `Unreleased` entry
belongs with the write path, where a reader can be told what actually changed for
them. The terminal close (`FEAT-2026-0113/G3-CLOSE`) carries the feature's full
§3 enumeration and the `close-k` changelog linkage.

### What gate 2 should know before it is armed

1. **`parse_marker`'s blast radius is wider than `PLAN.md` says.** The plan names
   three callers (`triage.apply_triage`, `bug_lane_state.triaged_bug_intake`,
   `agent/providers/triage.py`). The tree has **six call sites across five
   modules**: `specfuse/agent/state.py:167`, `specfuse/agent/triage_invoke.py:70`,
   `specfuse/loop/triage.py:202` and `:304`, `specfuse/loop/bug_lane_run.py:488`,
   `specfuse/loop/bug_lane_state.py:209`. `agent/providers/triage.py` is not a
   caller at all — it reaches the reader indirectly through
   `triage_invoke.classify_result`. Nothing in gate 1 depended on the count being
   right, but a gate-2 unit scoped by that list would be scoped wrong.
2. **`specfuse/loop/promotion.py` is not a triage caller**, despite grepping like
   one. It defines its own `parse_marker` / `render_marker` over a separate
   `<!-- specfuse:promoted feature_id={feature_id} -->` marker. Do not widen a
   gate-2 unit into it.
3. **The precedence declaration in `PLAN.md` still holds and is now load-bearing
   in a second way.** Marker first, label second, label as a projection. Gate 1
   has made the marker reader tolerant of a field nothing writes; the moment gate
   2 writes it, every issue marked before gate 2 becomes a two-field marker in a
   three-field world, which is exactly the asymmetry gate 3's backfill exists for.

### Lessons promoted

One durable rule went to `.specfuse/LEARNINGS.md`, tagged
`[FEAT-2026-0113/G1-CLOSE-INTERMEDIATE]`: loosening a published marker's reader
must be paired with an explicit fail-closed criterion, because tolerance and
strictness are the same edit and the failure mode flips direction silently. The
draft-time candidate — "is a positionally-anchored regex over a published marker
a recurring shape worth a rule?" — was checked rather than assumed, and the
answer is yes: the codebase carries **ten** `_MARKER_TEMPLATE`-convention
published markers and, after this gate, `triage.py` is the only one whose reader
scans fields instead of anchoring them. The rule names
`specfuse:autofix-attempt` specifically, because it is the only other multi-field
marker and therefore the only other one carrying triage's exact latent defect.

## Measurements

Every command below ran fresh in this close session, from the working tree, with
the repository venv (`.venv/bin/python`) and no git mutation. Working-tree source
state equals `026cf994f70d98f2675f3b2bc31c049d8956ad01` — the only uncommitted
changes are this close's own artifacts, nothing under `specfuse/` or `tests/`.
Per the dispatch contract this session ran no full suite, no coverage and no
`tier: broad` gate.

### feature_oracle: PASS

| Oracle | Command | Result | Exit |
|---|---|---|---|
| Gate `feature_oracle` | `python3 -m unittest tests.test_marker_dual_shape -v -b` | `Ran 11 tests`, `OK` | 0 |
| Triage-adjacent modules and the caller ratchet | `python3 -m unittest tests.test_triage tests.test_triage_apply tests.test_triage_skill_contract tests.test_triage_skips_agent_escalations tests.test_agent_provider_triage tests.test_agent_policy_triage_dial tests.test_agent_invoke_usage tests.test_caller_check_ratchet tests.test_bug_lane_run -b` | `Ran 90 tests`, `OK` | 0 |
| Repository-wide marker sweep, old regex vs. current reader | every `<!-- specfuse:triage … -->` literal in `git ls-files` | 15 distinct literals, 6 old-parseable, **0 regressions** | 0 |
| Generated-shape equivalence | `render_marker` over `CATEGORIES` × `CONFIDENCES` | 10 markers, **0 mismatches** old vs. new | 0 |
| Historical replay | `git show {81e10f9^,81e10f9,79be9a3}:specfuse/loop/triage.py` loaded as modules | red-before / `KeyError` / green-after, per the table above | 0 |
| Gate diff scope | `git --no-pager diff --stat main -- specfuse/` | one file, `specfuse/loop/triage.py`, +23/−6 | 0 |
| Narrow tier for `close-intermediate` (`gate_set: plannext`) | `python3 .specfuse/scripts/lint_plan.py <feature_dir>` | reported in this close's RESULT block | — |
| Closing lint | `python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` | reported in this close's RESULT block | — |

Before this session wrote anything, the closing lint exited 1 with exactly one
unmet requirement, `close-intermediate-b` (no `LEARNINGS.md` addition and no
"nothing generalizes" note). `close-intermediate-f` was not yet in scope because
`GATE-01-CRITERIA.md` carried only pristine stub entries.

**Driver broad run, cited and not re-run.** `broad_run_result` for gate 1,
`2026-09-18T00:48:19.798038+00:00`: `ok: true`, `failing: []`, over the 18-tree
digest recorded in `GATE-01.md`'s `broad_run:` block.

**Published-marker survey** (`grep -rn "_MARKER_TEMPLATE = " --include="*.py"
specfuse/`): 10 templates — `specfuse:finding`, `specfuse:autofix-attempt`,
`specfuse:question`, `specfuse:answered-escalation`, `specfuse:promoted`,
`specfuse:sla-repinged`, `specfuse:escalation`, `specfuse:triage`,
`specfuse:followup`, `specfuse:bug-automerge`. Of these, `specfuse:triage` is now
the only one read by a field scan; `specfuse:autofix-attempt` is the only other
multi-field marker and its reader is positionally anchored on
`fingerprint=(?P<fingerprint>\S+) at=(?P<at>[0-9.]+)`.

## Cost analysis

Reconciled against each unit's `planned_cost_usd` and the `attempt_outcome`
records in `events.jsonl` — not estimated. Four attempts are on record for gate
1 before this close.

| Unit | Planned | Attempts | Actual | Ratio | Note |
|---|---|---|---|---|---|
| `T01` | $3.00 | 1 (passed) | $0.292826 | 0.10× | 34.5 s, 3,485 output tokens |
| `T01H` | $1.00 | 1 (passed) | $0.293139 | 0.29× | 48.9 s; not in `PLAN.baseline.json` — inserted mid-gate |
| `T02` | $2.00 | 2 (blocked, then passed) | $1.029604 | 0.51× | $0.529971 blocked + $0.499633 passed; 293.6 s total |
| **Gate 1 implementation** | **$6.00** | **4** | **$1.615569** | **0.27×** | |
| `G1-CLOSE-INTERMEDIATE` | $4.50 | in progress | — | — | this unit |
| `G1-PLAN` | $6.00 | not started | — | — | |
| Feature total (planned) | $21.50 | | | | gate 2's units are not yet drafted |

**Reconciliation.**

- **Implementation came in at 27% of plan.** All three units are small, tightly
  scoped edits to one module and one test file; `planning-discipline.md`'s
  estimates are one-sided, so a 3.7× under-run reads as on-plan to the off-plan
  checks and is worth stating explicitly rather than leaving to be inferred.
  `evaluate_off_plan_signal` nonetheless reports this gate **off-plan**
  (`reflection_required` is `True`), which is why this section is written rather
  than skipped.
- **The escalation cost $0.53 and was worth it.** T02's blocked attempt is the
  single largest line item in the gate, 33% of implementation spend. It bought
  the `KeyError` regression, which the gate's own definition of done would
  otherwise have shipped: no criterion in T01 asserted on a *malformed* marker,
  and the broad run would have stayed green because the malformed literal at
  `tests/test_agent_invoke_usage.py:83` is never fed to `parse_marker` by that
  suite. Escalating rather than patching also produced a second dispatched unit
  with its own red-test-first evidence, which is why the fix is verifiable at all.
- **T01H was inserted after the baseline was snapshotted.** It carries a
  `planned_cost_usd` of $1.00 assigned at insertion and appears in `PLAN.md`'s
  "Mid-gate insertions" and "Assumptions" sections, but not in
  `PLAN.baseline.json`, which lists only T01, T02 and the two closing units.
  Anyone reconciling this feature from the baseline alone will be $1.00 short on
  plan and $0.29 short on actuals.
- **T02 was billed twice for one unit of work.** The re-dispatch re-read the same
  context (846k cached input tokens on both attempts) and produced a comparable
  volume of output (13,410 then 12,754 tokens). That is the standing price of the
  escalate-don't-patch boundary, and at $0.53 it is cheap relative to what it
  caught.

### Failure-class breakdown

`summarize_attempt_failure_classes` reports `(no non-passing attempts in scope)`
for gate 1, because it keys on the `failure_class` field and gate 1's one
non-passing attempt carries `failure_class: null`. That sentinel is accurate to
the driver's classifier and **misleading as a summary of the gate**, so the real
breakdown is recorded here:

| Class | Count | Detail |
|---|---|---|
| `agent_reported_blocked` (self-escalation, correct) | 1 | `FEAT-2026-0113/T02` attempt 1, `human_escalation` at `2026-09-18T00:31:43Z`. The unit's criterion 5 failed against a sibling unit's shipped code; it stopped at its Do-not-touch boundary and reported rather than patching. Resolved by inserting `FEAT-2026-0113/T01H`. |
| Verification failure | 0 | No attempt was refused by the driver's re-verification. |
| Guard refusal | 0 | No `produces_not_in_diff`, no closing-deliverable refusal. |
| Re-arm | 0 | `re_arm_count: 0` on every task. |

One blocked attempt in four, and it was the gate's highest-value attempt. No
attempt in this gate failed for a reason worth preventing.

## Gate 2

**What the gate set out to prove.** A triage run records a severity — marker
first, `severity:<value>` label second — in **both** repository shapes, and a
repository that declares its own `severity:*` scheme is left alone: nothing
created, no description rewritten. The rubric comes from the repository's own
label descriptions where it has them, and from specfuse's published
`DEFAULT_SEVERITY_RUBRIC` (with the four labels provisioned) where it has none.

Five units ran: T02H (inserted mid-gate) wired the thinnest end-to-end path so
the gate's `feature_oracle` existed at all; T03 extracted the label listing and
added `read_severity_rubric` + `DEFAULT_SEVERITY_RUBRIC`; T04 extended
`render_marker` / `apply_triage` to the third field and the projected label; T05
carried the rubric into the one classification session and made the reader fail
closed without a readable value; T06 wired it through `TriageProvider.execute`
and turned the oracle green on both shapes. All five are `status: done`.
Measurements are in `## Measurements — gate 2`; cost is reconciled in
`### Cost analysis` below. Per-criterion oracle, kind and state for all 25
acceptance criteria are in `GATE-02-CRITERIA.md`.

### The load-bearing question: was a repository's own severity scheme disturbed?

**No. Zero `gh label create` calls and zero label-description writes against any
repository that declares a `severity:*` scheme of its own.** This is the property
gate 3 has no premise without, so it was measured by argv over the whole call
sequence in this session — an independent probe driving `TriageProvider.execute`
with an injected runner, not a re-reading of T06's assertions:

**Case A — repository declares the four specfuse-shaped labels, all described:**

```
1. gh label list --json name,color,description --limit 1000 --repo o/r
2. claude  [classification session]
3. gh issue edit 101 --repo o/r --body <marker: category=bug confidence=high severity=high>
4. gh issue edit 101 --repo o/r --add-label triage:bug,severity:high
```

`gh label create` calls: **0**. argv containing `--description`: **0**. Marker
(3) precedes label (4).

**Case B — repository declares a scheme that is not specfuse's:**
`severity:critical` / `severity:major` / `severity:minor`, all three described,
which is the measured real-world case `T06`'s escalation trigger names. Identical
shape to case A: **0** creates, **0** `--description` argv, marker before label.

The rubric-reader level was probed separately, because non-interference has to
hold for scheme shapes the run-level test does not enumerate:

| Repository's own `severity:*` labels | Rubric returned | `gh label create` calls |
|---|---|---|
| `low`/`medium`/`high`/`critical`, all described | its own four descriptions | **0** |
| `critical`/`major`/`minor`, all described | `{critical: "Prod down."}` | **0** |
| `high` described **empty**, `low` described | shipped text for `high` only, its own `low` kept | **0** |
| only `severity:major` (no value in `SEVERITY_VALUES`) | `{}` | **0** |
| none at all | full `DEFAULT_SEVERITY_RUBRIC` | 4 |

The branch test is `name.startswith("severity:")`, not membership in
`SEVERITY_VALUES` — so the last declares-own row is the interesting one: a
repository whose whole scheme lies outside specfuse's vocabulary gets an **empty
rubric and no severity recorded**, and is still not touched. That is inert for
that repository but safe, and it is the correct precedence: not disturbing an
operator's labels outranks recording a severity. It is worth carrying into gate 3
as a known coverage hole rather than a defect — `rules.bugs.severity_aliases`
(#3349) already exists as the operator's declared mapping for exactly those
labels, and nothing in this gate reads it.

**Criterion 2b — provisioning precedes the first `--add-label`.** Measured on the
declares-none branch (case C), where a label applied before it exists fails
(#3244):

```
1. gh label list …
2. gh label create severity:low      --force --color c2e0c6 --description …
3. gh label create severity:medium   --force --color fbca04 --description …
4. gh label create severity:high     --force --color d93f0b --description …
5. gh label create severity:critical --force --color b60205 --description …
6. claude  [classification session]
7. gh issue edit 103 --repo o/r --body <marker: … severity=high>
8. gh issue edit 103 --repo o/r --add-label triage:bug,severity:high
```

All four creates precede the single `--add-label`, every one carries `--force`,
and the ordering holds at run scope and not merely per issue: over three
untriaged issues (case E) the sequence is **one** `gh label list`, **four**
`gh label create`, then three marker/label pairs — 14 calls, no second listing
and no repeated create.

**The degradation path still produces today's sequence byte for byte.** With the
listing failing (case D): `gh label list` (fails) → `claude` → `gh issue edit
--body <marker: category=bug confidence=high>` → `gh issue edit --add-label
triage:bug`. No `severity=` in the marker, no `severity:` in the label argument,
zero creates, no raise.

**Escalation triggers: none fired.** No label was created against a
declares-its-own repository; no description it authored was overwritten;
provisioning ran only on the declares-none branch; and the two-field marker is
still byte-identical — `render_marker` over the full `CATEGORIES` × `CONFIDENCES`
cross-product (10 shapes) matches the literal
`<!-- specfuse:triage category={c} confidence={f} -->` with **0** mismatches.

### The gate's own finding: T06 deleted an assertion T02H was dispatched to add

T02H's body states that T06 "extends this module with the severity assertions its
own criteria name; it does not rewrite the harness." **It rewrote the harness.**
T02H shipped one test, `test_execute_writes_marker_then_label_in_order`, in class
`TestTriageSeverityEndToEnd`; at HEAD the class is `SeverityEndToEnd` and that
test name does not exist. The diff is +172/−39, not additive.

The substance mostly survived — `test_failing_label_listing_degrades_to_todays_write_sequence`
carries the same severity-free case — with one exception that matters. T02H
asserted the **order** of today's sequence structurally (`marker_call, label_call
= edit_calls`, then per-call `--body`/`--add-label` exclusivity). The surviving
test asserts contents and counts and **not order**. Ordering is still asserted at
HEAD, but only on the severity-*carrying* paths (`assertLess` at lines 134 and
188). So the precedence claim for a run that records no severity — the
degradation path, the one an operator on a broken `gh` actually gets — has no
test pinning it any more. The behaviour is correct: case D above measures marker
before label. The *assertion* is gone.

Nothing caught this. T02H's criteria were recorded green at T02H's tree; the
full suite stayed green because the replacement tests pass; and `produces:`
matching cannot see it, because the file is legitimately in T06's `produces:`
list too. This is the gate's most transferable lesson and is promoted below.

### Per-criterion result

All 25 criteria across T02H (5), T03 (7), T04 (5), T05 (4) and T06 (4) are
`state: pass`, each against an oracle re-run fresh in this session.
`GATE-02-CRITERIA.md` carries the oracle, `kind`, `state`, proving SHA and
attempt for each; the summary:

| Unit | Criteria | Result | Proved by |
|---|---|---|---|
| T02H | #1–#5 | 5/5 pass | `git cat-file -e` at the pre-unit tree for the red-before claim; the T02H blob for what it shipped; the module green at HEAD. #3's ordering assertion is proved at T02H's tree and re-measured at HEAD by argv, not by a surviving test — see the finding above |
| T03 | #1–#7 | 7/7 pass | `tests.test_severity_rubric` (10 cases); `grep -c '"label", "list"'` → `1`; the five-row rubric table above; `test_provision_labels` + `test_label_provisioning_runner_contract` unedited and green |
| T04 | #1–#5 | 5/5 pass | `tests.test_triage_severity_write` (7 cases); `render_marker` 10-shape byte-equality; case D's argv identical to today's; `tests.test_triage_apply` green unedited |
| T05 | #1–#4 | 4/4 pass | `tests.test_triage_severity_classify` (12 cases); `grep -c` for default-definition text in `triage_invoke.py` → **0**, with `DEFAULT_SEVERITY_RUBRIC` defined at `labels.py:347` and nowhere else |
| T06 | #1–#4 | 4/4 pass | the gate `feature_oracle` (5 cases); the independent argv probe, cases A/B/C/D/E |

Every `kind` is `narrow`: each oracle is a named test module or nodeid, a
countable grep over a fixed file set, a bounded diff, or an enumerated argv
probe over a closed case set. The full suite, coverage and the `tier: broad`
gates are the driver's once-per-gate broad run and are cited below, not re-run
here.

### Deferred verification

`(nothing — every acceptance criterion was verified in-loop)`

All 25 criteria were verified in this session against a command with an observed
exit code. Three things are worth stating alongside that, none of them a deferred
criterion:

- **Gate 1's residual is re-stated, not retired.** No oracle in this feature has
  yet read a real issue body outside this repository. Gate 2 made it *larger*
  rather than smaller: every gate-2 oracle injects a runner, so the `gh label
  list` JSON, the classification answer and every write are all authored by the
  test. What has never been exercised is a live `gh` against a real repository's
  label set. Gate 3's backfill mode is the first surface that reads
  already-marked issues, and it remains where a live-corpus check belongs.
- **A repository whose scheme lies entirely outside `SEVERITY_VALUES` records no
  severity.** Verified in-loop (the `{}` row above) and behaving as designed; it
  is a scope statement for gate 3, not an unverified criterion.
- **The broad tier ran, and it was the driver that ran it.** Per the dispatch
  contract this session ran no full suite, no coverage and no `tier: broad`
  gate. The broad run is cited below, including the one that failed.

### Consumer-visible contract changes

Three additions and one behaviour change, all in the write path; no removal, no
rename, nothing an existing consumer depends on is broken:

- **`added`** — `specfuse.loop.labels.read_severity_rubric(target, *, runner,
  repo)` returning `{severity_value: description}`, and the published
  `specfuse.loop.labels.DEFAULT_SEVERITY_RUBRIC` / `SEVERITY_LABEL_SPECS` it
  falls back to.
- **`added`** — `render_marker(category, confidence, severity=...)` emits a third
  `severity=<value>` field; the two-field call is byte-identical to before.
- **`changed`** — a triage run now writes `severity=` into the marker and
  projects a `severity:<value>` label, marker first.
- **`changed`** — a repository that declares **no** `severity:*` label has the
  four labels provisioned on first use, `gh label create … --force`, once per
  run.

**A repository that declares its own `severity:*` scheme has nothing created and
nothing overwritten** — that is the property an existing consumer will check
first, it is the contract that replaced the withdrawn opt-out, and it is measured
by argv above rather than asserted in prose. `CHANGELOG.md`'s `Unreleased`
section gains the corresponding entry, which is the one gate 1 deliberately
deferred to the gate that ships the write path.

### What gate 3 should know before it is armed

1. **The classifier and the floor read different vocabularies.** The rubric is
   built only for values in `agent_policy.SEVERITY_VALUES`, while
   `rules.bugs.severity_aliases` (#3349) exists precisely so a floor can read
   `severity:major`. A repository on an aliased scheme is therefore readable by
   the floor and invisible to the classifier. Gate 3's backfill will meet those
   repositories first, since they are the ones with the most unlabelled history.
2. **Backfill's idempotency key is the marker, and it is now three-field.** Every
   issue marked before this gate carries a two-field marker that parses fine and
   records no severity. Backfill must amend the marker before adding the label,
   per `PLAN.md`'s Record precedence — a backfill unit that labels first is wrong
   rather than a variant.
3. **The listing is once per `execute` run, and backfill is a different run
   shape.** Provisioning is bounded per run, not per issue; a backfill mode that
   re-enters `execute` per issue would re-list per issue. The bound is asserted
   in `test_listing_and_provisioning_happen_once_per_run`, which only covers the
   normal path.
4. **Do not trust a same-gate sibling's promise not to rewrite your tests.** See
   the T02H/T06 finding above; the drafting consequence is the promoted rule.

### Lessons promoted

Three durable rules went to `.specfuse/LEARNINGS.md`, tagged
`[FEAT-2026-0113/G2-CLOSE-INTERMEDIATE]`: (1) a non-interference contract proved
by argv over the whole call sequence is a categorically stronger claim than
"behaves equivalently" in prose, and is the shape to reach for whenever a feature
promises not to touch something an operator owns; (2) a safety constraint stated
over a *bundle* can be strictly wider than the constraint that is load-bearing —
here "the rubric must be the operator's" instead of "the floor must be the
operator's", which shipped a feature inert by default; (3) a later unit in the
same gate can silently delete an earlier unit's assertions, and nothing in the
loop notices.

Two draft-time candidates were **not** promoted. The oracle-ordering deadlock
that cost this gate four attempts is already covered by `authoring-work-units`
§14 (tracer bullet) — the rule existed and the gate was drafted against it
anyway, which is a drafting-review problem, not a missing rule. And the caller
ratchet's reverse direction is `caller_check`'s documented behaviour, not a
lesson.

### Cost analysis

Reconciled against each unit's `planned_cost_usd` and the `attempt_outcome`
records in `events.jsonl` — not estimated. Ten attempts are on record for gate 2
before this close's own dispatch.

| Unit | Planned | Attempts | Actual | Ratio | Note |
|---|---|---|---|---|---|
| `T02H` | $2.00 | 1 (passed) | $0.314276 | 0.16× | 38.3 s; inserted mid-gate, after the deadlock |
| `T03` | $3.00 | 3 (failed, failed, passed) | $2.902027 | 0.97× | $0.839038 + $0.879547 discarded, $1.183442 passed; 655.6 s total |
| `T04` | $3.00 | 3 (failed, failed, passed) | $2.030093 | 0.68× | $0.556754 + $0.780525 discarded, $0.692815 passed; 362.3 s total |
| `T05` | $2.50 | 1 (passed) | $0.470493 | 0.19× | 80.4 s |
| `T06` | $3.00 | 1 (passed) | $0.822717 | 0.27× | 163.2 s |
| **Gate 2 implementation** | **$13.50** | **9** | **$6.539607** | **0.48×** | |
| `G2-CLOSE-INTERMEDIATE` | $4.50 | 1 prep-halt ($0.00) + this one | — | — | the halt cost nothing; see below |
| `G2-PLAN` | $6.00 | not started | — | — | |
| Feature total (planned) | $43.50 | | | | gate 1 actual $1.615569 + two closing units |

**Reconciliation.**

- **Gate 2 came in at 48% of plan, and 47% of what it spent was discarded.**
  $3.055863 of the $6.539607 went to four attempts that produced nothing kept:
  T03 attempts 1–2 and T04 attempts 1–2, all four failing on the identical
  signature `ERROR: test_triage_severity_end_to_end
  (unittest.loader._FailedTest.test_triage_severity_end_to_end)`. Both units
  escalated `spinning_signature_repeat` at attempt 2, correctly. Neither could
  ever have passed: the gate's `feature_oracle` names a module that was T06's
  `produces:` file and was in both units' Do-not-touch lists, and `verify()` runs
  the `feature_oracle` untiered on every attempt. That is a **drafting** defect
  priced at $3.06 — a gate whose oracle is red until its last unit lands, against
  a driver that runs the oracle on every attempt.
- **The fix was a tracer bullet, and it cost $0.31.** T02H wired the thinnest
  end-to-end path and turned the oracle green before any unit that had to be
  verified against it. T03 and T04 then passed first try on re-arm. The ratio is
  the argument for `authoring-work-units` §14 in one line: $0.31 spent up front
  would have saved $3.06.
- **Gate 2's whole unit set is absent from `PLAN.baseline.json`.** The baseline
  records `{"gate": 2, "work_units": []}` — gate 2 was drafted by `G1-PLAN` after
  the snapshot. Anyone reconciling this feature from the baseline alone will be
  $13.50 short on plan for gate 2 and will read the arm predicate's
  `budget_projection` "within 2.0× baseline planned total $20.50" against a
  planned total that never included this gate. The projection still came in
  clean ($32.57 against a $41.00 cap), but it was clean against the wrong
  denominator.
- **The prep halt cost $0.00 and one dispatch cycle.** The close's first dispatch
  halted before the session started: the WU declared `oracles: [recent-commits]`,
  a *gate* name, where the key takes a `verification.yml` **set** name
  (`oracles`). `duration_seconds: 0.003`, `cost_usd: 0.0`. Cheap, and caught by
  the driver rather than by a session burning context on it.
- **One out-of-loop commit sits inside this gate's range.** The gate-2 broad run
  failed on `test_the_baseline_has_not_silently_shrunk`; `1a6a0d7` removed
  `read_severity_rubric` from the caller ratchet's `BASELINE`. This is the
  ratchet's reverse direction working as designed — T03 added the entry
  correctly (the symbol landed ahead of its callers by design) and T06 gave it a
  caller, at which point a `BASELINE` entry must be removed or it becomes a stale
  waiver. Net effect across the gate is zero: `git diff 8169640..HEAD --
  tests/test_caller_check_ratchet.py` is empty. No unit could reasonably have
  caught it — T03 had no caller yet, and the symbol only became reachable at T06.

### Failure-class breakdown

`summarize_attempt_failure_classes` reports gate 2's four non-passing attempts
under `failure_class: other`, which is accurate to the driver's classifier and
uninformative as a summary. The real breakdown:

| Class | Count | Detail |
|---|---|---|
| Oracle-unsatisfiable-by-construction | 4 | T03 attempts 1–2, T04 attempts 1–2. One signature across all four: the gate's `feature_oracle` named a module no dispatched unit was permitted to create. $3.055863. Resolved by inserting `FEAT-2026-0113/T02H`. |
| `spinning_signature_repeat` escalations | 2 | T03 and T04, both at attempt 2. The driver stopped each unit at the right point; neither agent could have fixed the cause from inside its own boundary. |
| Broad-run gate failure | 1 | `broad_run_gate_failure` at gate 2: `tests` (`test_the_baseline_has_not_silently_shrunk`) and `coverage` (`no_gate_marker`, a consequence of the suite failing). Fixed out of loop by `1a6a0d7`; the re-run is clean. |
| Prep halt | 1 | `G2-CLOSE-INTERMEDIATE` attempt 1, `prep_halted`, $0.00 — a malformed `oracles:` key, fixed in `f13dd80`. |
| Verification failure | 0 | No attempt was refused by the driver's re-verification. |
| Guard refusal | 0 | No `produces_not_in_diff`, no closing-deliverable refusal. |

Four of gate 2's nine implementation attempts failed, and all four failed for the
same preventable reason. Unlike gate 1 — where the one blocked attempt bought the
gate's most valuable finding — none of these bought anything. The gate's real
finding (T06 deleting T02H's assertion) was found by this close, not by an
attempt.

## Measurements — gate 2

Every command below ran fresh in this close session, from the working tree, with
the repository venv (`.venv/bin/python`) and no git mutation. Working-tree source
state equals `4ad0253647b8f5c461a1b56723549a802138c1c0` — the only uncommitted
changes are this close's own artifacts, nothing under `specfuse/` or `tests/`.
Per the dispatch contract this session ran no full suite, no coverage and no
`tier: broad` gate.

### feature_oracle: PASS

| Oracle | Command | Result | Exit |
|---|---|---|---|
| Gate `feature_oracle` | `python3 -m unittest tests.test_triage_severity_end_to_end -v -b` | `Ran 5 tests`, `OK` | 0 |
| T03's module | `python3 -m unittest tests.test_severity_rubric -v -b` | `Ran 10 tests`, `OK` | 0 |
| T04's module | `python3 -m unittest tests.test_triage_severity_write -v -b` | `Ran 7 tests`, `OK` | 0 |
| T05's module | `python3 -m unittest tests.test_triage_severity_classify -v -b` | `Ran 12 tests`, `OK` | 0 |
| Gate 1's module, unregressed | `python3 -m unittest tests.test_marker_dual_shape -v -b` | `Ran 11 tests`, `OK` | 0 |
| T03's unedited neighbours + the ratchet | `python3 -m unittest tests.test_provision_labels tests.test_label_provisioning_runner_contract tests.test_caller_check_ratchet -b` | `Ran 28 tests`, `OK` | 0 |
| Triage write path + skill contract | `python3 -m unittest tests.test_triage tests.test_triage_apply tests.test_triage_skill_contract tests.test_triage_skips_agent_escalations -b` | `Ran 40 tests`, `OK` | 0 |
| Provider, dial, invocation usage | `python3 -m unittest tests.test_agent_provider_triage tests.test_agent_policy_triage_dial tests.test_agent_invoke_usage -b` | `Ran 16 tests`, `OK` | 0 |
| Downstream marker readers | `python3 -m unittest tests.test_bug_lane_run tests.test_agent_state -b` | `Ran 36 tests`, `OK` | 0 |
| **Non-interference, by argv** | independent probe: `TriageProvider.execute` with an injected runner, five cases (A/B/C/D/E) | declares-own: **0** creates, **0** `--description`; declares-none: 4 creates all before the first `--add-label`; 3 issues: 1 listing, 4 creates | 0 |
| Rubric-reader branch table | `read_severity_rubric` over five label-set shapes | as tabulated above; **0** creates on every declares-own shape | 0 |
| Two-field marker byte-identity | `render_marker` over `CATEGORIES` × `CONFIDENCES` vs. the literal | 10 shapes, **0** mismatches; three-field form parses to `{'category','confidence','severity'}` | 0 |
| T03#2 single-listing-site | `grep -c '"label", "list"' specfuse/loop/labels.py` | `1` | 0 |
| T05#2 no second copy of the defaults | `grep -c "Minor impact\|Moderate impact\|Major impact\|Severe impact\|DEFAULT_SEVERITY_RUBRIC" specfuse/agent/triage_invoke.py` | `0` (negative observation) | 1 |
| `DEFAULT_SEVERITY_RUBRIC` definition sites | `grep -rn DEFAULT_SEVERITY_RUBRIC --include="*.py" specfuse/` | defined once, `specfuse/loop/labels.py:347` | 0 |
| T02H red-before | `git cat-file -e 8169640:tests/test_triage_severity_end_to_end.py` | `ABSENT` at the pre-unit tree | 1 |
| T02H harness rewrite | `git diff --stat 3f1c2f7 a9ca8f1 -- tests/test_triage_severity_end_to_end.py` | +172/−39; class renamed, T02H's test name absent at HEAD | 0 |
| Ratchet net effect | `git diff --stat 8169640..HEAD -- tests/test_caller_check_ratchet.py` | empty — added by T03, removed by `1a6a0d7` | 0 |
| Gate 2 source scope | `git diff --stat 8169640..HEAD -- specfuse/ tests/` | 4 source files, 4 test files, +955/−37 | 0 |
| Narrow tier for `close-intermediate` (`gate_set: plannext`) | `python3 .specfuse/scripts/lint_plan.py <feature_dir>` | reported in this close's RESULT block | — |
| Closing lint | `python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` | reported in this close's RESULT block | — |

**Driver broad runs, cited and not re-run.** Two `broad_run_result` events exist
for gate 2. The first, `2026-09-18T02:46:19.667559+00:00`, recorded `ok: false`
with `tests` failing on `test_the_baseline_has_not_silently_shrunk` and
`coverage` failing as a consequence. After `1a6a0d7`, the second,
`2026-09-18T02:56:51.893745+00:00`, recorded `ok: true`, `failing: []`, over the
18-tree digest pinned in `GATE-02.md`'s `broad_run:` block — the tree this close
runs against.
