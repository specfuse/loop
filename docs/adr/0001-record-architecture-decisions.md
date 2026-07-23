# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-07-22

## Context

Specfuse-loop makes design decisions that outlive the pull request that
introduced them — the single-lock-per-repo model, the fresh-session-per-work-unit
contract, the event-schema shape. When such a decision is only captured in a PR
description or a commit body, the reasoning is hard to find later and easy to
relitigate. The roadmap now also supports a `blocked` feature status whose
blocker can be an ADR awaiting approval (see the status legend in
`.specfuse/roadmap.md`); for that to be useful, ADRs need a stable home and a
predictable filename shape to link to.

## Decision

Record architecture decisions as numbered Markdown files under `docs/adr/`,
one decision per file, named `NNNN-kebab-title.md` with a zero-padded ordinal.
Each ADR carries a `Status` (`Proposed` → `Accepted`/`Rejected`, later
`Superseded by ADR-NNNN`), a `Date`, and the sections Context / Decision /
Consequences. ADRs are immutable once `Accepted`: a changed decision is a new
ADR that supersedes the old one, never an in-place rewrite.

A roadmap feature that cannot proceed until a decision is made links the
relevant ADR from its `**Blocked by.**` block and sits at `status: blocked`
until that ADR reaches `Accepted`.

## Consequences

- Decisions have one durable, greppable home; `docs/adr/` is not synced into the
  scaffold seed, so it stays this repo's own record.
- A `Proposed` ADR is a first-class blocker: the roadmap can name *what decision*
  a feature waits on and link straight to it.
- The overhead is one small file per real decision. Not every change needs an
  ADR — only those whose reasoning a future maintainer would otherwise have to
  reconstruct.
