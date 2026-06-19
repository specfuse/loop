# Gate-2 review — drafted by G1-PLAN

Operator's pre-arm review for gate 2 of `FEAT-2026-0026-pip-scaffold-data`
(`specfuse init`). Flip each gate-2 WU `status: draft` → `pending` only after working the
**Open questions** + **Cross-repo / invented-value contracts** sections below.

> Filename note: this file is `GATE-02-REVIEW.md`, not `GATE-01-REVIEW.md`. The G1-PLAN
> WU body says "GATE-01-REVIEW.md", but the driver's `assert_gate_review_exists`
> (`specfuse/loop/loop.py:2405`) computes the expected name from the **next** gate —
> `GATE-{this_gate+1:02d}-REVIEW.md`. For gate-1 plan-next that is `GATE-02-REVIEW.md`.
> The previous attempt failed exactly here (`GATE-02-REVIEW.md absent or empty`). The WU
> text is the stale label; the driver is authority.

## Gate-1 summary

Gate 1 shipped the **data substrate** as three substantive WUs + the auto-closed
intermediate ceremony:

- **T01** — the scaffold seed (`templates/`, `rules/`, `verification.yml.example`,
  `roadmap.template.md`, `LEARNINGS.template.md`, `VERSION`, `gitignore.snippet`) shipped
  as package data under `specfuse/loop/data/`, included in the wheel. ($1.50 planned /
  $1.00 actual.)
- **T02** — `specfuse.loop.scaffold`: `iter_scaffold_files`, `read_scaffold`,
  `scaffold_version`, resolved via `importlib.resources` (no `__file__` paths), proven to
  resolve from an installed wheel. ($2.00 / $0.54.)
- **T03** — `scripts/sync-scaffold.sh` + `tests/test_scaffold_data_in_sync.py` drift guard
  keeping package data == canonical `.specfuse/`. ($2.00 / $1.32.)

Gate-1 substantive spend: **$2.86 actual vs $5.50 planned** (auto-closed on-plan,
predicate=v1, no overrun reasons). The data layer landed cleanly; nothing forced a
re-scope. Gate 2 builds the **write** path on top of T02's read API.

## Gate-2 substantive WUs (drafted)

### T04 — `specfuse init` core writer ($2.50, high)

`specfuse.loop.scaffold.init_specfuse(target)` writes a fresh `.specfuse/` tree
(templates, rules, VERSION, seeded roadmap/LEARNINGS/verification.yml, empty `features/`)
from T02's resource API, and **refuses** (distinct catchable error pointing at
`specfuse upgrade`) if `.specfuse/` already exists — no partial write. Byte-faithfulness
is tested against `read_scaffold`, not against disk. Depends on T02.

### T05 — `.claude` wiring + `.gitignore`, merge-safe ($2.50, high)

