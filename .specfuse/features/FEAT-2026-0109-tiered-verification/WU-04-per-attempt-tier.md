---
id: FEAT-2026-0109/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
oracle_env: macos_local
produces_driver_helper: resolve_gate_tiers
produces:
  - specfuse/loop/loop.py
  - specfuse/loop/data/verification.yml.example
  - .specfuse/verification.yml
  - tests/test_tiered_verification_e2e.py
model: sonnet
effort: high
gate_set: code
---

# Tracer bullet — a per-attempt tier that runs the narrow gates and only those

**Objective.** Give each `code` gate a declared tier and make a per-attempt
verification execute only the narrow one, so an attempt stops paying for the
fifteen gates that have nothing to say about the file it touched.

**Context.** FEAT-2026-0109/T04; read `PLAN.md`, `GATE-02.md` (including its
measurement table and its oracle contract), and `GATE-02-REVIEW.md`.

Today `verify()` (`loop.py:4206`) resolves one gate set by work-unit type
(`GATES_FOR_TYPE`), unions the WU's `extra_gates`, orders by `needs:`, appends
the gate's `feature_oracle`, and runs the lot through `_run_gate_set` on every
attempt. Measured on this tree that is 169.4s per attempt, of which 146.1s is
the full unittest suite and 0.05s is `ruff`. The narrow tier is roughly 6s.

This unit is the **tracer bullet** for gate 2: it makes
`tests/test_tiered_verification_e2e.py` — the gate's `feature_oracle`, red on
HEAD because the module does not exist — go green on the per-attempt half. It
may leave the changed-file selector (T05) and the once-per-gate broad run (T06)
as stubs behind it; no other unit in this gate may.

**Incremental edit to `specfuse/loop/loop.py`.** T01 delivered this file in
gate 1 (the attribution helper and the skipped entry call). This unit adds a
tier resolution in front of `_run_gate_set` and a per-attempt command
substitution; it changes nothing in `probe_baseline`, `gate_baseline_check` or
`attribute_failure_to_baseline`.

