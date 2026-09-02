---
name: authoring-work-units
description: "How to write a single Specfuse work unit that won't block spuriously or pass hollowly. Reference for humans authoring WUs in the loop, and for reviewing PM-agent drafts in the orchestrator. Thirteen numbered rules, five written in full (§2 criteria scope, §6 sizing, §9 hollow-pass pre-flight, §12 red-test-first, §13 produces:) and the rest one-paragraph pointers to the surface that owns them."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Authoring a work unit

How to fill the five-section WU contract (`.specfuse/templates/WU.template.md`,
methodology §4). **Target shape: 30-45 lines** — an objective, two to five acceptance
criteria each paired with the check that judges it, a `produces:` list, do-not-touch as
deltas, one or two escalation triggers. A longer body is usually restating a rule (link
it) or carrying two WUs (§6).

**The bar.** Every rule names a concrete failure mode it prevents; one that can't
is filler and was cut. Prefer a pointer to the surface that owns a fact over a second
copy here. Section numbers are stable — other skills, `lint_plan` and gate reviews cite
them — so a rule that moved keeps its heading as a pointer.

## 1. Context — write for a cold session

Name the correlation ID and the grounding files a memoryless session needs, and
**reference** the rules under `.specfuse/rules/` rather than restating them.
*Prevents:* thrashing for lack of grounding, and acting on a stale restatement.

## 2. Acceptance criteria — scope to the feature's own footprint

Criteria that grep or scan the **whole repo** trip on pre-existing, unrelated state and
cause a correct-but-unwanted block. Bound every check to the feature's own footprint:
its slug, the paths it creates or edits, the symbols it introduces, the files in
`generated_surfaces` / `produces`.

- Phrase each criterion as an **objective statement a gate can mechanically check**
  (`"GET /health returns 200"` ✓, `"endpoint is well-tested"` ✗).
- No compound criteria (`"X and also Y"`): split them, so one failure attributes to one
  line. Two to five criteria is the well-sized range.
- A criterion needing inspection of unrelated repo parts is the wrong shape — narrow it,
  or move the check to a hygiene WU or the `code` gate set.
- **Terminal `close` WUs: no "flip `PLAN.md status` to `done`" criterion.** The driver
  owns it (`fire_terminal_flips`, gated on `verdict_permits_terminal_flips`).

*Prevents:* a "grep returns zero hits" criterion blocking on a stale pointer the WU
never touched (`.specfuse/LEARNINGS.md`, `[meta/first-live-use]`).

## 3. Do not touch — write the deltas, not the whole rule

List only what `.specfuse/rules/never-touch.md` does not already bind: the sibling-WU
files in this gate, by path, and the repo-specific paths this WU might brush.
*Prevents:* a restated boundary list that drifts from the rule.

## 4. Verification — name the gates the driver will actually run

Name the set as declared in this repo's `verification.yml`, prefer a **scoped** command
for iteration work (a full-suite run per attempt collapses the three-attempt budget into
one), and confirm the runner exits non-zero when nothing matches. For `close` /
`close-intermediate` name `specfuse lint --closing`, never the guard names it checks
(that registry is `specfuse/loop/closing_requirements.py`). *Prevents:* a WU that passes
its own check and fails the driver's re-run.

## 5. Escalation triggers — the real hazard, not any flagging condition

Name triggers as conditions, not actions (`"if no router module exists, block — that's a
different unit"`, not `"create the router"`). When a tripped criterion might be
pre-existing unrelated state, a reasoned `status: blocked` with the evidence is the
right move ([`../../rules/result-contract.md`](../../rules/result-contract.md)).
*Prevents:* a doubtful pass that spends the gate's trust budget.

## 6. Sizing — one WU = one focused session's work

A WU is crafted to land in a single fresh-session pass; the Ralph property (fresh
context per attempt) only buys leverage when the unit fits.

