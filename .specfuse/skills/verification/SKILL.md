---
name: specfuse-verification
description: Run and report Specfuse work-unit verification gates before declaring a task done. Use this skill whenever you are executing a Specfuse work unit and need to confirm the work is actually complete — running tests, coverage, linting, compiler-warning, and security-scan gates and reporting structured evidence. Use it even when the work "looks done"; declaring complete without running the gates is the single most common failure mode and this skill exists to prevent it.
---

# Specfuse verification

The discipline: **state intent, act, verify, report.** This skill covers the *verify*
step. You do not get to decide a work unit is done — the gates do. Your job is to run
them, read the output honestly, and put the evidence in the RESULT block. The driver
re-runs these same gates as the real exit oracle, so a dishonest self-report buys
nothing but a wasted attempt.

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

Read `.specfuse/verification.yml`, select the set for your type, and run every command
in it. If a command is missing for a gate your acceptance criteria need, that is itself
a `blocked` condition — report it; do not skip the gate.

## The code gates (mergeability)

For `implementation` units, all of the following are **mandatory** and mirror the
branch-protection rules the eventual PR must satisfy. An agent that passes its own
checks but would fail branch protection has done the wrong thing.

- **All tests pass.** Zero failures, zero errors.
- **Coverage ≥ 90%.** Below threshold is a fail, not a warning.
- **Zero compiler/build warnings.** Warnings are failures here.
- **Lint clean.** No violations.
- **Security scan clean (OWASP).** No findings at the configured severity.

## The plannext gate (forward-design integrity)

For a `plan-next` unit, "done" means the next gate you drafted is actually
dispatchable. The `plannext` set runs `lint_plan.py`, which checks every drafted WU has
valid frontmatter and the five mandatory sections, every dependency edge resolves, and
the closing sequence is present and ordered. A malformed draft must fail here — at the
human's review point — not three gates later mid-dispatch.

## How to run and interpret

1. Run each gate command exactly as declared. Do not substitute a "quick" check.
2. A non-zero exit code is a fail. Some tools exit 0 with failures in stdout — know
   your tools and check output, not just exit codes.
3. Capture concrete evidence: the failing test name, the coverage number, the specific
   lint rule. "Tests pass" is not evidence; "47 passed, coverage 91.2%" is.

## Reporting

Roll each gate's result into the RESULT block (see `.specfuse/rules/result-contract.md`).
If **any** mandatory gate fails, do **not** emit `status: complete`. Fix the cause and
re-run (you are inside a bounded retry), or, if an escalation trigger applies, emit
`status: blocked` with the failing evidence and stop.

## Worked example — failing run, retried

```
$ pytest -q  ->  46 passed, 1 failed  (exit 1)
```
Tests fail → do NOT report complete. Read the failure, fix the cause, re-run the full
gate set. If a gate fails for a reason you cannot fix within the unit's boundaries
(e.g. it requires touching generated code), emit `status: blocked`.
