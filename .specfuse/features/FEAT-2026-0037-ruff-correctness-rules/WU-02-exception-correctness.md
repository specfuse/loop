---
id: FEAT-2026-0037/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
model: sonnet
effort: medium
gate_set: code
driver_version: 0.3.24
started_at: 2026-07-25T13:18:51.686121+00:00
duration_seconds: 312.173
cost_usd: 0.826306
input_tokens: 60
output_tokens: 7557
---

# Adopt exception-handling correctness rules (BLE001, S110, TRY004)

**Objective.** Add `BLE001` (blind `except`), `S110` (try-except-pass), and
`TRY004` to the lint `select` and resolve each finding, so swallowed exceptions
are named and justified rather than silent.

**Context.** Part of FEAT-2026-0037, depends on T01 (shares the `[tool.ruff.lint]
select` edit in `pyproject.toml`). Only the **specific** codes are added — not
the whole `S` (bandit) or `TRY` families, which would pull the out-of-scope
`S603`/`S607` and `TRY003` noise. ruff ≥ 0.16 must be the resolved linter.
Binding rules in `.specfuse/rules/` apply.

`Red-test exempt: lint-adoption / correctness-hardening pass, not new feature
behavior (§12 carve-out). Proof is ruff-clean under the added rules + the suite
green.`

**Acceptance criteria.**
- `[tool.ruff.lint] select` additionally includes `"BLE001"`, `"S110"`, and
  `"TRY004"` (specific codes, not whole `S`/`TRY` families).
- `ruff check specfuse .specfuse/scripts tests scripts` (ruff ≥ 0.16) reports
  zero `BLE001`, `S110`, and `TRY004` findings.
- Each `BLE001` blind `except:` / `except Exception:` is fixed by narrowing to
  the specific exception(s) actually expected, or — where catch-all is
  intentional (a top-level driver guard) — by binding the exception and logging
  it, not silently swallowing.
- Each `S110` try-except-pass either handles the exception meaningfully or, if a
  pass is genuinely correct, carries an explicit reason (the rule is satisfied
  by handling, not by blanket `noqa`).
- Each `TRY004` (prefer `TypeError` for wrong-type checks) is fixed on its merit.
- Full suite passes with the same test count as HEAD: `python3 -m unittest
  discover -s tests -q` → `OK`.

**Do not touch.** The subprocess `check=` work from T01 (already done); the ruff
version pin; any file solely to satisfy a non-selected rule. `.git/`, secrets.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates, now also enforcing `BLE001`+`S110`+`TRY004`,
must pass under ruff ≥ 0.16. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if narrowing a blind `except`
would require guessing which exceptions a call can actually raise and the code
gives no signal (a wrong narrowing can let a real error escape) — surface it.
Blocked is respectable (`result-contract.md` rule 4).
