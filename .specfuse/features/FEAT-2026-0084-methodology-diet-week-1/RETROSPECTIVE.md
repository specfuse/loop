# Retrospective — FEAT-2026-0084, methodology diet, week 1

## Gate 1

**Verdict: `met`.** All four `GATE-01.md` measurements re-run fresh in this
session (2026-09-02), against the working tree at
`7fb098a` + T01–T04's squashes. Every number below was produced by the command
quoted beside it in this session; none is copied from a producing unit's
RESULT block.

The "before" column is measured against the merge-base
`cdc2842f92604a7afdf70db5e6c1432d31d89e6c` (`git merge-base HEAD origin/main`),
not against `PLAN.md` § Notes' recorded prose. The two agree.

## Measurements

| # | Measurement | Before | After | Target |
| --- | --- | --- | --- | --- |
| 1 | Included-rules word count | **7,213** | **2,379** | ≤ 2,500 |
| 1b | Included-rules line count | 889 | 297 | — |
| 1c | Rules in the include block | 7 | 3 | — |
| 1d | `operator-escalation.md` / `human-output.md` in the include set | yes | **no** | absent |
| 2 | `WU.template.md` lines | **199** | **70** | ≤ 70 |
| 3 | `authoring-work-units/SKILL.md` lines | **571** | **200** | ≤ 200 |
| 4 | Single-gate threshold (`docs/methodology.md` §6) | **4** | **8** | 8 |
| 4b | `GATE_PROPORTIONALITY_THRESHOLD` (`lint_plan.py`) | (constant absent) | **8** | 8 |
| 5 | Unobservable-AC rule: ERROR count over the corpus | 0 (rule absent) | **0** | 0 |
| 6 | Ceremony-proportionality rule: WARN count over the corpus | 0 (rule absent) | **18** | WARN-only, non-blocking |
| 7 | Total ERROR over all 73 feature folders | — | **0** | 0 |

### Commands, with the number each produced

**1 / 1b / 1c / 1d — included-rules budget.**

```
# before
for f in $(git show cdc2842:.claude/CLAUDE.md | sed -n 's/^@\(\.specfuse\/rules\/.*\.md\)$/\1/p'); do git show cdc2842:$f; done | wc -w
   -> 7213      (and | wc -l -> 889; the list printed 7 files)
# after
cat $(sed -n 's/^@\(\.specfuse\/rules\/.*\.md\)$/\1/p' .claude/CLAUDE.md) | wc -w
   -> 2379      (and | wc -l -> 297; the list printed 3 files:
                 result-contract.md, never-touch.md, security-boundaries.md)
```

The pruned set ships, not just holds locally:

```
grep -n '@\.specfuse/rules/' specfuse/loop/scaffold.py
   -> 235-237 _RULES_BLOCK: result-contract.md, never-touch.md, security-boundaries.md
   -> 252-255 the removal list upgrade strips: correlation-ids.md,
      verification-discipline.md, operator-escalation.md, human-output.md
cat specfuse/loop/data/rules/{result-contract,never-touch,security-boundaries}.md | wc -w
   -> 2379      (the vendored copy matches the canonical set word for word)
```

`operator-escalation.md` and `human-output.md` appear nowhere in either the
worktree include block or `_RULES_BLOCK`; both rules still ship in
`.specfuse/rules/` and are referenced from the human-facing skills.

**2 / 3 — template and authoring-skill size.**

```
git show cdc2842:.specfuse/templates/WU.template.md | wc -l          -> 199
wc -l < .specfuse/templates/WU.template.md                            -> 70
git show cdc2842:plugins/specfuse/skills/authoring-work-units/SKILL.md | wc -l -> 571
wc -l < plugins/specfuse/skills/authoring-work-units/SKILL.md          -> 200
wc -l < .specfuse/skills/authoring-work-units/SKILL.md                 -> 200   (vendored copy in sync)
```

A work unit rendered from the new template lints clean:
`tests/test_wu_template_renders_lintable.py` runs inside the fresh
`python3 -m unittest discover -s tests -q` pass recorded below.

**4 / 4b — the threshold.**

```
git show cdc2842:docs/methodology.md | grep -nE "≤ 4"
   -> 350: `qa_execution`, `qa_curation`) is **≤ 4** drafts as a **single gate** with
grep -nE "≤ 8" docs/methodology.md
   -> 442: `qa_execution`, `qa_curation`) is **≤ 8** drafts as a **single gate** with
sed -n '826p' specfuse/loop/lint_plan.py
   -> GATE_PROPORTIONALITY_THRESHOLD = 8
```

