---
id: FEAT-2026-0039/T08
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.50
produces:
  - tests/test_monitoring_fenced_blocks.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.4.0
started_at: 2026-07-26T05:10:26.498699+00:00
duration_seconds: 298.653
cost_usd: 0.877608
input_tokens: 54
output_tokens: 8341
---

# Add the fenced-yaml-block drift test

**Objective.** Add `tests/test_monitoring_fenced_blocks.py` — a drift guard that
extracts every fenced `yaml` block from the `derive-monitoring` skill and the
local-runner bootstrap artifacts and runs each through `validate_monitoring`, so no
example anywhere in this feature can silently drift from gate 1's schema.

**Context.** This is `FEAT-2026-0039/T08`, the last substantive WU of gate 2,
following T06 and T07. Read `PLAN.md` in this folder (its **Gate 2 sketch** section
declares this test) and `GATE-02.md`'s definition of done, whose fifth bullet is
exactly this test's assertion.

**Why this exists.** Gate 1 shipped one validated example
(`.specfuse/monitoring.yml.example`, guarded by the `monitoring-example-lint` gate).
Gate 2 adds several more, all living inside markdown prose where no gate looks. A
prose example that drifts is worse than no example: an operator copies it, the
validator rejects the result, and the skill's whole credibility goes with it.

**The surfaces this test covers**, declared as an explicit list in the test module so
a reader can see the scope rather than infer it from a glob:

- `plugins/specfuse/skills/derive-monitoring/SKILL.md`
- `plugins/specfuse/skills/derive-monitoring/PROMPT.md`
- `.specfuse/skills/derive-monitoring/SKILL.md`
- `.specfuse/skills/derive-monitoring/PROMPT.md`
- `.specfuse/monitoring-secrets-checklist.md`

`.specfuse/monitoring.overrides.yml.example` is a YAML file, not prose, and T06
already validates it directly; do not double-cover it here.

**The fragment problem, and the convention that solves it.** `validate_monitoring`
requires top-level `environments:` and `components:` keys, so a block showing only a
`checks:` snippet reports "missing top-level 'environments' key" and a naive
extractor would demand every snippet be a whole file. The convention:

- A fenced `yaml` block is validated as a **complete config** by default.
- A deliberate fragment carries `# lint-monitoring: fragment` as its **first line**.
  The extractor skips it — and the test asserts the *count* of fragment markers
  against an explicit expected number, so the escape hatch cannot quietly become the
  norm. A new fragment is a one-line test edit and a visible decision.

**How to call the validator.** `validate_monitoring` takes a **path**, not a string
(read `specfuse/loop/lint_monitoring.py`). Write each extracted block to a
`tempfile` path and validate that. Import from `specfuse.loop.lint_monitoring`, the
canonical module — not from the `.specfuse/scripts/` shim.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `verification-discipline.md`) apply. Do not restate them.

**Acceptance criteria.**

1. `tests/test_monitoring_fenced_blocks.py::test_every_yaml_block_validates_clean`
   exists and **fails on HEAD before this WU's edits** (the module does not yet
   exist). It extracts every fenced `yaml` block from the five declared surfaces,
   writes each to a temporary path, calls `validate_monitoring`, and asserts an empty
   finding list — with a failure message naming the source file and the block's line
   number, so a drift failure is diagnosable without bisecting.
2. **Negative observation.** `test_extractor_catches_a_broken_block` builds a
   markdown string in the test containing a `yaml` block with a single deliberate
   defect (an out-of-enum `runner` value) and asserts the extraction-plus-validate
   path reports exactly one finding naming that dial. Without this, a broken
   extractor that finds zero blocks passes AC1 vacuously
   (`verification-discipline.md` §3).
3. `test_extractor_finds_the_expected_block_count` asserts the total number of
   extracted `yaml` blocks across the five surfaces is at least 1 and equals an
   explicit expected count declared in the test. This is the second half of the
   vacuous-pass guard: a glob that silently matches nothing turns this red.
4. `test_fragment_markers_are_bounded` asserts every skipped block carries
   `# lint-monitoring: fragment` as its first line, and that the number of such
   blocks equals an explicit expected count declared in the test.
5. `test_declared_surfaces_all_exist` asserts each of the five declared paths exists
   — so a T07 rename or a sync miss surfaces here as a named failure rather than as
   a silently shrunken scan.
6. **Coverage-scope statement.** The test module carries a comment listing the
   monitoring-example surfaces this test does **not** cover and why — at minimum
   `docs/concepts/monitoring-schema.md`'s `## Example` section, which gate 1 shipped
   and which no gate currently validates. Either extend the declared surface list to
   include it (preferred, if its example is a complete config) or record the
   exclusion with a one-line reason. A silent omission reads as "covered everything"
   when it is not.
7. Any monitoring config the test builds inline uses obvious `acme-*` placeholders
   for every organization name, host, workspace ID, and queue name, and no
   credential-shaped literal — `leak-scan` runs on this diff and the pre-commit hook
   is stricter than the CI gate.
8. Every new `subprocess.run` call, if any, declares `check=` explicitly (`PLW1510`,
   enforced since FEAT-2026-0037).

**Do not touch.** The skill files under `plugins/specfuse/skills/derive-monitoring/`
and `.specfuse/skills/derive-monitoring/` (T07 owns them — if a block fails this
test, that is a real defect in T07's example and it escalates; do not edit the
example to make the test pass, and do not loosen the test to accept it); the
bootstrap artifacts (T06); `specfuse/loop/lint_monitoring.py` and
`.specfuse/monitoring.yml.example` (gate 1); `.specfuse/verification.yml`;
`.specfuse/rules/design-for-diagnosis.md` (T04); the discovery reference
implementation (T05); `.git/`, secrets. The driver owns all git operations. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` — `tests`,
`lint`, `security`, `coverage` ≥ 90%, `leak-scan`, `monitoring-example-lint`, and
the bats suites — must all pass, plus
`python3 -m pytest tests/test_monitoring_fenced_blocks.py -v` run directly and read
for the AC1–AC5 test names. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if a block in T07's skill fails
validation — that is a real defect in T07's deliverable, and the correct response is
to escalate it, not to edit T07's file (this WU does not own it) and not to weaken
the test (`never-touch.md`'s note on `verification.yml`: the response to a failing
gate is to fix what it flags). Also block if the fragment convention cannot be
applied because the skill's examples are predominantly fragments — that would mean
the drift test covers almost nothing, which is a human decision about gate 2's
verification story rather than something to accept quietly. If
`tests/test_monitoring_fenced_blocks.py` is absent from the files you edited, emit
`status: blocked` — do not claim complete. Blocked is respectable
(`result-contract.md` rule 4).
