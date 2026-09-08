---
feature_id: FEAT-2026-0109
title: Tiered verification and a lazy baseline probe
slug: tiered-verification
branch: feat/FEAT-2026-0109-tiered-verification
roadmap_goal: The driver stops paying for verification nobody needed — the baseline probe becomes lazy and attributes a failure only when one happens, the per-attempt gate set narrows to what the unit actually touched with the full suite reserved for once per gate, and a unit that edits the driver no longer halts the run.
autonomy_default: review
status: active
planned_cost_usd: 26.00
---

# Plan: Tiered verification and a lazy baseline probe

Half of a median attempt is the driver's own verification. FEAT-2026-0102
removed the duplicated suite execution *inside* a pass — the `code` set fell
320.2s → 173.4s — but not the cost of running the whole set per attempt, and
not the re-probe that every restart pays.

The probe's real job is **attribution**: telling "this WU broke it" from "it
was already broken", which is why a red probe escalates
`preexisting_gate_failure` rather than blaming a unit. That answer is not
needed until something fails. Measured on the FEAT-2026-0101 run: five probes,
roughly 15 minutes of wall clock, **every one returning `failing: []`** — the
premium was paid at every gate entry and every restart against an event that
did not occur once.

So gate 1 makes the probe lazy: skip at entry, and attribute retroactively
against the post-reset tree when a unit's verification first fails. Gate 2
narrows what runs per attempt. Gate 3 removes the restart tax.

## Scope boundary

**IN.** Lazy attribution and the provenance that makes it readable (gate 1);
tree-hash keying for the probe that does still run (gate 1); the per-attempt
vs per-gate tier split (gate 2); running the driver from an installed copy
(gate 3).

**OUT, deliberately.**