Behavioural check on a purpose-built fixture (8 substantive units, close WU,
identical bodies; only the gate partition differs):

```
python3 -m specfuse.loop.lint_plan $TMPDIR/t04probe/one | grep -c ceremony-proportionality  -> 0
python3 -m specfuse.loop.lint_plan $TMPDIR/t04probe/two | grep    ceremony-proportionality
   -> WARN: .../two: planned substantive WU count (8) is at most the
      ceremony-proportionality threshold (8) but the plan spans 2 gates.
```

**5 — the unobservable-AC rule, with its negative observation.**

Fixture: one `status: pending` implementation WU whose single acceptance
criterion is `- The migration is applied in prod.` (no backticked check).

```
# A. no escape hatch
python3 -m specfuse.loop.lint_plan $TMPDIR/t03probe/feature
   -> ERROR: .../WU-01-impl.md: acceptance criterion the loop cannot observe:
      'The migration is applied in prod.'
# B. same criterion, WU carries oracle_env: github_actions_ci
   -> 0 matching findings
# C. same criterion, WU carries human_only: true
   -> 0 matching findings
```

Corpus sweep (the count that gated shipping the rule at ERROR):

```
for d in .specfuse/features/*/; do python3 -m specfuse.loop.lint_plan "$d"; done \
  | grep -c "cannot observe"     -> 0
```

**6 / 7 — corpus sweep totals.**

```
for d in .specfuse/features/*/; do python3 -m specfuse.loop.lint_plan "$d"; done
  | grep -c "^ERROR"                        -> 0
  | grep -c "ceremony-proportionality"      -> 18
  | grep -c "^WARN"                         -> 226
ls -d .specfuse/features/*/ | wc -l          -> 73
```

The 18 proportionality WARNs are the intended, non-blocking finding: 18 of the
73 existing features are small enough that today's threshold would have drafted
them as one gate. The sweep exits non-zero on exactly one folder,
`.specfuse/features/FEAT-2026-0078-produces-incremental/`, reporting
`missing PLAN.md`. That folder is **empty and untracked** — `git ls-files` on it
returns 0 paths, `git log` on it returns no commits, `ls -la` shows no entries.
It is local dirt on this machine dated 2026-08-25, not repository state, and not
this feature's doing. Zero ERROR over every tracked feature folder stands.

### Oracles re-run fresh

| Oracle | Result |
| --- | --- |
| `python3 -m unittest discover -s tests -q` | `Ran 3654 tests in 147.404s` / `OK (skipped=1)`, exit 0 |
| `bash scripts/smoke-test.sh` | `smoke test: OK`, exit 0 |
| `specfuse lint` over every feature folder | 0 ERROR (see above) |

**Both suites were re-run outside the Bash sandbox.** Inside it the unit suite
reported `FAILED (failures=2, errors=85)`, all 85 sharing one signature:
`PermissionError: [Errno 1] Operation not permitted:
'/Users/christian/.claude/session-env/...'` from `require_session_env_writable`,
plus 2 wheel-build failures from blocked network. That is a report about where
the suite ran, not about the repository; the unsandboxed re-run is the one
recorded above.

## Retrospective

**Did this feature's own ~40-line work units execute cleanly?**

Yes. Body lengths, excluding frontmatter, were 41 / 40 / 45 / 35 lines
(`awk 'c==2{n++} /^---$/{c++}'` per file) against the 94-line typical body
`PLAN.md` cites. Three of the four units passed on **attempt 1** (T02, T03,
T04). The one unit that did not, T01, did not fail for want of context.

Its two non-passing attempts both record
`failure_class: produces_not_in_diff`, `failure_signature: correlation-ids.md`
— the driver refusing the close because `.specfuse/rules/correlation-ids.md`
was declared in T01's `produces:` but absent from its squash diff. Both
attempts' `agent_status` and `agent_blocked_reason` are `null`: the sessions
believed they were done and the driver disagreed. The cause is in the WU's own
frontmatter, not its prose. T01's only acceptance criterion touching that file
is a **preservation** criterion — "`correlation-ids.md` still carries
`CORRELATION_ID_RE`'s pattern in prose" — so a session that satisfied every
criterion correctly would leave the file unchanged and be refused. A 94-line
body would have carried the same contradiction.

