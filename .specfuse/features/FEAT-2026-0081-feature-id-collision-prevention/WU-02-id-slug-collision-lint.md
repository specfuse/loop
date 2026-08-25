---
id: FEAT-2026-0081/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
produces_driver_helper: _check_id_slug_binding
produces:
  - specfuse/loop/lint_roadmap.py
  - tests/test_lint_roadmap_id_binding.py
model: sonnet
effort: medium
---

# One feature ID, one slug — make a divergence an ERROR at lint time

**Objective.** Add a check to the roadmap linter: a `feature_id` claimed by two
different slugs across `roadmap.md`, `roadmap-archive.md`, feature folder names,
or `PLAN.md` frontmatter is an ERROR, so a collision or a botched manual
renumbering fails the next lint instead of surviving to merge.

**Context.** Second WU of FEAT-2026-0081; read `PLAN.md` in this folder for the
scope boundary, the existing-mechanism verdict, and the draft-time probe numbers
this WU must re-measure. Independent of T01 — no dependency edge, different file.

**This extends a shipped linter; it does not build one.** FEAT-2026-0034 shipped
`specfuse/loop/lint_roadmap.py` as a repo-scoped sibling to `lint_plan.py`,
already wired into `verification.yml`'s `code` set as `roadmap-link-gate` via
`.specfuse/scripts/roadmap_link_gate.py`. Read these before writing:

- `lint_roadmap(repo_root) -> list[Finding]` is the entry point. It returns
  structured findings and **does not raise** — 0034's stated reason is that a
  linter which crashes in a gate cannot distinguish "found a problem" from
  "could not look". Preserve that posture exactly.
- `_check_uniqueness(roadmap_anchors, archive_anchors)` (`lint_roadmap.py:207`)
  is the nearest existing relative and is **not** what this WU needs: it compares
  **anchors**, catching an ID *defined twice*. Its finding text says so. An ID
  claimed by two different slugs is a different property; add a check, do not
  widen that one.
- `_check_section_status` and `_check_blocked_by` are the models for a check that
  reads table rows and detail sections together.

**Why here and not `lint_plan.py`:** `lint_plan` is feature-scoped and
structurally cannot compare two features. 0034 recorded that reasoning when it
built a sibling rather than adding a second mode to a single-job tool.

**Severity flip — probe before you assert.** PLAN.md records a draft-time probe
(78 roadmap rows, no duplicate IDs; 68 IDs across four sources, zero slug
disagreement). Per `[FEAT-2026-0034/G1-CLOSE/re-verify-the-producer-not-the-audit]`,
that is a dated observation, not a current fact. **Re-run it as your first act**
and quote the numbers in your RESULT. A dirty tree means ship the check as WARN
and report the violations — do **not** weaken the rule to make the tree pass.

Binding rules in `.specfuse/rules/` apply. Do not restate them.

**Acceptance criteria.**

- `tests/test_lint_roadmap_id_binding.py::test_same_id_two_slugs_is_an_error`
  exists and **fails on HEAD before this WU's edits** (the module does not yet
  exist). A fixture tree where one `feature_id` appears with two different slugs
  produces a finding at `SEVERITY_ERROR`.
- After this WU's edits that same test passes, and so does
  `tests/test_lint_roadmap_id_binding.py::test_consistent_id_binding_is_clean` —
  a fixture tree where every ID maps to exactly one slug produces **zero**
  findings from this check. This is PLAN.md's escalation-predicate answer made
  executable; assert it directly.
- All four sources participate. Four tests, one per source pair, each pairing a
  correct claim in one source with a divergent slug in another
  (`roadmap.md` ↔ `roadmap-archive.md`, `roadmap.md` ↔ folder name,
  folder name ↔ `PLAN.md` frontmatter, `roadmap.md` ↔ `PLAN.md` frontmatter).
- The finding **names every source and its claimed slug**, not just "conflict".
  A test asserts both slugs and both source names appear in the message. The
  operator's next action is deciding which claim is right; a message that does
  not say what the claims are cannot support that.
- **The probe re-run, on the real tree, quoted in the RESULT:**
  `lint_roadmap(Path("."))` produces zero findings **of this new class** against
  this repository. If it does not, report each violation and ship the check at
  WARN with a one-line note — see the escalation triggers.
- `roadmap-link-gate` still passes on this repo:
  `python3 .specfuse/scripts/roadmap_link_gate.py` exits 0.
- The linter still does not raise on a malformed or missing input. A test feeds
  it an unreadable roadmap and asserts a finding is returned rather than an
  exception — 0034's posture, re-asserted because this WU adds file reads
  (folder names, `PLAN.md` frontmatter) that 0034's checks did not perform.
- `_check_id_slug_binding` is importable: `python3 -c "from
  specfuse.loop.lint_roadmap import _check_id_slug_binding"` exits 0.
- The four existing check classes are unchanged. Assert mechanically: the
  existing `lint_roadmap` tests pass untouched.
- Every new `subprocess.run` (if any) declares `check=` explicitly (`PLW1510`).

**Do not touch.** `_check_uniqueness`, `_check_anchor_adjacency`,
`_check_ref_resolution`, `_check_blocked_by` and `_check_section_status` — 0034's
shipped checks, whose behavior other tests assert; `specfuse/loop/lint_plan.py`;
`specfuse/loop/feature_ids.py` (T01 owns it — this WU does its own reading rather
than taking a dependency on a unit that may not have landed);
`auto_archive_feature`, which 0034 deliberately did **not** import on the grounds
that a check sharing its subject's parser inherits its bugs. `.git/`, secrets.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
symbol-import check, the `roadmap_link_gate.py` run, and the probe re-run above.
See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if the probe re-run finds
existing violations in this repository. Shipping the ERROR would red
`roadmap-link-gate` for **every work unit of every feature in this repo**, which
is a repo-wide stoppage caused by a check nobody has triaged yet — the operator
decides whether to clean up or downgrade, not you. Report the violations in the
block. Also block if honouring the four-source read requires `lint_roadmap` to
raise on any input, since not raising is a shipped property of that module. If
`_check_id_slug_binding` is absent from the files you edited, emit
`status: blocked` — do not claim complete. Blocked is respectable
(`result-contract.md` rule 4).
