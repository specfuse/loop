---
id: FEAT-2026-0070/T06
type: implementation
status: draft
attempts: 0
planned_cost_usd: 2.00
produces:
  - specfuse/loop/loop.py
  - tests/test_autoclose_deferral_visibility.py
oracle_env: macos_local
produces_driver_helper: build_autoclose_debt_enumeration
model: sonnet
effort: medium
---

# Auto-close writes the concrete deferred-verification worklist, not a paragraph saying it didn't

**Objective.** Make both auto-close stub writers enumerate, criterion by criterion, the
acceptance criteria no session walked — and emit a machine-readable debt marker — so an
auto-closed gate leaves a **worklist** rather than an absence. No agent dispatch.

**Context.** This is `FEAT-2026-0070/T06`, the load-bearing WU of gate 2 and the direct
answer to **#241**. Read `PLAN.md`, `GATE-02.md`, and `GATE-02-REVIEW.md` in this folder
first. Depends on `FEAT-2026-0070/T05`, which puts the acceptance-criteria slicer in
`specfuse/loop/_wu_sections.py` where `loop.py` can import it.

**What exists today, and why it is not enough.** `append_stub_retrospective_intermediate`
(`loop.py:3574`) and `write_stub_retrospective_terminal` (`loop.py:3420`) already emit a
`## What the loop did NOT verify (gate N)` heading — issue #157 added it, and
`tests/test_autoclose_deferral_visibility.py` guards it. But the section's body is a fixed
paragraph that says the list "was **not** enumerated". It names the gap; it does not close
it. `[FEAT-2026-0039/G2-CLOSE]` is what that costs: gate 1 auto-closed at $0.00 against a
$5.00 estimate and moved the walk into the terminal close, where it cost **more**, because
the session doing it had not written those WUs. The saving was a debt entry.

**The design constraint that shapes this WU.** The predicate cannot reason over acceptance
criteria — but it does not need to. The WU files are on disk, their `**Acceptance
criteria.**` sections are already machine-sliceable, and the gate's WU list is already in
`PLAN.md`'s graph. **Read them and write them out.** That is a string-building change
inside a function that already runs, in-process, at close time.

**Read `recheck_terminal_verdict` (`loop.py:3281`) before starting.** T02's primitive is
the shape to copy: it locates WU files from the `PLAN.md` graph and reads their frontmatter
**from disk**, never from an in-memory `WorkUnit` — the auto-close path does not have one
loaded for the WUs it is enumerating. Same property applies here.

Binding rules in `.specfuse/rules/` apply.

**Acceptance criteria.**

1. **Red test:**
   `tests/test_autoclose_deferral_visibility.py::TestAutoCloseDebtEnumeration::test_intermediate_stub_enumerates_each_substantive_wu_criteria`
   exists and **fails on HEAD before this WU's edits** —
   `python3 -m unittest tests.test_autoclose_deferral_visibility.TestAutoCloseDebtEnumeration -v`
   exits non-zero. It builds a feature directory with a two-WU gate whose WU bodies carry
   distinct, greppable acceptance criteria, calls
   `append_stub_retrospective_intermediate`, and asserts each WU's ID **and** the text of
   each of its criteria appears in `RETROSPECTIVE.md`. No such class exists on HEAD.
2. The same test passes after this WU's edits.
3. A new helper `build_autoclose_debt_enumeration(feature_dir, gate_number) -> str` in
   `loop.py` returns the enumeration block, and **both** stub writers call it. One builder,
   two callers — a second copy of the format in the terminal writer is the divergence
   `[FEAT-2026-0023/G1-CLOSE]` names, in a different place.
4. **The enumeration lists only substantive WUs.** It imports the type filter from
   `gate_eval` rather than redefining it in `loop.py` (`_NON_SUBSTANTIVE_TYPES`,
   `gate_eval.py:35`, single call site at `:262`; promote it to a public name and keep the
   private name as an alias if you prefer, but do not fork the set). One test asserts a
   gate's `close-intermediate` and `plan-next` WUs are absent from the output.
5. **The block carries a machine-readable marker**, first line of the section, exactly:
   `<!-- specfuse:autoclose-debt gate={N} wus={comma-separated sub-ids} criteria={int} predicate={version} -->`
   `FEAT-2026-0070/T07`'s invariant matches `gate=(\d+)` against it and nothing else, so
   the `gate=` token's spelling is a contract between the two WUs — a test asserts the
   literal, not just "a comment is present".
6. **Each criterion is rendered as its own line, prefixed `deferred:`,** under its WU's
   ID and file name, first line only, truncated to 200 characters with a trailing `…` when
   longer. The existing prose (this gate auto-closed, the ceremony did not run, who
   reconciles it) is **kept** — the enumeration is added beneath it, not swapped for it.
