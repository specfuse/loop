---
id: FEAT-2026-0005/T01
type: implementation
model: claude-sonnet-4-6
status: pending
attempts: 0
---

# Add a `close` WU type that collapses the closing sequence (single-gate only)

**Objective.** Introduce a single `close` work-unit type that performs all four
closing ceremonies (retrospective + lessons + docs + terminal verdict) in one
session, accepted by the linter and driver **only for single-gate features**, so
trivial features stop paying four dispatches (incl. an Opus plan-next) to close.

**Context.** This is `FEAT-2026-0005/T01`. Today every gate must end with the
ordered sequence `retrospective → lessons → docs → plan-next` — `lint_plan.py`
enforces it (`CLOSING_SEQUENCE`) and `loop.py` runs each as a separate dispatch.
On a one-substantive-WU feature that is four sessions for a tiny change, and the
terminal `plan-next` is boilerplate (no next gate to forward-design). The two
ceremonies that carry real cross-feature value — `lessons` (the `LEARNINGS.md`
pump) and `docs` (roadmap/doc reconciliation) — must be **preserved**, folded
into the one `close` WU, not dropped. The collapse is **single-gate-only**:
multi-gate features keep the four-WU sequence, where forward-design `plan-next`
earns its cost. Reference the binding rules under `.specfuse/rules/`; honor
`result-contract.md`, `never-touch.md`. The driver owns all git.

Grounding files: `.specfuse/scripts/lint_plan.py` (`VALID_TYPES`,
`CLOSING_SEQUENCE`, the per-gate closing check in `lint()`),
`.specfuse/scripts/loop.py` (`GATES_FOR_TYPE`, the closing dispatch in `run()`),
`.specfuse/templates/WU.template.md`, and `docs/methodology.md` §3/§6.

**Acceptance criteria.**
1. `lint_plan.py` admits `close` as a valid WU type (`VALID_TYPES`).
2. A gate's closing is valid when it is **either** the existing
   `[retrospective, lessons, docs, plan-next]` sequence **or** a single `close`
   WU as the gate's only closing-type unit.
3. A single `close` WU is **rejected** unless the feature's graph has exactly one
   gate. A `close` WU appearing in any feature with two or more gates is a lint
   error naming the constraint. (Multi-gate features must use the four-WU
   sequence.)
4. `loop.py`'s `GATES_FOR_TYPE` maps `close` to a verification gate set, and the
   driver runs/commits a `close` WU like any other closing unit. Its verification
   runs `lint_plan.py` on the feature (structural validity preserved after the
   close).
5. `WU.template.md` documents the `close` type: what one session must produce
   (write `RETROSPECTIVE.md`; append durable `LEARNINGS.md` entries; reconcile
   docs + roadmap; write the terminal feature-arc verdict) and the
   single-gate-only constraint.
6. Tests in `tests/` assert: (a) lint accepts a single-gate feature whose gate
   closes with one `close` WU; (b) lint rejects a `close` WU in a two-gate
   feature; (c) lint still accepts a four-WU `[retrospective, lessons, docs,
   plan-next]` closing (regression).

**Do not touch.** The `Backend` seam / `make_backend`, the working-tree lock
helper, `gh_features.py`, `adopt_feature.py`, `gh_backend.py`, the verification
gate *commands* in `verification.yml` (you MAY add a `close` gate-set mapping in
`loop.py`'s `GATES_FOR_TYPE`, but do not weaken existing gate commands), any
binding rule under `.specfuse/rules/`, secrets, `.git/`. The driver owns git —
edit files only. Files this WU changes: `.specfuse/scripts/lint_plan.py`,
`.specfuse/scripts/loop.py`, `.specfuse/templates/WU.template.md`, and a test
file under `tests/`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (tests,
ruff, bandit, coverage ≥ floor). Run them in order.

**Escalation triggers.** If collapsing into one `close` would erase the
multi-gate `plan-next`'s forward-design role (i.e. the change can't be cleanly
restricted to single-gate features), stop and emit `status: blocked` — the
collapse must be single-gate-only by construction. If mapping `close` in
`GATES_FOR_TYPE` would require a new gate set in `verification.yml` that does not
exist, prefer reusing the `plannext` set and note it; only block if neither
existing set fits.
</content>
