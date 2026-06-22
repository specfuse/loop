# Specfuse Loop

**For engineers using AI coding agents** — a local-first driver that structures features as verified, work-unit sequences so each agent session runs focused on one task instead of accumulating context drift.

A small, local-first executor for the **Plan + Work Unit** pattern in a single
repository. You plan a feature as a sequence of *gates*, each a batch of
self-contained *work units* with explicit acceptance criteria and verification.
The loop dispatches each work unit to a fresh agent session, verifies the result
itself, commits one squashed commit per unit, and stops at each gate so you can
reflect — with the next gate already drafted and waiting for your review.

Specfuse Loop is one of three independently-adoptable projects under the Specfuse
methodology suite:

- **`specfuse/codegen`** — deterministic source code from OpenAPI / AsyncAPI /
  Arazzo specifications.
- **`specfuse/loop`** — *this project*. Single-repo, spec-optional, lightweight.
  You author the task graph directly; no specification and no agent-coordination
  overhead are required.
- **`specfuse/orchestrator`** — multi-repo, spec-first, agent coordination across
  many component repositories.

Use any one without the others. The loop and the orchestrator share the same
gate-cycle methodology (see [`docs/methodology.md`](docs/methodology.md)); the
loop is the lightweight surface for work that lives in one repo and may have no
formal specification.

## Why it exists

AI coding agents do well on narrow, well-scoped work and poorly on large, vague
work. The loop's bet is that the leverage is in the *planning*: if you remove
ambiguity up front — crisp work units with hard boundaries and machine-checkable
verification — then execution can run with a fresh agent per unit, re-grounding
from durable files each time rather than accumulating context drift. It is the
[Ralph loop](docs/concepts/ralph-lineage.md) idea applied at work-unit granularity, with
the planning rigor Ralph's bare task list lacks.

## How it works (in one minute)

- A **feature** lives in `.specfuse/features/FEAT-YYYY-NNNN-slug/`, with a
  `PLAN.md` (the task graph: gate order, work-unit membership, dependencies),
  one `GATE-NN.md` per gate, and one `WU-*.md` per work unit (frontmatter + the
  prompt body a fresh session receives). The loop also handles *orchestrated*
  features dispatched by the Specfuse Orchestrator, identified by
  `INIT-YYYY-NNNN/FNN` IDs — the loop treats both namespaces identically; only
  the ID root differs. Use `.specfuse/scripts/gh_features.py` to discover a
  target repo's open `specfuse:feature` issues as feature candidates; use
  `.specfuse/scripts/adopt_feature.py <repo> <issue-number>` (or the
  interactive `/adopt-feature` skill) to scaffold a dispatchable feature
  folder from a picked issue.
- The **driver** (`specfuse-loop`, from the pip package) walks the current gate's
  ready work units, dispatches each as a fresh `claude -p` session, runs the unit's
  verification itself as the exit oracle, and commits one squashed,
  trailer-carrying commit per unit. A failed gate is retried with a fresh
  session carrying the failure evidence, up to three attempts, then escalated.
- Each gate ends with a **closing sequence** so reflection, a durable
  cross-feature `LEARNINGS.md`, documentation, and *drafting the next gate* all
  happen systematically. Non-terminal gates use a two-WU form
  (`close-intermediate` + `plan-next`); the terminal gate uses a single `close`
  WU. A legacy four-WU form (`retrospective → lessons → docs → plan-next`) is
  accepted but emits a lint warning.
- The gate is the **human boundary.** The driver runs unattended within a gate
  and stops at it; you review the next gate's draft and arm it. (Under automatic
  mode, safe gates can self-arm; the dangerous edges always pull you back in —
  see the methodology doc.)

## Quickstart

In a target single-repo project:

**Contributing to this repo?** Run `./scripts/install-hooks.sh` once after
cloning to enable the pre-push hook (runs `scripts/smoke-test.sh` — same
checks CI runs — before each `git push`). Bypass with `git push --no-verify`.

The driver installs from PyPI and the skills ship as a Claude Code plugin:

