# RETROSPECTIVE — FEAT-2026-0048, autonomous bug pipeline

Terminal close of a single-gate feature. Correlation ID
`FEAT-2026-0048/G1-CLOSE`. Everything below was produced in this close session;
where a number or a verdict came from a producing WU's self-report rather than
from a command run here, it says so.

## Gate 1

### 1. What shipped

Four substantive work units, strictly serial, all `done` on attempt 1:

| WU | Deliverable | Files touched (from `events.jsonl` `files_touched`) |
|---|---|---|
| `T01` | Verify FEAT-2026-0044's shipped schema against this plan's assumed table, then add the two bug-lane dials and their resolvers | `specfuse/loop/agent_policy.py`, `.specfuse/agent-policy.yml.example`, `tests/test_bug_lane_policy_contract.py` |
| `T02` | `evaluate_merge_guardrails` — the pure, fail-closed merge-eligibility predicate over six guardrails | `specfuse/loop/bug_lane.py`, `tests/test_bug_lane_guardrails.py` |
| `T03` | GitHub-resident merge-cap state and the triaged-bug intake | `specfuse/loop/bug_lane_state.py`, `tests/test_bug_lane_state.py` |
| `T04` | `run_bug_lane` — fix → PR → guarded merge, with escalation on refusal | `specfuse/loop/bug_lane_run.py`, `tests/test_bug_lane_run.py` |

The dial ships `off`. This repository's own `.specfuse/agent-policy.yml` still
reads `rules.bugs.automerge: "off"` and this close did not touch that file.

### 2. Oracles re-run fresh (close-discipline.md §1) — all ten green

Every command below was run in this session against the working tree, with its
exit code read directly. Nothing here is inherited from a producing WU's
self-report. All commands ran under `.venv/bin/`; `PYTHONPATH` was set to the
repository root where a script was invoked from outside it, because a
`specfuse-loop 0.7.1` wheel is also installed in the venv and shadows the
working tree for any process whose `sys.path[0]` is not the repo (see
§8, finding 3).

| Gate | Command | Exit | Observed |
|---|---|---|---|
| `tests` | `python3 -m unittest discover -s tests -v -b` | **0** | `Ran 2700 tests in 99.281s` — `OK (skipped=3)` |
| `lint` | `ruff check specfuse .specfuse/scripts tests scripts` | **0** | `All checks passed!` |
| `security` | `bandit -r specfuse .specfuse/scripts -ll` | **0** | `No issues identified.` — 18023 LOC scanned, Medium 0 / High 0 |
| `coverage` | `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90` | **0** | `TOTAL 8703 580 93%` |
| `leak-scan` | `python3 .specfuse/scripts/leak_scan.py --all` | **0** | `leak-scan: clean` (gitleaks 8.30.1) |
| `agent-policy-example-lint` | `python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && … .specfuse/agent-policy.yml` | **0** | no findings on either file |
| `event-type-gate` | `python3 .specfuse/scripts/event_type_gate.py` | **0** | `no validation errors across 57 events.jsonl file(s), 1369 event(s) checked` |
| `roadmap-link-gate` | `python3 .specfuse/scripts/roadmap_link_gate.py` | **0** | `0 error(s), 4 warning(s)` — all four warnings are pre-existing unlinked Detail cells (FEAT-2026-0011/0049/0050/0052), none touched by this feature |
| `arm-sweep-gate` | `python3 .specfuse/scripts/arm_sweep_gate.py` | **0** | `evaluable=18 evaluated=18 could_not_evaluate=0` |
| `monitoring-example-lint` | `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` | **0** | `OK — monitoring config is structurally valid (or absent).` |

Four scoped module re-runs, one per producing WU, for the per-criterion state
recorded in `GATE-01-CRITERIA.md`:

| Command | Exit | Observed |
|---|---|---|
| `python3 -m unittest tests.test_bug_lane_policy_contract -v` | **0** | `Ran 22 tests … OK` |
| `python3 -m unittest tests.test_bug_lane_guardrails -v` | **0** | `Ran 35 tests … OK` |
| `python3 -m unittest tests.test_bug_lane_state -v` | **0** | `Ran 11 tests … OK` |
| `python3 -m unittest tests.test_bug_lane_run -v` | **0** | `Ran 31 tests … OK` |

The `code` gate set in `.specfuse/verification.yml` also declares six `bats`
suites (`leak-scan-hook`, `sync-scaffold-bats`, `sync-scaffold-symlinks-bats`,
`init-sh-shim-bats`, `init-skills-bats`, `hookspath-conflict-bats`). This WU's
criterion 1 enumerated ten gates and did not name them, so they were not run
here — see § *What the loop did NOT verify*. Nothing in this feature touches
the operator scripts they cover.

### 3. The three guardrail claims, re-tested from the shipped code

The feature's whole risk argument rests on three claims. All three were
re-tested in this session against the shipped modules — not read, executed —
through a harness written for this close. Every assertion passed.

**Claim 1 — the dial ships `off`, and this repo's live policy still reads `off`.**

