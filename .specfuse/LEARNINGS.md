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

- [FEAT-2026-0003/G2-LESSONS] Output volume above ~80k tokens in a single
  WU session is a prospective split signal, not just a retrospective
  warning. T03 produced 95k output tokens (6× the prior max) because it
  combined new script logic, 260 lines of tests requiring intimate
  knowledge of another module's internal data structures, AND a one-line
  cross-gate fix. The WU succeeded in one attempt, but it is not the safe
  default for WUs of similar density. Rule: when a WU spec includes (a)
  two or more new files totalling 400+ lines AND (b) a test suite that
  must replicate another module's internal schemas or protocol shapes to
  write correct stubs, split at the logic/test-coverage seam: a script WU
  lands first, a test-coverage WU (T0N-test) runs after it. The split
  point is justified by coupling — tests that depend on the script's
  internals cannot be authored before the script exists anyway.

- [FEAT-2026-0003/G2-LESSONS] When a WU's acceptance criteria include a
  linter integration ("tool X exits 0 on the produced artifact"), the spec
  must also include a companion failure-mode AC: "tool X exits non-zero on
  a known-bad version of that artifact." Without an explicit failure-mode
  AC, an agent will implement and test the happy path only; the rejection
  direction tests only the linter's own correctness, not the integration
  from this WU's output. Rule: for every AC of the form "lint_plan / ruff
  / mypy exits 0 on artifact Y," add a sibling AC naming a specific
  malformed variant and asserting a non-zero exit. T03's `TestMalformedBody`
  test class was added via a pre-arm review catch, not from the original
  spec — it would not have been written without that catch.

- [FEAT-2026-0003/G2-LESSONS] Automated code gates (tests, ruff, bandit,
  coverage --fail-under) pass trivially for prose and markdown artifacts.
  A WU whose only output is a SKILL.md, a doc file, or a template receives
  a structurally vacuous "pass" from the driver — no test runs, no linter
  fires, nothing falsifiable executes. Rule: for WUs producing purely prose
  artifacts, the Verification section must declare one of: (a) a structural
  linter that checks required sections/keys (e.g. `grep -c "^## Method"
  SKILL.md`), or (b) "human review at PR" as the explicit verification
  gate with a checklist of what the reviewer must confirm. Letting code
  gates stand in for prose quality produces a false-positive "pass" signal
  that the driver cannot distinguish from a real verification.

- [FEAT-2026-0003/G2-LESSONS] The hygiene WU pattern
  ([meta/first-live-use]) covers *surprise* cross-cutting fixes discovered
  during a WU's execution. It does NOT apply to cross-module changes the
  WU author already anticipated: if a change to a gate-N module is listed
  in the WU's own AC 0 before dispatch, that change belongs bundled into
  the substantive WU — creating a hygiene WU for it adds unnecessary gate
  complexity. The distinction is: surprise-during-grind → hygiene WU;
  planned-and-listed-in-ACs → bundle and document in the commit message.
  T03 widened `gh_features.list_features` (planned, in AC 0) correctly as
  a bundle; the commit message explicitly called out both concerns. Rule:
  before inserting a hygiene WU, check whether the cross-cutting change was
  already in the dispatched WU's ACs. If it was, the hygiene WU is the
  wrong tool — strengthen the commit message instead.

- [FEAT-2026-0003/G2-LESSONS] Scaffold-generated WU bodies (from
  `adopt_feature.py`, `draft-feature`, or any template emitter) are
  structural scaffolding, not actionable specs. The `_closing_wu()` helper
  in T03's adopt script generates closing WUs with generic ACs ("The
  artifact for this unit exists and is substantive") and generic escalation
  triggers. These satisfy the linter's five-section structural check but
  are not dispatchable without human refinement. Rule: any WU whose body
  was generated by a scaffold tool must be reviewed and its ACs rewritten
  to be specific and falsifiable before the driver dispatches it. The
  plan-next WU (Opus model) is the natural checkpoint for this review —
  G2-PLAN's scope should include a pass over every scaffold-generated WU
  body in the gate it details.

- [FEAT-2026-0003/G3-LESSONS] When a WU's acceptance criteria name values
  that live in an external system — label names, API field names, event
  schema keys, shared protocol constants — those values must be verified
  against the authoritative documentation in that external system before
  the gate is armed. Inventing plausible values from the feature's internal
  conventions is a silent correctness risk: the value looks right to the
  author, satisfies the WU's AC, and only fails at smoke time. T06's label
  scheme (`loop:in-progress`/`loop:complete`) was invented by G2-PLAN; the
  correct scheme (`state:in-progress`/`state:done`) came from reading the
  orchestrator's `naming-convention.md §5.1` and `labels.md` at gate-3
  arming time. Rule: for every WU AC that references an external system's
  vocabulary, add a pre-arm check line to the WU spec: "verify [value]
  against [authoritative source] before locking this AC." The gate review
  document is the right place to list these open verifications; the gate is
  not armed until every item is checked.

