---
id: FEAT-2026-0037/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 8.00
---

# Adopt subprocess-correctness rules (PLW1510 + bugbear); make `check=` explicit

**Objective.** Add `PLW1510` and `B` (flake8-bugbear) to the lint `select`, then
resolve every finding — chiefly making `subprocess.run` calls declare `check=`
explicitly by reviewing each call site — so the gate catches silently-ignored
subprocess failures.

**Context.** Part of FEAT-2026-0037, first WU. The lint gate is `ruff check
specfuse .specfuse/scripts tests scripts` (`.specfuse/verification.yml`); the
selected ruleset lives in `pyproject.toml` `[tool.ruff.lint] select` (currently
`["E4","E7","E9","F"]`, pinned by FEAT-2026-0036). `PLW1510` is **not**
auto-fixable and its fix is semantic. ruff ≥ 0.16 must be the resolved linter.
Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`)
apply. Do not restate them.

`Red-test exempt: lint-adoption / correctness-hardening pass, not new feature
behavior (§12 carve-out). Proof is ruff-clean under the added rules + the full
suite still green, not a single red→green test. NOTE: adding check=True DOES
change runtime behavior (raises on non-zero); the suite is the regression oracle
and each call site is reviewed for intent — see Acceptance.`

**Acceptance criteria.**
- `[tool.ruff.lint] select` in `pyproject.toml` includes `"PLW1510"` and `"B"`.
- `ruff check specfuse .specfuse/scripts tests scripts` (ruff ≥ 0.16) reports
  zero `PLW1510` and zero `B` findings — quote `ruff --version` and the clean
  result.
- Every `subprocess.run` flagged by `PLW1510` has an **explicit** `check=`:
  `check=True` where a non-zero exit indicates a real failure the caller should
  not proceed past; `check=False` **only** where the code already inspects
  `.returncode` (or the failure is deliberately tolerated) — with the existing
  handling visible at the call site. No call is left implicit.
- Each `check=True` added is confirmed **not** to break an intentional
  ignore-exit path: the full suite passes with the SAME test count as HEAD
  (`python3 -m unittest discover -s tests -q` → `OK`), and any call that
  previously relied on continuing past a non-zero exit was given `check=False`,
  not `check=True`.
- Bugbear (`B`) findings (e.g. `B017` assert-raises-Exception, `B602`/`B603`/
  `B604` subprocess-shell) are fixed on their merits, not silenced with `noqa`.
- No style/hygiene rule was added to `select` (that's out of scope); no
  subprocess *command* string was changed (only `check=` added).

**Do not touch.** The subprocess command strings / argv themselves; the ruff
version pin (leave `ruff>=0.6`); any file solely to satisfy a non-selected rule.
`.git/`, secrets. The driver owns git. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` (tests,
coverage, warnings, lint, security), now enforcing `PLW1510`+`B` via the updated
select, must pass under ruff ≥ 0.16. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if a `subprocess.run` call's
correct `check=` value is genuinely ambiguous (the intent of ignoring vs
enforcing exit is unclear and no test or comment settles it) — guessing
`check=True` could change behavior; surface it for a human decision. Also block
if adding `check=True` anywhere makes a previously-passing test fail and the
right resolution isn't obviously `check=False` (it may be a latent real bug the
rule just exposed — report, don't paper over). Blocked is respectable
(`result-contract.md` rule 4).
