---
id: FEAT-2026-0016/T08
type: implementation
effort: medium
status: blocked_human
attempts: 0
planned_cost_usd: 1.20
generated_surfaces: []
produces_driver_helper: []
duration_seconds: 189.821
cost_usd: 0.403617
input_tokens: 18
output_tokens: 8621
---

# `/learnings-suggest` skill — cluster `failure_signature` across features, surface candidate LEARNINGS entries

**Objective.** Add a new read-only skill at
`.specfuse/skills/learnings-suggest/SKILL.md` (discoverable via
`.claude/skills/learnings-suggest`) that scans `attempt_outcome`
events across every feature folder under `.specfuse/features/`,
clusters non-passing attempts by `(failure_class,
failure_signature)`, and surfaces clusters whose count crosses a
configurable threshold as candidate LEARNINGS entries — with the
operator deciding whether to promote each candidate. The skill
does NOT auto-append to `.specfuse/LEARNINGS.md`.

**Context.** This is `FEAT-2026-0016/T08`. Consumer #5 of the
attempt_outcome data layer. The LEARNINGS-promotion pipeline today
(per `LEARNINGS.md` header + `authoring-work-units` SKILL.md §
"This skill distills `.specfuse/LEARNINGS.md`") is
**runs → retrospective → lessons → LEARNINGS.md**, gated by the
human authoring the `lessons` WU. With T01's events now carrying
structured `failure_signature` data, the same signature recurring
across multiple WUs / multiple features is mechanically
discoverable — the skill is the operator's third-eye over that
recurrence.

What the skill is NOT: an auto-appender, a verdict-maker, or a
substitute for `lessons` WUs. The pipeline above is
authoritative; this skill surfaces candidates only.

Skill discovery model (per `.claude/CLAUDE.md`): skills live at
`.specfuse/skills/<name>/SKILL.md`; discovery requires a symlink
at `.claude/skills/<name>` pointing to the SKILL.md (the project
uses `.specfuse/skills/` as canonical and `.claude/skills/` as
the discovery surface). T08 creates both the SKILL.md and the
symlink.

Cross-reference contracts shipped by gate 1:

- T01 — `attempt_outcome` payload fields `failure_class`,
  `failure_signature`, `outcome` per PLAN.md "Event payload
  shape — `attempt_outcome` v1".
- `LEARNINGS.md` entry format documented in its header: one
  bullet per entry, leading `[FEAT-YYYY-NNNN/G<n>-LESSONS]` tag
  citing the originating gate.

Reference binding rules: `.specfuse/rules/result-contract.md`,
`.specfuse/rules/never-touch.md`.

**§10 helper-duplication pre-flight.** Before authoring:

```bash
# Confirm no existing skill already does signature clustering
grep -rln 'failure_signature\|learnings.suggest\|cluster' .specfuse/skills/ 2>/dev/null

# Existing skills' SKILL.md frontmatter shape (model for the new file)
head -10 .specfuse/skills/gate-status/SKILL.md
head -10 .specfuse/skills/authoring-work-units/SKILL.md

# Existing .claude/skills symlinks (model for the new symlink)
ls -la .claude/skills/

# Confirm features directory layout for cross-feature scan
ls -d .specfuse/features/FEAT-* | head -5
```

**Acceptance criteria.**

1. **Skill file created** at
   `.specfuse/skills/learnings-suggest/SKILL.md` with standard
   skill frontmatter:

   ```yaml
   ---
   name: learnings-suggest
   description: Scan attempt_outcome events across features, cluster non-passing attempts by (failure_class, failure_signature), and surface clusters above a configurable threshold as candidate LEARNINGS entries for the operator to promote. Read-only — does NOT auto-append to LEARNINGS.md.
   ---
   ```

   The body declares the skill `Run interactively` (same hard
   rule shape as `/gate-status`), citing
   `.specfuse/rules/result-contract.md` for the read-only
   contract.

2. **Discovery symlink created** at
   `.claude/skills/learnings-suggest` pointing to
   `../../.specfuse/skills/learnings-suggest/SKILL.md` (relative
   symlink, matching the path topology of existing skill
   symlinks — confirm with `ls -la .claude/skills/` at
   pre-flight time).

3. **Skill body documents the four operator-facing steps.**

   - **§1 Scan.** Glob every `.specfuse/features/FEAT-*/events.jsonl`.
     For each file, read line-by-line, parse JSON, retain
     records where `event_type == "attempt_outcome"` and
     `payload.outcome != "passed"`. Skip malformed lines with a
     printed warning (do NOT abort the scan).

   - **§2 Cluster.** Group retained records by the tuple
     `(payload.failure_class, payload.failure_signature)`. For
     each cluster, count occurrences and record the set of
     `correlation_id` values (WU IDs across features) that
     contributed.

   - **§3 Threshold + render.** Default threshold:
     **≥ 2 distinct WUs (correlation_ids) in the cluster** — a
     single WU spinning on the same signature is a per-WU bug,
     not a general lesson. The skill prints a candidate-list
     table sorted by descending cluster size:

     ```text
     # cluster | failure_class | failure_signature | WUs | total attempts
     1         | tests         | test_foo          | 4   | 7
     2         | other         | no_gate_marker    | 3   | 5
     ```

     Above the threshold only. The threshold is an explicit skill
     argument (`--min-wus N`, default `2`) — document the flag
     in the body. Skills are model-driven, so the "flag" is a
     spoken parameter the operator may set; the SKILL.md body
     instructs the operator to surface it explicitly.

   - **§4 Propose-and-confirm per cluster.** For each cluster
     above the threshold, the skill drafts a candidate
     LEARNINGS entry following the format in `LEARNINGS.md`
     header — a bullet beginning
     `[meta/learnings-suggest] <failure_class>/<short signature> recurs across <N> WUs (<list>): ...`
     and asks the operator: `promote / skip / edit?`. The skill
     MUST NOT append to `LEARNINGS.md` on its own — only after
     explicit `promote` (or `edit` followed by accept).

