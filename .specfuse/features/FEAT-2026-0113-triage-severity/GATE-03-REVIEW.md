---
gate: 3
drafted_by: FEAT-2026-0113/G2-PLAN
open_questions:
  - "Q1 (T07, T10): the mode is a flag on `specfuse-agent` (`--backfill-severity`), not its own console script. Cheaper to add, and it shares the conductor's repo detection and branch restore — but it puts a bulk issue-mutating maintenance mode behind the same binary an unattended run uses. Should it be its own entry point instead?"
  - "Q2 (T10 criterion 4): dry run is the default and `--apply` is required to write. That makes the first invocation always safe and the real one always deliberate, at the cost of a second command. Is the extra step worth it, or should `--backfill-severity` write and `--dry-run` opt out?"
  - "Q3 (T08 criterion 3): `--limit` bounds the run, and the draft sets no default below `DEFAULT_LIST_LIMIT` (100). The measured backlog is 31. Should the default be lower — 10, say — so an unbounded first run is impossible, or does that just train operators to pass `--limit 100`?"
  - "Q4 (T08, carried from gate 2's Q2): a repository whose whole `severity:*` scheme lies outside `SEVERITY_VALUES` gets an empty rubric, so a backfill there is a no-op (T10 criterion 3) even though `rules.bugs.severity_aliases` already maps those labels for the floor. Gate 2's retrospective says backfill meets those repositories first. Should T10 read aliases, or is that a fifth unit?"
  - "Q5 (T09): backfill writes the amended marker from the body it read at selection time. If the body changed in between, the amend silently reverts that edit. The draft escalates rather than re-reading (T09's second trigger). Should it re-read each body immediately before writing instead?"
  - "Q6 (T11): the live-corpus dry run is drafted as a `type: human` unit, which halts the driver mid-gate. Alternative: fold it into `G3-CLOSE` as deferred verification. The draft chose the halt because gate 1's residual has now been carried twice."
---

# Gate 3 review — backfill for issues already marked

Written by `FEAT-2026-0113/G2-PLAN` for the human who arms **gate 3**. Every unit
below is `status: draft`; arming is your act, not the driver's. This file reviews
what gate 3 is drafted as — gate 2's close is in `GATE-02-REVIEW.md` and
`RETROSPECTIVE.md`.

**Gate 2's premise held, and this gate has no premise without it.**
`RETROSPECTIVE.md` (`### The load-bearing question: was a repository's own
severity scheme disturbed?`) records **zero** `gh label create` calls and zero
description writes against any repository declaring its own `severity:*` scheme,
measured by argv over the whole call sequence in cases A and B, with provisioning
observed only on the declares-none branch. This unit's escalation trigger — *if
the non-interference assertion did not hold, do not draft a backfill on top of
it* — did not fire. That is what licenses everything below: a backfill amends
markers in bulk, and the write path it amends them with is now known safe.

## What gate 3 is drafted as

Four substantive units, one human unit, and the terminal close. `PLAN.md`'s graph
carries the dependencies; the chain is serial because each unit lands a layer the
next one calls:

| Unit | File | What it lands | Depends on |
|---|---|---|---|
| `T07` | `WU-07-backfill-walking-skeleton.md` | the `--backfill-severity` flag, `severity_backfill.py`, and the gate's `feature_oracle` | — |
| `T08` | `WU-08-backfill-selection-and-amend.md` | `list_severity_backfill_candidates` + `amend_marker_severity` in `triage.py` | T07 |
| `T09` | `WU-09-backfill-write-path.md` | `apply_severity_backfill`: marker amended first, label projected second | T08 |
| `T10` | `WU-10-backfill-run-shape.md` | rubric once per run, classification, fail-closed, dry-run default | T09 |
| `T11` | `WU-11-live-corpus-dry-run.md` | `type: human` — the dry run against a real repository | T10 |

**`T07` is the tracer bullet, and it is named as one** (`/authoring-work-units`
§14). This is the correction gate 2 paid four attempts to learn: the
`feature_oracle` is appended to **every** attempt's gate list, so T03 and T04
each failed twice on a `ModuleNotFoundError` for a test module only T06 was
allowed to create. Drafting the walking skeleton first, rather than inserting it
mid-gate as `T02H`, is the whole of that lesson applied. T07's Context names
exactly what it may stub — selection breadth, the marker amendment (a local
`_amend_marker` that T09 deletes), and the classification session — and what it
may not: the marker-then-label order.

