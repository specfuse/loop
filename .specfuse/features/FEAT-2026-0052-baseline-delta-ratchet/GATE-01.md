---
gate: 1
status: open
cost_budget_usd: 31.00
---

# Gate 1 — Baseline-delta ratchet, waiver, and tracking-issue emission

Definition of done: an operator facing a `preexisting_gate_failure` halt has a
third exit. `--waive-baseline` records a durable, sha-pinned waiver in the gate
file; the run proceeds; every failure already in the recorded baseline stops
blocking work units; every failure beyond it still fails normally; the waived
debt is filed as a `waived-baseline` GitHub issue (or the exact
`gh issue create` command is printed when `gh` is unreachable); and both the halt
message and the proceed message say all of this in plain English.

## Arming discipline

- **The escalation-predicate check in PLAN.md is the arming evidence, in both
  directions.** With no waiver present, WU classification must be byte-identical
  to today (T01's no-waiver test). With a waiver present, a newly-introduced
  failure must still fail (T01's red test). Neither is a claim to accept at
  arming — both are named tests in T01's acceptance.
- **This lowers a severity conditionally, so §4's runtime-probe rule applies.**
  Before arming, confirm this repo's `code` gates are green on the feature's base
  commit. A red base tree here means the driver halts on 0051's own probe at gate
  entry — correct behavior, and the exact situation this feature is about, but a
  confusing first encounter while the waiver does not yet exist.
- **Know the recovery path before starting:** `--no-baseline-probe` (0051/T02)
  disables the probe entirely and returns the driver to pre-0051 behavior. It
  weakens no gate. If the ratchet misfires mid-feature, that flag — not a hand-
  edited gate file — is the way out.
- **Exactly one WU carries `unsandboxed: true`.** T03 needs a live `gh` round
  trip. Per the CORRECTED LEARNINGS entry
  `[FEAT-2026-0014/T01/gh-claudeP-broken]`, that flag is the right lever and the
  escape is confined to the single WU that needs it. **A second WU wanting the
  flag is an escalation, not a copy-paste.**

The `review` autonomy default is load-bearing. A bug in a pre-dispatch halt does
not fail loudly — it silently stops work from being dispatched. A bug in a
*ratchet* is worse in the opposite direction: it silently lets work through. Both
want human eyes on the diff, not auto-close.