| Assertion | Result |
|---|---|
| `resolve_bug_automerge('.specfuse/agent-policy.yml') is False` | `False` ✅ |
| `resolve_bug_automerge()` (default path resolution) `is False` | `False` ✅ |
| `resolve_bug_automerge(<absent file>) is False` | ✅ |
| `resolve_bug_automerge(<policy with no rules.bugs>) is False` | ✅ |
| `resolve_bug_automerge(<automerge: true — the boolean, not the string>) is False` | ✅ |

The last row is the interesting one: the resolver requires the exact string
`"on"`, so the most likely operator typo — a YAML boolean — reads as *off*,
not as *on*.

**Claim 2 — the predicate fails closed on malformed input.**

`evaluate_merge_guardrails` takes seven keyword-only inputs. Each was
malformed in turn against an otherwise-eligible fixture — 43 malformed values
across the seven, plus 7 omission cases. A control ran first: the unmodified
fixture returns `eligible=True`, so every decline below is caused by the
malformation and not by a fixture that could never pass.

| Input | Malformed values exercised | Every case |
|---|---|---|
| `changed_files` | `None`, a bare `str`, `42`, `[1, 2]`, a bare `object()`, `b"tests/"` | `eligible=False`, `unreadable_input` |
| `ci_conclusion` | `None`, `42`, `[]`, a dict, `""`, `b"success"` | `eligible=False`, `ci_not_green` |
| `diff_lines` | `None`, `"40"`, `-1`, `3.5`, `True`, `object()` | `eligible=False`, `unreadable_input` |
| `max_diff_lines` | `None`, `"150"`, `0`, `-5`, `1.5`, `True` | `eligible=False`, `unreadable_input` |
| `provenance` | `None`, a `str`, `42`, `{}`, unknown `kind`, missing `ref`, whitespace `ref` | `eligible=False`, `untraceable_provenance` |
| `max_merges_per_day` | `None`, `"3"`, `0`, `-1`, `2.5`, `True` | `eligible=False`, `unreadable_input` |
| `state_reader` | `None`, `object()`, a reader that **raises**, a reader returning `"three"`, a `str` | `eligible=False`, `unreadable_input` |

**Nothing raised.** The raising `state_reader` is the sharpest case — a
`RuntimeError` out of the GitHub read is caught and converted to a decline
rather than propagating. Separately, omitting any of the seven raises
`TypeError` at the call boundary: they are keyword-only with no defaults, so a
caller cannot silently drop a guardrail input.

`bool` is deliberately rejected everywhere an `int` is expected (`True` is an
`int` in Python, and `max_diff_lines: True` would otherwise mean "cap of 1").

**Claim 3 — `JUDGE_PATHS` is imported, not copied.**

```
$ python3 -c "import specfuse.loop.bug_lane as bl, specfuse.loop.arm_eval as ae; ..."
bug_lane.JUDGE_PATHS is arm_eval.JUDGE_PATHS -> True
id(bug_lane.JUDGE_PATHS)= 4453684544  id(arm_eval.JUDGE_PATHS)= 4453684544
value = ('.specfuse/verification.yml', '.specfuse/hooks/', '.specfuse/rules/',
         '.github/workflows/', 'specfuse/loop/', 'pyproject.toml')
EXIT=0
```

Object identity, in a fresh interpreter — not equality, which a copied literal
would also satisfy. `grep -n JUDGE_PATHS specfuse/loop/bug_lane.py` shows one
import (line 32), one use (line 150), and one docstring mention: no second
definition exists to drift.

### 4. The composite oracle — dial FORCED ON, one guardrail failing at a time

This is the assertion no individual WU could make, and the one that would
catch every WU passing while the lane still merges something it should not. It
runs `run_bug_lane` end to end — `/fix-bug` invocation, PR discovery, diff
read, CI read, provenance read, cap read, decision, merge — against a fake
`gh`/`claude` runner that records every argv, with the dial **forced `on`** in
a temporary policy file written to a `TemporaryDirectory`. This repository's
`.specfuse/agent-policy.yml` was never written, and reads `off` before and
after.

A control ran first, because "did not merge" six times is worthless if the
harness never reaches the merge path at all:

| Case | Outcome | `gh pr merge` calls | Label applied |
|---|---|---|---|
| **CONTROL** — dial on, all six guardrails satisfied | `merged` | **1** | — |
| only `no_test_evidence` failing | `declined` | **0** | `no_test_evidence` |
| only `ci_not_green` failing | `declined` | **0** | `ci_not_green` |
| only `diff_too_large` failing | `declined` | **0** | `diff_too_large` |
| only `judge_path_touched` failing | `declined` | **0** | `judge_path_touched` |
| only `untraceable_provenance` failing | `declined` | **0** | `untraceable_provenance` |
| only `daily_cap_reached` failing | `declined` | **0** | `daily_cap_reached` |

Six for six: with the dial on and exactly one guardrail failing, no merge
command reaches the runner, the PR is labeled with the declining reason, and
it is left open. The control proves the path was live. The four WUs compose.

The `judge_path_touched` fixture is worth naming: its diff is
`tests/test_fix.py` plus `specfuse/loop/loop.py` — a legitimate, test-first,
CI-green, in-cap, traceable bug fix to the driver itself. It does not merge,
because `specfuse/loop/` is in `JUDGE_PATHS`. That is the guardrail doing
exactly the job it exists for.

