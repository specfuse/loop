# Gate-3 review — drafted by G2-PLAN

Operator's pre-arm review for gate 3 of `FEAT-2026-0027-self-provisioning-driver`
(terminal: `specfuse doctor` + first-run scaffold prompt + legacy `scripts/`/`skills/`
migration-prune). Flip the gate-3 WU `status: draft` → `pending` only after working the
**Open questions** + **Cross-repo / invented-value contracts** sections below.

> Filename note: this file is `GATE-03-REVIEW.md`. The driver's
> `assert_gate_review_exists` computes the expected name from the **next** gate
> (`GATE-{this_gate+1:02d}-REVIEW.md`); for a gate-2 plan-next that is
> `GATE-03-REVIEW.md`, even though the authoring WU (`G2-PLAN`) lives in gate 2.

## Gate-2 summary

Gate 2 shipped the **plugin-config currency** layer as a single substantive WU (the
escalation in `GATE-02-REVIEW.md` collapsed it from the skeleton's implied two):

- **T04** — `scaffold.refresh_claude_plugin_config` (parse-merge-rewrite
  `.claude/settings.json`: restore a removed `enabledPlugins["specfuse@specfuse"]`,
  correct a **value-drifted** `extraKnownMarketplaces["specfuse"]`, preserve every other
  key) + `auto_sync` calls it on create / equal / older-overlay, warns on the in-repo
  drift it corrects, stays read-only under `--dry-run`. ($2.50 planned / $1.48 actual,
  1 attempt.) Verified at draft time: `scaffold.py:233`, `loop.py:3477`.

T04 closed the **in-repo** drift (project `.claude/settings.json` vs what the driver
writes). It explicitly deferred the **cross-process** drift (a pip-installed
`specfuse-loop` vs the plugin Claude Code installed from the marketplace) to gate 3's
`doctor` — that boundary is the spine of T05 below.

## Gate-3 substantive WUs (drafted)

Three independent WUs, each depending on T04 (plugin-refresh + version surfaces).

### T05 — `specfuse doctor` read-only diagnosis ($2.50, high)
`scaffold.doctor(target, *, installed_driver_version, plugins_manifest_path=None) ->
dict`. **Writes nothing.** Reports scaffold-version status (current / behind / ahead /
none), in-repo plugin drift (a **dry-run** `refresh_claude_plugin_config` delta), the
cross-process installed plugin version (best-effort from
`~/.claude/plugins/installed_plugins.json`, `None` when absent), and a recommended
action. The read-only counterpart to T04's correct-and-warn.

### T06 — first-run scaffold prompt ($2.00, medium)
Gates `auto_sync`'s **create** branch (`loop.py:3514`, today unconditional) behind a TTY
`[Y/n]` confirm before self-provisioning a fresh repo; decline aborts with no writes +
opt-out guidance; non-TTY proceeds with a notice (CI never blocks). Reuses T03's consent
pattern (`loop.py:3586`). Single-repo, fully loop-dispatchable.

### T07 — legacy `scripts/`/`skills/` migration-prune ($2.50, high)
`scaffold.migrate_legacy(target, *, dry_run=False) -> list[str]`. Prunes redundant legacy
`.specfuse/scripts/` + `.specfuse/skills/` copies driven by an **explicit keep-list**;
the keep-list is a hard guard (refuse, don't delete) and includes the live shims
`.specfuse/verification.yml` still calls. The cross-repo `specfuse init --migrate` wires
it. **Highest-risk WU of the gate** — see Open question 2.

Gate-3 closing: the pre-scaffolded single **`G3-CLOSE`** (WU-90-gate-3-close.md) — gate 3
is **terminal**, so it keeps the one-WU `close` (RETRO+LESSONS+DOCS+verdict folded), not a
close-intermediate/plan-next pair. Its `depends_on` is now `[T05, T06, T07]`.

## Roadmap-anchor check

`roadmap_goal`: *"Make a plain specfuse-loop run self-provision the project to the
installed driver version — create/overlay .specfuse/ (never downgrade) + refresh the
Claude plugin config — so adoption is 'install global, run anywhere, done'."*

- "install global, **run anywhere, done**" → **T06** is the missing safety affordance:
  self-provisioning a fresh repo should confirm on a TTY, not surprise the user.
- "refresh the Claude plugin config" was gate 2 (T04); **T05 `doctor`** adds the
  read-only diagnosis the PLAN gate-3 scope names ("plugin state, drift, recommended
  action"), including the cross-process drift T04 structurally can't see.
- **T07 (migration-prune)** is the one item that is *not* directly in the `roadmap_goal`
  sentence — it traces to PLAN.md:37-39 ("the legacy `scripts/`/`skills/`
  migration-prune is IN (gate 3)") and the `init.sh` v1.1 removal arc. On-arc per the
  PLAN, not per the one-line goal. **Flag:** if the operator considers migration-prune
  out of this feature's spine, T07 is the WU to cut/defer — it is the most separable.

**Anchor verdict:** gate 3 is on-arc. No `roadmap_goal` change implied. Gate 3 is terminal;
after `G3-CLOSE` the feature is done and `init.sh`'s v1.1 deletion is unblocked (a
follow-on operator step, not a WU here).

## If you check only three things

1. **Can `doctor` actually read the Claude-Code-installed plugin version? Partially.**
   Verified at draft: `~/.claude/plugins/installed_plugins.json` exists, is readable, and
   carries `plugins["specfuse@specfuse"][].version`. BUT — it is **not repo-readable**
   (absent under CI/sandbox) **and for a marketplace plugin the `version` is a git commit
   SHA, not a semver** (observed: `caveman@caveman` → `"655b7d9c5431"`). So `doctor`
   cannot *order* the plugin version against `DRIVER_VERSION` — it reports the identifier
   opaquely and degrades to `unknown` when the manifest is absent. T05 is drafted to
   degrade gracefully, **not** to block. Confirm you accept a **partial** cross-process
   diagnosis before arming (Open question 1).
2. **T07's keep-list is the entire correctness surface — confirm it before arming.**
   `.specfuse/verification.yml` calls `.specfuse/scripts/lint_plan.py` (plannext gate) and
   `.specfuse/scripts/leak_scan.py` (code gate); both are **live shims**. A blanket prune
   of `.specfuse/scripts/` breaks the loop's own gates. T07 is drafted keep-list-guarded
   with a hard refuse, and its escalation blocks if the keep-list can't be enumerated
   exhaustively. **Do not arm T07 until the keep-list is operator-confirmed** (Open
   question 2).
3. **First-run decline semantics (T06).** Declining the prompt must abort the *create*
   only — not silently suppress a later run phase. Confirm the create branch's return
   path doesn't feed run-level control flow in a way that makes "decline" mean "abort the
   whole run" unexpectedly. T06 escalates if that coupling exists (Open question 3).

## Open questions (mapped to draft WUs)

1. **Partial plugin diagnosis (T05).** The cross-process plugin version is best-effort
   (home-readable only, SHA-valued, absent in CI). Accept a partial diagnosis that prints
   `unknown` when the manifest is missing and never orders SHA-vs-semver? Drafted as
   degrade-gracefully. *The brief's escalation said: if `doctor` can't read the version,
   surface it here rather than ship a silently-degrading WU — surfaced.* Confirm before
   arming.
2. **Migration-prune keep-list (T07).** What is the exhaustive set of
   `.specfuse/scripts/` / `.specfuse/skills/` paths the loop still depends on? Draft-time
   scan of `verification.yml` found `lint_plan.py` + `leak_scan.py`; the `.specfuse/scripts/`
   tree also holds `_miniyaml.py`, `leak_scan_content.py`, `validate-event.py`,
   `adopt_feature.py`, `gate_eval.py`, `gh_backend.py`, `gh_features.py`,
   `leak_denylist.{txt,hashes}`, `loop.py` — several are shims/support the loop may invoke
   indirectly. **Resolve the full keep-list before arming T07.** T07's escalation blocks
   rather than blanket-prune.
3. **First-run decline = abort create vs abort run (T06).** Drafted: decline skips create
   and returns; the run proceeds/exits as it would with no scaffold. Confirm that matches
   intended UX (vs. decline = hard-exit the whole `specfuse-loop` invocation).
4. **Skill symlink vs copy on prune (T07).** This source repo's `.specfuse/skills/*` are
   **symlinks** (per `.claude/CLAUDE.md`); a consumer's legacy copies may be real files.
   T07 must prune the link entry, never follow-and-delete a target outside `.specfuse/`.
   Confirm the prune treats symlinks correctly across both shapes.
5. **Does the `/specfuse:*` plugin fully cover the pruned skills (T07)?** Migration-prune
   assumes every skill removed from `.specfuse/skills/` is provided by the plugin. If a
   skill exists locally but not in the marketplace plugin, pruning it leaves a capability
   gap. T07's escalation blocks on a missing-skill gap; confirm parity is expected.

## Cross-repo / invented-value contracts

Per `[FEAT-2026-0003/G3-LESSONS]` + `/authoring-work-units` §8 (verify cross-surface
values against an authoritative source; this blind spot is systematic in `plan-next`
drafts). Each row is operator-checked before arming.

| Invented / contract value | Authoritative source | Used in | Checked |
|---|---|---|---|
| CLI subcommand name `specfuse doctor` | cross-repo `specfuse/specfuse` CLI (FEAT-2026-0026/0028) — **verify, not invent** | T05 (CLI hook, out of loop scope) | [ ] |
| CLI flag `specfuse init --migrate` | cross-repo `specfuse/specfuse` CLI — **verify, not invent** | T07 (CLI hook, out of loop scope) | [ ] |
| API name `doctor(target, *, installed_driver_version, plugins_manifest_path=None) -> dict` | invented this gate | T05 AC2, symbol check | [ ] |
| API name `migrate_legacy(target, *, dry_run=False) -> list[str]` | invented this gate | T07 AC2, symbol check | [ ] |
| Plugin manifest path `~/.claude/plugins/installed_plugins.json` + key path `plugins["specfuse@specfuse"][].version` | verified present on draft host; **Claude-Code-owned schema, may change** | T05 AC2/AC3 | [ ] |
| Plugin `version` is a git SHA (not semver) for marketplace plugins | observed in the live manifest (`caveman@caveman` → SHA) | T05 AC4 (no SHA-vs-semver ordering) | [ ] |
| Live shims that MUST survive prune: `.specfuse/scripts/lint_plan.py`, `.specfuse/scripts/leak_scan.py` | `.specfuse/verification.yml` (plannext + code gates) | T07 AC2/AC3 keep-list | [ ] |
| `_MARKETPLACE_VALUE` / `_PLUGIN_KEY` shape | `scaffold.py:174-181` | T05 AC2 (in-repo drift via dry-run refresh) | [ ] |
| `--no-autosync` flag + `.specfuse/config` `autosync: false` | gate-1 T03 (`loop.py` main + `auto_sync` opt-out) | T06 AC5 | [ ] |

The first two rows are the gate's biggest exposure: `doctor` and `--migrate` are
**cross-repo CLI surfaces this repo does not own**. The drafted WUs ship only the
loop-dispatchable scaffold API (mirroring how `init`/`upgrade` are API functions wired
from the cross-repo CLI); the subcommand/flag wiring belongs to `specfuse/specfuse` and
must be confirmed there, not invented in this gate.

## Predicate-version note

Cost figures cited are predicate=v1. Gate-3 WU `planned_cost_usd` totals **$8.50**:
substantive **$7.00** (T05 $2.50 + T06 $2.00 + T07 $2.50) + terminal close **$1.50**
(G3-CLOSE). The PLAN.md feature-level `planned_cost_usd` ($18.00) was the draft-time
whole-feature estimate; with per-WU costs now carried on all three gates the sum-of-WUs
diverges, so the lint planned-cost WARN is expected and informational, not an error.
Leaving the feature-level figure as-is preserves the original estimate for cost-variance
calibration in `G3-CLOSE`'s cost analysis.
