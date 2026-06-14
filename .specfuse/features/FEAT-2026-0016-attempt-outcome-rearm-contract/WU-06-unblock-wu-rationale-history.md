---
id: FEAT-2026-0016/T06
type: implementation
effort: high
status: draft
attempts: 0
planned_cost_usd: 1.50
generated_surfaces: []
produces_driver_helper: []
---

# `/unblock-wu` mandatory re-arm rationale + `re_arm_history` write

**Objective.** Extend the `/unblock-wu` skill so that every re-arm
(sandboxed or unsandboxed) requires a mandatory one-line
rationale, appends a new `re_arm_history` entry to the WU's
frontmatter, and increments `re_arm_count`. T02's driver
`detect_rearm_dispatch` (already shipped) reads the incremented
count on the next dispatch and fires `fold_cumulative_on_rearm`
automatically.

**Context.** This is `FEAT-2026-0016/T06`. Consumer #3 of the
data layer. The skill today (`.specfuse/skills/unblock-wu/SKILL.md`
§3) prompts for "what changed?" as **required free text**, but
captures it nowhere durable — it lives in the operator's
terminal-scrollback and dies. T06 makes the rationale a
load-bearing audit signal: written to the WU's
`re_arm_history` list (the structured shape T02 documented in
`WU.template.md`), surfaced by `/gate-status` (T05), and
referenced by the driver's `re_arm_dispatched` event payload.

Cross-reference the driver contracts shipped by gate 1:

- T02 (loop.py line ~639) — `detect_rearm_dispatch` returns
  `True` when `re_arm_count > 0 AND cost_usd > 0`. Therefore
  `/unblock-wu` MUST write the incremented `re_arm_count`
  BEFORE the operator runs `loop.py` for the re-arm; otherwise
  the cumulative-fold misfires. The handshake is "skill writes
  frontmatter → operator runs driver → driver detects on first
  dispatch".
- T02 (loop.py line ~2362) — the driver's `re_arm_dispatched`
  event reads `re_arm_history[-1].reason` for its `reason`
  payload field. T06's write of the history entry is the
  upstream source for that event's `reason`. A re-arm without
  the history write produces a `re_arm_dispatched` event with
  `reason: ""`.

The skill body lives at `.specfuse/skills/unblock-wu/SKILL.md`;
discovered via `.claude/skills/unblock-wu` symlink (already in
place — verified by `ls -la .claude/skills/`).

Reference binding rules:
`.specfuse/rules/result-contract.md`, `.specfuse/rules/never-touch.md`.

**§10 helper-duplication pre-flight.** Before authoring:

```bash
# Existing unblock-wu skill body (the file being edited)
wc -l .specfuse/skills/unblock-wu/SKILL.md

# Existing rationale prompt (currently free text for r and u)
grep -nE 'what changed|rationale|free text' .specfuse/skills/unblock-wu/SKILL.md

# Existing T02 driver contract for re_arm_count + re_arm_history
grep -nE 'detect_rearm_dispatch|re_arm_history|re_arm_count' .specfuse/scripts/loop.py | head -10

# Confirm T02's WU.template.md frontmatter notes (the schema source of truth)
grep -nE 're_arm_count|re_arm_history' .specfuse/templates/WU.template.md
```

**Acceptance criteria.**

1. **Rationale is mandatory — empty rejected.** Update the per-WU
   decision section (§3 of `SKILL.md`) so that on `r` (sandboxed)
   and `u` (unsandboxed) re-arm choices, the operator's rationale
   input is required and non-empty. If the operator submits an
   empty string (or whitespace-only), the skill prints
   `re-arm rationale required — type a one-line reason or choose s/a` and
   re-prompts the same WU. The skill MUST NOT proceed to a
   frontmatter write with an empty rationale.

2. **Skill writes `re_arm_history` entry.** On accept of an `r`
   or `u` re-arm with a non-empty rationale, the skill writes a
   new entry appended to the WU's frontmatter `re_arm_history`
   list. Entry shape:

   ```yaml
   - timestamp: <ISO 8601 UTC, e.g. 2026-06-15T12:34:56+00:00>
     prior_status: blocked_human
     prior_attempts: <int — the WU's pre-re-arm `attempts`>
     prior_cost_usd: <float — the WU's pre-re-arm `cost_usd`, default 0.0 when absent>
     prior_duration_seconds: <float — the WU's pre-re-arm `duration_seconds`, default 0.0>
     reason: "<operator's one-line rationale, trimmed>"
   ```

   The five fields are the contract documented in T02's
   `WU.template.md` notes for `re_arm_history`. The `reason` field
   is what T02's driver `re_arm_dispatched` event quotes.

3. **Skill increments `re_arm_count`.** Read the WU's existing
   `re_arm_count` (default 0 when absent); write back
   `re_arm_count + 1`. Performed atomically with the
   `re_arm_history` append (same frontmatter-write call). This
   increment is what T02's `detect_rearm_dispatch` keys on.