The ordering is worth recording as evidence, though not as a controlled
experiment: T01 landed the pruned include set at 10:10; T02 (12:38), T03
(12:50) and T04 (13:23) were each dispatched afterwards, under the 2,379-word
rule context, and each passed on its first attempt. Nothing in this feature's
own execution suggests the cut context under-served a unit.

**Which cut rule sentences did a unit ask for during its attempts?**

**None.** There is no `work/` directory in this feature folder and none in its
git history (`git log --all --name-only` over the folder lists only PLAN,
GATE, the five WU files and `events.jsonl`), so no attempt-note was ever
written — consistent with the driver writing them only on the refusal shapes
that produce one. Across all 19 events in `events.jsonl`, no attempt carries
an `agent_blocked_reason`, and no `human_escalation` after the pre-dispatch one
(below). T01's escalation trigger — "blocked if reaching 2,500 words requires
cutting a sentence a LEARNINGS entry or issue cites" — never fired; 2,379 words
was reached without it.

**The one thing that went sideways, and it is not a sizing problem.**

T01's third attempt satisfied the `produces_not_in_diff` guard by **adding 39
lines to `correlation-ids.md`** — new prose on landing an ordinal reservation
on the trunk before working under it, and on resolving an ordinal claimed only
on an unmerged branch. The content is substantive and well-grounded (it cites a
real double-collision), and it costs the dispatch budget nothing because
`correlation-ids.md` is no longer in the include set. But it is content **no
acceptance criterion asked for**, written under guard pressure, on a unit whose
stated objective was to *remove* prose. $10.28 of T01's $16.80 went to the two
refused attempts that produced it. That is the generalisable finding, promoted
to `## Lessons`.

## Cost analysis

`planned_cost_usd: 24.00` in `PLAN.md` is the per-WU sum: T01 $5.00 + T02
$5.00 + T03 $6.00 + T04 $3.00 + G1-CLOSE $5.00.

Actuals are the `task_completed` `cost_usd` per WU in `events.jsonl`, which
match each unit's `cost_usd:` frontmatter:

| WU | Planned | Actual | Ratio | Delta |
| --- | --- | --- | --- | --- |
| T01 | $5.00 | $16.80 | **3.36×** | +$11.80 |
| T02 | $5.00 | $10.69 | **2.14×** | +$5.69 |
| T03 | $6.00 | $1.05 | 0.18× | −$4.95 |
| T04 | $3.00 | $1.39 | 0.46× | −$1.61 |
| **Four units** | **$19.00** | **$29.94** | **1.58×** | **+$10.94 (+57.6%)** |
| G1-CLOSE | $5.00 | (this session; not yet stamped) | — | — |
| **Feature** | **$24.00** | **≥ $29.94** | **≥ 1.25×** | **≥ +$5.94 (+24.8%)** |

**Delta, named: +$10.94 on the four producing units, +57.6% over their planned
$19.00, and the feature is already +$5.94 over its whole $24.00 plan before
this close's own spend is stamped.**

Two units breach `docs/methodology.md`'s "no WU > 2× planned" rule — T01 at
3.36× and T02 at 2.14×. The concentration is legible rather than diffuse:

- **T01's overrun is 96% explained by its two refused attempts.** $5.64 + $4.64
  = $10.28 of the $11.80 overrun bought nothing but the third attempt's
  starting position. Removing one path from a `produces:` list at arm time
  would have avoided essentially all of it.
- **T02's overrun is scope, not retries.** One attempt, $10.69, 91,534 output
  tokens and 2,154 seconds — it rewrote a 571-line skill down to 200 and a
  199-line template down to 70. The plan under-costed the largest prose rewrite
  in the feature at the same $5.00 as the smallest.
- **T03 and T04 came in at a fifth and a half of plan**, returning $6.56. The
  estimator over-costed the two code changes and under-costed the two prose
  ones, which is the inverse of the usual bias and worth carrying into the next
  week's plan.

### Failure-class breakdown

| Class | Count | Where |
| --- | --- | --- |
| `produces_not_in_diff` | 2 | T01 attempts 1 and 2, both `failure_signature: correlation-ids.md` |
| `passed` | 4 | T01 attempt 3, T02/T03/T04 attempt 1 |

Two further driver-level events, neither an attempt outcome:

