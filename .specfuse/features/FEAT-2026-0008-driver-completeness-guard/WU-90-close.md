---
id: FEAT-2026-0008/G1-CLOSE
type: close
model: claude-opus-4-7
effort: high
status: pending
attempts: 0
---

# Gate 1 close — combined closing ceremony

**Objective.** Close this single-gate feature in one session: write the
retrospective, promote durable lessons, reconcile docs and roadmap, and
write the terminal feature-arc verdict — the union of the four classic
closing ceremonies (`close` type, valid here because the feature has
exactly one gate).

**Context.** This is `FEAT-2026-0008/G1-CLOSE`. Read this feature's
`events.jsonl` (the gate slice), the gate's commits, the root
`.specfuse/LEARNINGS.md`, and PLAN.md's `roadmap_goal`. Single-gate, so
no next gate to forward-design. Reference the binding rules under
`.specfuse/rules/`; honor `result-contract.md`, `never-touch.md`. The
driver owns all git.

This feature's whole point was to close the hollow-pass gap. The close
ceremony has a special diagnostic responsibility: **read the events.jsonl
and inspect `git diff main..HEAD --stat` to confirm the three guard
helpers actually exist** before writing the verdict. If any of T01/T02/
T03 hollow-passed despite the guards (recursive failure), the
retrospective must name it loudly and the verdict must NOT claim the
goal is met.

**Acceptance criteria.**
1. `RETROSPECTIVE.md` exists in this feature folder: per WU, what worked,
   what failed and why, attempt count, and any rule/template/boundary
   missing or ambiguous. Cite specific events.jsonl evidence per WU.
2. **Diagnostic check (NEW, this feature only).** The retrospective
   includes a section `## Guard-helper existence audit` that runs and
   reports:
   - `grep -c "def is_zero_token_attempt" .specfuse/scripts/loop.py`
   - `grep -c "def verify_files_changed" .specfuse/scripts/loop.py`
   - `grep -c "def extract_smoke_imports" .specfuse/scripts/loop.py`
   - `grep -c "def run_smoke_imports" .specfuse/scripts/loop.py`
   - `ls tests/test_loop_zero_token_guard.py tests/test_loop_files_changed_guard.py tests/test_loop_smoke_runner.py`
   Each expected to be `1` / present. Any `0` or missing file is a
   hollow-pass — name it loudly in the retrospective and in the verdict.
3. Durable, generalizable lessons (if any) appended to the root
   `.specfuse/LEARNINGS.md`, tagged `FEAT-2026-0008/G1-CLOSE`.
   Feature-specific noise stays in `RETROSPECTIVE.md`. If nothing
   generalizes, append nothing and say so.
4. Docs and roadmap reconciled: this feature's row in
   `.specfuse/roadmap.md` reflects whether the goal was met (status
   `done` if the audit passed; `done` with a note if partial; do NOT
   leave as `active`). The PLAN.md `status:` is flipped to `done` in
   this WU — the close ceremony owns this flip, not a follow-on commit.
5. A `# Feature-arc verdict` section is appended to `RETROSPECTIVE.md`
   stating whether `roadmap_goal` is met, citing AC 2's audit. If any
   guard hollow-passed, the verdict must recommend the appropriate
   recovery action (manual land vs FEAT-2026-0009 vs revert).

**Do not touch.** Source code (`loop.py`, `lint_plan.py`, etc.) — this
is a closing unit, it does not change behavior. Other WU files,
generated directories, secrets, `.git/`. You write `RETROSPECTIVE.md`,
append to `LEARNINGS.md`, update `roadmap.md`, flip `PLAN.md` status —
nothing else.

**Verification.** The `plannext` gate set in `.specfuse/verification.yml`
(`lint_plan.py` on this feature — structural validity preserved). Plus
the `doc` gates (file exists / something changed).

**Escalation triggers.**
1. **Audit reveals hollow pass.** If AC 2's audit shows any of the four
   guard helpers absent, do NOT write the verdict as "goal met". Write
   the retrospective honestly and emit `status: blocked` with a
   `blocked_reason` naming which guards are missing — recovery requires
   a human decision (manual reland vs revert vs FEAT-2026-0009).
2. **Conflicting roadmap state.** If `roadmap.md` already shows this
   feature as `done` (e.g. another close path raced this one), do not
   overwrite — read the existing state, reconcile in the verdict, and
   stop. Two `done` flips with conflicting summaries is worse than one.
