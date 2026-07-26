---
id: FEAT-2026-0069/T08
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
oracle_env: macos_local
produces:
  - plugins/specfuse/skills/derive-monitoring/SKILL.md
  - plugins/specfuse/skills/derive-monitoring/PROMPT.md
  - .specfuse/skills/derive-monitoring/SKILL.md
  - .specfuse/skills/derive-monitoring/PROMPT.md
  - tests/test_derive_monitoring_skill_registration.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.4.0
started_at: 2026-07-26T20:25:23.974315+00:00
duration_seconds: 360.603
cost_usd: 1.031204
input_tokens: 52
output_tokens: 9157
---

# Make the `derive-monitoring` skill's method prose describe deployment-keyed discovery

**Objective.** Bring the skill's Step 1, Step 3, and Seams sections into agreement with
what the reference implementation does after `T06` and `T07`, so the prose an operator
follows and the algorithm the tests pin are one thing rather than two.

**Context.** This is `FEAT-2026-0069/T08`, the last substantive work unit of gate 2. It
depends on `FEAT-2026-0069/T07`; the prose cannot be written truthfully before the
behavior it describes exists.

`PLAN.md`'s gate 2 sketch names the gap: *"`derive-monitoring`'s Step 1 and Step 4
currently describe component discovery with no target concept."* Gate 1's close narrowed
that — both `SKILL.md` copies now show `targets[]` on `dlq` in every worked example, and
§4a already carries the per-check-type targets matrix (`SKILL.md:200-212`). What gate 1
did **not** touch is the *discovery* half:

- **Step 1** (`SKILL.md:93-110`) still frames a component as a thing you find by gathering
  "the evidence that it is HTTP-serving, message-consuming, or neither" — the trigger-keyed
  framing `T06` replaces. It also describes `discover_components(tree, patterns)` as
  matching "an evidence-pattern table", and lists the emitted record's fields as `name`,
  `type`, `http_serving`, `message_consuming`, `evidence` — with no `subscriptions` and no
  `schedules`.
- **The Seams table** (`SKILL.md:292-298`) describes the stack-specific input of step 1 as
  "the `patterns` table: per-stack evidence markers." After `T06` the stack-specific input
  is two tables — deployment markers with a scope prefix, and a trigger table.
- **`PROMPT.md:50-54`** repeats the same two claims in the dispatch prompt.

**Canonical copy first.** `plugins/specfuse/skills/` is the marketplace-published plugin
and the canonical source; `.specfuse/skills/` is a byte-for-byte vendored copy produced by
`scripts/sync-scaffold.sh`, and `tests/test_skills_vendored_in_sync.py` is the drift guard.
Edit the canonical copy, then run the sync script — never hand-edit the vendored copy, and
never edit only one. The two copies are byte-identical today (`cmp` exits `0`).

**`Red-test exempt`: not claimed.** This WU ships prose, but the prose has a mechanical
oracle: `tests/test_derive_monitoring_skill_registration.py` already asserts specific
strings against `_CANONICAL_DIR`, and AC1 adds to it.

**Acceptance criteria.**

1. `tests/test_derive_monitoring_skill_registration.py::TestStep1IsDeploymentKeyed::test_step_1_describes_deployment_keyed_discovery`
   exists and **fails on HEAD before this WU runs** —
   `python3 -m unittest tests.test_derive_monitoring_skill_registration.TestStep1IsDeploymentKeyed -v`
   exits non-zero (no such class today). It asserts against `_CANONICAL_DIR / "SKILL.md"`
   that the Step 1 text names deployment evidence as the discovery key and names both
   `subscriptions` and `schedules` as record fields — assertions that are false on HEAD's
   prose, so the test is red on content and not only on absence.
2. Step 1 states the keying rule in one sentence a reader cannot misapply: **a component is
   a deployable** — it exists because a deployment artifact names it — **and a trigger
   registration is evidence of that deployable's type and the source of its target list,
   never a component in its own right.** It gives the operative reason, which is the reason
   `PLAN.md` opens with and is decisive rather than stylistic: the role name a telemetry
   backend reports is **per-process**, so N triggers in one host share one role name, and N
   components would each carry the same role-name-keyed `error-logs` and `heartbeat` query —
   N duplicate findings per exception.
3. Step 1's description of the reference implementation matches it after `T07`: the
   `patterns` input is deployment markers plus a scope prefix per candidate and a sibling
   trigger table; the emitted record carries `subscriptions` and `schedules`; `http_serving`
   and `message_consuming` are **derived** from matched triggers, not declared.
