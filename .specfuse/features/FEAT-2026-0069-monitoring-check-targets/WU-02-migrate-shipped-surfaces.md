---
id: FEAT-2026-0069/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
produces:
  - .specfuse/monitoring.yml.example
  - specfuse/loop/data/monitoring.yml.example
  - docs/concepts/monitoring-schema.md
  - plugins/specfuse/skills/derive-monitoring/SKILL.md
  - tests/test_monitoring_example.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.4.0
started_at: 2026-07-26T16:49:49.228949+00:00
duration_seconds: 653.049
cost_usd: 1.51133
input_tokens: 1631
output_tokens: 12520
---

# Migrate every shipped surface to carry check targets

**Objective.** Add a functions-host component — one deployable, multiple DLQ targets,
multiple heartbeat targets — to the shipped example; document the component-vs-target
axis; and propagate the new shape through every fenced YAML block the repo ships, so
that T03 can make targets required without turning a correct tree red.

**Context.** This is `FEAT-2026-0069/T02`. Read `PLAN.md` in this folder — this WU is
the **migrate** step of the expand → migrate → contract sequence its
escalation-predicate section describes. T01 taught the validator to accept `targets`;
T03 will make them required on `dlq`. Between those two, every shipped example must
already carry targets, or T03 turns this repo's own `monitoring-example-lint` gate red
and (per FEAT-2026-0051's preflight baseline probe) halts the feature before T03's own
tests ever run.

The example you are extending currently models two components: an HTTP service and a
single-subscription queue consumer. Neither can show the bug this feature fixes, because
the bug only appears when **one deployable carries many subscriptions or schedules**.
That is the shape to add.

**Two propagation mechanics matter here, and getting either wrong wastes the WU:**

1. `.specfuse/monitoring.yml.example` and `specfuse/loop/data/monitoring.yml.example` are
   **byte-identical copies today**. The second is the packaged seed. Both must change
   together.
2. The `derive-monitoring` skill has four copies — two under
   `plugins/specfuse/skills/derive-monitoring/` (canonical, marketplace-published) and
   two under `.specfuse/skills/derive-monitoring/`. **Edit the canonical pair, then run
   `scripts/sync-scaffold.sh` to produce the others.** Hand-editing four files is the
   drift this repo already built tooling against, and the `sync-scaffold-bats` gate
   checks the sync.

`tests/test_monitoring_fenced_blocks.py` extracts every ```yaml block from five declared
surfaces and runs each through `validate_monitoring`. It is your fastest feedback loop:
run it after every edit, not at the end.

Binding rules in `.specfuse/rules/` apply — `security-boundaries.md` especially, see AC3.

**Acceptance criteria.**

1. `tests/test_monitoring_example.py::TestTargetsAreExercised::test_example_has_a_multi_target_dlq_check`
   exists and **fails on HEAD before this WU's edits** — no shipped example carries
   `targets` at all. It asserts the example contains at least one `dlq` check with two or
   more targets, each carrying both `subscription` and `function`.
2. After this WU's edits that test passes, and a companion assertion covers heartbeat: at
   least one `heartbeat` check with two or more targets carrying distinct `cron` values.
3. The example gains a **third component** modelling the motivating shape: one deployable
   whose `type` names it a multi-trigger host, carrying ≥ 2 DLQ targets on distinct
   subscriptions and ≥ 2 heartbeat targets on distinct schedules. **Placeholders only** —
   `acme-*` names, `Etc/UTC` for timezones, no real organization, host, queue, or
   workspace name. `.specfuse/rules/security-boundaries.md` and the `leak-scan` gate both
   bite on this surface, and `leak-scan`'s pre-commit form is stricter than its CI form.
4. The example's inline comments explain **why** the new component's checks are shaped
   that way — one `dlq` check with many targets rather than many `dlq` checks, and no
   attempt to make each trigger its own component. An example that shows the shape
   without the reason invites the next author to undo it.
5. `docs/concepts/monitoring-schema.md` gains a `## Check targets` section stating the
   axis distinction in the feature's own terms: component = unit of deployment and
   attribution; check target = unit of failure-artifact enumeration.
6. That section states the decisive reason N-components-per-trigger is not the fix:
   `cloud_RoleName` is **per-process**, so N components sharing one host would each carry
   an `error-logs`/`heartbeat` check that is literally the same query — N duplicate
   findings per exception — and the design-for-diagnosis property "per-component role
   name matches `monitoring.yml` `name`" becomes unsatisfiable by construction. This is
   the argument a future reader needs; without it the schema looks arbitrarily complex.
7. That section documents the per-type coordinate table: `dlq` → `subscription` +
   `function`; `heartbeat` → `name` + optional `cron`/`timezone`; `error-logs` and
   `http-5xx` → targets not permitted. It also states that targets are **not yet required**
   on `dlq` and that T03 changes this — or, if T03 has already landed, matches reality.
   Do not describe a state the validator is not in.
8. The `derive-monitoring` skill's Step 4a fenced example carries targets, edited in
   `plugins/specfuse/skills/derive-monitoring/SKILL.md` and propagated by
   `scripts/sync-scaffold.sh`. `git diff --stat` shows both
   `.specfuse/skills/derive-monitoring/*` files changed **without** having been edited by
   hand.
9. `cmp .specfuse/monitoring.yml.example specfuse/loop/data/monitoring.yml.example` exits
   0 — they are byte-identical today and nothing in this WU may split them.
10. `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` exits 0.
11. `tests/test_monitoring_fenced_blocks.py` passes — every ```yaml block across all five
    declared surfaces still validates clean.
12. `tests/test_monitoring_example.py`'s existing assertions still pass: the example
    exercises every member of `CHECK_TYPES` (`:59`) and the docs table documents every
    member (`:94`). This WU does not change the enum, so both should hold untouched — if
    either breaks, you have edited something T04 owns.

**Do not touch.**

- `specfuse/loop/lint_monitoring.py` — T01 shipped the validation, T03 flips the
  requirement. This WU changes data and prose, not logic.
- `CHECK_TYPES` and anything to do with `queue-stalled` — T04 owns the new check type.
- `tests/test_derive_monitoring_discovery.py` — T03 owns the reference-implementation
  change.
- `.specfuse/skills/derive-monitoring/SKILL.md` and `PROMPT.md` **as direct edits** — they
  are outputs of `scripts/sync-scaffold.sh`, not sources.
- `.git/`, secrets. The driver owns all git operations. See
  `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` — `tests`, `ruff`,
`bandit`, coverage, `leak-scan`, `sync-scaffold-bats`, and the other bats suites — must
all pass, plus the explicit `cmp` in AC9 and the CLI exit check in AC10.

**Escalation triggers.** Emit `status: blocked` if:

- `scripts/sync-scaffold.sh` does not reproduce the `.specfuse/skills/` copies from the
  canonical pair. Hand-editing four files to work around it defeats the gate that exists
  to catch drift; a broken sync script is worth surfacing.
- The `leak-scan` pre-commit hook rejects a placeholder you chose. Per
  `.specfuse/LEARNINGS.md` the hook is stricter than the CI oracle and has fired on
  innocuous tokens before; pick a different placeholder rather than suppressing the hook,
  and if no placeholder passes, block and say which token was rejected.
- The new component cannot be expressed without naming a specific broker or cloud vendor
  in the example. The example must read as neutrally as the existing `acme-broker` /
  `acme-telemetry` bindings do.

Blocked is a respectable outcome (`result-contract.md` rule 4).