7. **No silent cap.** If the gate's total criterion count exceeds 40, list the first 40 and
   emit a final literal line `- … {K} further criteria not listed; read the WU files` with
   the real K. A truncation that does not announce itself reads as "that was all of them".
   One test covers a >40-criteria gate.
8. **Degrades rather than raises.** A WU file that is missing, unreadable, or has no
   `**Acceptance criteria.**` section produces a `deferred: <criteria not parseable>` line
   naming the file, not an exception. Auto-close runs inside the close path; a traceback
   here fails a gate that was otherwise on-plan. One test per case.
9. The three existing tests in `tests/test_autoclose_deferral_visibility.py` still pass
   **unedited** — `## What the loop did NOT verify`, `Gate 2's close`, the gate heading, and
   `gate_total_cost: $1.23` are all still emitted.
10. `python3 -c "from specfuse.loop.loop import build_autoclose_debt_enumeration"` exits 0
    (`authoring-work-units` §9 symbol-existence check).
11. `python3 -m unittest discover -s tests -v` exits zero, in particular
    `tests/test_gate_eval_intermediate_wiring.py`, `tests/test_gate_eval_terminal_wiring.py`,
    and `tests/test_force_full_close.py`.
12. Coverage stays ≥ 90%.

**Cost-reintroduction trade (`[FEAT-2026-0039/G2-CLOSE]`).** This WU lands on the **keeps
the saving** side, and it must be able to prove it. The enumeration is built by reading
files the driver has already located, inside a function the auto-close path already calls.
It dispatches no session, spawns no subprocess, and calls no model. A design that reached
for an agent to summarise the criteria would have traded #241's defect for exactly the cost
auto-close exists to avoid — and would have been the *second* time this repo paid it.
**State the observed wall-clock delta of the auto-close path in the RESULT block** as the
evidence, not the claim.

**Do not touch.**

- `evaluate_auto_close` and the `AutoCloseDecision` dataclass (`gate_eval.py:285`, `:38`) —
  the predicate's inputs, checks, and `predicate_version` are unchanged. This WU changes
  what auto-close *writes*, never what it *decides*. Adding a field to the frozen dataclass
  would ripple into `tests/test_gate_eval*.py` for no gain; the builder reads `PLAN.md`
  itself.
- `maybe_auto_close_terminal` / `maybe_auto_close_intermediate` (`loop.py:3495`, `:3624`) —
  callers only. Their short-circuits (`_already_auto_closed`, `_close_wu_disables_auto_close`,
  `_gate_impl_deliverables_present`) are correct and out of scope.
- `mark_close_wu_auto_closed` (`loop.py:3462`) — the frontmatter flip, including
  `verdict: met`, is unchanged.
- **The terminal writer's missing idempotency guard.**
  `append_stub_retrospective_intermediate` skips when a `## Gate N … auto-closed` heading
  already exists; `write_stub_retrospective_terminal` has no such guard and appends
  unconditionally. Pre-existing asymmetry, guarded upstream by `_already_auto_closed`.
  Out of scope — handled as an open question in `GATE-02-REVIEW.md` for the human to rule
  on at arming. Do not add a guard here on your own initiative.
- `fire_terminal_flips`, `recheck_terminal_verdict`, `assert_terminal_flips_fired` — gate
  1's surfaces. Read `recheck_terminal_verdict` for its disk-reading shape; change nothing.
- `specfuse/loop/_wu_sections.py` — `FEAT-2026-0070/T05` owns it. Import it; do not edit it.
- `.git/`, secrets. The driver owns all git operations. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (tests, ruff, bandit,
coverage ≥ 90%, leak-scan, the four `bats` gates). Scoped red/green proof:
`python3 -m unittest tests.test_autoclose_deferral_visibility -v`. Symbol check per AC10.

> Sandbox note: the four `bats` gates call `mktemp -d` in `setup`, which the default session
> sandbox denies before any assertion runs (`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`).
> Report which sandbox each gate ran under.

**Escalation triggers.** Emit `status: blocked` if the gate's WU list or the WU bodies
cannot be read from disk at the point the stub writers run — the writers take
`(feature_dir, gate_number, decision)` and nothing else, and if that is not enough to reach
`PLAN.md`'s graph then the enumeration needs a signature change, which is an operator
decision about the auto-close call contract rather than something to work around with a
module-level global. Also block if honouring AC3 (one builder, two callers) would require
the terminal and intermediate sections to diverge in shape: that would mean the two paths
genuinely need different enumerations, and the reviewer should decide that, not this
session. Blocked is a respectable outcome (`result-contract.md` rule 4).
