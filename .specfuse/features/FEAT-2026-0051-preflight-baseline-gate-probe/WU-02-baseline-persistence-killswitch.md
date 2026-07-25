---
id: FEAT-2026-0051/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
produces_driver_helper: read_gate_baseline, write_gate_baseline, baseline_probe_enabled
produces:
  - specfuse/loop/loop.py
  - tests/test_baseline_persistence.py
---

# Persist the baseline in gate frontmatter; add the re-probe policy and kill-switch

**Objective.** Record T01's probe result in `GATE-NN.md` frontmatter so the probe
is not re-paid on every driver resume, re-probe only when the tree has moved, and
add `--no-baseline-probe` plus a `verification.yml` opt-out.

**Context.** Part of FEAT-2026-0051, second WU; depends on T01, which created
`probe_baseline()` and the halt path. Read `PLAN.md` for scope. The probe is one
full `code`-set run (this repo: unittest + ruff + bandit + coverage + four bats
suites — minutes, not seconds), and the driver is resumed constantly: after each
halt, each re-arm, each operator fix. Re-probing on every invocation is the cost
this WU removes.

Gate frontmatter is the established home for gate state (`status`,
`cost_budget_usd` — see `gate_budget_usd` at `loop.py:1544` for the read
pattern). Writes go through the existing bookkeeping-commit path, not a new
persistence mechanism.

Record shape:

```yaml
baseline:
  sha: <the sha probed>
  probed_at: <UTC ISO>
  failing:
    - gate: <gate name>
      failure_class: <class>
      failure_signature: <signature>
```

An empty `failing:` list is a real, meaningful record — "probed, and it was
green" is exactly what lets the next resume skip the run. It must be
distinguishable from an absent `baseline:` key.

**Re-probe policy.** Skip the probe when `baseline.sha` equals the sha the driver
is about to dispatch into. Re-probe when they differ. Nothing else invalidates
it in v1 — deliberately: a time-based expiry would reintroduce the per-resume
cost this WU exists to remove, and FEAT-2026-0052's waiver work is where staleness
gets revisited with real data.

Binding rules in `.specfuse/rules/` apply. Do not restate them.

**Acceptance criteria.**
- `tests/test_baseline_persistence.py::test_second_entry_skips_probe_when_sha_unchanged`
  exists and **fails on HEAD before this WU's edits**. It runs gate entry twice
  against an unchanged sha with a counting probe stub and asserts the probe ran
  **exactly once**.
- After this WU's edits that test passes, and so does
  `::test_moved_sha_reprobes` — a changed sha runs the probe a second time.
- A green probe writes `baseline:` with an empty `failing:` list, and the next
  entry skips on it. A test asserts the empty-list record is not treated as
  "never probed".
- The baseline write is committed via `commit_bookkeeping` alongside the gate
  file — asserted by a test. An uncommitted write does not survive
  `git reset --hard`.
- `--no-baseline-probe` on the driver CLI skips the probe entirely: the probe
  stub is called zero times and dispatch proceeds exactly as on today's driver.
- A `verification.yml` opt-out key disables the probe for a project permanently,
  with the same observable effect. A test covers it.
- `baseline_probe_enabled()` is importable and resolves precedence in one place:
  CLI flag beats config key beats the default (enabled).
- Symbol check: `python3 -c "from specfuse.loop.loop import read_gate_baseline,
  write_gate_baseline, baseline_probe_enabled"` exits 0.
- A malformed or partial `baseline:` block (missing `sha`, unparseable) is
  treated as **absent** and re-probed, never crashed on. A test feeds a
  half-written block.

**Flag-scope table** (`.specfuse/rules/planning-discipline.md` §3). The headline
claim is: *the switch disables the probe and nothing else*. Every path the flag
is claimed to affect:

| Code path | Gated by flag? | Why |
|---|---|---|
| `probe_baseline()` invocation at gate entry | yes | The switch's entire purpose — no probe run, no cost. |
| `preexisting_gate_failure` halt | yes (transitively) | No probe means no failing set, so the halt cannot fire. Today's behavior exactly. |
| `write_gate_baseline()` | yes | Nothing probed, nothing to record. Any existing `baseline:` block is left untouched, not cleared. |
| `verify()` — the per-WU exit oracle | **no** | The switch weakens no gate. Every WU is still gated on the full `code` set, pass/fail semantics unchanged. This row is the one that distinguishes the switch from the mute flag issue #234 rejected. |
| Per-gate `cost_budget_usd` brake | **no** | Independent brake, untouched. |
| Spinning detection / attempt budget | **no** | Unchanged; without the probe the driver spins exactly as it does today. |

**Do not touch.** `verify()`'s pass/fail semantics (out of scope for the whole
feature — see PLAN.md's scope boundary); the escalation message text and evidence
payload (T03); `probe_baseline()`'s own probing logic (T01's, extend only at the
call site). `.git/`, secrets. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
symbol checks above. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if writing `baseline:` into gate
frontmatter cannot be done through the existing frontmatter writer without
reformatting the rest of the file — a rewrite that reorders or reflows other gate
keys would show up as spurious diff noise in every gate file and needs a human
call. Also block if the sha the driver is "about to dispatch into" is ambiguous
at the call site (e.g. uncommitted working-tree changes make HEAD not the tree
being measured) — guessing here silently makes the skip-policy wrong. If any of
the three named symbols is absent from the files you edited, emit `status:
blocked` — do not claim complete. Blocked is respectable (`result-contract.md`
rule 4).
