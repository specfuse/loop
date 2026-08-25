---
id: FEAT-2026-0052/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
produces_driver_helper: write_gate_waiver, read_gate_waiver, waiver_covers_baseline
produces:
  - specfuse/loop/loop.py
  - tests/test_baseline_waiver.py
model: sonnet
effort: medium
---

# Record a durable, sha-pinned waiver in the gate file and proceed past the halt

**Objective.** Add `--waive-baseline`: it writes a `waiver:` block into the gate's
frontmatter pinned to the baseline sha and the exact failing set it waives, the
gate-entry path proceeds instead of halting when that waiver covers the current
baseline, and the decision survives a driver resume because it lives on disk
rather than in argv.

**Context.** Second WU of FEAT-2026-0052; read `PLAN.md` in this folder first —
in particular the scope boundary's rejection of a per-gate mute (issue #234) and
the Notes entry on sha pinning, which this WU implements. T01 built the
subtraction and a `baseline_waiver_active` predicate against an injected value;
this WU gives that predicate its real storage and wires the proceed path.

Reuse, do not reimplement — all four already exist from FEAT-2026-0051:

- `write_frontmatter_block(gate_file, "baseline", lines)` is how
  `write_gate_baseline` (`loop.py:4006`) persists a nested mapping into gate
  frontmatter without reflowing the rest of the file. The `waiver:` block uses
  the same writer, the same way.
- `read_gate_baseline(gate_file)` (`loop.py:3976`) is the shape to mirror for
  `read_gate_waiver`: return `None` — never raise — on an absent block, a
  non-mapping, or a missing required key. A malformed waiver must read as **no
  waiver** (fail closed: the gate halts), never as a permissive one.
- `gate_baseline_check(gate_file, feature_dir, cfg, head_sha)` (`loop.py:4031`)
  returns `(failing_gates, freshly_probed)` and is called at gate entry
  (`loop.py:6643`). The proceed decision goes **after** that call — the probe
  still measures the full truth; the waiver only changes what the driver does
  with it.
- The halt block at `loop.py:6666-6683` (`set_gate(awaiting_review)` →
  `human_escalation` event → `commit_bookkeeping` → `return 1`) is the branch the
  waiver skips. Skip it; do not rewrite it.

**Sha-and-set pinning is the load-bearing property of this WU.** A waiver records
the baseline `sha` and the exact `failing` set it was granted against. When the
current baseline's failing set contains an entry the waiver does not name, the
waiver does **not** cover it and the gate halts as usual. Without this, a waiver
granted for one advisory silently swallows the next one — which is the mute #234
rejected, wearing a different hat.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`verification-discipline.md`) apply. Do not restate them.

**Acceptance criteria.**

- `tests/test_baseline_waiver.py::test_waiver_does_not_cover_a_new_failure`
  exists and **fails on HEAD before this WU's edits** (the module does not yet
  exist). A waiver granted against a baseline of `{A}` does not cover a baseline
  of `{A, B}`: `waiver_covers_baseline` returns False and the gate still halts.
- After this WU's edits that same test passes, and so does
  `tests/test_baseline_waiver.py::test_waiver_covers_its_own_baseline_and_proceeds`
  — with a waiver matching the recorded failing set, gate entry proceeds to the
  frontier loop and dispatches work units instead of returning 1.
- `--waive-baseline` exists on the driver CLI and writes the `waiver:` block. A
  test asserts the flag is accepted and the block lands in the gate file.
- The waiver block carries, at minimum, `sha`, `waived_at`, and `failing` (the
  set it covers). A test asserts each key is present and that `failing` is
  written as an explicit list — an empty list, never an omitted key, mirroring
  `write_gate_baseline`'s own rule so `read_gate_waiver` can distinguish "waived
  nothing" from "not waived".
- **The waiver survives resume.** A test runs gate entry twice against the same
  gate file with the flag passed only on the first run, and asserts the second
  run proceeds without the flag. This is the criterion that rejects a
  flag-only design; assert it directly.
- The waiver write is **committed** via `commit_bookkeeping` on the path that
  writes it. A test asserts this: an uncommitted frontmatter write silently
  reverts on the next `git reset --hard` (#199's class of bug, the same reason
  0051 commits its green-probe record).
- A malformed or partial `waiver:` block reads as **no waiver** and the gate
  halts. A test asserts each of: block absent, block not a mapping, `sha`
  missing, `failing` missing.
- A waiver whose `sha` does not match the current baseline `sha` does not apply.
  A test asserts this separately from the failing-set case — the tree moved, the
  waiver is stale.
- `read_gate_waiver`, `write_gate_waiver` and `waiver_covers_baseline` are
  importable: `python3 -c "from specfuse.loop.loop import read_gate_waiver,
  write_gate_waiver, waiver_covers_baseline"` exits 0.
- `baseline_waiver_active` (T01's predicate) now resolves against the real
  frontmatter, and T01's tests still pass unchanged.
- Every new `subprocess.run` (if any) declares `check=` explicitly (`PLW1510`).

**Flag-scope table.** `--waive-baseline` is a behavior flag (`.specfuse/rules/planning-discipline.md` §3).

| Code path | Gated by flag? | Why |
|---|---|---|
| `write_gate_waiver` at gate entry | yes | the flag's only job is to record the decision once |
| the `preexisting_gate_failure` halt branch | yes — skipped when the waiver covers the baseline | this is the third exit the feature exists to add |
| `probe_baseline` / `gate_baseline_check` | no | the probe still measures the full truth; only the response changes |
| T01's subtraction at the outcome layer | no — it reads the **stored waiver**, not the flag | which is why the decision survives resume |
| `--no-baseline-probe` (0051/T02) | no | independent switch; disables the probe entirely, unaffected by this one |
| `verify()` | no | untouched, as in T01 |

**Do not touch.** `verify()`; `probe_baseline` and the probe's measurement logic;
T01's `subtract_baseline_failures` (call it, do not edit it); the escalation and
proceed message text (T04 owns both — this WU may emit a minimal factual line);
tracking-issue emission (T03). `.git/`, secrets. The driver owns git. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
symbol-import check above, plus T01's test module still green. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if the proceed path cannot be
placed after `gate_baseline_check` without reordering the existing gate-entry
side effects (the status flip, the event emission, the bookkeeping commit) — a
reorder there can double-emit bookkeeping, and FEAT-2026-0051/T01 carried the
same trigger for the same reason. Also block if writing `waiver:` alongside
`baseline:` in the same frontmatter turns out to reflow or corrupt the gate file:
that would break 0051's shipped `baseline:` reader, and a human must decide
before you work around it. If `write_gate_waiver` is absent from the files you
edited, emit `status: blocked` — do not claim complete. Blocked is respectable
(`result-contract.md` rule 4).
