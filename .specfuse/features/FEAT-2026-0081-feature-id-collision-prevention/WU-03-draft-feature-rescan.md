---
id: FEAT-2026-0081/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
oracle_env: macos_local
produces_driver_helper: confirm_feature_id_still_free
produces:
  - specfuse/loop/feature_ids.py
  - tests/test_feature_ids_confirm.py
  - .specfuse/skills/draft-feature/SKILL.md
model: sonnet
effort: medium
---

# Re-check the ID immediately before the folder is written, not only when it is proposed

**Objective.** Narrow the collision race window: add
`confirm_feature_id_still_free()` and have `/draft-feature` call it immediately
before it writes a feature folder, so an ID claimed between the step-1 proposal
and the write is caught rather than collided with.

**Context.** Third WU of FEAT-2026-0081; read `PLAN.md` in this folder first.
Depends on T01, which ships `next_feature_id()` and `scan_claimed_ids()` in
`specfuse/loop/feature_ids.py` — this WU adds the confirm entry point beside them
and wires the skill to call it.

**The window this closes, stated precisely.** Two features were drafted three
minutes apart in different worktrees and both took the same ID. The colliding PR
was created *after* the first draft's scan ran, so no query shape at step 1 could
have caught it. Re-running the scan at write time does not make the window zero —
it shrinks it from "however long the drafting interview takes" to "the moment
between the check and the write". Say that honestly in the skill prose; a claim
that this eliminates collisions would be false, and T02's lint is the backstop
precisely because it does not.

**A skill-prose edit alone is not this WU's deliverable.** The prose says what an
agent should do; the function is what makes it checkable. Both, or the unit is a
hollow pass — this is why the WU produces a test module and not only a `.md`.

`.specfuse/skills/draft-feature/SKILL.md` step 6 ("Write only on accept") is the
call site. Its step 1 already specifies the four-source scan by reference to
`roadmap-add`'s prose; leave step 1's semantics alone and add the second check at
step 6.

Binding rules in `.specfuse/rules/` apply. Do not restate them.

**Acceptance criteria.**

- `tests/test_feature_ids_confirm.py::test_id_claimed_since_the_proposal_is_refused`
  exists and **fails on HEAD before this WU's edits** (the module does not yet
  exist). Given a first scan where `FEAT-2026-0043` is free and a second scan
  where it is claimed, `confirm_feature_id_still_free` reports it as taken.
- After this WU's edits that same test passes, and so does
  `tests/test_feature_ids_confirm.py::test_unchanged_id_confirms_clean` — an ID
  still free at the second call confirms without complaint, so the common path is
  a no-op.
- `confirm_feature_id_still_free` returns **which source** newly claims the ID,
  not merely a boolean. A test asserts the source name is present. An operator
  told "that ID is taken" with no pointer cannot act; T01's `scan_claimed_ids`
  already returns per-source detail, so this is a pass-through, not new work.
- The function is importable: `python3 -c "from specfuse.loop.feature_ids import
  confirm_feature_id_still_free"` exits 0.
- The GitHub reader is injected here too, exactly as in T01, and every test above
  runs with no network. A test asserts an unreachable GitHub degrades to a
  warning and does **not** block the write — a network blip must not stop a
  drafting session; T02's lint catches what the degraded scan misses.
- `.specfuse/skills/draft-feature/SKILL.md` step 6 instructs the re-check before
  the folder write, names the function, and states plainly that this narrows the
  window rather than closing it. A grep confirms the instruction is present in
  the shipped skill file.
- The skill's canonical copy is updated in the right direction. This repo keeps
  skills canonical under `plugins/` and syncs them into `.specfuse/`; run
  `scripts/sync-scaffold.sh` (or the repo's documented equivalent) and confirm
  both copies match rather than editing one and leaving the other behind. State
  in your RESULT which copy you edited and which the sync propagated.
- Every new `subprocess.run` (if any) declares `check=` explicitly (`PLW1510`).

**Do not touch.** `next_feature_id` and `scan_claimed_ids`' semantics (T01 owns
them — call them, do not edit them); `specfuse/loop/lint_roadmap.py` (T02);
`.specfuse/skills/roadmap-add/SKILL.md`'s *Computing the next ID* prose, which is
T01's specification and must keep saying what it says; the umbrella CLI.
`.git/`, secrets. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
symbol-import check and the skill-copy sync check above. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if `/draft-feature`'s step 6 has
been restructured by FEAT-2026-0082 in a way that makes the call site ambiguous —
`agent-policy.yml:47` records 0081 as queued behind 0082 because both touch this
skill, and guessing where the call goes in a rewritten step is how a wiring race
gets introduced rather than fixed. Also block if the canonical-copy direction for
skills is unclear in this repo: editing the wrong copy means the sync silently
reverts your work. If `confirm_feature_id_still_free` is absent from the files
you edited, emit `status: blocked` — do not claim complete. Blocked is
respectable (`result-contract.md` rule 4).
