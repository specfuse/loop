# Gate-2 review — drafted by G1-PLAN

Operator's pre-arm review for gate 2 of `FEAT-2026-0027-self-provisioning-driver`
(plugin-config refresh + driver/plugin drift warning). Flip the gate-2 WU
`status: draft` → `pending` only after working the **Open questions** +
**Cross-repo / invented-value contracts** sections below.

> Filename note: this file is `GATE-02-REVIEW.md`, not `GATE-01-REVIEW.md`. The
> G1-PLAN WU body says "GATE-02-REVIEW.md" and that is correct here — the driver's
> `assert_gate_review_exists` computes the expected name from the **next** gate
> (`GATE-{this_gate+1:02d}-REVIEW.md`); for gate-1 plan-next that is
> `GATE-02-REVIEW.md`.

## Gate-1 summary

Gate 1 shipped the **auto-sync engine** as three substantive WUs + the auto-closed
intermediate ceremony (auto-closed on-plan, predicate=v1, no overrun reasons):

- **T01** — `.specfuse/.scaffold-manifest` (sha256 per versioned file) +
  `scaffold.detect_modified` to tell a pristine versioned file from a user-edited one.
- **T02** — `auto_sync` decision tree (create / overlay / no-op / never-downgrade)
  replacing the fail-loud `check_scaffold_version`. ($2.50 planned / $1.33 actual.)
- **T03** — TTY consent prompt + `--no-autosync` flag + `.specfuse/config`
  `autosync: false` toggle. ($2.00 planned / $1.33 actual.)

Gate-1 substantive spend: **$3.47 actual** (the auto-closed gate total). Nothing
forced a re-scope. Gate 2 builds the **plugin-config currency** layer on top of T02's
`auto_sync`.

## The escalation fired — gate 2 collapsed to one substantive WU

G1-PLAN's escalation trigger said: *"If gate 1's retrospective shows 0026's
`wire_claude` already fully covers gate 2's plugin-config scope (leaving only the
drift warning), surface it — gate 2 may collapse to a single WU."* Gate 1 auto-closed
without a detailed retrospective, so I read the code directly
(`specfuse/loop/scaffold.py`, `specfuse/loop/loop.py`). Findings:

- `wire_claude` → `_write_settings_json` (`scaffold.py:210-238`) already writes
  `extraKnownMarketplaces["specfuse"]` + `enabledPlugins["specfuse@specfuse"]`,
  merge-safe.
- `init` **and** `upgrade_specfuse` both call `wire_claude` (`scaffold.py:342,354`),
  and `auto_sync`'s **create** + **older-overlay** branches call those — so those
  branches already refresh the plugin config indirectly.

So the gate-2 scope is genuinely smaller than the skeleton implied. Only **two real
gaps** remain, both folded into one WU (**T04**):

1. **Steady-state runs never refresh.** `auto_sync`'s equal-version branch
   (`loop.py:3544`) returns with no writes — the common every-run case — so a removed
   plugin entry or stale value is never re-asserted.
2. **`_write_settings_json` is additive-only** (`scaffold.py:228-234`): value set
   *only when the key is absent*. A changed `_MARKETPLACE_VALUE` (`scaffold.py:175`)
   between driver versions leaves the project on the stale value — the silent drift
   the roadmap's "warn on driver/plugin drift" was pointing at.

I did **not** pad gate 2 with a second "drift-warning" WU: T04's refresh already
detects+corrects the in-repo drift and warns in the same pass; a separate
non-mutating warning WU would either duplicate T04 or overlap gate 3's `doctor`. The
**cross-process** drift (a pip-installed `specfuse-loop` vs the plugin Claude Code
installed from the marketplace) is **not repo-readable** and is deferred to gate 3's
`doctor` — that is the honest home for it.

## Gate-2 substantive WU (drafted)

### T04 — auto-sync refreshes the `.claude` plugin config + warns on drift ($2.50, high)

New `scaffold.refresh_claude_plugin_config(target) -> list[str]`:
parse-merge-rewrite `.claude/settings.json` so a removed
`enabledPlugins["specfuse@specfuse"]` is restored and a missing-or-**value-drifted**
`extraKnownMarketplaces["specfuse"]` is set to the installed value, preserving every
other key; returns the changed entries. `wire_claude` reuses it (closing the
additive-only gap on init/upgrade too). `auto_sync` calls it on the create / equal /
older-overlaid branches; the newer-refuse + `--no-autosync` / `autosync: false`
opt-outs skip it. A non-empty change list on a non-create run prints a `WARNING:`
naming the drift it corrected. `--dry-run` reports without writing. Red-test:
`tests/test_autosync_plugin.py` (equal-branch refresh + drifted-value correction).
Depends on T03.

Gate-2 closing: `G2-CLOSE-INTERMEDIATE` (WU-92) → `G2-PLAN` (WU-93) — gate 2 is
non-terminal; gate 3 (doctor + first-run + migrate) is terminal with the
pre-scaffolded single `G3-CLOSE`, whose real `depends_on` G2-PLAN will set.

## Roadmap-anchor check

`roadmap_goal`: *"Make a plain specfuse-loop run self-provision the project to the
installed driver version — create/overlay .specfuse/ (never downgrade) + **refresh the
Claude plugin config** — so adoption is 'install global, run anywhere, done'."*

- "refresh the Claude plugin config" → **gate 2 (this draft) covers it.** T04 makes
  the refresh happen on *every* run and corrects value-drift — the gap 0026 left.
