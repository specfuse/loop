## Gate 1 — auto-closed (predicate=v1)

On-plan intermediate close; full close-intermediate ceremony
skipped per `evaluate_auto_close`. `plan-next` WU dispatched
to draft gate 2.

- feature_id: FEAT-2026-0027
- predicate_version: v1
- gate_total_cost: $3.47
- gate_budget: <unset>
- reasons: [] (auto=True)

## Gate 2 — auto-closed (predicate=v1)

On-plan intermediate close; full close-intermediate ceremony
skipped per `evaluate_auto_close`. `plan-next` WU dispatched
to draft gate 3.

- feature_id: FEAT-2026-0027
- predicate_version: v1
- gate_total_cost: $1.48
- gate_budget: <unset>
- reasons: [] (auto=True)

## Gate 3 — doctor + first-run + migrate (terminal, completed interactively)

Gate 3 shipped the operator-facing self-provisioning surfaces (loop-dispatchable API
side; the cross-repo `specfuse` CLI exposure is FEAT-2026-0028-style follow-on):

- **T05** — `scaffold.doctor()`: read-only diagnosis (driver vs scaffold version, in-repo
  plugin-config drift, best-effort cross-process plugin version). 2 attempts.
- **T06** — first-run consent prompt gating `auto_sync`'s create branch (TTY confirm /
  non-TTY proceed / opt-outs). 1 attempt (post-fix).
- **T07** — `scaffold.migrate_legacy()`: prune legacy `.specfuse/scripts/` + `.specfuse/skills/`,
  keep-set derived from the target's verification.yml + settings.json, refuse-if-unparseable.
  1 attempt.

The terminal close (G3-CLOSE) was dispatched but killed by another concurrent session
mid-write; completed by hand here (no leak, no crash — just an external interrupt).

### Cost analysis
Planned substantive (PLAN.md): T05 $2.50 + T06 $2.00 + T07 $2.50 = $7.00. Actual per-WU
spend is understated in this record because gate-3's `events.jsonl` history was reverted
during the run to clear a leak-scan self-poison (see below), so the non-passing attempts
(T05's leak rejection, T06's hang + leak) are no longer in the event log. The real cost
ran higher than plan due to that robustness battle — captured qualitatively here rather
than as clean per-WU deltas.

### What the loop did NOT verify
- **Cross-process plugin version** (T05 doctor): `~/.claude/plugins/installed_plugins.json`
  is home-only (absent in CI/sandbox) and SHA-valued — `doctor` reports it opaquely /
  `unknown`; not exercised against a real installed plugin in-loop.
- **First-run prompt against a real TTY** (T06): tests mock `isatty`/`input`; the real
  interactive prompt is not exercised by the loop sandbox.
- **A real legacy-repo migration** (T07): `migrate_legacy` is tested against `tmp_path`
  fixtures; pruning an actual old-init.sh consumer repo is an operator action.
- **Per-WU cost reconciliation**: gate-3 event history was reverted (leak self-poison
  cleanup), so the clean planned-vs-actual table is unavailable for this gate.

### Robustness battle (drove fixes, landed on this branch / filed)
Gate 3 surfaced and fixed real driver-resilience gaps:
- leak-scan `Path.home` false-positive → fixed (#73, `d858f3e`); filed the systemic
  self-poison (#76) + the unhandled bookkeeping-commit crash (#75).
- gate verify could hang forever → fixed: `stdin=DEVNULL` + process-group kill (`79f2162`).
- arm-gate edits wiped by `reset --hard` (#74) + the broader uncommitted-state-loss
  class (#71) — observed, filed, committed the arm durably as the workaround.

## Terminal verdict — verdict: met

The self-provisioning driver is delivered: `auto_sync` version-syncs `.specfuse/` on every
run (create/overlay/no-op/never-downgrade, manifest-based edit detection, TTY-aware
consent + opt-outs), refreshes the `.claude` plugin config, and `doctor` / first-run /
`migrate_legacy` round out the operator surfaces. Goal ("install global, run anywhere")
met to the limit the loop can verify; the deferred items above are operator/CI/cross-repo.
Notably, gate 3 also hardened the loop itself (gate-hang + leak-scan fixes) — those plus
the remaining filed issues (#71/#72/#74/#75/#76/#46) are the pre-release cleanup batch.