4. **Read-only contract enforced for the scan.** The skill MUST
   NOT write to any `events.jsonl`, any feature folder, or
   `LEARNINGS.md` (except on explicit operator `promote` in §4).
   Document this in a `## Hard rules` section mirroring
   `/gate-status`'s shape.

5. **Trace-every-claim rule.** Every cluster the skill surfaces
   must cite at least one specific `events.jsonl` line (path +
   line number) the operator can verify. Mirrors
   `/gate-status`'s "Hard rules" §2.

6. **Legacy-event tolerance.** Features whose events.jsonl
   predates T01 contain no `attempt_outcome` records and
   contribute nothing to the clusters — the skill renders them
   silently as "no contributing data" (NOT as an error). Mirrors
   T05's legacy-event handling for the same data layer.

7. **Symbol-existence + structure checks** before declaring
   complete:

   ```bash
   # a. Skill file exists and is non-empty
   test -s .specfuse/skills/learnings-suggest/SKILL.md

   # b. Frontmatter shape — name + description present
   grep -qE '^name: learnings-suggest$' .specfuse/skills/learnings-suggest/SKILL.md
   grep -qE '^description: ' .specfuse/skills/learnings-suggest/SKILL.md

   # c. Four numbered sections present (Scan / Cluster / Threshold + render / Propose-and-confirm)
   for sec in '§1 Scan' '§2 Cluster' '§3 Threshold' '§4 Propose-and-confirm'; do
     grep -qF "$sec" .specfuse/skills/learnings-suggest/SKILL.md || { echo "missing section: $sec"; exit 1; }
   done

   # d. Discovery symlink present and valid
   test -L .claude/skills/learnings-suggest
   test -f .claude/skills/learnings-suggest

   # e. Read-only / Hard-rules section present
   grep -qE '^## Hard rules' .specfuse/skills/learnings-suggest/SKILL.md
   grep -qE '(read-only|MUST NOT.*append|MUST NOT.*write)' .specfuse/skills/learnings-suggest/SKILL.md

   # f. attempt_outcome event_type referenced (the data layer this skill consumes)
   grep -qE 'attempt_outcome' .specfuse/skills/learnings-suggest/SKILL.md

   # g. Working-tree diff covers both new files
   { git diff --name-only HEAD; git ls-files --others --exclude-standard; } | grep -qx '.specfuse/skills/learnings-suggest/SKILL.md'
   { git diff --name-only HEAD; git ls-files --others --exclude-standard; } | grep -qx '.claude/skills/learnings-suggest'
   ```

   Any check failing → `status: blocked`. Do NOT flip
   frontmatter as substitute.

**Do not touch.** Files this WU may create:
- `.specfuse/skills/learnings-suggest/SKILL.md` (new)
- `.claude/skills/learnings-suggest` (new symlink → `../../.specfuse/skills/learnings-suggest/SKILL.md`)

Files this WU may NOT edit: `.specfuse/LEARNINGS.md` (the skill
APPENDS to this at promote-time; the WU itself does not), any
existing skill body, `loop.py`, `gate_eval.py`, `lint_plan.py`,
T01–T07's surfaces, any existing `events.jsonl` (scanned
read-only), tests, other features, secrets, `.git/`. Driver owns
all git; edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `doc` gate set in
`.specfuse/verification.yml` (skill files are documentation, not
code) + AC7 grep + symlink checks. This WU adds no importable
Python symbols, so no Python existence checks apply. The skill
itself is exercised by the operator at any time post-ship; a
unit-test surface for skill prose is out of scope.

**Escalation triggers.**

1. **Completeness.** AC7 (a)–(d) any failing → `status: blocked`.
   Skill file missing, frontmatter malformed, or symlink
   absent/broken.
2. **Skill discovery topology drift.** If `.claude/skills/` does
   not use relative symlinks pointing into `.specfuse/skills/`
   (the §10 pre-flight check), do NOT invent a new discovery
   convention — emit `status: blocked` and let the operator
   reconcile.
3. **LEARNINGS append contract drift.** If `LEARNINGS.md`'s
   entry format documented in its header has changed (e.g. a
   new mandatory metadata block) since this WU was drafted, the
   skill's drafting template under §4 must match. Name the
   drift and emit `status: blocked` — the format is
   authoritative.
4. **Cross-feature scan boundary.** The skill scans every
   feature folder under `.specfuse/features/`. If a feature
   folder exists OUTSIDE that path (`.specfuse/features-archive/`,
   etc.), the skill's documented glob misses it. If the §10
   pre-flight surfaces such a folder, name it explicitly in the
   skill body's scope statement; do not silently miss data.
