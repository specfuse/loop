---
id: FEAT-2026-0069/T03H
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
produces:
  - .specfuse/monitoring.yml.example
  - specfuse/loop/data/monitoring.yml.example
  - .specfuse/monitoring.overrides.yml.example
  - specfuse/loop/data/monitoring.overrides.yml.example
  - plugins/specfuse/skills/derive-monitoring/SKILL.md
  - tests/test_monitoring_example.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.4.0
started_at: 2026-07-26T17:49:38.659154+00:00
duration_seconds: 436.12
cost_usd: 0.834602
input_tokens: 44
output_tokens: 9558
---

# Hygiene: give every remaining shipped `dlq` check its `targets`

**Objective.** Add `targets` to the three shipped `dlq` checks that T02's
migration missed, and add the acceptance criterion T02 lacked — that **zero**
target-less `dlq` checks remain anywhere — so T03 can make `targets` required
without inheriting a non-conforming tree.

**Context.** This is `FEAT-2026-0069/T03H`, a **hygiene work unit** inserted
because `FEAT-2026-0069/T03` blocked. Per
`.specfuse/skills/authoring-work-units/SKILL.md` §7, the evidence for why this
WU exists is quoted verbatim from `events.jsonl`:

```json
{
  "timestamp": "2026-07-26T17:21:20.267922+00:00",
  "correlation_id": "FEAT-2026-0069/T03",
  "event_type": "human_escalation",
  "source": "driver",
  "source_version": "0.4.0",
  "payload": {
    "reason": "spinning_signature_repeat",
    "failure_class": "tests",
    "failure_signature": "$ python3 -m unittest discover -s tests -v",
    "attempts": 3
  }
}
```

T03's attempt-3 note names the decisive finding:

```
### monitoring-example-lint: FAIL
  - component 'order-worker': checks[0]: 'dlq' check requires 'targets'
    — each target needs 'subscription' and 'function'
```

**What went wrong, so you fix the cause and not just the symptom.** T02's
objective was to *migrate every shipped surface*; its acceptance criteria tested
*adding* one — "at least one `dlq` check with ≥2 targets." That was satisfiable
while leaving every pre-existing `dlq` check untouched, and it was. T03 then
made `targets` required and the tree it inherited was already non-conforming.
T03's agent correctly refused to reach into T02's files (its escalation trigger
forbids it) and blocked. **The missing criterion is the durable deliverable
here** — the YAML edits alone would let the same gap recur on the next
migration.

**The complete enumeration** (run at authoring time via
`grep -c "type: dlq"` vs `grep -c "targets:"` across every shipped surface;
§10). Three logical surfaces remain, two of them duplicated across a copy pair:

1. `.specfuse/monitoring.yml.example` — the `order-worker` component's `dlq`
   check (~line 103). **Byte-identical twin:** `specfuse/loop/data/monitoring.yml.example`.
2. `.specfuse/monitoring.overrides.yml.example` — the `dlq` check at ~line 66.
   **Byte-identical twin:** `specfuse/loop/data/monitoring.overrides.yml.example`.
3. `plugins/specfuse/skills/derive-monitoring/SKILL.md` — the `dlq` check in the
   **§4b overrides** fenced block (~line 238). The §4a block at ~line 189
   already has targets; do not touch it. Propagate to `.specfuse/skills/` with
   `scripts/sync-scaffold.sh` — do **not** hand-edit the synced copies.

**Your oracle already exists — one test per surface.** The operator reproduced
T03's escalated failure in full (applied the contract flip locally, ran
`python3 -m unittest discover -s tests -v`, reverted). Each of the three
surfaces has an existing test that lints it, currently green **only because
`targets` is still optional**, and each goes red the instant T03 flips:

| Surface | Test that will catch it |
|---|---|
| 1 `monitoring.yml.example` | `test_monitoring_example.MonitoringExampleTests.test_shipped_example_validates_clean` |
| 2 `monitoring.overrides.yml.example` | `test_monitoring_bootstrap_artifacts.TestOverridesExampleValidatesClean.test_overrides_example_validates_clean` |
| 3 `derive-monitoring/SKILL.md` §4b | `test_monitoring_fenced_blocks.MonitoringFencedBlockTests.test_every_yaml_block_validates_clean` |

Do **not** author duplicates of these. What is genuinely missing is the
tree-wide criterion below (AC1) — the one that fails *now*, while `targets` is
optional, and so would have caught T02's partial migration at T02 time.

