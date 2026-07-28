<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0046, Escalation contract + /attention inbox

**Correlation ID.** `FEAT-2026-0046/G1-CLOSE`. Single terminal gate, four substantive
work units plus this close. No `close-intermediate`, no `plan-next`, no gate 2.

**What shipped.** A `needs-human` escalation issue format expressed as a
machine-checkable contract (`specfuse/loop/escalation.py`), an idempotent emission
primitive that is invoked but never auto-fired, the `/attention` read-only inbox skill,
and a grep-shaped guard with a positive control proving the skill cannot write state.

## Gate 1 — oracle re-run, fresh

Every oracle named by T01–T04, re-run in this close session against the working tree.
Exit codes read directly from the process, not inherited from any producing WU's
self-report. Interpreter: `.venv/bin/python3`, 3.14.6; pytest 9.1.1.

| # | Command | Exit | Observed |
|---|---|---|---|
| 1 | `python3 -m pytest tests/test_escalation_contract.py -q` | `0` | `10 passed in 0.01s` |
| 2 | `python3 -m pytest tests/test_escalation_emit.py -q` | `0` | `6 passed in 0.01s` |
| 3 | `python3 -m pytest tests/test_attention_skill_structure.py -q` | `0` | `2 passed in 0.02s` |
| 4 | `python3 -m pytest tests/test_attention_nonwriting_guard.py -q` | `0` | `3 passed in 0.01s` |
| 5 | `python3 -m pytest tests/test_skills_vendored_in_sync.py -q` | `0` | `4 passed in 0.02s` |
| 6 | `python3 -c "from specfuse.loop.escalation import NEEDS_HUMAN_LABEL, CATEGORY_LABELS, render_escalation_body, validate_escalation_body"` | `0` | T01 criterion 12, all four symbols importable |
| 7 | `python3 -c "from specfuse.loop.escalation import emit_escalation"` | `0` | T02 criterion 11 |
| 8 | `grep -rn "emit_escalation" specfuse/loop/loop.py` | `1` | no output — no call site; the primitive is not auto-wired |

25 tests, all green. Oracle 8's exit `1` is the passing result: grep exits non-zero on
no match, and no match is exactly what T02 criterion 8 requires — the dispatch loop must
not invoke the primitive. Recorded here explicitly because a reader scanning the "Exit"
column for zeros would misread it.

A first run of the pytest oracles piped through `tail`, which returns the exit code of
`tail` rather than pytest. The table above is the re-run that captures each command's
own status. Noted because the numbers, not the green text, are what this section claims.

### Failure-class breakdown

No non-passing attempts. All four substantive work units passed on attempt 1 with
`failure_class: null` and `failure_signature: null` in every `attempt_outcome` event —
`grep -c '"outcome": "passed"' events.jsonl` covers 4 of 4 dispatched units.

