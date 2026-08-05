---
id: FEAT-2026-0057/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
oracle_env: macos_local
generated_surfaces: []
produces:
  - .specfuse/verification.yml
  - tests/test_oracle_set_declared.py
  - .specfuse/skills/verification/SKILL.md
model: sonnet
effort: medium
gate_set: code
driver_version: 0.9.3
started_at: 2026-08-05T12:21:19.821013+00:00
duration_seconds: 754.855
cost_usd: 1.39874
input_tokens: 4
output_tokens: 1195
---

# Declare this repo's oracle set and document the pre-dispatch contract

**Objective.** Prove the contract on this repository by declaring one real oracle
set, guard it structurally, and write down how `prep` / `oracles` differ from
`extra_gates`.

`Red-test exempt: declaration and docs — the structural guard in criterion 2 is
this unit's oracle, and it asserts a configuration invariant rather than new
runtime behaviour. The runtime behaviour it depends on was proven red-to-green in
T01 and T02.`

**Context.** Correlation ID `FEAT-2026-0057/T03`, the last substantive unit in
this feature's only gate. It depends on `FEAT-2026-0057/T01` and
`FEAT-2026-0057/T02`, both `done`: the pre-dispatch runner and the capture budget
exist and are tested. Read `PLAN.md` in this folder for framing and the scope
boundary.

This unit exists because of what the feature's existing-mechanism search found.
`extra_gates` has shipped since issue #62, does most of what this feature's
roadmap entry asked for, and was never used — the mechanism was not missing, it
was undiscovered and mistimed. Shipping a second mechanism without documenting
the difference between them would reproduce exactly that outcome. So the
documentation here is load-bearing, not decoration: a reader must be able to tell
which of the two they want.

The grounding files:

- `.specfuse/verification.yml` — the file you add a set to. Read its header
  comments first: it declares itself the single source of truth for what CI runs,
  and `scripts/smoke-test.sh` derives its gate list from it at run time (#592).
  Note its authoring rule: **gate commands are self-contained** — no
  `--no-build`, `--no-restore`, or any skip-build flag.
- `specfuse/loop/gate_commands.py` — how sets are read by name, which is why
  adding a top-level key is additive.
- `.specfuse/skills/verification/SKILL.md` — the doc you extend.
- `tests/test_bats_suites_gated.py` — the structural-invariant guard precedent
  from FEAT-2026-0072: assert the invariant in both directions, and make the
  assertion itself falsifiable.

Binding rules apply by reference: `.specfuse/rules/result-contract.md`,
`.specfuse/rules/never-touch.md`, `.specfuse/rules/security-boundaries.md`,
`.specfuse/rules/correlation-ids.md`.

**Acceptance criteria.**

1. `.specfuse/verification.yml` declares a top-level `oracles` set with at least
   one entry, each carrying both `name` and `command`, and each command
   self-contained per the file's stated authoring rule (no skip-build flags).
2. `tests/test_oracle_set_declared.py` asserts the declared `oracles` set is
   non-empty and that every entry carries both a `name` and a `command` key, so a
   declared-but-malformed set fails on the first run rather than drifting. The
   test must be falsifiable: it fails if the set is emptied or an entry loses a
   key.
3. `.specfuse/skills/verification/SKILL.md` documents the `prep` and `oracles`
   frontmatter keys, stating that both resolve against `verification.yml` set
   names and that both run **before** dispatch.
4. The same document names `extra_gates`, states that it runs at **exit**, and
   gives a reader the rule for choosing between them.
5. `python3 -m unittest tests.test_oracle_set_declared` exits zero.

**Do not touch.**

- The three set bodies named `code:`, `doc:`, and `plannext:`. This unit edits
  `.specfuse/verification.yml` — that file is in its `produces` list — but only by
  **appending a new top-level `oracles:` key**. Do not edit, reorder, reword, or
  delete any entry inside those three existing sets, and do not touch the file's
  header comments. That additivity is what keeps the gate's other work units on a
  working oracle — see GATE-01.md's verification note.
- `specfuse/loop/prerun.py`, `specfuse/loop/prerun_capture.py`, and their tests —
  T01's and T02's files, already `done`.
- `scripts/smoke-test.sh` and `.github/workflows/ci.yml`. Both derive from
  `verification.yml` and must not grow a copy of the gate list; the file's header
  is explicit that a gate added there is executed by CI with no other edit.
- Generated directories, secrets (`.env`, `*.pem`, `*.key`, `credentials.json`),
  and `.git/` internals. See `.specfuse/rules/never-touch.md`.
- **The driver owns all git.** You edit files only — never run `git`.

**Verification.**

- The `code` gate set as declared in `.specfuse/verification.yml`: `tests`,
  `lint`, `security`, `coverage` (≥ 90%), `leak-scan`, `event-type-gate`,
  `roadmap-link-gate`, `arm-sweep-gate`.
- `python3 -m unittest tests.test_oracle_set_declared` (criterion 5).
- Confirm the `code` set still resolves after your edit — run the `tests` gate
  and check it executes the same suite it did before.

**Escalation triggers.**

- If declaring the `oracles` set changes how any existing set resolves, or if
  `scripts/smoke-test.sh` starts picking the new set up as a CI gate, emit
  `status: blocked`. Additivity is the assumption this unit and the gate's
  sequencing both rest on; if it is false, a human needs to decide the shape, not
  this session.
- If no honest oracle set can be declared for this repository — if every candidate
  command duplicates an existing `code` gate — block and say so rather than
  declaring a set that exists only to satisfy criterion 1. A hollow declaration is
  worse than an absent one, for the same reason the file's own header gives about
  declared-but-unrun gates.
- If `tests/test_oracle_set_declared.py` is absent from the files you edited, emit
  `status: blocked` — do not claim complete.
- Blocked is a respectable outcome (`.specfuse/rules/result-contract.md` rule 4).