**The declaration shape, and why it is one list and not two.**
`scripts/smoke-test.sh` derives CI's gate list from `verification.yml` at run
time (#592), and `.github/workflows/ci.yml` just invokes that script. A new
top-level `code-narrow:` / `code-broad:` pair would therefore silently drop
gates from CI the moment the runner kept reading `code:`. So: keep the single
`code:` list and annotate each entry, e.g. a `tier:` key alongside the existing
`name`, `command` and `needs:`.

**Absent-key behaviour is the load-bearing decision.** An entry that declares
no tier must keep today's behaviour exactly — it runs per attempt *and* in the
broad run. Opting a gate **out** of the per-attempt run is an explicit
declaration; a gate added later, by anyone, is never silently demoted. A
`verification.yml` with no tier keys anywhere must behave byte-identically to
today, which is also what keeps an older driver reading a newer config safe:
unknown keys are ignored.

**The `tests` gate narrows; it does not disappear.** Per attempt it runs a
selected subset of test modules; per gate it runs whole under `coverage run`,
unchanged. That is one gate entry with two commands, not two entries — a second
entry would need a second name and would break the `needs: [tests]` edge the
`coverage` gate already declares. Give the entry a per-attempt command carrying
a substitution the driver fills with the selected modules; `verification.yml`
already substitutes `{feature_dir}` in the `doc` and `plannext` sets, so the
mechanism exists and this is a second placeholder, not a new idea.

**The selection this unit ships, and the part it defers.** T04's selection is
the unit's **own declared test paths** — the entries of its `produces:` list
that live under `tests/`. That is the cheap, author-declared half, measured at
3.9s for a gate-1 unit's three modules, and it needs no new inference
machinery: `produces:` already exists and is already machine-enforced by the
presence gate. The changed-file half — "tests touching changed files" — is
T05's, and the reasoning behind the rule chosen for it is in
`GATE-02-REVIEW.md` § "Tests touching changed files". Until T05 lands, a unit
whose `produces:` names no test path selects nothing, which must fall back to
the full command (below), not to an empty run.

**Fail safe, never open.** An empty selection, a `produces:` naming no test
path, or any path the selector cannot resolve falls back to the gate's **full**
command. The tier is allowed to run more than necessary and never allowed to
run nothing. A narrow tier that silently ran zero tests and reported PASS is
the hollow pass this whole feature would otherwise manufacture at scale.

**A self-hosting hazard, stated so it is not rediscovered.** This unit edits
`.specfuse/verification.yml`, which is this repo's own exit oracle, and
`specfuse/loop/loop.py`, which is the driver executing the run. The driver
process already running will trip `driver_staleness_detected` and halt for a
restart after this unit lands, exactly as T01–T03 did; that is expected, not a
failure. Do **not** weaken, reorder or remove any gate in `.specfuse/verification.yml`
to make this unit pass — adding a tier key to an entry is in scope, editing an
entry's own `command` is not (`never-touch.md`, "A note on verification.yml").
Mirror any new key into `specfuse/loop/data/verification.yml.example` in the
same pass, with a comment saying what the absent key means; a config key that
ships without an example is a key nobody discovers.

**Flag-scope table (`planning-discipline.md` §3).** `tier:` gates which gates
run, so every path that resolves a gate list is either deliberately gated by it
or deliberately not. Added at arm time; if implementation shows a row is wrong,
say so in the RESULT rather than silently widening the flag.

| Code path | Gated by `tier:`? | Why |
|---|---|---|
| `verify()`'s per-attempt gate list | **Yes** | The point of the unit: a per-attempt run executes the narrow tier only. |
| The once-per-gate broad run | No — T06 owns it | T04 may leave it stubbed; a tier-aware broad run that dropped gates would be the silent-coverage-loss failure this feature must not cause. |
| `probe_baseline` / `attribute_failure_to_baseline` | **No** | Attribution answers "was this tree already red", which is a question about the full `code` set. Narrowing it would make a pre-existing failure invisible to the mechanism gate 1 built to find it. |
| `gate_commands.iter_code_gates` (CI + `smoke-test.sh`, #592) | **No** | CI derives its list from `code:` and must keep running every gate. This is why the tier is an annotation on one list rather than a `code-narrow:`/`code-broad:` split. |
| The gate's `feature_oracle` append | **No** | The oracle runs on every attempt by FEAT-2026-0101's contract; tiering it would remove the end-to-end signal the per-attempt tier depends on. |

**Acceptance criteria.**

- `tests/test_tiered_verification_e2e.py::test_per_attempt_run_executes_only_the_narrow_tier` fails on HEAD (the module does not exist) and passes after: driving the real `loop.run()` through one dispatched attempt with a recording `_run_gate_set`, the gates declared per-gate-only are **absent** from the executed list, and the narrow ones are present. Asserted from the recorded execution, not by reading `verification.yml`.
- `::test_untiered_gate_still_runs_every_attempt`: an entry declaring no `tier` is present in the per-attempt run — the absent-key default, asserted as an observed execution.
- `::test_a_config_with_no_tier_keys_is_byte_identical_to_today`: the executed gate list for a `verification.yml` carrying no tier key anywhere equals the list today's code produces for the same input.
- `::test_selection_falls_back_to_the_full_command_when_empty`: a unit whose `produces:` names no path under `tests/` runs the `tests` gate's **full** command, and the recorded command is the full one — not an empty selection and not a skipped gate.
- `::test_declared_test_paths_are_selected`: a unit whose `produces:` names two paths under `tests/` runs the per-attempt command with exactly those two modules, and the full command does not appear in the recorded run.
- `python3 -m unittest tests.test_tiered_verification_e2e -q` reports `OK` (this gate's `feature_oracle`).
- `python3 -m unittest discover -s tests -q` reports `OK`.
- `bash scripts/smoke-test.sh` reports `smoke test: OK` — the CI runner still derives every gate from `code:`, including the ones now tiered per-gate.

**Do not touch.** T05's changed-file selector and T06's broad-run bookkeeping
beyond the stubs this unit needs; T07's attribution bound; gate 1's units,
`GATE-01.md`'s `baseline:` block, and `RETROSPECTIVE.md`; `probe_baseline`,
`gate_baseline_check` and `attribute_failure_to_baseline`; the `command:`
string of every gate entry this repo's verification config already declares —
adding a tier key beside one is this unit's job, editing what one runs is not;
`.specfuse/rules/`, `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus this
gate's `feature_oracle`.

**Escalation triggers.** Emit `status: blocked` if the per-attempt command
cannot be expressed without splitting `code:` into two top-level lists — that
would put CI's derived gate list (#592) at risk and is an operator decision,
not a drafting one. Also block if narrowing the `tests` gate cannot preserve
the `needs: [tests]` edge the `coverage` gate declares, rather than quietly
dropping either the edge or the coverage gate.