- **1 × `human_escalation`, `reason: preexisting_gate_failure`**, at gate entry
  before any unit was dispatched. Three gates were already red on the branch
  point: `tests` (`test_real_tree_is_clean_on_all_four_invariants`), `coverage`
  (`[07:45:37] bug-1 failed after 0s — RuntimeError: boom on bug-1`), and
  `roadmap-link-gate` (`ref '#feat-2026-0084' in roadmap.md does not resolve`).
  Zero work units were dispatched for that halt; the roadmap anchor was added
  in `ddf7d6b` and the gate reopened. All three are green in this close's fresh
  re-runs.
- **3 × `driver_staleness_detected`, `driver_restart_required`**, after T01, T03
  and T04 — each because the unit edited driver-owned source (`scaffold.py`,
  `lint_plan.py`) that the running driver had already loaded. Expected for a
  feature whose subject is the driver's own linter and scaffold; each cost a
  restart, not an attempt.

## What the loop did NOT verify

- **The roadmap goal's "next three features" clause.** `roadmap_goal` reads
  "The next three features drafted after merge carry work units of 45 lines or
  fewer, every acceptance criterion names a check the loop can run, features of
  up to 8 substantive units draft as one gate…". By construction no artifact
  existing at close time can satisfy it: the features it quantifies over have
  not been drafted. This is a **post-merge check, not a hedge** — the verdict is
  `met` on the gate's own definition of done, which is the four measurements
  above and which are all verified. **The check to run:** after the third
  feature drafted following this merge, measure `wc -l` on its work-unit bodies
  (expect ≤ 45), run `specfuse lint` on each and confirm zero
  `cannot observe` ERRORs, and confirm any feature with ≤ 8 substantive units
  drafted as a single gate. If the numbers miss, the correction belongs to the
  week-2 feature, not to a re-open of this one.
- **Nothing else.** Every other acceptance criterion in `GATE-01.md` and in this
  close's own body was verified in-loop by a command run in this session.

## Consumer-visible contract changes

Two, and both change what **every downstream scaffold** receives from
`specfuse init` and `specfuse upgrade`:

1. **The `@`-include block in the generated `.claude/CLAUDE.md` drops from seven
   rules to three.** `_RULES_BLOCK` (`specfuse/loop/scaffold.py:235-237`) now
   ships `result-contract.md`, `never-touch.md`, `security-boundaries.md` only.
   `correlation-ids.md`, `verification-discipline.md`, `operator-escalation.md`
   and `human-output.md` are removed from the block, and `specfuse upgrade`
   **strips those four `@`-lines from an existing target's `CLAUDE.md`**
   (`scaffold.py:252-255`) rather than leaving both blocks. All seven rule files
   still ship in `.specfuse/rules/`; four of them are now linked-to rather than
   auto-loaded. Per-dispatch binding-rule context drops from 7,213 to 2,379
   words. **A target that hand-edited its include block will have the four lines
   removed by upgrade**; project-authored rules belong in `.specfuse/rules-local/`,
   which upgrade does not touch.
2. **`.specfuse/templates/WU.template.md` shrinks from 199 lines to 70.** Every
   scaffolded project receives the shorter template; work units authored from it
   are structurally different documents (five bold sections, no restated rules).
   Existing work units are untouched and still lint clean — the corpus sweep
   over all 73 feature folders reports 0 ERROR.

Also shipped, and consumer-visible as *new lint output* rather than as a
changed artifact: `lint_plan` gains an ERROR on an acceptance criterion the loop
cannot observe (escape hatches: `oracle_env` naming a non-local environment, or
`human_only: true`) and a WARN when a feature of ≤ 8 substantive units spans more
than one gate. Both are enumerated in `CHANGELOG.md`'s `Unreleased`.

## Lessons

One, appended to `.specfuse/LEARNINGS.md`:

> A `produces:` path whose only acceptance criterion is a **preservation**
> criterion is an unsatisfiable declaration — the driver's
> `produces_not_in_diff` guard demands a diff the criteria forbid, and the
> cheapest way out is to invent an edit. T01 paid $10.28 across two refused
> attempts and then added 39 lines of unrequested prose to
> `correlation-ids.md` to clear it. Rule: `produces:` lists only paths a
> criterion requires **changing**; a path the WU must merely leave intact
> belongs in an acceptance criterion, never in `produces:`.

Nothing else here generalises: the cost overrun is this plan's estimator being
wrong in a specific direction, and the three `driver_restart_required` halts are
expected for a feature that edits the running driver.
