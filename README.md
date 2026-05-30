# Specfuse Loop

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
[Ralph loop](docs/ralph-lineage.md) idea applied at work-unit granularity, with
the planning rigor Ralph's bare task list lacks.

## How it works (in one minute)

- A **feature** lives in `.specfuse/features/FEAT-YYYY-NNNN-slug/`, with a
  `PLAN.md` (the task graph: gate order, work-unit membership, dependencies),
  one `GATE-NN.md` per gate, and one `WU-*.md` per work unit (frontmatter + the
  prompt body a fresh session receives).
- The **driver** (`.specfuse/scripts/loop.py`) walks the current gate's ready
  work units, dispatches each as a fresh `claude -p` session, runs the unit's
  verification itself as the exit oracle, and commits one squashed,
  trailer-carrying commit per unit. A failed gate is retried with a fresh
  session carrying the failure evidence, up to three attempts, then escalated.
- Each gate ends with a fixed **closing sequence** — retrospective, lessons,
  docs, and plan-next — so reflection, a durable cross-feature `LEARNINGS.md`,
  documentation, and *drafting the next gate* all happen systematically rather
  than when you remember to ask.
- The gate is the **human boundary.** The driver runs unattended within a gate
  and stops at it; you review the next gate's draft and arm it. (Under automatic
  mode, safe gates can self-arm; the dangerous edges always pull you back in —
  see the methodology doc.)

## Quickstart

In a target single-repo project:

```bash
# from the specfuse-loop checkout
./init.sh /path/to/your-project

# then, in your project
cd /path/to/your-project
pip install pyyaml
$EDITOR .specfuse/verification.yml      # match the `code` gates to your stack
# author your first feature folder under .specfuse/features/ from .specfuse/templates/
python .specfuse/scripts/loop.py --dry-run
python .specfuse/scripts/loop.py
```

This repository is also a **self-demonstrating reference installation**: its own
`.specfuse/` contains a worked example feature
(`features/FEAT-2026-0001-health-endpoint/`). From the repo root you can run:

```bash
pip install pyyaml
python .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0001-health-endpoint
python .specfuse/scripts/loop.py --dry-run
```

## Layout

```
specfuse-loop/
├── LICENSE  NOTICE  CONTRIBUTING.md  README.md  .gitignore
├── init.sh                      scaffold .specfuse/ into a target repo
├── docs/
│   ├── methodology.md           the gate-cycle contract (shared with the orchestrator)
│   ├── architecture-addendum-gates-and-iterative-planning.md
│   └── ralph-lineage.md         why the loop exists; the Ralph / Gas Town lineage
└── .specfuse/                   canonical scaffold + worked example
    ├── README.md
    ├── roadmap.template.md  verification.yml.example  LEARNINGS.md
    ├── rules/result-contract.md
    ├── skills/verification/SKILL.md
    ├── scripts/{loop.py, lint_plan.py}
    ├── templates/{PLAN,GATE,WU}.template.md
    └── features/FEAT-2026-0001-health-endpoint/   (the worked example)
```

## Status

Early. The driver, linter, parsing, dependency ordering, draft/arm gating, and
verification wiring are tested; the gate *cycle as a way of working* — and in
particular whether `plan-next` drafts a next gate you would actually arm — is
what the first real features are meant to prove. Treat the methodology contracts
as still-moving until that evidence exists.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
