---
id: FEAT-2026-0042/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
produces:
  - specfuse/monitor/autofix_invoke.py
  - tests/test_autofix_invoke.py
oracle_env: macos_local
model: sonnet
effort: medium
---

# The headless `fix-bug` invoker: build the call, classify the result

**Objective.** Ship `specfuse/monitor/autofix_invoke.py` — the surface that turns
"fire an automated fix on issue NN" into a concrete headless `fix-bug` invocation and
turns that invocation's result back into exactly one of the three outcomes T03's
skill defines. It builds and classifies; the caller (T05) executes.

**Context.** Correlation ID `FEAT-2026-0042/T04`. Read `PLAN.md` and `GATE-02.md`
first, then the `## Headless mode` section of `plugins/specfuse/skills/fix-bug/SKILL.md`
— that section is the authoritative contract this module consumes, and its closed
outcome set (`refused` / `could_not_proceed` / `completed`) is not this module's to
extend. `RETROSPECTIVE.md` records why `refused` is a normal, expected result of a
fired run rather than a failure: T01 decides the finding *looks* small from the
diagnosis, and `fix-bug`, having read the actual code, decides whether it *is*.

**This module builds and classifies. It does not run anything.** No `subprocess`, no
network, no `gh`, no `claude` launch. The command it builds is handed back to an
injected runner that T05 owns and that T06 is the only work unit permitted to point
at a real repository. Keeping the launch out of this module is what lets its whole
test surface be stub-verified inside the sandbox.

**Fail closed.** A session result this module cannot classify — empty output, a
truncated run, two outcome words present, an outcome string outside the closed set —
resolves to `could_not_proceed`, never `completed`. Resolving an unreadable result to
"the fix landed" would let T05 skip the failure label on a run that never finished,
which is the shape a guardrail takes when it reads as present and is not.

## The safety floor — carried forward, not re-decidable here

Auto-merge belongs to [FEAT-2026-0048](../../roadmap.md#feat-2026-0048) and is
**impossible in this feature**. No work unit in this gate may merge a pull request,
enable auto-merge, or push to a protected branch. The ceiling is an unwanted PR on a
branch. A work unit that believes it needs to widen this is an escalation to the
operator, not a judgement call.

That constraint is load-bearing *inside this module*, not just around it: the prompt
this module builds is what a fresh headless session reads, so the prohibition has to
be literal text in the prompt, not an assumption about the skill's good behaviour.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

## The contract

Three public names, stated in the module docstring:

- `OUTCOMES` — the closed tuple of the three outcome strings, spelled exactly as the
  skill's `## Headless mode` section spells them. No fourth member.
- `build_invocation(...)` — given the issue number, the repository, and the working
  directory the run should happen in, return the argv and the prompt text for a
  headless `fix-bug` session. It returns them; it does not run them.
- `classify_outcome(...)` — given a completed session's result text, return exactly
  one member of `OUTCOMES`.

Build the argv for a fresh headless session in the same shape the loop driver's own
dispatch path uses (`claude -p` with an explicit model and effort, prompt on stdin) —
but build it here, in this module, rather than importing or extending that path.
The driver dispatches work units; this dispatches a bug fix. Coupling them would put
a `fix-bug` launch inside the surface that runs every work unit in the loop.

**Acceptance criteria.**

1. `tests/test_autofix_invoke.py::TestAutofixInvoke::test_unclassifiable_result_is_could_not_proceed`
   exists and **fails on HEAD before this WU runs** (`specfuse/monitor/autofix_invoke.py`
   does not exist, which counts as red), and passes after this WU's edits.
2. That test asserts empty output, output carrying no outcome word, and output
   carrying two different outcome words all resolve to `could_not_proceed` — never
   `completed`, never a raise.
3. A test asserts `OUTCOMES` is exactly the three strings the `## Headless mode`
   section of `plugins/specfuse/skills/fix-bug/SKILL.md` defines, read from that file
   rather than restated in the test, so the two surfaces cannot drift apart silently.
4. A test asserts the prompt `build_invocation` returns names the issue number, puts
   the skill in headless mode, and carries a literal prohibition on merging a pull
   request, enabling auto-merge, and pushing to a protected branch.
5. One classification test per outcome in `OUTCOMES`, each asserting the returned
   outcome and that no other member is returned for that input.
6. This module runs nothing itself:
   `grep -nE "subprocess|requests|urllib|os\.system|^import |^from " specfuse/monitor/autofix_invoke.py`
   shows no execution or network import. Quote the output.
7. No test in `tests/test_autofix_invoke.py` launches a real session or makes a real
   `gh` call — the test file greps its own subject for the same execution imports, the
   way `tests/test_autofix_state.py` already greps its own subject, so a raw call that
   escaped a stub fails the suite.
8. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `specfuse/monitor/autofix.py` — T01 owns the predicate.
`specfuse/monitor/autofix_state.py` and `specfuse/loop/labels.py` — T02 owns the
state and the label registry. `plugins/specfuse/skills/fix-bug/SKILL.md` and its
vendored copy under `.specfuse/skills/fix-bug/` — T03 owns them; the headless
contract is what this module consumes, and if it looks wrong that is an escalation,
not an edit. `specfuse/monitor/autofix_run.py` — T05 owns the wiring that calls this
module. `specfuse/monitor/cli.py` — the harvest cycle gains no autofix caller in this
gate. `specfuse/loop/` — the driver's dispatch path is not extended by this feature.
`.specfuse/monitoring.yml.example` — the shipped default stays `"off"`. The driver
owns all git: this session edits files only and never runs `git`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` — every gate in
that set: `tests`, `lint`, `security`, `coverage` (≥90%), `leak-scan`. Beyond the
gates, run the symbol-existence check and quote it:
`python3 -c "from specfuse.monitor.autofix_invoke import OUTCOMES, build_invocation, classify_outcome"`.
Criteria 2 and 4 are the load-bearing ones — an unclassifiable result resolving to
`completed` would let a run that never finished pass unlabelled, and a prompt without
the literal prohibition is the one place in this feature where the safety floor stops
being enforced by anything but hope.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
`## Headless mode` section defines an outcome set that is not the three strings named
above, in which case name the drift rather than inventing a fourth outcome or
silently widening `OUTCOMES`; a session result cannot be classified without changing
the skill's own halt→outcome mapping table, which is T03's contract and not this
WU's to revise; or `OUTCOMES`, `build_invocation`, or `classify_outcome` is absent
from the files you edited — do not claim `complete` on a module that does not define
them. Do **not** make any `gh` call, launch a real headless session, create a branch,
or open a pull request from this work unit: it is sandboxed and stub-verified, and
`FEAT-2026-0042/T06` is the only work unit in this gate permitted to reach a real
repository. Do **not** merge a pull request, enable auto-merge, or push to a
protected branch under any circumstance — that is FEAT-2026-0048's territory and an
escalation to the operator, not a design choice.
