---
id: FEAT-2026-0081/G2-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
auto_close_disabled: true
model: opus
effort: high
produces:
  - .specfuse/features/FEAT-2026-0081-feature-id-collision-prevention/RETROSPECTIVE.md
  - .specfuse/LEARNINGS-pending.md
---

# Gate 2 close — renumbering as a command (placeholder)

**Placeholder, pre-declared at draft time.** This file exists so the linter reads
the last gate as non-empty and therefore terminal — without it, gate 1 is
misidentified as the terminal gate and its `close-intermediate` → `plan-next`
sequence is rejected. `FEAT-2026-0081/G1-PLAN` drafts gate 2's substantive work
units above this entry, sets this unit's real `depends_on`, and replaces the
criteria below with ones that name what gate 2 actually shipped. Status stays
`draft` until a human arms the gate.

**Objective.** Terminal close of FEAT-2026-0081: re-run the oracles fresh, record
retrospective + lessons + docs + terminal verdict in one session, and confirm the
renumbering command genuinely rewrites every ID-bearing surface and genuinely
leaves the two that must keep the old ID alone.

**Context.** Terminal close. Depends on gate 2's substantive units, which
`G1-PLAN` drafts. Binding rules in `.specfuse/rules/` (`result-contract.md`,
`close-discipline.md`) apply. The driver owns the terminal `PLAN.md status ->
done` flip — do **not** add a status-flip acceptance criterion.

> Run `specfuse lint --closing` and confirm it exits 0 before this WU reports
> `complete` — see `.specfuse/rules/close-discipline.md` §4.

**Acceptance criteria** (to be rewritten by `G1-PLAN` against what gate 2 ships;
these three are load-bearing and must survive that rewrite in some form).

- **A real renumbering, run fresh in this session against a fixture feature** —
  not inherited from a unit test. Every ID-bearing surface is rewritten, and the
  result passes `python3 -m specfuse.loop.lint_plan` and
  `python3 .specfuse/scripts/roadmap_link_gate.py`. Gate 1's own collision check
  is the oracle here: a renumbering that misses a file is exactly the divergence
  that check was built to catch, so a clean lint after a renumber is meaningful
  evidence rather than a tautology.
- **The keep-the-old-ID rule, asserted mechanically.** After the renumbering,
  the fixture's `events.jsonl` and `PLAN.baseline.json` still carry the **old**
  correlation ID, and the retrospective note explaining that to a future reader
  is present. A close that cannot show this has not verified the one rule this
  feature wrote down in advance precisely because it is easy to reason away.
- **Consumer-visible contract changes** (§3): enumerate them and block on human
  acknowledgment rather than writing `n/a`. Expect at minimum a new console
  script in `[project.scripts]` and the cross-repo follow-up for the umbrella's
  `DELEGATED_COMMANDS` entry, which this repo cannot land and which must
  therefore be filed rather than silently deferred.
- A `## Cost analysis` section in `RETROSPECTIVE.md` reconciling the feature's
  `planned_cost_usd` against actual spend from `events.jsonl`, delta named.
  `assert_cost_analysis_section_when_met` requires this heading on a `met`
  verdict and checks **after** dispatch, so omitting it costs a full re-attempt.
- A `## Gate 2` heading in `RETROSPECTIVE.md`, for the same reason gate 1's close
  needs `## Gate 1` — `assert_retrospective_gate_section` checks it after
  dispatch.
- Lessons stage to `.specfuse/LEARNINGS-pending.md`, **not** `LEARNINGS.md`:
  this feature is `autonomy_default: auto`, where
  `assert_learnings_staged_under_auto` refuses the direct write.

**Do not touch.** Source and test files (gate 2's substantive units own those);
gate 1's record; `.git/`, secrets. This WU writes only its close record. The
driver owns git and the terminal PLAN flip. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext`/close gates plus a fresh re-run of the oracles
gate 2's criteria name. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if the fresh renumbering proof
disagrees with gate 2's unit tests, or if a renumbered fixture lints clean while
a manual inspection finds a surface the command missed — a bulk mutator that
silently half-rewrites is worse than the hand sweep it replaces, and that is the
failure this whole feature exists to prevent. Blocked is respectable
(`result-contract.md` rule 4).
