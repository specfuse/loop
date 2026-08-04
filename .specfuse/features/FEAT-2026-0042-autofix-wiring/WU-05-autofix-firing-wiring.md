---
id: FEAT-2026-0042/T05
type: implementation
status: draft
attempts: 0
planned_cost_usd: 4.50
produces:
  - specfuse/monitor/autofix_run.py
  - tests/test_autofix_run.py
oracle_env: macos_local
model: sonnet
effort: medium
---

# The firing wiring: decide, record, fire, label

**Objective.** Ship `specfuse/monitor/autofix_run.py` — the one place where T01's
decision, T02's durable state, and T04's invoker meet. Given a diagnosed finding
issue, it reads the diagnosis, asks T01 whether to fire, records the attempt, fires
through T04's invoker, and labels the result. This is the work unit that makes the
`autofix` dial stop being inert.

**Context.** Correlation ID `FEAT-2026-0042/T05`. Read `PLAN.md`, `GATE-02.md`, and
`RETROSPECTIVE.md` first. Gate 1 shipped four pieces this module composes and does
not modify: `specfuse/monitor/autofix.py` (`decide`, the three decisions, the seven
reasons), `specfuse/monitor/autofix_state.py` (`has_prior_attempt`, `record_attempt`,
`daily_cap_reached`, `GitHubAutofixState`, `AUTOFIX_FAILED_LABEL`),
`specfuse/monitor/diagnosis.py` (`parse`), and — from T04 — the invoker. The
retrospective is explicit that `CONFIDENCE_THRESHOLD` and `DAILY_CAP` stay hardcoded
module constants and must not be relocated into `monitoring.yml` by this gate.

**Everything reaches GitHub through an injected runner, and `fix-bug` through an
injected invoker.** This module composes; it shells out to nothing directly. That is
what keeps its whole test surface stub-verified inside the sandbox and makes
`FEAT-2026-0042/T06` the single work unit in this gate that touches a real repository.

## The safety floor — carried forward, not re-decidable here