- **A CI-result fast path.** Attractive and cheap to build — CI runs
  `scripts/smoke-test.sh`, which derives its gate list from
  `verification.yml` (#592), so a CI verdict covers the same gate set, and
  `gh` is already a driver dependency. It is out because it cannot be the
  general answer and gate 1 makes it largely moot. **Measured:** every probe
  SHA on the FEAT-2026-0101 run was local-only — `ba8fab4`, `ba29587`,
  `f7e20c4`, `320456c`, 0 of 4 known to CI — because the probe runs at HEAD
  and HEAD after `--prepare`, a bookkeeping commit or a squash is never
  pushed. The restart case, the expensive one, has no CI result by
  construction. **And environment:** CI is Linux plus a Windows job while the
  driver here runs macOS, and the probe must predict whether *this* machine's
  gate run will be green, because that run is the WU's exit oracle. T03's
  provenance field is the precondition if it is ever revisited.
- **Changing what a gate set contains.** Gate 2 changes *when* gates run, not
  which gates exist or what they assert.
- **Parallel dispatch of the ready frontier.** FEAT-2026-0105.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep commands run:**
  ```
  grep -n "def probe_baseline\|def gate_baseline_check\|def baseline_probe_enabled" specfuse/loop/loop.py
  grep -n "def read_gate_baseline\|def write_gate_baseline" specfuse/loop/loop.py
  grep -rn "write-tree\|write_tree\|tree_hash" specfuse/loop/*.py
  ```
- **Verdict:** `found the probe surface, reusing it; no tree-hash mechanism exists`.
  `probe_baseline` (`loop.py:4307`), `gate_baseline_check` (`:4618`),
  `baseline_probe_enabled` (`:4643`), `read_gate_baseline` (`:4485`) and
  `write_gate_baseline` (`:4543`) are the whole surface. `probe_baseline` is
  already factored out of `verify()` and takes `(feature_dir, cfg)` with no
  work-unit argument, so calling it from a failure path needs no new
  execution machinery — the same reuse FEAT-2026-0102 relied on.
- **Half of gate 1 already ships.** `baseline_probe_enabled` already honours
  the `--no-baseline-probe` CLI flag and a `baseline_probe` key in
  `verification.yml`, so *skipping* is available today. The missing half is
  the retroactive attribution that makes skipping safe.
- **Nothing keys anything on a tree hash.** The grep returns no hits, so T02
  is new. `git rev-parse HEAD^{tree}` is the primitive; the record it writes
  is `read_gate_baseline`'s existing block, which is why T02 is small.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

n/a — this feature raises no check to `ERROR`, flips no `WARNING` to
blocking, and asserts no "zero issues" close predicate. It changes *when*
existing verification runs, never what any rule reports. The one adjacent
risk is the opposite of a false positive: a lazy probe could let a
pre-existing failure be attributed to a unit that did not cause it, which is
exactly what T01's retroactive attribution exists to prevent and what its
acceptance criteria assert.

## Task graph

```yaml
# Three gates. Gate 1 is self-contained and ships the wall-clock win on its
# own. Gates 2 and 3 are skeletal — `plan-next` drafts each from the prior
# gate's retrospective, along with its own `feature_oracle` (#3262).
#
# Gate 3 is the installed-copy driver ALONE, deliberately. [FEAT-2026-0019/G1]
# records that a feature migrating the harness the driver itself runs cannot
# be decomposed into separately-gated units — each unit's exit oracle is the
# surface being migrated — and the last attempt cost $5.63 and 49 minutes of
# thrash before abandonment. Giving it its own gate is what lets it land
# atomically.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0109/T01
        file: WU-01-lazy-attribution.md
        depends_on: []
      - id: FEAT-2026-0109/T02
        file: WU-02-tree-hash-keying.md
        depends_on: [FEAT-2026-0109/T01]
      - id: FEAT-2026-0109/T03
        file: WU-03-baseline-provenance.md
        depends_on: [FEAT-2026-0109/T01]
      # --- closing sequence: 2-WU intermediate (non-terminal gate) ---
      - id: FEAT-2026-0109/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on: [FEAT-2026-0109/T01, FEAT-2026-0109/T02, FEAT-2026-0109/T03]
      - id: FEAT-2026-0109/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0109/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units: []
  - gate: 3
    file: GATE-03.md
    work_units:
      # Scaffolded so lint reads gate 1 as non-terminal. G2's plan-next
      # inserts gate 3's substantive units above this entry.
      - id: FEAT-2026-0109/G3-CLOSE
        file: WU-90-gate-3-close.md
        depends_on: []
```

## Notes

- **What gate 1 is worth.** On the FEAT-2026-0101 run the probe cost roughly
  15 minutes across five entries and returned `failing: []` every time. Gate 1
  removes that from the green path entirely and pays it only when a unit
  actually fails.
- **The cost gate 1 accepts, stated plainly.** When the tree really is
  pre-broken, one agent dispatch is burned discovering it — roughly $1–4 and
  15–25 minutes — and that agent may thrash on a failure it did not cause.
  Bounded to one dispatch per gate because the retroactive probe fires on the
  first failure, and the driver's hard reset discards the thrash. Against
  ~3 minutes × every entry and restart, at the failure rates measured, the
  trade is clearly right — but it is a trade, not a free win.
- **Why gate 2 waits for gate 1's `plan-next`.** The per-attempt tier needs a
  rule for "tests touching changed files", and what that rule should be is
  better answered after gate 1 has made the driver's failure path explicit.
  FEAT-2026-0101 supplies the `feature_oracle` the tier lists among its cheap
  gates; that prerequisite is already merged.
- **Cost calibration.** FEAT-2026-0102's per-WU estimates ran 2.6× high;
  FEAT-2026-0101's recalibrated ones came in close ($12.98 substantive against
  $11.00 planned, the overshoot almost entirely one unit's discarded
  discovery). These follow 0101's calibration. `planned_cost_usd` covers
  gate 1's five units plus the scaffolded gate-3 close ($8.00), which is the
  set that exists today; gates 2 and 3's substantive units are costed by their
  own `plan-next` and will raise it.
- **Two authoring constraints this feature's units will meet**, learned the
  expensive way on FEAT-2026-0101/T02, which burned three attempts
  rediscovering them: an edit to `.specfuse/rules/*.md` must be mirrored
  byte-for-byte into `specfuse/loop/data/rules/`, and a new closing-requirement
  entry must name a real guard function in `lint_closing.py`. Any unit here
  touching those surfaces states them in its own body rather than leaving them
  to be discovered by failing.
</content>
