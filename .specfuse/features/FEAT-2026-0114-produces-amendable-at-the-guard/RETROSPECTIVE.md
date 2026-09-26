# Retrospective — FEAT-2026-0114 gate 1

## Measurements

### feature_oracle: PASS

Fresh run, this session, on `HEAD` (`23d5023d4b3748ebb9c42107f476a4becbd07683`),
unsandboxed (the sandboxed run fails every test in the module with
`loop.py: cannot create a directory under
'/Users/christian/.claude/session-env'`, a sandbox deny-list hit, not a defect
— see `sandbox_blocks_git_network_and_gh` precedent):

```
$ python3 -m unittest tests.test_produces_amendment_e2e -v -b
test_amended_path_is_dropped_and_pass_proceeds ... ok
test_amendment_disabled_by_project_default_is_still_refused ... ok
test_dropping_every_declared_path_is_still_refused ... ok

Ran 3 tests in 1.815s

OK
```
Exit code: 0.

### Per-criterion oracle re-runs (this session, fresh, same tree)

All 17 criteria across T01, T02, T02H, T03, T04 were re-verified fresh this
attempt (0 carried forward — this is the first close attempt on this gate).
Full detail — criterion text, oracle command, kind, state, sha, attempt — is
recorded per-entry in `GATE-01-CRITERIA.md`. Summary: all 17 `pass`, all 17
`kind: narrow`, all re-run against `23d5023d4b3748ebb9c42107f476a4becbd07683`
this attempt (`attempt: 1`). Commands run and their exit codes:

| WU | oracle command | exit |
| --- | --- | --- |
| T01#1-3 | `python3 -m unittest tests.test_produces_amendment_e2e -v -b` | 0 |
| T01#4 | `python3 -m unittest tests.test_produces_justification tests.test_guard_repair_e2e tests.test_deliverable_presence_gate tests.test_attempt_outcome_contract -v -b` | 0 |
| T02#1-2 | `python3 -m unittest tests.test_produces_repair_note -v -b` | 0 |
| T02#3 | `python3 -m unittest tests.test_deterministic_refusal_repeat tests.test_guard_repair_e2e tests.test_guard_refusal_failure_excerpt -v -b` | 0 |
| T02H#1 | `python3 -m unittest tests.test_produces_justification -v -b` | 0 |
| T02H#2 | `python3 -m unittest tests.test_produces_repair_note -v -b` | 0 |
| T02H#3 | `python3 -m unittest tests.test_produces_amendment_e2e tests.test_guard_repair_e2e tests.test_produces_repair_note -v -b` | 0 |
| T03#1-2 | `python3 -m unittest tests.test_judge_sees_dropped_produces -v -b` | 0 |
| T03#3 | `python3 -m unittest tests.test_judge_module tests.test_judge_close_path tests.test_judge_path_registry -v -b` | 0 |
| T04#1 | `grep -c "produces_amended" .specfuse/rules/result-contract.md docs/methodology.md .specfuse/skills/authoring-work-units/SKILL.md` | 0 (counts: 2, 2, 1) |
| T04#2 | `grep -n "produces_amendable" .specfuse/verification.yml.example docs/methodology.md` | 0 |
| T04#3 | `scripts/sync-scaffold.sh && python3 -m unittest tests.test_scaffold_data_in_sync -v -b` | 0 (already in sync, 29 files checked) |
| T04#4 | `python3 .specfuse/scripts/leak_scan.py --all` | 0 (`leak-scan: clean`) |

### Produces refusal / amendment activity this gate

`no produces refusal or amendment occurred in this gate`

Read from this feature's own `events.jsonl`: no `attempt_outcome` event in the
file carries `failure_class: produces_not_in_diff`, and no `attempt_outcome`
carries `produces_amended` in its payload. The one non-passing attempt
recorded (`FEAT-2026-0114/T04`, first cycle, `2026-09-26T15:23:16Z`) carries
`failure_class: "tests"` with `failure_signature:
test_justifying_the_wrong_path_or_nothing_useful_is_still_refused` — a
pre-existing-test regression (see Failure-class breakdown below), not a
`produces_not_in_diff` refusal. The feature that builds the amendment/refusal
machinery exercised it only inside its own oracle's stubbed `loop.run()`
harness (`tests.test_produces_amendment_e2e`, `tests.test_produces_repair_note`),
which is what T01#1–3/T02#1–2 above re-confirm; it has not yet fired on a real
dispatched unit anywhere in this repo's own event history.

## Cost analysis

| WU | planned_cost_usd | actual (sum of `attempt_outcome.cost_usd`) | attempts | delta (planned − actual) |
| --- | ---: | ---: | ---: | ---: |
| T01 | $6.00 | $1.078728 | 1 | +$4.921272 under |
| T02 | $4.00 | $1.229695 | 1 | +$2.770305 under |
| T02H | $3.00 | $0.296324 | 1 | +$2.703676 under |
| T03 | $4.00 | $0.779243 | 1 | +$3.220757 under |
| T04 | $3.00 | $2.856274 (attempt 1 failed $1.226250 + attempt 2 passed $1.630024) | 2 (one re-arm cycle) | +$0.143726 under |
| **substantive total** | **$20.00** (T01+T02+T03+T04 as originally planned) | **$6.240264** | — | **31% of the planned substantive spend** |

