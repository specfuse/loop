---
id: FEAT-2026-0016/T05
type: implementation
effort: medium
status: pending
attempts: 0
planned_cost_usd: 1.20
generated_surfaces: []
produces_driver_helper: []
---

# `/gate-status` per-attempt + re-arm surfacing from events.jsonl

**Objective.** Extend the `/gate-status` skill to render, for each
`blocked_human` WU under the active feature, a per-attempt table
sourced from that WU's `attempt_outcome` events (T01-emitted) plus
the WU frontmatter's `re_arm_count` + latest `re_arm_history`
entry (T02-shipped, T06-written). Removes the operator's "grep
driver stdout via my session" workaround.

**Context.** This is `FEAT-2026-0016/T05`. Consumer #2 of the
attempt_outcome data layer. The skill today (§4 in
`.specfuse/skills/gate-status/SKILL.md`) quotes only the latest
`human_escalation` event verbatim; the structured per-attempt
detail T01 now writes into events.jsonl is not surfaced. T05
adds the missing read.

The skill lives at `.specfuse/skills/gate-status/SKILL.md` and is
discovered via the symlink at `.claude/skills/gate-status` per
the project's `CLAUDE.md` convention. The symlink already exists;
no skill-discovery work is in scope here.

Cross-reference the driver contracts shipped by gate 1:

- T01 (loop.py line ~476) — `emit_attempt_outcome` writes events
  with payload fields `attempt`, `outcome`, `failure_class`,
  `failure_signature`, `failure_excerpt`, `cost_usd`,
  `duration_seconds`, `re_arm_count`, etc., per PLAN.md
  § "Event payload shape — `attempt_outcome` v1". T05 reads
  those fields; their shape is locked at v1.
- T02 (`WU.template.md` frontmatter notes) — `re_arm_count`,
  `re_arm_history` (a list of dicts with at least a `reason` key
  + `timestamp`, `prior_status`, `prior_attempts`,
  `prior_cost_usd`, `prior_duration_seconds`). T05 reads the
  last element of `re_arm_history` for the surfaced reason.

Reference binding rules:
`.specfuse/rules/result-contract.md`, `.specfuse/rules/never-touch.md`.

**§10 helper-duplication pre-flight.** Before authoring:

```bash
# Existing gate-status skill body (the file being edited)
wc -l .specfuse/skills/gate-status/SKILL.md

# Confirm no other skill already surfaces per-attempt tables
grep -rln 'attempt_outcome' .specfuse/skills/

# Confirm the symlink discovery path is in place (don't recreate)
ls -la .claude/skills/gate-status

# Confirm T01's emitted event field names (the source of truth for the read)
grep -nE 'emit_attempt_outcome|"failure_class"|"failure_signature"' .specfuse/scripts/loop.py | head -20
```

**Acceptance criteria.**

1. **Skill section added — Per-attempt table.** Add a new
   subsection under §4 ("For each blocked_human WU, synthesize
   the diagnosis") of
   `.specfuse/skills/gate-status/SKILL.md` titled
   `#### Per-attempt outcomes`. The subsection instructs the
   skill operator to:
   - Read `events.jsonl` for the active feature, filter to
     `event_type == "attempt_outcome"` events whose
     `correlation_id` matches the blocked WU's id.
   - Render a table:
     ```
     attempt | outcome | failure_class | failure_signature | duration | cost
     ```
     One row per matching event, in event-file order. Cost is
     dollars to 4 decimals; duration is seconds to 3 decimals;
     `failure_class` / `failure_signature` show `-` when null.
   - Quote `failure_excerpt` verbatim ONLY for the latest failing
     attempt (the one immediately preceding the
     `human_escalation`), to keep the report scannable.

2. **Skill section added — Re-arm history.** Add a sibling
   subsection `#### Re-arm history` under §4. Instructs:
   - Read the blocked WU's frontmatter `re_arm_count` (default
     0 when absent) and `re_arm_history` (default empty list).
   - If `re_arm_count == 0`: print `re_arm_count: 0 — never
     re-armed`. Stop the subsection.
   - If `re_arm_count > 0`: print
     `re_arm_count: <N>  latest re-arm reason: "<reason>"`
     where `<reason>` is `re_arm_history[-1].reason` quoted
     verbatim. Also print the latest entry's `timestamp` if
     present.

