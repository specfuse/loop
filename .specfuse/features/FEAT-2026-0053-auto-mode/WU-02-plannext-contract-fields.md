---
id: FEAT-2026-0053/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces:
  - tests/test_lint_plan_contract_fields.py
produces_driver_helper:
  - lint_plan_next_draft
---

# Machine-readable plan-next contract fields, warn-only lint

**Objective.** Teach the plan-next output contract three veto-only fields —
`open_questions`, `human_only`, `provenance` — documented in the templates and
covered by warn-only lint.

**Context.** Correlation ID `FEAT-2026-0053/T02`. The arm predicate (T03) reads
three model-authored signals, all of which may only *subtract* autonomy:

- `open_questions:` — a **required explicit list** in the `GATE-{N+1}-REVIEW.md`
  frontmatter. An empty list (`open_questions: []`) means "nothing requires an
  answer before execution." A **missing field is not an empty list** — under
  `auto` (gate 2) it parks the feature. Fail closed.
- `human_only: true` — optional per-WU frontmatter self-flag on a draft the
  planner knows needs a human (it just wrote a defaults flip).
- `provenance:` — optional per-WU frontmatter string citing the retrospective
  item or `events.jsonl` failure event that motivated an **added** WU (one not
  in the plan baseline). The predicate, not lint, decides "added" — lint cannot
  see the baseline at draft time and must not try.

**Decoupling rule, binding:** the review file's doubt prose ("if you check only
three things...") stays mandatory and is NEVER coupled to these fields by lint.
One field both unblocking the model and feeding the human summary teaches the
model that hedging is expensive. The lint checks field *presence and shape*
only.

Two mechanical constraints discovered at drafting: the review-file naming
contract lives in `.specfuse/rules/close-discipline.md` §4 (`GATE-{N+1}-REVIEW.md`,
named for the gate being armed) — verify the exact strings there before locking
any check (authoring §8); and templates are duplicated (`.specfuse/templates/`
working copies, `specfuse/loop/data/templates/` canonical scaffold copies) with
`tests/test_scaffold_data_in_sync.py` as drift guard — **edit both copies of
`WU.template.md` or the `tests` gate fails**.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_lint_plan_contract_fields.py::TestContractFields::test_review_missing_open_questions_warns`
   exists and **fails on HEAD before this WU runs** (file does not yet exist —
   red).
2. `lint_plan_next_draft` WARNs when the review file for a just-closed gate
   lacks an `open_questions:` field, and is silent when the field is present —
   including present-and-empty.
3. `human_only: true` and `provenance:` in WU frontmatter produce no lint
   warning or error (valid, recognized fields).
4. Both copies of `WU.template.md` (`.specfuse/templates/` and
   `specfuse/loop/data/templates/`) document the three fields in the
   frontmatter notes as veto-only autonomy signals, and
   `tests/test_scaffold_data_in_sync.py` still passes.
5. The full existing lint test suite passes unchanged — every new check is
   WARN-only; nothing blocks in this gate.
6. `tests/test_lint_plan_contract_fields.py::TestContractFields::test_review_missing_open_questions_warns`
   **passes after this WU's edits**.

**Do not touch.** `specfuse/loop/arm_eval.py` (T03's file — does not exist yet;
do not create it). `specfuse/loop/plan_baseline.py` (T01's). The blocking/ERROR
path of `lint_plan.py` — this unit adds warns only. Generated directories,
secrets, `.git/`. The driver owns all git — edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` set in `.specfuse/verification.yml`. Scoped
iteration run: `python3 -m unittest tests.test_lint_plan_contract_fields -v`.
Sync guard: `python3 -m unittest tests.test_scaffold_data_in_sync -v`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`close-discipline.md` §4's review-file contract contradicts the frontmatter
placement this unit assumes (where the `open_questions` field lives is then an
operator decision, not yours); or the template sync mechanism turns out to
require more than editing the two copies (a generator, a build step) — that is
a different unit of work.
