---
feature_id: FEAT-2026-0037
title: Adopt ruff's correctness rule families (subprocess + exception handling)
slug: ruff-correctness-rules
branch: feat/FEAT-2026-0037-ruff-correctness-rules
roadmap_goal: Deliberately opt into ruff 0.16's correctness families — subprocess-run-without-check, bugbear, blind-except, try-except-pass — fixing each finding by review, so the linter catches the silent-subprocess-failure class in a driver that shells out constantly.
autonomy_default: review
status: active                  # active | blocked | deferred | done | abandoned
planned_cost_usd: 17.00
---

# Plan: Adopt ruff's correctness rule families

FEAT-2026-0036 pinned the lint `select` to the classic default to stop ruff
0.16's broadened defaults from breaking CI. This feature reverses that for the
subset that earns it: the **correctness** families. The headline is `PLW1510`
(`subprocess.run` without an explicit `check=`) — in a driver that shells out to
git and gate commands constantly, a subprocess whose non-zero exit is silently
ignored is exactly the "read failure as success" bug class behind hard-to-trace
loop failures (see the FEAT-2026-0036 hollow-pass LEARNINGS). Bugbear (`B`),
blind-except (`BLE001`), try-except-pass (`S110`), and `TRY004` round out the
correctness set. Style/hygiene families are explicitly out (see scope boundary).

Each finding is fixed by **review, not blanket autofix** — `PLW1510` is not
auto-fixable, and the fix is semantic (`check=True` where a silent failure is a
bug; explicit `check=False` only where exit is intentionally handled). The rules
are added to `select` in the same WU that fixes them, so the gate enforces the
family under ruff 0.16 and an unfixed finding cannot pass (the FEAT-2026-0036
lesson: the gate must run the ruleset it is meant to enforce).

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

n/a — no new enforcement mechanism designed. This feature extends the *existing*
ruff `code` gate (`.specfuse/verification.yml`, `ruff check specfuse
.specfuse/scripts tests scripts`) by adding rule codes to `[tool.ruff.lint]
select`. Both ruff and the gate already exist; nothing new is built.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

The added rules make new findings block the (already-blocking) lint gate — a
severity increase. **Zero-on-correct-input holds:** after each WU fixes its
family's findings, `ruff check` with the newly-selected rules reports zero on
the corrected tree (verified in every WU's acceptance and re-run fresh in the
close). The predicate is satisfiable — the rules do not fire on the intended
final state.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0037/T01
        file: WU-01-subprocess-correctness.md
        depends_on: []
      - id: FEAT-2026-0037/T02
        file: WU-02-exception-correctness.md
        depends_on: [FEAT-2026-0037/T01]
      # --- terminal gate: single close WU ---
      - id: FEAT-2026-0037/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0037/T01, FEAT-2026-0037/T02]
```

## Notes

- Single-gate feature (2 substantive WUs ≤ 4): one terminal `close`, no
  intermediate ceremony — proportionality (`docs/methodology.md §6`).
- T01 and T02 both edit `[tool.ruff.lint] select` in `pyproject.toml`; T02
  depends on T01 to serialize that shared edit and keep the gate enforcing.
- Scope OUT: style/hygiene families (`SIM117`/`SIM102`/`ISC`/`C4`/`LOG015`/
  `RUF059`/`PIE`), the broad subprocess-**security** rules (`S603`/`S607` — a
  separate, much larger feature), and rewriting any subprocess *command* (only
  the explicit `check=` is added). No `per-file-ignores` — tests are enforced
  too (a false-green test is on-theme).
