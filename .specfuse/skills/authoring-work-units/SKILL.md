---
name: authoring-work-units
description: How to write a single Specfuse work unit that won't block spuriously or pass hollowly. Reference for humans authoring WUs in the loop, and for reviewing PM-agent drafts in the orchestrator. Lean v0.1; six evidence-backed rules, one per spot a real run has tripped on.
---

# Authoring a work unit

This skill teaches how to fill the five-section WU contract
(`.specfuse/templates/WU.template.md`, methodology §4) well — section by
section, plus one cross-cutting sizing rule.

**The bar.** Every rule below names a concrete failure mode it prevents. If
a rule can't name the failure, it's filler and was cut. `"Write clear
acceptance criteria"` is filler; `"Scope acceptance-criteria checks to the
feature's own footprint — repo-wide greps trip on pre-existing unrelated
state"` is the right shape. Apply the same bar when adding rules.

This is shared methodology craft — works for the loop (single-repo) and the
orchestrator (multi-repo). The loop is the near-term author, like the
architecture addendum; orchestrator-side adoption is the fold-in.

---

## 1. Context — write for a cold session

The body below the frontmatter is **all a fresh, memoryless session gets**.

- Name the correlation ID (`FEAT-YYYY-NNNN/TNN`) and the grounding files
  (specs, docs, target paths) the session needs to orient.
- **Reference** binding rules under `.specfuse/rules/` — never restate.
  Restated rules drift from source.
- Enough to orient, not a wall. If you're summarizing the feature spec,
  the WU is misscoped — link it instead.

> *Prevents:* a fresh session thrashing for lack of grounding, or acting
> on a restated rule that has since changed at source.

## 2. Acceptance criteria — scope to the feature's own footprint

Criteria that grep or scan the **whole repo** trip on pre-existing,
unrelated state and cause a correct-but-unwanted block. Bound every check
to the feature's own footprint: its slug, the paths it creates or edits,
the symbols it introduces, the files in `generated_surfaces` /
`files_changed`.

- Phrase each criterion as an **objective statement a reviewer can judge
  and a gate can mechanically check** — not an intention. (`"GET /health
  returns 200 with JSON {status, version}"` ✓ — `"endpoint is
  well-tested"` ✗.)
- Avoid compound criteria (`"X and also Y"`). Split so a single failure
  attributes to a single line.
- A criterion that needs inspecting unrelated parts of the repo is the
  wrong shape; narrow the scope, or move the check to a repo-wide
  hygiene WU / the `code` gate set.

> *Prevents:* a throwaway "grep returns zero hits" criterion blocking on a
> stale roadmap pointer the WU never touched (real failure logged in
> `.specfuse/LEARNINGS.md` under `[meta/first-live-use]`); also prevents
> reviewers waving through subjective criteria that hide unmet
> requirements.

## 3. Do not touch — name real paths, not platitudes

Generic `"don't touch other files"` is one an agent will cross. List the
actual boundaries this WU might brush against:

- The **generated directories** in this repo (`_generated/`, `gen-src/`,
  or whatever your repo declares).
- The **specific sibling-WU files** in this gate, by path, if the gate's
  graph is already laid out and the WU's work is adjacent to theirs.
- **Secrets** files (`.env`, `*.pem`, `*.key`, `credentials.json`) and
  `.git/` internals.
- **The driver owns all git.** The session edits files only — never runs
  `git`. State this even when it feels redundant; without it, an agent
  helpfully runs `git add` and corrupts the driver's bookkeeping.

> *Prevents:* an agent reaching into a generated directory because "don't
> touch other files" didn't sound like *this*; and side commits the
> driver's squash can't reconcile.

## 4. Verification — name the gates the driver will actually run

The WU's Verification section names gates, but the driver (or branch
protection) runs whatever is in `verification.yml`'s relevant set. If they
disagree, the WU's stated verification is fiction.

- For `implementation` WUs, name the `code` set as declared in this
  repo's `verification.yml`. Don't list a gate the file doesn't have, and
  don't omit one it does.
- For fast-iteration or probe work, prefer a **scoped** gate command
  (`pytest tests/test_health.py`, `mvn test -Dtest=HealthTest`) over a
  full-suite one. A minutes-long full run on every attempt makes the
  three-attempt budget effectively one attempt.
- Some runners fail silently on a missing-but-named test (no tests found
  ≠ all passed). Name a real test, and confirm the runner exits non-zero
  when nothing matches.

> *Prevents:* a WU that "passes" the agent's check but fails the driver's
> re-run; and a WU burning each of three attempts on a full suite the
> iteration didn't need.

## 5. Escalation triggers — distinguish "my check tripped" from "the bad thing happened"

Triggers should fire on the **real hazard**, not on any flagging condition.
The best observed agent behaviour, when a criterion tripped ambiguously,
emitted `status: blocked` *and* explained the trip might be a false alarm
on pre-existing state, recommending human review — rather than pushing
through or silently passing.

- Name triggers as conditions, not actions: `"if no router module exists,
  block — that's a different unit of work"`, not `"create the router."`
- When you're unsure whether a tripped criterion is the real failure or
  pre-existing unrelated state, the right move is a reasoned
  `status: blocked` with the evidence. **Blocked is a respectable
  outcome** (see [`../../rules/result-contract.md`](../../rules/result-contract.md));
  a guessed pass is worse than an honest block.
- A trigger that only ever fires on the agent's own bug is not a trigger;
  it's a code-quality concern. Triggers exist for spec/scope ambiguities
  the agent shouldn't resolve unilaterally.

> *Prevents:* the agent forcing a doubtful pass that costs the gate's
> trust budget; also prevents triggers that fire constantly and become
> noise the next reader ignores.

---

## 6. Sizing — one WU = one focused session's work

A WU is crafted to land in a single fresh-session pass. The Ralph property
(fresh context per attempt) only buys leverage when the unit is
small-enough to fit.

- If a WU needs multiple rounds of **unrelated** work, it's two WUs.
  ("Add the endpoint AND refactor the router module" is two.)
- If a WU's acceptance criteria number in the double digits, suspect
  bundling — most well-sized WUs have 2–5 criteria.
- Sizing interacts with gate-cutting (how to slice a feature into the
  right number of gates with the right WUs each). **That's a separate
  skill** and is deferred until multi-gate runs surface decomposition
  evidence; this skill stays at the per-WU level.

> *Prevents:* a WU that exhausts the three-attempt budget on the first
> sub-problem and never reaches the second; also prevents the driver
> producing one squashed commit that mixes two unrelated changes.

---

## This skill distills `.specfuse/LEARNINGS.md`

When a gate's `lessons` work unit surfaces a new authoring rule — one that
would change how a future WU is written or executed — it graduates here
once it's reusable and durable. The pipeline is **runs → retrospective →
lessons → LEARNINGS.md → this skill**. If a rule lives only in LEARNINGS
and would clearly change WU authoring, it's a candidate for promotion on
the next edit.

## Version

**v0.1.** Six rules, one per spot a real run has tripped on (single-gate
runs to date). Expected to grow as multi-gate runs surface authoring
lessons that don't fit the per-WU frame.
