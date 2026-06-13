---
name: draft-feature
description: Interactively draft a Specfuse feature — its gate skeleton, gate 1's work units, and the matching files — for a major initiative in a Specfuse-integrated project. Reads roadmap, LEARNINGS, recent feature exemplars, binding rules, and the project itself; asks framing questions wearing multiple hats; proposes and only writes on accept. The drafting counterpart to authoring-work-units (per-WU craft) and feature-conversion (post-hoc fixes). Lean v0.1; expected to grow as real features are drafted with it.
---

# Draft a feature (interactive)

This skill produces the file tree a Specfuse feature needs to be
dispatchable: `PLAN.md` (frontmatter + framing + the gates graph),
`GATE-NN.md` files (one per gate), and `WU-*.md` files for gate 1's
substantive work units plus the four closing-sequence units. Posture
mirrors `derive-verification` and `plan-next`: **draft, then arm**. The
skill proposes the structure section by section, asks before writing,
and writes only on your explicit accept.

**Run interactively.** The skill asks multiple framing questions
wearing different hats (product / architect / QA / reviewer /
operator); `claude -p` with stdin redirected consumes the channel the
skill needs to ask through. Start `claude` in the target project and
ask it to run this skill against your feature idea.

## Hard rules

- **Trace every proposal to evidence.** Every gate the skill proposes,
  every WU it lists, every acceptance criterion it suggests must trace
  to a stated goal, a question you answered, or a file it read. If a
  proposal can't name its source, it's invention and the skill must
  ask instead.
- **Infer first, ask last.** A question is legitimate only when no
  file the skill could read would answer it. Asking "what language is
  this?" when `package.json` exists is a skill bug.
- **Don't restate the binding rules.** `.specfuse/rules/*.md` and the
  per-WU craft in `.specfuse/skills/authoring-work-units/SKILL.md` are
  binding by reference. The skill points at them; it does not
  duplicate them.