### 5. The solo-drafting decision audit — all seven

This feature was drafted **solo, with no operator interview**, on operator
instruction (2026-08-09). `PLAN.md` § *Assumed decisions* lists seven
decisions taken without a human. What the implementation did to each:

| # | Assumed decision | Verdict |
|---|---|---|
| 1 | Single gate, single terminal `close` — four substantive WUs at the ceremony-proportionality threshold | **Validated.** All four passed on attempt 1; no `plan-next` ran unattended; the close is the only load-bearing ceremony. |
| 2 | The guardrail predicate is pure and fails closed, copying `autofix.decide`'s docstring promise | **Validated, and the strongest of the seven.** 50 fail-closed cases re-proven in §3. The purity half is also real: the module opens no file and spawns no process — every input, including the cap-state reader, is injected. |
| 3 | The merge cap's state lives on GitHub, never on disk | **Validated in shape, unexercised in fact.** `GitHubMergeCapState` re-derives the count from `<!-- specfuse:bug-automerge at=… -->` markers on merged PRs on every call; no counter is maintained anywhere. But no call has ever left the process — every test and this close's harness inject a fake runner, so the `gh pr list --state merged` read has never run against a real repository. See § *What the loop did NOT verify*. |
| 4 | Never-auto-merge paths are `arm_eval.JUDGE_PATHS`, imported not retyped | **Validated** by object identity (§3, claim 3). |
| 5 | Test-first evidence is checked structurally, not semantically | **Validated as specified, and the decision that strained hardest.** `_has_test_evidence` is `any(path.startswith("tests/"))`. That is exactly what was decided, and the anti-model-approval reasoning behind it holds. But two consequences were not priced: an empty `tests/test_noop.py` satisfies it, and — more seriously for a scaffold shipped to other projects — a repository whose tests live in `spec/`, `src/**/__tests__/`, or `*_test.go` has **no** path that satisfies it, so its bug lane can never merge anything. The prefix is hardcoded, with no dial. This repo's own layout is the only one it fits. |
| 6 | Guardrail failure labels the PR and leaves it open for a human | **Validated in the happy path, with a real gap.** The label is applied, the PR is not closed, no retry happens — all re-proven in §4. The gap: the six reason constants are not in `specfuse/loop/labels.py`'s `LABEL_REGISTRY`, and the `gh pr edit --add-label` call passes `check=True`. On a real repository that has not been provisioned with those six labels, the declining path raises instead of leaving a labeled PR. See §8, finding 1. |
| 7 | `bug_automerge` reads from `rules.bugs.automerge`, not a new top-level dial | **Validated.** `resolve_bug_automerge` reads exactly that path; no second home was created. |

Nothing in the audit is *unexercised* in the sense of "never touched" — but
decisions 3 and 5 are unexercised in the sense that matters: decision 3 has
never met a real GitHub API, and decision 5 has never met a repository whose
tests are not under `tests/`.

### 6. What T01 found about the schema this feature was drafted against

This feature was drafted the same evening as FEAT-2026-0044 and **before 0044
ran**, so every schema reference in `PLAN.md` was an assumption about a file
that did not exist. `T01` existed for exactly one reason: verify the shipped
schema against the assumed table and escalate on divergence rather than
adapting silently.

**T01 did not escalate: every row of the assumed table held.**
`tests/test_bug_lane_policy_contract.py::TestAssumedSurfaces` asserts all six
rows — the module exists, `load_policy(path=None)` returns the parsed mapping,
`validate_agent_policy(path=None)` returns `ERROR: ` / `WARN: `-prefixed
findings, and the shipped example declares `rules.bugs.automerge`,
`rules.bugs.min_severity`, and `rules.bugs.preempt`. That class re-ran green in
this close.

**One thing did diverge, and it cost nothing — by luck, not by design.** The
plan's assumed table wrote the dial's values as `off | on`, unquoted. The
shipped schema requires them quoted: this repo's `_miniyaml` rejects a bare
`off` outright (`only lowercase true/false accepted as booleans (got 'off')`)
rather than coercing it, so the shipped example and the live policy both write
`automerge: "off"`. FEAT-2026-0044's own close already recorded this as a
pending lesson against *its* T01, naming FEAT-2026-0048 as the feature drafted
against the unquoted literal. The reason it cost nothing here is that this
feature's checks were all expressible against the *parsed* value —
`resolve_bug_automerge` compares to the string `"on"` after parsing, and never
sees the source spelling. Had any acceptance criterion been written as a grep
for the literal `automerge: off`, T01 would have escalated on a purely
cosmetic difference, or worse, adapted to it.

That is the honest summary of the drafted-against-a-nonexistent-schema risk on
this feature: the mitigation was mechanical and it worked, the one divergence
that existed was cosmetic, and the reason it stayed cosmetic is a property of
how the criteria happened to be phrased rather than something the plan
controlled.

### 7. Lessons

Three lessons are staged in `LEARNINGS-pending.md` in this feature directory,
not in `.specfuse/LEARNINGS.md`. This feature runs under
`autonomy_default: auto`, so `assert_learnings_staged_under_auto` refuses a
close whose diff touches the repo-wide file — a human promotes them at PR
review instead. **Nothing generalizes** directly into `.specfuse/LEARNINGS.md`
from this close; that is the mechanism working, not an absence of lessons.

