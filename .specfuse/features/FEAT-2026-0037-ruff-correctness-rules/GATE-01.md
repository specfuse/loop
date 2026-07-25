---
gate: 1
status: awaiting_review
---

# Gate 1 — Adopt ruff's correctness rule families

Definition of done: `PLW1510`, `B` (bugbear), `BLE001`, `S110`, and `TRY004`
are in `[tool.ruff.lint] select`; every finding they raise across `specfuse/`,
`.specfuse/scripts/`, `tests/`, and `scripts/` is resolved by review;
`ruff check` is clean under ruff 0.16 with the expanded select; and the full
test suite is unchanged and green.

## Arming discipline

Two WUs make new rules block the (already-blocking) lint gate — a severity
increase. Before arming, confirm the escalation-predicate check in PLAN.md
(rules report zero on the corrected final-state tree) and that ruff ≥ 0.16 is
installed in the working venv so the gate enforces the added families. The
`review` autonomy default is load-bearing here: the `subprocess.run` `check=`
decisions are semantic (a wrong `check=True` on an intentional ignore-exit call
changes behavior), so the diff wants human eyes before merge, not auto-close.