- Multiple rounds of **unrelated** work means two WUs ("add the endpoint AND refactor
  the router module").
- Double-digit acceptance criteria means bundling; well-sized WUs have 2-5.
- A body past ~45 lines is the same smell in prose: it restates rules that belong behind
  a link, or carries two units of work. (Gate-cutting is a separate concern from per-WU
  sizing.)

*Prevents:* a WU that spends its whole attempt budget on the first of its two
sub-problems, and a squash commit mixing two unrelated changes.

## 7. Hygiene work units — when a blocked WU points outside its scope

When a WU's verification cannot pass because of a pre-existing bug in a path its
**Do not touch** forbids, insert a **hygiene WU** earlier in the gate, scoped to
that fix alone: ID `T<NN>H` (`T02H1`, `T02H2` for several,
[`../../rules/correlation-ids.md`](../../rules/correlation-ids.md)), one narrow
criterion, `produces:` naming only the broken file, wired into the graph before its
target (whose `depends_on` gains it and whose status returns to `pending`), and a
**Context** quoting the blocked WU's `human_escalation` event verbatim. Never widen the
blocked WU's boundary and never fix it out-of-loop; either erodes the per-WU contract or
the audit trail.

## 8. Cross-surface contract values — verify against the source, never invent

A criterion naming a value owned by **another system** (a label name, an API field, an
event-schema key, a branch/trailer format) is verified against the authoritative source
**before the gate is armed**: write a `verify <value> against <source>` line into the
WU, and carry a **Cross-repo contracts** table (value, source, checked) in every
plan-next gate review, where the blind spot is systematic. *Prevents:*
`[FEAT-2026-0003/G3-LESSONS]` — invented `loop:*` labels reporting state on a namespace
the poller never queries.

## 9. Hollow-pass pre-flight — enumerate symbols, then assert they exist

The `code` gate passes on an unchanged codebase when no test asserts an absent symbol.
Two halves of one pre-flight, both done while authoring, close that:

- **Enumerate before scoping.** A helper the WU names may exist more than once:
  `grep -rn "def <symbol>" tests/ src/`. On more than one hit, every hit is in scope
  **or** named in Do-not-touch as "out of scope — handled in <WU>". A WU creating a
  symbol meant to replace duplicates enumerates the call sites it will switch over;
  an author who cannot enumerate has an under-specified WU.
- **Assert existence in Verification.** For each new importable function, constant or
  class add `python3 -c "from module import symbol_name"` (or
  `grep -c "^def symbol_name" target.py` when import has side effects), plus a trigger:
  *"If [required_function / required_file] is absent from the files you edited, emit
  `status: blocked` — do not claim complete."*

*Prevents:* `FEAT-2026-0007/T04`, declared complete with zero production code and
the gate green on the unchanged tree; and FEAT-2026-0013's ship-fail-fail cycle, ~$10
re-attacking one `integration_workspace()` duplicate at a time.

## 10. Helper-duplication pre-flight

Folded into §9's first bullet.

## 11. Operator scripts are software, not docs

Moved to `docs/methodology.md` §5.1: a WU shipping an executable operator artifact
carries `shellcheck`, `bash -n`, and a bats happy-path with external commands stubbed —
in its acceptance criteria and as a named gate command.

## 12. Red-test first — name the failing test in the Acceptance criteria

An `implementation` WU introducing new behavior names a specific test that
**fails on the current tree** and **passes after** its edits. An agent that hasn't
written the test can't show the red→green transition, and one that hasn't written the
code can't flip it green: the loop's cheapest hollow-pass guard, with §4 and §9
downstream of skipping it.

Three bullets in **Acceptance criteria**: (1) `tests/<path>::<test_name>` exists and
fails on HEAD — a non-zero exit or a not-yet-existing file both count as red; (2) the
substantive change, as you'd have written it without this rule; (3) the
*same nodeid* passes after the edits. The test must be **scoped** (a pytest
nodeid, mocha `--grep`, JUnit `--tests`), never the full suite (§4).

**Skip when** there is no new behavior to assert: pure refactors (the suite is the
oracle), migrations whose oracle is row counts or schema shape, and `docs` / `lessons` /
`retrospective` / `close` / `plan-next`. Write `Red-test exempt: <reason>`; an exemption
with no reason is the violation.

## 13. `produces:` — declare named-file deliverables so the driver enforces them

Declare each named-file deliverable in `produces:`. The driver's presence gate
(`assert_declared_deliverables`) refuses `complete` when a listed path is missing or
empty, recording `deliverable_missing`; a body-level `test -s` is advisory.

- `produces: docs/report.md`, or `produces: ["src/a.py", "src/b.py"]` for a bundle.
  **Prefer one deliverable per WU** — a bundle listing only some of its files lets the
  rest pass silently (FEAT-2026-0020/T12 shipped `SECURITY.md`, not its bundled
  `CODE_OF_CONDUCT.md`).
- File-level only: it does not assert symbols inside a file (that's
  `produces_driver_helper`, lint-only) and is not retrofitted onto existing WUs.
  Independently of it, an `implementation` WU touching zero deliverable files records
  `no_deliverable_files` and blocks.
- Don't hand-copy path folklore into the body: run `specfuse lint <feature-dir>` before
  arming and read `check_produces_satisfiability` (WARN on a path a `done` WU already
  delivered) and `check_produces_boundary` (ERROR on a Do-not-touch collision).

*Prevents:* the zero-deliverable and partial-bundle hollow passes the
no-code-written guard left open (`[FEAT-2026-0020/G2/hollow-pass-presence-gates]`).

## Haiku — when (and when not)

`model: haiku` is opt-in per WU, never a default. Use it for `docs` WUs reconciling ≤ 2
files with no cross-WU reasoning, and `lessons` WUs appending ≤ 5 self-contained
entries. Avoid it for `implementation`, `plan-next`, `close`, `close-intermediate`, and
any `retrospective` over 3 substantive WUs: multi-file edits, forward design and
terminal verdicts regress on it. Defaults: `docs/methodology.md` §2.1.

## This skill distills `.specfuse/LEARNINGS.md`

The pipeline is **runs → retrospective → lessons → LEARNINGS.md → this skill**. A rule
graduates once it is reusable, durable, and would change how a future WU is written —
and graduating means finding it a home, not appending here.

## Version

**v0.11.** Diet (FEAT-2026-0084/T02): the skill prescribes a 30-45 line WU and
holds to 200 lines itself. §2, §6, §9, §12 and §13 stay in full; §1, §3, §4, §5, §7 and
§8 reduce to one paragraph with their citation; §10 folds into §9; §11 moves to
`docs/methodology.md` §5.1. Numbers are unchanged so citations resolve. Earlier: v0.10
§12, v0.9 §11, v0.8 §10, v0.6 Haiku, v0.5 §9, v0.4 §8, v0.2-v0.3 the produces-list
companion and the hygiene-WU pattern.