3. **Trace-every-claim rule preserved.** The existing
   skill's "Hard rules" §2 ("Trace every claim to a file") still
   applies. The new subsections cite the source file:
   `events.jsonl` for the table, WU frontmatter for the re-arm
   history. The skill MUST NOT infer per-attempt outcomes from
   anything other than `attempt_outcome` events.

4. **Backward compatibility — legacy events.** Features whose
   events.jsonl predates T01's standardized emission (FEAT-2026-0015
   and earlier) lack `attempt_outcome` records for some attempts.
   The skill renders the table with whatever rows exist; if NO
   `attempt_outcome` events exist for the WU, print
   `(no per-attempt events; legacy feature — see human_escalation
   above)`. The skill MUST NOT raise or stop on missing events.

5. **Read-only contract intact.** The skill stays read-only. No
   writes to events.jsonl, WU frontmatter, or any other file.
   The existing "Hard rules" §1 already states this; the new
   subsections do not introduce a write surface.

6. **Skill version bumped.** Update the `## Version` section at
   the bottom of `SKILL.md` with a new entry `v0.3.` noting the
   per-attempt + re-arm subsections were added consuming
   FEAT-2026-0016 gate-1's `attempt_outcome` + `re_arm_*`
   contracts. Preserve the existing v0.2 / v0.1 entries.

7. **Symbol-existence checks** before declaring complete:

   ```bash
   # a. New subsections present (exact heading match)
   grep -qE '^#### Per-attempt outcomes$' .specfuse/skills/gate-status/SKILL.md
   grep -qE '^#### Re-arm history$' .specfuse/skills/gate-status/SKILL.md

   # b. attempt_outcome event_type referenced in the skill body
   grep -qE 'event_type.*attempt_outcome|attempt_outcome.*event_type' .specfuse/skills/gate-status/SKILL.md

   # c. re_arm_count + re_arm_history both referenced
   grep -qE 're_arm_count' .specfuse/skills/gate-status/SKILL.md
   grep -qE 're_arm_history' .specfuse/skills/gate-status/SKILL.md

   # d. Version bumped to v0.3
   grep -qE '^\*\*v0\.3\.' .specfuse/skills/gate-status/SKILL.md

   # e. Working-tree diff touches the skill file
   { git diff --name-only HEAD; git ls-files --others --exclude-standard; } | grep -qx '.specfuse/skills/gate-status/SKILL.md'

   # f. Symlink discovery path still works (read-only check)
   test -L .claude/skills/gate-status
   ```

   Any check failing → `status: blocked`. Do NOT flip frontmatter
   as substitute.

**Do not touch.** Files this WU may edit:
- `.specfuse/skills/gate-status/SKILL.md` (one file)

No edits to: `.specfuse/scripts/loop.py` (T01 owns event shape),
`.specfuse/templates/WU.template.md` (T02 owns frontmatter
contract), the `unblock-wu` skill (T06 owns), `.claude/skills/`
symlinks (already in place), tests, other features, secrets,
`.git/`. Driver owns all git; edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `doc` gate set in `.specfuse/verification.yml`
(skill files are documentation, not code) + AC7 grep checks.
This WU adds no importable symbols, so no Python existence
checks apply. A real-feature smoke-run is out of scope here; the
operator validates the skill produces the expected output the
next time a WU sits at `blocked_human`.

**Escalation triggers.**

1. **Completeness.** AC7 (a) any of the four grep lines failing →
   `status: blocked`. Subsections missing or mis-titled.
2. **Spec disagreement with T01's event shape.** If T01's emitted
   `attempt_outcome` payload field names disagree with what this
   WU's AC1 instructs the skill to read (e.g. T01 wrote
   `signature` instead of `failure_signature`), DO NOT silently
   adapt the skill — emit `status: blocked` naming the field
   mismatch. The contract is locked at v1 in PLAN.md; a divergence
   is a T01 bug, not a T05 spec problem to swallow.
3. **Spec disagreement with T02's frontmatter shape.** Same shape
   as #2 for `re_arm_count` / `re_arm_history` field names. T02's
   `WU.template.md` notes are authoritative; if the skill spec
   reads `re_arm_log` instead of `re_arm_history` (the v1 name),
   emit `status: blocked`.
4. **Skill-symlink discovery broken.** If `test -L
   .claude/skills/gate-status` fails (the symlink is gone or
   broken), do NOT recreate it from this WU — that's a project
   structural change beyond this WU's scope. Emit `status: blocked`
   with the missing symlink named.