4. **Write ordering — frontmatter before driver dispatch.** The
   skill writes the incremented `re_arm_count` + appended
   `re_arm_history` entry as part of the SAME frontmatter update
   that flips `status: blocked_human → pending` and `attempts: N →
   0`. The "Print the resume command" step (§5) MUST come AFTER
   this write. Document this ordering in a new note line at the
   top of §3.

5. **Unsandboxed branch keeps its existing rationale field.** The
   `u` (unsandboxed) branch already writes `unsandboxed: true` +
   `unsandboxed_rationale: "<...>"` to frontmatter. T06 does NOT
   change that pair. The new `re_arm_history` entry's `reason`
   field is THE SAME rationale string the operator typed at the
   prompt (one input, two homes: `unsandboxed_rationale` for the
   driver's sandbox gate; `re_arm_history[-1].reason` for the
   cross-cycle audit trail).

6. **Skill version bumped.** Update the `## Version` section at
   the bottom of `SKILL.md` to a new entry `v0.2.` noting the
   mandatory rationale + `re_arm_history` write + `re_arm_count`
   increment. Preserve the existing v0.1 entry.

7. **No changes to the abandon / skip branches.** `/unblock-wu`'s
   `a` (abandon) and `s` (skip) per-WU choices DO NOT write to
   `re_arm_history` and DO NOT increment `re_arm_count`. They are
   not re-arms. The skill body must distinguish: the prompt,
   refusal, and writes in AC1–AC4 fire on `r` and `u` only.

8. **Symbol-existence checks** before declaring complete:

   ```bash
   # a. Mandatory-rationale refusal line present
   grep -qE 're-arm rationale required' .specfuse/skills/unblock-wu/SKILL.md

   # b. re_arm_history entry shape documented (all five field names)
   for f in timestamp prior_status prior_attempts prior_cost_usd prior_duration_seconds reason; do
     grep -qE "^[[:space:]]+$f:" .specfuse/skills/unblock-wu/SKILL.md || { echo "missing re_arm_history field doc: $f"; exit 1; }
   done

   # c. re_arm_count increment instruction present
   grep -qE 're_arm_count.*\+.*1|increment.*re_arm_count|re_arm_count + 1' .specfuse/skills/unblock-wu/SKILL.md

   # d. Write ordering note present (frontmatter before resume)
   grep -qE 'BEFORE.*driver|before.*operator runs|before.*resume command' .specfuse/skills/unblock-wu/SKILL.md

   # e. Version bumped to v0.2
   grep -qE '^\*\*v0\.2\.' .specfuse/skills/unblock-wu/SKILL.md

   # f. Working-tree diff touches the skill file
   { git diff --name-only HEAD; git ls-files --others --exclude-standard; } | grep -qx '.specfuse/skills/unblock-wu/SKILL.md'
   ```

   Any check failing → `status: blocked`. Do NOT flip frontmatter
   as substitute.

**Do not touch.** Files this WU may edit:
- `.specfuse/skills/unblock-wu/SKILL.md` (one file)

No edits to: `.specfuse/scripts/loop.py` (T02 owns
`detect_rearm_dispatch` / `fold_cumulative_on_rearm` /
`re_arm_dispatched` event), `.specfuse/templates/WU.template.md`
(T02 owns the frontmatter notes for these fields), the
`gate-status` skill (T05 owns), the `arm-gate` /
`abandon-feature` skills (out of scope), tests, other features,
secrets, `.git/`. Driver owns all git; edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `doc` gate set in `.specfuse/verification.yml`
+ AC8 grep checks. The skill itself is exercised by the operator
at the next `blocked_human` recovery; a unit-test surface for
skill prose is out of scope here.

**Escalation triggers.**

1. **Completeness.** AC8 (a)–(e) any failing → `status: blocked`.
   Spec text missing.
2. **T02 contract disagreement.** If the `re_arm_history` entry
   shape this WU specs (the five fields in AC2) disagrees with
   what T02 wrote into `WU.template.md`'s frontmatter notes,
   STOP — emit `status: blocked` naming the disagreement. The
   template is authoritative; this WU's spec adapts to the
   template, not the other way around.
3. **Handshake races.** If a careful read of T02's
   `detect_rearm_dispatch` suggests it could fire on the WRONG
   dispatch (e.g. the driver re-reads frontmatter at a different
   point than T02's notes claim), document the race in RESULT
   and emit `status: blocked`. Operator decides whether to extend
   T02 (separate WU) or proceed with documented limitation.
4. **Skill-as-interactive-only constraint.** The skill is
   declared "Run interactively" (today's hard rule). The
   mandatory-rationale prompt MUST be non-bypassable — there is
   no flag, env var, or `--rationale=...` shortcut that fills it
   in unprompted within this WU's scope. If the implementation
   exposes such a bypass, emit `status: blocked` — that's
   scope creep beyond T06 and erodes the audit signal.