4. The Seams table's step-1 rows name the two stack-specific tables (deployment markers +
   scope prefix; the trigger table) instead of "per-stack evidence markers". The invariant
   the table exists to state is unchanged and must survive the edit: a new stack is a new
   pattern table, never a change to `discover_components`, `suggest_checks`, or
   `audit_diagnosability`.
5. Step 3's question list is **unchanged in length and content** — the five legitimate
   questions stay five. A sentence in Step 1 or Step 3 states that target lists are derived
   from trigger evidence and are **never** an operator question, and that a coordinate
   discovery cannot name means the check is omitted rather than asked about, which is the
   rule `SKILL.md:210-212` already states for `dlq`. Asking the operator to enumerate
   subscriptions would be a Forbidden question by the skill's own definition.
6. `PROMPT.md`'s description of `discover_components` (`:50-54`) is corrected to match AC3.
   Everything else in `PROMPT.md` is out of scope.
7. Both copies are byte-identical after `scripts/sync-scaffold.sh` runs:
   `cmp plugins/specfuse/skills/derive-monitoring/SKILL.md .specfuse/skills/derive-monitoring/SKILL.md`
   and the same for `PROMPT.md` each exit `0`, and
   `python3 -m unittest tests.test_skills_vendored_in_sync -v` exits zero.
8. The same scoped test **passes after this WU's edits** —
   `python3 -m unittest tests.test_derive_monitoring_skill_registration.TestStep1IsDeploymentKeyed -v`
   exits zero.
9. `python3 -m unittest discover -s tests -v` exits zero — in particular every existing
   assertion in `tests/test_derive_monitoring_skill_registration.py` stays green, including
   the draft-never-write hard rule, the `WARN`-not-`ERROR` posture, and the
   credential-tokens-are-env-var-names-only scan.

**Do not touch.** `tests/test_derive_monitoring_discovery.py` — `T06` and `T07` own it, and
this WU describes their result rather than changing it; if the prose cannot be written
truthfully, that is an escalation, not a code edit. `SKILL.md`'s `## Hard rules` section
and the `## What this skill does *not* do` list — the draft-never-write posture and the
"does not modify `lint_monitoring.py` / `monitoring.yml.example`" boundaries are settled and
have tests behind them. §4a's per-check-type targets matrix (`SKILL.md:200-212`) — gate 1's
close wrote it and it is already correct. `.specfuse/skills/derive-monitoring/*` as a
hand-edit target — it is generated by `scripts/sync-scaffold.sh` from the canonical plugin
copy; editing it directly is the drift the guard test exists to catch. Other skills under
`plugins/specfuse/skills/`. `specfuse/loop/lint_monitoring.py` (`T05` owns it in this gate).
Gate 1's WU files and `GATE-01.md`. `PLAN.md`'s `status` field. `.git/`, secrets. The driver
owns all git operations — you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set from `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage`, `leak-scan`, `monitoring-example-lint`, `leak-scan-hook`,
`sync-scaffold-bats`, `init-sh-shim-bats`, `init-skills-bats`. Scoped red/green proof:
`python3 -m unittest tests.test_derive_monitoring_skill_registration.TestStep1IsDeploymentKeyed -v`.
Copy-identity check:
`cmp plugins/specfuse/skills/derive-monitoring/SKILL.md .specfuse/skills/derive-monitoring/SKILL.md && cmp plugins/specfuse/skills/derive-monitoring/PROMPT.md .specfuse/skills/derive-monitoring/PROMPT.md`.

> Sandbox note (`.specfuse/LEARNINGS.md` `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`): the
> three `bats` gates call `mktemp -d` in `setup`, which the default session sandbox denies
> (`Operation not permitted`) before any assertion runs. `sync-scaffold-bats` is one of
> them, and this WU runs `scripts/sync-scaffold.sh` itself — if the script fails on a
> `mktemp` denial rather than on its own logic, say so and re-run with the sandbox
> disabled rather than reading it as a regression.

**Escalation triggers.** Emit `status: blocked` if the prose cannot be written truthfully
because `T06`/`T07` landed a contract different from the one those WUs specify — the fix is
to the code or to the plan, and prose that papers over the difference is the failure this WU
exists to prevent. Also block if `scripts/sync-scaffold.sh` reports drift in a path this WU
did not edit: that means the vendored tree diverged from canonical before this gate, which
is a separate hygiene finding for the operator. Blocked is a respectable outcome
(`result-contract.md` rule 4).
