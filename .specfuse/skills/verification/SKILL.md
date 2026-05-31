---
name: specfuse-verification
description: Run and report Specfuse work-unit verification gates before declaring a task done. Use this skill whenever you are executing a Specfuse work unit and need to confirm the work is actually complete — running tests, coverage, linting, compiler-warning, and security-scan gates and reporting structured evidence. Use it even when the work "looks done"; declaring complete without running the gates is the single most common failure mode and this skill exists to prevent it.
---

# Specfuse verification

The discipline: **state intent, act, verify, report.** This skill covers the *verify*
step. You do not get to decide a work unit is done — the gates do. Your job is to run
them, read the output honestly, and put the evidence in the RESULT block. The driver
re-runs these same gates as the real exit oracle (see
[`../../rules/result-contract.md`](../../rules/result-contract.md)), so a dishonest
self-report buys nothing but a wasted attempt.

## Where the gates come from

Verification commands are declared per repository in `.specfuse/verification.yml`,
grouped into sets. Which set applies depends on your work unit's `type`:

| WU `type`        | Gate set   | What it proves |
|------------------|------------|----------------|
| `implementation` | `code`     | The code is mergeable |
| `retrospective`  | `doc`      | The retro artifact exists and changed |
| `lessons`        | `doc`      | LEARNINGS.md grew with rule-shaped entries |
| `docs`           | `doc`      | Docs/roadmap reflect what was built |
| `plan-next`      | `plannext` | The drafted next gate is structurally dispatchable |

Read `.specfuse/verification.yml`, select the set for your type, and run **every**
command in it. If a command is missing for a gate your acceptance criteria need, that
is itself a `blocked` condition — report it; do not skip the gate.

A `verification.yml` that is missing, invalid YAML, or missing a mandatory set for the
WU type you are executing makes the repo not ready for autonomous work. Emit
`status: blocked` with a precise reason — do not guess at what the gate "should" be.

## The code gates (mergeability)

For `implementation` units, all of the following are **mandatory** and mirror the
branch-protection rules the eventual PR must satisfy (where the repo has any). An
agent that passes its own checks but would fail those protections has done the wrong
thing.

- **All tests pass.** Zero failures, zero errors.
- **Coverage ≥ 90%.** Below threshold is a fail, not a warning.
- **Zero compiler/build warnings.** Warnings are failures here.
- **Lint clean.** No violations.
- **Security scan clean (OWASP-aligned).** No findings at the configured severity.

The gates are a **conjunction**: all must pass. A single failure means the unit is
not done.

## The plannext gate (forward-design integrity)

For a `plan-next` unit, "done" means the next gate you drafted is actually
dispatchable. The `plannext` set runs `lint_plan.py`, which checks every drafted WU
has valid frontmatter and the five mandatory sections, every dependency edge
resolves, and the closing sequence is present and ordered. A malformed draft must
fail here — at the human's review point — not three gates later mid-dispatch.

## The stale-artifact trap (a verification.yml authoring rule)

Gate commands declared in `.specfuse/verification.yml` **should be self-contained**.
Avoid `--no-build`, `--no-restore`, or any equivalent "skip-build" flag that makes
a gate command silently run against whatever binaries are already on disk.

The failure mode this guidance prevents is the **stale-artifact trap**: a gate
that embeds `--no-build` runs against pre-existing `bin/`, `obj/`, or
stack-equivalent artifacts that may be out of sync with the current source — after
a fresh checkout, after new test files have been added, after a symbol rename. A
`tests` gate using `--no-build` against stale artifacts can pass while new tests
are never actually executed, or fail for reasons unrelated to the change under
test. Either outcome corrodes the trust model the gate set exists to uphold.

The driver runs gate commands directly and is intentionally dumb about stacks — it
does not run a per-stack pre-build step. The mitigation is in the
`verification.yml` author's hands: declare gates that build/restore as part of
their own invocation (e.g. `dotnet test` without `--no-build`, `pytest` without a
separate `pip install` step) so the gate is correct regardless of what artifacts
the disk already holds.

If a stack genuinely requires a build step before tests are runnable, fold it into
the `tests` gate's command (e.g. `dotnet build && dotnet test --no-build` as a
single shell pipeline) so the build always precedes the gate and the inputs are
always fresh. The pre-build is part of the gate, not a thing the agent is
expected to know to run.

## How to run and interpret

For each gate:

1. **Resolve the command** from the relevant set in `.specfuse/verification.yml`. Run
   it exactly as declared. Do not substitute a "quick" check.
2. **Invoke** with the repo root as the working directory (or `{feature_dir}` for
   commands that substitute it).
3. **Capture** exit code, stdout, and stderr.
4. **Apply gate-specific interpretation:**

   | Gate | Pass condition |
   |---|---|
   | tests | Exit `0`. If a `passing_pattern` is declared, it must also match stdout. |
   | coverage | Exit `0` **and** parsed line coverage ≥ the declared threshold. |
   | warnings | Exit `0` (the command is responsible for failing on warnings, typically via warnings-as-errors). |
   | lint | Exit `0`. |
   | security | Exit `0` **and** the parsed report contains zero high/critical findings. |
   | build | Exit `0`. |

5. **Distinguish pass from invalid-run.** Exit `0` is necessary but not always
   sufficient. If the declared behavior is not met — a coverage command exited `0`
   but `report_path` does not exist, a security-scan command exited `0` but produced
   no parseable report — the gate is **fail with an invalid run**, not pass. Invalid
   runs count as a failed cycle for the spinning threshold.