- **Detail only gate 1.** Later gates are skeletal (declared in the
  PLAN's gates graph but with empty `work_units` lists). Each gate's
  substantive work units are filled in by the previous gate's
  `plan-next` closing unit when the prior gate completes — that's the
  methodology's whole forward-design move.

## When to invoke

When you're starting a new major initiative in a project that has
`.specfuse/` scaffolded. Tell Claude what the initiative is in one or
two sentences and ask it to run the draft-feature skill. The skill
takes that one-line idea and the project's existing state as its inputs.

## Method (strict order — read, probe, ask, propose, write)

### 1. Read the grounding context

Before any proposal, read what shapes good plans in *this* project:

- **`.specfuse/roadmap.md`** — what's done, what's active, what's
  planned. The new feature's correlation ID is the next sequential
  `FEAT-YYYY-NNNN` for the current year. The roadmap also reveals
  ordering constraints: a planned feature that this initiative
  conflicts with, supersedes, or unblocks.
- **`.specfuse/LEARNINGS.md`** — durable rules from past gates that
  would change how this feature is planned or sized.
- **`.specfuse/features/*/PLAN.md`** — recent feature exemplars. Read
  one or two to see what good gate-cutting looks like in this project
  (gate count, WU count per gate, typical depends_on shapes).
- **`.specfuse/rules/`** and **`.specfuse/templates/`** — the binding
  contracts (correlation IDs, never-touch, security-boundaries,
  result-contract; PLAN/GATE/WU templates).
- **The project's own `CLAUDE.md`** (root or `.claude/CLAUDE.md`) —
  conventions or constraints the project has declared.

### 2. Reconnaissance — probe the project

Light-touch read so framing questions are specific, not generic:

- Top-level layout, README.md, package manifest(s).
- The likely surfaces the feature touches (modules named by the idea).
  Enough to ask informed questions, not exhaustive.
- The existing test layout and `.specfuse/verification.yml` — so WU
  `Verification` sections later name the real gate commands.

### 3. Ask — wear multiple hats, batched

After steps 1–2, present a **single batched round** of framing
questions, organized by hat. Choose 3–5 hats whose perspective the
evidence didn't already answer. Forbidden: hats that have nothing
specific to ask for this feature ("just to be thorough" is filler).

- **Product hat** — *what user-observable outcome does this produce?*
  Who is the user (operator, developer, end customer)? What does
  success look like in one sentence?
- **Architect hat** — *what surfaces does this touch?* Additive or
  replacement? Cross-feature ordering or dependencies on planned
  roadmap items? Architectural debts this pays down or creates?
- **QA hat** — *what makes this hard to verify?* Boundary cases that
  will trip the gates? Integration points whose test story is unclear?
  Anything that needs a real environment that the gates can't provide?
- **Reviewer hat** — *at PR review, what would worry me?* The "scary"
  part of the change; the part where the agent will need the tightest
  acceptance criteria to keep it honest.
- **Operator hat** — *how does this ship and roll back?* Migration
  story, observability, feature-flag posture, deploy ordering.

Also ask, once, the universal framing trio:
1. What's the **roadmap_goal** in one sentence?
2. **Autonomy** — `auto`, `review`, or `supervised`?
3. **Scope boundary** — what's explicitly OUT for this feature?

### 4. Propose the gate skeleton

Drawing on the answers, propose N gates (typically 2–4 for a major
initiative). For each gate:

- A one-line **definition of done** (the human-meaningful milestone
  this gate produces).
- A bullet sketch of the substantive WUs it will contain (no
  details — those happen in step 5, and only for gate 1).
- Explicit **uncertainty callouts**: "I'm unsure whether X belongs in
  gate 2 or gate 3 — your call." Make these loud so they aren't
  missed in review.

Show the skeleton; accept revisions before continuing. Every gate ends
with a closing block whose shape depends on gate position:

- **Non-terminal gate** (any gate that is not the last): 2-WU closing
  sequence — `close-intermediate` (folds RETRO+LESSONS+DOCS into one
  session) followed immediately by `plan-next`.
- **Terminal gate** (the feature's final gate, any feature shape):
  single `close` WU, collapsing retrospective + lessons + docs +
  terminal verdict into one session.

### 5. Propose gate 1's WUs

For gate 1 only:

- List the substantive WUs (typically 2–5; the
  `/authoring-work-units` skill's sizing rule applies — if there are
  more than ~5, consider whether this is really one gate).
- For each, propose the `id`, `file`, `depends_on`, and the five-
  section body. **Delegate the per-WU craft** to
  [`../authoring-work-units/SKILL.md`](../authoring-work-units/SKILL.md) —
  read its rules and apply them; don't restate them here.
- Closing WUs for gate 1 follow the shape decided in step 4:
  - **Gate 1 is non-terminal**: generate 2 closing WUs mechanically —
    `G1-CLOSE-INTERMEDIATE` (file `WU-90-gate-1-close-intermediate.md`,
    type `close-intermediate`) then `G1-PLAN` (file
    `WU-91-gate-1-plan-next.md`, type `plan-next`). The
    `close-intermediate` WU depends on all substantive WUs; `G1-PLAN`
    depends on `G1-CLOSE-INTERMEDIATE`.
  - **Gate 1 is terminal** (single-gate feature): generate a single
    `G1-CLOSE` WU (file `WU-90-gate-1-close.md`, type `close`)
    depending on all substantive WUs.
  Surface whichever set applies for confirmation rather than per-section
  discussion.

#### Legacy: 4-WU sequence

Older features used a four-WU closing sequence: `G1-RETRO`
(`retrospective`), `G1-LESSONS` (`lessons`), `G1-DOCS` (`docs`),
`G1-PLAN` (`plan-next`). This shape is accepted by lint but emits a
WARN — do NOT use it for new features. If you are migrating an
in-flight feature that already has `G1-RETRO` / `G1-LESSONS` /
`G1-DOCS` drafted, leave those WUs as-is and let the gate complete
normally; the lint warning is advisory for in-flight work.

Show each substantive WU's draft before writing. Accept, modify, or
skip — same propose-and-confirm rhythm as `feature-conversion`.

### 6. Write only on accept; verify at the end

When the user has accepted the structure:

- Create the feature folder: `.specfuse/features/FEAT-YYYY-NNNN-<slug>/`.
- Write `PLAN.md` from the template (`.specfuse/templates/PLAN.template.md`)
  with the accepted frontmatter, framing prose, and gates graph.
- Write `GATE-NN.md` for each gate (full content for gate 1, stub for
  gates 2..N — empty `work_units` in the graph means the gate is
  awaiting `plan-next`).
- Write the WU files for gate 1 in the accepted forms.
- Append a one-line row to `.specfuse/roadmap.md` (status `planned`
  until the user flips it to `active` themselves).
- Run `python3 .specfuse/scripts/lint_plan.py
  .specfuse/features/<new-folder>`. Report PASS or the errors. If it
  fails, point at the `/feature-conversion` skill to walk the diff
  before the user re-runs.
- Optionally run `python3 .specfuse/scripts/loop.py --dry-run` to
  confirm the loop loads the feature cleanly.

End with the RESULT block defined in
[`../../rules/result-contract.md`](../../rules/result-contract.md).
`status: complete` means the user accepted, files are written, and
lint passes. If the user abandoned partway, emit `status: blocked`
with what was decided so far in `blocked_reason`.

## What this skill does NOT do

- **Does not flip status to `active`.** New feature stays `planned`
  in roadmap and PLAN frontmatter; the human arms it when ready.
- **Does not detail gates 2..N.** Later gates are drafted by the
  prior gate's `plan-next` — that's the methodology's iterative move.
- **Does not invent acceptance criteria.** If a criterion can't trace
  to a stated goal or a user answer, the skill asks rather than
  fabricates.
- **Does not modify other features, binding rules, templates, or
  verification.yml.** Touches only the new feature's folder and one
  new line in `roadmap.md`.
- **Does not run git.** The user reviews via `git diff` and commits
  when satisfied.

## Version

**v0.1.** Six steps; the hats and the universal framing trio are the
entire question-shape rule today. Expected to grow once real major
initiatives are drafted with it — which hat surfaced the highest-
leverage question, which step the user redoes most often, where the
gate skeleton needed revision after gate 1 actually ran. Shared
methodology craft (loop is near-term author, like the addendum).
