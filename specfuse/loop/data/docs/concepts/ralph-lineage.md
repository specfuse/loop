# Why the loop exists — lineage and positioning

## The Ralph lineage

The loop descends from the "Ralph" technique: in its purest form, a bash loop
that feeds a prompt to a coding agent repeatedly until the work is done, with a
fresh context each iteration and durable state kept in files (git history, a
progress file, a task list) rather than in the context window. Its insight is
that for large work, *stubbornness plus fresh context* beats a single clever
pass — the loop is the hero, not the model.

Ralph's known weakness is the thinness of its task list: a bare list of TODOs
gives an agent nothing to enforce patterns against, so it drifts. The ecosystem's
answer to "that's too coarse for serious work" has been to make the units of work
granular and self-contained enough that ephemeral workers can pick them up,
execute, and hand off — orchestration of many such workers ("Gas Town"-style).

The Specfuse Loop is that idea with the planning rigor added back in. It keeps
Ralph's fresh-context-per-iteration property but moves it to **work-unit
granularity**, and it replaces the thin task list with the **Plan + Work Unit**
pattern: crisp work units with hard "do not touch" boundaries, explicit
acceptance criteria, and machine-checkable verification gates. The up-front
planning investment is precisely what earns the right to let execution run
unattended — the richer the unit, the longer the loop can safely run before a
human checkpoint.

Two things distinguish it from vanilla Ralph:

- **Verification is the exit oracle, not the agent's say-so.** The driver re-runs
  the unit's gates and they decide done — eliminating Ralph's classic
  premature-"done" failure.
- **Gates are human checkpoints by design.** The loop runs unattended *within* a
  gate and stops *at* it. Reflection, a cross-feature learnings rollup, and
  drafting the next batch happen systematically as the gate's closing sequence,
  not when someone remembers to ask.

## Where it sits in Specfuse

Specfuse is a methodology and an organization, not a single tool. Three
independently-adoptable projects live under it:

- **`specfuse/codegen`** turns OpenAPI / AsyncAPI / Arazzo specifications into
  deterministic source code — the boilerplate no one should hand-write and no
  agent should hallucinate.
- **`specfuse/loop`** (this project) executes the Plan + Work Unit pattern in a
  single repository, with no specification required and no agent-coordination
  overhead. The lightweight surface.
- **`specfuse/orchestrator`** coordinates specialized agents across many
  component repositories from validated specifications — the heavyweight surface
  for multi-repo, spec-first feature delivery.

The loop and the orchestrator are two execution surfaces of **one** methodology
(see [`methodology.md`](../methodology.md)); they share the gate cycle, the
work-unit contract, the correlation-ID scheme, and the verification discipline.
The loop is the right home for work that lives in one repo or has no formal
spec; the orchestrator is the right home when the work genuinely spans repos and
is driven by specifications that `codegen` can turn into a stable foundation.

## What it is not

- Not a general-purpose AI coding platform. It does one shape of work:
  plan-driven, gated, fresh-context execution in a single repo.
- Not a replacement for human judgment. Every gate is a human checkpoint; the
  loop keeps agents *inside* a loop, it does not remove the loop.
- Not a hosted service. It runs on your machine, against your repo, under your
  accounts.