The three: (a) a guardrail whose evidence test is a hardcoded path prefix is a
repo-shaped guardrail, and shipping it in a scaffold makes it silently
inoperative elsewhere; (b) a code path that writes a label must be reconciled
against the label registry in the same WU, or the failure path fails; (c) the
solo-drafting cost signature FEAT-2026-0044 recorded **recurred here, exactly**
— which promotes it from an observation to a rule.

### 8. Incidental findings — reported, not repaired

This WU may not touch any source file under `specfuse/`. All three are
recorded here and in `LEARNINGS-pending.md`; none is repaired.

1. **The six declining-reason labels are not in `LABEL_REGISTRY`, and the
   label write is `check=True`.** `run_bug_lane`'s declining path calls
   `gh pr edit … --add-label <reason>` with `check=True`, where `<reason>` is
   one of `no_test_evidence`, `ci_not_green`, `diff_too_large`,
   `judge_path_touched`, `untraceable_provenance`, `daily_cap_reached`.
   `specfuse/loop/labels.py`'s registry holds ten names and none of these.
   `provision_labels` therefore never creates them, and on a repository where
   they do not exist `gh` exits non-zero and the `check=True` runner raises —
   so the "label it and leave it open for a human" outcome becomes an
   exception on precisely the path that is supposed to be the safe one. The
   comparable precedent, `autofix_run._apply_failed_label`, is also
   `check=True` but writes `AUTOFIX_FAILED_LABEL`, which *is* registered.
   Fix shape: add the six to `LABEL_REGISTRY`, or make the label write
   best-effort the way `triage.apply_triage` already does. Not a merge-safety
   defect — it cannot cause a merge — but it breaks the declining path's
   stated contract on a real repo.

2. **`_has_test_evidence` hardcodes `tests/`.** Covered in §5, decision 5.
   Consequence for a downstream project: the bug lane is permanently
   ineligible, silently, and reads as "the guardrails are working" in review.

3. **A `specfuse-loop 0.7.1` wheel in `.venv` shadows the working tree.**
   `specfuse` resolves as a namespace package, so a process whose
   `sys.path[0]` is not the repository root imports `specfuse.loop` from
   `site-packages` — where `agent_policy.resolve_bug_automerge` does not
   exist. This bit this close session once (a `ModuleNotFoundError` from a
   harness run out of a temp directory) and is a live footgun for any script
   invoked by absolute path. Not caused by this feature; recorded because a
   close is where an environment hazard gets written down.

4. **`.specfuse/agent-policy.yml`'s comment on the dial is now stale.** It
   reads `automerge: "off"   # FEAT-2026-0048 owns enforcement; not built yet`.
   Enforcement is now built. The comment was left untouched deliberately: this
   WU's **Do not touch** list names that file, and a close session editing the
   policy file — even a comment on the dial line — is exactly the move the
   rule exists to prevent. It belongs in the same operator commit that decides
   whether to flip the dial.

## Consumer-visible contract changes

Five consumer-visible changes. Enumerated per `close-discipline.md` §3 and
appended to `CHANGELOG.md`'s `Unreleased`, traced `FEAT-2026-0048`. **Human
acknowledgment has not been obtained** — this is a non-interactive `claude -p`
dispatch — and that is the first entry in the hedged-verdict follow-up record
below.

- **Two new optional dials under `rules.bugs` in `.specfuse/agent-policy.yml`:
  `max_diff_lines` (int > 0, default 150) and `max_merges_per_day` (int > 0,
  default 3).** Both are validated by `validate_agent_policy`, which now
  returns an `ERROR: ` finding naming the key for a zero, a negative, or a
  non-int. Both are optional and both have defaults, so **an existing policy
  file needs no edit** and continues to validate clean. Documented in
  `.specfuse/agent-policy.yml.example`. Note the pre-existing spelling
  constraint they inherit: values under `rules.bugs` that could parse as YAML
  booleans must be quoted, because this repo's parser rejects a bare `off`
  rather than coercing it.
- **`specfuse.loop.agent_policy` gains two public resolvers:
  `resolve_bug_automerge(path=None) -> bool` and
  `bug_lane_limits(path=None) -> dict`.** `resolve_bug_automerge` returns
  `True` only when `rules.bugs.automerge` is exactly the string `"on"` — an
  absent file, an absent key, and the boolean `True` all return `False`.
  `bug_lane_limits` returns `{"max_diff_lines": int, "max_merges_per_day": int}`,
  falling back to `(150, 3)`. Purely additive; no existing behaviour in that
  module changed.
