---
gate: 1
status: open
baseline:
  sha: a8f17a9c4bb140a81e36962fbdd03f2b87f2d131
  probed_at: 2026-09-07T19:55:09.719350+00:00
  entry_sha: ad59ccaba8595a2ba362d6c22fad3038fc82d98c
  failing: []
---

# Gate 1 — the suite runs once per pass, and the two gates still report distinct failures

## Definition of done

- A gate in `.specfuse/verification.yml` may declare `needs: [<gate>]`. The
  driver runs the set in dependency order; a gate whose dependency failed is
  reported `SKIP` and never counted as a pass.
- An unresolvable `needs:` target and a dependency cycle are both
  CONFIGURATION ERRORs, in the same shape as the existing unknown-`extra_gates`
  branch (`loop.py:4159`) — never a silent skip, never a silent pass.
- `gate_commands.py` emits gates in the same dependency order the driver uses,
  so `scripts/smoke-test.sh` and CI cannot disagree with the driver about
  whether a gate's prerequisites ran.
- This repo's `code` set runs its test suite **once** per pass: `tests` runs the
  suite under `coverage run`, `coverage` declares `needs: [tests]` and only
  reports. Measured `code`-set wall clock is recorded against the 118s baseline
  in `[FEAT-2026-0051/G1-CLOSE]`.
- `tests` and `coverage` still produce distinct `failure_class` values, and a
  failing test still yields a test-shaped `failure_signature` rather than a
  coverage-shaped one — the property that makes `spinning_signature_repeat` and
  `learnings-suggest` work.
- The authoring rule in the canonical `plugins/specfuse/skills/verification/SKILL.md`
  states the new contract: self-contained **unless** the gate declares `needs:`,
  in which case the runner owns the freshness guarantee.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

This is a single-gate feature with a terminal `close` (`docs/methodology.md` §6,
ceremony proportionality). There is no `plan-next` and no next gate to arm.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

No next gate is armed from here. Two items from the arming discipline still
bind on this gate's own review:

- **Escalation-predicate satisfiability (§2).** T01 introduces a CONFIGURATION
  ERROR. `PLAN.md` answers what it reports on a correct input: zero, because a
  gate set with no `needs:` key and a gate set whose `needs:` all resolve both
  report nothing. Confirm that still holds against the shipped
  `verification.yml.example` and every target scaffold before the close.
- **Runtime probe (§4).** T03 changes a default the driver runs on every
  attempt. Its acceptance requires the exact `code`-set commands to be run and
  timed, not a subset — see `[FEAT-2026-0039/G2-CLOSE]` on criteria naming
  runners the repo does not have, and the operator note "run smoke-test.sh, not
  ruff+unittest alone".

## Reflection notes

<Written by the human at review time. What surprised you, what the close got
wrong, whether the ordering discipline in PLAN.md's task graph actually held.>
</content>