6. **Capture concrete evidence.** The failing test name. The coverage number. The
   specific lint rule. "Tests pass" is not evidence; `"412 passed, coverage 0.94"`
   is. If raw output is too large, excerpt the most load-bearing line and reference
   where the full output lives.

Some tools exit `0` with failures buried in stdout — know your tools, and check
output, not just exit codes. A `passing_pattern` in `verification.yml` exists for
exactly that case.

## Reporting

Roll each gate's result into the RESULT block (see
[`../../rules/result-contract.md`](../../rules/result-contract.md)). The block is the
single-repo analog of the orchestrator surface's structured `task_completed` payload;
keep them aligned so a fold-in is a rename, not a redesign.

If **any** mandatory gate fails, do **not** emit `status: complete`. Fix the cause
and re-run the **full** gate set from the top — partial re-runs are forbidden,
because a later gate may have been masked by the earlier failure. Or, if an
escalation trigger applies, emit `status: blocked` with the failing evidence and
stop.

Before emitting:

- Re-read the produced artifact (the changed files, the appended LEARNINGS entry,
  the drafted next-gate WU files). The writing tool reports success for the action
  it took, not for the property you wanted.
- Confirm no secret-looking value appears in the evidence you are about to write.
  See [`../../rules/security-boundaries.md`](../../rules/security-boundaries.md).
- Confirm any correlation IDs you cite match the pattern in
  [`../../rules/correlation-ids.md`](../../rules/correlation-ids.md).

## Failure handling

A failed gate puts you in one of three situations, in order of first-to-try:

1. **Correctable locally.** Read the failing evidence, make a corrective edit, and
   re-run the **full** gate set from the top. A cycle is complete only when the
   whole set has been re-run green. A run that fixes the original failure but
   introduces a new failure counts as a **failed** cycle, not a passed one.
2. **Spinning threshold reached.** The driver dispatches at most three fresh
   attempts (see `loop.py`'s `MAX_ATTEMPTS`). If you are on attempt three and still
   failing, emit `status: blocked` with the precise evidence rather than spending
   the cycle on guesswork. The driver will escalate to a human; that is the right
   outcome, not a personal failure.
3. **Fundamentally blocked.** If the failing gate points at something outside the
   unit's boundaries — generated code that needs to change, a missing dependency
   the unit cannot create, a spec ambiguity the unit cannot resolve — emit
   `status: blocked` immediately with `blocked_reason` naming the boundary.

## Worked example — clean run

A `T01` implementation unit. The repo's `.specfuse/verification.yml` declares the
five `code` gates with Python commands.

1. Read `.specfuse/verification.yml`. Valid, all five `code` gates present.
2. Run `tests` (`pytest -q`): exit `0`, evidence `"127 passed"`, duration `8.1s` →
   **pass**.
3. Run `coverage` (`coverage report --fail-under=90`): exit `0`, line coverage
   `0.93` → **pass**.
4. Run `warnings`: exit `0` → **pass**.
5. Run `lint` (`ruff check .`): exit `0` → **pass**.
6. Run `security` (`bandit -r src -ll`): exit `0`, 0 high/critical → **pass**.
7. Re-read changed files. Confirm correlation ID `FEAT-2026-0007/T01` matches the
   WU file. Confirm no secret-looking value in evidence.
8. Emit RESULT with `status: complete` and the per-gate evidence. Stop.

## Worked example — failing run, retried

Same unit. The first pass introduces a test regression.

1. Run `tests`: exit `1`, evidence
   `"Failed: 1, Passed: 126 — test_orders.py::test_reject_missing_email"` →
   **fail**. Cycle 1 failure.
2. Read the failing test; the validation check was over-permissive. Fix the
   handler. Re-run **all five gates** from `tests`.
3. `tests` now passes (`127/127`); `coverage` `0.91` passes; `warnings` passes;
   `lint` fails — the new code path has a style violation. Cycle 2 failure.
4. Apply the lint fix. Re-run all five gates from the top.
5. Full pass on cycle 2 re-run. Emit RESULT with `status: complete` and the
   final green evidence. The failed cycles are reconstructable from the
   per-attempt notes the driver wrote under the feature's `work/` directory
   but do not appear in the success report.

Had cycle 2 also failed, attempt 3 would have been the last. After that the unit
is escalated to a human — not retried indefinitely. Honesty about failure earlier
in the cycle is cheaper than three fresh attempts chasing a `complete` that
verification keeps rejecting.

## What "verify" does not mean

- It does not mean "I thought about it and it seems right." The check must be
  mechanical.
- It does not mean "the previous step succeeded." Tools return success for the
  action they took, not for the property you want to guarantee.
- It does not mean "a similar unit has passed before." Nothing about a prior run
  transfers to this one.
- It does not mean "I ran some of the gate commands." Run all of them; if one is
  legitimately not applicable, that is a `blocked` condition to report, not a
  shortcut to take.

## Forbidden shortcuts

- Reporting `status: complete` and then "let me go verify." The order is the
  discipline. Verify, then report.
- Editing `verification.yml` to weaken or skip a failing gate. That is a
  [`never-touch.md`](../../rules/never-touch.md)-class violation — you do not
  weaken the checks to unblock yourself.
- Re-reading the artifact as a visual sanity check and then reporting without
  running the declared commands. Visual inspection complements the commands; it
  does not replace them.
- Running the commands once, seeing a failure, fixing the artifact, and reporting
  without running them again. Every verification cycle ends with a green run of
  the full set, or the cycle is not complete.
