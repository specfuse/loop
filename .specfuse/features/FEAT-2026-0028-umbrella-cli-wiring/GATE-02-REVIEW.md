<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 2 plan-next review — umbrella CLI rewire (interactive / cross-repo)

Drafted by `FEAT-2026-0028/G1-PLAN`. Gate 2 is the **terminal** gate and is
**interactive + cross-repo**: its substantive WUs (T03–T05) are specs for work done by
hand in the `specfuse/specfuse` umbrella repo, verified **there**, not by this loop. This
review is weighted toward doubt: it records the decisions I made on the planner's behalf,
the cross-repo values I could not see and therefore must be checked before arming, and the
open questions a human owns.

## Did I consider the escalation trigger? (Yes — proceed, not block)

WU-91 (G1-PLAN) carries an escalation: *if the umbrella rewire should be its own feature
because the cross-repo verification boundary is too lossy, surface it and emit
`status: blocked` instead of drafting un-verifiable WUs.* I considered it and **chose to
proceed**, because:

- The boundary was a **deliberate design choice made at feature-draft time**, not a
  surprise — PLAN.md's "Decisions" and `GATE-02.md` both pre-declare gate 2 as
  interactive/cross-repo, mirroring FEAT-2026-0019's PyPI gate. The lossiness is *named
  and bounded*, not unbounded.
- G2-CLOSE already has a machine-checkable `## What the loop did NOT verify` criterion
  that enumerates *all of gate 2* as deferred-to-sibling-repo. The audit trail survives.
- Splitting into a new feature would not remove the boundary — the umbrella work lives in
  another repo regardless; it would only add roadmap ceremony.

If you (the human arming this gate) judge the boundary intolerable, the right move is to
abandon gate 2 here and re-cut the umbrella work as a standalone `specfuse/specfuse`
feature. That is a live option, not a defect in these drafts.

## Decisions made on the planner's behalf (with rationale)

| # | Decision | Rationale | WU |
|---|----------|-----------|----|
| D1 | **`cmd_init` drops the init-time `pip install specfuse-loop`** and just calls `scaffold.init`. | The umbrella already hard-depends on `specfuse-loop` (`pyproject` `>=0.2.0`), so `specfuse.loop.scaffold` is importable at runtime — re-installing it at init time was stub-era belt-and-suspenders. | T03 |
| D2 | **`cmd_upgrade` gains a required `target` positional.** | HEAD `cmd_upgrade` takes no target (pip-only). The overlay step needs a repo to act on; `specfuse upgrade <repo>` matches `specfuse init <repo>`. | T04 |
| D3 | **Overlay BEFORE pip-upgrade**, in one process. | A pip-upgrade does not rebind the already-imported `scaffold` module, so overlay-after-pip would apply the OLD seed without a re-exec. Overlay-first applies the current seed now; pip-upgrade means the *next* run overlays newer. WU-91 also specified this order. | T04 |
| D4 | **`--dry-run` previews via a throwaway copy**, not a native `dry_run=` param. | The scaffold API has no dry-run path and adding one is a separate `specfuse-loop` change (OUT of this feature). `init --dry-run` scaffolds into a tempdir (exact — init writes a fresh tree); `upgrade --dry-run` copies the target `.specfuse/` into a tempdir and overlays the copy (exact for the prune/seed logic). Target untouched; tests assert it. | T05 |
| D5 | **`pyproject` dep stays `specfuse-loop>=0.2.0`.** | The bump to `>=0.3.0` belongs to the coordinated PyPI release, explicitly OUT of this feature (PLAN "Decisions"). Named in every WU's "Do not touch". | all |
| D6 | **No `produces:` frontmatter on T03–T05.** | The driver's `produces:` presence gate (`assert_declared_deliverables`) runs against THIS repo's disk; these deliverables (`specfuse/cli.py`, `tests/test_cli.py`) live in the sibling repo. Declaring them would make any accidental in-loop dispatch fail with `deliverable_missing`. Deliverable paths are named in each WU's body instead. Cost: a benign lint WARN per WU (non-blocking). | all |

## If you check only three things before arming

1. **The scaffold signatures these WUs code against are real.** T03/T04 assume
   `scaffold.init(target, *, ci_check=None) -> list[str]` raising `ScaffoldExistsError`,
   and `scaffold.upgrade_specfuse(target, *, ci_check=None) -> list[str]` raising
   `ScaffoldDowngradeError`. Verified against `specfuse/loop/scaffold.py` at draft time
   (lines 297/220/47/51) — re-confirm against the **editable `specfuse-loop` the umbrella
   repo actually imports**, since gate 2 runs later and `main` may have moved.
2. **The overlay-before-pip ordering (D3) is what you want.** It is load-bearing and
   defended on process-import semantics, but if the team prefers "fetch newest seed, then
   overlay it" the WU must re-exec after pip-upgrade — a different shape. Decide before T04
   is built, not after.
