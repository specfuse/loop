---
id: FEAT-2026-0069/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces:
  - specfuse/loop/lint_monitoring.py
  - tests/test_lint_monitoring.py
  - tests/test_derive_monitoring_discovery.py
oracle_env: macos_local
---

# Contract: make `targets` required on `dlq` checks

**Objective.** Make a target-less `dlq` check a validator finding, and carry the
discovery reference implementation across the same break in the minimum way that keeps
it honest.

**Context.** This is `FEAT-2026-0069/T03`, the **contract** step of the expand →
migrate → contract sequence in `PLAN.md`'s escalation-predicate section. T01 taught the
validator to accept `targets`; T02 migrated every shipped example to carry them. Nothing
target-less should remain in the tree, which is what makes this flip safe.

Why `dlq` and not `heartbeat`: a DLQ **always** belongs to a specific subscription, so a
target-less `dlq` is always underspecified — on the observed host it means 20 unrelated
subscriptions fingerprinting into one bucket. A heartbeat on a single-process HTTP
service genuinely has nothing to enumerate; the component *is* the thing that went
silent. Requiring targets there would force a redundant self-referential target on every
HTTP component. The asymmetry traces to a property, not to convenience — preserve it.

**The coupling that shapes this WU** (enumerated in `PLAN.md`'s §10 note, so you are not
discovering it at dispatch cost): `suggest_checks()` in
`tests/test_derive_monitoring_discovery.py:102` emits a target-less
`{"type": "dlq", "harvest_mode": "peek"}` for any message-consuming component;
`render_monitoring_yml()` renders each check's own keys at one indent level;
`TestDiscoveredConfigPassesLint` (`:332`) runs that render through `validate_monitoring`
and asserts zero findings. This flip turns that test red, and the renderer cannot emit a
nested list-of-mappings at all. So this WU carries the **minimal** reference-implementation
change needed to keep it truthful — and no more.

**The line you must not cross.** `discover_components()` and the `_STACK_A_PATTERNS`
evidence table are **gate 2's scope**. Gate 2 re-keys discovery onto deployment evidence
so a deployable carrying N triggers yields one component with N targets. This WU changes
only what `suggest_checks` and `render_monitoring_yml` do with an **already-discovered**
record. If you find yourself editing the pattern table, stop — see the escalation
triggers.

**The honesty constraint on `suggest_checks`.** The `derive-monitoring` skill's hard rule
is that it never invents evidence. A DLQ target needs a real `subscription` and a real
`function`. So `suggest_checks` must read them off the component record (a neutral
`subscriptions` field, populated by discovery) and emit one target per known
subscription. A message-consuming component with **no** known subscriptions gets **no
`dlq` check at all** — that is the honest output, not a fabricated placeholder target.
This also pre-figures gate 2 correctly instead of contradicting it.

Binding rules in `.specfuse/rules/` apply.

**Acceptance criteria.**

1. `tests/test_lint_monitoring.py::TestTargetsRequired::test_dlq_without_targets_is_rejected`
   exists and **fails on HEAD before this WU's edits** — a target-less `dlq` validates
   clean today, asserted deliberately by T01's AC7. This test inverts that assertion.
2. After this WU's edits that test passes.
3. The finding text **names the fix inline**: it states that a `dlq` check requires
   `targets` and that each target needs `subscription` and `function`. A test asserts both
   coordinate names appear in the finding string. There is no migration document for an
   operator to fall back on (no live config exists to migrate), so the finding is the only
   place the fix gets explained — a finding that does not tell you what to write is a bad
   finding.
4. `heartbeat` **remains valid with no targets** — asserted explicitly, not left implied.
   A regression here silently forces a redundant target onto every HTTP component.
5. `error-logs` and `http-5xx` still reject targets (T01's behavior, unchanged) — assert
   it so this WU's edits cannot loosen it as a side effect.
6. `suggest_checks()` reads a neutral `subscriptions` list off the component record and
   emits one `dlq` target per entry, each carrying `subscription` and `function`.
7. `suggest_checks()` emits **no** `dlq` check for a message-consuming component whose
   record has no `subscriptions` — asserted by its own test. It does **not** invent a
   subscription name, a function name, or a placeholder target.
8. `render_monitoring_yml()` renders nested `targets` list-of-mappings at correct
   indentation. Round-trip test: render → `specfuse.loop._miniyaml.parse` → the parsed
   targets equal the input structure. Assert on the parse, not on the rendered string —
   string-shape assertions break on cosmetic changes and prove less.
9. `TestDiscoveredConfigPassesLint` passes: Stack A's fixture gains the minimum
   subscription data its message-consuming component needs to render a valid `dlq` check.
10. `TestNeutralRecordsSurviveASecondStack` passes — the second stack's render also flows
    through `validate_monitoring` and must not have been broken by the fixture change.
11. `TestSuggestChecksNeverInvariant` still passes, untouched.
12. `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` exits
    0 — T02 already migrated it, so this is the check that T02 actually did its job.
13. `tests/test_monitoring_fenced_blocks.py` passes: every shipped ```yaml block still
    validates against the now-stricter validator. If any block fails, T02 missed a
    surface — fix the block, do not loosen the validator.
14. Coverage stays ≥ 90%.

**Do not touch.**

- `discover_components()` and `_STACK_A_PATTERNS` in
  `tests/test_derive_monitoring_discovery.py` — **out of scope, handled in gate 2.** The
  re-keying onto deployment evidence is that gate's entire purpose. Adding fixture
  *data* (an existing component record's `subscriptions`) is in scope; changing what the
  matcher keys on is not.
- `.specfuse/monitoring.yml.example`, `specfuse/loop/data/monitoring.yml.example`, and
  `docs/concepts/monitoring-schema.md` — T02 owns them. If they need changing for this
  flip to pass, T02 was incomplete: block and say so rather than fixing it here, because
  a T02 gap that goes unreported will recur in the next migration.
- `CHECK_TYPES` and `queue-stalled` — T04.
- `specfuse/loop/_miniyaml.py`.
- `.git/`, secrets. The driver owns all git operations. See
  `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` — `tests`, `ruff`,
`bandit`, coverage ≥ 90%, `leak-scan`, and the bats suites — must all pass, plus the
explicit CLI exit check in AC12.

**Escalation triggers.** Emit `status: blocked` if:

- Making `dlq` targets required cannot be done without changing `discover_components` or
  the evidence pattern table. That would mean gate 1 and gate 2 are **not separable** and
  `PLAN.md`'s gate cut is wrong — which is a replan decision for the operator, not
  something to push through. Say which coupling forced it.
- A shipped example still carries a target-less `dlq` after T02. That is a T02 gap; report
  it rather than silently repairing it.
- Keeping `suggest_checks` honest appears to require inventing a subscription or function
  name. It does not — emitting no `dlq` check is the correct output — so if you conclude
  otherwise, halt and explain, because inventing evidence violates the
  `derive-monitoring` skill's central guarantee.

Blocked is a respectable outcome (`result-contract.md` rule 4).
</content>
