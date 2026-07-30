---
id: FEAT-2026-0053/T09
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
provenance: "PLAN.md scope boundary — LEARNINGS staged to a pending file (gate 2, drafted by G1-PLAN). The post-pass invariant (AC#2) is added beyond that sketch because [FEAT-2026-0053/G1-CLOSE]'s own gate-1 lessons went straight to .specfuse/LEARNINGS.md under a human-reviewed gate; under auto nothing but a mechanical check stands between an unread gate and a durable cross-feature rule."
produces:
  - tests/test_learnings_staging.py
  - .specfuse/templates/LEARNINGS-pending.template.md
produces_driver_helper:
  - post-pass invariant refusing a closing WU that writes .specfuse/LEARNINGS.md under autonomy_default auto
oracle_env: macos_local
---

# LEARNINGS staging — an unread gate may not write a durable cross-feature rule

**Objective.** Under `autonomy_default: auto`, route a closing WU's promoted
lessons to a feature-local `LEARNINGS-pending.md` instead of
`.specfuse/LEARNINGS.md`, and enforce that routing mechanically.

**Context.** Correlation ID `FEAT-2026-0053/T09`. Depends on T06 (the dial
read). `.specfuse/LEARNINGS.md` is loaded into planning context for **every
future feature in this repo** — it is the most durable, widest-blast-radius
artifact a closing WU writes. Today a human reads the gate before those lessons
compound into anything; under `auto` nobody does, so a misframed gate's
generalisation would silently become a rule that shapes every subsequent plan.

`.specfuse/rules/planning-discipline.md` §5 already carries the cautionary case
in its own body: two earlier revisions of that section each generalised a floor
from a single feature and had to be replaced by a distribution. That correction
happened because humans read it. `auto` removes that reader, so the promotion
step moves to the one human read that remains — the PR.

**The staging contract.**

- Under `auto`, a `close` / `close-intermediate` WU appends its lessons to
  `LEARNINGS-pending.md` **in the feature directory**, not to
  `.specfuse/LEARNINGS.md`.
- `LEARNINGS-pending.md` opens with a header stating what it is and exactly how
  a human promotes it at PR review — the artifact must be self-describing, since
  its reader arrives at it from a PR diff with no other context.
- Under `review` and `supervised` nothing changes: lessons go straight to
  `.specfuse/LEARNINGS.md` as they do today. A human read the gate; that is the
  approval this staging substitutes for.
- Promotion itself stays a human action in this WU's scope. Automating it is
  not gate 2's work and must not be attempted here.

**Instruction is not enforcement.** Telling a closing session where to write is
necessary but not sufficient — the whole feature's organizing principle is that
model-authored output cannot be trusted to approve itself. So this WU also adds
a post-pass invariant for closing-type WUs: under `auto`, a closing WU whose
diff touches `.specfuse/LEARNINGS.md` does not pass. That check is the actual
deliverable; the template and the instruction are how a session succeeds at it.

Binding rules apply by reference: `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`.

**Flag-scope table** (`.specfuse/rules/planning-discipline.md` §3). The behavior
flag is `autonomy_default: auto`; the claim is *"under `auto`, lessons stage
instead of landing"*.

| Code path | Gated by flag? | Why |
|---|---|---|
| Closing-WU post-pass invariant on `.specfuse/LEARNINGS.md` | yes | only `auto` lacks the human gate read that authorises a durable rule |
| Closing-WU dispatch instruction naming the staging file | yes | a `review` feature must keep writing straight to `.specfuse/LEARNINGS.md` |
| `learnings-suggest` / `learnings-curate` skills | no | they read and propose; they never write durable rules unattended |
| `.specfuse/LEARNINGS.md` content and format | no | unchanged — staging changes the destination, not the entry shape |
| Implementation WUs | no | they do not promote lessons; only closing types do |
| Promotion at PR review | no | stays a human action in every mode |

**Acceptance criteria.**

1. `tests/test_learnings_staging.py::TestLearningsStaging::test_auto_closing_wu_writing_learnings_does_not_pass`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist — red).
2. Under `autonomy_default: auto`, a `close-intermediate` or `close` WU whose
   diff modifies `.specfuse/LEARNINGS.md` does not pass the post-pass
   invariants, and the refusal reason names the staging file.
3. Under `autonomy_default: review` and `supervised`, the identical diff passes
   — the invariant is inert outside `auto`.
4. Under `auto`, a closing WU whose diff modifies only
   `<feature-dir>/LEARNINGS-pending.md` passes.
5. `.specfuse/templates/LEARNINGS-pending.template.md` exists, and its header
   states what the file is and the exact promotion step a human takes at PR
   review.
6. Both scaffold copies of any edited template stay in sync —
   `python3 -m unittest tests.test_scaffold_data_in_sync -v` exits 0. (The
   canonical scaffold copies live under `specfuse/loop/data/templates/` and the
   working copies under `.specfuse/templates/`; editing one and not the other
   fails this gate.)
7. `tests/test_learnings_staging.py::TestLearningsStaging::test_auto_closing_wu_writing_learnings_does_not_pass`
   **passes after this WU's edits**, and `python3 -m unittest tests.test_learnings_staging -v`
   exits 0.

**Do not touch.** `.specfuse/LEARNINGS.md`'s existing content — this WU changes
where new entries land, never what is already there, and must not migrate,
reword, or reorder a single existing entry. The `learnings-suggest` and
`learnings-curate` skills. The arm transaction (T05), the arm branch (T06), the
severity flip (T07), `FEATURE-REVIEW.md` accumulation (T08). Promotion
automation — out of scope by decision, not by oversight. Generated directories,
secrets, `.git/`. The driver owns all git — you edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` set in `.specfuse/verification.yml`. Scoped
iteration runs: `python3 -m unittest tests.test_learnings_staging -v` and
`python3 -m unittest tests.test_scaffold_data_in_sync -v`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
the closing-WU post-pass invariant surface cannot express a check conditioned on
the feature's `autonomy_default` without restructuring how invariants are
registered (a restructure is a different unit — name the specific obstruction);
or if a closing WU has a legitimate reason to edit `.specfuse/LEARNINGS.md`
under `auto` that this WU's contract would wrongly refuse — that is a
plan-level contradiction, and `result-contract.md`'s closing obligation 2 says
block rather than write the finding into a gate document.
