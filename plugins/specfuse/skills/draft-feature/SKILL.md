---
name: draft-feature
description: "Interactively draft a Specfuse feature \u2014 its gate skeleton, gate 1's work units, and the matching files \u2014 for a major initiative in a Specfuse-integrated project. Reads roadmap, LEARNINGS, recent feature exemplars, binding rules, and the project itself; walks a guided one-question-at-a-time interview (elicitation questions open, decision questions with prose pros/cons + a recommendation, never tables); proposes and only writes on accept. The drafting counterpart to authoring-work-units (per-WU craft) and feature-conversion (post-hoc fixes). Lean v0.1; expected to grow as real features are drafted with it."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Draft a feature (interactive)

This skill produces the file tree a Specfuse feature needs to be
dispatchable: `PLAN.md` (frontmatter + framing + the gates graph),
`GATE-NN.md` files (one per gate), and `WU-*.md` files for gate 1's
substantive work units plus the four closing-sequence units. Posture
mirrors `derive-verification` and `plan-next`: **draft, then arm**. The
skill proposes the structure section by section, asks before writing,
and writes only on your explicit accept.

**Run interactively.** The skill walks a guided interview — one framing
question at a time, wearing different hats (product / architect / QA /
reviewer / operator) — so `claude -p` with stdin redirected consumes the
channel the skill needs to ask through. Start `claude` in the target
project and ask it to run this skill against your feature idea.

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
- **Detail only gate 1.** Later gates are skeletal — their *substantive*
  work units are filled in by the previous gate's `plan-next` closing
  unit when the prior gate completes (the methodology's forward-design
  move). **But the FINAL gate must pre-declare its terminal `close` WU**
  (one graph entry + a `status: draft` placeholder file), because the
  linter treats the *last non-empty gate* as terminal
  (`lint_plan.py`): with every later gate's `work_units` empty, gate 1
  is misread as terminal and its `close-intermediate → plan-next`
  sequence is rejected. So: intermediate later gates may be empty; the
  last gate carries a lone `close` placeholder (plan-next inserts that
  gate's substantive WUs *before* it). See step 6.

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
  `FEAT-YYYY-NNNN` for the current year — computed with the **four-source
  next-ID scan** from the `roadmap-add` skill (roadmap table, `PLAN.md`
  files, `LEARNINGS`/`RETROSPECTIVE`, **and GitHub issue/PR titles+bodies
  when reachable**), so an ID reserved only on a GitHub issue is not reused.
  Do not derive the ID from the roadmap table alone. The roadmap also reveals
  ordering constraints: a planned feature that this initiative
  conflicts with, supersedes, or unblocks.
- **LEARNINGS slice, not the whole file.** `PLAN.md` doesn't exist yet at
  this step, so build a short query from what's already in hand: the
  one-line feature idea the user gave you, the provisional slug, and any
  surface names the idea already mentions. Run
  `python3 .specfuse/scripts/learnings_query.py "<query>" --top 8` and read
  only the returned bullets — durable rules from past gates that would
  change how this feature is planned or sized. If the CLI prints the
  sentinel line `LEARNINGS-LOAD-WHOLE` (small/early-stage repos, too few
  entries to rank), fall back to reading `.specfuse/LEARNINGS.md` whole.
  Don't read the whole file otherwise.
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

### 3. Interview — one decision at a time, guided

Walk the user through the framing questions as a **guided interview:
one question per turn**, not a single batched wall. This is the flow —
there is **no mode toggle**. Do not open with "do you want the quick
version or the guided one?"; that meta-question is itself something a
newcomer can't answer, and it's the friction this interview exists to
remove.

The interview **auto-scales** — it does not mean "ask everything." The
"infer first, ask last" hard rule governs the *set*: ask only what the
evidence from steps 1–2 didn't already answer, so a well-grounded
feature is two or three questions and a vague one is more. A hat with
nothing specific to ask is skipped, not filled with filler.

**Escape hatch (in-flow, not up-front).** If the user says some variant
of "take your recommendations for the rest," stop asking: apply your
recommended option to every remaining *decision* question, then jump to
step 4 with all the assumed choices surfaced together for a single
confirm. This is the expert fast-path — an exit mid-interview, never a
choice imposed at the start.

**Generate the questions by wearing the hats, surfaced one at a time,
highest-leverage first:**

- **Product** — what user-observable outcome does this produce? Who is
  the user (operator, developer, end customer)? One-sentence success.
- **Architect** — what surfaces does this touch? Additive or
  replacement? Cross-feature ordering or dependencies on planned items?
- **QA** — what makes this hard to verify? Boundary cases that trip the
  gates? Anything needing a real environment the gates can't provide?
- **Reviewer** — the scary part of the change; where the agent needs
  the tightest acceptance criteria to stay honest.
- **Operator** — how does this ship and roll back? Migration,
  observability, feature-flag posture, deploy ordering.

Also cover, once, the universal framing trio: the **roadmap_goal** (one
sentence), **autonomy** (`auto` / `review` / `supervised`), and the
**scope boundary** (what's explicitly OUT).

**Two kinds of question — ask them differently. This is the crux of the
interview.**

- **Elicitation — only the user knows the answer** (roadmap_goal, who
  the user is, what's out of scope, a domain constraint). Ask it
  **open**, in one or two plain sentences. Do NOT manufacture options
  for these: a fake multiple-choice on the user's own intent reads as a
  phone tree and buries the real question.
- **Decision — you can enumerate real options and have a basis to
  recommend** (autonomy level; additive vs replacement; gate count;
  single-gate vs multi-gate; a WU's red-test strategy; where an
  integration gets verified). Present each as:
  1. the decision in one line, **and why it matters to the driver** —
     the downstream dispatch, gating, or ceremony it changes;
  2. each viable option as a short **prose** paragraph: the option,
     then its pros and cons in plain sentences;
  3. your **recommendation** — which option, and the one reason it wins
     *here*, anchored in evidence from steps 1–2;
  4. the ask: "which — or override?"

  **Never render the options as a table.** A table flattens away the
  pros and cons that make the choice legible — they belong in prose.
  This is `/pick-feature`'s decision shape applied per question.

Keep **uncertainty callouts loud** as you go: when you're unsure whether
something belongs in this feature at all, or in gate 2 vs gate 3, say so
at that question rather than deciding silently. And carry each answer
forward — a question an earlier answer already settled is not asked
again (the "infer first" rule applied across the interview, not only
against files).

### 4. Propose the gate skeleton

> **Existing-mechanism search first (#209 item 6).** Before drafting any WU
> that designs a validation rule, a severity level, an enforcement gate, or a
> measurement, run the existing-mechanism search and record the command +
> verdict in PLAN.md's `Existing-mechanism search` section — see
> `.specfuse/rules/planning-discipline.md` §1. FEAT-2026-0049 spent two gates
> building enforcement that already existed one grep away. Features designing
> no such mechanism write the section's explicit n/a line.

#### Size rule — ceremony proportionality

Before sketching the gate count, tally planned substantive WUs (types
`implementation`, `qa_authoring`, `qa_execution`, `qa_curation`).
When **planned substantive WU count ≤ 4**, draft a **single gate** with a
**single terminal close** WU (type `close`) — no `close-intermediate`, no `plan-next`.
The canonical threshold is stated in `docs/methodology.md §6 "Ceremony
proportionality"` (one fact, one home); reference it, do not redefine it.

Off-plan escape: a single-gate feature whose gate goes off-plan (blocked WU,
replan, cost overrun) still receives the full close ceremony via the
`gate_eval` auto-close predicate — the predicate disables auto-close and the
driver dispatches the close WU as a normal reflective session. This rule
trades reflection only on features that stay small and on-plan.

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
- **Operator-script trigger.** If a proposed WU emits a committed
  executable for human operators (a `.sh` script, a helper installed
  on PATH, a runbook whose body is shell to be copy-pasted), apply
  `/authoring-work-units` §11: the WU's Acceptance must include
  `shellcheck` clean, `bash -n` parses, and at least one bats
  happy-path test with external commands stubbed. Surface this in
  the proposal so the user can confirm or skip on the
  pure-markdown-runbook exception.
- **Red-test-first trigger.** For every proposed `implementation` WU
  that introduces new behavior, apply `/authoring-work-units` §12:
  Acceptance bullet 1 names a specific scoped test (`tests/<path>::
  <test_name>` or runner-equivalent nodeid) that **fails on HEAD
  before this WU runs**; bullet 3 asserts the same test passes after.
  Propose the red_test path at draft time so the operator can confirm
  the test exists / will be authored as the WU's first step, or
  invoke the §12 exemption (refactor / migration / pure-data WU)
  with a one-line rationale. Skip the trigger for closing WUs
  (`close`, `close-intermediate`, `plan-next`, `retrospective`,
  `lessons`, `docs`) — the rule applies to behaviour-introducing
  implementation work only.
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

  **Every `close` (and `close-intermediate`) WU body must include a
  `## Cost analysis` section as one of its acceptance criteria bullets.**
  Draft the AC bullet as: "A `## Cost analysis` section is present,
  reconciling `planned_cost_usd` (from PLAN.md and per-WU frontmatter)
  against actual spend (from events.jsonl), with delta named." The
  hollow-pass guard (`assert_cost_analysis_section_when_met`, T07)
  enforces this at execution time; listing it as an explicit AC bullet
  makes the contract visible at plan-next authoring time.

  **Every `close` (and `close-intermediate`) WU body must also include
  a `## What the loop did NOT verify` section as one of its acceptance
  criteria bullets.** Draft the AC bullet as: "A `## What the loop did
  NOT verify` section is present, enumerating each acceptance criterion
  whose verification was deferred (loop-sandbox limit, cross-repo
  coordination, real-system access). For each: the criterion, why
  deferred, and where verification actually happens (post-merge step,
  operator action, follow-up feature). If the list has more than 2
  entries OR more than 30% of the gate's criteria, the retrospective
  must flag the feature's single-gate sizing under `## What I'd
  change`." The section is required even when empty — write
  `(nothing — every acceptance criterion was verified in-loop)` so
  the explicit count is visible. The section's purpose is to surface
  the artifact-vs-real-state gap that single-gate cross-system
  features otherwise paper over: a feature that closes `verdict: met`
  while four of six AC bullets are post-merge-deferred is closing on
  artifact shape, not real-system behaviour. Counting them at retro
  time, where the lessons WU runs, is the methodology's last chance
  to catch the gap before the close commit.

  **Do NOT add a "flip `PLAN.md status` to `done`" acceptance criterion to
  the terminal `close` WU.** The driver owns the terminal PLAN flip:
  `fire_terminal_flips` (loop.py) flips `PLAN.md status -> done` — gated on
  `verdict_permits_terminal_flips` — as part of the same modified-paths set it
  uses for the terminal gate and roadmap row, on BOTH the dispatched-close and
  the agent-less auto-close path (FEAT-2026-0023/T01, closes #49). A manual
  agent flip is redundant; the agent need not write `PLAN.md status` at all.

  Cost tables feed `evaluate_auto_close` at gate close. A WU's
  `planned_cost_usd` is the threshold the predicate's per-WU ratio check
  measures against (criteria 3 + 4 in PLAN.md's Predicate v1). Honest
  planning makes auto-close behave; over-generous estimates make every
  gate auto-close even when it shouldn't.

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
  gates 2..N). Give each stub gate `status: open` (NOT `draft` — `draft`
  is a WU status, not a gate status; gate statuses are `open` /
  `awaiting_review` / `passed`).
- **Multi-gate features: pre-declare the FINAL gate's terminal `close`.**
  For a 2+-gate feature, the last gate's `work_units` must list one
  entry — its terminal `close` WU (id `FEAT-YYYY-NNNN/G<N>-CLOSE`, file
  `WU-9x-gate-N-close.md`) — and you write that WU file as a
  `status: draft` placeholder (`depends_on: []` for now; `plan-next`
  updates it to depend on the substantive WUs it inserts before it).
  This is what makes the last gate the *non-empty* terminal gate so the
  linter reads gate 1 as non-terminal. Intermediate gates (between the
  first and last) may keep empty `work_units`.
- Write the WU files for gate 1 in the accepted forms (and the final
  gate's `close` placeholder per the bullet above).
- Append a one-line row to `.specfuse/roadmap.md` (status `planned`
  until the user flips it to `active` themselves), **and** an inline
  `## FEAT-YYYY-NNNN — <title>` detail section (place it among the other
  detail sections, before `## Notes`) capturing the goal, shape, and scope
  boundary. The detail section is not optional cosmetics: `auto_archive_feature`
  moves it into `roadmap-archive.md` and writes the `<a id="feat-yyyy-nnnn">`
  anchor the terminal-close post-pass invariant (`assert_terminal_flips_fired`)
  requires. A row without a detail section forces the driver to synthesize a
  stub at archive time (it no longer halts, since FEAT-2026-0022, but the stub
  carries no real record). Write the real section now.
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

**v0.2 (FEAT-2026-0035).** Step 3 rewritten from a single batched round
into a **guided one-question-at-a-time interview**. No mode toggle; the
question set auto-scales via "infer first, ask last," with an in-flow
"take your recommendations for the rest" escape hatch. Questions split
into **elicitation** (only the user knows — asked open) and **decision**
(skill enumerates — presented as prose options + pros/cons +
recommendation + pick, the `/pick-feature` shape, never a table). The
hats now *generate* questions surfaced sequentially rather than a batch.
Aimed at onboarding newcomers and tightening driver alignment.

**v0.1.** Six steps; the hats and the universal framing trio, asked as a
single batched round, were the entire question-shape rule. Expected to
grow once real major initiatives are drafted with it — which hat
surfaced the highest-leverage question, which step the user redoes most
often, where the gate skeleton needed revision after gate 1 actually
ran. Shared methodology craft (loop is near-term author, like the
addendum).
