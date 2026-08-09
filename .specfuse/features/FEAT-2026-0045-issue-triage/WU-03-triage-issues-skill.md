---
id: FEAT-2026-0045/T03
type: implementation
status: done
attempts: 2
planned_cost_usd: 3.50
produces:
  - plugins/specfuse/skills/triage-issues/SKILL.md
  - .specfuse/skills/triage-issues/SKILL.md
  - tests/test_triage_skill_contract.py
oracle_env: macos_local
duration_seconds: 1507.895
cost_usd: 2.38633
input_tokens: 6262
output_tokens: 22081
---

# The `/triage-issues` skill: judgment over the mechanism

**Objective.** Author `/triage-issues` — the interactive skill that categorises inbound
issues and calls the T01/T02 mechanism to record the result — and bind its documented
vocabulary to the module's constants with a drift test.

**Context.** Correlation ID `FEAT-2026-0045/T03`. Depends on T01 and T02. Read `PLAN.md`
first, particularly **the seam**: the module owns mechanism, the skill owns judgment. The
skill classifies free text; it does not re-implement the vocabulary, the routes, the
marker format, or the scan.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `human-output.md`, `operator-escalation.md`.

**Where the skill lives, and which direction it syncs.** The canonical source is
`plugins/specfuse/skills/triage-issues/SKILL.md` — the marketplace-published plugin.
`.specfuse/skills/` is a byte-for-byte **copy** vendored from it by
`scripts/sync-scaffold.sh`, and `.claude/skills/` holds forward symlinks into
`.specfuse/skills/`. Author the plugin copy, then run the sync script; do not hand-edit
`.specfuse/skills/triage-issues/`. `tests/test_skills_vendored_in_sync.py` enforces this
and will fail if the two diverge. Note this is the **opposite** direction from rules and
templates, which vendor `.specfuse/` → package data.

**Write the skill in the established shape.** Read `plugins/specfuse/skills/attention/`
and `plugins/specfuse/skills/diagnose-issue/` first — `attention` for how a read-only
issue-queue skill is structured, `diagnose-issue` for how a skill hands its result to a
Python module. Match their section shape (frontmatter, Hard rules, When to invoke,
Method, What this skill does NOT do, Escalation framing, Version), do not invent a new one.

**What the skill must get right.**

- **Propose and confirm.** Per-issue: proposed category, proposed route, a one-paragraph
  rationale, and a confidence. The operator accepts, changes, or skips each. Nothing is
  written before an explicit accept.
- **Skip the already-structured.** An issue `list_untriaged` flags as harvester-created
  is already structured; propose its category from that structure rather than
  re-categorising it from prose. This is the row's fingerprint-awareness clause.
- **`duplicate` is judgment-only.** The module gives it a marker and a route and nothing
  else — no similarity search, no automatic linking. The skill proposes it from reading;
  the operator confirms. Say so plainly in the skill body so a future reader does not
  assume detection exists.
- **Never act on a route.** Categorise, route, record. Invoking `/fix-bug`, writing a
  roadmap row, or closing an issue are all out of scope per `PLAN.md` — the skill names
  the route and stops.
- **Do not restate the vocabulary's semantics as prose the module doesn't hold.** The
  skill documents the five categories and their routes; the module defines them. Where
  the skill lists them, it is quoting a contract, not authoring one.
- **Report per `human-output.md`**, and use the six-part `operator-escalation.md` shape
  wherever the skill halts for a decision.

**The drift test, and what it does not prove.** AC1's test asserts the categories and
routes documented in SKILL.md match `triage.py`'s constants exactly. That is worth
having — prose and constants are two statements of one contract and prose drifts. It is
**not** proof that an agent following the prose triages an unseen issue correctly; no
test in this repository composes the skill with the module. State this limitation in the
skill's own Version section, so the passing test is not read as "the skill is proven."
This is `[FEAT-2026-0069/G2-CLOSE]` applied at authoring time rather than discovered at
close.

**Red-test note.** This WU introduces new behaviour (a new skill surface and a new
contract binding), so §12 applies normally — AC1 is the red test. No exemption claimed.

**Acceptance criteria.**

1. **Red first.** `tests/test_triage_skill_contract.py::test_skill_vocabulary_matches_module`
   exists and **fails on HEAD before any source edit** — SKILL.md does not exist yet.
   Record the failing output.
2. `plugins/specfuse/skills/triage-issues/SKILL.md` exists with valid skill frontmatter
   (`name`, `description`), matching the shape of the sibling skills named above.
3. `test_skill_vocabulary_matches_module` **passes** after the edits: every member of
   `CATEGORIES` appears in SKILL.md, every route string from the route map appears in
   SKILL.md, and SKILL.md names no category outside `CATEGORIES`. The test imports the
   constants; it does not hardcode the five strings.
4. `scripts/sync-scaffold.sh` has been run, and
   `python3 -m unittest tests.test_skills_vendored_in_sync -v` passes — the plugin copy
   and the vendored copy are byte-for-byte identical.
5. `.claude/skills/triage-issues` resolves to `.specfuse/skills/triage-issues` (the
   forward symlink the sync script creates).
6. SKILL.md contains an explicit statement that the drift test does not prove an agent
   following the prose triages correctly. Checkable by grep for the claim's substance.
7. SKILL.md states that `duplicate` has no detection mechanism and is operator judgment.
8. SKILL.md's "What this skill does NOT do" section names acting on a route (invoking
   `/fix-bug`, writing roadmap rows, closing issues) as out of scope.
9. The `code` gate set in `.specfuse/verification.yml` passes: tests, lint, security,
   coverage ≥ 90%, leak-scan, event-type-gate, roadmap-link-gate, arm-sweep-gate.

**Do not touch.** `.git/`, secrets, `specfuse/loop/triage.py` (T01 and T02 own it — this
WU consumes it; if it needs changing, that is an escalation, not an edit), other skills
under `plugins/specfuse/skills/`, `skills-lock.json` (third-party skills only). Do not
hand-edit `.specfuse/skills/triage-issues/` — run the sync script. The driver owns all
git operations. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, run per
`.specfuse/skills/verification/SKILL.md`, plus AC4's explicit vendored-in-sync run and
AC5's symlink resolution check.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:

- `plugins/specfuse/skills/triage-issues/SKILL.md` is absent from the files you edited
  when you believe you are done — do not claim complete.
- Writing the skill reveals that the module's vocabulary or routes are wrong for the
  judgment the skill must express. Do not edit `triage.py` to fit; that contract is T01's
  and changing it here silently invalidates T01's and T02's tests.
- `scripts/sync-scaffold.sh` fails or produces a diff the vendored-in-sync test still
  rejects.
- The skill appears to need `gh` at author time to be verifiable. It does not — its
  oracle is the drift test. If you believe otherwise, stop: PLAN.md's sandbox constraint
  makes live `gh` unavailable in-loop by design.

Blocked is a respectable outcome — `result-contract.md` rule 4.
