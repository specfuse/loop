---
id: FEAT-2026-0037/G1-CLOSE
type: close
status: done
attempts: 2
planned_cost_usd: 5.00
auto_close_disabled: true
verdict: met
duration_seconds: 1029.663
cost_usd: 4.874997
input_tokens: 1517
output_tokens: 51439
---

# Gate 1 close — Adopt ruff's correctness rule families

**Objective.** Terminal close: re-run the oracles fresh, record retrospective +
lessons + docs note + verdict in one session, and confirm the correctness
families are genuinely enforced and clean — not artifact-shaped.

**Context.** Terminal close of FEAT-2026-0037. Depends on T01 (subprocess) and
T02 (exceptions). Binding rules in `.specfuse/rules/` (`result-contract.md`,
`close-discipline.md`) apply. The driver owns the terminal `PLAN.md status ->
done` flip — do NOT add a status-flip acceptance criterion.

**Acceptance criteria.**
- A `## Retrospective` section: how many `PLW1510`/`B`/`BLE001`/`S110`/`TRY004`
  findings were fixed, how many `subprocess.run` calls took `check=True` vs
  `check=False`, and any that were genuinely ambiguous; plus `## What I'd change`.
- A `## Lessons` section with any durable rule worth promoting to
  `.specfuse/LEARNINGS.md` — e.g. whether `check=False` call sites revealed a
  latent bug, or a pattern for deciding `check=` intent.
- A `## Docs` note: confirm whether any contributor doc should mention the
  expanded lint ruleset, or name the doc touched.
- A `## Cost analysis` section reconciling `planned_cost_usd` (PLAN + per-WU)
  against actual spend (events.jsonl), delta named.
- A `## What the loop did NOT verify` section enumerating any deferred criterion
  (with why + where it actually happens); required even when empty — write
  `(nothing — every acceptance criterion was verified in-loop)`.
- **Oracles re-run fresh** (close-discipline §1): `ruff --version` (≥ 0.16) and
  `ruff check specfuse .specfuse/scripts tests scripts` exit 0 with the expanded
  select, read directly (not from T01/T02 self-report); `python3 -m unittest
  discover -s tests -q` reports `OK`; the `[tool.ruff.lint] select` in
  `pyproject.toml` contains all five added codes.
- **Consumer-visible contract changes** (§3): `n/a — no consumer-visible
  contract change` (a dev-lint ruleset change plus behavior-preserving `check=`
  additions; no API/CLI/scaffold surface moved).

**Do not touch.** Source and test files (T01/T02 own those), `.git/`, secrets.
This WU writes only its close record. The driver owns git and the terminal PLAN
flip. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext`/close gates plus a fresh re-run of the oracles
above. See `.specfuse/skills/verification/SKILL.md`. On a hedged outcome, record
the follow-up per close-discipline §2.

**Escalation triggers.** Emit `status: blocked` if a fresh oracle re-run
disagrees with T01/T02's self-report (any selected rule still firing, a test
failing, or a code missing from `select`) — report rather than close on artifact
shape. Blocked is respectable (`result-contract.md` rule 4).
