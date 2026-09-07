# Gate 1 — per-criterion close state

Written by `FEAT-2026-0102/G1-CLOSE`, attempt 1. `kind` and `state` are recorded
by the close that ran the oracle, per `.specfuse/rules/close-discipline.md` §5 —
never inferred by a reader.

One entry per bullet of `GATE-01.md` § *Definition of done*, attributed to the
work unit that produced the behaviour. `narrow` entries are proved by a scoped,
countable oracle (a structural assert over a named function, a purpose-built bad
input, a `diff`, a `grep`) so their green would be sound to carry forward across
close attempts. `broad` entries execute the whole test suite or the whole `code`
gate set and have no knowable scope, so they re-ran unconditionally this attempt.

### T01#1

- **criterion:** A gate in `.specfuse/verification.yml` may declare
  `needs: [<gate>]`; the driver runs the set in dependency order, and a gate
  whose dependency failed is reported `SKIP` and never counted as a pass
- **oracle:** `loop.order_gate_set` over the live `code` set (`tests` at index 0,
  `coverage` at index 3), plus `loop._run_gate_set` over a two-gate fixture whose
  `tests` command points at a throwaway directory holding one deliberately
  failing test — `coverage` returns `ok=False` with the report
  `### coverage: SKIP — dependency 'tests' failed` and its command is never run
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `27d4fe249eadebbb185aa6532e36cbad725a7d6e`
- **attempt:** `1`

### T01#2

- **criterion:** An unresolvable `needs:` target and a dependency cycle are both
  CONFIGURATION ERRORs, in the same shape as the existing unknown-`extra_gates`
  branch — never a silent skip, never a silent pass
- **oracle:** two negative observations on purpose-built bad inputs — a set whose
  `coverage` gate declares `needs: [nosuchgate]`, and a two-gate `a` ↔ `b` cycle
  — each pushed through `loop.order_gate_set`, `gate_commands._order_gates` and
  `loop.probe_baseline`. All six refuse; `probe_baseline` emits
  `failure_class: configuration_error` with the `CONFIGURATION ERROR: … This is
  not a work-unit failure — fix verification.yml and re-run.` signature
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `27d4fe249eadebbb185aa6532e36cbad725a7d6e`
- **attempt:** `1`

### T02#1

- **criterion:** `gate_commands.py` emits gates in the same dependency order the
  driver uses, so `scripts/smoke-test.sh` and CI cannot disagree with the driver
  about whether a gate's prerequisites ran
- **oracle:** `gate_commands.iter_code_gates(".specfuse/verification.yml")` name
  list compared element-wise against `loop.order_gate_set` over the same file —
  two 16-element lists, equal. Also `tests/test_gate_commands_needs.py` (T02),
  which runs under the `tests` gate
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `27d4fe249eadebbb185aa6532e36cbad725a7d6e`
- **attempt:** `1`

### T03#1

- **criterion:** This repo's `code` set runs its test suite **once** per pass —
  `tests` runs the suite under `coverage run`, `coverage` declares
  `needs: [tests]` and only reports; measured `code`-set wall clock recorded
  against the 118s baseline in `[FEAT-2026-0051/G1-CLOSE]`
- **oracle:** `bash scripts/smoke-test.sh` (exit 0) with its output counted for
  `Ran <N> tests` lines — exactly 1; plus the full 16-gate `code` set timed
  through `order_gate_set` + `_run_gate_set` in both gate shapes on one tree:
  320.2s before, 173.4s after, `coverage` 147.6s → 0.5s. See
  `RETROSPECTIVE.md` § *The `code`-set wall clock* for the recorded
  non-commensurability of the stored 118s absolute with today's 16-gate set
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `27d4fe249eadebbb185aa6532e36cbad725a7d6e`
- **attempt:** `1`

### T03#2

- **criterion:** `tests` and `coverage` still produce distinct `failure_class`
  values, and a failing test still yields a test-shaped `failure_signature`
  rather than a coverage-shaped one
- **oracle:** two fixture runs through `_run_gate_set` +
  `parse_gate_failure_signature` — a red test yields
  `failure_class='tests'` / `failure_signature='test_deliberately_red'` with
  `coverage` SKIPped; a green suite with `coverage report --fail-under=100`
  yields `failure_class='coverage'` with a `.py`-path signature and `coverage`
  actually executed. The two classes are distinct
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `27d4fe249eadebbb185aa6532e36cbad725a7d6e`
- **attempt:** `1`

### T03#3

- **criterion:** The authoring rule in the canonical
  `plugins/specfuse/skills/verification/SKILL.md` states the new contract:
  self-contained **unless** the gate declares `needs:`, in which case the runner
  owns the freshness guarantee
- **oracle:** `grep -n "self-contained unless it declares"
  plugins/specfuse/skills/verification/SKILL.md` → the rule at lines 112-121 of
  the canonical copy; `diff plugins/specfuse/skills/verification/SKILL.md
  .specfuse/skills/verification/SKILL.md` → exit 0, byte-identical
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `27d4fe249eadebbb185aa6532e36cbad725a7d6e`
- **attempt:** `1`

### G1-CLOSE#1

- **criterion:** Per-criterion state and the narrow/broad oracle contract:
  `close-discipline.md` §5
- **oracle:** this artifact; `specfuse lint --closing` over this feature
  directory reports no `close-l` finding
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `27d4fe249eadebbb185aa6532e36cbad725a7d6e`
- **attempt:** `1`
