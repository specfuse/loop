---
id: FEAT-2026-0103/T04H
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.00
provenance: "Gate 1 broad run (2026-09-10T02:32Z): test_package_data_matches_canonical — T04 wrote the defaults block into specfuse/loop/data/verification.yml.example, the package mirror, while the canonical .specfuse/verification.yml.example was left untouched; T04's produces: named the mirror, an authoring defect"
produces:
  - .specfuse/verification.yml.example
  - specfuse/loop/data/docs/methodology.md
model: sonnet
duration_seconds: 1232.612
cost_usd: 0.998202
input_tokens: 22
output_tokens: 2322
escalation_reason: spinning_signature_repeat
escalation_failure_class: tests
escalation_failure_signature: test_package_docs_match_canonical
re_arm_count: 1
re_arm_history:
  -
    timestamp: 2026-09-10T10:44:11+00:00
    prior_status: blocked_human
    prior_attempts: 2
    prior_cost_usd: 0.998202
    prior_duration_seconds: 1232.612
    reason: "go, try again"
reproduced_signature: "test_package_docs_match_canonical"
---

# Hygiene: both of T04's edits land on the canonical side and the mirrors are re-synced

**Objective.** T04 edited two documentation files on opposite sides of the
canonical/mirror split: the `defaults:` block went into the package mirror
`specfuse/loop/data/verification.yml.example` (canonical:
`.specfuse/verification.yml.example`, untouched), and the retain-and-repair
paragraph went into the canonical `docs/methodology.md` (mirror:
`specfuse/loop/data/docs/methodology.md`, untouched). Put the block into the
canonical example, refresh both mirrors, and make every test in
`tests/test_scaffold_data_in_sync.py` green.

**Context.** FEAT-2026-0103/T04H, hygiene precursor to the close. In this
repository `.specfuse/` is canonical and `specfuse/loop/data/` is its
byte-for-byte package copy, refreshed by `scripts/sync-scaffold.sh`
(comment at its head: ".specfuse/ sources into specfuse/loop/data/").
Repo `docs/` is canonical for `specfuse/loop/data/docs/` the same way
(`test_package_docs_match_canonical`; both tests say "Run:
scripts/sync-scaffold.sh"). Two drifts today, both T04's:
`diff .specfuse/verification.yml.example specfuse/loop/data/verification.yml.example`
shows one added block on the mirror side (19 lines, `# TOP-LEVEL
\`defaults:\` block` through the commented `defaults:` example), and
`diff docs/methodology.md specfuse/loop/data/docs/methodology.md` shows the
retain-and-repair paragraph on the canonical side only. Step 1: copy the
block, verbatim and at the same position, into `.specfuse/verification.yml.example`
— do not re-word it, the mirror is what the next release ships and T04's own
test reads it. Step 2: run `scripts/sync-scaffold.sh`; it must leave
`specfuse/loop/data/verification.yml.example` byte-identical to HEAD and
rewrite `specfuse/loop/data/docs/methodology.md` to match `docs/methodology.md`.
The first attempt of this unit did step 1 correctly and was refused by the
docs test it was not told about; this body now names both.

**Acceptance criteria.**

1. `python3 -m unittest tests.test_scaffold_data_in_sync -v` fails on HEAD
   with two failures (`test_package_data_matches_canonical`,
   `test_package_docs_match_canonical`) and exits 0 after — every test in
   that module, not one of them.
2. `diff .specfuse/verification.yml.example specfuse/loop/data/verification.yml.example`
   and `diff docs/methodology.md specfuse/loop/data/docs/methodology.md` both
   print nothing.
3. `git diff --stat` for this unit touches exactly `.specfuse/verification.yml.example`
   and `specfuse/loop/data/docs/methodology.md`;
   `specfuse/loop/data/verification.yml.example` and `docs/methodology.md`
   are byte-identical to HEAD.
4. `python3 -m unittest tests.test_retain_on_guard_refusal_docs -v` still exits 0.

**Do not touch.** `specfuse/loop/data/verification.yml.example` and
`docs/methodology.md` (T04's deliverables, already correct — this unit only
moves them to the side they belong on); `specfuse/loop/*.py`;
`.specfuse/verification.yml`; `.specfuse/rules/`.

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** Stop with `status: blocked` if `scripts/sync-scaffold.sh`
rewrites any path other than the two this unit produces (name the paths) —
that would be a third drift this unit must not absorb — or if the sync test
module reports a failure in neither of the two named tests.