- **Three new importable modules ship in the wheel:
  `specfuse.loop.bug_lane`, `specfuse.loop.bug_lane_state`, and
  `specfuse.loop.bug_lane_run`.** Nothing previously occupied those import
  paths. Public surface: `bug_lane.evaluate_merge_guardrails` (keyword-only,
  pure, fail-closed), `bug_lane.MergeDecision`, `bug_lane.MergeCapStateReader`,
  and the eight `REASON_*` constants; `bug_lane_state.GitHubMergeCapState`,
  `merges_last_24h`, `record_merge`, `render_merge_marker`,
  `parse_merge_marker`, `triaged_bug_intake`, `ROLLING_WINDOW_SECONDS`; and
  `bug_lane_run.run_bug_lane`, `pr_ci_conclusion`, `BugLaneResult`, plus the
  outcome constants. Every GitHub access in all three goes through an injected
  `runner` callable, so a consumer supplies its own; none of them reaches the
  network on its own.
- **A new published marker on merged PRs:
  `<!-- specfuse:bug-automerge at={epoch_seconds} -->`.** Written by
  `record_merge` onto the PR body after an auto-merge, and the sole source of
  the rolling-24h merge count, which is re-derived from these markers on every
  call rather than maintained as a counter. **Once any PR in any repository
  carries one, changing this format orphans it** — the merge would stop
  counting toward the cap. Treat the format as frozen. `record_merge` is
  idempotent: a second call for the same PR writes nothing. Note the exact
  shape: it carries an `at=` timestamp, not the bare
  `<!-- specfuse:bug-automerge -->` this WU's own criterion 9 anticipated.
- **A triaged-bug intake for the bug lane —
  `bug_lane_state.triaged_bug_intake(runner, repo, *, limit=100)`** — returning
  open issues carrying a `bug`-category `<!-- specfuse:triage … -->` marker
  (FEAT-2026-0045's format, parsed with that module's own parser, not a second
  copy), excluding any issue already labeled `auto-fix-attempted-failed`.
  **Correction to this WU's criterion 9:** the intake shipped as this importable
  function, *not* as a change to the `/fix-bug` skill. No skill file in this
  feature's diff was modified — `events.jsonl`'s `files_touched` across
  `T01`–`T04` lists only the four modules, their four test files, and the WU
  documents. `/fix-bug`'s own contract, including every refusal path, is
  unchanged. A consumer that expected a new slash-command surface will not find
  one; the caller is FEAT-2026-0049's scheduler.

## What the loop did NOT verify

No predecessor auto-close debt markers exist in this feature — a search for
`specfuse:autoclose-debt` across the feature folder finds nothing — so
`close-g` has nothing to reconcile.

