## Gate 1 — auto-closed (predicate=v1)

On-plan intermediate close; full close-intermediate ceremony
skipped per `evaluate_auto_close`. `plan-next` WU dispatched
to draft gate 2.

- feature_id: FEAT-2026-0028
- predicate_version: v1
- gate_total_cost: $2.96
- gate_budget: <unset>
- reasons: [] (auto=True)

## Gate 2 — umbrella CLI rewire (interactive, cross-repo)

Completed interactively against the `specfuse/specfuse` repo (commit `3f7d812` there),
since the loop driver cannot dispatch a sibling repo. T03/T04/T05:

- **T03** — `cmd_init` → `scaffold.init(target, ci_check)`; writes `.specfuse/` + `.claude`;
  `ScaffoldExistsError` → non-zero pointing at `specfuse upgrade`; curl-bash removed.
- **T04** — `cmd_upgrade` → `scaffold.upgrade_specfuse(target)` BEFORE the pip-upgrade;
  `ScaffoldDowngradeError` → non-zero, no pip (never-downgrade honored).
- **T05** — both subcommands gained `--dry-run` (temp-dir preview, writes nothing, no
  pip) + `--ci-check`; `test_cli.py` rewritten against the real scaffold API.

Verified in the umbrella repo: 11 tests green, ruff clean, and an end-to-end smoke —
`specfuse init <repo>` lays a full `.specfuse/` (incl. `docs/`) + `.claude/` (CLAUDE.md,
settings.json plugin config); `upgrade --dry-run` previews without touching the target.

## Cost analysis

Gate 1 substantive: planned $3.50 (T01 1.50 + T02 2.00) vs actual ~$2.96 (gate total) —
under plan (T01 took 2 attempts but stayed within). Gate 2 was interactive (cost folded
into the live session, not per-WU tracked). No predicate overruns; gate 1 auto-closed.

## What the loop did NOT verify

- **All of gate 2 (T03/T04/T05).** The umbrella CLI rewire was authored, tested, and
  smoke-verified in the `specfuse/specfuse` repo (11 tests, ruff, end-to-end init/upgrade
  smoke) — NOT in this loop run. The loop verified only the structural lint of the gate-2
  drafts. Evidence: `specfuse/specfuse` commit `3f7d812`.
- **The coordinated PyPI release.** Versions/dep-pin intentionally NOT bumped here;
  `specfuse-loop` v0.3.0 + `specfuse` release is the post-FEAT-2026-0027 step.

## Terminal verdict — verdict: met

`specfuse init`/`upgrade` now scaffold end-to-end (umbrella CLI calls the
`specfuse.loop.scaffold` API) and docs ship in the pip seed — delivered and verified
(gate 1 in-loop; gate 2 in the umbrella repo with passing tests + an end-to-end smoke).
Downstream + out of scope: the coordinated release (post-0027) and init.sh's v1.1
deletion. Follow-up: add native `dry_run=` to `scaffold.init`/`upgrade_specfuse`
(cleaner than the CLI's temp-copy preview).