```bash
pip install specfuse                            # umbrella CLI; pulls specfuse-loop>=0.3.0
#   gives you: specfuse, specfuse-loop, specfuse-lint

# in Claude Code, enable the skills plugin (one-time):
#   /plugin marketplace add specfuse/specfuse
#   /plugin install specfuse@specfuse

specfuse init /path/to/your-project             # scaffold .specfuse/ + wire .claude/ (--dry-run previews)

cd /path/to/your-project
$EDITOR .specfuse/verification.yml              # match the `code` gates to your stack
# author your first feature (in Claude Code: /draft-feature)
specfuse-loop --dry-run                          # show the gate walk, no dispatch
specfuse-loop                                    # the real run
```

> **Distribution.** Code ships via pip — `specfuse` (umbrella CLI: `init` /
> `upgrade`) pulls `specfuse-loop` (the driver); Claude assets ship via the
> [`specfuse/specfuse`](https://github.com/specfuse/specfuse) plugin marketplace.
> `specfuse init` lays down `.specfuse/` and wires `.claude/`; `specfuse upgrade`
> overlays a newer scaffold and pip-upgrades both packages. Every `specfuse-loop`
> run self-provisions (version-syncs `.specfuse/` from the installed package), so
> an upgrade reaches existing projects on their next run. (`./init.sh` is a
> deprecated v1.0 shim that delegates to `specfuse init`/`upgrade`; slated for
> removal.)

> **One driver per working tree.** The driver holds an exclusive advisory lock on
> `.specfuse/.loop.lock` for the duration of a run; a second driver targeting the
> same checkout exits immediately with a clear error message. To run two features
> in parallel, use separate `git worktree` checkouts — each gets its own lock.
> `--dry-run` is exempt and may run alongside a live driver.

This repository is also a **self-demonstrating reference installation**: its own
`.specfuse/` contains a worked example feature
(`features/FEAT-2026-0001-health-endpoint/`). From the repo root you can run:

```bash
python .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0001-health-endpoint
python .specfuse/scripts/loop.py --dry-run
```

## Layout

```
specfuse-loop/
├── LICENSE  NOTICE  CONTRIBUTING.md  README.md  .gitignore
├── init.sh                      deprecated v1.0 shim → delegates to `specfuse init`/`upgrade`
├── docs/
│   ├── getting-started.md       narrated first-feature + operator walkthrough
│   ├── methodology.md           the gate-cycle contract (shared with the orchestrator)
│   ├── skills.md                the skills catalog, ordered by lifecycle phase
│   ├── concepts/                why it exists; orchestrator mapping
│   │   ├── ralph-lineage.md     the Ralph / Gas Town lineage
│   │   └── architecture-addendum-gates-and-iterative-planning.md
│   └── dev/                     internal working notes (not user-facing)
└── .specfuse/                   canonical scaffold + worked example
    ├── README.md
    ├── roadmap.template.md  verification.yml.example  LEARNINGS.md
    ├── rules/result-contract.md
    ├── skills/verification/SKILL.md
    ├── scripts/{loop.py, lint_plan.py, gh_features.py, adopt_feature.py, gh_backend.py}
    ├── templates/{PLAN,GATE,WU}.template.md
    └── features/FEAT-2026-0001-health-endpoint/   (the worked example)
```

`specfuse init` also ships the durable docs — `methodology.md`, `skills.md`, and
`concepts/` — into a target's `.specfuse/docs/`, so an initialized repo is
self-documenting without this checkout.

## Status

Early but exercised. The driver, linter, parsing, dependency ordering, draft/arm
gating, the deterministic auto-close predicate, and verification wiring are all
tested, and the loop dogfoods itself — its own `.specfuse/features/` holds 20+
features taken through the full gate cycle, including multi-gate features whose
forward-design model (each gate's `plan-next` drafts the next) has held across
four consecutive gates.

What works today: single-feature and orchestrator-dispatched features; adopting a
GitHub `specfuse:feature` issue into a dispatchable folder; GitHub issue-label
state transitions for adopted features; per-gate auto-close on clean runs with a
full-ceremony fallback when a gate goes off-plan; and a single-driver working-tree
lock so two drivers can't corrupt one checkout.

Expect rough edges. The interfaces (WU contract, RESULT block, correlation-ID
scheme, `verification.yml` shape) are stable; tooling around them is still
hardening.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
