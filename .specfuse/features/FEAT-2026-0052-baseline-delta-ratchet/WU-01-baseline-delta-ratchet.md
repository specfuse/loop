---
id: FEAT-2026-0052/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 6.00
oracle_env: macos_local
produces_driver_helper: subtract_baseline_failures, baseline_waiver_active
produces:
  - specfuse/loop/loop.py
  - tests/test_baseline_ratchet.py
model: sonnet
effort: medium
---

# Subtract the recorded baseline from a work unit's failing gates

**Objective.** Add the baseline-delta ratchet: when a gate carries an active
waiver, a work unit's attempt is classified `failed` only on failures **beyond**
the recorded baseline set, so pre-existing debt stops blocking while anything a
work unit newly introduces still fails normally.

**Context.** First WU of FEAT-2026-0052; read `PLAN.md` in this folder for the
scope boundary, the existing-mechanism verdict, and the escalation-predicate
answers this WU makes executable. This is the direct successor to
FEAT-2026-0051, which shipped the pre-flight probe and the baseline record but
deliberately left the "proceed anyway" path unbuilt.

**The single most important constraint in this WU: `verify()` is not yours to
change.** `verify()` (`specfuse/loop/loop.py:3762`) returns `(ok, report)` and is
the exit oracle for every work unit in every downstream project. FEAT-2026-0051/T01
was told to block rather than alter it, and that decision stands. The subtraction
belongs at the **outcome layer** — `execute_unit_attempt` (`loop.py:4068`), the
function whose docstring already enumerates `"passed"`, `"failed"` and
`"files_changed_mismatch"` and which already holds the `files_changed_mismatch`
guard, the closest existing relative of what you are adding.

Three seams already exist and must be **reused, not reimplemented**:

- `read_gate_baseline(gate_file)` (`loop.py:3976`) returns
  `{"sha", "probed_at", "failing"}` or `None` when the block is absent or
  malformed. `failing` is a list of
  `{"gate", "failure_class", "failure_signature"}`.
- `parse_gate_failure_signature(report)` (`loop.py:660`) maps a gate report to
  `(failure_class, failure_signature)` — the **same** key shape the baseline
  stores. FEAT-2026-0051/T01's WU stated this was built that way for this
  ratchet. The delta is a set comparison over an existing key; do not write a
  new parser.
- `_run_gate_set` / `verify()` already produce the per-gate report you compare
  against. Read them; change neither.

The waiver's storage format is **T02's** to design and write. For this WU, treat
"is there an active waiver for this gate" as a single small predicate
(`baseline_waiver_active`) that T02 will fill in against real frontmatter — give
it a signature T02 can implement behind, and keep every ratchet test driving it
through an injected/stubbed value rather than a real gate file.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`verification-discipline.md`) apply. Do not restate them.

**Acceptance criteria.**

- `tests/test_baseline_ratchet.py::test_new_failure_still_fails_under_waiver`
  exists and **fails on HEAD before this WU's edits** (the module does not yet
  exist). With a waiver active and a baseline recording gate `dependency-audit`,
  a work unit whose attempt fails on a **different** gate is classified `failed`.
  This is the criterion that separates this design from the per-gate mute issue
  #234 rejected; it is the first test for that reason.
- After this WU's edits that same test passes, and so does
  `tests/test_baseline_ratchet.py::test_baseline_failure_is_subtracted_under_waiver`
  — a work unit failing **only** on a gate present in the recorded baseline, with
  a matching `failure_class` and `failure_signature`, is not classified `failed`.
- `tests/test_baseline_ratchet.py::test_no_waiver_is_byte_identical` passes: with
  no active waiver, classification is unchanged from today for both a passing and
  a failing attempt. This is PLAN.md's escalation-predicate answer made
  executable — assert it directly, do not infer it from the two tests above.
- A failure whose gate name matches a baseline entry but whose
  `failure_signature` **differs** is classified `failed`. A test asserts this
  specific case: same gate, new failure, still blocks.
- `subtract_baseline_failures` and `baseline_waiver_active` are importable:
  `python3 -c "from specfuse.loop.loop import subtract_baseline_failures,
  baseline_waiver_active"` exits 0.
- `subtract_baseline_failures` is a pure function over
  `(live_failures, baseline_failures)` returning the residual list — no file
  reads, no git calls, no globals. A test calls it directly with literal lists.
- `verify()` is unchanged. Assert it mechanically:
  `git diff HEAD -- specfuse/loop/loop.py` shows no edit inside `verify()`'s
  body, and the existing verify tests pass untouched. If the ratchet cannot be
  built without editing `verify()`, that is an escalation, not a judgement call —
  see below.
- A waived-through failure is still **recorded**, not erased: the attempt's
  outcome payload names the subtracted entries, so `events.jsonl` distinguishes
  "passed" from "failed but waived". A test reads the payload and asserts the
  subtracted set is present.
- Every new `subprocess.run` (if any) declares `check=` explicitly — the lint
  gate enforces `PLW1510` since FEAT-2026-0037.

**Flag-scope table.** The waiver is a behavior flag (`.specfuse/rules/planning-discipline.md` §3).

| Code path | Gated by waiver? | Why |
|---|---|---|
| `execute_unit_attempt` → outcome classification | yes | the one place the subtraction runs |
| `verify()` and `_run_gate_set` | no | untouched by design; they still report the raw verdict |
| gate-entry probe (`gate_baseline_check`) | no | T02 owns the halt-vs-proceed decision; the probe itself still measures the full truth |
| `doc` / `plannext` gate sets | no | 0051 probes only `code`; the ratchet inherits that boundary |
| the `files_changed_mismatch` guard | no | orthogonal — a waived gate failure must not suppress a files-changed mismatch |

**Do not touch.** `verify()`'s body and its `(ok, report)` contract; the
subprocess hang defenses in `_run_gate_set` (stdin=DEVNULL, process-group kill);
the gate frontmatter writer and the waiver's own storage format (T02 owns both);
the escalation message text (T04 owns it); tracking-issue emission (T03).
`.git/`, secrets. The driver owns git. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` (tests, lint,
security, coverage ≥ 90%, leak-scan, the bats suites) plus the symbol-import
check above. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if the subtraction cannot be
placed at the outcome layer without changing `verify()`'s observable
`(ok, report)` contract — that contract is every WU's exit oracle in every
downstream project and changing it is out of scope for this WU and this feature.
Also block if `parse_gate_failure_signature` turns out **not** to produce
comparable keys for a baseline entry and a live failure: FEAT-2026-0051/T01
asserted it does, and if that assertion is wrong the whole feature's design rests
on it and a human must know before you work around it. If
`subtract_baseline_failures` is absent from the files you edited, emit
`status: blocked` — do not claim complete. Blocked is respectable
(`result-contract.md` rule 4).
