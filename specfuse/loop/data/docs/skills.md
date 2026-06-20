# Skills catalog

The loop ships a set of Claude Code skills — interactive, conversational
operations you invoke as `/skill-name` inside Claude Code. They are the human
side of the gate cycle: the driver (`loop.py`) runs unattended *within* a gate;
the skills are how you plan features, arm gates, diagnose halts, and wrap up.

Every skill is **propose-and-confirm**: it reads state, shows you what it intends
to do, and writes only on your explicit go-ahead. None of them dispatch agent
sessions or run the loop — they manipulate the durable files (`roadmap.md`,
`PLAN.md`, `GATE-NN.md`, `WU-*.md`, `LEARNINGS.md`) that the driver then acts on.

All skills below ship to a target repo via `init.sh` and appear under
`.specfuse/skills/` (symlinked into `.claude/skills/` so Claude Code discovers
them).

## The lifecycle, in order

A feature moves through these phases. The skill for each phase is named.

```
roadmap ──/pick-feature──▶ active ──/draft-feature──▶ gate 1 detailed
                                                            │
                                                   python loop.py
                                                            │
                                   ┌────────────────────────┴───────────────┐
                                   ▼                                         ▼
                          gate auto-closes                        driver halts at gate
                                   │                              (awaiting_review)
                                   │                                         │
                                   │                                   /arm-gate
                                   └────────────────────────┬───────────────┘
                                                            │
                                                  next gate executes …
                                                            │
                                                  terminal gate done
                                                            │
                                                      /wrap-feature ──▶ PR
```

### 1. Pick — choose the next feature

- **`/pick-feature`** — read the roadmap and `LEARNINGS.md`, surface 2–3
  candidates for the next pull with hat-based trade-offs, recommend one. On your
  pick, flips status `planned → active` and prints the next command. Hands off to
  `/draft-feature`.
- **`/roadmap-add`** — add a new feature row to the roadmap before it's ready to
  pick.

### 2. Draft — turn a picked feature into a runnable gate

- **`/draft-feature`** — interactively draft a feature: read roadmap + LEARNINGS +
  exemplars + the project itself, ask framing questions wearing multiple hats,
  propose the gate skeleton and gate 1's work units, write the folder only on
  accept, then lint. Delegates per-WU craft to `authoring-work-units`.
- **`authoring-work-units`** — reference, not an interactive flow: the rules for
  filling the five-section WU contract well, each tied to a real failure mode.
  Read it while drafting or reviewing WUs.
- **`/derive-verification`** — draft a `.specfuse/verification.yml` for a project
  by inspecting its CI, tooling manifests, and code. Run this once when
  bootstrapping the loop in a repo that already has CI worth deriving gates from.

### 3. Run — the driver (not a skill)

`python .specfuse/scripts/loop.py` walks the active gate, dispatches each WU as a
fresh session, verifies, and commits. It is a script, not a skill. It either
auto-closes a clean gate or halts at the gate boundary for review.

### 4. Arm — the human checkpoint at each gate

- **`/arm-gate`** — at a gate boundary (driver halted with `awaiting_review`, next
  gate's WUs in `draft`), walk each drafted WU accept / revise / reject, flip
  statuses, mark the completed gate `passed`, and print the resume command. This
  is the methodology's central human checkpoint, made fast.

### 5. Diagnose — when the loop halts on a problem

- **`/gate-status`** — "where do we stand?" Read-only. Walks the current gate's WU
  statuses, `events.jsonl`, and per-attempt notes; synthesizes a per-blocked-WU
  diagnosis: what's blocked, likely root cause, options, recommended action. Run
  this first when the driver stops unexpectedly.
- **`/unblock-wu`** — re-arm one or more `blocked_human` WUs after you fix the
  underlying cause (credentials, spec ambiguity, missing dep). Flips
  `blocked_human → pending`, resets attempts, re-opens the gate if needed, prints
  the resume command.
- **`/abandon-feature`** — cleanly abandon the active feature when retry isn't
  worth it. Flips every non-terminal WU/gate/PLAN/roadmap surface to its
  abandoned state behind a single up-front confirmation.

### 6. Wrap — finish a done feature

- **`/wrap-feature`** — after the terminal gate is `done`, push the feature
  branch, open a PR, optionally watch CI, and point at the next pick. Refuses if
  PLAN.md isn't `done` yet.
- **`/roadmap-archive`** — move a done or abandoned feature's detail section from
  `roadmap.md` to `roadmap-archive.md`, leaving a back-link.

## Cross-cutting

- **`verification`** — the run-and-report-the-gates skill. The same verification
  the driver runs as its exit oracle, available to invoke directly when you want
  to confirm a WU is actually complete before declaring done. Read
  [`methodology.md` §5](methodology.md) for why verification — not the agent's
  self-report — decides done.
- **`/fix-bug`** — triage and fix a reported bug *outside* the feature
  methodology: 1 bug = 1 branch = 1 PR, test-first. Refuses and proposes
  promoting to a feature if the work is large or risky.
- **`/feature-conversion`** — bring an existing feature folder into conformance
  with the current scaffold's structural contract. Runs after `init.sh --upgrade`
  flags a feature as `FAIL`. Interactive, lint-driven.
- **`/learnings-suggest`** — scan `attempt_outcome` events across features,
  cluster non-passing attempts, and surface recurring patterns as candidate
  `LEARNINGS.md` entries. Read-only — you promote. The *additive* half.
- **`/learnings-curate`** — the *compaction* half. `LEARNINGS.md` is loaded whole
  into every planning session, so it must stay bounded. This skill clusters
  duplicate / superseded / over-broad entries and, on your per-cluster accept,
  merges duplicates, retires superseded entries into `LEARNINGS-archive.md`, and
  promotes methodology-wide rules into `.specfuse/rules/*.md`. Mirrors
  `roadmap-archive` for the lessons feedback loop. It never archives an entry just
  because its origin feature is done — provenance is not scope.
- **`/adopt-feature`** — scaffold a dispatchable feature folder from a GitHub
  `specfuse:feature` issue (orchestrator integration). Pairs with
  `.specfuse/scripts/gh_features.py` (discover candidates) and
  `adopt_feature.py`.

## See also

- [`methodology.md`](methodology.md) — the contracts these skills manipulate.
- [`getting-started.md`](getting-started.md) — a narrated run that uses the
  pick → draft → run → arm → wrap path end to end.
