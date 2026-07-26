---
id: FEAT-2026-0039/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.00
produces:
  - .specfuse/rules/design-for-diagnosis.md
  - specfuse/loop/data/rules/design-for-diagnosis.md
  - tests/test_design_for_diagnosis_rule.py
oracle_env: macos_local
model: sonnet
effort: medium
---

# Author the design-for-diagnosis rule and seed it without @-importing it

**Objective.** Add `.specfuse/rules/design-for-diagnosis.md` — the reference rule
that says what a deployed component must do to be diagnosable — and seed it into
scaffolded projects **without** adding it to `CLAUDE.md`'s `@`-import list.

**Context.** This is `FEAT-2026-0039/T04`, the first WU of gate 2. Read `PLAN.md`
in this folder (its **Gate 2 sketch** section states this rule's posture as a
decision already made) and `GATE-02.md`'s definition of done.

**What the rule says.** It governs how the *target application's* code is written
so the check types gate 1's schema admits (`dlq`, `error-logs`, `http-5xx`,
`heartbeat`, `invariant`) can actually produce a diagnosable finding rather than a
bare alert. At minimum, one section per property, each with a *why* grounded in a
check type that fails without it:

- **Correlation IDs propagate** across component boundaries and appear in every log
  line and every message envelope — the property that makes an `error-logs` finding
  traceable to the request that caused it. Cross-reference
  `.specfuse/rules/correlation-ids.md`, which already governs the loop's own IDs;
  this rule is its application-runtime sibling, not a restatement.
- **Structured logging** — machine-parseable records with a stable field set, so an
  `error-logs` check can fingerprint repeat findings instead of diffing prose.
- **Per-component role names** that match the `name` field in `monitoring.yml`, so a
  harvested finding attributes to one component. A component whose logs do not
  self-identify makes a multi-component `monitoring.yml` undiagnosable.
- **DLQ error-context capture** — a dead-lettered message carries the failure
  context (exception, correlation ID, attempt count), not just the payload. A `dlq`
  check on a queue whose entries carry no context reports that something failed and
  nothing about why.

Keep it **provider-agnostic and language-agnostic**: no framework names, no logging
library names, no vendor names. The rule states properties; each project's
`.specfuse/rules-local/` states how it achieves them.

**The posture is reference-only, and that is the load-bearing decision.** This rule
governs application code, not how a work unit executes, so it sits in
`.specfuse/rules/` **unimported** — the same posture as `planning-discipline.md` and
`close-discipline.md`, neither of which appears in `_RULES_BLOCK`. Importing it
would tax every session in every downstream project for a rule most sessions never
consult. Do not add it to `_RULES_BLOCK` in `specfuse/loop/scaffold.py`, and do not
add it to this repo's `.claude/CLAUDE.md`.

**Seeding a new rule touches six enumerated surfaces.** All six are explicit lists;
a new rule file that misses any one of them fails a green suite. Read each before
editing, and update all six:

1. `specfuse/loop/data/rules/design-for-diagnosis.md` — the packaged copy (byte
   identical to the canonical `.specfuse/` file).
2. `scripts/sync-scaffold.sh` — the `FILES=()` array. **Not `CORE_FILES`**: that
   array is the subset vendored from the methodology core, and this rule is
   loop-authored, like `planning-discipline.md` and `close-discipline.md`.
3. `tests/test_scaffold_data_in_sync.py` — the `TRACKED` set.
4. `tests/test_scaffold_resources.py` — its expected-relpath list.
5. `tests/test_init_integration.py` — both lists: the module-level expected set and
   `test_rules_byte_faithful`'s list.
6. `tests/sync_scaffold.bats` — its `setup()` writes one fixture file per entry in
   `FILES`. `sync-scaffold.sh` runs under `set -euo pipefail` and `sync_file()`
   returns 1 on a missing canonical source, so a `FILES` entry with no bats fixture
   turns `[ "$status" -eq 0 ]` red.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `verification-discipline.md`) apply.
Do not restate them.

**Acceptance criteria.**

1. `tests/test_design_for_diagnosis_rule.py::test_rule_is_seeded` exists and
   **fails on HEAD before this WU's edits** (the rule file does not yet exist). It
   runs the scaffold init path into a temporary directory and asserts
   `rules/design-for-diagnosis.md` is present in the written relpaths.
2. After this WU's edits that test passes, and so does
   `tests/test_design_for_diagnosis_rule.py::test_rule_is_not_at_imported` —
   asserting `specfuse.loop.scaffold._RULES_BLOCK` does **not** contain the string
   `design-for-diagnosis`. This is the reference-only posture made executable; a
   later WU that "helpfully" imports the rule turns this test red.
3. A test asserts the seeded rule is **byte-identical** to
   `.specfuse/rules/design-for-diagnosis.md`, so the packaged copy cannot drift.
4. `python3 -m pytest tests/test_scaffold_data_in_sync.py tests/test_scaffold_resources.py tests/test_init_integration.py`
   exits 0 — all four enumerated list surfaces updated.
5. `bats tests/sync_scaffold.bats` exits 0 — surface 6 updated.
6. `grep -c "^## " .specfuse/rules/design-for-diagnosis.md` returns at least 4 — one
   section per property above.
7. The rule names **no** framework, logging-library, cloud-provider, or
   vendor-specific identifier. A test asserts the rule's text contains no member of
   a stack-token denylist the test declares inline (the same posture T05 uses to
   hold the provider-agnostic boundary). If a reviewer wants a vendor named, that is
   `.specfuse/rules-local/` work in the consuming project, not this file.
8. Every organization name, host, and queue name used as an illustration is an
   obvious placeholder (`acme-*`), never a real one — `leak-scan` runs on this
   diff and the pre-commit hook is stricter than the CI gate.
9. Every new `subprocess.run` call, if any, declares `check=` explicitly (`PLW1510`,
   enforced since FEAT-2026-0037).

**Do not touch.** `specfuse/loop/scaffold.py`'s `_RULES_BLOCK` (AC2 asserts it stays
unchanged — this is the decision, not an oversight); `.claude/CLAUDE.md`'s import
list; the existing rule files under `.specfuse/rules/`; `_SEED_RENAME`'s existing
entries; gate 1's shipped artifacts (`lint_monitoring.py`, `monitoring.yml.example`,
the shim, the gate); T05's, T06's, T07's and T08's deliverables; `.git/`, secrets.
The driver owns all git operations — you edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` — `tests`,
`lint`, `security`, `coverage` ≥ 90%, `leak-scan`, `monitoring-example-lint`, and
the bats suites (`sync-scaffold-bats`, `init-sh-shim-bats`, `init-skills-bats`) —
must all pass, plus AC4's and AC5's named commands run individually. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if seeding this rule cannot be done
without adding it to `_RULES_BLOCK` — the unimported posture is a recorded decision
in `PLAN.md`, and importing it to make a test pass reverses that decision silently.
Also block if a sixth-surface list turns out to be generated rather than
hand-maintained (a generator would own it, per `never-touch.md` §1). If
`.specfuse/rules/design-for-diagnosis.md` is absent from the files you edited, emit
`status: blocked` — do not claim complete. Blocked is respectable
(`result-contract.md` rule 4).
