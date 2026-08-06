---
id: FEAT-2026-0056/T07
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
oracle_env: macos_local
model: sonnet
effort: medium
produces_driver_helper:
  - specfuse.loop.criteria_state.build_reverification_worklist
produces:
  - tests/test_criteria_worklist.py
generated_surfaces: []
---

# Partition recorded criterion state into a re-verification worklist

**Objective.** Add `build_reverification_worklist` to
`specfuse/loop/criteria_state.py`: a pure function that partitions a gate's recorded
criterion entries into what a re-dispatched close may carry forward and what it must
re-verify, grouping identical oracle commands so each runs once per attempt.

**Context.** This is `FEAT-2026-0056/T07`, gate 2 — the unit that turns recorded
state into a decision. Read `PLAN.md` § *Scope decision: what invalidates a cached
green*, `GATE-02.md`, and `.specfuse/rules/close-discipline.md` §5 before editing.

Gate 1 made per-criterion state *recorded* and *linted*. Nothing reads it. This unit
is the reader, and it is deliberately **pure**: entries in, partition out, no file
I/O, no subprocess, no driver state. T08 does the wiring. Same schema-then-consumer
cut the feature's two gates already use.

**The invalidation rule, from `PLAN.md` and not open here.** Invalidation is by
oracle **kind**, not by diff intersection. A `narrow` oracle has a knowable scope —
a scoped test nodeid, a symbol-existence import, a structural assert, a countable
grep — so its green survives a re-close. A `broad` oracle — the full test suite, a
full regeneration, a scenario matrix — does not, and **re-runs unconditionally on
every close attempt**. `PLAN.md` rejected path-intersection invalidation and
diff-derived test selection with reasons; this unit implements the decision, it does
not revisit it.

**Fail-safe default.** An entry is carried forward only when it is *provably* safe:
`kind == "narrow"` **and** `state == "pass"` **and** `oracle` is not `None` **and**
`attempt` is not `None`. Everything else goes to the re-verify list — a missing
`kind`, an unrecognized `kind`, `state: fail`, `state: unverified`, a criterion that
first appeared this attempt, and every `broad` entry regardless of its state. A
`broad` entry is never compared against the current attempt here: the worklist is
built at the *start* of an attempt, so any recorded `broad` green necessarily
belongs to a prior one.

**Existing mechanism (`planning-discipline.md` §1).** `grep -rniE 'worklist' specfuse
--include='*.py'` returns one hit: `build_autoclose_debt_enumeration`
(`specfuse/loop/loop.py:4028`), "the deferred-verification worklist for an auto-closed
gate". It is a different worklist — it enumerates criteria a gate *never verified*
because it auto-closed, and it reads nothing recorded. Not reused. What the two do
share is `extract_wu_criteria`, already hoisted by T02, so the "what are this gate's
acceptance criteria" parser stays single-sourced.
`grep -rniE 'carry_forward|carried[- ]forward|reverif' specfuse --include='*.py'`
returns one hit, a docstring in `lint_closing.py`. No existing mechanism; building
new.

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_criteria_worklist.py::test_broad_pass_never_carries_forward` exists
   and **fails on HEAD before this WU's edits**. Record the failing output in the
   RESULT block before editing production code.
2. `specfuse/loop/criteria_state.py` exports `build_reverification_worklist(entries,
   current_attempt)` returning a frozen dataclass with three fields: `carry_forward`
   (list of `CriterionStateEntry`), `reverify` (list of `CriterionStateEntry`), and
   `oracle_groups` (list of `(oracle_command, [criterion_id, ...])` pairs).
3. The function is pure: `grep -n 'open(\|Path(\|subprocess\|os\.' ` over the
   function's own body returns no match. Paste the grep.
4. An entry with `kind: narrow`, `state: pass`, a non-empty `oracle:`, and a
   non-empty `attempt:` lands in `carry_forward`.
5. An entry with `kind: broad` and `state: pass` lands in `reverify` — asserted for
   an `attempt:` equal to `current_attempt` as well as one below it. This is the
   soundness contract; a partition that carries a `broad` green forward fails this
   WU.
6. An entry with `kind: narrow` and `state: fail` lands in `reverify`.
7. An entry with `state: unverified` lands in `reverify`, whatever its `kind`.
8. An entry whose `kind` is absent, and one whose `kind` is not in `ORACLE_KINDS`,
   both land in `reverify` — the fail-safe default, asserted without raising.
9. `carry_forward` and `reverify` partition the input exactly:
   `len(carry_forward) + len(reverify) == len(entries)`, no `criterion_id` appears in
   both, and each list preserves the input's document order.
10. Two `reverify` entries whose `oracle:` strings are byte-identical produce **one**
    `oracle_groups` pair naming both `criterion_id`s, in document order. An entry
    with no `oracle:` contributes no `oracle_groups` pair and still appears in
    `reverify`.
11. `python3 -c "from specfuse.loop.criteria_state import build_reverification_worklist"`
    exits 0.
12. The test named in criterion 1 **passes** after this WU's edits.

**Do not touch.** `parse_criteria_state`, `render_criteria_state`, `criterion_id_for`,
`ORACLE_KINDS`, and `CRITERION_STATES` in `specfuse/loop/criteria_state.py` — T01's,
and their signatures and values are contract. `criteria_filename` /
`CRITERIA_FILENAME_RE` in the same module (T05's scope — import them if you need
them, do not redefine). `specfuse/loop/loop.py` — T08 owns every driver call site for
this function, and a call site added here would be dead code the gate's own units
disagree about. `specfuse/loop/lint_closing.py` (T06's scope).
`specfuse/loop/closing_requirements.py`. `.specfuse/verification.yml`.
`.specfuse/rules/` and `.specfuse/templates/`. `GATE-01.md` and gate 1's work units.
Any other feature's folder under `.specfuse/features/`. Generated directories,
secrets, `.git/`. The driver owns all git operations — you edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`
(`python3 -m unittest discover -s tests -v -b`), `lint`, `security`, `coverage`
(`--fail-under=90`), `leak-scan`, `event-type-gate`. In addition run criterion 11's
symbol-existence check verbatim and criterion 3's purity grep, pasting both outputs.
Criterion 1's red observation must be recorded before production edits.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
delivering criterion 5 would require a `broad` entry to be carried forward under any
condition — that weakens the contract `PLAN.md` calls the reason the feature is
sound, and is a design change an operator makes, not this WU; the partition in
criterion 9 cannot hold because an entry is classifiable into neither list, meaning
the rule has a gap the WU body does not cover; `build_reverification_worklist` is
absent from the files you edited or criterion 11's import fails — do not claim
complete; or satisfying criterion 3's purity would require reading the artifact from
disk inside this function, which is T08's job and not this one's.