Auto-merge belongs to [FEAT-2026-0048](../../roadmap.md#feat-2026-0048) and is
**impossible in this feature**. No work unit in this gate may merge a pull request,
enable auto-merge, or push to a protected branch. The ceiling is an unwanted PR on a
branch. A work unit that believes it needs to widen this is an escalation to the
operator, not a judgement call.

## Flag-scope table (`.specfuse/rules/planning-discipline.md` §3)

This work unit is the `autofix` dial's first consumer, so the claim "the dial goes
live" is only as true as this table. Every row is a decision, not a description.

| Code path | Gated by `autofix`? | Why |
| --- | --- | --- |
| `autofix_run.run_autofix` — this module's entry point | **yes** | It calls T01's `decide`, which reads the dial first and returns `DECLINE` before anything else is evaluated. This is the only path that can fire. |
| `specfuse-monitor run` — the harvest cycle in `specfuse/monitor/cli.py` | **not gated, because it is deliberately not wired** | A routine harvest that could launch a fix is a far wider blast radius than this gate can verify, and it would fire on findings nobody read. The firing path stays behind its own explicit entry point. |
| `specfuse/monitor/autofix_state.py` writes | no | Reached only from the `FIRE` branch, after the dial has been read. |
| T04's invoker | no | A pure builder/classifier. It never reads the dial and must not start. |
| `specfuse/loop/lint_monitoring.py` dial validation | no | Validates the value; never acts on it. Unchanged by this gate. |
| `specfuse/loop/labels.py` label registry | no | `AUTOFIX_FAILED_LABEL` is registered regardless of any component's dial. Unchanged by this gate. |

**The entry point is its own, not a subcommand of the harvest cycle.** Ship a `main()`
in this module, invoked as `python3 -m specfuse.monitor.autofix_run`, following
`specfuse/monitor/diagnose_cli.py`'s precedent. Row two of the table is the reason,
and it is a scope decision this WU is not free to reverse: wiring the firing path into
`specfuse-monitor run` is a separate change with a separate blast radius, and this
gate's live evidence covers the explicit entry point only.

## Two things to get right, both cheap to get wrong

**Record the attempt *before* invoking, never after.** `record_attempt` is idempotent
and the whole point of it is one fix run per fingerprint. If the invoke happens first
and the session is killed mid-run — which is not hypothetical; this feature's own
gate 1 lost an attempt to an infra kill — no marker exists, and the next invocation
fires the same fingerprint again. Recording first can at worst cost one fingerprint a
run it never got; recording last can cost a repository a retry storm.

**The dial is per-component, and `decide` wants a component-keyed mapping.**
`.specfuse/monitoring.yml` holds `components:` as a *list* of dicts; `decide` reads
`monitoring_config[component]["autofix"]`. Adapt the list into a name-keyed mapping
here rather than changing either side's shape.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

## The contract

`run_autofix(...)` takes an injected runner, an injected invoker, the repository, the
finding issue number, the parsed monitoring config, and the component name, and:

1. reads the finding issue — its body for the fingerprint marker
   `specfuse/monitor/issues.py` already writes, its comments for the most recent
   diagnosis comment body;
2. calls `decide` with that diagnosis body, the component-keyed config, the
   fingerprint, and a `GitHubAutofixState` reader;
3. on `DECLINE` — does nothing at all: no write, no label, no invoke;
4. on `ROUTE_TO_HUMAN` — leaves the finding for a human, and does **not** record an
   attempt: routing is not a spent fix run, and recording one would permanently bar a
   finding a human might later want fixed;
5. on `FIRE` — records the attempt, then invokes, then labels: `refused` and
   `could_not_proceed` apply `AUTOFIX_FAILED_LABEL`; `completed` applies no failure
   label.

Return the decision, the reason, and the outcome (or `None` when nothing fired) so the
caller and T06 can assert on what happened rather than infer it from side effects.

**Acceptance criteria.**

1. `tests/test_autofix_run.py::TestAutofixRun::test_dial_off_never_invokes_the_fixer`
   exists and **fails on HEAD before this WU runs** (`specfuse/monitor/autofix_run.py`
   does not exist, which counts as red), and passes after this WU's edits.
2. That test asserts a component whose dial is `"off"` — given an otherwise perfect
   diagnosis (`confidence: 1.0`, `fix_scope: small`, no prior attempt, cap not
   reached) — produces zero calls on the injected invoker and zero writing calls on
   the injected runner.
3. A test asserts that on `FIRE` the attempt is recorded **before** the invoker is
   called, by asserting the observed order of calls, not merely that both happened.
4. A test asserts `ROUTE_TO_HUMAN` calls neither the invoker nor `record_attempt`.
5. A test per outcome asserts the label mapping: `refused` and `could_not_proceed`
   apply `AUTOFIX_FAILED_LABEL`, `completed` applies no failure label. The constant is
   imported from `specfuse/monitor/autofix_state.py`, never spelled as a literal:
   `grep -n "auto-fix-attempted-failed" specfuse/monitor/autofix_run.py` returns
   nothing. Quote the output.
6. The harvest cycle gains no caller: `grep -n "autofix" specfuse/monitor/cli.py`
   returns no hit. Quote the output.
7. Nothing in this module can merge, enable auto-merge, or push to a protected branch:
   `grep -nE "pr merge|--auto|--admin|push" specfuse/monitor/autofix_run.py` returns
   no such call. Quote the output.
8. This module shells out to nothing directly:
   `grep -nE "subprocess|requests|urllib|os\.system" specfuse/monitor/autofix_run.py`
   returns nothing, and no test in `tests/test_autofix_run.py` makes a real `gh` call.
   Quote the output.
9. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `specfuse/monitor/autofix.py` — T01 owns the predicate; if a rule
needs changing that is an escalation. `specfuse/monitor/autofix_state.py` and
`specfuse/loop/labels.py` — T02 owns the state and the label registry; import from
them, do not edit them, and do not relocate `CONFIDENCE_THRESHOLD` or `DAILY_CAP`
anywhere. `specfuse/monitor/autofix_invoke.py` — T04 owns the invoker; this module
calls it through injection. `specfuse/monitor/diagnosis.py` and
`specfuse/monitor/issues.py` — FEAT-2026-0040 and FEAT-2026-0041 own the diagnosis
contract and the finding-issue marker convention; read them, never invent a second
marker. `plugins/specfuse/skills/fix-bug/SKILL.md` and its vendored copy under
`.specfuse/skills/fix-bug/` — T03 owns them. `specfuse/monitor/cli.py` — criterion 6
is the point; the harvest cycle is read for that grep and otherwise untouched.
`specfuse/loop/` — the driver's dispatch path is not extended by this feature.
`.specfuse/monitoring.yml.example` and `specfuse/loop/data/monitoring.yml.example` —
the shipped default stays `"off"`, and the two copies are byte-compared by
`tests/test_scaffold_data_in_sync.py`, so an edit to either goes red until
`scripts/sync-scaffold.sh` runs. The driver owns all git: this session edits files
only and never runs `git`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` — every gate in
that set: `tests`, `lint`, `security`, `coverage` (≥90%), `leak-scan`. Beyond the
gates, run the symbol-existence check and quote it:
`python3 -c "from specfuse.monitor.autofix_run import run_autofix, main"`. Criteria 3
and 7 are the load-bearing ones — a record-after-invoke ordering turns the
one-run-per-fingerprint guarantee into nothing the first time a session is killed,
and criterion 7 is where this feature's central safety claim is mechanically checked
rather than asserted.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
finding issue's diagnosis cannot be located or parsed without changing
`specfuse/monitor/diagnosis.py`'s contract or `specfuse/monitor/issues.py`'s marker
convention, both of which are owned elsewhere; `decide` needs an input the finding
issue does not carry, which is a T01 contract gap and not this WU's to paper over
with a default; the component-keyed adaptation cannot be done without changing
`decide`'s signature; or `run_autofix` is absent from the files you edited — do not
claim `complete` on a module that does not define it. Do **not** write any `gh` call
into this module or its tests that reaches a real repository: this WU is sandboxed and
stub-verified, and `FEAT-2026-0042/T06` is the only work unit in this gate permitted
to reach one. Do **not** merge a pull request, enable auto-merge, or push to a
protected branch — that is FEAT-2026-0048's territory and an escalation to the
operator, not a design choice.
