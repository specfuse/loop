---
id: FEAT-2026-0036/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
---

# Gate 1 close — Adopt ruff 0.16

**Objective.** Terminal close for the single-gate feature: re-run the oracles
fresh, record the retrospective + lessons + docs note + verdict in one session,
and confirm the feature's north star (linter current, tree clean, pin gone) is
actually met — not just artifact-shaped.

**Context.** Terminal close of FEAT-2026-0036 (collapses retrospective +
lessons + docs + verdict). Depends on T01 (import cleanup) and T02 (pin lift).
Binding rules in `.specfuse/rules/` (`result-contract.md`, `close-discipline.md`)
apply. The driver owns the terminal `PLAN.md status -> done` flip — do NOT add a
status-flip acceptance criterion.

**Acceptance criteria.**
- A `## Retrospective` section: what went as planned, what surprised (e.g. how
  many of the ~300 were auto-fixable vs hand-fixed), and a `## What I'd change`
  note.
- A `## Lessons` section with any durable rule worth promoting to
  `.specfuse/LEARNINGS.md` — at minimum the "pin external linters/formatters in
  CI so an upstream release can't break every PR at once" lesson this feature
  exists because of.
- A `## Docs` note: confirm no user-facing doc change is needed (internal tooling
  constraint), or name the doc touched.
- A `## Cost analysis` section is present, reconciling `planned_cost_usd` (PLAN
  + per-WU frontmatter) against actual spend (events.jsonl), with the delta
  named.
- A `## What the loop did NOT verify` section is present, enumerating each
  acceptance criterion whose verification was deferred (with why and where it
  actually happens). Required even when empty — write `(nothing — every
  acceptance criterion was verified in-loop)`.
- **Oracles re-run fresh** (close-discipline §1): `ruff --version` (≥ 0.16) and
  `ruff check` exit 0, read directly (not from T01/T02 self-report);
  `python3 -m unittest discover -s tests -q` reports `OK`;
  `python3 -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"`
  exits 0 and the loaded `dev` extra shows no `<0.16` bound.
- **Consumer-visible contract changes** (§3): `n/a — no consumer-visible
  contract change` (a dev-only lint constraint; no API, CLI, or scaffold surface
  moved).

**Do not touch.** Source and test files (T01/T02 own those), `.git/`, secrets.
This WU writes only its own close record. The driver owns git and the terminal
PLAN flip. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext`/close gates plus a fresh re-run of the oracles
named above. See `.specfuse/skills/verification/SKILL.md`. On a hedged outcome,
record the follow-up per close-discipline §2.

**Escalation triggers.** Emit `status: blocked` if a fresh oracle re-run
disagrees with T01/T02's self-report (ruff non-zero, a test failing, or the pin
still present) — the feature is not actually done; report rather than close on
artifact shape. Blocked is a respectable outcome (`result-contract.md` rule 4).
