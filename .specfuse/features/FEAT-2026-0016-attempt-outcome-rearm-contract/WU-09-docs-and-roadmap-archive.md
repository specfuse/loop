---
id: FEAT-2026-0016/T09
type: implementation
effort: low
status: done
attempts: 1
planned_cost_usd: 0.50
generated_surfaces: []
produces_driver_helper: []
duration_seconds: 183.858
cost_usd: 0.549118
input_tokens: 23
output_tokens: 7114
---

# Docs — methodology.md per-attempt event contract + roadmap-archive merged-in 0016 scope

**Objective.** Document the `attempt_outcome` per-attempt event
contract (v1 payload shape, locked taxonomy) and the re-arm
WU-frontmatter additions in `docs/methodology.md` so the
methodology spec reflects the data layer this feature ships. Move
the FEAT-2026-0016 detail section in `.specfuse/roadmap.md`
(the originally-planned re-arm-contract scope, now folded into
this feature per PLAN.md "Folded scope") to
`.specfuse/roadmap-archive.md`, with a back-link from the
roadmap row's Detail cell.

**Context.** This is `FEAT-2026-0016/T09`. The docs counterpart
to T07/T08's code-side consumers — closes the doc-trail loop so
future features that touch attempt outcomes (or future
predicate-v2 work) reference a documented contract, not
events.jsonl by example. The roadmap-archive move mirrors the
documented folding pattern (FEAT-2026-0012 → FEAT-2026-0015) and
keeps `.specfuse/roadmap.md` lean now that all the original
0016 scope ships under this feature.

Cross-reference contracts:

- PLAN.md "Event payload shape — `attempt_outcome` v1" — the
  authoritative payload schema. T09 documents the shape in
  methodology.md without restating; reference the PLAN.md
  pointer for the field-by-field reader.
- PLAN.md "Re-arm contract — WU frontmatter additions" — the
  six new frontmatter fields. Documented in T02's WU.template.md
  notes already; T09 cross-links from methodology.md to the
  template (one fact, one home — methodology.md narrates the
  contract, the template is the field-level spec).
- `roadmap-archive` skill — `.specfuse/skills/roadmap-archive/`
  is the canonical archiver. T09 may invoke its pattern by
  hand-edit (the skill is operator-driven; this WU performs the
  same edit deterministically as a docs WU).

Reference binding rules: `.specfuse/rules/result-contract.md`,
`.specfuse/rules/never-touch.md`.

**§10 helper-duplication pre-flight.** Before authoring:

```bash
# Confirm methodology.md section structure (where the new prose attaches)
grep -nE '^## ' docs/methodology.md | head -20

# Locate the existing FEAT-2026-0016 detail section in roadmap.md
grep -n '^## FEAT-2026-0016' .specfuse/roadmap.md

# Confirm roadmap-archive format (anchor + back-link convention)
grep -nE '^## FEAT-2026|<a id=' .specfuse/roadmap-archive.md | head -10

# Confirm the roadmap row's Detail cell format for done features (the back-link target)
grep -nE 'roadmap-archive\.md#feat-2026' .specfuse/roadmap.md | head -5
```

**Acceptance criteria.**

