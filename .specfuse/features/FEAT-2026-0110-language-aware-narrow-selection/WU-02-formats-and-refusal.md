---
id: FEAT-2026-0110/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
produces_driver_helper:
  - NARROW_SELECTION_FORMATS
produces:
  - specfuse/loop/loop.py
  - tests/test_language_aware_narrow_selection.py
---

# Complete the format set, and refuse an unknown one

**Objective.** Add the `path` format and the Gradle repeated-flag rendering, and
make an unknown `format` a `CONFIGURATION ERROR` naming the gate rather than a
silent fallback to the full suite.

**Context.** FEAT-2026-0110/T02, issue #3281. T01 shipped the config plumbing
and `class_name`. This unit finishes the contract `GATE-01.md` declares.

Why the refusal matters: an empty selection already falls back to the gate's
full `command` — fail safe by design. A *typo'd* format would take the same
path, so a project would declare narrowing, see the full suite run every
attempt, and have nothing to tell it why. That is the exact misattribution
FEAT-2026-0101 fixed for a degraded `feature_oracle`, and the convention to
follow is that one: refuse loudly, name the gate file, never pass silently.
There is no shared gate-key validator to extend (PLAN.md's existing-mechanism
search), so follow the per-site convention already at `loop.py:173`,
`loop.py:462` and the `feature_oracle` refusal.

Gradle is what `item_template` exists for: `--tests A --tests B` is a repeated
flag, which no `separator` alone can produce.

**Acceptance criteria.**

1. A new test in `tests/test_language_aware_narrow_selection.py` asserting the
   Gradle shape fails before this unit and passes after: a gate declaring
   `item_template: "--tests {module}"` with `separator: " "` and
   `format: class_name` resolves to `./gradlew test --tests FooTest --tests BarTest`.
2. `format: path` renders each selected `produces:` entry verbatim, asserted by
   a test in the same module (a JS-shaped fixture under `__tests__/` resolving
   to the paths themselves).
3. An unknown `format` value raises a `CONFIGURATION ERROR` whose message names
   `.specfuse/verification.yml` and the offending gate's `name`, asserted by a
   test that checks the message contains both; it does **not** fall back to the
   gate's full `command`.
4. `python3 -m unittest tests.test_language_aware_narrow_selection -v` exits 0,
   and a gate declaring no `narrow_selection` still resolves byte-identically:
   `python3 -m unittest tests.test_tiered_verification_e2e -v` exits 0.

**Do not touch.** `.specfuse/verification.yml`;
`CHANGED_FILE_SELECTION_ENABLED` and `select_tests_for_changed_files`; the
sibling WU files `WU-01-narrow-selection-config.md` and
`WU-03-document-the-contract.md`; plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set minus every gate declaring `tier: broad`,
with `tests` through its `narrow_command` over this unit's own `produces:` test
modules. Then `python3 -m unittest tests.test_language_aware_narrow_selection -v`.
Symbol check for each new symbol: `grep -n "<symbol>" specfuse/loop/loop.py`.
The broad tier is the driver's — never run in-session.

**Escalation triggers.** Stop with `status: blocked` if the `CONFIGURATION
ERROR` cannot be raised at a point where the gate's `name` is in scope (the
message is required to name it, and a refusal that cannot say which gate is
wrong is barely better than the silent fallback it replaces); or if adding the
refusal makes any existing gate in this repo's corpus report non-zero, which
would mean PLAN.md's satisfiability answer is wrong.
