---
id: FEAT-2026-0032/G1-PLAN
type: plan-next
status: pending
attempts: 0
planned_cost_usd: 1.00
generated_surfaces: []
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Gate 1 plan-next — draft gate 2's work units

**Objective.** Draft gate 2's substantive work units (Git-Bash gate-command
execution + interpreter/CLI resolution on Windows) and write `GATE-02-REVIEW.md`
so a human can review and arm the gate-1 → gate-2 boundary.

**Context.** This is `FEAT-2026-0032/G1-PLAN`. Gate 1 proved the driver imports
and walks on native Windows. Gate 2's definition of done (see `GATE-02.md`): a
real `verification.yml` gate command runs green through Git-Bash on
`windows-latest`; `python3`-style commands and `SMOKE_IMPORT_RE` resolve to the
Windows interpreter; the `claude` CLI resolves. The pre-declared `G2-CLOSE`
placeholder (`WU-92-gate-2-close.md`) is the terminal close; insert the
substantive WUs *before* it and update its `depends_on`.

Sketch to turn into real WUs (verify each call site against current source first):
- **Git-Bash routing.** Resolve `bash.exe` from the Git-for-Windows install
  (e.g. `git --exec-path` → sibling `bin/bash.exe`, or `shutil.which("bash")`);
  route the `shell=True` gate runner (`loop.py:~1735, ~1890`) and the
  smoke-import runner through `[bash, "-c", cmd]` on Windows. Fail loud with an
  actionable "install Git for Windows" message if no bash is found.
- **`python3` normalization.** Resolve `python3` → the running interpreter for
  gate commands and the `SMOKE_IMPORT_RE` literal (`loop.py:~1700`) on Windows.
- **Bare-`claude` resolution.** `CLAUDE_CMD` (`loop.py:79`) is invoked
  `shell=False` (`loop.py:~1609`); on Windows resolve via `shutil.which("claude")`
  honoring `PATHEXT` so `claude.cmd` is found.

**Acceptance criteria.**
1. `GATE-02-REVIEW.md` exists, listing each drafted gate-2 WU with its `id`,
   `file`, proposed `depends_on`, and a one-line rationale tracing to gate 2's
   DoD.
2. Each drafted gate-2 WU file is written with `status: draft` and the full
   five-section body, following `/authoring-work-units` (red-test-first §12 for
   behavior-introducing WUs; `produces` / `produces_driver_helper` §13).
3. `PLAN.md`'s gate-2 `work_units` graph is updated to list the drafted WUs
   *before* `G2-CLOSE`, and `G2-CLOSE`'s `depends_on` is updated to depend on
   them.
4. A **Cross-repo contracts** table is present in `GATE-02-REVIEW.md` for any
   value that lives in an external system (e.g. the Git-for-Windows `bash.exe`
   relative path, the `windows-latest` runner's interpreter names), each with its
   authoritative source and a checked/unchecked status (§8) — none locked until
   verified.
5. No gate-2 WU is flipped to `pending` — arming is the human's job at review.

**Do not touch.** Gate-1 WU files (`done`). Secrets, `.git/`. The driver owns all
git — edit files only.

**Verification.** The `plannext` gate set. `lint_plan.py` must still PASS on the
feature folder after the graph edits.

**Escalation triggers.**
- If gate 1's outcome makes a gate-2 WU unnecessary or reveals a missing one
  (e.g. a second `shell=True` site surfaced), adjust the draft and note it in the
  review — do not mechanically copy this sketch.
- If any Cross-repo contract value cannot be verified against its source at draft
  time, leave the AC that depends on it explicitly unlocked in the review rather
  than inventing the value (§8).
