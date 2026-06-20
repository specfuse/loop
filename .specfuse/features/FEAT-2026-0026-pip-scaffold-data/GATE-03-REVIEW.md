# Gate-3 review — drafted by G2-PLAN

Operator's pre-arm review for gate 3 of `FEAT-2026-0026-pip-scaffold-data`
(`specfuse upgrade` + the `init.sh` thin shim). Gate 3 is **terminal**. Flip each gate-3 WU
`status: draft` → `pending` only after working the **Open questions** + **Cross-repo /
invented-value contracts** sections below.

> Filename note: this file is `GATE-03-REVIEW.md`. The driver's `assert_gate_review_exists`
> computes the expected name from the **next** gate — `GATE-{this_gate+1:02d}-REVIEW.md`. For
> gate-2 plan-next (this WU) that is `GATE-03-REVIEW.md`. (Gate 2's review hit the symmetric
> case: G1-PLAN's body said `GATE-01-REVIEW.md` but the driver wanted `GATE-02-REVIEW.md`.)

## Gate-2 summary

Gate 2 shipped the **write path** (`specfuse init`) as three substantive WUs + the
auto-closed intermediate ceremony:

- **T04** — `specfuse.loop.scaffold.init_specfuse(target, *, ci_check=None)`: writes a fresh
  `.specfuse/` (templates, rules, VERSION, seeded roadmap/LEARNINGS/verification.yml, empty
  `features/`) from T02's resource API; refuses (`ScaffoldExistsError` → points at
  `specfuse upgrade`) if `.specfuse/` exists; byte-faithful to `read_scaffold`. (1 attempt,
  $0.68 actual / $2.50 planned.)
- **T05** — `wire_claude(target)` + `.gitignore` writer: runtime-artifact ignore lines,
  CLAUDE.md `@rules` block, the **pip-command** settings allowlist (`specfuse-loop:*` /
  `specfuse-lint:*`, OQ3 resolved), and the Claude Code plugin config
  (`extraKnownMarketplaces`/`enabledPlugins`, exact shape pinned against the docs, OQ2
  resolved) — all merge-safe; no symlinks (the plugin replaces the bridge). Also added the
  `init(target)` orchestrating entry point (OQ6 resolved). (1 attempt, $0.88 / $2.50.)
- **T06** — end-to-end init integration test against a `tmp_path` repo + installed-wheel leg
  (skip-guarded). (1 attempt, $1.01 / $2.00.)

Gate-2 substantive spend: **$2.57 actual vs $7.00 planned** (auto-closed on-plan,
predicate=v1, no overrun reasons). The write path landed cleanly in one attempt each;
nothing forced a re-scope. **Gate 3 builds the overlay path (`upgrade`) on T04's writer and
T05's wiring, then shrinks `init.sh` to a shim** — closing the init.sh-replacement arc.

## Gate-3 substantive WUs (drafted)

### T07 — `specfuse upgrade` core overlay ($2.50, high)

`upgrade_specfuse(target, *, ci_check=None)`: overlays the versioned seed (`templates/`,
`rules/`, `verification.yml.example`) onto an **existing** `.specfuse/`, stamps `VERSION`,
seeds missing user-authored files, prunes removed-versioned files (scoped to the versioned
footprint), refreshes `.claude` via `wire_claude`, and is **version-gated / never-downgrade**
(`ScaffoldDowngradeError` if installed seed < target VERSION). Preserves user-authored files.
Depends on T04. Two deliberate divergences from `init.sh --upgrade` — smaller versioned
footprint (no `skills/`/`scripts/`/`docs/`) and a new never-downgrade gate — are called out
in the contracts table.

### T08 — `init.sh` thin shim ($1.50, medium)

Rewrites `init.sh` from ~600-line scaffolder to a forwarding wrapper: parse `--upgrade` /
`--dry-run` / `<target>`, delegate to `specfuse init` / `specfuse upgrade`, keep the
deprecation banner verbatim, error if `specfuse` is absent. **No scaffolding logic remains**
(grep gate). Operator script → §11 (shellcheck + `bash -n` + bats happy-path), and adds the
`init-sh-shim-bats` gate to `verification.yml`. Actual **deletion** of `init.sh` stays the
later v1.1 cut (PLAN decision). Depends on T04+T05+T07.

### T09 — `specfuse upgrade` end-to-end integration test ($2.00, high)

