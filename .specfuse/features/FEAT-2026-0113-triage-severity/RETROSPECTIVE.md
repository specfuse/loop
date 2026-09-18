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
