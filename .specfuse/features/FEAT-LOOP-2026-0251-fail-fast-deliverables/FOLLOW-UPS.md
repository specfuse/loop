# Follow-ups — FEAT-LOOP-2026-0251

Re-close, 2026-11-26. One entry is open. The two entries from the first close are listed
under "Resolved"; both re-run conditions now hold.

### The early refusal also outranks three other checks, and no precedence is stated for them

**Criterion (verbatim).** "A surviving skip, or an early refusal whose outcome or failure
class differs from the late one for the same input, other than the deliverable-over-
`files_changed_mismatch` precedence `GATE-01.md` states (#3608): record `not_met` with a
follow-up."

**Evidence.** A probe drove `loop.run()` with the key `true` and then `false`. Each input
leaves a deliverable refusal in place and also trips a second check. Each cell is outcome /
failure class. The unit declares `src/rule.py`.

| Input | `true` | `false` |
|---|---|---|
| D: failing smoke-import line, `src/rule.py` untouched | `produces_not_in_diff` / `produces_not_in_diff` | `smoke_import_failed` / `smoke_import_failed` |
| E: produced `.md` with a `BLOCKED` verdict heading, `src/rule.py` untouched | `produces_not_in_diff` / `produces_not_in_diff` | `failed` / `guard_refusal` |
| F: `close` unit, `src/rule.py` untouched | `produces_not_in_diff` / `produces_not_in_diff` | `closing_deliverable_missing` / `guard_refusal` |
| G: failing smoke-import line, `src/rule.py` emptied | `deliverable_missing` / `guard_refusal` | `smoke_import_failed` / `smoke_import_failed` |

Controls: with every declared path changed and the key `true`, the D unit still gets
`smoke_import_failed` and the E unit still gets `failed` / `guard_refusal`. Details are in
`RETROSPECTIVE.md` under "Early against late, same input".

**What happened, in plain terms.** Every one of these attempts is still refused. Only the
name of the refusal, and so the retry advice, differs. The deliverable check now runs first,
so it wins over every check that used to run before it. The amendment after the first close
named just one of those checks. The first close had mentioned the others only as something
read in the code. The close cannot choose the precedence itself, and its instructions tell
it to record this.

One side effect comes from reading the code and was not measured. The old smoke-import and
closing-deliverable refusals always reset the working tree. The early refusal keeps it by
default. So in D, F and G the next attempt likely starts from a different tree.

**Why it was not fixed automatically.** The close may not edit source, the gate's definition
of done or the close unit.

**Options.**

1. State one general rule: a deliverable refusal takes precedence over every check that
   runs after the agent session (the verification gates and the later guards), and says so
   in `GATE-01.md`, the close unit's trigger and `docs/methodology.md`. For: no code change;
   matches what was built; covers checks nobody has listed. Against: on such an attempt the
   other problem is reported only on a later attempt, after the deliverable is fixed. It
   relaxes the plan after the fact, and costs one more close.
2. Run the cheap later checks (blocked verdict, smoke-import) before the early refusal. For:
   those outcomes match the old order. Against: smoke-import runs commands from the unit
   body and the closing guards expect a squashed commit, so this is real code and test work;
   `PLAN.md` decision 4 says those guards stay where they are.
3. Accept the `not_met` and merge by hand. For: no further loop spend. Against: the record
   keeps a failed gate for a difference in labelling.

**Recommendation.** Option 1. It states the rule once instead of one guard per re-close.

**Re-run condition.** Either `GATE-01.md` and the close unit's escalation trigger both state
a precedence that covers cases D to G, or each of D to G records the same outcome and
failure class with the key `true` and `false`, asserted by a test.

## Resolved

#### An early refusal records a different outcome from the late order for one input

**Tracked as #3608.** **Re-run condition holds.** `GATE-01.md` ("Precedence when two
refusals apply") and the close unit's escalation trigger state that the deliverable refusal
takes precedence over `files_changed_mismatch`.
`test_deliverable_refusal_outranks_files_changed_mismatch` asserts both sides and passed in
this session; the probe's case A agrees.

#### Clause 6 does not hold literally for two pre-existing tests

**Tracked as #3609.** **Re-run condition holds.** `GATE-01.md` clause 6, widened on
2026-11-26, covers edits forced by moving code into a shared helper and by new lint wording.
The ten changed modules pass (68 tests, exit 0), and the two edits are named in
`RETROSPECTIVE.md`.