| Item | Why not verified in-loop | Where it actually gets checked |
| --- | --- | --- |
| **A live auto-merge against a real PR** — the end-to-end path from a triaged issue to a merged pull request | This feature never turns the dial on. `.specfuse/agent-policy.yml` reads `off` and the WU forbids flipping it, so the merge call has only ever executed against a fake runner. The composite oracle (§4) forces the dial on in a temporary in-memory policy, which proves the *decision logic* composes but never issues a real `gh pr merge`. This is an operator-deferred oracle by construction, not an oversight. | An operator flipping `rules.bugs.automerge: "on"` in a separate, reviewed commit, then observing one real bug fix through the lane. It is not an acceptance criterion of any WU in this feature — no unit claims to merge a real PR — but it is the claim a reader will most want evidence for. |
| **Every `gh` interaction in all three new modules** — `pr list`, `pr view`, `pr checks`, `pr edit`, `pr merge`, `issue view`, `issue create` | Every call site takes an injected `runner`, and every test and this close's harness inject a fake. No process in this feature's history has invoked `gh`. Argv shapes are asserted; responses are fabricated. | The first real run of the lane. The most likely failure is an argv or `--json` field that `gh` rejects — e.g. `gh pr checks --json conclusion` returning a shape the parser reads as `unknown`, which fails *closed* (no merge) rather than dangerously. |
| **`T01#1`, `T02#1`, `T03#1`, `T04#1` — the red-test half** ("this test fails on HEAD **before** this WU runs") | Point-in-time oracles. The edits are landed; re-running against a tree that no longer exists needs `git`, which a work-unit session may not use. The re-runnable half — the test exists and passes now — was re-run and is recorded `state: pass` in `GATE-01-CRITERIA.md`. | Each producing WU's own RESULT and the driver's red-test guard at the moment that unit ran. |
| **The six `bats` suites in the `code` gate set** (`leak-scan-hook`, `sync-scaffold-bats`, `sync-scaffold-symlinks-bats`, `init-sh-shim-bats`, `init-skills-bats`, `hookspath-conflict-bats`) | This WU's criterion 1 enumerated ten gates by name and did not include them. Recorded rather than quietly treated as out of scope. | CI, via `scripts/smoke-test.sh`, which derives its gate list from `.specfuse/verification.yml` and runs all sixteen. Nothing in this feature touches the operator scripts they cover. |
| **Human acknowledgment of the consumer-visible contract-change list** (`close-discipline.md` §3, this WU's criterion 9) | A `claude -p` dispatch has no human to ask, and consent cannot be recorded by the session that needs it without fabricating it. | Operator review at the gate boundary, or `/accept-hedged-close`. |
| **Decision 3 in fact — that GitHub-resident state actually survives an ephemeral runner** | The design is right (nothing on disk, count re-derived per call), but it has never been observed across two invocations in different containers. | The first two-invocation run on a real runner. `merges_last_24h` fails closed to `10**9` on any read failure, so the failure mode is "never merges", not "exceeds the cap". |
| **The stale comment on the dial line in `.specfuse/agent-policy.yml`** | The file is on this WU's **Do not touch** list. | The operator commit that decides whether to flip the dial. |

## Hedged-verdict follow-up record

### Human acknowledgment of the consumer-visible contract-change list

- **criterion (verbatim):** "**Consumer-visible contract changes** enumerated
  (`close-discipline.md` §3): the two new `rules.bugs` dials, the new
  `specfuse/loop/bug_lane*.py` modules, the `/fix-bug` lane gaining a
  triaged-issue intake, and the new `<!-- specfuse:bug-automerge -->` marker on
  merged PRs — or exactly `n/a — no consumer-visible contract change` if
  genuinely empty, which it is not."
- **why it is unverifiable here:** the enumeration is written and the
  `CHANGELOG.md` `Unreleased` appends are done. `close-discipline.md` §3
  additionally requires the close to *block on explicit human acknowledgment*
  of the list. This is a non-interactive dispatch; there is nobody to ask, and
  recording consent that was never given would be a fabrication. The
  enumeration also carries two corrections a human should specifically read —
  the intake shipped as a function rather than a `/fix-bug` change, and the
  marker carries an `at=` timestamp — so this is not a rubber stamp.
- **exact re-run condition that would upgrade the verdict:** an operator reads
  the § *Consumer-visible contract changes* list above and accepts it, at the
  gate boundary or through `/accept-hedged-close`.
- **kind:** `acceptance-discharged`

### The lane has never merged a real pull request

- **criterion (verbatim):** "**The composite oracle** no individual WU could
  run: with the dial forced `on` in a temporary in-memory policy, a PR fixture
  failing exactly one guardrail does not merge — repeated for all six."
- **why it is unverifiable here:** the criterion as written *is* met — all six
  cases ran and passed in §4, with a control proving the merge path was live.
  What is not met, and what this entry exists to name, is the thing the
  criterion is a proxy for: the lane has never issued a real `gh pr merge`, so
  every claim about it rests on fabricated `gh` responses. This feature
  deliberately never turns the dial on, so no in-repo work can close that gap.
- **exact re-run condition that would upgrade the verdict:** an operator flips
  `rules.bugs.automerge: "on"` in a separate reviewed commit and one real bug
  fix goes through the lane end to end, producing a merged PR carrying a
  `<!-- specfuse:bug-automerge at=… -->` marker. Observing the marker on a real
  merged PR discharges this and the GitHub-resident-state question together.
- **kind:** `externally-verifiable-later`

### The declining path raises on a repository without the six reason labels

- **criterion (verbatim):** "On a declining path the PR is labeled with the
  guardrail's reason constant and left **open** — a test asserts no close
  command and no re-invocation reaches the runner." (`T04`, criterion 7)
- **why it is unverifiable here:** the criterion passes against an injected
  runner, which accepts any `--add-label` value. Against real `gh`, the six
  reason constants are not in `LABEL_REGISTRY`, `provision_labels` never
  creates them, and the call passes `check=True` — so on an unprovisioned
  repository the declining path raises rather than leaving a labeled PR open.
  Repairing it means editing `specfuse/loop/labels.py` or
  `specfuse/loop/bug_lane_run.py`, and this WU may not touch any source file
  under `specfuse/`.
- **exact re-run condition that would upgrade the verdict:** the six reason
  constants are added to `LABEL_REGISTRY` (or the label write is made
  best-effort, following `triage.apply_triage`), and a declining run is
  observed against a real repository leaving the PR open and labeled.
- **kind:** `externally-verifiable-later`

### The test-evidence guardrail is inoperative outside a `tests/` layout

- **criterion (verbatim):** "**Test-first evidence is checked structurally, not
  semantically.** The guardrail asserts the PR's diff adds at least one test
  file and that CI ran green" (`PLAN.md` § *Assumed decisions*, decision 5).
- **why it is unverifiable here:** the guardrail is implemented as
  `any(path.startswith("tests/"))`, with the prefix hardcoded and no dial. In
  this repository that is correct and every test passes. In a consumer project
  whose tests live in `spec/`, `src/**/__tests__/`, or alongside sources as
  `*_test.go`, no diff can ever satisfy it, so the lane silently never merges —
  and no oracle available in this repository can observe that, because this
  repository has the layout the prefix assumes. It is an assumed decision taken
  without an operator, and widening it is a scope change, not a fix.
- **exact re-run condition that would upgrade the verdict:** an operator
  decides whether the prefix becomes configurable (a `rules.bugs.test_paths`
  dial is the obvious shape) or is deliberately frozen as a
  this-repo-only guardrail, and the decision is recorded. Either answer
  discharges it; the open question is what makes it hedged.
- **kind:** `acceptance-discharged`

## Cost analysis

Actuals are read from this feature's `events.jsonl` — the `task_completed`
payload's `cost_usd` and `cumulative_cost_usd` per WU. `re_arm_count` is `0`
and `cumulative_cost_usd` equals `cost_usd` for all four substantive units, so
no re-arm cycle contributed recorded spend.

### Per-unit reconciliation against `planned_cost_usd`

| WU | Planned | Actual | Delta | Variance | Attempts |
|---|---|---|---|---|---|
| `T01` | $2.50 | $0.805799 | −$1.694201 | **−67.8%** | 1 |
| `T02` | $5.00 | $1.038923 | −$3.961077 | **−79.2%** | 1 |
| `T03` | $4.00 | $0.827689 | −$3.172311 | **−79.3%** | 1 |
| `T04` | $4.50 | $3.597465 | −$0.902535 | −20.1% | 1 |
| **`T01`–`T04`** | **$16.00** | **$6.269876** | **−$9.730124** | **−60.8%** | 4 |
| `G1-CLOSE` | $5.00 | *not yet recorded* | — | — | 1 (this session) |

### Gate and feature totals

- **Gate 1 budget: $26.00.** Recorded spend at the time this section was
  written is $6.27, or 24.1% of the budget. Adding this close's $5.00 estimate
  brings the projection to about $11.27 — roughly 43% of the gate budget.
- **Feature planned total: $21.00** (`PLAN.md` frontmatter). The five WUs'
  `planned_cost_usd` values sum to exactly $21.00, so the plan is internally
  consistent — $2.50 + $5.00 + $4.00 + $4.50 + $5.00.
- **Gate budget headroom over the plan: $5.00.** The gate was budgeted 24%
  above the sum of its units' estimates. None of that headroom was needed.

### The three units over 50% variance — one cause, and it is not efficiency

`T01` (−67.8%), `T02` (−79.2%) and `T03` (−79.3%) all came in more than 50%
under plan, and none of the three is thin: `T02` delivered a 185-line module
plus a 253-line test file with 35 tests at 21% of its estimate. The cause is an
accounting error, not unusual productivity, and it is the **same cause
FEAT-2026-0044's close already recorded against its own four units** (−69%,
−55%, −62%, −80%). Both features were drafted solo in the same unattended
session, and a solo-drafted plan front-loads every load-bearing string into the
WU body: `T02`'s work unit named the module path, the function signature, the
six reason constants, the module to copy the shape from (`autofix.decide`), and
the exact import to use for `JUDGE_PATHS`. A unit given all of that spends
nothing on discovery — and discovery is precisely what an interview-drafted
estimate implicitly prices. `T04` is the control that confirms the diagnosis:
it is the one unit that had to *build* something the plan could not hand it
(`pr_ci_conclusion`, the one mechanism the existing-mechanism search found
missing), and it is the only one inside 50% at −20.1%.

