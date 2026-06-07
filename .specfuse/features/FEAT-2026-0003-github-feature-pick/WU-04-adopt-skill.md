---
id: FEAT-2026-0003/T04
type: implementation
model: claude-sonnet-4-6
status: done
attempts: 1
cost_usd: 0.299924
input_tokens: 8
output_tokens: 8237
---

# Interactive pick-and-adopt skill

**Objective.** Add `.specfuse/skills/adopt-feature/SKILL.md`: the human-facing
interactive flow that lists a target repo's `specfuse:feature` candidates,
presents them as a pick list, and on the human's explicit pick invokes the
gate-2 scaffolding script (`adopt_feature.py` from T03) to materialize the new
feature folder.

**Context.** This is `FEAT-2026-0003/T04`, gate 2 of the GitHub feature-pick
build. The human design choice (see this feature's `WU-93-gate-1-plan-next.md`
prompt) was **script + skill**: T03 owns the scaffolding behavior; this WU owns
the interactive wrapper humans actually invoke. The skill is the loop's "pick a
GitHub feature and grind it" entrypoint — mirroring `pick-feature` (which picks
from a roadmap row) but with `gh issue list` as its source. Read the two
exemplars before authoring:
[`.specfuse/skills/pick-feature/SKILL.md`](../../skills/pick-feature/SKILL.md) and
[`.specfuse/skills/draft-feature/SKILL.md`](../../skills/draft-feature/SKILL.md).

The skill is a markdown artifact (frontmatter + sectioned prose) — the
methodology's `SKILL.md` shape, with `name:` and `description:` in frontmatter and
prose below. It does not run code itself; it instructs Claude to call
`gh_features.list_features` and `adopt_feature.py` (both shipped by gate 1 / T03).
Reference the binding rules under `.specfuse/rules/` and the per-WU craft in
`.specfuse/skills/authoring-work-units/SKILL.md`. The skill ends by pointing at
[`../../rules/result-contract.md`](../../rules/result-contract.md) for the
RESULT block.

**Acceptance criteria.**
1. `.specfuse/skills/adopt-feature/SKILL.md` exists with frontmatter declaring
   `name: adopt-feature` and a single-line `description:` summarizing the
   interactive pick-and-adopt flow (target audience: a human running `claude`
   interactively in any repo that wants to grind a GitHub `specfuse:feature`
   issue).
2. The body declares a numbered **Method** section with at least these steps,
   in order: (a) read the target repo (`<owner>/<name>`) from a CLI argument
   when present, else ask once; (b) read `.specfuse/roadmap.md` to detect an
   already-active feature and surface a "honor active features" warning
   mirroring `pick-feature`'s rule, requiring an explicit override before
   proceeding; (c) invoke `python3 .specfuse/scripts/gh_features.py <repo>` (or
   the `list_features` function programmatically) to enumerate candidates; (d)
   present 2–N candidates as a markdown table with columns `# | feature_id |
   title | initiative | type | autonomy | url`, capped at the top 5 by
   `number` (most recent issues first) — if fewer than 2, present whatever
   exists; (e) accept the human's pick by number or by `feature_id`; (f) invoke
   `python3 .specfuse/scripts/adopt_feature.py <repo> <issue-number>` and print
   its stdout (the created folder path); (g) print a one-line next-command:
   `Run /draft-feature on the new folder to refine gate 1, or python3
   .specfuse/scripts/loop.py --feature <folder> to dispatch as-seeded.`
3. The body includes a **Hard rules** section restating: recommend never decide
   (the human picks); honor active features; modify only the new feature
   folder via the T03 script (do not touch other features, rules, or
   templates); infer from `gh_features.list_features` before asking ("infer
   first, ask last"); the issue body IS the WU contract — do not rewrite it
   during adoption.
4. The body includes a **What this skill does NOT do** section restating: does
   not flip the new feature's status to `active` (the human arms it); does not
   edit other features, binding rules, or templates; does not run git; does
   not refine the seeded WU-01 (that's `/draft-feature` or the gate 1 grind);
   does not loop or auto-dispatch (the human runs `loop.py`).
5. The body ends with a one-line pointer to
   [`../../rules/result-contract.md`](../../rules/result-contract.md) for the
   RESULT block format, and a `**v0.1.**` version line.
6. No file other than `.specfuse/skills/adopt-feature/SKILL.md` is created or
   modified by this WU.

**Do not touch.** `.specfuse/scripts/` (gh_features.py and adopt_feature.py are
referenced, not edited here), any other skill under `.specfuse/skills/`, any
binding rule under `.specfuse/rules/`, any template under `.specfuse/templates/`,
any existing feature folder under `.specfuse/features/`, generated directories,
secrets, `.git/`. The driver owns all git — edit files only. This WU produces
**exactly one new file**: `.specfuse/skills/adopt-feature/SKILL.md`. No other
file is created or edited.

**Verification.** The `code` gates in `.specfuse/verification.yml`: tests, ruff
lint (does not lint markdown), bandit (does not scan markdown), coverage
`--fail-under=70`. The artifact itself is a markdown skill file with no
executable code, so the `code` gates pass trivially as long as the surrounding
test suite is unaffected; the artifact's substantive quality is judged by the
human reviewer reading the SKILL.md against the gate-2 review checklist (see
`GATE-02-REVIEW.md`'s "Flagged for attention" entry on T04).

**Escalation triggers.** If T03's CLI surface ends up shaped differently from
the contract documented here (`<repo> <issue-number>` positional args, stdout
= one line with the created folder path), stop and emit `status: blocked` —
the skill must match the script's surface verbatim or the flow breaks at the
human pick. If the human chose to skip the "honor active features" step at
T03's review time (i.e. that rule was rejected for gate 2), block: the skill's
step (b) cannot be authored without that decision.
