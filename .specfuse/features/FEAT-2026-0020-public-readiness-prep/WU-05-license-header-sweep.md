---
id: FEAT-2026-0020/T05
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 0.80
duration_seconds: 175.55
cost_usd: 0.399444
input_tokens: 14
output_tokens: 8699
---

# Confirm Apache-2.0 license headers across .specfuse/ source files; record gaps in AUDIT.md

**Objective.** Iterate every `*.py` / `*.sh` / `*.md` file under `.specfuse/scripts/`,
`.specfuse/skills/`, `.specfuse/rules/`, and `.specfuse/templates/`, check for an
Apache-2.0 license header (or SPDX `Apache-2.0` short-form), and record findings + the
proposed header block to insert per missing-header file in `AUDIT.md §licenses`.

**Context.** Part of FEAT-2026-0020 gate 1 (audit). Repo carries Apache-2.0 LICENSE at
the root; per-file headers make the license explicit when files are read out of context
(e.g. someone vendors a single skill into their own project). Roadmap detail: spot checks
already show most files have headers — this is the mechanical confirm.

Binding rules + PLAN.md "Notes" apply.

Red-test exempt: audit/report WU, no behavioral surface introduced.

**Acceptance criteria.**

- Iteration covers exactly: `find .specfuse/scripts .specfuse/skills .specfuse/rules
  .specfuse/templates -type f \( -name '*.py' -o -name '*.sh' -o -name '*.md' \)`.
- Header detected if EITHER `Apache License, Version 2.0` OR SPDX-style
  `SPDX-License-Identifier: Apache-2.0` appears within the first 30 lines of the file.
- `AUDIT.md §licenses` heading exists with a table: `file | has-header (✓/✗) |
  proposed-header-block (when ✗)`.
- For each missing file, the proposed header block is the exact text to insert (language-
  appropriate comment style — `#` for `.py` / `.sh`, `<!-- … -->` for `.md`).
- Summary line: `Total files scanned: N. Missing headers: M. Coverage: X%.`
- This WU also records, separately, the verdict on the repo-root `LICENSE` file
  (presence + Apache-2.0 identity).

**Do not touch.**

- File edits inserting the headers (T06 or gate 2 owns the insertion if trivial; per
  roadmap detail the operator's call).
- Files outside the four enumerated directories.
- Other audit WUs' AUDIT.md sections.
- `.git/`.
- See `.specfuse/rules/never-touch.md`.

**Verification.**

- Code gates per `.specfuse/verification.yml`.
- Symbol-presence: `grep -q "^## §licenses$" AUDIT.md`.
- Oracle environment: `macos_local`.

**Escalation triggers.**

- Coverage drops below the operator-pre-approved threshold (default ≥80%) — many missing
  headers signals a different remediation strategy (script-insert vs hand-edit) →
  `status: blocked` to discuss before T06.
- If §licenses heading is absent after edits, emit `status: blocked`.