- [FEAT-2026-0003/G3-LESSONS] The two-case linter test pattern from
  [FEAT-2026-0003/G2-LESSONS] ("exits 0 on valid artifact, exits non-zero
  on malformed artifact") is incomplete when an adapter embeds content from
  an external surface verbatim. A third case is required: the external
  surface's format variant may be structurally valid by that surface's own
  convention but use a syntax the local linter does not accept (e.g., ATX
  headings `## Context` vs the loop's bold-preamble `**Context.**`). Gate 3
  surfaced this exactly: `adopt_feature.py` embedded `#287`'s body verbatim;
  `lint_plan.py` rejected it not because sections were absent but because
  ATX-heading detection was not implemented. Rule: when a WU spec writes an
  adapter that embeds external-source content, add a third linter test
  fixture that represents the external surface's actual heading/formatting
  convention (verified against a real example from that surface). If the
  linter rejects this fixture, that is a pre-dispatch blocking finding — the
  linter must be widened before the adapter is dispatchable, not after.

- [FEAT-2026-0003/G3-LESSONS] WUs that mutate state in an external
  production system (live GitHub issues, deployed infrastructure, databases
  with real data) are a categorically different class from automated WUs —
  not because their output is hard to machine-verify (the G2-LESSONS
  prose-artifact problem), but because the mutation itself is irreversible at
  execution time and cannot be safely delegated to the driver's subprocess
  loop. Rule: when a gate plan includes a live-mutation WU, designate it
  out-of-loop in the WU spec before the gate is armed. The WU spec must
  include: (1) an explicit pre-condition checklist stating what to verify
  before running, (2) a cleanup/restore acceptance criterion confirming the
  external system was returned to its pre-smoke state, (3) a smoke journal
  filename as the mandatory output artifact, and (4) `artifact-changed` as
  the driver-side verification proxy. The gate plan's arming note should
  document the human-operated designation so reviewers understand why no
  driver events exist for this WU.

- [FEAT-2026-0003/G3-LESSONS/multi-gate] Plan-next WUs (Opus) produce
  forward-design drafts from the prior gate's artifacts alone — they cannot
  read other repositories or external documentation. This creates a
  systematic blind spot: all values that name cross-repo contracts (label
  namespaces, API field names, event schemas, shared protocol constants)
  will be invented from first principles rather than verified. The
  inventions are not random; they are plausible, internally consistent, and
  wrong in precisely the way a well-reasoned guess is wrong. Gate 3
  confirmed: G2-PLAN named the label-scheme uncertainty in GATE-03-REVIEW.md
  Flagged 2 and prescribed the verification path; the human checked before
  arming and found the correct scheme. The process works when the review
  document is explicit and the human acts on it. Rule: every gate review
  document produced by a plan-next WU must include a "Cross-repo contracts"
  section listing each value the plan invented alongside the authoritative
  source the human must read before arming. The gate is not armed until
  every item in that section is checked and its entry updated with the
  verified value.

- [FEAT-2026-0003/G4-LESSONS] When a terminal-case plan-next WU evaluates
  branch-B (extend with an escalation gate) vs opening a new feature, three
  tests must all pass before gate extension is chosen: (1) **Scope** — the
  fix fits in hours of work, not a feature's worth; a single WU completing
  in minutes is well within the threshold. (2) **Contiguous proof** — the
  smoke evidence, the artifact under fix, and the proposed fix all live on
  the active branch already; a new feature would re-discover the same
  evidence from scratch. (3) **Disciplined trigger** — the escalation fired
  on live, concrete evidence (a specific, reproducible failure against a real
  artifact), not on speculative risk. If all three pass, extend with a gate.
  If any fails — scope grows to weeks, evidence requires a fresh branch, or
  the finding is theoretical — open a new feature instead. Appending gates
  on weak evidence or large scope corrodes the "feature ends" contract and
  trains future plan-next WUs to treat gate extension as a low-cost default.
  T08 closed gate 4 in 2m54s at 7,826 output tokens; the entire fix was
  one regex + three test cases. That scope is the bar.

- [FEAT-2026-0003/G4-LESSONS] A gate's substantive WU count should match
  its actual scope, not be inflated to match a prior gate's shape. Gate 4
  closed the roadmap goal with one substantive WU — the smallest in the
  feature — plus the standard four-WU closing sequence. No extra WUs were
  added for structural symmetry with gate 3's three-WU split. The four-WU
  closing sequence (RETRO → LESSONS → DOCS → PLAN) is fixed scaffolding and
  applies at every gate regardless of size; what varies is the gate's
  substantive WU list. Rule: when sizing a gate — especially an escalation
  gate appended at a terminal case — let the work drive the WU count. A
  single-WU gate on a genuinely bounded fix is correct methodology, not an
  indication the gate was rushed or under-designed.

- [FEAT-2026-0004/G1-LESSONS] Tools that perform tree-global git mutations
  must enforce concurrency at the working-tree level, not at a logical-unit
  or feature-id level. A pidfile is insufficient for the SIGKILL case: the
  pid-holding process is dead, the file remains, and the next launch either
  stalls or skips the check. `flock(2)` (Python: `fcntl.flock(fd, LOCK_EX |
  LOCK_NB)`) is the correct primitive — the kernel releases the advisory lock
  automatically on process exit, including SIGKILL, with no cleanup step.
  Rule: when a WU adds concurrency protection to any subprocess-heavy driver,
  specify `flock` + a `.lock` file tracked in `.gitignore` as the locking
  primitive; explicitly rule out pidfiles in the WU spec and explain the
  SIGKILL rationale so the agent does not substitute a pidfile as a "simpler"
  alternative.

- [FEAT-2026-0004/G1-LESSONS] When a Python function must hold a POSIX
  advisory lock for its entire execution lifetime, assign the file descriptor
  to a named local variable in that function's stack frame and never close or
  release it explicitly. Do NOT use `with` / a context manager (closes the fd
  on `__exit__`), and do NOT assign to `_` (may trigger GC and premature
  release). The kernel releases the flock on process exit — including SIGKILL
  — making `atexit` hooks and `try/finally` unnecessary. Rule: a WU spec that
  requires a "held for process lifetime" lock must state this fd-lifetime
  constraint explicitly; without it, an agent familiar with Python
  context-manager idioms will wrap the acquire in `with`, silently releasing
  the lock at the end of the block.

- [FEAT-2026-0004/G1-LESSONS] When a bootstrap or `init.sh` script must
  append a single line to a file (`.gitignore`, config, `.env.example`)
  idempotently, use `grep -qxF "$line" "$file" || echo "$line" >> "$file"`.
  The `-x` flag (full-line match) prevents a shorter prefix of the line from
  satisfying the check; the `-F` flag (literal string, no regex) prevents
  special characters in the line from producing false positives. Re-running
  the script in either INIT or UPGRADE mode leaves the file untouched when
  the line is already present. Rule: any WU that authors or modifies an
  `init.sh`-style bootstrap script must use this idiom for line-append
  idempotency; a plain `grep -q` without `-xF` is a latent bug waiting for a
  line whose content is a prefix of another line already in the file.

- [FEAT-2026-0004/G1-LESSONS] An escalation trigger is load-bearing only
  when it names the exact structural condition that would fire it — not just
  the outcome ("if this gets complicated, block"). T01's trigger read: "If
  `run()` cannot acquire the lock before a git mutation without a larger
  refactor of its early-setup ordering, block and name the ordering conflict."
  That precision let the agent confirm non-firing explicitly ("the function's
  structure was already compatible") rather than quietly work around the
  constraint. Rule: when authoring a WU that touches an existing function with
  non-trivial call ordering, write the escalation trigger as a falsifiable
  structural claim — name the specific site, the condition, and what a
  violating scenario looks like — so the agent can report "trigger checked,
  did not fire" rather than omitting the check entirely.

- [FEAT-2026-0005/G1-LESSONS] Closing-ceremony weight should scale with
  feature size. The four-WU closing sequence (RETRO → LESSONS → DOCS → PLAN)
  is the right default for multi-gate features, where each gate accumulates
  enough state to justify independent retrospective and planning steps. A
  single-gate feature produces a thin closing sequence that costs more in
  ceremony overhead than it yields in structured value. Rule: when a feature
  is scoped to a single gate from the start, use the `close` WU type to
  collapse the closing sequence into one dispatch. This is not a shortcut —
  the `close` WU still requires the full set of closing artifacts
  (RETROSPECTIVE.md, LEARNINGS.md entries, docs/roadmap reconciliation,
  terminal verdict); it eliminates the four-way dispatch overhead, not the
  obligations.

- [FEAT-2026-0005/G1-LESSONS] When a WU adds a new named type to a
  validation or dispatch system (a WU type, a gate category, a CLI command),
  the WU's acceptance criteria must explicitly require updating every regex,
  constant, or enum that references the full set of valid names. Missing one
  produces a silent correctness gap: the new type works at execution time but
  fails any validation path that checks names by pattern. T01 added the
  `close` WU type; the agent correctly updated `CORRELATION_ID_RE` to include
  the `CLOSE` segment — but this was inferred, not required by the WU AC.
  Rule: before dispatching a WU that introduces a new named type, enumerate
  all regex/enum/constant sites that list type names explicitly and add each
  as a falsifiable AC (e.g. "CORRELATION_ID_RE includes CLOSE segment").

- [FEAT-2026-0005/G1-LESSONS] The two-case linter-guard test pattern
  ([FEAT-2026-0003/G2-LESSONS]: accept valid, reject malformed) needs a third
  case when the change modifies a guard that previously accepted an existing
  class of artifacts: a regression test on a pre-existing valid fixture.
  Without it, a conditional branch added to handle the new case can
  accidentally shadow or break the original acceptance path. T01's third test
  (`test_four_wu_closing_sequence_still_passes`) used the live
  `FEAT-2026-0001-health-endpoint` fixture and confirmed that four-WU features
  still lint cleanly after the `close` branch was added. Rule: when a WU
  modifies a validation guard that previously accepted a class of inputs, add
  "regression on existing valid fixture" as an explicit AC — name a specific
  existing fixture and assert the linter still exits 0 on it.
