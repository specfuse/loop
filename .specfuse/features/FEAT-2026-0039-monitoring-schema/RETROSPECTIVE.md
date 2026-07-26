# FEAT-2026-0039 — Retrospective

Monitoring schema + `derive-monitoring` skill. Two gates, eight substantive work
units, one auto-closed intermediate close, one plan-next, one terminal close (this
document). Verdict: **`met_locally`** — see [Feature arc](#feature-arc--verdict).

---

## Gate 1 — auto-closed (predicate=v1)

*(Preserved verbatim as the driver generated it. The reconciliation it demands is
[below](#what-the-loop-did-not-verify).)*

On-plan intermediate close; full close-intermediate ceremony
skipped per `evaluate_auto_close`. `plan-next` WU dispatched
to draft gate 2.

- feature_id: FEAT-2026-0039
- predicate_version: v1
- gate_total_cost: $5.93
- gate_budget: <unset>
- reasons: [] (auto=True)

## What the loop did NOT verify (gate 1)

*(Preserved verbatim. **Reconciled by this close** — see the per-criterion walk in
[Gate 1 — per-WU](#gate-1--per-wu-reconstructed-at-terminal-close) and the surviving
entries in [What the loop did NOT verify](#what-the-loop-did-not-verify).)*

This gate auto-closed on-plan; the full close-intermediate ceremony did
not run, so the per-criterion deferred-verification list was **not**
enumerated. Any acceptance criterion whose verification is deferred
(loop-sandbox limit, cross-repo coordination, real-system access) is
unrecorded here. Gate 2's close MUST reconcile these
before the feature's terminal verdict — auto-close cannot enumerate them.

---

## Oracles re-run fresh (`close-discipline.md` §1)

Every oracle this feature's criteria name, re-run in this session, exit codes read
directly. Nothing below is inherited from a producing WU's self-report.

### The full `code` gate set

| Gate | Command | Exit | Observed |
|---|---|---|---|
| tests | `python3 -m unittest discover -s tests -v` | **0** | `Ran 1407 tests in 46.558s` / `OK (skipped=3)` |
| lint | `ruff check specfuse .specfuse/scripts tests scripts` | **0** | `All checks passed!` |
| security | `bandit -r specfuse .specfuse/scripts -ll` | **0** | `No issues identified.` (7937 LOC, 0 `#nosec` skips) |
| coverage | `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90` | **0** | `TOTAL 3788 224 94%` |
| leak-scan | `python3 .specfuse/scripts/leak_scan.py --all` | **0** | `leak-scan: clean` |
| monitoring-example-lint | `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` | **0** | `OK — monitoring config is structurally valid (or absent).` |
| leak-scan-hook | `bats tests/leak_scan_hook.bats` | **0** | 3/3 ok |
| sync-scaffold-bats | `bats tests/sync_scaffold.bats` | **0** | 5/5 ok |
| init-sh-shim-bats | `bats tests/init_sh_shim.bats` | **0** | 5/5 ok |
| init-skills-bats | `bats tests/init_skills_idempotent.bats` | **0** | ok |

**Environment note, because it will recur.** The three `bats` suites whose `setup()`
calls a bare `mktemp -d` fail under the default agent sandbox with
`mktemp: mkdtemp failed on /var/folders/…/T/…: Operation not permitted`, and macOS
`mktemp -d` ignores `TMPDIR`/`BATS_TMPDIR` for the bare form, so the usual redirect
does not help. They were re-run with the sandbox disabled; each suite roots its work
in its own `TESTDIR` under a `REPO_ROOT` override and does not touch the real repo.
This is a harness restriction, not a gate defect — `init_skills_idempotent.bats`
passes either way because it does not `mktemp`.

### Gate-set commands named in individual acceptance criteria

| Claim | Command | Exit | Observed |
|---|---|---|---|
| T01 AC3 — validator importable | `python3 -c "from specfuse.loop.lint_monitoring import validate_monitoring"` | **0** | — |
| T01 AC5 — absent file is not an error | `python3 .specfuse/scripts/lint_monitoring.py <absent path>` | **0** | `OK — … (or absent).` |
| T01 AC10 — `_miniyaml` is the only parser | `grep -n "^import yaml\|^from yaml" specfuse/loop/lint_monitoring.py` | 1 (no match) | correct |
| T03 AC3 — shim resolves from source | `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` | **0** | — |
| T04 AC3 — packaged rule byte-identical | `cmp .specfuse/rules/design-for-diagnosis.md specfuse/loop/data/rules/design-for-diagnosis.md` | **0** | identical |
| T04 AC6 — ≥4 property sections | `grep -c "^## " .specfuse/rules/design-for-diagnosis.md` | — | `4` |
| T06 AC7 — 0040 named in both artifacts | `grep -c FEAT-2026-0040 <overrides example> <secrets checklist>` | — | `2` and `2` |
| T06 — overrides example validates | `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.overrides.yml.example` | **0** | — |
| T07 AC2 — skill trees byte-identical | `diff -r plugins/specfuse/skills/derive-monitoring .specfuse/skills/derive-monitoring` | **0** | identical |
| plannext gate | `python3 .specfuse/scripts/lint_plan.py <feature_dir>` | **0** once this close writes `verdict:` | see note |

The `plan-lint` run at the start of this session exited **1** with
`ERROR: WU-92-gate-2-close.md: close-type WU missing or invalid 'verdict' frontmatter`.
That is the expected pre-state for a close WU: `verdict` is written *by* the close.
This session wrote `verdict: met_locally`, which is in `VERDICT_VALUES`.

### Per-module re-run of every test this feature added

`pytest` is **not installed** in this repo's `.venv`, so the `python3 -m pytest …`
spellings several acceptance criteria use (T04 AC4, T05, T06 AC8, T07 AC2/AC9, T08)
cannot be executed as written. Each was re-run through `python3 -m unittest`, which
is what the `tests` gate itself uses — the same test bodies, a different runner. All
green:

| Module | Tests | Exit |
|---|---|---|
| `tests/test_lint_monitoring.py` | 28 | 0 |
| `tests/test_monitoring_example.py` | 6 | 0 |
| `tests/test_monitoring_seed.py` | 4 | 0 |
| `tests/test_design_for_diagnosis_rule.py` | 5 | 0 |
| `tests/test_derive_monitoring_discovery.py` | 12 | 0 |
| `tests/test_monitoring_bootstrap_artifacts.py` | 7 | 0 |
| `tests/test_derive_monitoring_skill_registration.py` | 13 | 0 |
| `tests/test_monitoring_fenced_blocks.py` | 5 | 0 |
| `tests/test_skills_vendored_in_sync.py` | 4 | 0 |
| `tests/test_scaffold_data_in_sync.py` | 3 | 0 |
| `tests/test_scaffold_resources.py` | 5 | 0 |
| `tests/test_init_integration.py` | 28 | 0 (1 skipped) |

All 27 acceptance-criteria-named test functions were confirmed present by name in
their declared modules. No producing WU's self-report was taken on trust, and the
fresh re-run **agrees with every one of them** — no escalation trigger fired.

---

## Gate 1 — per-WU (reconstructed at terminal close)

Gate 1 auto-closed, so this walk is the reconciliation criterion 3 demands: each of
T01–T03's acceptance criteria classified as *verified in-loop* or *deferred*.

### On the "fails on HEAD before this WU's edits" criteria

Every WU in this feature carries a red-test-first criterion, and a close session
cannot run `git` (`result-contract.md` rule 1), so none can be re-checked by
checkout. They are nonetheless **verified by construction, not deferred**: in all
eight cases the named red test asserts on an artifact in that WU's own `produces:`
list — an import of a module the WU created (T01, T05, T08) or a file/registration
the WU created (T02, T03, T04, T06, T07). With the artifact absent the test cannot
pass. This is a structural argument, and it is the strongest one available in-loop;
it is recorded here rather than left implicit.

### T01 — `lint_monitoring.py` (11 criteria)

**All 11 verified in-loop.** AC1/AC2/AC4–AC9 are the 28 tests in
`tests/test_lint_monitoring.py`, re-run green above, including the negative
observations that matter: an out-of-enum check type, an out-of-enum value for each of
the three dials, a missing required component field, an inline connection-string
credential, and the absent-file case. AC3 and AC10 were re-run as commands. AC11
(`PLW1510`) is enforced by the `lint` gate, exit 0. **Nothing deferred.**

### T02 — example + schema doc (8 criteria)

**All 8 verified in-loop.** AC1–AC5 and AC7 are the 6 tests in
`tests/test_monitoring_example.py`, green. AC5's second assertion
(`leak_scan.py --all`) re-run: `leak-scan: clean`, exit 0. AC6 and AC8 are doc
content, confirmed by re-reading `docs/concepts/monitoring-schema.md` — it names
FEAT-2026-0040 as the consumer (line 19), states provider names are opaque (line 22),
and says an absent `monitoring.yml` is valid. **Nothing deferred.**

### T03 — shim, seeding, gate wiring (8 criteria)

**7 of 8 verified in-loop; 1 deferred.** AC1–AC3 and AC5–AC7 are covered by
`tests/test_monitoring_seed.py`, `tests/test_scaffold_data_in_sync.py`,
`tests/test_scaffold_resources.py` and `tests/test_init_integration.py`, all green.
AC4 (the `monitoring-example-lint` gate exists and its command exits 0) was re-run
directly. The commented-out gate in `.specfuse/verification.yml.example` names
`specfuse-monitor-lint`; that console script **does exist** —
`pyproject.toml:66` registers `specfuse-monitor-lint = "specfuse.loop.lint_monitoring:main"`.
This was checked specifically because a commented gate pointing at a nonexistent
binary is the `[FEAT-2026-0029/G1-CLOSE]` failure the PLAN was built to avoid; it is
not present here.

**Deferred: AC8** — *"Nothing in this WU changes the pass/fail behavior of an
existing gate… the full `code` set passes both before and after."* The "before" half
is a differential claim about a tree that no longer exists, and a close session
cannot check out the pre-WU sha. Carried to
[What the loop did NOT verify](#what-the-loop-did-not-verify). T06 AC9 is the same
criterion and the same deferral.

---

## Gate 2 — per-WU

### T04 — the design-for-diagnosis rule (9 criteria, **2 attempts**)

Ships `.specfuse/rules/design-for-diagnosis.md` (4 property sections: correlation-ID
propagation, structured logging, per-component role names, DLQ error-context
capture), its byte-identical packaged copy, and `tests/test_design_for_diagnosis_rule.py`.
All 9 criteria verified in-loop: 5 tests green, `cmp` identical, `grep -c "^## "` = 4,
and `'design-for-diagnosis' in _RULES_BLOCK` → `False` (the reference-only posture,
asserted rather than assumed). The rule is also absent from `.claude/CLAUDE.md`'s
import list, confirmed by grep.

**Why attempt 1 failed, precisely.** The attempt's `files_touched` is exactly the
three paths in `produces:` — the rule, its packaged copy, and the test — and **none**
of the five list surfaces the WU body enumerates in a numbered block. The suite went
red on `tests` and `coverage`; the agent reported `agent_status: complete` anyway and
the driver's gate re-run caught it. Attempt 2 added `scripts/sync-scaffold.sh`,
`tests/sync_scaffold.bats`, `tests/test_init_integration.py`,
`tests/test_scaffold_data_in_sync.py`, `tests/test_scaffold_resources.py` — **and
`tests/test_scaffold_init.py`, which the WU's enumeration did not list.** The
enumeration was both ignored and, independently, incomplete. See
[What I'd change](#what-id-change).

### T05 — component-discovery reference implementation (11 criteria)

`tests/test_derive_monitoring_discovery.py`, 12 tests, all green. The chain that
matters is AC1: discovery output rendered as YAML validates clean against gate 1's
`validate_monitoring` — gate 2's definition of done reduced to one assertion, and it
holds. Both boundary tests are present and green (`test_neutral_records_survive_a_second_stack`,
`test_core_names_no_stack_tokens`), as are both halves of the negative observation
(`test_audit_fires_on_an_undiagnosable_tree` / `test_audit_is_quiet_on_a_diagnosable_tree`)
and the severity-set assertion (`test_audit_findings_are_all_warn`). The
WARN-never-ERROR decision is held by a test on the *emittable severity set*, not on
one fixture's output — the stronger form.

What these tests do **not** establish is field accuracy; see
[What the loop did NOT verify](#what-the-loop-did-not-verify) entry 2.

### T06 — local-runner bootstrap artifacts (10 criteria)

`.specfuse/monitoring.overrides.yml.example` and
`.specfuse/monitoring-secrets-checklist.md`, both seeded without a `_SEED_RENAME`
entry, both packaged byte-identically, with `.specfuse/monitoring.overrides.yml`
appended to both copies of `gitignore.snippet`. 7 tests green, including
`test_chosen_filename_has_no_dot_local_segment` (the guard that keeps a future rename
from reintroducing the `spinning_detected` trap `PLAN.md` paid for once already) and
`test_secrets_checklist_names_no_values` with its required negative case. The
overrides example validates against gate 1's schema unchanged — this feature ships
exactly one monitoring schema, not two. AC9 is deferred with T03 AC8.

### T07 — the `derive-monitoring` skill (12 criteria)

`SKILL.md` (14876 bytes) + `PROMPT.md` (6993 bytes), byte-identical across
`plugins/specfuse/skills/` and `.specfuse/skills/` (`diff -r` exit 0), registered in
both copies of `docs/skills.md`. 13 tests green: frontmatter carries
`name: derive-monitoring` and a description naming the drafted artifact; the
draft-never-write posture, the WARN-not-ERROR severity, the citations of T04's rule
and T05's reference implementation, and the operator-prerequisite framing of the
symlink are each asserted rather than assumed; AC8's credential check carries its
negative case.

T07 came in at $3.25 against a $2.50 plan — the overrun `GATE-02-REVIEW.md` §1.11
predicted, for the reason it predicted.

### T08 — fenced-block drift test (8 criteria)

`tests/test_monitoring_fenced_blocks.py`, 5 tests green. It extracts 4 fenced `yaml`
blocks across 5 declared surfaces and validates each; `_EXPECTED_FRAGMENT_COUNT = 0`,
so **every** monitoring example in the skill and the bootstrap prose is a complete,
schema-valid config — the fragment escape hatch exists and is currently unused. Both
vacuous-pass guards are present (`test_extractor_catches_a_broken_block`,
`test_extractor_finds_the_expected_block_count`).

**AC6's coverage-scope statement was independently checked, not accepted.** The
module excludes `docs/concepts/monitoring-schema.md` on the stated grounds that its
`## Example` section has no inline fenced block and points at
`.specfuse/monitoring.yml.example` instead. Verified: grepping that file for a fence
returns **nothing**, and the section reads exactly as claimed. `GATE-02-REVIEW.md`
§3(e) is therefore genuinely closed rather than deferred.

### Failure-class breakdown

| failure_class | non-passed attempts | dominant signature |
|---------------|---------------------|--------------------|
| tests | 1 | `$ python3 -m unittest discover -s tests -v` |
| **total** | **1** | — |

One non-passing attempt across the whole feature: T04 attempt 1, analysed above.
(The driver's own `assert_failure_class_breakdown_when_failures_present` computes an
empty scope here, because `_gate_number_from_wu_id` resolves gate numbers only for
`G<N>-` prefixed ids and returns `None` for `T04`. The table is included anyway —
the attempt happened, and a guard that cannot see it is not a reason to omit it.)

---

## Feature arc — verdict

**`met_locally`.** `met` is not available and was not close.

`PLAN.md`'s `roadmap_goal` asks for four things: a declarative `monitoring.yml`
schema with a committed structural validator, a seeded design-for-diagnosis rule, the
`derive-monitoring` skill that drafts a project's monitoring config from repo
evidence, and — the stated *purpose* — that FEAT-2026-0040 be built against a
contract that is machine-checkable rather than prose.

- **Schema + committed validator — delivered and verified.** `validate_monitoring`
  exists, is importable, is exercised by 28 tests including negative cases for every
  enum and the inline-credential rule, and guards the shipped example through a
  blocking `code` gate that runs on every WU from T03 onward. The machine-checkable
  contract 0040 was promised is real.
- **Seeded design-for-diagnosis rule — delivered and verified.** Present, seeded,
  byte-faithful, four property sections, and provably *not* `@`-imported.
- **The skill — delivered as a document; unproven as a skill.** This is the gap. It
  exists, is registered, is internally consistent, cites its dependencies, and every
  example in it validates against the schema. Nobody has run it. Its value is the
  interview, and the interview has no in-loop oracle at all
  (`GATE-02-REVIEW.md` §3(c)).
- **`GATE-02.md`'s definition of done** — *"an operator can run `/derive-monitoring`
  and get a drafted `monitoring.yml` that passes gate 1's validator"* — is two
  clauses. The second is proven on a stylized fixture (T05 AC1). The first is not
  proven at all, and is not even currently *possible*: the
  `.claude/skills/derive-monitoring` discovery symlink does not exist, because
  creating it is operator work the sandbox denies to a dispatched session.

**On the two deliberate scope narrowings.** Both were recorded before the work, not
excused after it, and both survive scrutiny:

1. **GitHub Actions runner workflow → FEAT-2026-0040.** Correct and vindicated. That
   workflow's body invokes `specfuse-monitor run`, which does not exist until 0040;
   shipping it here would have been the `[FEAT-2026-0029/G1-CLOSE]` failure verbatim.
   The narrowing cost the roadmap's deliverable (c) one bullet and cost the feature
   nothing — the "first `--dry-run` is minutes away" property survives for local runs
   via T06's artifacts. Note the distinction T06 had to hold and did: a data file
   whose consumer arrives later is valid standing alone; a script that *invokes* a
   nonexistent binary is not.
2. **Live run → post-merge operator work.** Not a narrowing of ambition so much as an
   admission of what a dispatched session is. It is the reason the verdict is hedged.

The feature delivers its stated *purpose* — 0040 inherits a machine-checkable
contract, and FEAT-2026-0040/0041/0042/0043 can unblock on it. It does not deliver
the operator-facing promise in `GATE-02.md`'s first clause. `met_locally` is the
honest ceiling, and the follow-up record below is what makes it a state rather than a
dead end.

---

## Cost analysis

`planned_cost_usd: 34.00` at the feature level. Actual spend read from
`events.jsonl` (`attempt_outcome.cost_usd`, summed across attempts), excluding this
close WU, which is in flight as this is written.

### Gate 1 — planned $18.00, actual **$12.23**, delta **−$5.77 (−32.0%)**

| WU | Planned | Actual | Delta | Note |
|---|---|---|---|---|
| T01 validator | $3.00 | $2.07 | −$0.93 (−30.9%) | 1 attempt |
| T02 example + doc | $2.50 | $0.63 | −$1.87 (−74.6%) | 1 attempt; the cheapest WU in the feature |
| T03 shim + seed + gate | $2.50 | $3.23 | +$0.73 (+29.0%) | 14 files touched — the widest gate-1 diff |
| G1-CLOSE-INTERMEDIATE | $5.00 | **$0.00** | −$5.00 (−100%) | auto-closed, `attempts: 0`, never dispatched |
| G1-PLAN | $5.00 | $6.30 | +$1.30 (+26.0%) | drafted 5 WUs + a 26KB gate review |

**The gate-1 underrun is not a saving; it is a deferral, and this close is where the
bill arrived.** $5.00 of the $5.77 underrun is one line: the close-intermediate that
never ran. Its absence is precisely why criterion 3 exists — the per-criterion
deferred-verification walk it would have done became an acceptance criterion on the
terminal close, and a meaningful share of this session's tokens went to reconstructing
T01–T03's verification state after the fact. Auto-close moved the work later and made
it more expensive (a fresh session re-reading three WUs it did not write); it did not
remove it. Reported as −32% because that is what the arithmetic says, but a reader
should not take gate 1 as evidence of efficient estimation.

### Gate 2 — planned $16.00 ($11.00 substantive + $5.00 close), substantive actual **$11.29**, delta **+$0.29 (+2.6%)**

| WU | Planned | Actual | Delta | Note |
|---|---|---|---|---|
| T04 rule | $2.00 | $3.03 | **+$1.03 (+51.7%)** | 2 attempts; $1.37 of it the failed one |
| T05 discovery | $3.00 | $2.29 | −$0.71 (−23.8%) | 1 attempt |
| T06 bootstrap | $2.00 | $1.84 | −$0.16 (−8.2%) | 1 attempt |
| T07 skill | $2.50 | $3.25 | **+$0.75 (+30.2%)** | 1 attempt |
| T08 drift test | $1.50 | $0.88 | −$0.62 (−41.5%) | 1 attempt |
| G2-CLOSE | $5.00 | *(in flight)* | — | `planning-discipline.md` §5 floor |

Gate 2's substantive estimate landed within 3% in aggregate — but the aggregate hides
that the per-WU errors were large in both directions and that the pre-registered
prediction was half wrong. `GATE-02-REVIEW.md` §1.11 named **T05 and T07** as the
likeliest overruns. T07 overran by 30%, for the stated reason (SKILL.md authoring
volume). **T05 came in 24% *under*** — the eight-tests-plus-two-fixtures work it was
padded for went cleanly first try. And the real overrun, **T04 at +52%**, was flagged
by nobody, because its risk was not authoring volume at all: it was a mechanical
six-surface enumeration, and it cost a whole retry.

Against `GATE-02.md`'s `cost_budget_usd: 20.0`, gate 2 lands at ~$16.29 including
this close at plan — inside budget.

### Feature total

**Planned $34.00. Actual $23.52 excluding this close** (gate 1 $12.23 + gate 2
$11.29). With G2-CLOSE at its $5.00 plan the feature lands near **$28.52, −$5.48
(−16.1%)**. Essentially the entire remaining underrun is the un-run close-intermediate;
the eight substantive WUs together were planned at $19.00 and cost $17.22 (−9.4%),
which is the number to carry forward as this repo's estimation accuracy for
implementation WUs.

**Calibration lesson for the next plan.** Overrun risk in this feature tracked
*retry probability*, not prose volume — and retry probability tracked **mechanical
fan-out**: the WUs that had to edit a hand-maintained list in N places (T03 at +29%,
T04 at +52%) overran; the WUs that had to write a lot of prose or a lot of tests
(T05, T08) came in under. Estimate the enumeration, not the essay.

---

## Consumer-visible contract changes

`close-discipline.md` §3. FEAT-2026-0040, 0041, 0042 and 0043 are all `blocked` on
this feature; this section is their handoff document. **This list requires explicit
human acknowledgment before the terminal flips.**

### 1. New Python API — `specfuse.loop.lint_monitoring`

`__all__ = ("validate_monitoring", "main")`.

```
validate_monitoring(path: str | Path | None = None) -> list[str]
```

Returns a list of human-readable finding strings; **`[]` means valid**. Default path
`.specfuse/monitoring.yml`. **An absent file returns `[]`** — monitoring is opt-in and
a project that has not configured it is in a correct final state. Takes a **path, not
a string of YAML**. Parses via `specfuse/loop/_miniyaml.py`; the package keeps zero
runtime dependencies and this module does not import `yaml`.

Module-level constants 0040 can consume rather than re-declare:

| Name | Value |
|---|---|
| `RUNNER_VALUES` | `{"local", "gh-actions", "in-cluster"}` |
| `DIAGNOSE_VALUES` | `{"manual", "auto"}` |
| `AUTOFIX_VALUES` | `{"off", "on"}` (must be **quoted** in YAML — `_miniyaml` rejects bare `off`/`on`) |
| `CHECK_TYPES` | `{"dlq", "error-logs", "http-5xx", "heartbeat", "invariant"}` |
| `HARVEST_MODE_VALUES` | `{"peek", "quarantine"}` |
| `REQUIRED_COMPONENT_FIELDS` | `("name", "type", "runner", "diagnose", "autofix", "checks")` |
| `REQUIRED_PROVIDER_BINDINGS` | `("telemetry", "broker")` |

`_CREDENTIAL_KEY_RE` and `_ENV_VAR_NAME_RE` are private but load-bearing on the
security posture: **credentials by environment-variable name only**; an inline
connection-string-shaped literal is a finding, not a style note.

### 2. New console script — `specfuse-monitor-lint`

`pyproject.toml:66` → `specfuse.loop.lint_monitoring:main`. Exits 0 on valid or
absent, non-zero on findings. **New entry point in the published wheel.**

### 3. New scaffold shim — `.specfuse/scripts/lint_monitoring.py`

Follows the `lint_plan.py` shim pattern: path-inserts the repo root, re-exports the
package module's public namespace, delegates `main()`. Holds no validation logic.
Resolves from source without a pip install.

### 4. New blocking `code` gate — `monitoring-example-lint`

Added to **this repo's** `.specfuse/verification.yml`, pointed at
`.specfuse/monitoring.yml.example`. Deliberately not pointed at a live config: this
repo is a CLI tool with no deployable components, so a live-config gate would fail
permanently or pass vacuously. **Additive** — the full `code` set is green.

### 5. New commented-out gate in `.specfuse/verification.yml.example`

```
  # Uncomment after running /derive-monitoring to draft .specfuse/monitoring.yml.
  # - name: monitoring-example-lint
  #   command: "specfuse-monitor-lint .specfuse/monitoring.yml"
```

Commented **on purpose** — an uncommented gate would fail every freshly-scaffolded
project on day one. Its binary is real (item 2).

### 6. New seed files — four, none renamed

| Seeded path | Packaged copy |
|---|---|
| `.specfuse/monitoring.yml.example` | `specfuse/loop/data/monitoring.yml.example` |
| `.specfuse/monitoring.overrides.yml.example` | `specfuse/loop/data/monitoring.overrides.yml.example` |
| `.specfuse/monitoring-secrets-checklist.md` | `specfuse/loop/data/monitoring-secrets-checklist.md` |
| `.specfuse/rules/design-for-diagnosis.md` | `specfuse/loop/data/rules/design-for-diagnosis.md` |

**No `_SEED_RENAME` entry for any of them.** Monitoring is opt-in; a rename would
auto-create live monitoring config in every scaffolded project, including ones that
deploy nothing. `test_example_is_not_renamed_on_init` and
`test_both_artifacts_are_seeded_without_rename` are the guards on that decision.

### 7. `.specfuse/gitignore.snippet` (and its packaged copy) — one appended line

`.specfuse/monitoring.overrides.yml` — the **live** overrides file, not the
`.example`. Both copies byte-identical.

### 8. New rule — `.specfuse/rules/design-for-diagnosis.md`, **reference-only**

Seeded into scaffolded projects and deliberately **not** added to `_RULES_BLOCK` /
`CLAUDE.md`'s `@`-import list — the same posture as `planning-discipline.md` and
`close-discipline.md`. It governs application-runtime code, not work-unit execution;
importing it would tax every session in every downstream project. Asserted by
`test_rule_is_not_at_imported`, so a later "helpful" import turns a test red.

### 9. New skill — `/derive-monitoring`

`plugins/specfuse/skills/derive-monitoring/{SKILL.md,PROMPT.md}`, vendored
byte-identically to `.specfuse/skills/derive-monitoring/`, registered in both copies
of `docs/skills.md`. **Requires an operator-created discovery symlink before it is
invocable** — see the follow-up record.

### 10. New doc — `docs/concepts/monitoring-schema.md`

The schema reference the skill cites. Names FEAT-2026-0040 as the consumer and states
that provider names are opaque strings this layer does not interpret.

### Removals and renames

**None.** Nothing was removed, renamed, or had its signature changed. Every item
above is additive.

---

## What the loop did NOT verify

Six entries. This exceeds the two-entry threshold, so feature gate sizing is flagged
under [What I'd change](#what-id-change).

### 1. The live run of `derive-monitoring` against a real multi-component backend

**Never happens in-loop, structurally.** The skill is interactive and its target is a
*different repository*. A dispatched session has neither half of what it needs: no
human channel (the skill's own documented behaviour is that piping `PROMPT.md` via
`claude -p` consumes stdin and silently degrades to `[gap]` mode) and no access or
commit rights in a target repo. No amount of test-writing closes this.

**In-loop substitute:** a stylized `{relpath: content}` repo-tree fixture built in a
`tempfile` directory (T05), two `acme-*` components, one HTTP-serving and one
message-consuming.

**Exact re-run condition that upgrades this to verified:** an operator runs
`/derive-monitoring` against a real project and the drafted `.specfuse/monitoring.yml`
passes `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml` with an
empty finding list.

**And that condition is necessary but *not sufficient*** (`GATE-02-REVIEW.md` §3(c)).
A clean-validating draft proves the output is schema-valid; it says nothing about
whether the interview asked the right questions, declined the ones the repo already
answered, or produced components the operator recognises. The only oracle for
interview quality is a human judging the draft's content.

### 2. That discovery's evidence patterns match how a real backend is laid out

T05's fixture tree was written by the same session that wrote the pattern table that
matches it. **A closed loop always closes.** What the tests prove is real —
determinism, schema-validity of the output, the audit firing and staying quiet
appropriately, neutral-record shape surviving a second stack — but every quantity
that matters in the field is unmeasured: whether a real repo yields the right *number*
of components (a monorepo or a service mesh may yield dozens, or one), whether the
suggested checks are the ones an operator would have chosen, whether audit findings
are actionable or noise. These are a **regression guard on an algorithm's shape**, not
evidence that the algorithm works.

**Re-run condition:** the first real backend discovery run (bundled with entry 1) —
the operator confirms the discovered component set matches the components they know
they deploy, with no false positives and no omissions.

### 3. That the provider-agnostic boundary holds against a genuinely third stack

Two mechanisms hold it — behavioural (`test_neutral_records_survive_a_second_stack`)
and structural (`test_core_names_no_stack_tokens`) — and both have a stated weakness.
The behavioural test compares two fixtures the same session authored: a mistaken model
of both stacks in the same direction produces two fixtures encoding the same mistake
and a test that agrees with itself. The structural test is only as good as a
hand-written token denylist, and "provider-agnostic" is a negative property no finite
denylist proves. They make leakage hard and visible; not impossible.

**Re-run condition:** FEAT-2026-0040 writes its first real provider adapter against
this core without needing to special-case the core.

### 4. That neither T03 nor T06 changed an existing gate's pass/fail behaviour

T03 AC8 and T06 AC9 assert the full `code` set passes *before and after*. The "after"
half is verified — the set is green. The "before" half is a differential claim about a
tree that no longer exists, and a close session cannot run `git`
(`result-contract.md` rule 1). Low residual risk (both gates are green now and
`monitoring-example-lint` is scoped to a file this feature introduced), but it is an
unverified claim and it is not going to be recorded as a verified one.

**Re-run condition:** check out each WU's parent sha and run the full `code` set; or,
better, have the driver capture the pre-dispatch gate-set result so the differential is
data rather than an assertion.

### 5. That `/derive-monitoring` is actually invocable

The `.claude/skills/derive-monitoring` discovery symlink **does not exist** —
confirmed absent. Creating it is an operator prerequisite, not agent work: Claude
Code's sandbox lists `.claude/skills` under `denyWithinAllow`, a deny rule nested in
an allow scope that survives `unsandboxed: true` (`[FEAT-2026-0016/G3-CLOSE]`). Until
an operator runs it, the skill ships but does not resolve as a slash command.

**Re-run condition:**

```
ln -s ../../.specfuse/skills/derive-monitoring .claude/skills/derive-monitoring
```

then confirm `/derive-monitoring` resolves.

### 6. That the skill's prose and T05's algorithm stay in agreement

`SKILL.md` cites the reference implementation's path so a reader can check, but
nothing *detects* the case where T05's algorithm changes and the skill's prose
description of it does not. The skill is read by a model, and a model follows the
prose. Residual and accepted (`GATE-02-REVIEW.md` §3(d)), named here so 0040 does not
discover it as a surprise.

**Re-run condition:** a test asserting the skill's method section and the reference
implementation's function signatures agree — or, more honestly, promoting the
reference implementation out of the test module into a real module the skill can point
at unambiguously.

### Also unverified, and cheap to say

`python3 -m pytest` is the spelling several acceptance criteria use, and **pytest is
not installed in this repo's `.venv`**. Those criteria were satisfied via
`python3 -m unittest` on the same test bodies. Nobody has ever run them the way they
are written. Either install pytest or stop writing `pytest` into criteria for a repo
whose gate is `unittest`.

---

## Hedged-verdict follow-up record (`close-discipline.md` §2)

`met_locally` without this record is a polite synonym for "unknown". One entry per
unmet criterion.

### FU-1 — `GATE-02.md` definition of done, clause 1

> *"An operator can run `/derive-monitoring` against a multi-component project and
> get a drafted `monitoring.yml` that passes gate 1's validator, plus the local-runner
> bootstrap artifacts."*

**Unmet:** clause 1 ("an operator can run `/derive-monitoring`") is unproven; clause 2
("that passes gate 1's validator") is proven on a stylized fixture only.

**Why unverifiable here:** a dispatched WU has no human channel and no target
repository; and the discovery symlink the slash command needs is denied to a
dispatched session by the sandbox.

**Upgrade condition (all three, in order):**

1. `ln -s ../../.specfuse/skills/derive-monitoring .claude/skills/derive-monitoring`
2. An operator runs `/derive-monitoring` against a real multi-component project.
3. The drafted `.specfuse/monitoring.yml` passes
   `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml` clean **and**
   the operator confirms the discovered component set and suggested checks match what
   they actually deploy.

Steps 1–2 alone upgrade nothing. Step 3's second half is a human judgement and there
is no substitute for it.

### FU-2 — T03 AC8 / T06 AC9, the before-and-after gate claim

> *"Nothing in this WU changes the pass/fail behavior of an existing gate. The full
> `code` set passes both before and after."*

**Unmet:** the "before" measurement was never independently captured.

**Why unverifiable here:** close sessions cannot run `git`, so the pre-WU tree is
unreachable.

**Upgrade condition:** check out each WU's parent sha, run the full `code` set,
confirm green. Durable fix (worth more than the re-run): have the driver record the
gate-set result at dispatch time so the differential is data both the WU and the close
can read.

### FU-3 — the provider-agnostic boundary

**Unmet:** held by two mechanisms with stated, real weaknesses (entry 3 above).

**Upgrade condition:** FEAT-2026-0040 ships its first telemetry and broker adapter
against this core with no special-casing of `discover_components` or
`validate_monitoring`. If 0040 has to patch either, the boundary did not hold and this
feature's central claim needs revisiting.

### FU-4 — discovery's field accuracy

**Unmet:** the fixture is a closed loop (entry 2 above).

**Upgrade condition:** bundled with FU-1 step 3 — the first real backend run is the
first measurement. Record the result in 0040's plan as a calibration input, whichever
way it goes.

---

## What I'd change

### Gate sizing is flagged — six deferred entries against a two-entry threshold

Per the `draft-feature` threshold (`SKILL.md:283` — more than two deferred entries
**or** more than 30% of the gate's criteria), the entry-count arm fires: six entries.
The percentage arm does **not** — six against 58 acceptance criteria across gate 2 and
this close is ~10%.

**But the honest reading is that the threshold is measuring the wrong thing here.**
Five of the six deferrals share one root cause, and it is not gate sizing: this
feature's central deliverable is an **interactive skill whose target is a different
repository**, and that is unverifiable in-loop *at any gate size*. Splitting gate 2
into three gates would produce three gates each carrying the same deferral. The
threshold is calibrated for "the gate tried to do too much"; what happened here is
"the gate delivered something the loop structurally cannot test."

The real lesson is at **draft time**, not gate-sizing time: a feature whose definition
of done is an operator experience should say so in `PLAN.md` and pre-declare
`met_locally` as its ceiling at drafting, rather than discovering it at the arming
review (§3(c)) and confirming it at the close. `GATE-02.md`'s definition of done was
written as if the loop could verify it; it never could. Two of this close's eight
acceptance criteria exist to manage the consequences of that phrasing.

### Auto-close should not skip the deferred-verification enumeration

Gate 1 auto-closed on-plan and saved $5.00 by not dispatching its close-intermediate.
What it actually did was move that gate's per-criterion deferred walk into the terminal
close as criterion 3 — and make it more expensive, because the session doing it did not
write T01–T03 and had to reconstruct their verification state from the WU files. The
auto-generated gate-1 retrospective is admirably honest that this happened; the fix is
that `evaluate_auto_close` should either enumerate the deferred list itself (it has the
WU files) or refuse to auto-close a gate whose WUs carry criteria it cannot classify.
"Auto-closed, deferred list unenumerated" is a *debt entry*, and it should be priced
like one rather than reported as a saving.

### The multi-surface seeding enumeration should be derived, not hand-written

T04's failed attempt is the cleanest failure in the feature. The WU body spelled out
the five list surfaces in a numbered block, with a per-surface explanation of what
breaks if you miss it. The agent edited its three `produces:` files and none of the
five. That is a prose-enumeration miss and it cost a full attempt and $1.37.

Worse, **the enumeration was itself incomplete**: attempt 2 also had to touch
`tests/test_scaffold_init.py`, which the WU did not list — and T03 and T06 touched it
too, so the omission was inherited across three WUs, each hand-copying the previous
author's list. A hand-written fan-out enumeration reproduces the previous author's
blind spots with perfect fidelity.

Two durable fixes, both cheap: (a) at authoring time derive the list mechanically
(grep the repo for an existing seed filename and list every file that names it) rather
than copying it from a sibling WU; (b) better, make the seed registry the single source
and have the tests read from it, so adding a seed file is one edit instead of seven.
The current design puts a seven-way consistency requirement on human enumeration and
then guards it with tests — the tests do catch it, but they catch it one attempt later.

### `planned_cost_usd` should be estimated against enumeration count, not prose volume

The pre-registered prediction in `GATE-02-REVIEW.md` §1.11 named T05 and T07 as the
overrun risks, reasoning from authoring volume. T07 overran; T05 came in 24% under;
the actual worst overrun was T04, which nobody flagged. The pattern across both gates
is unambiguous: the WUs that overran (T03 +29%, T04 +52%) were the ones editing a
hand-maintained list in many places; the WUs that came in under (T02 −75%, T08 −42%,
T05 −24%) were the ones writing a lot of content in few files. Retry probability, not
token volume, drives cost — and retry probability tracks mechanical fan-out.

### Smaller things

- **Stop writing `python3 -m pytest` into acceptance criteria** for a repo whose
  `tests` gate is `python3 -m unittest discover`. Six criteria across four WUs name a
  runner that is not installed. Nobody noticed because the unittest bodies pass either
  way — which is exactly the problem: an acceptance criterion nobody can execute as
  written is not an oracle.
- **The bare `mktemp -d` in three bats `setup()` functions** is un-runnable under the
  default agent sandbox and ignores `TMPDIR`. Templating it against `BATS_TMPDIR` /
  `TMPDIR` would make those three gates runnable without disabling the sandbox. Small
  change, removes a recurring reason to reach for `dangerouslyDisableSandbox`.
- **`_gate_number_from_wu_id` returns `None` for `T04`-style ids**, so
  `assert_failure_class_breakdown_when_failures_present` computed an empty scope for a
  gate that genuinely had a failed attempt. The guard is currently blind to exactly the
  failures it exists to surface, for every WU not named `G<N>-…`. Worth a driver issue.
- **`GATE-02.md`'s definition-of-done bullet still says the WU list "is filled in
  then"** and was never filled in (`GATE-02-REVIEW.md` §1.12 flagged this as a one-line
  arm-time edit; it was not made). `PLAN.md`'s graph is authoritative, so nothing is
  broken — but a reader of `GATE-02.md` alone cannot tell what gate 2 contained.

---

## FU-1 discharge — the live run happened (2026-07-26, post-close)

`FU-1`'s upgrade condition had three steps. All three are now satisfied.

1. **Discovery symlink created** — `.claude/skills/derive-monitoring`, by the operator
   from an interactive session, as the WU predicted a dispatched session could not.
2. **`/derive-monitoring` run against a real multi-component project** — a downstream
   .NET backend: one HTTP API deployed by Helm chart, plus one functions host carrying
   20 message-topic subscriptions and 10 scheduled triggers.
3. **The drafted config passes the validator, and the operator confirmed the component
   set** — `lint_monitoring.py` exited 0 on both the drafted `monitoring.yml` and the
   drafted overrides file (run, not asserted), and the operator confirmed the two
   discovered components match what they actually deploy.

**FU-1 is discharged.** Gate 2's definition-of-done clause 1 — "an operator can run
`/derive-monitoring` … and get a drafted `monitoring.yml` that passes gate 1's
validator" — is now proven on a real repository rather than on a fixture.

### What the run found — five gaps, four issues, none of them unmet criteria of this feature

The run's value was not confirmation; it was the gaps it surfaced *before*
FEAT-2026-0040 builds adapters against the contract:

- **The component axis is wrong for enumeration** (#245). Correctly collapsing 30
  triggers to 2 deployables leaves no way to express per-subscription DLQ attribution
  or per-schedule heartbeat. Checks need a `targets` list; components stay the
  deployment/attribution unit.
- **Discovery would have emitted 30 components** (#245). A matcher keyed on trigger
  attributes returns one component per trigger. The right key is *deployment* evidence,
  with trigger registrations as evidence of a component's **type**. The gate-2 fixture
  could not catch this: its stack had one trigger per deployable.
- **`_ENV_VAR_NAME_RE` rejects `Section__Key`** (#246), the canonical env-var spelling
  for hierarchical config in .NET and Spring alike.
- **A wedged consumer is invisible to every existing check type** (#247) — including
  `invariant`, because queue depth is a broker coordinate a telemetry query cannot see.
- **Deployment-regression detection on 4xx codes** (#248) — expressible today via
  `invariant`, which would erode the discrete-artifact model by precedent rather than
  by decision. Filed as a scope question, not a schema change.

### Bearing on FU-4 (discovery's field accuracy)

Partially measured, and the honest reading is uncomfortable: the **skill** produced the
right answer, but it did so because the operator-facing session applied judgement about
what constitutes a deployable. `discover_components` driven by a naive per-stack pattern
table would have returned 30. FU-4 is therefore **not** discharged by this run — it is
now measured, and the measurement says the algorithm needs deployment-evidence keying it
does not currently have. Tracked in #245.

FU-2 and FU-3 remain open and unmeasured.
