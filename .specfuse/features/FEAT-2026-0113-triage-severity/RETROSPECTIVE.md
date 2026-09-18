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

## Gate 3

**What the gate set out to prove.** Issues already carrying a triage marker with
no `severity=` field can be re-read and labelled under an explicit mode, never as
part of a normal run. Eight units ran: T07 the walking skeleton (single issue,
`_amend_marker` and `_STUB_SEVERITY` stubbed); T08 the selection predicate and
`amend_marker_severity`; T07H (inserted mid-gate) the console-script provenance
guard; T09 the bulk write path, marker first and label second; T10 the real run
shape — rubric once, classify each, write only under `--apply`; T11, a `type: human`
read-only dry run against the repository where the 31 were measured; T08H (inserted
mid-gate, *because* of what T11 found) making `--limit` bound candidates rather than
the listing window; and T10H (inserted mid-gate, because the caller ratchet went red
on the broad run) removing `backfill_severity`, the now-superseded tracer bullet.
All eight are `status: done`. Measurements are in `## Measurements — gate 3`; cost
is reconciled under `## Cost analysis`, which reconciles the whole feature.
Per-criterion oracle, kind and state for all 37 acceptance criteria are in
`GATE-03-CRITERIA.md`.

### The load-bearing question: are the measured 31 routable now?

**No. They are now *reachable*, and they are still not *routable*.** The distinction
is the whole finding, and it is the answer this close exists to give honestly rather
than to soften.

**Reachable — yes, and this is new.** `PLAN.md` measured 31 bug-marked issues carrying
a marker and no severity label, stranded permanently because the marker is the
idempotency key and it was already written. `list_untriaged` excludes them correctly
and always will. `list_severity_backfill_candidates` is the inverse selection, and
`T11` ran it against that repository read-only: **84 candidates at `--limit 200`, 74
at `--limit 100`, against 191 open issues** — a superset of the 31. Before this gate
nothing could name them; now a bounded, dry-run-by-default command does.

**Routable — no, for a reason this feature cannot fix from inside itself.** Routing
means `rules.bugs.min_severity` stops failing closed on them, which requires a
severity to be *written*, which requires the classifier to *answer*. In that
repository it mostly cannot. Its own scheme is `severity:critical` /
`severity:major` / `severity:minor`; only `critical` is in
`agent_policy.SEVERITY_VALUES`, so `read_severity_rubric` returns a **single-entry
rubric**, and `classify_severity` fails closed on every value outside it. `T11`'s
recorded evidence is the measurement: of the 5 issues its dry run selected,
**1 classified (`#1883`, `severity=critical`) and 4 returned "no usable
classification, skipped"**. Re-measured independently in this close (probe case B):
a repository declaring `critical`/`major`/`minor` yields `rubric == ['critical']`, and
a repository whose scheme is fully disjoint from the vocabulary (case C) yields `{}`
and a one-call no-op run.

So the honest statement is: **backfill ships able to select the 31 and able to route
only the subset a one-word rubric can classify.** That is not a surprise and not a
regression — `GATE-03.md`'s arm-checkpoint Q4 declared it in advance ("backfill ships
before it can unstrand the 31 measured issues in the repository that motivated the
feature. That is accepted, not overlooked"), and named the two changes that do
unstrand them: **#3355**, a shipped default alias table, and **#3356**, an opt-in
mode that harmonises a repository's own labels onto the standard vocabulary. #3356
reuses this gate's selection and write machinery, which is what this gate bought.

**And there is a second, sharper reason not to widen the rubric first.** `T11`'s run
surfaced it and it is not hypothetical: **#1902, #1895 and #1893 already carry
`severity:minor` / `severity:major` / `severity:major` — labels a person applied —
while their markers carry no `severity=`.** The predicate selects on the *marker*, so
a human-labelled issue is a backfill candidate. Today that is masked, because all
three resolve to "no usable classification" against the single-entry rubric. **It
stops being masked the moment #3355 lands**: the classifier could answer `high` for an
issue a person labelled `minor`, and the write path would add `severity:high`
alongside the human's `severity:minor` — two severities on one issue, the agent's
silently winning at the floor because `read_severity_label` returns the first it
recognises. The shape of the fix is *reconciliation* — an issue whose label already
states a severity has its marker written **from that label**, not from a fresh
classification — and no unit in this gate builds it. It is recorded on #3355 as a
prerequisite and re-stated here so the terminal verdict does not read as "done".

### Was a repository's own severity scheme disturbed? (criterion 3)

**No. Zero `gh label create` calls and zero label-description writes against any
repository that declares a `severity:*` scheme of its own, measured by argv over the
whole call sequence — including the write path.** Gate 2 established this contract
for the normal triage run; this is the same question asked again of the *new* run
shape, by an independent in-session probe driving `run_backfill` with an injected
runner, not by re-reading T10's assertions.