This matters beyond bookkeeping. Persistently over-planned unit costs inflate
gate budgets, and the gate budget is the control that is supposed to stop a
runaway feature. A gate budgeted at $26.00 that reliably spends $11 is not a
safety margin; it is a brake with slack in the cable. The rule that follows —
price a solo-drafted, string-complete WU as transcription-plus-tests rather
than design-plus-implementation — is staged in `LEARNINGS-pending.md`, and it
is now a *recurrence*, not an observation.

### What `events.jsonl` does not contain

Three dispatches in this gate were killed externally and re-armed, leaving
`chore(loop): re-arm FEAT-2026-0048/T03 after an external kill`,
`… /T04 after an external kill`, and
`chore(loop): commit dispatch scaffold and re-arm FEAT-2026-0048/G1-CLOSE` in
the branch history. A killed session writes no `attempt_outcome`, so whatever
those dispatches spent before dying is **absent from `events.jsonl` and absent
from every number above.** The reconciliation is complete over recorded
attempts and understates true spend by an unknown amount. Recording the gap is
the honest move; inventing an estimate for it would not be.

Separately, the captured oracle output injected into this session's prompt
lists a different set of commit SHAs for the same commit subjects than the
session's own start-of-session snapshot (`5790bad`/`13e4938` versus
`da380a7`). That is consistent with the pre-dispatch capture having been taken
during the killed `G1-CLOSE` dispatch rather than this one. This session may
not run `git`, so it was not investigated further; it is noted so a reader does
not treat the two lists as contradictory evidence.

### Failure-class breakdown

| failure_class | non-passed attempts | scope |
|---------------|---------------------|-------|
| (none) | 0 | substantive WUs `T01`–`T04` — the guard's scope |
| **total in guard scope** | **0** | — |

Every substantive work unit passed on attempt 1. No `attempt_outcome` event in
this feature's `events.jsonl` carries a non-null `failure_class`, and no
`outcome` other than `passed` appears. The three externally-killed dispatches
described above produced no `attempt_outcome` at all, so they are not a failure
class — they are missing data, accounted for in the section above rather than
here.

## Hedged verdict accepted

- **Accepted verdict:** `met_locally`
- **Operator reason (verbatim):** "the core functionality has been delivered, will need a separate feature to test it and issues have been created for followups"
- **Contract-change list:** acknowledged by the operator at PR review (#1312), discharging the first entry.
- **Recorded:** 2026-08-10T11:36:22+00:00

The verdict ceiling at acceptance time was **rework exists** — two entries are
`externally-verifiable-later` and neither was discharged before acceptance. They
ship genuinely open.

**Tracking surfaces opened at acceptance** (recorded here, not stitched into the
verbatim entries below):

- *The declining path raises on a repository without the six reason labels* — the
  review found the scope wider than the entry states: the eight `REASON_*` values are
  absent from `LABEL_REGISTRY` entirely, so `provision_labels` creates them in **no**
  repository, this one included. Filed as **#1420**, priority, to be fixed on its own
  branch with its own red-green proof rather than patched in here.
- *The test-evidence guardrail is inoperative outside a `tests/` layout* — filed as
  **#1418** with both discharge options (configurable `rules.bugs.test_paths` dial, or
  a deliberate this-repo-only freeze).

