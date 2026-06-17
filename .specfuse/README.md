# Specfuse loop — single-repo starter kit (exploded layout)

A Ralph-style executor for the **Plan + Work Unit** pattern, sized for a self-contained
repo (e.g. the Specfuse Generator). It runs a feature's work units gate by gate, with a
fresh agent session per unit, and stops at each gate for you to reflect — and the next
gate's work units are already drafted and waiting for your review. The same core folds
into the Specfuse Orchestrator for multi-repo work; the environment-specific parts are
isolated behind a seam (see the end of this file).

> **New here?** `init.sh` ships the durable docs into `.specfuse/docs/`. Start with
> [`docs/getting-started.md`](docs/getting-started.md) (install → first feature →
> operating a run), then [`docs/skills.md`](docs/skills.md) and
> [`docs/methodology.md`](docs/methodology.md).

## Layout

```
.specfuse/
  roadmap.md                  # master index: features + feature status   (template: roadmap.template.md)
  LEARNINGS.md                # cross-feature durable lessons, appended each gate
  verification.yml            # this repo's gate commands                  (example: verification.yml.example)
  features/
    FEAT-2026-0001-health-endpoint/        # one folder per feature
      PLAN.md                 # the task GRAPH: gate order, WU membership, dependency edges, feature status
      GATE-01.md              # gate status + definition of done + reflection notes
      GATE-02.md
      WU-01-health-endpoint.md            # self-contained: frontmatter + the prompt body
      WU-02-endpoint-tests.md
      WU-90-gate-1-retrospective.md       # closing sequence (enforced by the linter)
      WU-91-gate-1-lessons.md
      WU-92-gate-1-docs.md
      WU-93-gate-1-plan-next.md
      RETROSPECTIVE.md        # feature-local raw observations    (produced at run time)
      GATE-01-REVIEW.md       # plan-next's findings for your review (produced at run time)
      events.jsonl            # per-feature event log             (produced at run time)
  rules/
    result-contract.md        # the agent -> driver RESULT block contract
  skills/
    verification/SKILL.md     # run-and-report the gates before declaring done
  scripts/
    loop.py                   # the driver
    lint_plan.py              # structural validator (also plan-next's verification gate)
    gh_features.py            # list a repo's open specfuse:feature issues as candidates
    adopt_feature.py          # scaffold a feature folder from a picked GitHub issue
    gh_backend.py             # GitHubBackend(Backend): state:* label transitions for adopted features
  templates/
    PLAN.template.md  GATE.template.md  WU.template.md
```

**Ownership — one fact, one home.** PLAN.md owns the *shape* (gates, membership,
dependencies). Each GATE file owns its *gate status*. Each WU file owns *its own status*
and carries *its own prompt*. Dependencies live in PLAN.md, never in WU frontmatter — a
dispatched session never needs to know its own dependencies; scheduling is the driver's
job. This is exactly the Specfuse Orchestrator's feature/task split, one level down.

## Setup

```bash
cp .specfuse/roadmap.template.md      .specfuse/roadmap.md
cp .specfuse/verification.yml.example .specfuse/verification.yml
pip install pyyaml
# edit verification.yml so the `code` gates match your stack AND your branch protection
```

Author a feature folder from the templates (the included `FEAT-2026-0001-health-endpoint`
is a worked example you can copy and adapt), or adopt one from a GitHub `specfuse:feature`
issue via the `/adopt-feature` skill or `python .specfuse/scripts/adopt_feature.py <repo>
<issue-number>`. Then create the feature branch named in PLAN.md's frontmatter.

## The lifecycle

1. **Validate** the feature's structure before running:
   ```bash
   python .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0001-health-endpoint
   ```
2. **Dry-run** to see the current gate walked, in dependency order, without dispatching:
   ```bash
   python .specfuse/scripts/loop.py --dry-run
   ```
3. **Run** (uses the single active feature, or pass `--feature <dir>`):
   ```bash
   python .specfuse/scripts/loop.py
   ```

For each ready work unit the driver marks it `in_progress`, dispatches a **fresh**
`claude -p` session with the unit's model and prompt body, runs the unit's verification
**itself** as the exit oracle, and on pass makes **one squashed commit** carrying the
`Feature: FEAT-.../TNN` trailer. On a failed gate it discards the attempt and
re-dispatches a fresh session carrying the failure evidence, up to three attempts, then
escalates the unit to `blocked_human` and halts the gate.

The gate's closing sequence runs automatically as its last four units:
**retrospective → lessons → docs → plan-next.** Retrospective writes feature-local
observations; lessons promotes the generalizable subset to the root `LEARNINGS.md`; docs
reconciles documentation and the roadmap; **plan-next (Opus) drafts the *next* gate's
work units** (as `draft`), wires them into PLAN.md, and writes `GATE-NN-REVIEW.md`.

4. **Review and arm.** When the gate completes the driver stops. The next gate is already
   drafted. Read `GATE-NN-REVIEW.md` — it is weighted toward where the planner was *least*
   certain and tells you where to look. Edit or accept the draft WU files, flip the ones
   you accept to `status: pending`, set the finished gate's status to `passed`, and re-run.
   The driver will refuse to execute a gate whose units are still `draft` — arming is the
   human checkpoint, and it is deliberately not automated.

## Design notes

- **Fresh context per dispatch.** Each unit is a new session; durable state lives in the
  plan, GATE/WU files, git history, the event log, and `work/` failure notes — never in a
  context window. That is the Ralph property, kept at work-unit granularity because your
  units are crafted to land in one pass.
- **The driver is dumb on purpose.** Parse, dispatch, verify, commit, advance. No build
  logic. Intelligence is in the WU prompts, the shared rules, and the gates.
- **Verification is the exit oracle.** The agent's RESULT is advisory; the driver re-runs
  the gates and they decide done. Keep `verification.yml`'s `code` set in lock-step with
  branch protection.
- **The gate is the human boundary.** Unattended within a gate; hard stop at it. The
  closing sequence makes reflection, lessons, docs, and *next-gate drafting* happen
  systematically — and plan-next drafts but never arms, so the highest-leverage human
  checkpoint stays human.
- **Pattern enforcement is a prompt concern.** Want TDD order or a structure? Put it in the
  WU prompt and the shared rules; the fresh session follows it every dispatch.

## Folding into the Specfuse Orchestrator

Everything portable transfers as-is: the WU contract, the rules and verification skill, the
RESULT block, squash-per-WU commits, the correlation-ID scheme, the linter, and the loop
logic. Three things are environment-specific and swap at fold-in:

| Concern        | Single-repo (here)                 | Orchestrator (multi-repo)              |
|----------------|------------------------------------|----------------------------------------|
| State backend  | status in WU / GATE file frontmatter; `GitHubBackend` for adopted features (issue labels) | GitHub issue labels + feature registry |
| Dispatch       | `loop.py` shells out directly       | inbox files + polling loop             |
| Branch / merge | one branch, squash per WU           | branch + PR per task, merge watcher    |

The state backend is behind the `Backend` class in `loop.py` — subclass it to write issue
labels and nothing above it changes. `GitHubBackend` (`gh_backend.py`) does this for adopted
features: `make_backend(feat_fm)` selects `GitHubBackend` when `source_issue_url` is present
in PLAN.md frontmatter, and transitions `state:ready → state:in-progress → state:done` on the
GitHub issue as the loop grinds. The branch/merge strategy genuinely differs (a multi-repo
feature cannot be one branch), so it is meant to differ — don't force portability there.
