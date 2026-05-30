# Contributing to Specfuse Loop

Specfuse Loop is part of the Specfuse methodology suite, alongside
`specfuse/codegen` and `specfuse/orchestrator`. Each project is independently
adoptable; contributions should keep the loop usable on its own, with no hard
dependency on the other two.

## Ground rules

- **Open-source hygiene from every commit.** No consumer-product names, no
  private-organization names, no internal URLs, no fixtures containing
  sensitive data. Write every commit message and code comment as if a stranger
  will read it. Apache 2.0 license headers belong on source files from the
  first commit.
- **Boring beats clever.** Git, Markdown, a polling/driver loop, plain files.
  Every piece should be individually replaceable. Nothing load-bearing that
  needn't be.
- **The contract is shared; the implementation is local.** The gate-cycle
  methodology, the work-unit contract, the correlation-ID scheme, and the
  verification discipline are shared vocabulary with `specfuse/orchestrator`.
  Changes to those contracts are coordinated, not unilateral — see
  `docs/methodology.md`.

## Before opening a PR

- Run `python .specfuse/scripts/lint_plan.py .specfuse/features/<feature>` on
  any feature folder you touched.
- Run `python .specfuse/scripts/loop.py --dry-run` against the bundled example
  and confirm it still walks the gate in dependency order.
- Keep changes scoped. A PR that changes the loop driver and the methodology
  contract at once is two PRs.

## Reporting

Use the issue tracker for bugs and design discussion. For anything touching the
shared contracts, say so explicitly in the issue title so it can be coordinated
with the other Specfuse projects.
