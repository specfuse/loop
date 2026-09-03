# Glossary

The words Specfuse uses, in the order you meet them. Each entry says what the
thing *is* and, where one exists, the command or skill that acts on it.

For the full contract behind any of these, see
[`methodology.md`](methodology.md); this page is the first read, not the
reference.

## The shape of the work

**Roadmap** — `.specfuse/roadmap.md`, the ordered list of features a project
intends to build, one row each. Add to it with `/roadmap-add`; pick what to
build next with `/pick-feature`.

**Feature** — one substantial piece of work, `FEAT-YYYY-NNNN`, with a folder
under `.specfuse/features/`. Its `PLAN.md` holds the goal, the gates, and the
budget. Roughly: a thing you would describe in a sentence to someone who does
not work on the project.

**Gate** — a stage of a feature, numbered from 1. A gate holds a set of work
units, a budget, and acceptance criteria. **The gate is where the loop stops
and you decide** — everything inside one runs unattended; the boundary between
two is yours.

**Work unit (WU)** — the smallest dispatchable piece: one file, one job, one
fresh session. `FEAT-YYYY-NNNN/T01`. Everything the session needs is in that
file, because it starts with no memory of anything before it.

**Verification** — the commands in `.specfuse/verification.yml` that decide
whether a work unit actually passed. The loop runs them itself and does not
take the session's word for it.

**LEARNINGS** — `.specfuse/LEARNINGS.md`, what earlier work taught, carried
into later planning so the same mistake is not made twice.

## What happens to it

**Draft** — write a feature and its first gate's work units, usually with
`/draft-feature`. Drafted units are proposals; nothing runs yet.

**Arm** — review the drafted units and accept, revise, or reject each, then
release the gate to run. This is the human checkpoint. `/arm-gate`.

**Dispatch** — hand one work unit to a fresh session and let it work.
`specfuse run` walks the current gate and dispatches whatever is ready.

**Attempt** — one dispatch of one work unit. A unit gets three before the loop
gives up and asks you.

**Close** — the ceremony that ends a gate: what was learned, what it cost,
whether the goal was met, and drafting the next gate. The loop runs it as a
work unit like any other.

**Wrap** — finish the feature: push the branch, open the pull request.
`/wrap-feature`.

**Self-provisioning** — every `specfuse run` first checks whether
`.specfuse/` matches the installed version and updates it if not, so an upgrade
reaches a project on its next run.

## States you will see

**A feature** is `planned`, `active`, `blocked`, `done`, or `abandoned`.
`blocked` means a named dependency is unmet — clear it with `/block-feature
--unblock`.

**A gate** is `open` (running), `awaiting_review` (finished, waiting for you to
arm the next one), or `passed`.

**A work unit** is `draft`, `pending` (armed, waiting its turn), `in_progress`,
`done`, `abandoned`, or `blocked_human`.

**`blocked_human`** — a unit tried, failed three times, and stopped. Nothing is
broken and nothing is lost; it needs a decision. `/gate-status` explains what
happened, `/unblock-wu` re-arms it once you have fixed the cause.

**A close verdict** is `met` (the goal was achieved and shown) or `not_met`.
There is no partial credit. A `not_met` close writes `FOLLOW-UPS.md` — one
entry per criterion it could not meet — and the loop files one tracked issue
per entry, so what is unfinished is visible as work rather than softened into
the verdict.

**`FOLLOW-UPS.md`** — the record a `not_met` close leaves behind: per failed
criterion, the criterion itself, the evidence, and what would satisfy it.

**A `type: human` work unit** — a step only a person can perform (reply, sign,
click, run something interactively). The loop halts on it rather than
dispatching it; you do the step, mark it `done` with `evidence:`, and the run
resumes. It goes *before* the close, so the human step is recorded rather than
hedged after the fact.

**`## Post-merge checklist`** — an optional `PLAN.md` section for anything only
observable in production. It is filed as one tracked issue at close; it is
never an acceptance criterion.

## Terms that look like jargon because they are

**Oracle** — the check that decides pass or fail. A *narrow* oracle tests one
specific thing, so a pass can be trusted later; a *broad* one (a whole test
suite) covers too much for its green to be carried forward.

**`produces:`** — the files a work unit promises to deliver. The loop compares
them against what actually changed, so a unit cannot report success having
written nothing.

**Hollow pass** — a work unit reporting success without changing anything. The
`produces:` check exists to catch it.

**Spinning** — repeated attempts making no progress. The loop detects it and
stops rather than spending the remaining budget.

**Re-arm** — putting a stopped work unit back in the queue after fixing the
cause. Requires a one-line reason from you, which is the record of why it was
worth retrying.

**Escalation** — the loop stopping to ask you something, with what it tried,
why it stopped, the options, and a recommendation.

**Auto mode** — letting safe gates arm themselves. The dangerous boundaries
still stop for you. See
[`concepts/adopting-auto-mode.md`](concepts/adopting-auto-mode.md).
