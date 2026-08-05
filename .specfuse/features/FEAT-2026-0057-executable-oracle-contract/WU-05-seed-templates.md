---
id: FEAT-2026-0057/T05
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
oracle_env: macos_local
generated_surfaces: []
provenance: "FEAT-2026-0057/G1-CLOSE second-pass RETROSPECTIVE.md follow-up FU-3R — T04 made the driver read `prep:`/`oracles:`, and neither key appears in either shipped WU template nor either shipped verification.yml.example, so a downstream project gets the behaviour with no seed documenting it."
produces:
  - specfuse/loop/data/templates/WU.template.md
  - specfuse/loop/data/verification.yml.example
  - tests/test_seed_documents_prerun_keys.py
---

# Document `prep`, `oracles`, and `extra_gates` in the shipped scaffold seeds

**Objective.** Make the two new frontmatter keys discoverable by a downstream
author, in the files `specfuse init` actually writes.

**Context.** Correlation ID `FEAT-2026-0057/T05`. Read `RETROSPECTIVE.md` in this
folder, follow-up **FU-3R**, before starting.

T04 wired `prep:` and `oracles:` into the driver, so they now change behaviour for
every project that upgrades. Neither key appears in
`specfuse/loop/data/templates/WU.template.md`, and no `oracles:` set appears in
`specfuse/loop/data/verification.yml.example`. Before T04 that gap was harmless —
nothing read the keys. Now the driver reads them and a downstream author has no
seed that mentions they exist.

**A related fact worth acting on.** `grep -c "extra_gates"` against the canonical
seed template returns **0**. `extra_gates` has shipped since issue #62 and is
undocumented in the template an author actually fills in. That is the mechanical
explanation for this feature's founding observation — the mechanism existed, did
most of what was wanted, and nobody used it. Documenting the new keys without
documenting the one they sit beside would repeat the mistake, so all three are in
scope here.

Grounding files:

- `specfuse/loop/data/templates/WU.template.md` — the canonical seed. Its
  `AUTHOR-SET FIELDS` comment block is where optional frontmatter fields are
  described; match its existing voice and entry shape exactly.
- `specfuse/loop/data/verification.yml.example` — the canonical seed config.
- `.specfuse/skills/verification/SKILL.md` — T03 already documented the
  `prep`/`oracles`/`extra_gates` distinction here. **Do not restate it**; the seed
  entries should be short and point at the skill for the full contract.
- `scripts/sync-scaffold.sh` — propagates canonical seeds to the vendored
  `.specfuse/` copies. The vendored copies are outputs of this script, never
  hand-edited.

Binding rules apply by reference: `.specfuse/rules/result-contract.md`,
`.specfuse/rules/never-touch.md`, `.specfuse/rules/security-boundaries.md`,
`.specfuse/rules/correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_seed_documents_prerun_keys.py::TestSeeds::test_wu_template_documents_prerun_keys`
   exists and **fails on HEAD before this work unit runs** — the file does not yet
   exist, which counts as red. Scoped run:
   `python3 -m unittest tests.test_seed_documents_prerun_keys.TestSeeds.test_wu_template_documents_prerun_keys`.
2. `specfuse/loop/data/templates/WU.template.md` documents `prep`, `oracles`, and
   `extra_gates` in its `AUTHOR-SET FIELDS` block — each naming that it resolves
   against a `verification.yml` set name, and each saying **when** it runs:
   `prep` and `oracles` before dispatch, `extra_gates` at exit.
3. `specfuse/loop/data/verification.yml.example` carries a commented `oracles:`
   set with at least one worked example and a one-line note that entries are
   informational captures rather than pass/fail gates.
4. The test in criterion 1 asserts all three key names appear in the canonical
   template and that `^oracles:` (commented or live) appears in the canonical
   example — falsifiable in both directions, so deleting an entry fails it.
5. `bash scripts/sync-scaffold.sh` has been run, and the vendored copies under
   `.specfuse/` match the canonical seeds.
6. The test in criterion 1 passes after the edits.

**Do not touch.**

- Any production code under `specfuse/loop/*.py`. This unit edits seed data and
  adds one test; it changes no behaviour.
- `.specfuse/skills/verification/SKILL.md` — T03's, already landed and verified
  byte-identical across both shipped copies. Point at it, do not rewrite it.
- `.specfuse/verification.yml` — this repo's live config, T03's. Only the
  `.example` seed is in scope.
- The vendored `.specfuse/templates/` and `.specfuse/verification.yml.example`
  copies **as hand edits** — they must change only as output of
  `scripts/sync-scaffold.sh` per criterion 5.
- Other features' folders, generated directories, secrets, `.git/`. See
  `.specfuse/rules/never-touch.md`.
- **The driver owns all git.** You edit files only — never run `git`.

**Verification.**

- The `code` gate set in `.specfuse/verification.yml`.
- The scoped red→green run named in criteria 1 and 6.
- Confirm sync left no drift: the canonical and vendored copies agree.

**Escalation triggers.**

- If `scripts/sync-scaffold.sh` fails or rewrites files beyond the two seeds, emit
  `status: blocked` with its output rather than hand-editing the vendored copies
  to match.
- If the template's `AUTHOR-SET FIELDS` block has no natural place for a field
  that is read by the driver but not written by an author, block and say so — the
  block's structure is a contract with its readers, not something to improvise
  around.
- Blocked is a respectable outcome (`.specfuse/rules/result-contract.md` rule 4).
