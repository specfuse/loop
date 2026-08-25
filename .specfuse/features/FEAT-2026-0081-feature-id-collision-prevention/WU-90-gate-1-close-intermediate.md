---
id: FEAT-2026-0081/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: pending
attempts: 0
planned_cost_usd: 4.50
oracle_env: macos_local
auto_close_disabled: true
model: opus
effort: high
produces:
  - .specfuse/features/FEAT-2026-0081-feature-id-collision-prevention/RETROSPECTIVE.md
  - .specfuse/LEARNINGS-pending.md
---

# Gate 1 close — collision prevention

**Objective.** Non-terminal close: re-run the oracles fresh, fold retrospective +
lessons + docs into one record, and answer whether the prevention half actually
prevents anything — not whether the tests are shaped like it does.

**Context.** Close of gate 1 of FEAT-2026-0081. Depends on T01 (the extracted
four-source scan), T02 (the ID→slug ERROR), T03 (the write-time re-check).
`G1-PLAN` runs after this and drafts gate 2 from what this record says. Binding
rules in `.specfuse/rules/` (`result-contract.md`, `close-discipline.md`) apply.
This is **not** the terminal gate — do not write a terminal verdict and do not
flip `PLAN.md status`.

> Run `specfuse lint --closing` and confirm it exits 0 before this WU reports
> `complete` — see `.specfuse/rules/close-discipline.md` §4.

**Acceptance criteria.**

- `RETROSPECTIVE.md` carries a `## Gate 1` heading — the driver's
  `assert_retrospective_gate_section` guard requires it and checks **after**
  dispatch, so omitting it costs a full re-attempt.
- A `## Retrospective` section answering, from evidence rather than from the
  plan: whether T02's probe re-run agreed with PLAN.md's draft-time numbers (78
  rows, 68 IDs, zero divergence) or found the tree had moved; whether extracting
  the scan changed what it produces for this repo, which T01 was forbidden to do;
  and whether `autonomy_default: auto` let any gate boundary pass without a human
  where one would have helped. Plus `## What I'd change`.
- A `## Lessons` section with any durable rule worth promoting. **This feature
  is `autonomy_default: auto`, so lessons stage to `.specfuse/LEARNINGS-pending.md`
  — writing `.specfuse/LEARNINGS.md` directly is refused by
  `assert_learnings_staged_under_auto` after dispatch.** In particular whether "prose that instructs an agent
  is not a mechanism until something can check it" is worth stating generally,
  since that is the reasoning that turned this feature's line 1 from a skill edit
  into a function.
- A `## Docs` note: whether `roadmap-add/SKILL.md` should now point at
  `next_feature_id()` as the definition rather than re-describing the scan, or
  name the doc touched. A prose spec and a shipped function that disagree is the
  exact drift this gate exists to remove.
- A `## Cost analysis` section reconciling `planned_cost_usd` (PLAN's $24.00 and
  the per-WU estimates) against actual spend read from `events.jsonl`, delta
  named. If the delta does not blend across WU types, say so rather than
  reporting one average.
- A `## What the loop did NOT verify` section enumerating every deferred
  criterion with why and where it actually gets checked; required even when empty
  — write `(nothing — every acceptance criterion was verified in-loop)`. Expect
  at least one entry: the race window's narrowing is proven by two concurrent
  drafting sessions in different worktrees, which cannot happen inside one loop.
- **Oracles re-run fresh** (close-discipline §1), read directly and never from a
  producing WU's self-report: `python3 -m unittest discover -s tests -q` reports
  `OK`; `python3 -c "from specfuse.loop.feature_ids import next_feature_id,
  scan_claimed_ids, confirm_feature_id_still_free"` exits 0; `python3 -c "from
  specfuse.loop.lint_roadmap import _check_id_slug_binding"` exits 0;
  `python3 .specfuse/scripts/roadmap_link_gate.py` exits 0; the full `code` gate
  set passes.
- **Collision proof, run fresh in this session and not inherited from a unit
  test:** against a temp fixture tree, an ID claimed by two different slugs
  produces an ERROR from `lint_roadmap`, and the same tree with the divergence
  repaired produces none. Quote both finding messages verbatim — the message is
  what an operator acts on, and a human should read it once before this ships.
- **Window-narrowing proof:** `confirm_feature_id_still_free` refuses an ID that
  became claimed between two scans, driven through injected sources with no
  network. State plainly in the record that this narrows rather than closes the
  window, and that T02's lint is the backstop.
- **Consumer-visible contract changes** (§3): enumerate them and block on human
  acknowledgment rather than writing `n/a`. Expect at least a new module
  (`specfuse/loop/feature_ids.py`), a new console script (`specfuse-next-id`) in
  `[project.scripts]`, a new ERROR class in a gate every feature in this repo
  runs, and a changed `/draft-feature` contract. The ERROR row carries the real
  risk and deserves its own line: it reds `roadmap-link-gate` repo-wide, not just
  for this feature.
- On a hedged outcome, record the follow-up per close-discipline §2 with a
  `kind:` per unmet criterion.

**Do not touch.** Source and test files (T01–T03 own those); gate 2's WUs
(`G1-PLAN` drafts them next, and drafting them here would pre-empt the unit whose
whole job that is); `.git/`, secrets. This WU writes only its close record. The
driver owns git. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext`/close gates plus a fresh re-run of the oracles
above. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if the fresh collision proof
disagrees with T02's unit tests — a check that passes its own tests but does not
fire on a real divergent tree is the hollow pass this criterion exists to catch,
and this feature's entire value is that the check fires. Also block if T01's
extraction turns out to have changed what the scan produces for this repo: that
is a silent behavior change inside a refactor, and a human must weigh it rather
than have it absorbed into a close. Blocked is respectable
(`result-contract.md` rule 4).