- The PLAN forward-arc line for gate 2 also says "warn on driver/plugin version
  drift." T04 warns on the **in-repo** drift it corrects. The **cross-process**
  version drift is deferred to gate 3 `doctor` (PLAN gate-3 scope already names
  "plugin state, drift"). Flag now so the G2-CLOSE-INTERMEDIATE "what the loop did NOT
  verify" doesn't read as a miss.

**Anchor verdict:** gate 2 is on-arc. No `roadmap_goal` change implied. The escalation
fired (collapse to one substantive WU) and is recorded — not drift.

## If you check only three things

1. **Is `extraKnownMarketplaces["specfuse"]` driver-owned or user-owned?** T04's whole
   value-drift correction (AC2) hinges on this being **driver-owned provenance** safe
   to overwrite to the installed value. If a user is expected to hand-edit it, T04
   must escalate instead of clobber. Confirm the intended ownership **before arming**
   — this is the single decision that changes T04's contract (Open question 1).
2. **Refreshing on the equal branch must stay noise-free.** AC4 requires a clean
   (already-current) run to print **nothing** and write **nothing** — the PLAN's
   hard constraint is "no diff noise mid-work" (`PLAN.md:95`). A refresh that
   rewrites `settings.json` with reordered keys on every run would violate it. Verify
   T04's idempotency test asserts byte-stability when current.
3. **The drift warning is not gate 3's `doctor`.** T04 warns on in-repo drift it
   *corrects* during auto-sync; `doctor` (gate 3) *diagnoses* read-only, including the
   cross-process plugin version T04 can't see. Confirm you want both — if `doctor`
   should own all drift messaging, T04's AC4 warning collapses to a one-line notice
   (Open question 3).

## Open questions (mapped to draft WUs)

1. **Marketplace-value ownership (T04 AC2).** Is `extraKnownMarketplaces["specfuse"]`
   driver-owned (T04 overwrites drift → correct) or user-customizable (T04 must
   `status: blocked` rather than clobber)? *Resolve before arming T04.* T04's
   escalation trigger names this explicitly.
2. **Refresh on the never-downgrade branch (T04 AC3).** T04 skips refresh when the
   scaffold is newer than the installed driver (never-downgrade is absolute). Confirm
   that's right — an older driver arguably should not assert *its* (older) plugin
   value over a newer project. Drafted as skip; confirm.
3. **In-repo drift warning vs gate-3 `doctor` (T04 AC4 ↔ gate 3).** Two drift
   surfaces: T04's correct-and-warn (gate 2) and `doctor`'s read-only diagnosis (gate
   3). Decide the division before arming so they don't ship duplicate/contradictory
   messaging. G2-PLAN must carry this into the gate-3 draft.
4. **Coverage ≥ 90 on the new branch (T04 AC6).** `auto_sync` is large; adding the
   refresh calls + warning across five branches must keep coverage green without a
   full-suite run per attempt. T04 names a scoped `tests/test_autosync_plugin.py` red
   run; confirm the `code` gate's coverage threshold is satisfiable for the new lines.

## Cross-repo / invented-value contracts

Per `[FEAT-2026-0003/G3-LESSONS]` + `/authoring-work-units` §8 (verify cross-surface
values against an authoritative source). Each row is operator-checked before arming.

| Invented / contract value | Authoritative source | Used in | Checked |
|---|---|---|---|
| API name `refresh_claude_plugin_config(target) -> list[str]` | invented this gate | T04 AC2, AC6 symbol check | [ ] |
| Marketplace key `specfuse` + value `{source:{source:github,repo:specfuse/specfuse}}` | `scaffold.py:174-180` (`_MARKETPLACE_KEY`/`_MARKETPLACE_VALUE`) | T04 AC2 | [ ] |
| Plugin key `specfuse@specfuse` → `true` | `scaffold.py:181` (`_PLUGIN_KEY`) | T04 AC2 | [ ] |
| settings.json shape (`extraKnownMarketplaces` / `enabledPlugins` / `permissions`) | `scaffold.py:_write_settings_json` (210-238) + a real plugin-enabled `.claude/settings.json` | T04 AC2 | [ ] |
| `--no-autosync` flag + `.specfuse/config` `autosync: false` | gate-1 T03 (`loop.py` main + `auto_sync` opt-out) | T04 AC3 | [ ] |
| `_MARKETPLACE_VALUE` actually *changes* across versions (the drift T04 corrects exists) | git history of `scaffold.py` `_MARKETPLACE_VALUE` | T04 motivation | [ ] |

The last row matters: if `_MARKETPLACE_VALUE` has never changed and never will, the
value-drift half of T04 is dead code — confirm there is a realistic version in which
it differs (e.g. the marketplace repo/ref moving) before arming, or scope T04 to the
removed-entry-restore case only.

## Predicate-version note

Cost figures cited are predicate=v1. Gate-2 WU `planned_cost_usd` totals **$6.50**:
substantive **$2.50** (T04) + closing **$4.00** (G2-CLOSE-INTERMEDIATE $1.50 + G2-PLAN
$2.50). The single-substantive-WU gate is the deliberate result of the escalation, not
under-planning. The PLAN.md feature-level `planned_cost_usd` ($11.50) was the draft-time
whole-feature estimate; with gates 2–3 now carrying per-WU costs the sum-of-WUs diverges,
so the lint planned-cost WARN is expected and informational, not an error. Leaving the
feature-level figure as-is preserves the original estimate for cost-variance calibration.