Two `human_escalation` events do appear in `events.jsonl`, at 21:10:52 and 21:21:58,
both `reason: preexisting_gate_failure`. These are **not** work-unit failures: zero work
units were dispatched for either, and the payloads say so directly ("No work unit caused
this failure"). The integration branch entered gate 1 with four red checks
(`leak-scan-hook`, `sync-scaffold-bats`, `init-sh-shim-bats`, `hookspath-conflict-bats`),
each classed `other` with signature `no_gate_marker`; a first repair cleared three, a
second cleared `hookspath-conflict-bats`, and T01 started at 21:24:34. The cost was
roughly 14 minutes of operator wall-clock and two driver halts, and it is invisible in
the dollar figures below because no agent ran.

## Cost analysis

`PLAN.md` declares `planned_cost_usd: 17.00`. The per-WU frontmatter sums to exactly
that: $2.50 + $3.50 + $4.00 + $2.00 + $5.00. Actuals below are read from
`events.jsonl`'s `attempt_outcome` / `task_completed` payloads.

| WU | Planned | Actual | Delta | |
|---|---|---|---|---|
| T01 escalation issue contract | $2.50 | $0.999586 | −$1.500414 | −60.0% |
| T02 emission primitive | $3.50 | $0.682318 | −$2.817682 | −80.5% |
| T03 `/attention` skill | $4.00 | $0.869812 | −$3.130188 | −78.3% |
| T04 non-writing guard | $2.00 | $0.641066 | −$1.358934 | −67.9% |
| **Substantive subtotal** | **$12.00** | **$3.192782** | **−$8.807218** | **−73.4%** |
| G1-CLOSE (this WU) | $5.00 | not yet in `events.jsonl` | — | — |
| **Feature total** | **$17.00** | **≥ $3.192782** | — | — |

**The delta, named.** The four substantive work units came in **$8.81 under plan, −73.4%**.
This close's own spend is not reconcilable here: the driver writes the close's
`attempt_outcome` after the session ends, so `events.jsonl` cannot contain it while the
session is authoring the file that reads it. Bracketing it instead — if this close
consumes its full $5.00 budget the feature lands at $8.19 (−51.8% against $17.00); at a
spend proportional to the substantive units' overshoot, nearer $4.20–$5.20 (−75% to −69%).
Either bracket leaves the feature well under plan. The operator can close the bracket
after the squash with `grep 'G1-CLOSE' events.jsonl`.

**Why the miss is this large.** Every WU was priced on `model: sonnet` at
`effort: medium` and every one of them was, in the end, a single additive module or test
file against a stated interface. T02's −80.5% is the clearest case: it was priced for the
risk of discovering `gh` search syntax, and the runner seam in `gh_backend.py` meant that
discovery never happened — a stub was injected and the question was deferred rather than
answered. The plan bought insurance against live-API discovery and then, by design, did
not use it. That is not a pricing error so much as a pricing model that charges for risk
the scope boundary had already removed.

The pattern is uniform across all four units (−60% to −80.5%), which is what distinguishes
it from noise. Per `[FEAT-2026-0070/G1-CLOSE]`'s standing caution, a calibration lesson
drawn from one gate's uniform miss is a hypothesis, not a rule — see the LEARNINGS entry,
which is phrased as one.

## What the loop did NOT verify

Four deferrals. Each names the criterion, why verification was deferred, and where it
actually happens.

**1. The real `gh issue create` invocation behind `emit_escalation`.**
Criteria: T02 3, 4, 5, 7 — the create call's arguments carry `needs-human`, exactly one
`CATEGORY_LABELS` member, the configured assignee, and a body satisfying
`validate_escalation_body`.
*Deferred because:* every test injects a stub runner. T02 criterion 9 forbids invoking
the real `gh` binary, and `PLAN.md` records the trade explicitly. What is verified is the
argument list handed to the runner; what is not is that `gh` accepts it — in particular
that the five category labels and `needs-human` exist in the repository at all.
`gh issue create` fails on an unknown label.
*Verified instead by:* an operator post-merge step. Create the six labels
(`needs-human`, `gate-review`, `blocked-wu`, `triage-question`, `drafting-needed`,
`merge-approval`), then invoke `emit_escalation` once against a scratch repository and
confirm the issue appears labelled and assigned.

**2. The idempotency search — `gh issue list --search "<!-- specfuse:escalation id=… -->"`.**
Criterion: T02 6 — a second emit for the same correlation ID creates nothing and returns
the existing issue's number.
*Deferred because:* the stub returns whatever the test hands it, so the test proves the
find-then-create branch logic and nothing about the query. This is the sharpest of the
four: `_find_existing_issue` passes an HTML comment to GitHub's `--search`, and GitHub's
issue search index does not reliably tokenise HTML comment content. The code does re-check
`marker in issue["body"]` on each returned row, so a search that matches too *broadly*
degrades safely; a search that returns **nothing** does not — it silently files a
duplicate on every retry, which is the one property this WU called load-bearing.
*Verified instead by:* the same post-merge step, run twice. If the second call files a
second issue, the fix is to drop `--search` and filter `gh issue list --label needs-human
--json number,body` client-side, which the existing body re-check already makes correct.

**3. `/attention`'s live `gh pr list` stale-PR sweep.**
Criteria: T03 6 (the `stale` state class) and T03 10 (graceful degradation when `gh` is
unavailable, local sweep still runs).
*Deferred because:* both are asserted as prose present in `SKILL.md` by a structural
test. No test runs `gh pr list`, and no test removes `gh` from `PATH` to observe the
degradation actually degrading.
*Verified instead by:* the operator running `/attention` post-merge, once normally and
once with `gh` unavailable.

**4. `/attention` end-to-end — the skill is never executed.**
Criteria: T03 2–11 as a whole.
*Deferred because:* this is the `[FEAT-2026-0003/G2-LESSONS]` structural-oracle remedy
working as designed — it converts a vacuous markdown pass into a real assertion that the
required sections exist. What it cannot assert is that an agent following those sections
produces a correct inbox. The gap is narrower than it sounds (T04's guard does execute,
against both copies of the skill text) but it is not zero.
*Verified instead by:* first real operator use.

**Sizing flag (criterion 3).** Four entries exceeds the two-entry threshold, so the
feature's single-gate sizing is flagged under `## What I'd change` below.

## Consumer-visible contract changes

Enumerated across T01–T04 per `close-discipline.md` §3. **Every entry is an addition.
Zero removals. Zero renames. Zero changes to any pre-existing symbol, file, or
behaviour** — `specfuse/loop/loop.py` and `specfuse/loop/gh_backend.py` were both on the
do-not-touch list and neither appears in any `files_touched` payload in `events.jsonl`.

**Added — Python API, `specfuse.loop.escalation` (new module):**

| Symbol | Kind | Contract |
|---|---|---|
| `NEEDS_HUMAN_LABEL` | `str` constant | `"needs-human"` |
| `DEFAULT_ASSIGNEE` | `str` constant | `"specfuse-operator"` |
| `CATEGORY_LABELS` | `frozenset[str]` | exactly `gate-review`, `blocked-wu`, `triage-question`, `drafting-needed`, `merge-approval` |
| `render_escalation_body(correlation_id, *, category, done_so_far, issue_summary, decision_needed, why_not_auto, options, recommendation) -> str` | function | keyword-only after the ID; `options` is `list[tuple[label, pros, cons]]`; raises `ValueError` on an unknown category or fewer than two options |
| `validate_escalation_body(text) -> list[str]` | function | `[]` means conforming; each finding names the missing part |
| `emit_escalation(correlation_id, *, category, repo, …, assignee=DEFAULT_ASSIGNEE, runner=None) -> str` | function | returns the issue number; idempotent per correlation ID; `runner=None` means the real `gh` |

**Added — issue-body format** (a wire contract: anything parsing these issues, notably
FEAT-2026-0049, depends on it):

- The six `##` part headings from `operator-escalation.md`, in order: *What has been done
  so far*, *What this issue is about*, *What decision is needed, and why*, *Why it did
  not, or could not, close automatically*, *Options, each with pros and cons*,
  *A recommendation*.
- A numbered-answers section headed `Reply with a number`, with ≥2 numbered options.
- The correlation marker `<!-- specfuse:escalation id=<correlation-id> -->`, which is
  both the idempotency key and the parse anchor.

**Added — GitHub label vocabulary.** Six labels that must exist in any repository this
primitive files into (deferral 1). This is the only entry that imposes an obligation
outside the codebase.

**Added — `/attention` skill**, canonical at `plugins/specfuse/skills/attention/SKILL.md`,
vendored byte-identically to `.specfuse/skills/attention/SKILL.md`. New user-facing slash
command; read-only by contract, enforced by `tests/test_attention_nonwriting_guard.py`
over both copies.

**Added — four test modules** (`test_escalation_contract.py`, `test_escalation_emit.py`,
`test_attention_skill_structure.py`, `test_attention_nonwriting_guard.py`).

**Human acknowledgment.** The list is additive-only, so nothing here can break an existing
consumer and there is no breaking change requiring a pre-merge block. Acknowledgment is
the PR review. The one item needing an explicit operator action rather than a nod is the
label vocabulary: the labels must exist before the first real emission, or
`gh issue create` fails.

## What went well

- **The runner seam paid off immediately.** T02 was told to mirror
  `gh_backend.GitHubBackend`'s `_runner` rather than invent a convention, and it did.
  Naming the existing seam and the file to read it in is the difference between reuse and
  a second convention.
- **The positive control did its job as its own work unit.** T04's split — guard and
  control as one WU, separate from the skill it judges — meant the zero in "zero write-verb
  matches" is evidence of a clean skill rather than evidence of a dead regex. At $0.64 it
  was the cheapest unit in the gate.
- **The scope boundary held.** Oracle 8 confirms the dispatch loop still has no call site
  for `emit_escalation`. A primitive that files live GitHub issues stayed out of the
  automatic path, which is what `[FEAT-2026-0003/G3-LESSONS]` demanded.
- **Zero re-arms, zero failed attempts, zero blocked units.** The only halts were the
  pre-existing red baseline, which no work unit caused.

## What I'd change

- **Single-gate sizing — flagged per criterion 3, with a caveat.** Four deferrals against
  a two-entry threshold trips the flag, so here it is. But the honest reading is that the
  flag points at the wrong cause: the deferrals do not come from packing four units into
  one gate, they come from one deliberate decision — no work unit touches live GitHub —
  which `PLAN.md` recorded up front and which a two-gate split would have reproduced
  exactly. A gate 2 would have had to either cross that boundary or inherit all four
  deferrals unchanged. **What would actually have closed them** is one work unit that runs
  `emit_escalation` twice against a scratch repository behind an opt-in environment
  variable, skipped by default. That is a scope change, not a sizing change. Recording
  both readings so the flag is not later mistaken for evidence that the gate was too big.
- **Price the risk the scope boundary already removed at zero.** T02 carried the gate's
  largest budget ($3.50) for live-`gh` discovery risk that criterion 9 had already
  forbidden it from taking, and came in 80.5% under. When a WU's own criteria mandate a
  stub, the integration risk is deferred, not priced — and the deferral belongs in the
  close's `## What the loop did NOT verify` section, where it now is.
- **The idempotency search deserved a named uncertainty, not a stubbed pass.** Deferral 2
  is a real open question about GitHub's search behaviour that the WU's escalation triggers
  half-anticipated ("if the `gh` search syntax… cannot be expressed without a real API call
  to discover it"). The WU satisfied its criteria without ever confronting it. A stub can
  make an unanswered question look answered; that is worth stating at authoring time.

## Terminal verdict

**`met`.** All nine of this close's acceptance criteria are satisfied, and all eight
oracles named by criterion 4 were re-run fresh in this session with exit codes read
directly — 25 tests green, plus the negative grep. All four substantive units' criteria
were verified as written; none rests on a producing WU's self-report.

The verdict is not hedged to `met_locally` because the four deferrals above are not
criteria this gate claimed and failed to verify. Each is a consequence of the no-live-
GitHub boundary that `PLAN.md` declared before any unit ran, and the criteria were
authored stub-scoped to match. Hedging here would misuse `met_locally`, which
`close-discipline.md` §2 reserves for criteria unverifiable in this environment — these
were verified, at the scope they were written to. The residual integration risk is
recorded above as named operator post-merge steps rather than smuggled into a verdict.

The driver owns the terminal flips (gate → `passed`, `PLAN.md` → `done`, roadmap row →
`done`). This close writes none of them.