3. **The `upgrade --dry-run` copy reproduces the overlay faithfully (D4/T05).** The overlay
   prunes and seeds based on the *target's* existing tree; the preview is only honest if
   the temp copy is a faithful clone. T05's escalation says block rather than ship a
   lying preview — confirm you accept the copy-and-overlay approach over scoping dry-run to
   `init` only.

## Cross-repo contracts (authoring §8 — verify against source before arming)

`plan-next` systematically invents plausible cross-repo values. Every value below was
read from a source at draft time; the **Checked** column is for the arming human to
re-confirm against the editable `specfuse-loop` / umbrella HEAD at gate-2 run time.

| Value | Used in | Authoritative source | Draft-time status | Re-check |
|-------|---------|----------------------|-------------------|----------|
| `scaffold.init(target, *, ci_check=None) -> list[str]` | T03 | `specfuse/loop/scaffold.py:297` | matches | ☐ |
| `ScaffoldExistsError` (exists-refusal) | T03, T05 | `scaffold.py:47` | matches | ☐ |
| `scaffold.upgrade_specfuse(target, *, ci_check=None) -> list[str]` | T04, T05 | `scaffold.py:220` | matches | ☐ |
| `ScaffoldDowngradeError` (downgrade-refusal) | T04, T05 | `scaffold.py:51` | matches | ☐ |
| `PLUGIN_UPDATE_HINT`, `_pip_install(...)` helpers | T03, T04 | `specfuse/specfuse` `cli.py:33,39` | present | ☐ |
| umbrella dep pin `specfuse-loop>=0.2.0` | all (Do-not-touch) | `specfuse/specfuse` `pyproject.toml:25` | matches | ☐ |
| `ci_check` param semantics (currently a no-op, wiring deferred) | T03 | `scaffold.py:76` docstring | "accepted for API compat" | ☐ |

## Open questions (each mapped to a WU)

1. **`--dry-run` preview semantics for `upgrade` (T05).** The copy-and-overlay approach is
   exact but heavier than a native `dry_run=`. *Resolution path:* accept it for this gate;
   file a follow-up loop-repo WU to add `dry_run=` to `scaffold.init`/`upgrade_specfuse`
   (cleaner, removes the temp-copy dance). Do NOT widen this feature to cover it.
2. **Cross-repo verification boundary (all of gate 2 → G2-CLOSE).** The loop verifies only
   the structural lint of these drafts; the real oracle (`pytest tests/test_cli.py`) runs
   in `specfuse/specfuse`. G2-CLOSE's `## What the loop did NOT verify` must enumerate
   this. *Resolution path:* the human who runs T03–T05 in the umbrella repo reports the
   pytest result back into G2-CLOSE's verdict (`met` only if actually built + green there;
   `partial` if only specced).
3. **`cmd_upgrade` re-exec after pip-upgrade (T04, deferred).** If single-run "fetch newest
   seed then overlay it" is wanted, that is a re-exec design beyond D3. *Resolution path:*
   out of scope unless you reject D3 above; otherwise a future enhancement.
4. **`--ci-check` surface (T03).** `scaffold.init`'s `ci_check` is currently a no-op
   (wiring deferred in `specfuse-loop`). T03 threads it for forward-compat. *Resolution
   path:* confirm you want the `--ci-check` flag exposed now vs. passing `None` until the
   scaffold side wires it; either is defensible.

## Roadmap-anchor check

`.specfuse/roadmap.md` §FEAT-2026-0028 "Goal" (line 652) reads: *"Rewire
`specfuse/specfuse` cli.py: `cmd_init` → `scaffold.init(target, ci_check=...)`;
`cmd_upgrade` → `upgrade_specfuse(target)` then the pip-upgrade + plugin hint. Wire
`--dry-run`. Verify against the real (no longer stub) API."* The drafted WUs map 1:1:
T03 = `cmd_init` rewire, T04 = `cmd_upgrade` rewire, T05 = `--dry-run` + real-API test
sweep. No scope drift; no roadmap line left unaddressed by a WU; nothing in the WUs
exceeds the roadmap goal. The docs-in-seed half of the roadmap goal was gate 1 (shipped).

## Arming checklist

- [ ] Re-confirm the seven Cross-repo-contracts rows against the editable `specfuse-loop`
      + umbrella HEAD.
- [ ] Accept or reject D3 (overlay-before-pip ordering) and D4 (dry-run via copy).
- [ ] Decide the `--ci-check` exposure question (open Q4).
- [ ] Flip T03/T04/T05 `draft → pending` (or revise/reject); mark gate 1 `passed`; mark
      gate 2 `open`. The loop driver owns the flips via `arm-gate`.
- [ ] Remember: T03–T05 are built and verified **by hand in `specfuse/specfuse`** — the
      loop will not dispatch them. G2-CLOSE records what the loop could not verify.
