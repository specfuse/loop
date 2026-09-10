---
id: FEAT-2026-0103/T04H
type: implementation
status: blocked_human
attempts: 0
planned_cost_usd: 1.00
provenance: "Gate 1 broad run (2026-09-10T02:32Z): test_package_data_matches_canonical — T04 wrote the defaults block into specfuse/loop/data/verification.yml.example, the package mirror, while the canonical .specfuse/verification.yml.example was left untouched; T04's produces: named the mirror, an authoring defect"
produces:
  - .specfuse/verification.yml.example
model: sonnet
duration_seconds: 1232.612
cost_usd: 0.998202
input_tokens: 22
output_tokens: 2322
escalation_reason: spinning_signature_repeat
escalation_failure_class: tests
escalation_failure_signature: test_package_docs_match_canonical
---

# Hygiene: the `defaults:` block lives in the canonical example, mirrored by sync-scaffold

**Objective.** Put T04's `defaults:` documentation block into
`.specfuse/verification.yml.example`, the canonical file, so the package
mirror under `specfuse/loop/data/` byte-matches it again and
`tests/test_scaffold_data_in_sync.py` is green.

**Context.** FEAT-2026-0103/T04H, hygiene precursor to the close. In this
repository `.specfuse/` is canonical and `specfuse/loop/data/` is its
byte-for-byte package copy, refreshed by `scripts/sync-scaffold.sh`
(comment at its head: ".specfuse/ sources into specfuse/loop/data/").
`test_package_data_matches_canonical` compares the two. T04 edited only the
mirror, so `diff .specfuse/verification.yml.example
specfuse/loop/data/verification.yml.example` today shows exactly one added
block (19 lines, `# TOP-LEVEL \`defaults:\` block` through the commented
`defaults:` example). Copy that block, verbatim and at the same position,
into the canonical file. Do not re-word it: the mirror is already what the
next release ships and T04's own test reads it. Then run
`scripts/sync-scaffold.sh` (or verify the two files are byte-equal without
it) — the mirror must not change.

**Acceptance criteria.**

1. `python3 -m unittest tests.test_scaffold_data_in_sync -v` fails on HEAD
   (`content differs: verification.yml.example`) and exits 0 after.
2. `diff .specfuse/verification.yml.example specfuse/loop/data/verification.yml.example`
   prints nothing.
3. `git diff --stat` for this unit touches `.specfuse/verification.yml.example`
   only; `specfuse/loop/data/verification.yml.example` is byte-identical to HEAD.
4. `python3 -m unittest tests.test_retain_on_guard_refusal_docs -v` still exits 0.

**Do not touch.** `specfuse/loop/data/verification.yml.example` (T04's
deliverable, already correct); `docs/methodology.md`; `specfuse/loop/`;
`.specfuse/verification.yml`; `.specfuse/rules/`.

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** Stop with `status: blocked` if `scripts/sync-scaffold.sh`
rewrites anything other than the example file (name the paths) — that would
mean another drift this unit must not absorb.
