# Feature retrospective — FEAT-2026-0014 GHA Node.js 20 deprecation bump

Single-gate, single-substantive-WU feature. Bump
`actions/checkout@v4` → `@v6` and `actions/setup-python@v5` → `@v6`
in `.github/workflows/ci.yml` ahead of GitHub's 2026-06-16 forced
Node-24 upgrade.

## T01 — Bump action versions in ci.yml

**Final outcome.** Completed in 1 attempt after a WU rewrite. Net
code change: two `uses:` lines in `.github/workflows/ci.yml`. Final
landing commit: `d97b4e8` (`feat: Bump GitHub Actions to Node-24
generation in ci.yml`).

**What worked.** The rewrite (commit `f2dc1b4`) dropped the gh-CLI
acceptance criteria entirely. Once the WU's ACs no longer required
hitting `api.github.com` via the operator's `gh` CLI, the
file-edit-only path was trivial and landed in a 43-second session
(`task_completed` 2026-06-11T18:33:29Z, attempt 1, cost
$0.1588362).

**What failed.** Pre-rewrite, T01 burned five dispatch attempts —
all `human_escalation` events in `events.jsonl` — every one
blocked on `gh CLI not authenticated; AC4/AC5 cannot run`:

| Attempt | Timestamp (UTC)        | Blocked reason (verbatim)                                                                  |
|---------|------------------------|--------------------------------------------------------------------------------------------|
| 1       | 2026-06-11T15:53:06Z   | "gh CLI not authenticated; AC4/AC5 cannot run"                                             |
| 2       | 2026-06-11T16:19:42Z   | "The token in GH_TOKEN is invalid"                                                         |
| 3       | 2026-06-11T16:37:29Z   | unsandboxed retry (rationale: `claude -p` sandbox blocks gh auth round-trip) — still 401 |
| 4       | 2026-06-11T16:44:35Z   | "The token in keyring is invalid"                                                          |
| 5 (×3)  | 2026-06-11T17:02:41Z → 17:07:48Z | `spinning_detected` (3 internal attempts within session) — same gh-auth wall    |

Total pre-rewrite spend (sum of `cost_usd` from `attempts_usage`):
≈ $1.22 across 7 inner attempts before the WU was rewritten. The
operator's host had no valid GitHub token for the duration of the
gate. `unsandboxed_dispatch` (attempt 3) was the recovery skill's
correct response to "maybe the sandbox is blocking auth" — it
wasn't; the token itself was invalid.

**Rule/template/boundary gaps.** None new for this run. The gate
exposes existing learnings already promoted to `LEARNINGS.md`:

- ACs that depend on the operator's authenticated tooling (gh
  CLI, cloud SDK creds) make the WU host-environment-coupled and
  silently fail when those creds rot. Recovery is "re-arm the WU
  with weaker ACs" — exactly what happened here. The
  `WU-01-close.md` re-arm (commit `f2dc1b4`) dropped the
  gh-touching ACs.
- The 3-attempt spinning escalation worked as designed. The
  driver halted, the operator re-armed the WU with reduced
  scope, and the next dispatch landed clean.

No durable rule promoted from this gate (see
`## Durable lessons` below).

## Pin-bump existence audit

Recursive AC-2 audit, run live against
`.github/workflows/ci.yml` at close time:

```
$ grep -c 'actions/checkout@v6' .github/workflows/ci.yml
1
$ grep -c 'actions/setup-python@v6' .github/workflows/ci.yml
1
$ grep -cE 'actions/(checkout@v[0-5]|setup-python@v[0-5])' .github/workflows/ci.yml
0
```

All three values match expectations (`1`, `1`, `0`). The
`@v6` pins are present and no stale `@v[0-5]` pins remain. Not
a hollow pass.

## Roadmap-state reconciliation

Escalation trigger 2 fired softly: `.specfuse/roadmap.md` table
row (line 32) carried `planned`, not `active`, when this close
ran — the row was never flipped to `active` at feature start.
The detail section at line 588 also reads `**Status: planned.**`
rather than the `**Status: active.**` the WU AC names. This is
a forgotten roadmap-row promotion at feature start, not a
historical-state conflict; the legitimate close action is
straight `planned` → `done` on both surfaces. The WU's text was
written assuming the standard active→done flip, but the
underlying intent — "land the feature, mark the roadmap done" —
is unambiguous. Flip applied to both surfaces.

## Durable lessons

Nothing generalizes from this gate. The host-credential-coupling
failure mode is already covered in LEARNINGS by prior features
(WU re-arm pattern). The pin-bump itself is mechanical. No
append to `.specfuse/LEARNINGS.md`.

# Feature-arc verdict

**`roadmap_goal` met.** Goal text (from `PLAN.md` frontmatter):
"Bump GitHub Actions to versions supporting Node.js 24 natively,
ahead of the 2026-06-16 deprecation, so CI keeps running without
warnings." The AC-2 audit above confirms both targeted actions
now pin `@v6` (the Node-24 generation per GitHub's deprecation
notice) and no stale `@v[0-5]` pins remain in `ci.yml`. CI
workflow file structurally unchanged otherwise.

Deadline: 2026-06-16 forced upgrade. Today is 2026-06-11 — five
days of margin. No deadline overrun.

Caveat: this close ceremony does NOT verify a live CI run
emitted no deprecation warning, because that AC was dropped
from T01's rewrite (the gh-CLI dependence made it
host-coupled). The next push to any branch will exercise the
new pins; if a regression surfaces, it would be a successor
feature, not a re-open of this one.
