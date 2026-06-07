# LEARNINGS

Durable, reusable rules distilled from every gate's retrospective. The `lessons` work
unit appends here; planning reads here before detailing any new feature. This is the
feedback loop that makes each plan better than the last.

Append only. Phrase each entry as a rule that would change how a FUTURE work unit is
written or executed, not a one-off observation. De-duplicate against what is here.
Feature-specific observations stay in that feature's `RETROSPECTIVE.md` and are not
promoted here.

## Format

```
- [FEAT-2026-0001/G1] Implementation WUs must name the module a new route/handler
  lives in; "add it to the router" cost a blocked attempt when no router existed yet.
```

## Entries

<!-- lessons work units append below this line -->

- [meta/first-live-use] Scope a feature's acceptance criteria to the feature's
  own footprint — its slug, the paths it creates or edits, the symbols it
  introduces. Acceptance criteria that grep or scan the WHOLE repo will trip
  on pre-existing, unrelated state and (correctly) cause the agent to emit
  `status: blocked` even when the WU's own work is fine. Example failure mode:
  a "no TODO comments anywhere in the tree" check that fires on legacy code
  the WU never touches. Rule: bound checks to the feature's path prefixes
  (e.g. `src/<slug>/**`) or to files the WU declares in `generated_surfaces` /
  `files_changed`; repo-wide invariants belong in a separate hygiene WU or in
  the repo's `code` gate set, not in a per-feature acceptance criterion.

- [meta/first-live-use] Name what the WU is expected to PRODUCE, not only what
  it must NOT touch. The "Do not touch" section bounds the WU on one side;
  without an equally-explicit "produces" list, an agent can helpfully write
  files that should belong to a later WU (e.g. docs that were T92's job
  showing up in T01's commit) without the verification gates objecting. Rule:
  in addition to the "Do not touch" list, the WU's Acceptance criteria should
  name the specific files/sections the WU is expected to author. A reviewer
  reading the diff should be able to point at every changed file and find it
  in either the WU's produces-list or the gate's verification output.

- [meta/first-live-use] The "hygiene WU" pattern — when a substantive WU
  discovers a pre-existing bug in a path its "Do not touch" rule forbids
  (typical case: shared module, infrastructure config, dependency version),
  the right move is to insert a narrow hygiene WU EARLIER in the gate (or as
  a precursor gate) that fixes only that issue. Not: loosen the blocked WU's
  scope to permit the cross-cutting fix (muddies its boundary). Not: fix it
  manually out-of-loop and pretend the gate ran clean (silent drift between
  the methodology's history and git's). The hygiene WU should have a single,
  obvious acceptance criterion ("module X's attribute Y matches the
  azurerm-3.x name `automatic_channel_upgrade`") and pass on its own
  verification; the original blocked WU then runs after, unmodified.

- [meta/loop-driver-bugs] Driver bookkeeping (frontmatter status flips,
  events.jsonl appends, per-attempt notes) must be committed if it should
  survive across WUs — uncommitted writes are wiped by the inter-attempt
  `git reset --hard`. The fix in commit bcc9bee separates agent-work commits
  (per-WU squash) from bookkeeping commits (`chore(loop): ...`). When
  authoring WUs whose verification commands themselves write to disk,
  remember the agent's working tree is reset between failed attempts —
  scratch files written during a failed attempt won't persist into the next
  attempt's prompt unless the agent explicitly buffers them in the prompt-
  facing failure note that the driver hands to the next attempt.

- [FEAT-2026-0003/G1-LESSONS] State the exact expected file count in the
  Do-not-touch section (e.g. "exactly three files: X, Y, Z"). An agent that
  touches one extra file to be helpful does so because the WU did not
  explicitly forbid it — a numeric bound closes that door without ambiguity.
  Both T01 (3 files) and T02 (2 new files) finished in one attempt with no
  scope drift; attribute at least part of that to the explicit count. Rule:
  every WU's Do-not-touch must name specific paths AND state the total count
  of files expected to change, so a reviewer reading the diff has a
  falsifiable scope claim.

- [FEAT-2026-0003/G1-LESSONS] When a WU defines a CLI surface or invokes an
  external command that returns structured data, the AC must specify three
  things: (1) the exact fields/keys to request or parse, (2) the output
  field delimiter (tab, space, comma), and (3) how to render an absent or
  None optional field (empty string, `-`, or another sentinel). Omitting
  any of these forces the agent to make a reasonable-but-breaking choice the
  next consumer inherits silently. T02's CLI printed the Python string
  `"None"` for a missing `task_type` because the WU said what to print but
  not how to render absence. A parser expecting an empty field gets the
  literal four-character string instead.

- [FEAT-2026-0003/G1-LESSONS] Cut gates along the offline/live boundary:
  a gate whose entire scope can be unit-tested without external systems
  (network, live auth, real API) can be verified deterministically and
  atomically by the driver. Live integration belongs in a dedicated later
  gate. The benefit is not just CI speed — it is that the offline gate's
  verification is free of flakiness, reproducible across machines, and
  never blocked by token/quota limits. Rule: when detailing a new gate, ask
  "can every WU in this gate be tested without a network call?" If yes, mark
  it offline-first in the PLAN and keep live-integration WUs out of scope
  for that gate.

- [FEAT-2026-0003/G1-LESSONS] Closing-WU numbering conventions (e.g.
  "90+ range so they sort last") must live in a binding rule or the
  `draft-feature` template, not in a PLAN.md comment. A comment in one
  feature's PLAN is invisible to the next feature's author and produces
  inconsistent scaffolding. Rule: any implicit scaffold convention that
  future `draft-feature` runs must reproduce — WU numbering, section
  ordering, required closing sequence — belongs in `.specfuse/rules/` or
  the WU authoring guide, and the linter should enforce it if feasible.