**Where the mode sits.** `specfuse-agent --backfill-severity`, reachable only
from `main()`'s own flag branch. `default_providers` gains nothing, so no
conductor run can enter the backfill path — "never part of a normal run" is a
structural property here, not a convention, and T07 criterion 2 is what asserts
it. Q1 asks whether it should be its own console script instead.

## If you check only three things, check these

1. **That `T09`'s criterion 1 still asserts the *order*, not the presence, of the
   two writes.** `PLAN.md`'s **Record precedence** fixes marker-authoritative,
   label-as-projection, marker-written-first, and a unit that reorders them is
   wrong rather than a variation. The cheap way to make that criterion pass is to
   weaken it to "both calls happen" — which a reordered implementation also
   satisfies, and which would leave issues labelled with a severity their marker
   does not carry. Every later reader scans the marker, not the label.
2. **`T08` criterion 1's second half — the stop condition.** An issue whose
   marker already carries `severity=` is not a candidate. That single clause is
   what makes a repeat backfill a no-op, and it is the only thing standing
   between a re-run and a bulk marker rewrite over issues that were already
   done. It is asserted twice on purpose: as a selection property (T08) and by
   argv as a write property (T09 criterion 2). If one of those two is dropped
   during arming, keep the argv one.
3. **Q2 — whether dry run should be the default.** It is the one decision here
   that changes what an operator's first command does, and it is cheaper to
   settle now than after T10 dispatches. The draft's answer is yes; the cost is a
   second command before anything happens.

## Record precedence — how each drafted unit honours it

| Unit | Where precedence binds it | Criterion |
|---|---|---|
| `T07` | the skeleton writes marker then label for one issue | #1 (call order) |
| `T08` | n/a — pure functions, issues no write; `amend_marker_severity` produces the authoritative record's new text | #4, #5 |
| `T09` | the write path proper: amended marker, then the projected label | #1 (order), #3 (a failed label leaves the marker in place; a failed marker leaves no label) |
| `T10` | n/a at write level — decides *whether* to write, never in what order | — |
| `T11` | n/a — read-only | — |

No unit re-derives the label from anything but the marker, and no unit writes a
label for an issue whose marker write failed (T09 criterion 3). The repair
branch — a marker already carrying a severity whose label is missing — is
explicitly **gate 2's** (`apply_triage`'s `[FEAT-2026-0045/T01/marker-label-desync]`
path) and is named out of scope in T09's Do-not-touch, so backfill and repair
cannot both claim the same issue.

## Blast radius — what selects, and what stops

`GATE-03.md`'s milestone is a mode that touches the stranded 31 and nothing else.
Four bounds, each drafted onto a named criterion rather than left to the
implementation:

| Bound | Mechanism | Where |
|---|---|---|
| What is selected | marker parses, carries **no** `severity=` field, category inside `CATEGORIES` | T08 #1, #2 |
| What is excluded | harvester findings (`has_finding_marker`), agent-authored escalations (`escalation.CATEGORY_LABELS`), unmarked issues | T08 #2 |
| How many | `--limit <n>` bounds both the `gh issue list` argv and the returned rows | T08 #3 |
| What stops a re-run | a marker already carrying `severity=` is not a candidate **and** produces zero `gh` calls | T08 #1, T09 #2 |
| What stops any write at all | no `--apply`, no `gh issue edit` | T10 #4 |

**Label provisioning is gate 2's and is not re-derived.**
`labels.read_severity_rubric` (`specfuse/loop/labels.py:405`) already provisions
the four `SEVERITY_LABEL_SPECS` labels, fail-soft and only on the declares-none
branch, through `gh label create … --force`. A backfill run therefore finds the
four labels already present in a repository that declares no scheme — because
the same reader put them there, idempotently — and creates nothing in a
repository that declares its own. T10 criterion 5 is the countable version:
`grep -c '"label", "create"'` over `severity_backfill.py` reports `0`, and a run
against a declares-own repository issues zero creates by argv over the whole
sequence. That is gate 2's non-interference contract re-measured on the new run
shape rather than assumed to carry over.

## Existing-mechanism search (`planning-discipline.md` §1)

Run in this drafting session, not inherited:

