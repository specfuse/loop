---
id: FEAT-2026-0069/T06
type: implementation
status: draft
attempts: 0
planned_cost_usd: 4.00
oracle_env: macos_local
produces:
  - tests/test_derive_monitoring_discovery.py
---

# Re-key `discover_components` onto deployment evidence

**Objective.** Make a component a *deployable* rather than a *trigger*: `discover_components`
keys on deployment evidence, and trigger registrations become evidence of a component's
type and the source of its target lists.

**Context.** This is `FEAT-2026-0069/T06`, the axis-defining work unit of gate 2. Gate 1
made the **schema** able to express one component with N targets; discovery still returns
one component per trigger, so on the motivating host (one functions host, 20 queue
subscriptions, 10 timers) it returns 30 components where the correct answer is 2 —
`RETROSPECTIVE.md` § *What the loop did NOT verify* entry 1.

The reference implementation is `tests/test_derive_monitoring_discovery.py` — the
algorithm lives in the test module on purpose (there is no `specfuse/loop/` production
module for it; the skill is prose and points at this module). `discover_components`
(`:58`) today iterates `patterns["components"]`, each candidate carrying
`evidence_markers` plus **hand-declared** `http_serving` / `message_consuming` booleans.
That is the trigger-keyed contract this WU replaces. `PLAN.md`'s gate 2 sketch names it:
*"This is a change to the `patterns` table contract, not just to a pattern table — treat
it as such."*

**The contract this WU establishes.**

Per candidate in `patterns["components"]`:

| field | before | after |
|---|---|---|
| `evidence_markers` | markers that make the candidate exist | **removed** |
| `deployment_markers` | — | markers on *deployment* artifacts (chart, compose service, container definition) that make the candidate exist |
| `scope_prefix` | — | the relpath prefix that bounds which files count as this deployable's own |
| `http_serving` | hand-declared boolean | **derived** — true iff an `http`-kind trigger matched inside the scope |
| `message_consuming` | hand-declared boolean | **derived** — true iff at least one `subscription`-kind trigger matched inside the scope |

New sibling table `patterns["triggers"]`, a flat list. Each entry carries a `marker`, a
`kind` in `{http, subscription, schedule}`, and the coordinates that kind contributes:
`subscription` entries carry `subscription` + `function`; `schedule` entries carry `name`
+ `cron` + `timezone`; `http` entries carry no coordinates (they only set the dial).

Emitted record gains two neutral lists — `subscriptions` (`{subscription, function}` per
entry) and `schedules` (`{name, cron, timezone}` per entry) — in trigger-table order.
`evidence` keeps its existing meaning and stays sorted and de-duplicated; a component's
evidence is now its deployment file **plus** every scoped file a trigger matched in.

**Neutrality is a blocking constraint, not a preference** (`PLAN.md` Notes). `subscription`,
`function`, `name`, `cron`, `timezone`, `http`, `schedule` are all vendor-neutral and stay
that way; `test_core_names_no_stack_tokens` (`:490`) scans the `CORE:BEGIN`/`CORE:END`
slice against `_STACK_TOKEN_DENYLIST` and will catch a leak. Escalate rather than
special-case one provider.

