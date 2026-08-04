---
id: FEAT-2026-0042/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
produces:
  - specfuse/monitor/autofix.py
  - tests/test_autofix_predicate.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-08-03T22:30:36.351451+00:00
duration_seconds: 474.273
cost_usd: 1.163152
input_tokens: 44
output_tokens: 14845
---

# The autofix predicate: fire, route, or decline — and say why

**Objective.** Ship `specfuse/monitor/autofix.py` with a pure function that answers
"should this diagnosed finding be handed to an automated fix?" from a `Diagnosis`,
the component's `autofix` dial, and the rate-limit state — returning the decision and
the reason for it.

**Context.** Correlation ID `FEAT-2026-0042/T01`. Read `PLAN.md` first — it records
that the dial already exists and is inert, that the confidence threshold is
deliberately hardcoded, and the safety floor this feature cannot widen. Do not reopen
those decisions.

**Pure, and firing nothing.** This function decides. It does not invoke `fix-bug`,
create a branch, open a pull request, call `gh`, or touch the network. Gate 1 ships a
decision layer that cannot act; that is the gate's whole safety property.

**Why the threshold is a constant and not config.** FEAT-2026-0053's arm predicate
hardcodes its stop-class constants for exactly this reason: a safety threshold that
lives in a config file can be tuned into uselessness by the person it is meant to
stop. `autofix: on|off` is per-component and belongs in `monitoring.yml`; *how
confident is confident enough* is not.

**Fail closed.** Any input the predicate cannot evaluate — a `Diagnosis` that will not
parse, a component absent from the config, a malformed dial value, unreadable state —
returns *decline*, never *fire*. A predicate that guesses "probably fine" on an input
it cannot read is worse than no predicate, because it reads as a guardrail.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

## The contract

The decision is a small closed vocabulary, not a boolean — the caller must be able to
tell *declined* from *routed to a human*, and the reason must survive into the label
and the issue comment gate 2 will write. State the vocabulary in the module docstring.

The rules, in the order they must be evaluated:

1. Component's `autofix` dial is not `"on"` → **decline**. The dial is the outermost
   gate and nothing overrides it.
2. `fix_scope` is `large` or `external` → **route to human**. These are not failures;
   they are findings whose fix is out of an automated run's competence.
3. `confidence` below the hardcoded threshold → **route to human**.
4. This fingerprint already has a recorded autofix attempt → **decline**.
5. The daily cap is reached → **decline**.
6. Otherwise → **fire**.

Rate-limit state is **read through an injected reader**, not fetched here — T02 owns
where state lives. This module must remain testable with no GitHub and no network.

**Acceptance criteria.**

1. `tests/test_autofix_predicate.py::TestAutofixPredicate::test_dial_off_declines_regardless_of_confidence`
   exists and **fails on HEAD before this WU runs** (`specfuse/monitor/autofix.py`
   does not exist, which counts as red).
2. That test asserts a perfect diagnosis — `confidence: 1.0`, `fix_scope: small`, no
   prior attempt, cap not reached — still **declines** when the component's dial is
   `"off"`, and it passes after this WU's edits.
3. One test per rule 2–6 above, each asserting both the decision **and** that the
   reason names which rule fired. A decision with an unattributable reason is
   untraceable in the issue comment gate 2 writes.
4. A test asserts `large` and `external` produce **route-to-human**, not decline —
   these must be distinguishable, because gate 2 routes them differently.
5. Four fail-closed tests, one each: an unparseable `Diagnosis`, a component absent
   from the config, a malformed dial value, and a state reader that raises. All four
   return decline, none raise, none return fire.
6. A test asserts the confidence threshold is a module constant and the predicate
   reads no config file: `grep -n "open(\|Path(\|yaml\|load" specfuse/monitor/autofix.py`
   returns no config read. Quote the output.
7. `specfuse/monitor/autofix.py` makes no subprocess, network, or `gh` call. Assert
   with `grep -n "^from \|^import \|subprocess\|requests\|urllib\|gh " specfuse/monitor/autofix.py`
   and quote it.
8. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `specfuse/monitor/diagnosis.py` — FEAT-2026-0041 owns the
`Diagnosis` contract; if the predicate needs a field it does not expose, that is an
escalation. `specfuse/loop/labels.py` and the state layer — T02 owns both.
`.specfuse/skills/fix-bug/` — T03 owns it. `.specfuse/monitoring.yml.example` — the
dial already exists and needs no change.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Criterion 5 is the load-bearing
one — a predicate that raises instead of declining turns an unreadable input into a
crashed harvester run, and a predicate that fires on one is the failure this whole
feature exists to prevent.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
`Diagnosis` contract lacks a field the rules need; the decision vocabulary cannot
distinguish decline from route-to-human without changing T02's or gate 2's expected
interface; or a rule cannot be evaluated without reading state directly, which would
break the injected-reader boundary. Do **not** invoke `fix-bug`, create a branch,
open a pull request, or make any writing `gh` call from this work unit — gate 1 fires
nothing, and a WU that believes it must has misread the gate boundary.