| Case | Repository's own `severity:*` labels | `apply` | Rubric | `gh label create` | argv with `--description` | Marker before label |
|---|---|---|---|---|---|---|
| A | specfuse's own four, all described | yes | its own four | **0** | **0** | yes (idx 4 < 5) |
| B | `critical`/`major`/`minor`, all described | yes | `['critical']` | **0** | **0** | yes (idx 4 < 5) |
| C | `p0`/`p1` — disjoint from the vocabulary | yes | `{}` | **0** | **0** | n/a — no writes at all |
| D | **none at all** (control) | yes | shipped default four | 4 | 4 | yes (idx 8 < 9) |
| E | specfuse's own four | **no** | its own four | **0** | **0** | n/a — zero `gh issue edit` |

**Declares-own totals: `gh label create` = 0, `--description` argv = 0.** Case D is
the control that proves the probe can see a create when one occurs — four creates,
all carrying `--force`, all before the first `--add-label` (#3244's ordering), and
the rubric-source precedence intact. Case C is the interesting one: a repository whose
whole scheme lies outside `SEVERITY_VALUES` gets an empty rubric, and the **entire**
call sequence is one `gh label list` — no candidate listing, no `claude` invocation,
no write. Inert for that repository, and still untouched. That is the correct
precedence and it is the same one gate 2 recorded.

Case E is the shape `T11` ran against a real repository: `apply=False` issues zero
`gh issue edit` calls of any kind.

### `severity_backfill.py` diffed across its declaring units (criterion 5)

Gate 2's durable lesson applied to gate 3: a shared `produces:` entry is the signal,
"extends, does not rewrite" is a wish rather than a guard, and a per-gate criteria
artifact can otherwise record a green with no test behind it. **Six units declare
`specfuse/agent/severity_backfill.py` in `produces:`**, not the three the close body
named — T07, T07H, T09, T10, T08H and T10H — so all five consecutive pairs are
diffed below, with the three named pairs stated in full.

| Pair | Commits | Diff | What the later unit replaced |
|---|---|---|---|
| T07 → T07H | `deec4ce` → `f0833ab` | +2/−0 | Nothing. Purely additive: the `warn_if_out_of_tree` import and its call as `main()`'s first statement. |
| **T07 → T09** | `deec4ce` → `d859fc6` | **+74/−15** | **One deletion, and it was the named one.** `_amend_marker` — T07's single permitted stub, named in T07#4 for exactly this — is deleted, and `backfill_severity`'s one call site is switched to `triage.amend_marker_severity`. Everything else is additive (`apply_severity_backfill`, the docstring paragraph describing it). No assertion of T07's was replaced: T07's four tests all still existed and ran green at this commit. |
| **T09 → T10** | `d859fc6` → `905d4dc` | **+129/−24** | **T07's CLI contract, in full.** `build_parser` loses its positional `issue` argument and gains `--limit`; `main()` stops calling `backfill_severity` and calls the new `run_backfill`; `print(json.dumps(report))` is replaced by `_print_run_report`'s line-per-issue output. The module docstring is rewritten around the new shape. `backfill_severity` itself is left in place and **orphaned** — reachable only from T07's test — which the docstring records honestly ("`run_backfill` does not call it and does not share its stub"). No test of T09's or T07's was edited; `apply_severity_backfill` is untouched and becomes `run_backfill`'s one write call site. |
| T10 → T08H | `905d4dc` → `0d9a400` | +10/−0 | Nothing replaced. Additive: the zero-candidate report line in `_print_run_report`. The `--limit` semantics fix itself is in `triage.py`, not here. |
| **T08H → T10H** | `0d9a400` → `96c0f04` | **+0/−61** | **`backfill_severity` and its docstring paragraph, deliberately and with coverage checked first.** Deletions only. T10H was dispatched *because* the caller ratchet failed the broad run on exactly this symbol; its body checked where the behaviour was covered before deleting (#3328's ruling), named `test_severity_backfill_apply.py:32` as the survivor, and its criterion 5 required that survivor to be *shown running*, not assumed. `git diff 29f4ef2 96c0f04 -- tests/test_caller_check_ratchet.py` is empty — no BASELINE waiver was minted — and neither `test_severity_backfill_apply.py` nor `test_severity_backfill_run.py` appears in its commit stat, so the deletion did not accommodate itself by editing its own replacement. |

**The diff is what covers what a grep cannot.** `T09`'s `grep -c "def _amend_marker"`
returning `0` is evidence for the T07→T09 pair and for nothing else; the T09→T10 pair
— where an earlier unit's entire command-line contract was replaced — has no grep
behind it at all, and only the diff shows it.

### The gate's own findings

Three, all surfaced by this close's own re-runs rather than by any attempt.

**1. `T09`'s criterion 4 is not met, and was recorded green.** It requires
`grep -c '"issue", "list"'` **and** `grep -c "run_claude"` over
`specfuse/agent/severity_backfill.py` to *both* report `0` at T09's tree. Measured:
`run_claude` → `0`, but `"issue", "list"` → **1**, at T09's tree and still at HEAD
(`specfuse/agent/severity_backfill.py:218`, inside `_find_issue`). The criterion's
*intent* holds — `apply_severity_backfill`, the write path, neither lists nor
classifies — but its *oracle* is module-scoped while its claim is function-scoped,
and a module-scoped grep was always going to see T07's tracer-bullet helper sitting
next door. This is recorded `state: fail` in `GATE-03-CRITERIA.md` and carries a
`FOLLOW-UPS.md` entry.

**2. Two private tracer-bullet symbols are dead at HEAD, and no guard can see them.**
`_find_issue` has no caller repo-wide (`grep -rn _find_issue --include="*.py" .` → one
hit, its own definition) — T10H removed `backfill_severity`, its only caller, and
left it. `_STUB_SEVERITY` has no reader, and its `#:` comment still reads "Stands in
for T10's classification session (gate 3, walking skeleton)" — a comment describing a
stub for a path that shipped. **The caller ratchet is public-symbol-only**, which is
why it caught `backfill_severity` on the broad run and cannot catch these. The gate's
cleanup was correct as far as its guard could see, and its guard could not see the
whole tracer bullet.

**3. The gate's `feature_oracle` no longer asserts the thing `GATE-03.md` says it
drives.** `GATE-03.md`'s Definition of done describes the oracle as driving *the pair*
— "a backfill that runs, and a normal run that does not … Both halves are in one
module because the milestone is the pair". At HEAD
`tests/test_severity_backfill_end_to_end.py` holds **two tests, and both are
structural**: one greps `run.py`, one diffs `pyproject.toml`. The behavioural half
was deleted by T10H — legitimately, with its replacement named and verified — but
nothing moved an end-to-end assertion back into the oracle's own module. So the
oracle exits 0 (verified fresh this session, `Ran 2 tests`, `OK`) while asserting only
the negative half of the milestone. The *behaviour* is covered — `test_severity_backfill_run.py`
(7 tests) and `test_severity_backfill_apply.py` (4 tests) both run green, and this
close's argv probe re-measures the full sequence independently — but the gate's own
declared feature-level question is no longer being asked by the command declared to
ask it. This carries a `FOLLOW-UPS.md` entry.

This is gate 2's lesson recurring with a twist worth naming: gate 2's deletion was
*silent* and unauthorised; gate 3's was *reasoned, authorised and coverage-checked*,
and still hollowed the gate's feature-level oracle — because the authorisation was
written against "is this behaviour covered somewhere?" and not against "does the
gate's declared oracle still ask the gate's declared question?"

### Gate 1's carried residual (criterion 4)

**Partly discharged, and re-carried narrower — by name.**

Gate 1's residual, restated rather than retired by gate 2's close, was: *no oracle in
gates 1 and 2 read a real issue body outside this repository.* That is confirmed —
every gate-1 and gate-2 oracle injects a runner, so the `gh label list` JSON, the
classification answer and every write were authored by a test.

**`T11` is the unit placed to change that, and it did.** It ran
`python3 -m specfuse.agent.severity_backfill --repo <repo> --limit 5` against the real
repository where the 31 were measured, read real issue bodies, real markers and real
label sets, and pasted the selection into `GATE-03-REVIEW.md` with the marker line
each row was selected on. It did more than discharge the residual: it found two
defects no injected runner had — `--limit` bounding the listing window instead of the
candidate count, and a zero-candidate run printing nothing — and those produced `T08H`.
It also found the human-applied-severity collision above, which is the single most
consequential thing anyone learned in this gate.

**What is re-carried, narrowly:** `--apply` has never been passed against a real
repository. Every *write* in this feature — every `gh issue edit --body`, every
`--add-label` — has only ever been observed against an injected runner. `T11`'s
Do-not-touch forbade `--apply` deliberately ("the writing run is the operator's
decision after the close"), so this is by design, not an omission. But the residual
should not be recorded as closed: **the read half is discharged; the write half is
not, and the first real `--apply` run is an operator action with no oracle behind it
yet.**

### Per-criterion result

**36 of 37 `state: pass`, 1 `state: fail`** — each against an oracle re-run fresh in
this session. `GATE-03-CRITERIA.md` carries the oracle, `kind`, `state`, proving SHA
and attempt for each; the summary:

| Unit | Criteria | Result | Proved by |
|---|---|---|---|
| T07 | #1–#4 | 4/4 pass | `git cat-file -e be190bc:` for the red-before; the unit's own tree extracted with `git archive deec4ce \| tar -x` and run there (3/4 green, the 4th needs a `.git` the archive has none of); at HEAD the ordering claim is carried by `test_severity_backfill_apply.py:32` and by the argv probe, because T10H deleted the named test |
| T08 | #1–#5 | 5/5 pass | `tests.test_severity_backfill_marker` (11 cases, 4 of them one-per-exclusion); `grep -c '"issue", "list"' specfuse/loop/triage.py` → `1`; `grep -c "specfuse:triage"` → `3`; `grep -rn "def amend_marker_severity" specfuse/` → one hit |
| T07H | #1–#5 | 5/5 pass | the driver's `baseline_attribution` event for the red-before, re-derived structurally from `36f41e4`'s 7-script/6-module mismatch; `tests.test_build_provenance` (13 cases); the tuple read 6 → 7 with the six originals byte-identical; #5 is the driver's broad run, cited |
| T08H | #1–#5 | 5/5 pass | `tests.test_severity_backfill_limit` (4 cases); independent probes for paging (84 issues, candidates at 80–84, `limit=3` → 3), exhaustion (1 finite listing call) and the zero-candidate line naming repository and limit |
| T09 | #1–#3 pass, **#4 fail** | 3/4 | `tests.test_severity_backfill_apply` (4 cases) and the argv probe for #1–#3; **#4 measured `1`, not `0`** — see finding 1 above |
| T10 | #1–#5 | 5/5 pass | `tests.test_severity_backfill_run` (7 cases); the five-case argv probe; `grep -c "def classify_severity"` → `0` and `grep -c '"label", "create"'` → `0`, both negative observations; the fail-closed path observed rejecting a purpose-built bad classification answer |
| T10H | #1–#6 | 6/6 pass | the driver's `broad_run_gate_failure` event for the red-before; `tests.test_caller_check_ratchet` (5 cases) green at HEAD with an **empty** BASELINE diff; `git show --stat 96c0f04` showing deletions only and neither replacement test module edited; #6 is the driver's broad run, cited |
| T11 | #1–#3 | 3/3 pass | the `evidence:` field at HEAD, the `## Live-corpus dry run (T11, 2026-09-18)` paste in `GATE-03-REVIEW.md` with per-row markers and `EXIT=0`, and the named surprise (#1902/#1895/#1893) the unit existed to surface |

Every `kind` is `narrow` except T07H#5 and T10H#6, which name the full `tests` and
`coverage` gates and are recorded `broad` and cited from the driver's once-per-gate
run rather than re-executed here.

### Deferred verification

`(one criterion is recorded not met; nothing is deferred unverified)`

Thirty-six criteria were verified in this session against a command with an observed
exit code, and the thirty-seventh was verified and **failed**. Four things are worth
stating alongside that, none of them a deferred criterion:

- **No `--apply` has ever run against a real repository.** See criterion 4 above. This
  is a scope statement and an operator prerequisite, not an unverified criterion.
- **The rubric-vocabulary mismatch is measured, not assumed.** A repository on an
  aliased scheme is readable by the floor (`rules.bugs.severity_aliases`, #3349) and
  largely invisible to the classifier. Gate 2 recorded this as a coverage hole; gate 3
  met it in the wild on the first live run and it is what makes the 31 unroutable.
- **`PLAN.md`'s task graph does not record gate 3's three mid-gate insertions.** T07H,
  T08H and T10H are `status: done` with their own commits, and `PLAN.md`'s
  `## Mid-gate insertions` section records only gate 1's T01H. The `# type: human`
  comment in the gate-3 graph also now sits above `T10H`, an implementation unit,
  rather than above `T11`, the human one — an insertion landed between the comment and
  the entry it annotates. Cosmetic in the graph, misleading to a reader, and not
  corrected here: `PLAN.md` is this close's Do-not-touch surface beyond its `status`.
- **The broad tier ran, and it was the driver that ran it.** Per the dispatch contract
  this session ran no full suite, no coverage and no `tier: broad` gate. The broad run
  is cited below, including the one that failed.

### Consumer-visible contract changes

One new console script and four new public functions; no removal, no rename, and
nothing an existing consumer depends on changes behaviour. `backfill_severity` was
added and removed **within this gate** and never appeared in a release, so it is not a
breaking removal and is not enumerated as one.

- **`added`** — `specfuse-backfill-severity`, a new console script
  (`specfuse.agent.severity_backfill:main`). `pyproject.toml` gains exactly one
  `[project.scripts]` line and no dependency change. Deliberately **not** a flag on
  `specfuse-agent`: a bulk issue-mutating maintenance mode behind the binary an
  unattended run uses is one argv typo from the wrong thing, and `specfuse/agent/run.py`
  is not edited by this gate at all (measured as an empty diff, not asserted).
- **`added`** — `specfuse.agent.severity_backfill.run_backfill(runner, repo,
  working_dir, *, apply=False, limit, model, effort)`, returning
  `{"rubric", "candidates", "rows", "reason"}`.
- **`added`** — `specfuse.agent.severity_backfill.apply_severity_backfill(runner, repo,
  decisions)`, the bulk decision-list write path, returning one row per decision.
- **`added`** — `specfuse.loop.triage.list_severity_backfill_candidates(runner, repo,
  limit)`: open, marked, severity-less issues, `limit` bounding **candidates** and not
  the listing window, paged until found or exhausted.
- **`added`** — `specfuse.loop.triage.amend_marker_severity(body, severity)`: in-place
  marker amendment, returning its input unchanged for a body with no marker or one
  already carrying `severity=`.

**Behaviour a consumer should know before running it:** the default is a **dry run** —
`--apply` is required to write anything, and without it the command issues zero
`gh issue edit` calls of any kind. A repository that declares its own `severity:*`
scheme has **nothing created and nothing overwritten**, measured by argv across the
whole call sequence (table above). A repository whose scheme shares no value with
`SEVERITY_VALUES` gets an empty rubric and the run is a no-op that says so rather than
guessing. `CHANGELOG.md`'s `Unreleased` section gains the corresponding entry.

### Failure-class breakdown

One non-passing attempt and three mid-gate insertions. The attempt table is the small
half of this story; the insertions are the large half, and two of the three were
triggered by a guard or a human rather than by a failing unit.

| Class | Count | Detail |
|---|---|---|
| Failed attempt | 1 | `T09` attempt 1, `$0.688403`, signature `FAIL: test_import_exposes_backfill_severity_and_the_named_stub` — **a sibling unit's assertion**, T07's, which required `_amend_marker` to be gone. T09's own four tests passed in the same run. It re-ran and passed. The unit was correct about what to build and wrong about what else it had to remove; T07's criterion 4 was the thing that told it, which is that criterion working. |
| Pre-existing gate failure | 1 | `preexisting_gate_failure` at 11:18, attributed to `T09`: `tests` red on `test_the_declared_console_scripts_match_the_wired_set`, `coverage` red downstream (`no_gate_marker`). **Not T09's defect** — T07 registered a console script and never wired the module into `test_build_provenance.py`'s `ENTRY_MODULES`. Resolved by inserting `T07H`. |
| Broad-run gate failure | 1 | `broad_run_gate_failure` at 11:50: `tests` red on `test_no_symbol_outside_the_baseline_is_called_only_by_tests` (the caller ratchet), `coverage` red downstream. `backfill_severity` had been dead since T10 landed and nothing noticed until the once-per-gate broad run. Resolved by inserting `T10H`. The re-run at 12:00:11 is `ok: true`, `failing: []`. |
| Human step | 1 | `human_step_required` at 11:29 for `T11`. By design — the driver halts and dispatches nothing. Cost `$0.00` in agent budget. |
| Defect found by a human, not a gate | 2 | `T11`'s live run found `--limit` bounding the listing window (`--limit 5` → 0 candidates, `--limit 100` → 74, `--limit 200` → 84, against 191 open issues) and a zero-candidate run printing nothing. **Neither was visible to any injected-runner test in the gate**, because a fixture returns the issues the fixture chose. Resolved by inserting `T08H`. |
| Verification failure | 0 | No attempt was refused by the driver's re-verification. |
| Guard refusal | 0 | No `produces_not_in_diff`, no closing-deliverable refusal. |

**Three of gate 3's four "failures" were caught by something other than a unit
attempt** — two by repo-wide guards on the broad run, one by a person running the
thing against reality. The one failing attempt cost `$0.69`; the three insertions
cost `$2.43` together and each bought a defect that would otherwise have shipped.
That ratio is the argument for the `type: human` unit and for the once-per-gate broad
run, in one table.

### Lessons promoted

Three durable rules go to `.specfuse/LEARNINGS.md`, tagged `[FEAT-2026-0113/G3-CLOSE]`:
(1) a walking skeleton is deleted as a *unit*, not as a symbol, and a public-symbol
ratchet cannot tell you when you have finished; (2) a criterion whose claim is
function-scoped and whose oracle is module-scoped passes or fails for reasons
unrelated to the claim — scope the grep to the thing you are asserting about; (3) an
authorised deletion that checks "is this behaviour covered somewhere?" can still
hollow the gate's own `feature_oracle`, so the question to ask before deleting from an
oracle's module is whether the oracle still asks the gate's declared question.

One draft-time candidate was **not** promoted: "run it against reality before you
believe your fixtures" is already `close-discipline.md` §2's `type: human` unit and
this gate used it correctly. The lesson there is not a new rule, it is the existing
rule paying out — recorded in the failure-class table instead.

## Measurements — gate 3

Every command below ran fresh in this close session, from the working tree, with the
repository venv (`.venv/bin/python`) and no git mutation — only read-only inspection
(`log`, `show`, `diff`, `cat-file`, `archive`), which criterion 5 requires by
construction. Working-tree source state equals HEAD
`0b408300ea99c136945d1f44e210d3620f7edd6a`: `git diff HEAD -- specfuse/ tests/
pyproject.toml` is empty, so the only uncommitted changes are this close's own
artifacts. Per the dispatch contract this session ran no full suite, no coverage and
no `tier: broad` gate.

### feature_oracle: PASS

| Oracle | Command | Result | Exit |
|---|---|---|---|
| Gate `feature_oracle` | `python3 -m unittest tests.test_severity_backfill_end_to_end -v -b` | `Ran 2 tests`, `OK` — **and see finding 3: two structural tests, no end-to-end assertion** | 0 |
| T08's module | `python3 -m unittest tests.test_severity_backfill_marker -b` | `Ran 11 tests`, `OK` | 0 |
| T09's module | `python3 -m unittest tests.test_severity_backfill_apply -b` | `Ran 4 tests`, `OK` | 0 |
| T10's module | `python3 -m unittest tests.test_severity_backfill_run -b` | `Ran 7 tests`, `OK` | 0 |
| T08H's module | `python3 -m unittest tests.test_severity_backfill_limit -b` | `Ran 4 tests`, `OK` | 0 |
| T07H's module | `python3 -m unittest tests.test_build_provenance -b` | `Ran 13 tests`, `OK` | 0 |
| T10H's guard | `python3 -m unittest tests.test_caller_check_ratchet -b` | `Ran 5 tests`, `OK` | 0 |
| Gate 3 combined | the six modules above in one invocation | `Ran 44 tests`, `OK` | 0 |
| Gates 1 and 2 unregressed | `python3 -m unittest tests.test_marker_dual_shape tests.test_triage_severity_end_to_end tests.test_severity_rubric tests.test_triage_severity_write tests.test_triage_severity_classify -b` | `Ran 45 tests`, `OK` | 0 |
| **Non-interference, by argv** | independent probe: `run_backfill` with an injected runner, five repository shapes (A/B/C/D/E), full call sequence printed | declares-own: **0** creates, **0** `--description`; declares-none control: 4 creates, all before the first `--add-label`; marker before label on every writing case; dry run: **0** `gh issue edit` | 0 |
| Fail-closed, negative observation | same probe handed a JSON classification answer instead of a marker | `classify_severity` → `None` for every candidate; **0** `gh issue edit` under `apply=True` | 0 |
| Zero-candidate report | independent probe, 5 unmarked issues, stdout captured | `no severity-backfill candidates found in <repo> under limit=5` — names repository and limit | 0 |
| Paging, candidate-bounded | independent probe: 84 issues, candidates at positions 80–84, `limit=3` | 3 returned; `gh issue list` window requested `100`, i.e. `_BACKFILL_PAGE_SIZE`, not the limit | 0 |
| Exhaustion terminates | independent probe: 13 issues, 2 candidates, `limit=50` | 2 returned after exactly 1 listing call | 0 |
| Dry-run print | independent probe, 3 candidates, `apply=False` | `0` `gh issue edit`; one line per issue | 0 |
| T09#4, first grep | `grep -c '"issue", "list"' specfuse/agent/severity_backfill.py` | **`1`** — criterion requires `0` | 0 |
| T09#4, at T09's own tree | `git show d859fc6:specfuse/agent/severity_backfill.py \| grep -c '"issue", "list"'` | **`1`** — criterion requires `0` | 0 |
| T09#4, second grep | `git show d859fc6:… \| grep -c run_claude` | `0` (holds) | 1 |
| T09#4, stub gone | `grep -c "def _amend_marker" specfuse/agent/severity_backfill.py` | `0` (negative observation) | 1 |
| `amend_marker_severity` definition sites | `grep -rn "def amend_marker_severity" specfuse/` | one hit, `specfuse/loop/triage.py:418` | 0 |
| Dead private symbols | `grep -rn "_find_issue" --include="*.py" .` / `grep -rn "_STUB_SEVERITY" specfuse/ tests/` | **1 hit each — their own definitions.** No caller, no reader | 0 |
| T10#5 no create site | `grep -c '"label", "create"' specfuse/agent/severity_backfill.py` | `0` (negative observation) | 1 |
| T10#2 no second classifier | `grep -c "def classify_severity" specfuse/agent/severity_backfill.py` | `0` (negative observation) | 1 |
| T10H#2 symbol removed | `grep -c "def backfill_severity" specfuse/agent/severity_backfill.py` | `0` (negative observation) | 1 |
| T07#2 conductor untouched | `grep -c severity_backfill specfuse/agent/run.py`; `git diff main -- specfuse/agent/run.py` | `0`; empty diff at both T07's tree and HEAD | 1; 0 |
| T08#3/#4 single-site greps | `grep -c '"issue", "list"' specfuse/loop/triage.py`; `grep -c "specfuse:triage" specfuse/loop/triage.py` | `1`; `3` | 0 |
| **Criterion 5, the five pair diffs** | `git --no-pager diff <a> <b> -- specfuse/agent/severity_backfill.py` for `deec4ce→f0833ab`, `deec4ce→d859fc6`, `d859fc6→905d4dc`, `905d4dc→0d9a400`, `0d9a400→96c0f04` | +2/−0, +74/−15, +129/−24, +10/−0, +0/−61 — tabulated above with what each replaced | 0 |
| T10H BASELINE untouched | `git diff 29f4ef2 96c0f04 -- tests/test_caller_check_ratchet.py` | empty — no waiver minted | 0 |
| T10H replacements unedited | `git show --stat 96c0f04` | 4 files; neither `test_severity_backfill_apply.py` nor `test_severity_backfill_run.py` among them | 0 |
| Red-before, five modules | `git cat-file -e <parent>:tests/test_severity_backfill_{end_to_end,marker,apply,run,limit}.py` | ABSENT at `be190bc`, `deec4ce`, `f0833ab`, `d859fc6`, `79b9b95` respectively | 1 (×5) |
| T07's tree, run in place | `git archive deec4ce \| tar -x -C <scratch>` then the three non-`.git` tests | `Ran 3 tests`, `OK` — including `test_marked_issue_without_severity_is_amended_then_labelled` | 0 |
| Gate 3 source scope | `git diff --stat 3ec5343 HEAD -- specfuse/ tests/ pyproject.toml` | 2 source files + `pyproject.toml`, 6 test files, +1067/−1 | 0 |
| Closing lint | `python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` | reported in this close's RESULT block | — |
| Narrow tier (`gate_set: plannext`) | `python3 .specfuse/scripts/lint_plan.py <feature_dir>` | reported in this close's RESULT block | — |

**Driver broad runs, cited and not re-run.** Two `broad_run_result` events exist for
gate 3. The first, `2026-09-18T11:50:55.551147+00:00`, recorded `ok: false` with
`tests` failing on `test_no_symbol_outside_the_baseline_is_called_only_by_tests` and
`coverage` failing as a consequence. After `T10H` (`96c0f04`), the second,
`2026-09-18T12:00:11.966737+00:00`, recorded `ok: true`, `failing: []`, over the
18-tree digest pinned in `GATE-03.md`'s `broad_run:` block — the tree this close runs
against.

## Cost analysis — the feature against `planned_cost_usd`

Reconciled against each unit's `planned_cost_usd` and the 26 `attempt_outcome` records
in `events.jsonl` — not estimated. `PLAN.md` declares `planned_cost_usd: 58.50`.
Total agent spend across the whole feature before this close's own dispatch:
**$34.756474**.

### Gate 3, per unit

| Unit | Planned | Attempts | Actual | Ratio | Note |
|---|---|---|---|---|---|
| `T07` | $3.00 | 1 (passed) | $0.865191 | 0.29× | 171.6 s; the walking skeleton |
| `T08` | $3.00 | 1 (passed) | $0.523399 | 0.17× | 104.2 s |
| `T07H` | $1.00 | 1 (passed) | $0.256693 | 0.26× | 30.2 s; **inserted mid-gate** after a pre-existing gate failure |
| `T09` | $3.00 | 2 (failed, passed) | $1.427305 | 0.48× | $0.688403 discarded, $0.738902 passed; 317.0 s total |
| `T10` | $3.50 | 1 (passed) | $1.124219 | 0.32× | 193.5 s |
| `T08H` | $1.50 | 1 (passed) | $0.706654 | 0.47× | 124.3 s; **inserted mid-gate** after T11's live run |
| `T10H` | $1.50 | 1 (passed) | $0.462125 | 0.31× | 69.2 s; **inserted mid-gate** after the broad run went red |
| `T11` | $0.50 | human, 0 agent attempts | $0.00 | — | operator time; the $0.50 stands in so a zero does not read as unestimated |
| **Gate 3 implementation** | **$17.00** | **8** | **$5.365586** | **0.32×** | 1010 s of agent time, ~16.8 min |
| `G3-CLOSE` | $5.00 | this one | — | — | |

### The feature

| Phase | Planned | Actual | Ratio |
|---|---|---|---|
| Gate 1 implementation | $6.00 | $1.615569 | 0.27× |
| Gate 1 closing (`G1-CLOSE-INTERMEDIATE` + `G1-PLAN`) | $10.50 | $8.918661 | 0.85× |
| Gate 2 implementation | $13.50 | $6.539607 | 0.48× |
| Gate 2 closing (`G2-CLOSE-INTERMEDIATE` + `G2-PLAN`) | $10.50 | $12.317052 | 1.17× |
| Gate 3 implementation | $17.00 | $5.365586 | 0.32× |
| `G3-CLOSE` | $5.00 | this session | — |
| **Feature, excluding this close** | **$62.50** | **$34.756474** | **0.56×** |

**Reconciliation.**

- **`planned_cost_usd: 58.50` is $4.00 short of what was actually planned.** Gate 3's
  three mid-gate insertions carry their own `planned_cost_usd` in their frontmatter —
  T07H $1.00, T08H $1.50, T10H $1.50 — and `PLAN.md`'s total was never revised to
  absorb them, exactly as gate 2's $13.50 was absorbed when `G1-PLAN` drafted it. The
  honest planned total is **$62.50**. Against the declared $58.50 the feature is at
  0.59×; against the real one, 0.56×. Either way it comes in well under, for the third
  gate running.
- **Implementation is cheap and the closing sequence is not.** Across three gates,
  implementation cost $13.52 against $36.50 planned (0.37×) while the closing units
  cost $21.24 against $26.00 planned (0.82×) — **61% of this feature's spend is
  closing ceremony**, and that is before this terminal close. The pattern is not a
  defect (the closes are what found T06's deleted assertion, and what found the three
  findings above), but it is the number `planning-discipline.md` §5's floors should be
  read against: the floors are close to right and the per-unit estimates are roughly
  3× too high.
- **Gate 3 discarded 13% of its spend, against gate 2's 47%.** $0.688403 of $5.365586,
  on one attempt, for one cause — T09 not removing a sibling's stub. Gate 2's tracer
  bullet lesson held: `T07` turned the `feature_oracle` green before any unit had to be
  verified against it, and no unit in gate 3 spun on an unsatisfiable oracle. The $0.31
  that bought that lesson in gate 2 saved something like $3 here.
- **The three insertions cost $2.425472 and each bought a shipped defect.** T07H a
  provenance guard blind to a new entry point; T08H a `--limit` that selected the wrong
  84 issues and a run that reported nothing; T10H a dead public symbol. None was found
  by the unit that caused it.
- **The arm predicate keeps firing `budget_projection` against the wrong denominator.**
  At 11:18 it fired: "projected spend $43.47 (spend $31.47 + remaining $12.00) exceeds
  2.0x baseline planned total $20.50 (cap $41.00)". `PLAN.baseline.json` records gates
  2 and 3 as `"work_units": []` — both were drafted after the snapshot — so the cap is
  computed from gate 1 alone. By 11:50 the same class read `clean` at $39.29 purely
  because the denominator never moved and the numerator happened to dip. **Gate 2's
  close recorded this and it fired again in gate 3**, which makes it a standing defect
  in the predicate's input rather than an observation: a feature that plans gate N+1
  during gate N can never have a baseline that covers it.
- **The prep-halt lesson held.** `G2-CLOSE-INTERMEDIATE`'s `$0.00` halt taught that
  `oracles:` takes a `verification.yml` **set** name; this WU's frontmatter carries the
  comment recording it and `oracles: [oracles]`, and this close dispatched first try.

## Verdict — FEAT-2026-0113, terminal

`not_met`. One acceptance criterion in this gate is measured failing, and the
feature's own motivating question is answered "not yet" on real evidence rather
than on test doubles. Both are recorded in `FOLLOW-UPS.md`; neither is softened
here. Advisory — the judge session decides, on `## Measurements` and the
per-criterion state, not on this section.

**Did this feature make the measured 31 routable?** **No.** They are *reachable* for
the first time — `list_severity_backfill_candidates` selects 84 of them at
`--limit 200` against 191 open issues in the repository where they were measured,
verified by `T11`'s read-only live run, where before this feature nothing could ever
name them again. They are not *routable*, because routing needs a severity written and
the classifier mostly cannot answer: that repository declares
`severity:critical`/`major`/`minor`, only `critical` is in `SEVERITY_VALUES`, and
`T11` measured **1 of 5 sampled candidates classified, 4 skipped as "no usable
classification"**. Re-measured in this close against an injected runner: that scheme
yields a one-word rubric, and a fully disjoint scheme yields a no-op. `#3355` (a
shipped default alias table) and `#3356` (harmonising a repository's own labels onto
the vocabulary) are what unstrand them, and `#3356` reuses this gate's selection and
write machinery.

**What this feature did deliver, and it is not small.** Triage now assesses and records
a severity for every new issue — marker first, label projected after — in both
repository shapes, without creating or overwriting a single label in a repository that
declares its own scheme (measured by argv across the whole call sequence, twice, on two
different run shapes). A bounded, dry-run-by-default backfill command exists and has
been run against reality. And the selection predicate has met real issue bodies, which
is how the one genuinely dangerous thing here was found before anyone wrote with it:
**three of the five issues the live run selected already carry a severity a person
applied**, and once the rubric widens, backfill would contradict that human's judgment
by adding a second severity label beside theirs.

**What is not done, by name.** `T09`'s criterion 4 is not met and the tracer-bullet
residue behind it (`_find_issue`, `_STUB_SEVERITY`) is dead in the shipped module. The
gate's own `feature_oracle` passes while asserting only the structural half of the
milestone `GATE-03.md` declares it drives. `--apply` has never run against a real
repository. And the reconciliation case — write the marker *from* an existing human
label rather than from a fresh classification — is a prerequisite for `#3355`, not a
nicety.
