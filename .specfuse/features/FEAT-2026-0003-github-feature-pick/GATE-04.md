---
gate: 4
status: draft
---

# Gate 4 — Adopted-folder lint admits orchestrator issue bodies

## Definition of done

<Drafted by `FEAT-2026-0003/G3-PLAN` as terminal-case branch B. The
milestone: `lint_plan.py`'s section detector accepts both bold-preamble
(`**Context.**`) and Markdown ATX (`## Context`) headings, so an
orchestrator issue body embedded verbatim by `adopt_feature.py` lints
clean. The existing adopted folder
`.specfuse/features/INIT-2026-0001-F06-conform-publishroster-to-validated-spec/`
(written by gate 3's T07 smoke against `RestoManagerApp/Backend#287`)
is the offline re-verification target — `lint_plan.py` over that folder
must exit 0 with the gate-4 fix applied.

Gate 4 closes the fourth mechanism of the feature's `roadmap_goal`
("grind through its gate cycle"). It is intentionally narrow: one
linter change + tests + re-lint of the existing adopted folder. A
second live `gh` mutation of #287 is OPTIONAL belt-and-braces and is
NOT a definition-of-done item — the cross-repo `state:*` label contract
is settled at gate 3.

Substantive WUs are NOT drafted here; gate 4's own `plan-next` (when
the gate is armed) authors them. The recommended shape — informed by
the feature-arc retrospective and the smoke journal — is:

- **T08 = widen `lint_plan.py` section detector** to accept the union
  pattern (`^(#+\s*|\**)<section>`), with the two-case linter test
  pattern from `[FEAT-2026-0003/G2-LESSONS]` (exits 0 on a fixture
  carrying ATX headings; exits non-zero on a fixture genuinely missing
  sections). Probably 2 files.
- **T09 = re-verify the adopted INIT-2026-0001-F06-… folder lints
  clean** with the gate-4 patch applied. Offline; no `gh` calls. The
  evidence artifact is the lint exit code + a one-paragraph note in
  `SMOKE-INIT-2026-0001-F06.md` confirming the gate-3 finding is
  resolved.

Gate 4's plan-next must also resolve the open question carried over
from `[FEAT-2026-0003/G3-LESSONS/multi-gate]`: verify the
ATX-headings assumption against the orchestrator's issue-body template
(`RestoManagerApp/orchestrator/`) before locking the linter regex. If
the orchestrator template emits ONLY ATX, the union pattern is still
correct (accepts both) but the "accept both" framing should be
re-examined.>

## Reflection notes

<Written by the human at gate 4 review time.>
</content>