**Enumerated test surface (from `G1-PLAN`'s AC8 runtime probe — do not rediscover it).**
The re-key was applied locally and `python3 -m unittest discover -s tests -v` was run in
full. With the algorithm re-keyed and the fixture pattern tables left alone, exactly four
of 1473 tests go red:

```
FAIL: test_discovered_config_passes_lint_monitoring (test_derive_monitoring_discovery.TestDiscoveredConfigPassesLint)
      AssertionError: Lists differ: ["missing top-level 'components' key"] != []
FAIL: test_fixture_tree_yields_expected_components (test_derive_monitoring_discovery.TestFixtureTreeYieldsExpectedComponents)
      AssertionError: 0 != 2
FAIL: test_second_stacks_render_also_passes_lint (test_derive_monitoring_discovery.TestNeutralRecordsSurviveASecondStack)
      AssertionError: Lists differ: ["missing top-level 'components' key"] != []
FAIL: test_autofix_round_trips_as_quoted_off_string (test_derive_monitoring_discovery.TestAutofixQuotedInEmittedYaml)
      AssertionError: 'autofix: "off"' not found in '...components:\n'
```

All four have the same cause: the Stack A / Stack B trees carry no deployment artifact, so
a deployment-keyed matcher returns zero components. Migrating both fixture pattern tables
and both trees (AC4) closes all four. With that migration also applied, the probe's
residual is **one** assertion — `test_fixture_tree_yields_expected_components`'s
`web["evidence"] == ["services/web/handler.txt"]`, which becomes
`["services/web/deploy.txt", "services/web/handler.txt"]` — and nothing outside this test
module goes red. **The cascade is bounded to one file.** `audit_diagnosability` needs no
change: its role-name property (`:163-171`) checks `any(name in tree[relpath] ...)` across
a component's evidence, and the deployment file stamps the name.

**The probe also found a vacuous-pass hazard, and AC6 exists because of it.**
`TestNeutralRecordsSurviveASecondStack::test_neutral_records_survive_a_second_stack` and
`TestOutputIsDeterministic::test_output_is_deterministic` both **passed** during the
un-migrated probe run — against zero components. `len([]) == len([])`, `sorted([]) ==
sorted([])`, and two empty sets are disjoint. These are the feature's provider-neutrality
boundary tests and they can currently pass on an empty discovery result.

**Acceptance criteria.**

1. `tests/test_derive_monitoring_discovery.py::TestDeploymentKeyedDiscovery::test_one_deployable_with_two_triggers_is_one_component`
   exists and **fails on HEAD before this WU runs** —
   `python3 -m unittest tests.test_derive_monitoring_discovery.TestDeploymentKeyedDiscovery -v`
   exits non-zero (no such class today, which counts as red). The test builds a tree with
   **one** deployment artifact and **two** trigger registrations inside its scope and
   asserts `len(discover_components(tree, patterns)) == 1`. On HEAD's trigger-keyed matcher
   the same shape yields 2, so the assertion is red on behavior, not only on absence.
2. `discover_components` implements the contract table above: candidates are matched on
   `deployment_markers`; `patterns["triggers"]` is consumed within `scope_prefix`;
   `http_serving` and `message_consuming` are derived, never read from the candidate.
   `grep -n "evidence_markers" tests/test_derive_monitoring_discovery.py` returns zero hits.
3. Emitted records carry `subscriptions` and `schedules` lists in trigger-table order, and
   `evidence` is sorted and free of duplicates.
4. `_STACK_A_PATTERNS` / `_STACK_A_TREE` and `_STACK_B_PATTERNS` / `_STACK_B_TREE` are
   migrated to the new contract — each stack gains a deployment artifact per component and
   a `triggers` table, and each candidate loses its hand-declared dials. Both stacks keep
   their entirely-disjoint marker vocabularies and names, which is the AC4 boundary
   property `TestNeutralRecordsSurviveASecondStack` exists to assert.
5. The same scoped test **passes after this WU's edits** —
   `python3 -m unittest tests.test_derive_monitoring_discovery.TestDeploymentKeyedDiscovery -v`
   exits zero.
6. `test_neutral_records_survive_a_second_stack` and `test_output_is_deterministic` each
   gain a non-emptiness assertion (`assertEqual(len(stack_a), 2)` /
   `assertTrue(first)`) so neither can pass on an empty discovery result. This closes the
   vacuous-pass hazard the probe exposed; without it the gate's own boundary tests are
   satisfiable by a discovery function that returns nothing.
7. `_with_subscriptions` (`:356`) and all four of its call sites (`:374`, `:440`, `:444`,
   `:463`) are **deleted**. It was T03's deliberate stand-in for evidence gate 2 derives —
   its own docstring says so. Leaving it in place would let every downstream assertion pass
   on test-injected subscription data rather than on data discovery derived, which is
   precisely the property this gate exists to prove.
   `grep -c "_with_subscriptions" tests/test_derive_monitoring_discovery.py` returns `0`.
8. The module docstring's description of `discover_components` (`:17-19`) and the
   `discover_components` docstring both describe the deployment-keyed contract. The stale
   phrase "matches an injected evidence-pattern table" no longer describes a table that
   does not exist.
9. `python3 -m unittest discover -s tests -v` exits zero. The full suite is the check that
   the cascade stayed inside this file, which the probe predicts and this criterion
   confirms.

**Do not touch.** `suggest_checks` (`:90`) — it consumes `subscriptions` already and
gains nothing here; **per-schedule `heartbeat` targets are `FEAT-2026-0069/T07`'s
deliverable**, deliberately deferred so this WU's red/green proof is about keying and not
about check emission. `render_monitoring_yml` (`:183`) — it already emits nested
`targets`, verified by `TestRenderTargetsRoundTrip` (`:590`); no rendering change is
needed and one would be out of scope. `audit_diagnosability` (`:132`) — the probe
confirms it stays green under the re-key; changing it here would be unforced. Adding a
Stack C fixture — that is `T07`'s `produces:`, and this file is shared between the two
WUs, so keep this WU's diff to the re-key plus the Stack A/B migration.
`specfuse/loop/lint_monitoring.py` — `FEAT-2026-0069/T05` owns it in this gate.
`_STACK_TOKEN_DENYLIST` — it is duplicated verbatim in
`tests/test_design_for_diagnosis_rule.py:25` by design (the two boundary tests keep
identical denylists rather than sharing an import); out of scope for this WU, and touching
one copy without the other is the §10 failure mode. Gate 1's WU files and `GATE-01.md`.
`PLAN.md`'s `status` field. `.git/`, secrets. The driver owns all git operations — you
edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set from `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage`, `leak-scan`, `monitoring-example-lint`, `leak-scan-hook`,
`sync-scaffold-bats`, `init-sh-shim-bats`, `init-skills-bats`. Scoped red/green proof:
`python3 -m unittest tests.test_derive_monitoring_discovery.TestDeploymentKeyedDiscovery -v`.
Module-scoped regression check while iterating (seconds, not minutes):
`python3 -m unittest tests.test_derive_monitoring_discovery -v`.

> Sandbox note (`.specfuse/LEARNINGS.md` `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`): the
> three `bats` gates call `mktemp -d` in `setup`, which the default session sandbox denies
> (`Operation not permitted`) before any assertion runs. Report which sandbox each gate ran
> under; do not read a sandbox denial as a regression.

**Escalation triggers.** Emit `status: blocked` if the full suite goes red **outside**
`tests/test_derive_monitoring_discovery.py` — `G1-PLAN`'s probe says the cascade is
bounded to this one file, and a failure elsewhere means the probe's re-key differs from
the one being implemented in a way the operator needs to see, not a way this session
should absorb. Also block if satisfying AC1 appears to require changing
`audit_diagnosability` or the skill's Step 1 contract: `GATE-01.md`'s arming discipline
names exactly that as the multi-WU cascade that does not fit one gate. Blocked is a
respectable outcome (`result-contract.md` rule 4).
</content>