1. **`docs/methodology.md` extended with per-attempt event
   contract.** Append a new subsection under §3 ("Deterministic
   auto-close path (FEAT-2026-0018)") OR add a sibling §3a — at
   the author's discretion based on §10 pre-flight — titled
   `### Per-attempt outcome events (FEAT-2026-0016)`. Body
   describes:
   - One `attempt_outcome` event emitted per dispatched attempt,
     standardized payload (`outcome`, `failure_class`,
     `failure_signature`, `failure_excerpt`, `cost_usd`,
     `duration_seconds`, `attempt`, `re_arm_count`).
   - Locked-at-v1 `outcome` taxonomy: `passed | failed |
     blocked | zero_token | files_changed_mismatch |
     post_pass_invariant_failed | closing_deliverable_missing |
     smoke_import_failed`.
   - Locked-at-v1 `failure_class` taxonomy: `tests | lint |
     security | coverage | symbol_existence | bandit | other |
     null`.
   - Pointer to PLAN.md (or the equivalent
     `.specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/PLAN.md`
     anchor) for the field-by-field schema. Do NOT restate the
     full payload — one fact, one home.

2. **`docs/methodology.md` extended with re-arm WU-frontmatter
   contract.** Append a paragraph (placement at the author's
   discretion, near §2 "Ownership" or §4 "The five-section
   work-unit contract") naming the six re-arm fields
   (`re_arm_count`, `re_arm_history`, `cumulative_cost_usd`,
   `cumulative_duration_seconds`, `cumulative_input_tokens`,
   `cumulative_output_tokens`) with a pointer to
   `.specfuse/templates/WU.template.md` frontmatter notes for
   the field-level spec. Same one-fact-one-home discipline as
   AC1.

3. **FEAT-2026-0016 detail section moved to
   `roadmap-archive.md`.** Cut the entire `## FEAT-2026-0016`
   section from `.specfuse/roadmap.md` (lines ~293+ as of this
   feature's start; confirm with the §10 pre-flight grep).
   Paste it into `.specfuse/roadmap-archive.md` under a
   matching `## FEAT-2026-0016 — Per-attempt outcome events +
   re-arm contract + audit trail` heading, preserving the
   original detail content verbatim. Add an HTML anchor
   immediately before the heading (matching the existing
   archive convention surfaced by the §10 pre-flight, e.g.
   `<a id="feat-2026-0016"></a>` if that is the convention in
   use).

4. **Roadmap row Detail cell back-linked.** In
   `.specfuse/roadmap.md`, the FEAT-2026-0016 row's Detail cell
   (currently `—`) becomes `[→ archive](roadmap-archive.md#feat-2026-0016)`,
   matching the format used for every other archived feature
   row. The row's status column is NOT changed by this WU
   (driver flips `done` post-close).

5. **Methodology.md changes additive only.** T09 does NOT
   modify existing methodology.md content beyond inserting the
   new subsection(s) — no rewording of existing paragraphs, no
   reordering of sections. Reviewers should see two clean
   additions plus the AC4 row edit + AC3 cut/paste.

6. **Symbol-existence + structure checks** before declaring
   complete:

   ```bash
   # a. methodology.md mentions the new event-type contract
   grep -qE 'Per-attempt outcome events' docs/methodology.md
   grep -qE 'attempt_outcome' docs/methodology.md

   # b. methodology.md mentions the re-arm frontmatter additions
   grep -qE 're_arm_count' docs/methodology.md
   grep -qE 're_arm_history' docs/methodology.md
   grep -qE 'cumulative_cost_usd' docs/methodology.md

   # c. roadmap.md no longer carries the FEAT-2026-0016 detail section
   ! grep -qE '^## FEAT-2026-0016' .specfuse/roadmap.md

   # d. roadmap-archive.md DOES carry the FEAT-2026-0016 detail section now
   grep -qE '^## FEAT-2026-0016' .specfuse/roadmap-archive.md

   # e. Roadmap row Detail cell back-links to the archive
   grep -E '^\| FEAT-2026-0016' .specfuse/roadmap.md | grep -qE 'roadmap-archive\.md#feat-2026-0016'

   # f. Working-tree diff covers the three expected files
   diff_paths=$({ git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u)
   echo "$diff_paths" | grep -qx 'docs/methodology.md'
   echo "$diff_paths" | grep -qx '.specfuse/roadmap.md'
   echo "$diff_paths" | grep -qx '.specfuse/roadmap-archive.md'
   ```

   Any check failing → `status: blocked` naming the failure.

**Do not touch.** Files this WU may edit:
- `docs/methodology.md` (additive subsection(s) only)
- `.specfuse/roadmap.md` (cut FEAT-2026-0016 detail section;
  update Detail cell of the matching table row)
- `.specfuse/roadmap-archive.md` (paste FEAT-2026-0016 detail
  section, with anchor)

No edits to: `.specfuse/templates/WU.template.md` (T02 owns;
methodology.md cross-links to it), `LEARNINGS.md` (G3-CLOSE
appends), PLAN.md, GATE-NN.md, other feature folders, T01–T08's
surfaces, skills, secrets, `.git/`. Driver owns all git; edit
files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `doc` gate set in
`.specfuse/verification.yml` + AC6 grep checks. No
Python-importable surface; no unit tests. The methodology.md
additions are reviewable prose — the reviewer at gate-3 close
confirms the pointers resolve and the prose reads cleanly.

**Escalation triggers.**

1. **Completeness.** AC6 (a)–(f) any failing → `status: blocked`.
   Documentation incomplete or roadmap edits malformed.
2. **Methodology.md restructure pending.** If methodology.md is
   actively being restructured by another feature in flight
   (the §10 pre-flight surfaces sections in unexpected order or
   §3 numbering off), name the gap and emit `status: blocked` —
   adding to a section that is about to move is wasted churn.
3. **Roadmap-archive anchor convention drift.** If the
   pre-flight surfaces NO existing `<a id="feat-2026-NNNN">`
   pattern in roadmap-archive.md, the archive convention may
   have changed. Do NOT invent an anchor format — match what's
   already there (lowercase, FEAT-2026-NNNN form), or emit
   `status: blocked` naming the convention question.
4. **Detail-cell back-link format drift.** If the §10
   pre-flight shows existing done-feature rows using a back-link
   format different from `[→ archive](roadmap-archive.md#feat-2026-NNNN)`
   (e.g. a different arrow glyph, a different anchor prefix),
   match the prevailing format. The roadmap row should look
   indistinguishable from neighboring archived rows.