Real upgrade against a `tmp_path` repo built by `init_specfuse`: versioned refreshed,
user-authored untouched, removed-versioned pruned, never-downgrade refused, `.claude`
refreshed + idempotent, installed-wheel leg (skip-guarded, mirrors T06). Deliverable IS the
test (red-test exempt). Depends on T07.

Gate-3 closing: terminal **`G3-CLOSE`** (WU-90, pre-scaffolded) — single WU collapsing
retro + lessons + docs + the feature-arc verdict. Its `depends_on` is now set to T07+T08+T09.
**No `G3-CLOSE-INTERMEDIATE` / `G3-PLAN`** (gate 3 is terminal).

## Roadmap-anchor check

`roadmap_goal`: *"Ship the scaffold seed inside the pip package so specfuse init/upgrade lay
down .specfuse/ from package resources, fully replacing init.sh (unblocking its v1.1
deletion)."*

- "upgrade … lay down .specfuse/ from package resources" → **gate 3 (this draft) covers it.**
  T07 does exactly the overlay; T09 proves it from the installed wheel.
- "fully replacing init.sh" → **T08 makes init.sh a shim** that delegates to the pip CLI, so
  the two scaffold paths can't drift. The shim is the replacement; the bash logic is gone.
- "unblocking its v1.1 deletion" → **the shim unblocks the deletion; the deletion itself
  stays a later v1.1 cut** (explicit PLAN decision). So G3-CLOSE's terminal verdict should
  read **"met modulo the deferred deletion"** — flagged here so it isn't misread as drift.

**Anchor verdict:** gate 3 closes the init.sh-replacement arc. No `roadmap_goal` change
implied by gate 2's retrospective; no escalation fired. The feature ships the full
`init`/`upgrade` substrate + the shim; only the physical `init.sh` removal is left to v1.1 by
design.

## If you check only three things

1. **`specfuse upgrade`'s versioned footprint is SMALLER than `init.sh --upgrade`'s.**
   `init.sh` overlays `VERSIONED_ITEMS=(templates rules skills verification.yml.example
   README.md VERSION)` plus a `scripts/` allowlist and `docs/` (`init.sh:90`, `:448-475`).
   The pip seed (T01) ships **only** `templates/`, `rules/`, `verification.yml.example`,
   `VERSION` (+ the `*.template.md` seeds + `gitignore.snippet`) — **no** `skills/`,
   `scripts/`, or `docs/`. T07 overlays only what the seed ships. **Confirm this is the
   intended footprint before arming** — if upgraded repos must still receive vendored
   `scripts/` or `docs/`, T07's scope grows and T01's seed is missing data (a gate-1
   re-scope, not a gate-3 tweak).
2. **Never-downgrade is invented — `init.sh` has no version gate.** T07 adds
   `ScaffoldDowngradeError` (refuse if `scaffold_version()` < target `.specfuse/VERSION`,
   semver compare). The error type, the compare semantics (strict `<` refuses; `==`/`>`
   proceed), and the semver parse of `MAJOR.MINOR.PATCH` are all new this gate. **Confirm the
   refusal direction and the equal-version behavior** (T07 proceeds on equal — re-overlay is
   a safe no-op-ish refresh) before arming.
3. **The init.sh-legacy migration prune is deliberately deferred (a real spec gap).** A repo
   scaffolded by the *old* `init.sh` has `.specfuse/scripts/` (vendored driver) and
   `.specfuse/skills/` (relative symlinks) that the pip-native model replaces with the
   plugin. Should `specfuse upgrade` **delete** those on upgrade (migrate to pip-native) or
   **leave** them? T07 deliberately **leaves them** (prune scoped to the versioned footprint
   only) and flags the question for the close — deleting user-adjacent directories is a
   migration-semantics call the loop must not make unilaterally. **Decide before arming
   whether legacy-prune belongs in this feature, a v1.1 cut, or FEAT-2026-0027.**

## Open questions (mapped to draft WUs)

1. **Umbrella CLI ownership (T08, carried from gate 2).** T08's shim delegates to
   `specfuse init` / `specfuse upgrade`. Those subcommands live in the cross-repo `specfuse`
   umbrella CLI (this repo is the `specfuse-loop` distribution; `[project.scripts]` ships only
   `specfuse-loop` / `specfuse-lint`). If the umbrella CLI does not yet expose
   `init`/`upgrade`, T08 can only be verified against a **stub** `specfuse` — confirm the CLI
   contract exists (or accept the stubbed bats + a "did NOT verify" close note). *Resolve
   before arming T08.*