`wire_claude(target)` + a `.gitignore` writer: runtime-artifact ignore lines (from the
seed's `gitignore.snippet`), CLAUDE.md `@rules` import block, settings allowlist, and the
Claude Code **plugin config** (`extraKnownMarketplaces` + `enabledPlugins`) — all
merge-safe (parse-merge-rewrite JSON; create-if-missing; never clobber user content). This
is the deliberate departure from init.sh: the plugin **replaces** the skill symlink trick
(AC5 asserts no symlinks). Depends on T04.

### T06 — end-to-end init integration test ($2.00, high)

Full `init` + wiring against a `tmp_path` repo: complete layout assertions, refusal,
idempotency, gitignore + plugin-config correctness, and an installed-wheel leg
(skip-guarded when the build toolchain is absent, mirroring T02). Deliverable IS the test
(red-test exempt). Depends on T04 + T05.

Gate-2 closing: `G2-CLOSE-INTERMEDIATE` (WU-92) → `G2-PLAN` (WU-93) — gate 2 is
non-terminal; gate 3 (`specfuse upgrade` + shim) is terminal with the pre-scaffolded
`G3-CLOSE`, whose real `depends_on` G2-PLAN will set.

## Roadmap-anchor check

`roadmap_goal`: *"Ship the scaffold seed inside the pip package so specfuse init/upgrade
lay down .specfuse/ from package resources, fully replacing init.sh (unblocking its v1.1
deletion)."*

- "init … lay down .specfuse/ from package resources" → **gate 2 (this draft) covers it.**
  T04/T05 do exactly this; T06 proves it from the installed wheel.
- "upgrade … from package resources" → **gate 3**, drafted by G2-PLAN.
- "fully replacing init.sh (v1.1 deletion)" → gate 3's init.sh shim; **actual deletion
  stays a later v1.1 cut** (PLAN decision), so the verdict at G3-CLOSE will be "met
  modulo the deferred deletion" — flag now so it isn't read as drift later.

**Anchor verdict:** gate 2 is on-arc. No `roadmap_goal` change implied by gate 1's
retrospective; no escalation fired.

## If you check only three things

1. **The umbrella `specfuse init` CLI is NOT in this repo.** This repo is the
   `specfuse-loop` distribution; `[project.scripts]` ships only `specfuse-loop` /
   `specfuse-lint` (`pyproject.toml:53-55`). Gate 2 deliberately delivers the
   **`specfuse.loop.scaffold` API** (`init_specfuse`, `wire_claude`), which the separate
   `specfuse` umbrella CLI calls (PLAN decision; FEAT-2026-0019 cross-repo). T04's "Do not
   touch" forbids adding a `specfuse` console script here. **Confirm this is still the
   intended split before arming** — if the umbrella CLI must live here, T04/T05 scope
   changes and the gate needs a fourth WU.
2. **Plugin-config schema is partly invented.** init.sh never wrote `extraKnownMarketplaces`
   / `enabledPlugins` — it symlinked skills and printed a `/plugin marketplace add` banner
   (`init.sh:380-381`). T05 writes real plugin config; the exact JSON shape + file location
   are not pinned by the seed. A wrong shape silently breaks skill discovery in the
   scaffolded repo. **Grep a known-good `.claude/settings.json` (e.g. a real
   plugin-enabled repo) for the authoritative schema before arming T05.**
3. **Settings allowlist content: legacy script paths vs pip commands.** init.sh writes
   `Bash(python3 .specfuse/scripts/loop.py:*)` + `lint_plan.py` allow entries
   (`init.sh:341-349`). The forward path is `specfuse-loop` / `specfuse-lint`. T05 mirrors
   init.sh for parity but flags this — **decide which the scaffolded allowlist should
   reference** before arming (see Open question 3).

## Open questions (mapped to draft WUs)

1. **Umbrella CLI ownership (T04, T05).** Is `specfuse.loop.scaffold.init_specfuse` the
   correct home, with the `specfuse` CLI cross-repo? If init/upgrade should live in *this*
   package behind a console script, the gate needs a CLI-wiring WU. *Resolve before
   arming T04.* (Escalation trigger in G1-PLAN explicitly lists this.)
2. **Plugin-config shape + location (T05).** Which JSON file holds `extraKnownMarketplaces`
   / `enabledPlugins`, and what are their exact shapes? T05 escalates (`status: blocked`)
   if it must invent them — pre-resolve to avoid a wasted attempt.
3. **Allowlist target (T05).** Should the scaffolded `settings.json` allow the pip
   commands (`specfuse-loop`/`specfuse-lint`) or init.sh's legacy `.specfuse/scripts/*.py`
   paths? Mixed signals: pip is the forward path, but `.specfuse/scripts/` shims still
   ship. *Operator decides; T05 mirrors init.sh as the conservative default.*
4. **`ci-check.sh` auto-detection (T04).** init.sh writes a delegating `verification.yml`
   when it finds a `ci-check.sh` in the target (`init.sh:211-251`). T04 scopes this to a
   caller-supplied `ci_check` param rather than re-implementing filesystem probing. Confirm
   that's acceptable, or promote ci-detection to its own concern.
5. **Installed-wheel leg in the sandbox (T06).** If the loop sandbox can't build/install a
   wheel (no network / no build backend), T06's AC5 runs skip-guarded and the close must
   record it under "what the loop did NOT verify". Confirm CI exercises the real wheel leg.
6. **Single orchestrating entry point (T04/T05/T06).** Should there be one
   `init(target)` that calls both `init_specfuse` + `wire_claude`, so callers (tests + the
   cross-repo CLI) don't duplicate the sequence? T06 escalates a note if the duplication
   bites; decide whether to fold it into T04.

## Cross-repo / invented-value contracts

Per `[FEAT-2026-0003/G3-LESSONS]` (verify cross-surface contract values against an
authoritative source). Each row is operator-checked before arming.

| Invented / contract value | Authoritative source | Used in | Checked |
|---|---|---|---|
| API name `init_specfuse(target, *, ci_check=None)` | invented this gate; PLAN § decisions | T04 AC2, T06 | [ ] |
| Refusal error type (e.g. `ScaffoldExistsError`) | invented this gate | T04 AC3, T06 AC2 | [ ] |
| API name `wire_claude(target)` | invented this gate | T05 AC2, T06 | [ ] |
| Marketplace id `specfuse/specfuse` | `init.sh:380` + deprecation banner | T05 AC4, T06 AC4 | [ ] |
| Plugin id `specfuse@specfuse` | `init.sh:381` + deprecation banner | T05 AC4, T06 AC4 | [ ] |
| `extraKnownMarketplaces` / `enabledPlugins` JSON shape | Claude Code plugin config (NOT in init.sh) | T05 AC2/AC4 | [ ] |
| Settings allowlist entries | `init.sh:341-349` (legacy) vs pip commands | T05 AC2 | [ ] |
| gitignore lines `.specfuse/.loop.lock`, `.specfuse/.scratch-*`, `.specfuse/scripts/__pycache__/` | seed `gitignore.snippet` + `init.sh:589-593` | T05 AC2, T06 AC4 | [ ] |
| CLAUDE.md `@.specfuse/rules/...` block (4 rules) | `init.sh:307-311` + this repo's `.claude/CLAUDE.md` | T05 AC2 | [ ] |

Each unchecked row is a value an arming operator should grep the codebase + a real
plugin-enabled `.claude/` for, to confirm it doesn't collide with or contradict an
existing convention.

## Predicate-version note

Cost figures cited are predicate=v1. Gate-2 WU `planned_cost_usd` totals **$11.00**:
substantive **$7.00** (T04 $2.50 + T05 $2.50 + T06 $2.00) + closing **$4.00**
(G2-CLOSE-INTERMEDIATE $1.50 + G2-PLAN $2.50). The PLAN.md feature-level
`planned_cost_usd` ($11.00) was the draft-time estimate for the whole feature; now that
gates 2–3 carry per-WU costs the sum-of-WUs is ~$22, so the lint planned-cost WARN is
expected and informational, not an error. Leaving the feature-level figure as-is
preserves the original estimate for cost-variance calibration rather than retrofitting it.
