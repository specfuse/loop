## Gate 1 — auto-closed (predicate=v1)

On-plan close; full retrospective ceremony skipped per
`evaluate_auto_close`.

- feature_id: FEAT-2026-0031
- predicate_version: v1
- gate_total_cost: $3.78
- gate_budget: <unset>
- reasons: [] (auto=True)

---

*Everything below is operator-authored after the fact. The gate auto-closed, so
`G1-CLOSE` never dispatched (`attempts: 0`, `auto_close: true`) and none of its
acceptance criteria ran. These sections are what that WU's body called for; they are
recorded here because the deferred-verification list matters independently of whether
a reflection session happened. See LEARNINGS `[FEAT-2026-0031/G1-CLOSE]`.*

## Cost analysis

| WU | Planned | Actual | Delta |
|---|---|---|---|
| T01 — resolver + lint | $1.20 | $1.40 | +$0.20 |
| T02 — branch cut + staleness guard | $1.60 | $1.16 | −$0.44 |
| T03 — PR base + runner routing | $1.20 | $1.22 | +$0.02 |
| G1-CLOSE | $1.50 | $0.00 | −$1.50 (auto-closed, never dispatched) |
| **Total** | **$5.50** | **$3.78** | **−$1.72** |

Substantive WUs came in at $3.78 against $4.00 planned — a 5.5% underspend, i.e. the
per-WU estimates were essentially accurate. The entire headline delta is the close WU's
unspent $1.50, which is an artifact of auto-close, not of estimation. Worth noting for
future planning: a single-gate feature that stays on-plan will systematically underrun
its planned total by the close WU's estimate, because `evaluate_auto_close`'s per-WU
ratio check measures against `planned_cost_usd` and honest estimates make the predicate
fire. All three WUs passed on attempt 1; no spinning, no re-arms, no escalations.

## What the loop did NOT verify

Two entries — both from T03, both known and declared at draft time, neither discovered
late. At the >2 sizing threshold, so this does not flag the single-gate sizing.

1. **Live `gh pr create --base <base>` against a real repo.** Deferred because `gh`
   returns auth errors inside `claude -p` (the documented `gh`↔claude-p bug, LEARNINGS
   `FEAT-2026-0020/G1-CLOSE-INTERMEDIATE`). The in-loop oracle was a stub-`_runner`
   argv assertion — it proves the call shape, not that a real PR targets correctly.
   Verified by the operator post-merge; this feature's own PR is the first live case.
2. **`wrap-feature` prose producing a correctly-targeted PR.** The skill's PR command
   is agent-followed markdown; the in-loop check was a grep that the text names
   `--base`. A grep proves the instruction is written, not that an agent obeys it.
   Verified when an operator next wraps a feature declaring a `base:`.

Both gaps are confined to the `gh` surface. The base resolution itself — `resolve_base`,
`ensure_base_ref`, and the branch cut — was verified in-loop against real git in a
tmpdir (28 tests), including the configured-base path (`feat/x` cut from `release/2.0`),
the no-base fallback (`feat/no-base` cut from `main`), and the Q3 fetch-on-miss path.

## What I'd change

- **Sizing: correct.** 3 substantive WUs, single gate, all green on attempt 1. The
  deferred list is 2 entries and both were predicted at draft time, which is the signal
  that the gate was scoped to what the loop could actually verify.
- **The close WU was mis-planned, not mis-sized.** Its body carried deliverables that
  matter regardless of reflection quality (the deferred-verification list above), and
  auto-close voided them. Those belonged in a substantive WU, or should have been
  written by hand from the start. This is now a durable lesson rather than a one-off.
- **The `gh pr view` bypass should have been caught by a test, not by reading.** It was
  found while drafting T03 by inspecting the module. A seam audit (grep for direct
  `subprocess.run` in a runner-injected module) would have surfaced it mechanically.