2. **Never-downgrade compare semantics (T07).** Strict `<` refuses, `==`/`>` proceed,
   `MAJOR.MINOR.PATCH` semver. Is re-overlay on an **equal** version the desired behavior (a
   safe refresh), or should equal also be a no-op/refusal? *Operator decides; T07 proceeds on
   equal as the conservative refresh default.*
3. **Legacy `scripts/`/`skills/` migration prune (T07).** See "check only three things" #3.
   In scope here, a v1.1 cut, or FEAT-2026-0027? T07 leaves them intact and flags it.
4. **`--dry-run` mapping (T08).** `init.sh --dry-run` currently previews. Does the `specfuse`
   CLI expose an equivalent? T08 forwards it and **escalates (`status: blocked`)** rather than
   silently dropping it — a silently-ignored `--dry-run` would scaffold for real. Confirm the
   CLI flag name.
5. **Installed-wheel leg in the sandbox (T09).** If the loop sandbox can't build/install a
   wheel, T09's AC6 runs skip-guarded and the close records it under "what the loop did NOT
   verify". Confirm CI exercises the real wheel leg (same as T06).
6. **`ci_check` on upgrade (T07).** T04 carries a `ci_check` param for the
   `verification.yml` seed-if-missing path. T07 mirrors it for symmetry. Confirm upgrade
   should re-seed a *missing* `verification.yml` from `ci_check` the same way init does (it
   should never overwrite an existing one — AC3).

## Cross-repo / invented-value contracts

Per `[FEAT-2026-0003/G3-LESSONS]` (verify cross-surface contract values against an
authoritative source). Each row is operator-checked before arming.

| Invented / contract value | Authoritative source | Used in | Checked |
|---|---|---|---|
| API name `upgrade_specfuse(target, *, ci_check=None)` | invented this gate; symmetry with T04 `init_specfuse` | T07 AC2, T09 | [ ] |
| Downgrade error type (e.g. `ScaffoldDowngradeError`) | invented this gate (init.sh has no version gate) | T07 AC5, T09 AC4 | [ ] |
| Never-downgrade compare (strict `<` refuses; semver `MAJOR.MINOR.PATCH`) | invented this gate; VERSION format `0.2.0` (`specfuse/loop/data/VERSION`) | T07 AC5 | [ ] |
| Versioned footprint = `templates/`, `rules/`, `verification.yml.example`, `VERSION` (NO `skills/`/`scripts/`/`docs/`) | T01 packaged seed vs `init.sh:90` VERSIONED_ITEMS | T07 AC2/AC4, T09 AC1/AC3 | [ ] |
| User-authored preserve set = `LEARNINGS.md`, `verification.yml`, `roadmap.md`, `features/` | `init.sh:108` USER_AUTHORED | T07 AC3, T09 AC2 | [ ] |
| Shim delegates to `specfuse init` / `specfuse upgrade` | `init.sh` deprecation banner (`init.sh:~370`) + cross-repo `specfuse` CLI | T08 AC2 | [ ] |
| `init-sh-shim-bats` gate command `bats tests/init_sh_shim.bats` | new; mirrors `sync-scaffold-bats` / `leak-scan-hook` in `verification.yml` | T08 AC5 | [ ] |
| `--dry-run` CLI-equivalent flag | cross-repo `specfuse` CLI contract (unpinned) | T08 AC2 | [ ] |

Each unchecked row is a value an arming operator should grep the codebase (and the cross-repo
`specfuse` CLI contract) for before locking the AC.

## Predicate-version note

Cost figures cited are predicate=v1. Gate-3 WU `planned_cost_usd` totals **$7.50**:
substantive **$6.00** (T07 $2.50 + T08 $1.50 + T09 $2.00) + closing **$1.50** (terminal
`G3-CLOSE`). The linter's feature-level WU-sum is now **$28.00** against the PLAN.md
feature-level `planned_cost_usd` of $22.00 (the draft-time estimate) — a 27% delta, so the
lint planned-cost WARN is expected and informational, not an error. Leaving the feature-level figure as-is preserves the
original estimate for cost-variance calibration rather than retrofitting it (same stance as
gate 2's review).
