---
id: FEAT-2026-0079/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.50
produces:
  - plugins/specfuse/skills/roadmap-archive/SKILL.md
  - .specfuse/skills/roadmap-archive/SKILL.md
  - tests/test_roadmap_archive_skill_delegates.py
---

# T02 — The skill invokes the archiver instead of restating it

## Context

`/roadmap-archive`'s Steps 2–5 describe the archiving mechanics in prose. Grepping the
current skill for `Status:`, `reconcil`, `inbound`, or `outbound` returns **nothing** —
the prose predates #1169 and says nothing about the reconciliation the driver now performs.
An operator following it reproduces the pre-fix behaviour.

This unit replaces those mechanics with a call to T01's CLI. The split is deliberate and is
the whole design of this feature:

- **Stays in the skill** — Step 1's row validation, `--auto`'s selection of which features to
  archive, and the confirmation prompt. That is human-facing judgement.
- **Moves to the driver** — everything that edits a file. The skill runs the command once per
  feature and reports what it returned.

Canonical source is `plugins/specfuse/skills/roadmap-archive/SKILL.md`. `.specfuse/skills/`
is vendored **from** it by `scripts/sync-scaffold.sh`, and `.claude/skills/roadmap-archive`
is a symlink to the vendored copy. Edit the canonical file, then run the sync — do not hand-
edit the vendored copy, and do not edit through the symlink.

The guard in acceptance 3 is the honest limit of what can be verified here. It cannot prove
an agent following the prose produces the right result — that would need an end-to-end
oracle composing prose and code, which does not exist. It *can* prove the prose no longer
describes mechanics, which is what stops the third copy growing back one paragraph at a
time. `[FEAT-2026-0069/G2-CLOSE]` is explicit that the difference between those two claims
must be named rather than blurred; the close WU records it as a deferred verification.

## Acceptance criteria

1. `tests/test_roadmap_archive_skill_delegates.py::test_skill_invokes_the_cli` fails on HEAD
   before this unit runs and passes after: the skill body contains the literal invocation
   (`python3 -m specfuse.loop.roadmap_archive` or the `.specfuse/scripts/` shim path).
2. The skill's Steps 2–5 no longer describe file-editing mechanics: no instruction to move a
   section, rewrite a `Detail` cell, append to the archive, or delete the inline section by
   hand. Steps 1 and 6 and the `--auto` selection/confirmation prose are retained.
3. `test_skill_carries_no_mechanics_prose` asserts the skill body does not reintroduce the
   restatement — keyed on the file-editing verbs above rather than on a keyword allowlist, so
   a paraphrase does not slip through.
4. One sentence may point at the driver as the owner (e.g. "the archiver reconciles
   cross-references and the status marker; see `auto_archive_feature`"). A sentence naming the
   owner is permitted; a paragraph restating the rules is not, and acceptance 3 is the line.
5. The skill branches on T01's three outcomes — `archived`, `already archived`,
   `refused: <reason>` — and surfaces `refused` to the operator with its reason rather than
   reporting success.
6. `plugins/…/SKILL.md` and `.specfuse/skills/…/SKILL.md` are byte-identical after
   `scripts/sync-scaffold.sh`, verified by `bats tests/sync_scaffold.bats`.

## Verification

- `python3 -m unittest discover -s tests -v -b`
- `bats tests/sync_scaffold.bats`
- `ruff check specfuse .specfuse/scripts tests scripts`
- `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90`
- `python3 .specfuse/scripts/roadmap_link_gate.py`

## Escalation triggers

Stop and escalate rather than guessing:

- The mechanics-prose guard cannot be written without a keyword allowlist that a paraphrase
  would defeat. A guard that only catches the exact current wording is worse than none — it
  reads as protection while permitting the drift.
- Removing the mechanics leaves a step whose remaining instruction is genuinely ambiguous to
  a human operator. Reintroducing prose to fix that reverses this feature's decision; the
  operator makes that call.
- `scripts/sync-scaffold.sh` does not reproduce the canonical file byte-for-byte.

## Do not touch

- `specfuse/loop/roadmap_archive.py` and the shim — T01's surface, consumed here as-is.
- The archiving algorithm itself — behaviour is held constant by this feature.
- The `.claude/skills/roadmap-archive` symlink — editing through it writes the vendored copy
  directly. The vendored file IS a declared deliverable of this unit, but only as output of
  `scripts/sync-scaffold.sh`; it is never hand-edited.
- Any other skill under `plugins/specfuse/skills/`.