`T02H` was not in the feature's original task graph — `PLAN.md`'s task-graph
comment records it as hygiene added at the gate-1 broad run, so its $3.00 is
additional to, not drawn from, the $22.00 total `PLAN.md` records
(`T01+T02+T03+T04+G1-CLOSE = 6+4+4+3+5 = 22`). `G1-CLOSE`'s own actual cost is
not reconciled here: this session's `attempt_outcome` has not been written
yet (it is written by the driver after this WU's own attempt concludes), so
there is nothing on disk yet to sum.

`T04` is the one WU whose actual approaches its plan: its first attempt
($1.226250) failed on a regression in code T02 had just landed (see below),
consuming budget on a failure it did not cause, before a second attempt
($1.630024) passed once `T02H` supplied the fix. Summing `attempt_outcome`
rows across the arming cycle (rather than reading `cumulative_cost_usd` alone)
is the reconciliation this repo's own `LEARNINGS.md` already names for a
re-armed unit — no cost surprise here, just the same rule applied.

### Failure-class breakdown

One non-passing `attempt_outcome` in this gate's `events.jsonl`:

- **`FEAT-2026-0114/T04`, attempt 1, 2026-09-26T15:23:16Z** —
  `failure_class: "tests"`, signature
  `test_justifying_the_wrong_path_or_nothing_useful_is_still_refused`. The
  driver's `baseline_attribution` / `human_escalation` events attributed this
  to `FEAT-2026-0114/T04` as a `preexisting_gate_failure` (the check was
  failing at gate entry and this gate had already landed work), while
  explicitly warning not to assume it predated the feature. It did not: `T02`
  (landed just before) had extended the `produces_not_in_diff` repair note
  with a verbatim YAML example, which pushed the note's key names past the
  500-character `failure_excerpt`'s head/tail window, and
  `test_produces_justification`'s excerpt assertion started failing as a
  result — a regression `T02`'s own acceptance criteria (T02#3, which names
  three *other* modules) did not cover. The operator authored `T02H` as a
  targeted hygiene unit (see `PLAN.md`'s task-graph comment) to move the key
  names ahead of the example; `T02H` passed on its first attempt, and `T04`'s
  second attempt then passed cleanly with the underlying regression fixed,
  not merely retried. No unit in this gate ended `blocked_human`, and no
  attempt was lost to a repeat of the same failure — `T04`'s two attempts show
  a fixed defect, not a spin.

## What the loop did NOT verify

`PLAN.md`'s `## Post-merge checklist` carries two items neither this close nor
any gate-1 oracle can observe from a single feature's own tree:

- **Criterion:** "Over the next ten features closed in this repo and the
  generator, count units with two or more consecutive `produces_not_in_diff`
  attempts (baseline: 6 in the 2026-09-10..26 window, 5 of them running to
  three) and the share that ended `blocked_human` on that class (baseline:
  all)." **Reason not verified here:** it is a rate measured across the next
  ten *future* feature closes in *two* repositories, which do not exist yet at
  this gate's close time — no oracle this gate can run today observes a
  population that has not happened. **Where it actually gets checked:** filed
  as a post-merge observation, not an acceptance criterion, per
  `close-discipline.md` §2; the current driver (`#3424`) appends
  `PLAN.md`'s post-merge checklist under this feature's archived detail
  section in `.specfuse/roadmap-archive.md` at auto-archive time rather than
  filing a tracked issue by default, so it is read there by whoever reviews
  this feature's archived entry against the next ten closes.

- **Criterion:** "Count `produces_amended` entries on passed events and, for
  each, whether the terminal close or judge cited the dropped path in a
  finding." **Reason not verified here:** as recorded in `## Measurements`
  above, this gate produced zero `produces_amended` events on any real
  dispatched unit — the mechanism was exercised only inside its own oracle's
  synthetic harness — so there is nothing to count yet, and whether a judge
  *cites* a drop is a property of judge behaviour on a future real drop, not
  of this gate's tree. **Where it actually gets checked:** the same
  `.specfuse/roadmap-archive.md` archived-detail section as the item above,
  reviewed once real `produces_amended` events accumulate in this repo's or
  the generator's event history.

## Consumer-visible contract changes

This feature adds three consumer-visible surfaces, all documented in `T04`'s
diff and confirmed present by the `T04#1`/`T04#2` oracle re-runs above:

- **RESULT block schema:** a new key, `produces_amended:` (a list of
  `{path, reason}` dicts), read beside the existing `produces_unchanged:` —
  documented in `.specfuse/rules/result-contract.md` and its
  `specfuse/loop/data/` mirror.
- **Work-unit frontmatter:** a new driver-written field,
  `produces_dropped:`, recording each amended-away path and its reason on the
  unit itself, and read into the judge's evidence bundle under a new
  `## Deliverables dropped by amendment` section (`T03`).
- **`verification.yml` schema:** a new `defaults.produces_amendable` boolean
  (default `true`; `false` restores today's refusal), documented in
  `.specfuse/verification.yml.example` and its `specfuse/loop/data/` mirror,
  and in `docs/methodology.md`.

Appended to `CHANGELOG.md`'s `Unreleased` section, classified `added`,
tracing to `FEAT-2026-0114`, in this same close.

## Durable lessons

Staged to `LEARNINGS-pending.md` in this feature directory (this repo runs
`autonomy_default: auto`, so `close-i` forbids appending
`.specfuse/LEARNINGS.md` directly) — one entry, distilled from the `T04`/`T02H`
sequence in the Failure-class breakdown above.