Binding rules in `.specfuse/rules/` apply.

**Acceptance criteria.**

1. **Red test — the criterion T02 lacked:**
   `tests/test_monitoring_example.py::TestNoTargetlessDlqRemains::test_no_shipped_surface_has_a_targetless_dlq`
   exists and **fails on HEAD before this WU's edits**, naming the offending
   file(s). It asserts that **no shipped surface contains a `dlq` check without
   a non-empty `targets` list** whose entries each carry `subscription` and
   `function`.

   Scope it over an **explicit file list** — the six paths in `produces:` plus
   the two `.specfuse/skills/derive-monitoring/*` synced copies — not a glob, so
   a new surface must be added consciously. For the two prose files, extract
   ```yaml fences the way `tests/test_monitoring_fenced_blocks.py` already does;
   reuse that helper rather than writing a second extractor.

   This is the load-bearing deliverable. It fails **now**, while `targets` is
   still optional, which is exactly what T02's ACs could not do — they asserted
   a new component *had* targets, never that no check *lacked* them.
2. After this WU's edits that test passes.
4. `order-worker`'s `dlq` check in **both** `monitoring.yml.example` copies
   carries `targets` with ≥1 entry, each with `subscription` and `function`.
   Placeholders only (`acme-*`) — `leak-scan`'s pre-commit form is stricter than
   its CI form and bites on this surface.
5. The `dlq` check in **both** `monitoring.overrides.yml.example` copies
   carries `targets` in the same shape.
6. The §4b fenced block in `plugins/specfuse/skills/derive-monitoring/SKILL.md`
   carries `targets`; `.specfuse/skills/derive-monitoring/SKILL.md` is updated
   **by running `scripts/sync-scaffold.sh`**, and `git diff --stat` shows it
   changed without having been hand-edited.
7. `cmp` exits 0 for both copy pairs:
   `.specfuse/monitoring.yml.example` vs `specfuse/loop/data/monitoring.yml.example`,
   and `.specfuse/monitoring.overrides.yml.example` vs
   `specfuse/loop/data/monitoring.overrides.yml.example`.
8. `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example`
   exits 0, and `tests/test_monitoring_fenced_blocks.py` passes — both must stay
   green, because `targets` is still **optional** at this point.
9. **`targets` remains optional on `dlq` after this WU.** T03 makes it required;
   this WU must not. A test asserting a target-less `dlq` is rejected belongs to
   T03 and must not appear here — if you add it, T03 has nothing left to turn red
   and its red-test contract is broken.
10. Coverage stays ≥ 90%.

**Do not touch.**

- `specfuse/loop/lint_monitoring.py` — **this WU changes data and tests only.**
  Making `targets` required is T03's entire job; doing it here would leave T03
  with no red test and collapse the expand → migrate → contract sequence that
  `PLAN.md`'s escalation-predicate section depends on.
- `.specfuse/features/FEAT-2026-0069-monitoring-check-targets/WU-02-*.md` and
  `WU-03-*.md` — T02 is `done` and T03 is being re-armed unmodified. Its scope
  and Do-not-touch bounds are intact by design; that is why the block was
  diagnosable.
- `CHECK_TYPES` / `queue-stalled` — T04.
- `discover_components` / `_STACK_A_PATTERNS` — gate 2.
- `.specfuse/skills/derive-monitoring/*` as direct edits — outputs of
  `scripts/sync-scaffold.sh`, not sources.
- `.git/`, secrets. The driver owns all git operations. See
  `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` — `tests`,
`ruff`, `bandit`, coverage ≥ 90%, `leak-scan`, `monitoring-example-lint`, and
the bats suites — must all pass, plus the two `cmp` checks in AC7.

**Escalation triggers.** Emit `status: blocked` if:

- A fourth target-less `dlq` surface turns up that the enumeration above does not
  list. That means the §10 enumeration was incomplete — report the surface so the
  count is corrected rather than silently widening scope.
- `scripts/sync-scaffold.sh` does not reproduce the `.specfuse/skills/` copy.
- Adding the AC-3 tree-wide assertion requires making `targets` required in the
  validator to express it. It does not — the assertion reads the YAML directly —
  so if you conclude otherwise, halt rather than pulling T03's work forward.

Blocked is a respectable outcome (`result-contract.md` rule 4).