### Follow-ups carried forward, verbatim and open

## Hedged-verdict follow-up record

### Human acknowledgment of the consumer-visible contract-change list

- **criterion (verbatim):** "**Consumer-visible contract changes** enumerated
  (`close-discipline.md` §3): the two new `rules.bugs` dials, the new
  `specfuse/loop/bug_lane*.py` modules, the `/fix-bug` lane gaining a
  triaged-issue intake, and the new `<!-- specfuse:bug-automerge -->` marker on
  merged PRs — or exactly `n/a — no consumer-visible contract change` if
  genuinely empty, which it is not."
- **why it is unverifiable here:** the enumeration is written and the
  `CHANGELOG.md` `Unreleased` appends are done. `close-discipline.md` §3
  additionally requires the close to *block on explicit human acknowledgment*
  of the list. This is a non-interactive dispatch; there is nobody to ask, and
  recording consent that was never given would be a fabrication. The
  enumeration also carries two corrections a human should specifically read —
  the intake shipped as a function rather than a `/fix-bug` change, and the
  marker carries an `at=` timestamp — so this is not a rubber stamp.
- **exact re-run condition that would upgrade the verdict:** an operator reads
  the § *Consumer-visible contract changes* list above and accepts it, at the
  gate boundary or through `/accept-hedged-close`.
- **kind:** `acceptance-discharged`

### The lane has never merged a real pull request

- **criterion (verbatim):** "**The composite oracle** no individual WU could
  run: with the dial forced `on` in a temporary in-memory policy, a PR fixture
  failing exactly one guardrail does not merge — repeated for all six."
- **why it is unverifiable here:** the criterion as written *is* met — all six
  cases ran and passed in §4, with a control proving the merge path was live.
  What is not met, and what this entry exists to name, is the thing the
  criterion is a proxy for: the lane has never issued a real `gh pr merge`, so
  every claim about it rests on fabricated `gh` responses. This feature
  deliberately never turns the dial on, so no in-repo work can close that gap.
- **exact re-run condition that would upgrade the verdict:** an operator flips
  `rules.bugs.automerge: "on"` in a separate reviewed commit and one real bug
  fix goes through the lane end to end, producing a merged PR carrying a
  `<!-- specfuse:bug-automerge at=… -->` marker. Observing the marker on a real
  merged PR discharges this and the GitHub-resident-state question together.
- **kind:** `externally-verifiable-later`

### The declining path raises on a repository without the six reason labels

- **criterion (verbatim):** "On a declining path the PR is labeled with the
  guardrail's reason constant and left **open** — a test asserts no close
  command and no re-invocation reaches the runner." (`T04`, criterion 7)
- **why it is unverifiable here:** the criterion passes against an injected
  runner, which accepts any `--add-label` value. Against real `gh`, the six
  reason constants are not in `LABEL_REGISTRY`, `provision_labels` never
  creates them, and the call passes `check=True` — so on an unprovisioned
  repository the declining path raises rather than leaving a labeled PR open.
  Repairing it means editing `specfuse/loop/labels.py` or
  `specfuse/loop/bug_lane_run.py`, and this WU may not touch any source file
  under `specfuse/`.
- **exact re-run condition that would upgrade the verdict:** the six reason
  constants are added to `LABEL_REGISTRY` (or the label write is made
  best-effort, following `triage.apply_triage`), and a declining run is
  observed against a real repository leaving the PR open and labeled.
- **kind:** `externally-verifiable-later`

### The test-evidence guardrail is inoperative outside a `tests/` layout

- **criterion (verbatim):** "**Test-first evidence is checked structurally, not
  semantically.** The guardrail asserts the PR's diff adds at least one test
  file and that CI ran green" (`PLAN.md` § *Assumed decisions*, decision 5).
- **why it is unverifiable here:** the guardrail is implemented as
  `any(path.startswith("tests/"))`, with the prefix hardcoded and no dial. In
  this repository that is correct and every test passes. In a consumer project
  whose tests live in `spec/`, `src/**/__tests__/`, or alongside sources as
  `*_test.go`, no diff can ever satisfy it, so the lane silently never merges —
  and no oracle available in this repository can observe that, because this
  repository has the layout the prefix assumes. It is an assumed decision taken
  without an operator, and widening it is a scope change, not a fix.
- **exact re-run condition that would upgrade the verdict:** an operator
  decides whether the prefix becomes configurable (a `rules.bugs.test_paths`
  dial is the obvious shape) or is deliberately frozen as a
  this-repo-only guardrail, and the decision is recorded. Either answer
  discharges it; the open question is what makes it hedged.
- **kind:** `acceptance-discharged`

## Cost analysis

