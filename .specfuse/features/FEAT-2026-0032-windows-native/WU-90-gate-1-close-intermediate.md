---
id: FEAT-2026-0032/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: pending
attempts: 0
planned_cost_usd: 1.20
generated_surfaces: []
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Gate 1 close-intermediate — retrospective + lessons + docs, single session

**Objective.** Close gate 1 by writing `RETROSPECTIVE.md` (with the mandatory
`## Cost analysis` and `## What the loop did NOT verify` sections), appending
durable lessons to `.specfuse/LEARNINGS.md`, and reconciling any docs/roadmap
state implied by gate 1's substantive WUs.

**Context.** This is `FEAT-2026-0032/G1-CLOSE-INTERMEDIATE`. Gate 1 made the
driver import and run on native Windows:
- T01 — portable working-tree lock (`_filelock.py`; `fcntl` → cross-platform)
- T02 — cross-platform gate-timeout kill (`killpg`/`SIGKILL` → `taskkill`)
- T03 — Windows home-path redaction (`_HOME_PATH_RE`) — the leak fix
- T04 — `windows-latest` CI leg (import + `--dry-run`)

This is the **runtime-unblock gate**: it proves the driver *loads and walks* on
Windows. Gate 2 wires *gate-command execution* through Git-Bash. The retro
should be explicit that much of T01/T02's Windows behavior is proven only by
mocked branch-selection tests in the Linux sandbox plus the CI leg's import +
`--dry-run` — see the deferred-verification section.

Reference: `.specfuse/rules/result-contract.md`,
`.specfuse/templates/WU.template.md` notes on `close-intermediate`,
`.specfuse/skills/verification/SKILL.md`.

**Acceptance criteria.**
1. `RETROSPECTIVE.md` exists at the feature-folder root, non-empty, with a
   `## Gate 1` section and a sub-section per substantive WU (T01–T04): attempts,
   blockers, surprises.
2. A `## Cost analysis` section is present, reconciling `planned_cost_usd` (from
   PLAN.md and per-WU frontmatter) against actual spend (from events.jsonl), per
   WU and aggregated to the gate-1 total, with the delta named. Variance > 50%
   carries a one-paragraph rationale. Reference predicate v1 criteria 3 (1.5×)
   and 4 (2×).
3. A `## What the loop did NOT verify` section is present, enumerating each
   acceptance criterion whose verification was deferred (loop-sandbox limit,
   cross-repo coordination, real-system access). For each: the criterion, why
   deferred, and where verification actually happens. Required even when empty
   (write `(nothing — every acceptance criterion was verified in-loop)`). Known
   entries to expect: T02's real-Windows timeout `taskkill` path (not exercised
   by the import+`--dry-run` CI leg → gate 2's gate execution); T01's contended
   SIGKILL lock handoff (post-merge manual). If the list exceeds 2 entries OR
   30% of the gate's criteria, flag the gate's sizing under `## What I'd change`.
4. `.specfuse/LEARNINGS.md` is appended with ≥ 1 durable lesson, or an explicit
   `[FEAT-2026-0032/G1-CLOSE-INTERMEDIATE] nothing generalizes` note.
5. Docs/roadmap state implied by gate 1 is reconciled (e.g. a "Git-Bash / Windows
   prereq" note if any user-facing doc already claims platform support); no
   invented scope.

**Do not touch.** Gate-1 WU implementation files (T01–T04 are `done`); gate-2
files. Secrets, `.git/`. The driver owns all git — edit files only.

**Verification.** The `doc` gate set for closing WUs. The driver's hollow-pass
guards enforce the `## Cost analysis` and `## What the loop did NOT verify`
sections at execution time; this WU lists them as explicit AC so the contract is
visible.

**Escalation triggers.**
- If `RETROSPECTIVE.md` cannot be written because a gate-1 WU's actual outcome
  is missing from events.jsonl, emit `status: blocked` with the gap.
- If the deferred-verification list would exceed the sizing threshold in AC 3,
  do not silently pass — record it and flag the sizing, per the AC.