- `grep -rn "backfill" --include="*.py" specfuse/` — every hit is unrelated
  (`lint_plan`'s cost backfill, `scaffold._backfill_rule_imports`). **No backfill
  mechanism exists.**
- `grep -rn "def .*marker" --include="*.py" specfuse/` — 21 marker functions
  across 12 modules, and **none amends a marker in place**; every one renders,
  parses or tests for presence. The only in-place marker rewrite in the package is
  `loop.py:7200`'s `_STATUS_MARKER_RE.sub`, over the roadmap status marker — a
  different marker, in a file, not an issue body.
- **Verdict:** `no in-place marker amender exists; reusing render_marker,
  parse_marker_fields and _list_open_issues rather than writing new ones`.
- **What that buys, concretely:** T08 renders the amended marker through the
  existing `render_marker` (already three-field since gate 2's T04) instead of a
  fourth literal — asserted as `grep -c "specfuse:triage" specfuse/loop/triage.py`
  still reporting `3` — and issues its listing through `_list_open_issues`,
  asserted as `grep -c '"issue", "list"'` still reporting `1`. T10 calls
  `read_severity_rubric` and `classify_severity` and defines neither, asserted by
  grep in its criteria 2 and 5. A drafted unit that issued its own `gh label
  list` would have failed this gate's own arming discipline.

## Flag-scope table (`planning-discipline.md` §3)

Gate 3 introduces the feature's only flags. The headline claim to check the table
against: *no invocation that exists today behaves differently after this gate.*

| Flag | Default | Code path it gates | Behaviour when absent |
|---|---|---|---|
| `--backfill-severity` | off | `main()`'s backfill branch only | byte-identical conductor run; `default_providers` is unchanged (T07 #2) |
| `--apply` | off | every `gh issue edit` in the backfill path | selection printed, zero writes (T10 #4) |
| `--limit <n>` | `DEFAULT_LIST_LIMIT` (100, `specfuse/monitor/issues.py:56`) | the candidate listing and the returned rows | the module default, as `list_untriaged` already uses (Q3) |

No policy key is added, and `rules.bugs.min_severity` is read nowhere in gate 3 —
where the floor sits stays the operator's, in gate 3 as in gate 2.

## Cross-repo contracts (`/authoring-work-units` §8)

Every value a drafted criterion names that is owned outside this feature, checked
against its source in this drafting session rather than recalled:

| Value | Source of truth | Checked |
|---|---|---|
| `<!-- specfuse:triage category=… confidence=… -->` | `specfuse/loop/triage.py:65` (`_MARKER_TEMPLATE`) | read, 2026-09-17 |
| the three-field form | `specfuse/loop/triage.py:66` (`_MARKER_TEMPLATE_WITH_SEVERITY`) | read, 2026-09-17 |
| `parse_marker_fields` / `render_marker(category, confidence, severity)` | `specfuse/loop/triage.py:135`, `:113` | read, 2026-09-17 |
| `apply_triage` never rewrites an existing marker | `specfuse/loop/triage.py:181` docstring + the marked branch | read, 2026-09-17 |
| `list_untriaged` excludes a marked issue whose labels are complete | `specfuse/loop/triage.py:308` | read, 2026-09-17 |
| `_list_open_issues` argv (`gh issue list --state open --limit … --json number,title,body,labels`) | `specfuse/loop/triage.py:162` | read, 2026-09-17 |
| `has_finding_marker` | `specfuse/monitor/issues.py:72` | read, 2026-09-17 |
| `DEFAULT_LIST_LIMIT = 100` | `specfuse/monitor/issues.py:56` | read, 2026-09-17 |
| `CATEGORY_LABELS` (5 labels) | `specfuse/loop/escalation.py:29` | read, 2026-09-17 |
| `_is_agent_escalation` keys on those labels | `specfuse/agent/providers/triage.py:146` | read, 2026-09-17 |
| `read_severity_rubric` provisions only on the declares-none branch | `specfuse/loop/labels.py:405`–`:454` | read, 2026-09-17 |
| `SEVERITY_LABEL_SPECS`, `DEFAULT_SEVERITY_RUBRIC` | `specfuse/loop/labels.py:357`, `:347` | read, 2026-09-17 |
| `classify_severity` fails closed below `confidence=high` | `specfuse/agent/triage_invoke.py:108` | read, 2026-09-17 |
| `build_invocation(..., rubric=…)` | `specfuse/agent/triage_invoke.py:41` | read, 2026-09-17 |
| `SEVERITY_VALUES`, `SEVERITY_LABEL_PREFIX` | `specfuse/loop/agent_policy.py:56`, `:340` | read, 2026-09-17 |
| `_build_arg_parser` / `main` / `default_providers` | `specfuse/agent/run.py:1113`, `:1136`, `:1041` | read, 2026-09-17 |

## Runtime probe (`planning-discipline.md` §4) — does not bind, and why

No drafted unit flips a default value or a severity. Both new flags default off,
and the absent-flag behaviour is asserted as unchanged rather than described
(T07 criterion 2). No lint check is raised to ERROR, no `WARNING` becomes
blocking, and no existing function's signature changes: T08 adds two functions
beside the marker functions and edits none of their bodies. `PLAN.md`'s
**Escalation-predicate satisfiability** section already records that the
"severity" in this feature's title is the severity of an inbound issue, a
different axis from a finding's severity.

If you want the probe anyway, the command is the full `tests` gate from
`.specfuse/verification.yml` with T08's two functions applied locally, and its
failure list belongs in this file before you arm.

## Open questions

**Q1 — a flag, or its own entry point?** Drafted as `specfuse-agent
--backfill-severity`. It reuses the conductor's repo detection, its branch
restore and its `--repo` handling, and adding a console script means a
`pyproject.toml` change and a reinstall before the mode can be run at all. The
counter-argument is real: this is a bulk issue-mutating maintenance command
living behind the binary an unattended loop invokes, and the only thing keeping
it out of a normal run is one branch in `main()`. The draft bounds that
structurally — `default_providers` gains nothing — rather than by convention.
Recommendation: leave it as a flag. You are the one who can overrule that.

**Q2 — dry run by default, or `--dry-run` to opt out?** Drafted as
dry-run-by-default with `--apply` required. The asymmetry is deliberate: the
failure mode of a too-cautious default is one extra command, and the failure
mode of the other default is 31 markers amended by an operator who wanted to see
the list first. `PLAN.md`'s risk-accepted paragraph and `autonomy_default:
review` both point the same way. Recommendation: keep it.

**Q3 — what should `--limit` default to?** Drafted at the module default
(`DEFAULT_LIST_LIMIT`, 100), which is what `list_untriaged` already uses. The
measured backlog is 31, so the default does not bound anything in practice. A
lower default (10) would make an unbounded first run impossible; it would also
mean a full backfill is three commands, and an operator who learns to type
`--limit 100` has un-bounded it anyway. Naming it rather than deciding it.

**Q4 — aliased schemes, carried from gate 2's Q2.** A repository whose
`severity:*` labels lie outside `SEVERITY_VALUES` (`severity:major`,
`severity:minor`) gets `{}` from `read_severity_rubric`, so T10 criterion 3 makes
the backfill a no-op there. Gate 2's retrospective is explicit that those are
exactly the repositories backfill meets first, since they have the most
unlabelled history, and that `rules.bugs.severity_aliases` (#3349) already exists
as the operator's declared mapping. The draft does **not** read aliases: doing so
means deciding whether an alias widens what the classifier may answer, which is
gate 2's open question re-opened, and it is a fifth unit's worth of work. Drafted
as a documented no-op, flagged here.

**Q5 — stale bodies.** T09 writes the amended marker built from the body read at
selection time. A body edited in between is silently reverted by the amend. The
draft escalates on the disagreement rather than re-reading (T09's second
trigger), because a re-read per issue doubles the `gh` calls and the window is
small for a maintenance command. If you think the window matters, the fix is one
`gh issue view` before each write and it belongs in T09's criteria, not in the
implementation's judgment.

**Q6 — is `T11` worth a driver halt?** A `type: human` unit stops the run and
waits for `/unblock-wu --done --evidence`. The alternative is folding the live
check into `G3-CLOSE` as deferred verification, which costs no halt and has been
this feature's pattern twice already — which is precisely the argument against
it. See the residual section below.

## Carried forward from gates 1 and 2

- **Gate 1's residual is drafted as resolved, not re-carried.** *No oracle in
  this feature has yet read a real issue body outside this repository.* Gate 2
  made it larger: every gate-2 oracle injects a runner, so the `gh label list`
  JSON, the classification answer and every write were authored by a test.
  `T11` is the unit that changes it — the operator runs the dry-run form against
  the repository where the 31 were measured and pastes the selection into this
  file under `## Live-corpus dry run`. It is placed **before** the close
  deliberately (`close-discipline.md` §2): a step only a person can perform is
  recorded as work, not softened into the terminal verdict afterwards. If you
  reject `T11` at arming, the residual is re-carried for a third time and
  `G3-CLOSE` criterion 4 is where that has to be said out loud.
- **Gate 2's own finding is why `T07`'s stub has a name.** A later unit in the
  same gate silently deleted an earlier unit's assertions and nothing noticed —
  `T02H`'s `test_execute_writes_marker_then_label_in_order` does not exist at
  HEAD, and the surviving replacement no longer pins the ordering on the
  severity-free degradation path. The drafting consequence, applied here: T07's
  one permitted stub is named (`_amend_marker`), T09's criterion 4 asserts by
  grep that it is gone and that `amend_marker_severity` has exactly one
  definition repo-wide, and every later unit's Do-not-touch names the sibling
  modules rather than trusting a promise. It does **not** fully solve the
  problem — nothing in the loop notices a deleted assertion — so when you arm
  T09 and T10, read what their test edits remove, not only what they add.
- **`list_untriaged` is the reason this gate exists**, and it is untouched. The
  measured 31 are excluded by it correctly: they are marked and their category
  labels are present. Backfill is a second selection over the same listing, not a
  change to that one.
- **One lint WARN is expected and accepted.** `specfuse lint` reports that T08's
  `produces: specfuse/loop/triage.py` was already delivered by the `done` T01.
  That is the WARN's documented "state the incremental edit in the body" case —
  T08 adds two functions beside the marker functions and edits none of their
  bodies, which its Objective and Do-not-touch both say. Dropping the path would
  disarm the driver's presence gate for this unit, which is worse.

## Live-corpus dry run

`(empty — `FEAT-2026-0113/T11` fills this in. Do not arm `G3-CLOSE` past an empty
section here without recording the residual as re-carried.)`

---

## Live-corpus dry run (T11, 2026-09-18)

Read-only. `--apply` not passed; no write of any kind was issued.

```
$ python3 -m specfuse.agent.severity_backfill --repo clabonte/generator --limit 5
#1902: no usable classification, skipped
#1895: no usable classification, skipped
#1893: no usable classification, skipped
#1883: severity=critical
#1876: no usable classification, skipped
EXIT=0
```

Invoked as the module rather than the `specfuse-backfill-severity` console
script: the script was registered by T07 this morning and is not on PATH until a
reinstall. Same entry point, same `main()`.

### Selection, with the marker each row was selected on

| Issue | Marker | Existing `severity:*` label | Title |
| --- | --- | --- | --- |
| #1902 | `category=bug confidence=high` | **`severity:minor`** | One multi-group regen writes several test-support CHANGE… |
| #1895 | `category=bug confidence=high` | **`severity:major`** | Dart conditional-read fake fabricates `"fake-etag"`… |
| #1893 | `category=bug confidence=high` | **`severity:major`** | Generated trigger ActivitySource names have no stable pr… |
| #1883 | `category=bug confidence=high` | *(none)* | Generated TypeScript package.json crashes a fresh `npm i`… |
| #1876 | `category=feature confidence=high` | *(none)* | Optimistic concurrency for keyless singleton operati… |

Every selected issue carries a triage marker with **no `severity=` field**, which
is the predicate's stated contract. Confirmed.

### This run is the one that found T08H's two defects

The first invocation of this exact command returned **zero rows and printed
nothing**. `--limit` bounded the `gh issue list` window rather than the candidate
count, and the five newest issues carry no triage marker at all. Measured:
`--limit 5` → 0 candidates, `--limit 100` → 74, `--limit 200` → 84, against 191
open issues. The default of 100 silently ignored the oldest 91. `T08H` fixed
both that and the silent zero-candidate report; this table is the post-fix run.

### Finding carried to the close: three selected issues already carry a human-assigned severity

#1902, #1895 and #1893 carry `severity:minor` / `severity:major` / `severity:major`
— labels a person applied — while their markers carry no `severity=`. The
predicate selects on the **marker**, so a human-labelled issue is a backfill
candidate.

Today that is masked: the rubric for this repository has a single entry
(`critical`, the only one of its three labels inside `SEVERITY_VALUES`), so all
three resolved to "no usable classification, skipped" and nothing was
contradicted.

**It stops being masked the moment #3355 lands.** With a fuller rubric the
classifier could answer `high` for an issue a person labelled `minor`, and the
write path would amend the marker and add `severity:high` alongside the human's
`severity:minor` — two severities on one issue, the agent's silently winning at
the floor because `read_severity_label` returns the first it recognises.

The shape of the fix is reconciliation rather than re-classification: an issue
whose label already states a severity should have its marker written **from that
label**, not from a fresh classification. That is a different operation from
backfilling an unlabelled issue and is not what any unit in this gate builds.

Recorded here rather than acted on: it is latent under the current rubric, and
#3355 is what makes it live.
