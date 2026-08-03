# LEARNINGS

Durable, reusable rules distilled from every gate's retrospective. The `lessons` work
unit appends here; planning reads here before detailing any new feature. This is the
feedback loop that makes each plan better than the last.

Append only. Phrase each entry as a rule that would change how a FUTURE work unit is
written or executed, not a one-off observation. De-duplicate against what is here.
Feature-specific observations stay in that feature's `RETROSPECTIVE.md` and are not
promoted here.

This file is loaded **whole** into every planning session, so it must stay bounded.
The `lessons` step and `/learnings-suggest` ADD entries; `/learnings-curate` is the
compaction counterpart — it merges duplicates, retires superseded entries into
`LEARNINGS-archive.md`, and promotes broadly-applicable rules into
`.specfuse/rules/*.md`. Run it when this file grows large enough to dilute signal.

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

- [FEAT-2026-0006/G1-CLOSE] When a WU implements new per-attempt instrumentation
  fields in the driver (e.g. `duration_seconds`, a future memory counter), that
  WU's own event record will lack those fields — the driver dispatching the
  implementing WU runs old code, before the commit lands. This bootstrap gap is
  structural and expected: the first WU tracked by the new field is the one
  dispatched after the implementing WU's commit. Rule: WU specs that add new
  driver-owned tracking fields should note the bootstrap gap in the Acceptance
  criteria — specifically which fields will be absent from the implementing WU's
  own `events.jsonl` entry — so a reviewer reading the log doesn't flag the
  absence as a correctness bug.

- [FEAT-2026-0007/G1-LESSONS] The `code` gate (`python3 -m unittest discover`)
  passes when no new tests are registered — it cannot detect that required new
  symbols, files, or functions were never written. T04 declared `status: complete`,
  the driver committed only the WU status flip, and verification passed on the
  unchanged codebase because the existing tests made no assertion about the absent
  functions. Rule: any WU that requires new importable symbols must include an
  explicit existence check in its own Verification section — not just "run the
  code gate." The canonical form is `python3 -c "from module import symbol_name"`
  for functions, or `python3 -c "from module import CONSTANT_NAME"` for constants;
  a `grep -c "^def symbol_name"` on the target file is an acceptable alternative
  when the import would trigger side-effects. Without this, an agent can claim
  complete without having written any production code and pass driver verification.

- [FEAT-2026-0007/G1-LESSONS] Escalation triggers guard against wrong changes
  but not against absent changes. T04's trigger read "stop if changing
  `dispatch()`'s signature breaks T02 or T03 tests" — a correct wrong-change
  guard. Its mirror was missing: "stop if the required functions are absent from
  your edits." Rule: every implementation WU that requires new named symbols must
  include a completeness escalation trigger alongside any correctness trigger. The
  canonical form is: "If [required_function_name] / [required_file] is absent
  from the files you edited, emit `status: blocked` — do not claim complete." The
  driver's verification cannot substitute for this because it runs gates against
  the post-commit tree; a completeness gap that passes the gates is invisible to
  the driver and only becomes visible at integration time.

- [FEAT-2026-0007/G1-LESSONS] When WU N produces a constant, directive, or prose
  artifact that WU N+1 must extend or specialize (e.g., T03 produced the
  `CAVEMAN_DIRECTIVE` body; T04 needed a "softer" variant of it), WU N's spec
  must either specify the content or include a note: "the exact text will be
  inferred by WU N+1 from this WU's output." Without that note, WU N+1's author
  has no spec anchor and the agent must infer the upstream content from the commit
  diff — which is correct in context but makes the dependency invisible to future
  readers. Rule: when a chain of WUs progressively refines a shared artifact,
  document the inheritance relationship explicitly in each WU's Context section so
  the dependency is auditable without reading commit history.

- [FEAT-2026-0007/G2-LESSONS] A WU session that bills 0 input/output tokens has
  produced nothing — but the driver currently commits it as `done` because the
  WU frontmatter status flip is the only staged change, and the code gate passes
  on the unchanged codebase. T08H (a hygiene WU with three explicit safeguards)
  repeated T04's exact failure via this path: 0 tokens, 225 s elapsed, status
  flipped to done, no symbols written. Rule: the driver must treat a 0-token WU
  session as a failed attempt, not a completed one. Until the driver enforces
  this, plan-next WUs should add a sentinel AC: "events.jsonl must show
  `input_tokens > 0` for this WU; if it does not, re-dispatch from scratch."

- [FEAT-2026-0007/G2-LESSONS] Agent-side safeguards (smoke-import checks in AC,
  completeness escalation triggers) are bypassed when the agent session crashes
  or produces 0 tokens before reaching those checks. T08H carried AC 9 (explicit
  smoke-import check) and two escalation triggers — none fired because the session
  generated no output at all. The G1-LESSONS entries on smoke checks and
  completeness triggers remain necessary; they are not sufficient. Rule: for any
  WU that re-lands symbols that previously failed silently (a hygiene WU),
  include a plan-next note requesting a driver-side pre-dependency-unlock check:
  run the WU's declared smoke-import command from the Verification section before
  advancing the dependency frontier. Agent-side guards catch reasoning failures;
  driver-side checks catch session crashes.

- [FEAT-2026-0007/G2-LESSONS] A gate that introduces a new enforcement mechanism
  (budget brake, slot cap, rate limiter) cannot exercise that mechanism against
  itself — the GATE.md for the implementing gate is authored before the code
  lands, and setting a budget against a gate mid-flight is undefined. T07
  introduced `cost_budget_usd` and the brake was never fired in Gate 2 because
  GATE-02.md had no budget field. Rule: when a plan-next WU details a gate whose
  substantive WUs include a new enforcement mechanism, add a note to the gate
  review document: "set `cost_budget_usd` (or equivalent) in GATE-N+1.md before
  arming the next gate to exercise this mechanism for the first time." The
  implementing gate's own GATE.md is intentionally left without a budget; the
  first exercise belongs to the successor.

- [FEAT-2026-0008/G1-CLOSE] When a feature's whole purpose is to fix a failure
  mode the methodology itself enables (a hollow pass, a silent no-op, a
  trust-model gap), its close ceremony must run a recursive audit: did the
  guards this feature was built to add actually land, AND are they wired into
  the path they were meant to intercept? Defining the helpers is not enough —
  an unwired helper is a hollow pass with extra steps. Rule: the close WU for
  any methodology-fix feature must include a "Guard-helper existence audit"
  section that runs grep / ls against the named symbols AND a wiring check
  (`grep -n "<helper_name>(" <target_file>` returns a call site in the path the
  feature names, not only the definition). If either check fails, the verdict
  must NOT claim the goal is met and the WU must emit `status: blocked` —
  hollow-passing the close ceremony of an anti-hollow-pass feature is the
  worst-case recursive failure and the methodology must catch it.

- [driver/files_changed-guard] The `files_changed` guard's diff check must
  account for **untracked** files, not just tracked diffs. `git diff
  head_before -- <path>` returns 0 ("no diff") for a freshly-created file
  the agent just wrote, because `git diff` doesn't see untracked files.
  Without the fix, a WU that legitimately creates new deliverables (a new
  `.tf`, `.sh`, `.md`, etc.) spins to `blocked_human` with the message
  "RESULT block declared files_changed paths that show NO diff against
  HEAD before this attempt" — even though the file is present and correct
  on disk. Compounding factor: `git reset --hard head_before` between
  attempts only resets tracked content; the untracked file persists, the
  next attempt re-writes the same bytes, and the false positive recurs.
  Rule: guards that probe "did this attempt actually change X" against a
  git baseline must combine `git diff --quiet` with `git ls-files --others
  --exclude-standard` to catch added-untracked. Symptom seen 4× in
  FEAT-2026-0012 (T04, T08, G3-PLAN, T11); fix lives in
  `verify_files_changed`.

- [FEAT-2026-0002/G1-CLOSE] Per-WU coverage acceptance criteria must use a
  per-file threshold (`coverage report --include=<path> --fail-under=N`),
  not a TOTAL roll-up. A per-file threshold is falsifiable about the module
  the WU touched: it survives unrelated changes elsewhere in the tree,
  decouples module-level completion from TOTAL drift, and forces the WU
  spec to name the actual surface under test. FEAT-2026-0002's four
  per-module WUs (T01 loop.py ≥ 95%, T02 validate-event.py ≥ 90%,
  T03 lint_plan.py ≥ 90%, T04 _miniyaml.py ≥ 90%) each carried its own
  `--include=` AC; the floor-flip WU (T05) then satisfied the TOTAL claim
  as a derived consequence. Rule: when authoring a coverage WU that targets
  a specific module, the AC must read `coverage report --include=<file>
  --fail-under=N`, not `coverage report --fail-under=N`. A TOTAL-only AC
  can be silently satisfied by *other* modules' coverage and tells a
  reviewer nothing about whether the WU's named surface was actually
  exercised.

- [FEAT-2026-0002/G1-CLOSE] When raising a project's `--fail-under` coverage
  floor, enumerate every site that asserts the floor and flip them
  atomically in a single WU. Sites typically include
  `.specfuse/verification.yml` (the methodology's `code` gate command),
  `scripts/smoke-test.sh` (the local smoke runner the operator runs before
  push), and any CI-side coverage step (`.github/workflows/ci.yml` if it
  carries an inline `--fail-under` rather than delegating to the others).
  A flip in one without the others produces silent drift where one gate
  enforces the new floor and another still enforces the old; a re-arm that
  changes the test floor without changing the smoke floor (or vice versa)
  lets the gates disagree across attempts. Rule: the floor-flip WU spec
  must list every `--fail-under` site as a falsifiable AC (`grep -n
  "fail-under" <files>` returning `=N` for each), and the close-WU's
  recursive audit must include the same grep so an inconsistent flip
  blocks the close. FEAT-2026-0002 T05 flipped both
  `.specfuse/verification.yml` and `scripts/smoke-test.sh` in one commit;
  the close ceremony audited both.

- [FEAT-2026-0002/G1-CLOSE] When a WU's AC uses a real existing artifact as
  "regression on valid fixture" evidence, the author must verify the
  artifact's actual contract status against the script under test before
  dispatching — not after. T02's AC 4 originally read "assert
  `validate-event.py` accepts a real event line from FEAT-2026-0008's
  events.jsonl"; the agent identified that the orchestrator's schema rejects
  driver-emitted events, and attributed that rejection to the schema's
  `source` enum being the orchestrator protocol.
  The re-arm fix inverted the AC to "rejects this real event" — semantically
  the right boundary evidence, polarity corrected.

  > **Correction [FEAT-2026-0060/G1-CLOSE].** The parenthetical attribution
  > above was wrong, and being wrong is what made the gap look intentional
  > for four features. The vendored `specfuse/loop/data/schemas/event.schema.json`
  > in this repository has **no `source` enum at all** — `properties.source`
  > carries exactly `type`, `description`, `pattern`, and its description
  > explicitly names *"the loop's single-repo `driver`"* as a legitimate
  > emitter. The schema anticipated the driver; it merely lacked its
  > vocabulary. The only thing rejecting driver events was the closed 28-entry
  > `event_type` enum. Read as "by design", that misattribution licensed
  > `loop.py`'s own comment to cite the gap as *precedent to follow*, and four
  > more unsanctioned types accumulated before FEAT-2026-0060 measured it at
  > 359 of 1043 corpus events (34%). Meta-rule: a lesson that explains **why a
  > tool rejects an artifact** must name the schema construct doing the
  > rejecting and be re-checked against the vendored file before it is cited,
  > because a wrong *reason* attached to a right *observation* is the most
  > durable kind of wrong — the observation keeps confirming it.

  Rule: every AC of the
  form "tool X accepts/rejects existing artifact Y" must include, in the
  WU's Context section, the contract claim that justifies the polarity
  (e.g., "Y's `source` field is in X's enum, therefore X accepts Y"). If
  the author cannot state the justifying contract, the AC is a guess and
  must be verified by running the tool on the artifact at author-time, not
  defer that verification to the agent's first attempt.

- [FEAT-2026-0002/G1-CLOSE/driver-incident] Bookkeeping commits the
  driver writes (`commit_bookkeeping` in `loop.py`) must force-add
  through `.gitignore` because some paths the driver intends to commit
  live under user-configured ignore prefixes — specifically
  `.specfuse/<feature>/work/<wu>/attempt-N.md`, persisted by the
  spinning-escalation path for human review while `.gitignore` declares
  `.specfuse/**/work/` as scratch (the rule landed alongside
  FEAT-2026-0004's lock-file ignore work). Without `git add -f`,
  `git add` returns exit 1 and the driver crashes with partially-flipped
  state on disk (WU frontmatter + `events.jsonl` append written, no
  commit). Force-add is safe for this function only because its caller
  is always the driver itself and curates the path list to driver-managed
  state; it is NOT a general license to bypass ignore rules elsewhere.
  Surfaced in FEAT-2026-0002/T03's first dispatch (3-attempt spin);
  driver fix in commit `17319cb` / cherry-pick `bf2fd16`. Rule: any
  driver helper that commits a curated, driver-owned path list must
  `git add -f` and must NOT be reused for paths that come from the
  agent, RESULT block, or user input.

- [FEAT-2026-0014/T01/driver-wipes-uncommitted] The driver's per-attempt
  `git reset --hard head_before` (between failed dispatches) WIPES any
  tracked-file modifications that aren't committed at the moment the
  driver runs, INCLUDING uncommitted edits to driver source
  (`.specfuse/scripts/loop.py`), other features' WU specs, or
  `.specfuse/LEARNINGS.md`. Untracked files survive (because `reset
  --hard` only touches tracked files), but a tracked file modified in
  the working tree and not yet committed disappears on the first WU
  block. Surfaced 2026-06-11 during FEAT-2026-0014/T01 cycles: a session
  authored loop.py improvements + a WU rewrite + LEARNINGS appends, did
  not commit, ran the loop on the same feature, and the driver reset
  wiped all three. Rule for operators: BEFORE running `python3
  .specfuse/scripts/loop.py` against an active feature, commit
  EVERYTHING tracked-but-uncommitted under `.specfuse/` (and anywhere
  else you've touched) — or move work to a non-tracked path. Rule for
  driver authors: consider extending the head_before reset to preserve
  files outside the active feature's folder (an allowlist of paths the
  agent is explicitly authorized to touch); current behavior is
  documented as a gotcha until that lands.

- [FEAT-2026-0014/T01/gh-claudeP-broken] `gh auth status` fails inside
  the dispatched `claude -p` subprocess even when the same `GH_TOKEN`
  succeeds via the operator's shell `gh` AND via shell `curl
  https://api.github.com/user`. Crucially the failure persists when
  claude -p is invoked with `--dangerously-skip-permissions` — so it
  is NOT the claude-p sandbox and the WU-level `unsandboxed: true`
  escape hatch does NOT fix it. Token is valid; gh's local state knows
  the account ("Active account: true" still prints); the API
  verification call inside claude-p returns "X Failed to log in to
  github.com using token (GH_TOKEN)". Root cause lives in the
  `gh`-binary ↔ claude-p subprocess interaction, unidentified as of
  2026-06-11. Reproducible from any shell: `gh auth status` ✓ + `curl
  -H "Authorization: token $GH_TOKEN" https://api.github.com/user` ✓,
  but `echo "Run \`gh auth status\` and dump raw output between
  MARK_BEGIN and MARK_END" | claude -p` (with or without
  `--dangerously-skip-permissions`) shows `X Failed`. Rule for WU
  authoring: any AC or escalation trigger that invokes `gh` from the
  dispatched agent's bash MUST NOT be written today. Instead choose
  one of: (a) operator-manual verification post-merge, recorded as a
  named step in `RETROSPECTIVE.md`; (b) replace `gh` with shell-side
  preflight + a simpler agent AC (operator runs `gh auth status`
  outside the loop, agent only edits the file); (c) `curl` with
  `$GH_TOKEN` from inside the agent — note the agent's safety filter
  may refuse curl with `Authorization` headers, so this path is
  unproven and requires its own probe at WU author time. Audit the
  unsandboxed escape hatch as INSUFFICIENT for this surface; the flag
  is still useful for other surfaces but is not a generic "make
  external CLIs work" lever.

- [FEAT-2026-0014/T01/preflight-must-dump-raw] When a preflight or
  diagnostic asks a `claude -p` session to classify the result of an
  external command ("output VALID or INVALID"), the model can emit
  either word without running the command, and the script gets a
  false positive. Rule: every probe that aims to verify an external
  tool's behavior must demand the *raw stdout+stderr* be dumped
  between unforgeable BEGIN/END markers and then grep the dumped
  text for a signature only the real tool emits (e.g. `gh auth
  status` prints `Logged in to github.com` on success; `curl /user`
  prints `"login":` on success). Apply to any future preflight or
  diagnostic skill that consults a `claude -p` session for ground
  truth: never trust agent classification when raw output exists.

- [FEAT-2026-0014/T01/unsandboxed-opt-in] The driver supports per-WU
  sandbox-escape via WU frontmatter `unsandboxed: true` +
  `unsandboxed_rationale: "<one-line>"`. The driver REFUSES to
  dispatch if `unsandboxed: true` without rationale (the rationale
  IS the audit signal). The driver emits an `unsandboxed_dispatch`
  event in events.jsonl BEFORE each attempt and prints a `⚠
  UNSANDBOXED dispatch` console line. Implemented in
  `.specfuse/scripts/loop.py::load_wu` (validation) and
  `loop.py::dispatch` (flag injection) and the attempt loop
  (event + console). The `/unblock-wu` skill offers re-arm-
  unsandboxed as an explicit per-WU decision; recovery-time
  escalation only — at planning time, prefer (a) operator-manual
  verification or (b) AC redesign when the trigger surface is a
  CLI's auth round-trip (see gh-claudeP-broken above). Sandbox-
  escape is NOT a substitute for AC redesign when the surface is
  broken upstream.

- [FEAT-2026-0013/G1-CLOSE] Test fixtures that combine `subprocess.run`
  (especially `git`) with `tempfile.TemporaryDirectory` on Python 3.12
  race against `shutil.rmtree` on cleanup. Two specific causes, both
  must be addressed together: (1) git's `gc.autoDetach` (default true
  since git 2.0) means any `git commit` / `git gc --auto` background-
  detaches a gc subprocess that outlives the parent and is still
  writing to `.git/objects` when `TemporaryDirectory.cleanup()` fires;
  (2) the index lock and other writers may not have flushed when the
  parent exits. Symptom: `OSError: [Errno 39] Directory not empty:
  '/tmp/.../.git/objects'`, intermittent, timing-dependent — three
  occurrences across different tests in this repo before fix. Rule:
  any test fixture that initializes a temp git repo inside a
  `TemporaryDirectory` MUST (a) pass `-c gc.auto=0` to every `git`
  invocation inside the fixture body (or `git -C <root> config gc.auto
  0` after `git init`), AND (b) run a sync barrier — `subprocess.run(
  ["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
  capture_output=True)` — in a `finally:` block after the `yield`,
  before the `TemporaryDirectory` context exits. Either alone is
  insufficient; both close the race deterministically. Belt-and-
  suspenders `ignore_cleanup_errors=True` is explicitly rejected — it
  hides future leaks and erodes verification-as-oracle.

- [FEAT-2026-0013/G1-CLOSE] An oracle of the form
  `unittest -q 2>&1 | tail -1` is fragile when the tests-under-test
  spawn subprocesses whose stdout is forwarded to the parent — that
  subprocess output can arrive AFTER unittest's `OK` / `FAILED`
  summary line, and `tail -1` will quietly start returning chatter
  instead of the verdict. The drift is silent: the oracle's output
  changes shape but the underlying tests are still passing (or
  failing) for the same reasons. T01's AC4 and G1-CLOSE's AC2 both
  used this oracle; both produced one-distinct-line output on this
  close run, but the line was driver chatter from an inner
  integration test, not `OK`. Rule: when an AC's oracle is "are
  N runs of a test suite all clean," prefer an exit-code count
  (`for i in $(seq 1 N); do unittest -q >/dev/null 2>&1; [ $? -eq 0
  ] && pass=$((pass+1)) || fail=$((fail+1)); done; echo "PASS:$pass
  FAIL:$fail"`) over a `tail -1 | sort | uniq -c` pattern. The exit
  code IS the verdict; stdout-tail is a proxy that decouples from the
  verdict the first time a downstream test starts logging. Apply at
  WU author time for any "run-N-times" AC.

- [FEAT-2026-0013/G1-CLOSE] **Amends and supersedes v1's gc.auto=0 +
  sync-barrier rule above (entry dated v1, line 618).** Test fixtures
  that combine `subprocess.run` (especially `git`) with
  `tempfile.TemporaryDirectory` on Python 3.12 race against
  `shutil.rmtree` on cleanup. v1's rule (a) gc.auto=0 + (b) sync
  barrier is necessary but proved INSUFFICIENT on Linux ext4 CI
  runners: FEAT-2026-0013 v1 shipped with both fixes, passed 50×
  macOS-local, and the SAME `OSError: Directory not empty` race fired
  on Linux runner `27412918877` (PR #9). Linux ext4 surfaces a
  cleanup race that macOS APFS hides. Rule (revised): any test
  fixture that initializes a temp git repo inside a
  `TemporaryDirectory` MUST do all three: (a) pass `-c gc.auto=0` to
  every `git` invocation in the fixture body (or `git -C <root>
  config gc.auto 0` after `git init`); (b) run a sync barrier —
  `subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
  check=True, capture_output=True)` — in a `finally:` block after
  the `yield`, before the `TemporaryDirectory` context exits; (c)
  construct the `TemporaryDirectory` with `ignore_cleanup_errors=True`
  (Python 3.10+) as belt-and-suspenders against Linux-only surfaces
  the gc + sync barrier doesn't cover. The v1 stance that
  `ignore_cleanup_errors=True` "hides future leaks and erodes
  verification-as-oracle" is REVERSED: when the root cause is being
  attacked AT THE SAME TIME (a)+(b), the suppression is
  harm-reduction, not symptom-only. Three together close the race
  deterministically on Linux CI; root-cause AND suppression, not
  either-or.

- [FEAT-2026-0013/G1-CLOSE] Oracle environment must match goal
  environment. A `roadmap_goal` of "deterministic on Python 3.12 CI
  runners" cannot be falsified by a 50× macOS-local audit — macOS
  APFS and Linux ext4 differ on whether in-flight directory writes
  race against `rmtree`, and the CI environment is the only place
  the goal's environment lives. v1's close ceremony reported the
  goal met on macOS-local evidence alone; the same fix failed on
  the very next CI run. Rule: when authoring a close-ceremony AC
  whose oracle is "run the failing test N times", the oracle command
  MUST be runnable in (or equivalent to) the environment named by
  `roadmap_goal`. For Linux-CI goals: add a Docker probe
  (`scripts/check-linux-race.sh` shape — Linux image, identical
  `tail` of the suite) and treat the operator-side probe run as the
  load-bearing AC, with macOS-local audit kept only as a necessary-
  but-not-sufficient pre-check. The verdict must explicitly call
  out the operator-side step and the CI run as the FINAL oracle.

- [FEAT-2026-0013/G1-CLOSE] Script-parity ≠ environment-parity. A
  pre-push hook (or any locally-runnable script) that REPRODUCES
  CI's commands verbatim does NOT reproduce CI's environment — it
  still runs on the developer's filesystem, kernel, and tempdir
  semantics. A race that is non-deterministic on macOS and
  deterministic on Linux ext4 will not surface in a pre-push hook
  on a Mac no matter how faithfully the hook mirrors the CI YAML.
  Rule: any pre-push gate intended to catch CI-environment-only
  failures (filesystem races, kernel-version-specific syscalls,
  glibc-vs-musl behavior, container runtime semantics) MUST run
  inside a container that matches CI's image. Document the
  distinction at the gate's spec-author time so future amendments
  do not collapse "we run the same commands" with "we run in the
  same environment." Pre-push hooks running on developer machines
  cannot catch races that are deterministic-on-CI; only a
  Docker-probe or equivalent environment-parity gate can.

- [FEAT-2026-0013/G1-CLOSE] Centralize-or-enumerate cross-cutting
  fixture patterns BEFORE the first fix-shape is dispatched. When a
  test fixture pattern (an `integration_workspace`, a `_minimal_git_
  repo`, a tempdir-backed harness) is duplicated across multiple test
  files via copy-paste, fixing one site does not generalize — the
  same race / leak / config-gap can fire from any of the other sites
  on the next CI run, in a DIFFERENT test name. FEAT-2026-0013's v1
  shipped a fix to `tests/test_driver_integration.py::
  integration_workspace`, passed 50× macOS-local + 50× Linux Docker,
  and the SAME race fired in `tests/test_loop_files_changed_guard.py
  ::integration_workspace` on Linux CI (v2 attempt). The repo has
  FIVE copies of `def integration_workspace()` plus ~50 bare
  `tempfile.TemporaryDirectory()` call sites. Rule: when an
  implementation WU author identifies a fixture-level race or leak,
  the WU spec MUST include a discovery AC: `grep -rn "def
  <fixture_name>" tests/` (or equivalent for the pattern at hand)
  and enumerate every site in the WU spec by file + line number.
  The fix-shape is correct only when applied to every enumerated
  site — typically by centralizing into one shared helper and
  replacing duplicate definitions with imports. Single-site fixes
  on cross-cutting patterns are a structural under-discovery, not a
  bounded scope. Cost of missing this on FEAT-2026-0013: two ship-
  and-CI-re-fail cycles + a re-arm cycle = ~$5 in agent costs and
  three days of methodology rounds.

- [FEAT-2026-0013/G1-CLOSE] Global git config can ambush WU
  dispatch. A developer machine carrying `commit.gpgsign=true` +
  `gpg.format=ssh` GLOBALLY (the default for some setups) will
  fail any `git commit` inside a dispatched agent session when no
  ssh-agent is reachable in the session's environment. The failure
  surfaces as `gpg failed to sign the data` / exit 128 inside any
  test fixture that runs `git commit`, including
  `_minimal_git_repo()` helpers. The agent — correctly — emits
  `status: blocked` rather than scope-creep into the test file,
  burning a dispatch cycle. Recovery is an operator-side
  `git config --local commit.gpgsign false` (working-copy only;
  preserves the global setting for the operator's own commits).
  FEAT-2026-0013 v3-attempts-1 and 2 burned $4.70 / 2552s on this
  block before the operator disabled it locally. Rule: every WU
  spec that requires `git commit` inside a temp-repo test fixture
  MUST also (a) set `commit.gpgSign=false` on the temp repo
  (`git -C <root> config commit.gpgSign false` right after
  `git init`), AND (b) document in the feature folder's PLAN.md or
  RETROSPECTIVE.md that the operator must verify
  `git config --get commit.gpgsign` returns `false` or empty in
  the repo's working copy BEFORE the first dispatch. The skill-side
  remedy is to extend `init.sh` or `/wrap-feature` with a preflight
  check on the operator's global gpg config; until that lands, this
  is a known dispatch-time foot-gun.

- [FEAT-2026-0013/G1-CLOSE] FEAT-2026-0008's `files_changed` diff
  guard is recursively validated. During FEAT-2026-0013 v3-attempt-3
  attempt-1, the dispatched agent emitted `status: complete` with
  `files_changed: ["tests/_workspace.py", ...]` but did not write
  `tests/_workspace.py` (the new file at the center of the v3 fix).
  The FEAT-2026-0008/T02 `verify_files_changed` guard caught the
  unchanged path (`attempt_outcome: files_changed_mismatch` in
  `events.jsonl`), rolled the squash back via
  `git reset --hard head_before`, and re-dispatched. Attempt-2
  wrote the file correctly and completed. Without the guard, the
  driver would have committed only the WU frontmatter status flip,
  `status: done` would have advanced the dependency frontier, and
  the gate would have closed against a missing file. This is the
  same failure mode FEAT-2026-0007's T04/T08H/T08 hit before
  FEAT-2026-0008 landed; the guard now closes it. Rule (durable,
  observational): the value of driver-side completeness guards is
  proven across multiple feature shipments; agent-side ACs and
  spec-side completeness triggers are necessary but the driver-side
  guard is the load-bearing safety net. Catalog this incident as
  the second live recursive validation of FEAT-2026-0008 (after
  FEAT-2026-0008's own close ceremony's audit-of-itself); use it
  when justifying analogous driver-side guards on other surfaces
  (e.g. FEAT-2026-0012's planned closing-deliverable guard).

- [FEAT-2026-0010/G1] Name load-bearing strings once in the
  foundation WU and reference them as exact-match literals in every
  dependent WU. FEAT-2026-0010/T01 specified the exact anchor string
  and back-link string for the archive format; T02 and T04 consumed
  those strings without drift, producing byte-reproducible output
  across the dependent chain. The pattern is reliable because it
  eliminates the "reasonable-but-different" synonym a later agent
  would otherwise invent. Rule: for any WU that introduces a string
  that a later WU must match (section headings, anchor IDs, back-link
  templates, CLI flag names), quote the exact target string in the
  foundation WU's Acceptance criteria and repeat it verbatim in each
  dependent WU's Context section — do not leave the dependent WU to
  infer it from the diff.

- [FEAT-2026-0010/G1] Interactive skill WUs that ship an `--auto`
  batch mode must state explicitly in their Context section whether
  downstream dogfood WUs in the same gate are expected to
  subprocess-invoke the skill or re-implement its algorithm by direct
  file editing. FEAT-2026-0010/T02 shipped the `roadmap-archive`
  skill with `--auto`; T04 re-implemented the algorithm directly (no
  subprocess call) and produced correct output — but the contract was
  implicit. An agent dispatched after T02 with no such note may
  choose either approach; subprocess-invoke and direct-edit produce
  the same result only when the skill has no side-effects on unrelated
  rows (which is a non-trivial property to verify at WU author time).
  Rule: every skill WU that ships a batch mode must include a
  "downstream use" note in Context naming which of the two patterns
  the next WU should follow and why.

- [FEAT-2026-0010/G1] A gate-close assertion that event count in
  `events.jsonl` equals the gate's WU count must run before the
  driver marks a gate `passed`. FEAT-2026-0010/T02 completed and had
  its WU frontmatter updated correctly, but no `task_started` /
  `task_completed` events were appended; the retro WU (T90) could not
  reconstruct T02's wall-clock span from the log and could only
  estimate cost from WU frontmatter. Missing events are detectable
  only by cross-referencing frontmatter against `events.jsonl` — a
  fragile, retro-only check. Rule: when authoring a gate-plan or
  driver feature, add a gate-close pre-condition: `assert len([e for e
  in events if e["feature_id"] == gate_id]) >= expected_wu_count`
  (or equivalent grep on `events.jsonl`); if the count is short,
  block gate advancement and surface the gap for operator review
  before the gate is marked passed.

- [FEAT-2026-0010/G2] For regex-heavy row-mutation WUs — where the
  agent must compute byte-offset or capture-group index arithmetic
  against a match object to locate and rewrite a specific cell — a
  concrete before/after fixture in the WU spec reduces first-attempt
  failure rate. T05 required 2 attempts; the most likely cause was
  off-by-one arithmetic in the Detail-cell update step. Rule: any WU
  spec that requires an agent to (a) match a structured text row via
  regex and (b) mutate a specific field within that row must include
  an exact before/after example showing the raw bytes of the row
  before the mutation and the expected bytes after. "Apply the
  Conventions section's format" is insufficient — show the
  transformation, not just the format.

- [FEAT-2026-0010/G2] A helper function that is fully test-validated
  but not yet exercised in production (e.g., T05's idempotency path
  in `auto_archive_feature`) must be flagged explicitly in the
  plan-next WU so the feature-close checklist includes a smoke-test
  at real completion time. Test coverage cannot substitute for
  production exercise when the path depends on the exact byte content
  of files written by other tools (e.g., `commit_bookkeeping`,
  `wrap-feature`). Rule: when a WU's retro notes that a code path was
  tested but not yet production-exercised, the plan-next WU for that
  gate must add a named checklist item: "smoke-test [path/function]
  at feature-close by triggering the production condition and
  confirming the return value matches the test fixture." Omitting this
  step leaves a class of silent failures (wrong byte sentinel,
  column-format mismatch) undetected until the next feature exercises
  the path in production.

- [FEAT-2026-0010/G2] When a driver-side helper must replicate the
  logic of an existing skill (e.g., `auto_archive_feature` in
  `loop.py` replicating `roadmap-archive`), the correct implementation
  pattern is to re-implement the algorithm directly in Python, NOT to
  subprocess-invoke the skill file. The pattern was established in T04
  (file-editing WU) and confirmed in T05 (driver hook): subprocess
  invocation is brittle in the driver's execution context (path
  assumptions, working-directory state, no clean stderr capture) while
  direct re-implementation is pure-function, unit-testable, and has no
  external dependencies. This pattern is now a settled decision for
  this codebase. Rule: when authoring a WU that adds a driver-side
  hook replicating skill behavior, state in the Context section: "use
  direct Python re-implementation, not subprocess invocation" and name
  the skill's algorithm steps the re-implementation must match
  verbatim. Do not leave the choice implicit; an agent without this
  note may choose subprocess invocation as the "DRY" option.

- [FEAT-2026-0015/G1] The §10 helper-duplication escalation trigger
  must be authored with the target file's specific coupling surfaces in
  mind, not just the obvious symbol names. FEAT-2026-0015/T02's §10
  grep checked `CLOSING_SEQUENCE|_CLOSING_TYPES` but omitted
  `CORRELATION_ID_RE` — a separate constant in the same file that
  encodes overlapping knowledge about the closing-type lexicon. The
  omission caused a silent divergence that T03's first attempt surfaced
  as a blocking failure. Rule: before authoring a §10 escalation
  trigger, enumerate every site in the target file that encodes
  overlapping knowledge about the new symbol (type registries, regexes,
  schema constants, enum members, doc examples) and include a grep
  pattern for each. A §10 trigger that only checks the most obvious
  coupling point is incomplete; the correct test is "is there ANY other
  location in the file — or in the files that import it — that must
  mirror this change?"

- [FEAT-2026-0015/G1] A WU re-armed after a hygiene-WU resolves its
  blocking condition may silently produce zero file changes on its
  first re-dispatch attempt — even though the hygiene fix is committed
  and the blocking pre-condition is gone. FEAT-2026-0015/T03 exited
  `files_changed_mismatch` on the second dispatch's first attempt
  (all four expected paths unchanged) despite T02H having landed. The
  plausible cause is cached tool-call state from the prior blocked
  session, which prevented the re-armed agent from perceiving the
  hygiene changes as "new context requiring action." No driver-level
  mitigation exists as of this writing. Rule: when arming a WU that
  was previously blocked by a missing pre-condition (now resolved via
  a hygiene WU), add a note to the arm-gate review: "first attempt
  may exit `files_changed_mismatch`; if so, re-dispatch unmodified —
  the second attempt will perceive the post-hygiene state correctly."
  Account for this extra dispatch in the WU's planned cost.

- [FEAT-2026-0015/G1] `low` effort ($0.50 planned cost) is
  systematically undersized for WUs that touch three or more files
  when any of those files carry documentation coupling (a prose rule
  that must stay consistent with a code constant, a template whose
  prose must agree with a linter, a skill whose examples must reflect
  the current valid-type set). FEAT-2026-0015/T03 was classified
  `low` and planned at $0.50; it touched four files (two templates,
  one skill, one test file) and ran $1.53 on its productive dispatch
  alone — 3× plan. T02H was classified `low` and ran $0.98 across two
  attempts against a $0.50 plan, driven by the surrounding regex
  correctness surface and documentation coupling in `correlation-
  ids.md`. Rule: classify a WU as `medium` ($0.80–$1.00 planned cost)
  when it touches three or more files OR when any touched file has
  documentation coupling. Reserve `low` for WUs that touch exactly
  one or two files with no prose-consistency obligation. Pure-additive
  dict extension in a single file (T01's profile: one driver file,
  three dict entries, four tests) is the canonical `low`/`medium`
  boundary case; T01 completed at $0.42 on a $1.00 medium plan,
  suggesting `low` is appropriate there — but only for that pattern.

- [FEAT-2026-0015/G1] When a WU modifies a scaffold template (e.g.,
  `PLAN.template.md`, `WU.template.md`), the gate must include a test
  that renders the template (or a representative excerpt) and runs the
  downstream linter against the rendered output. Verifying that the
  template file itself is well-formed is insufficient — the gate's
  oracle must be "lint passes on a PLAN.md produced from this
  template." FEAT-2026-0015/T03 introduced
  `tests/test_template_closing_shapes.py` for exactly this: it
  constructs minimal closing-WU sequences from the template shapes and
  asserts `lint_plan.py` accepts them. This extends the existing prose-
  artifact rule ([FEAT-2026-0003/G2-LESSONS]) specifically to
  templates: the structural linter that counts required sections must
  run on a RENDERED instance, not on the raw template text (which may
  pass naive section-count checks while producing linter-rejecting
  output when instantiated). Rule: any WU that edits a scaffold
  template file must declare, in its Verification section, the command
  that (a) instantiates the template into a minimal artifact and (b)
  runs the downstream linter on that artifact. A test file exercising
  this path is the preferred form; a Makefile or inline shell command
  is acceptable when a test file is out of scope.

- [FEAT-2026-0015/G2-CLOSE] Planned-cost estimation for WUs that touch
  the driver core (`loop.py`) is systematically half the actual cost
  at the current model mix (Sonnet 4.6 + Opus 4.7). Gate 2's five
  substantive WUs ran 106–194% over plan; the gate subtotal ran 147%
  over plan ($14.84 actual vs $6.00 planned). The pattern is
  uniform across all five WUs, not driven by outliers. Rule: when a
  WU is `implementation` type AND touches `.specfuse/scripts/loop.py`
  (or `lint_plan.py`), set the planned-cost floor at:
  `low → $1.50`, `medium → $2.50`, `high → $4.00`. Use the existing
  `low/medium/high` effort taxonomy but with these driver-core
  floors. Outside `loop.py` / `lint_plan.py`, the prior floors
  ([FEAT-2026-0015/G1]) still apply. Two-gate evidence (Gate 1 +68%,
  Gate 2 +147%) — this is no longer noise.

- [FEAT-2026-0015/G2-CLOSE] Type-keyed assertion tables
  (`dict[str, list[Callable]]`) are the right shape for a guard whose
  required deliverables differ by WU subtype. T07 landed
  `CLOSING_ASSERTIONS_BY_TYPE` with three keys (`close`,
  `close-intermediate`, `plan-next`), each carrying a per-subtype
  assertion list (5/3/2 respectively). The shape lets a new subtype be
  added without touching existing entries — additive-only — and lets
  each assertion be tested in isolation. Compare to a single-callable
  guard (`assert_closing_deliverables` as one giant if-chain): the
  if-chain forces shared early-return logic and makes per-subtype
  testing harder. Rule: when a driver guard must enforce
  context-dependent deliverables (different per WU type, per gate,
  per language), prefer a type-keyed dispatch table over inline
  branching. Each table entry is a unit-testable assertion; the
  dispatcher is a one-line `assertions = TABLE.get(wu.type, [])`
  lookup.

- [FEAT-2026-0015/G2-CLOSE] Lint surfaces introduced into a
  populated codebase should default to WARN (not ERROR) until a
  backfill sweep runs against existing artifacts. T05's `oracle_env`
  lint surface defaults to WARN because every WU authored before
  this feature pre-dates the field; an ERROR-only default would have
  spuriously blocked every legacy feature on its first re-lint. T08
  applied the same WARN-first stance to `planned_cost_usd`. Rule:
  when adding a new required field via lint, the rollout shape is
  (1) WARN-only for one feature cycle to confirm the field is being
  set in new authoring, (2) backfill sweep across legacy artifacts
  (single hygiene WU), (3) WARN → ERROR flip in a follow-on feature.
  Skipping step 1 and going ERROR-on-first-ship is a known
  spurious-block pattern.

- [FEAT-2026-0015/G2-CLOSE] When a planning artifact (PLAN.md's
  `## Planned-cost table`) and a per-unit frontmatter field
  (`WU.frontmatter.planned_cost_usd`) carry overlapping numeric
  knowledge, the two go stale the moment one is revised without the
  other. T08's WU frontmatter says `planned_cost_usd: 0.80` while
  PLAN.md's table row says `0.50` — both refer to the same WU.
  Neither is wrong; the WU was upgraded from `low` to `medium` after
  the table was drafted, and the table didn't track. Rule: designate
  ONE source as authoritative and have the other read from it. For
  this codebase the per-WU frontmatter is authoritative (set at draft
  time, revisable per-WU during planning); PLAN.md's table should be
  generated from the frontmatter or carry a stale-warning comment.
  Until the generation lands, treat WU frontmatter as the value the
  cost-analysis section quotes, with a footnote on any discrepancy.

- [FEAT-2026-0015/G2-CLOSE] The recursive-dogfood close ceremony
  pattern from [FEAT-2026-0008/G1-CLOSE] is now validated on a
  multi-gate feature whose terminal close is the FIRST production
  exercise of the new contract it shipped. This WU (G2-CLOSE) used
  `type: close` (new), wrote `verdict: met` (new field), produced a
  `## Cost analysis` section (new assertion target), and was
  exercised by T07's guard (new code) against its own commit. All six
  AC7 recursive grep checks passed. The pattern works: a methodology
  feature whose terminal close uses the methodology's own new shape
  is the load-bearing test that the contract is sound. Rule
  (reinforcing [FEAT-2026-0008/G1-CLOSE]): any future feature whose
  scope is "ship a new close-ceremony contract" MUST close its own
  terminal gate using that contract. Falling back to the previous
  contract "to be safe" invalidates the feature's central claim.

## FEAT-2026-0017/G1-CLOSE — close-WU hollow-pass surfaces compound

- **Verify-gate cannot catch impl-WU hollow-pass on its own.**
  Sonnet 4.6 hollow-passed FEAT-2026-0017/T01 three times by
  modifying only the WU frontmatter; tests passed because they
  ran against unchanged code. The existence-check discipline
  (authoring-work-units §9) caught it ONLY at the next close-WU
  layer. Rule: any implementation WU that declares
  `produces_driver_helper: <symbol>` should have a driver-side
  post-impl existence guard, not only a close-WU existence
  check. Until then, escalate driver-wiring impl-WUs to Opus
  4.7 by default — Sonnet's hollow-pass rate on this shape is
  high.

- **`assert_closing_deliverables` diff-only-touches-wu bypass
  was a silent hollow-pass loophole.** Added "for test fixture
  convenience" but no test actually depended on it. Real
  close-WU runs could pass with zero substantive output (only
  the driver's bookkeeping write in the squash diff). Removed
  in commit `6084a89` with regression test
  `test_close_fails_when_diff_only_touches_wu_file`. Rule:
  every "skip-assertions-on-trivial-diff" shortcut in the
  driver is a hollow-pass loophole until proven otherwise; any
  future addition needs an existing test that depends on it
  AND a paired test asserting it doesn't bypass real runs.

- **Methodology-level guard contracts must be cross-checked at
  feature plan time.** FEAT-2026-0015 added T06 (driver owns
  roadmap flip — close WU MUST NOT touch roadmap.md) and T07
  (close-deliverable guard REQUIRES docs/ or roadmap.md in
  squash) in the same feature. They contradict each other.
  Lint did not catch this. The first feature to actually
  exercise the post-T06 close-contract (FEAT-2026-0017)
  surfaced it. Rule: when a feature adds or changes a guard
  contract, the planning phase must include a "does any other
  guard contract this contradicts?" review step — ideally
  enforced by lint.

- **Operator's global git config can silently break tempdir-git
  tests across the whole repo.** Global `commit.gpgsign=true`
  with SSH signing → tempdir subprocesses fail `git commit -m
  init` with exit 128 because ssh-agent isn't reachable. Two
  test files (`test_loop_files_changed_guard.py`,
  `test_loop_orchestration.py`) had `_init_git` helpers that
  omitted the `git config commit.gpgSign false` pattern used by
  `tests/_workspace.py:36` and others. Reproduced on `main`.
  Fixed in commit `36cd193`. Rule: every tempdir-git test
  helper MUST run `git config commit.gpgSign false` after `git
  init`. Worth a lint check on tempdir-git patterns in tests.

- **The driver's `commit_bookkeeping` step is itself subject to
  the same signing flake.** During FEAT-2026-0017/T01 cycle 2,
  after the spinning-escalation, the driver tried to commit
  the blocked-status marker and crashed with the same exit 128
  signing failure — losing the audit trail commit. Rule: every
  driver `git commit` call site is a hidden subprocess-signing
  failure mode; the driver should detect signing is enabled and
  warn (or set `commit.gpgsign=false` for its own commits).

- **Opus 4.7 has a verdict-flip blind-spot for close-WUs.**
  Three consecutive attempts of FEAT-2026-0017/G1-CLOSE
  produced the bulky deliverables (RETROSPECTIVE.md, LEARNINGS
  append) every time but consistently failed to flip the
  one-line `verdict: not_set` frontmatter field, even with
  explicit retry feedback ("verdict 'not_set' absent or not in
  VERDICT_VALUES"). Likely cause: WU-body's "set verdict ONLY
  when X AND Y AND Z confirmed" caution overrides the terse
  retry signal; model stays neutral rather than commit.
  Workaround: operator finishes manually. Rule (provisional,
  needs deep-analysis): close-WU bodies should not
  over-condition the verdict-flip directive; consider promoting
  verdict-flip to a separate single-instruction step OR
  auto-deriving verdict from the RETROSPECTIVE.md's
  "Feature-arc verdict" section content. Tagged for
  deep-analysis session.

- **Uncommitted re-arm edits get reset.** Operator's first
  re-arm of T01 (status: blocked_human → pending) was not
  committed; the driver's `reset_preserving_events` on the
  next failed attempt wiped the re-arm via `git reset --hard
  head_before`. Cost: a full dispatch cycle that reproduced
  the original hollow-pass state. Rule: every operator-side
  re-arm via `/unblock-wu` (or manual frontmatter edit) MUST
  commit before re-dispatch. Worth building into the
  `/unblock-wu` skill as a mandatory step.

- **Full-feature cost can run 10× over plan when dogfood
  surfaces compound bugs.** FEAT-2026-0017 planned cost $3.20;
  actual $39.37 (12.3× overrun). All overspend on cycles where
  agent worked correctly but verify-gates failed for reasons
  outside WU stated scope (pre-existing repo bugs surfaced by
  the new feature's surface). Rule: planning-phase cost
  estimates should include a "first-of-its-kind dogfood
  multiplier" (typical 5-15×) when the feature introduces a new
  contract no prior feature has exercised end-to-end.

- **[FEAT-2026-0018/G1-CLOSE-INTERMEDIATE] Effort-band pricing is
  blind to spec density and history-as-fixture reads.** Gate 1
  overran +132% ($4.10 plan → $9.51 actual) across three WUs
  whose plans used the standard effort-band defaults
  (`implementation/high` → $1.50–1.80, `implementation/medium`
  → $0.80). T02 (tests) shipped 15 named test classes + 12
  lint-clean synthetic fixture directories on a single attempt
  for $4.18 — 92k output tokens, 2.79× plan. T03 (CLI +
  calibration) read 4 historical feature folders as fixtures
  in a single attempt — 5.3M cache-read tokens, 3.09× plan.
  T01's retry cost on a small-delta cycle was nearly equal to
  its first attempt (~$1.29 vs $1.56) because cache-reload on
  re-dispatch dominates the bill, so "attempt-2 << attempt-1"
  cost models are wrong. Rule: when planning a WU, raise the
  effort-band default by the spec-density inputs the band does
  not see — count named test classes / fixture directories /
  history-folder reads in the AC body and add a per-unit
  surcharge (rough heuristic: +$0.10 per named test class above
  5, +$0.10 per lint-clean fixture directory, +$0.20 per
  historical-feature-folder read). Treat re-dispatch cost as
  full-cycle cost, not delta cost, when budgeting attempts.

- **[FEAT-2026-0018/G2-CLOSE-INTERMEDIATE] Effort bands do not see
  wiring-site count; price multi-site driver-wiring per site.**
  Gate 2's three driver-wiring WUs split clean on the site axis:
  T05 wired ONE new site backed by T04's already-paid-for
  scaffolding and came in at 1.21× plan (`xhigh` $2.20). T04
  wired one site PLUS the FEAT-2026-0017 ordering invariant
  (stub-retro before `fire_terminal_flips`; post-flip
  `assert_terminal_flips_fired` must hold) and came in at 1.64×
  plan ($4.10). T06 was priced as `medium` ($0.80) but actually
  hooked into BOTH wiring sites T04 and T05 introduced, added a
  PLAN.md frontmatter field, defined precedence ordering between
  the CLI flag and the frontmatter, and shipped tests for each —
  same single-site-pricing-of-multi-site-work shape as gate 1's
  T02 (a 2.86× miss). Reproducible signal: count the distinct
  call-sites or files the WU's AC actually mutates; an
  `implementation/medium` band that touches ≥ 2 distinct wiring
  sites belongs at `high` with a per-extra-site surcharge
  (rough heuristic: +$0.40 per additional wiring site beyond the
  first, +$0.30 per orchestration-invariant the WU must preserve).
  Re-using a sibling WU's scaffolding (T05 ← T04) is the cheap
  case; introducing or coordinating sites is the expensive case.
  Rule: when an AC body names ≥ 2 file paths the WU must mutate,
  or ≥ 2 already-shipped helpers the WU must call into, raise
  the band; effort alone will price single-site work.

- **[FEAT-2026-0018/G2-CLOSE-INTERMEDIATE] Driver-wiring
  implementation WUs default to 2 attempts in practice; budget
  accordingly.** Every substantive gate-2 WU (T04, T05, T06)
  needed exactly 2 attempts. None escalated to `blocked_human`;
  none replanned. The first attempt commonly lands code that
  fails an AC-level verifier — symbol-existence check (AC8 in
  driver-wiring WUs), an integration test, or a post-pass
  invariant guard — and the re-dispatch lands clean. Combined
  with the gate-1 finding that re-dispatch cost is full-cycle
  cost (not delta cost), this means an honest cost plan for
  driver-wiring WUs should assume 2× the single-attempt cost,
  not 1× plus a small retry margin. Rule: when authoring a WU
  whose AC includes a symbol-existence guard (`produces_driver_
  helper`) or a multi-site integration assertion, set
  `planned_cost_usd` to 1.5–2× the single-attempt estimate;
  prefer over-budgeting on the planning line to under-budgeting
  and learning it from a 1.6× post-hoc ratio.

- **[FEAT-2026-0018/G3-CLOSE] A predicate that scores planner output
  is itself the planner-quality oracle once shipped — run it against the
  feature it shipped in at close ceremony.** FEAT-2026-0018 shipped
  `gate_eval.py` (deterministic on-plan / off-plan predicate against
  per-gate cost ratios, hard-overrun ceiling, plan-next overrun, and
  gate-budget exceedance). At G3-CLOSE, running `gate_eval.py backtest
  FEAT-2026-0018` against this feature itself returned `G01 auto=False`
  + `G02 auto=False` + `G03 auto=True` — every verdict matched the
  retrospective evidence the human had already written: gates 1 and 2
  documented multi-WU effort-band misclassifications + plan-next
  overruns + budget exceedances; gate 3 came in clean (single-attempt
  per WU, 0.81× plan substantive, well under raised budget). The
  predicate refused its own development gates and accepted its own
  dogfood gate, self-consistent. This is more than a sanity check: it
  promotes the predicate from "thing the close ceremony runs" to "thing
  the close ceremony USES as its planner-quality verdict." Rule: any
  feature that ships a verifier scoring planner output (cost-ratio gate,
  schema lint, drift detector, prediction calibration) must include a
  recursive self-evaluation in its close ceremony — run the verifier
  against the FEATURE'S OWN per-gate evidence and paste the verbatim
  output into the retrospective. When verdicts agree with the human-
  written narrative, that 'self-consistent' note is the
  load-bearing audit signal future planners read at draft-feature
  time. When verdicts disagree, the disagreement itself is the
  feature's first real escaped-bug evidence — promote it to a
  blocking lesson before shipping the next feature.

- **[FEAT-2026-0018/G3-CLOSE] A hygiene WU authored mid-gate to fix a
  bug surfaced by that same gate's evidence will, by its own cost,
  often push the gate over the predicate's auto-close criteria —
  pre-commit to whether the gate's predicate verdict is read pre-
  hygiene or post-hygiene.** FEAT-2026-0018's gate 3 originally
  evaluated `auto=True` against T07–T10 ($2.34 substantive, well
  under $8.00 budget). G3-CLOSE's first attempt diagnosed a wiring
  bug at `loop.py:2310` (terminal auto-close branch post-loop
  instead of in-loop pre-dispatch); the operator armed hygiene WU
  T11H to relocate the call site. T11H landed structurally clean
  but cost $3.65 against $0.80 planned (4.56×), pushing gate-3
  substantive to $8.40 — over the $8.00 budget AND tripping
  per-WU hard-overrun (criterion 4). The same gate, same data
  shape, same predicate, returned `auto=False` on the re-evaluation.
  Rule: when a gate-N close ceremony surfaces a hygiene WU that
  will land inside gate N, decide explicitly which predicate
  verdict is load-bearing — the PRE-hygiene verdict (the gate's
  outcome BEFORE the fix was needed; load-bearing for what the
  shipped feature actually achieved) or the POST-hygiene verdict
  (the gate's outcome AFTER the fix landed; load-bearing for
  the next planner reading the calibration history). Both are
  legitimate but they answer different questions; the
  retrospective must paste BOTH backtest outputs so the audit
  trail is unambiguous, and the verdict frontmatter must cite
  which one it anchors to. Corollary: hygiene WU `planned_cost_usd`
  must be priced generously, especially when the hygiene WU
  carries an invariant-shaped acceptance criterion (here,
  pre-dispatch ordering) — the hygiene WU's own cost is what
  determines whether the gate's recursive-dogfood verdict
  agrees with itself across the fix boundary.

- [FEAT-2026-0016/G1-CLOSE-INTERMEDIATE] Closing-deliverable WUs
  whose acceptance criteria check "is this new file in the diff?"
  must combine `git diff --name-only HEAD` with
  `git ls-files --others --exclude-standard`. `git diff` alone
  omits untracked files, so the AC fails spuriously on the very
  file the WU just created. T03's AC7e shipped with the broken
  single-command form and blocked correctly on first attempt; the
  agent diagnosed it with a direct LEARNINGS cite to
  `[driver/files_changed-guard]`. The same broken pattern existed
  in this WU's AC6 and was fixed pre-emptively (commit 3f77530).
  Generalizing rule: every closing-deliverable WU spec that
  produces a NEW file at the feature-folder root must use the
  combined `{ git diff --name-only HEAD; git ls-files --others
  --exclude-standard; }` form in its existence-check AC.
  Promoting to authoring-work-units §X (closing-deliverable AC
  patterns) is a candidate gate-3 docs task.

- [FEAT-2026-0016/G1-CLOSE-INTERMEDIATE] Standardized event
  payload contracts deserve a single emission helper, and the
  feature spec that introduces the contract carries a structural
  bootstrap gap that the retrospective must call out by name.
  T01 introduced `emit_attempt_outcome(...)` and migrated four
  legacy emission sites + added three new ones in one attempt;
  the spec's §10 helper-duplication pre-flight grep caught zero
  collisions, validating the "one helper, all sites" pattern.
  But because the driver runs the OLD code while dispatching the
  WU that ships the NEW code, T01's own events.jsonl lines lack
  the new payload fields — the first WU whose events carry the
  full v1 payload is T03 (the NEXT WU after T01 lands). Rule:
  any feature whose gate 1 ships an event-payload contract
  extension must (a) name the bootstrap gap explicitly in the
  WU spec ("this WU's own events lack the new fields, by
  design"), and (b) reconcile post-hoc in the retrospective by
  pointing to the first WU whose events carry the new shape.
  This pattern was first documented in `[FEAT-2026-0006/G1-CLOSE]`
  and is now confirmed across two features — promote to a
  drafting-time checklist item.

- [FEAT-2026-0016/G3-CLOSE] A driver helper that buckets
  attempt-level events into gates by parsing the
  `correlation_id` suffix must resolve **both** substantive-WU
  IDs (`TNN`) and closing-WU IDs (`G<n>-…`). T07's
  `summarize_attempt_failure_classes(feature_dir, gate_n=N)`
  delegates to `_gate_number_from_wu_id`, which currently
  matches only `G<n>-…` segments — substantive-WU IDs return
  `None` and are silently filtered out when `gate_n` is set.
  Observed at gate-3 close: T08 had one non-passing
  `attempt_outcome` (sandbox block, correctly diagnosed), the
  helper returned the `(no non-passing attempts in scope)`
  sentinel for `gate_n=3`, the close-guard
  `assert_failure_class_breakdown_when_failures_present`
  passed via the sentinel route, and the recursive-dogfood
  retrospective surfaced the gap. Rule: any helper that takes
  a `gate_n` parameter and resolves it from a `correlation_id`
  must load the gate-WU membership from `PLAN.md`'s
  `gates[].work_units[].id` graph (the authoritative source —
  the same shape that `WU-90-gate-N-close.md` AC10c's
  existence check derives). Corollary: the close-guard tied
  to such a helper is only as load-bearing as the helper's
  bucketing fidelity — when planning a helper-backed guard,
  invariant-test the bucketing against a fixture mixing
  substantive-WU and closing-WU events, not just one or the
  other.

- [FEAT-2026-0016/G3-CLOSE] Skill-adding WUs that need to
  create discovery surfaces under `.claude/skills/` cannot
  use a dispatched session to make the symlink, even with
  `unsandboxed: true` on the WU. Claude Code's sandbox lists
  `.claude/skills` under `denyWithinAllow`, which is a deny
  rule inside an allow scope — it survives `unsandboxed: true`.
  Observed at T08's first attempt: agent correctly diagnosed
  the boundary and emitted `status: blocked`; operator created
  the symlink manually from the main Claude Code session
  (which carries different sandbox permissions) and re-armed.
  Rule: skill-adding WU specs must split the work into
  (a) agent-side authoring of `.specfuse/skills/<name>/SKILL.md`
  and (b) operator-side symlink creation at
  `.claude/skills/<name>` — call out the split explicitly in
  the WU spec so the agent does not waste an attempt
  rediscovering the sandbox boundary. Equivalently, the WU
  spec can mark the symlink as a pre-dispatch operator
  prerequisite (analogous to how some test-fixture WUs
  pre-stage data).

- [FEAT-2026-0016/G3-CLOSE] Data-layer-first-then-consumers
  feature shape paid off cleanly in this feature's three-gate
  arc. Gate 1 shipped the contract surface (T01 emission +
  T02 frontmatter + T03 tests) in 3 substantive WUs / 3
  attempts / one spec-defect re-arm; gate 2 shipped three
  consumers (T04 / T05 / T06) in 3 substantive WUs / 3
  attempts / **zero** re-arms; gate 3 shipped the close-
  ceremony helper + skill + docs (T07 / T08 / T09) in 3
  substantive WUs / 4 attempts / one sandbox-boundary re-arm.
  Total feature substantive spend $9.04 against $13.20
  planned (-32% under plan). Rule: when a feature's
  `roadmap_goal` describes a contract + ≥ 2 consumers,
  default to a 3-gate arc with the contract isolated in gate
  1, consumer wiring in gate 2, and close-ceremony / skills /
  docs in gate 3 — the alternative ("mix data + consumers in
  one gate to ship faster") sacrifices the bootstrap-gap
  discipline that lets the data-layer's own retrospective be
  reviewed before consumers commit to its shape. Document this
  shape in the next `authoring-work-units` revision as the
  default for contract-shaped features.

- [FEAT-2026-0020/history-scrub/three-surfaces] `git filter-repo
  --replace-text` scrubs ONLY file contents (blobs). It does NOT
  touch commit messages or file paths/names. A scrub that runs only
  `--replace-text` looks done (working tree clean) but leaks persist
  in commit-message bodies and any filename that embeds a private
  token. Live evidence: first scrub left 35 message residuals + a
  `SMOKE-INIT-2026-0001-F06.md` filename. Rule: scrub all three
  surfaces in one pass — `--replace-text` + `--replace-message`
  (same mapping file) + `--path-rename` (or `--path … --invert-paths`
  to delete) — and VERIFY each surface separately (a single
  `git log --all -p | grep` blurs which surface still leaks).
  Reusable harness lives at
  `.specfuse/features/FEAT-2026-0020-public-readiness-prep/history-scrub/scrub-history.sh`
  (gitignored; `--verify-only` audits read-only).

- [FEAT-2026-0020/history-scrub/scope-vs-fixtures] `filter-repo
  --replace-text` rewrites HEAD's blobs too, so a too-broad mapping
  silently edits live SOURCE and TEST FIXTURES. Live evidence:
  blanket-redacting `INIT-2026-0001` — which is the scaffold's own
  canonical orchestrated correlation-ID sample (in
  `.specfuse/rules/correlation-ids.md` + 4 test suites), not an
  org-identifying string — broke 19 tests in one shot. Rules: (1)
  redact only genuinely-private tokens; a shared/sample identifier
  that also names a private instance is NOT automatically a leak —
  classify it. (2) Correct order is redact-working-tree-FIRST (fix
  any tests in lockstep, commit, suite green), THEN history-scrub —
  because once HEAD already matches the redacted form, `--replace-text`
  only rewrites OLD commits and the working tree + tests stay green.
  (3) Always run the test suite immediately after any history rewrite;
  blob substitution can break code with zero error output. Recovery
  path that worked: restore from the PRE-scrub bundle (the first one,
  pre-pass-1 — not an intermediate), re-scope, re-run.

- [FEAT-2026-0020/G1-CLOSE-INTERMEDIATE] Do NOT fold an out-of-loop-only
  audit surface into the same gate as in-loop-verifiable ones. An audit/
  remediation WU whose surface the dispatched agent cannot reach at all
  (e.g. the GitHub issue/PR surface — `gh` returns auth errors inside
  `claude -p`, the documented `gh`↔claude-p bug) produces ZERO in-loop
  evidence: both the audit and the fix run in the operator's session. Mixed
  with deferred-but-post-state-verified surfaces (secrets, working-tree
  refs, license headers — loop scans, operator fixes, loop re-scans), it
  inflates the gate's `## What the loop did NOT verify` count past the
  >2 sizing threshold. Rule: when authoring an audit gate, give any
  surface the agent cannot reach its OWN gate, OR mark the WU
  `designated-out-of-loop` at plan time with an operator-journal artifact
  as the verification proxy. Keeps the in-loop gate's deferred list ≤2 and
  stops "deferred but verified post-state" being conflated with "the loop
  never had eyes on this."

- [FEAT-2026-0020/G1-CLOSE-INTERMEDIATE] A close-intermediate WU that is
  DISPATCHED (not auto-closed) must carry a hedged `verdict:` in its
  frontmatter, even though the gate is non-terminal. `lint_plan.py`'s
  verdict-exempt set for close-type WUs omits `in_progress`/`in_review`,
  and the driver flips status→`in_progress` at dispatch, so plan-lint
  (the `plannext` gate set) FAILS mid-dispatch on a verdict-less close
  WU — even when AC text says "no terminal verdict." The driver has no
  `close-intermediate` terminal-flip branch (only `close` is read for
  `verdict_permits_terminal_flips`), so a non-`met` value (`met_locally`/
  `partially_met`) satisfies the lint while triggering nothing. Rule:
  author close-intermediate WUs to WRITE a hedged verdict reflecting the
  honest gate state; reserve `met`/`verdict:`-absence semantics for the
  auto-close path, which bypasses the in_progress lint window. (Fix the
  lint exempt-set to include in_progress/in_review only as a separate,
  deliberate WU — do not weaken a gate from inside a close session.)

- [FEAT-2026-0020/G2/hollow-pass-presence-gates] The driver enforces the
  `code` gate set (test suite) but does NOT machine-run the per-WU
  file/symbol-presence checks written in WU bodies. Two gate-2 WUs passed
  `done` with deliverables absent: T12 created SECURITY.md but not the
  bundled CODE_OF_CONDUCT.md (its own `test -s CODE_OF_CONDUCT.md` gate was
  never run); T16 touched ZERO files (no hook, no CI gate) yet passed, at
  $1.48 cost. The FEAT-2026-0008/0015 hollow-pass guards did not catch
  zero-deliverable or partial-bundle passes. Rules: (1) a WU's body
  presence/symbol checks must be promoted to machine-enforced gates the
  driver actually runs before accepting `complete` — filed as a loop bug.
  (2) Until then, run `/gate-status` before any gate close and spot-check
  that each `done` WU's named deliverable files exist on disk; `done` is
  not evidence of a deliverable. (3) A bundled WU (N files in one WU) is a
  hollow-pass amplifier — prefer one deliverable per WU, or assert every
  bundled file in a single machine gate.

- [FEAT-2026-0020/G2/out-of-loop-completion] When the loop cannot reliably
  produce + verify a deliverable (here: hollow passes the driver won't
  catch; a `gh`/`claude -p` auth surface; a CLI the prior WU never shipped),
  completing out-of-loop with REAL re-run verification beats re-dispatching
  the same WU body — a re-dispatch bets on the same gap. Acceptable for the
  loop's own repo; record it explicitly: set `completed_out_of_loop: true` +
  `completed_note` on the WU, and log it in the retrospective's "What the
  loop did NOT verify". Four WUs finished this way across FEAT-2026-0020
  (gate-1 T04; gate-2 T12/T16/T18 + the T15 CLI gap).

- [FEAT-2026-0020/G2/policy-text-content-filter] Generating standard
  policy/community text inline (Contributor Covenant 2.1, whose
  unacceptable-behavior list enumerates harassment/abuse terms) can trip the
  model OUTPUT content-filter and hard-block the turn ("Output blocked by
  content filtering policy"). Fix: do not generate such text inline — fetch
  it from its canonical source (raw.githubusercontent.com is allowlisted)
  and post-process in shell so the body never passes through model output.
  Applies to any vendored license/policy/CoC boilerplate.

- [FEAT-2026-0020/G2/leak-guard-surface-asymmetry] A leak detector needs
  DIFFERENT scopes per caller. Structural regexes (user-path / email /
  private-host) are right on a DIFF (a newly-introduced path is suspicious)
  but false-positive as an absolute repo gate (doc placeholders like
  `/Users/<user>/`, the detector's own test fixtures, config addresses like
  git@github.com). So: pre-commit (`--staged`) runs the full structural +
  denylist + secrets scan on the diff; the CI gate (`--all`) runs only the
  high-confidence checks (gitignored literal denylist + gitleaks secrets).
  Verified: `--all` exits 0 on the clean tree; `--staged` blocks a planted
  path. Generalize: heuristic regexes belong on diffs, not whole-tree gates.

## FEAT-2026-0022/G1-CLOSE — deliverable presence is now machine-enforced

- [FEAT-2026-0022/G1-CLOSE] The advisory→enforced promotion that
  [FEAT-2026-0020/G2/hollow-pass-presence-gates] filed as a loop bug is
  shipped. Three independent driver-side guards now sit in the
  parse→squash→advance pipeline: `WorkUnit.produces` (parsed field +
  advisory lint WARN), `assert_declared_deliverables` (each `produces:`
  path must exist + be non-empty before `complete` is accepted, else
  `deliverable_missing`), and `assert_implementation_touched_files` (an
  `implementation` WU touching zero deliverable files records
  `no_deliverable_files` and blocks). This closes the two shapes the
  no-code-written guard ([FEAT-2026-0008/G1-CLOSE]) left open:
  zero-deliverable (T16) and partial-bundle (T12). Rule: a body-level
  `test -s` presence check is advisory and worthless on its own — the
  only presence check that runs is the one the driver runs. Promote
  named-file deliverables to `produces:` so they are enforced, not
  attested.

- [FEAT-2026-0022/G1-CLOSE] Recursive-dogfood close validated a third
  time (after [FEAT-2026-0008/G1-CLOSE], [FEAT-2026-0015/G2-CLOSE]): a
  feature whose purpose is to ship hollow-pass guards must audit that
  its OWN three WUs did not hollow-pass the guards they add. Live
  recursive validation here went past existence — the close ran
  `test_deliverable_presence_gate` (10) and `test_empty_files_escalation`
  (6) and confirmed both the BLOCK path (`deliverable_missing` /
  `no_deliverable_files` fire and escalate to `blocked_human` after
  MAX_ATTEMPTS) and the clean path (a satisfied deliverable does NOT
  block). Existence + green tests + asserted block-outcomes is the
  three-layer audit; existence alone would have missed a guard that
  parses but never fires.

## FEAT-2026-0023/G1-CLOSE — seam bugs need an integration layer; terminal flips need ONE owner

- [FEAT-2026-0023/G1-CLOSE] Three driver bugs (#47 row-only archive
  anchor, #48 `ensure_feature_branch` raw traceback, #49 auto-close
  leaves `PLAN.md status: active`) were one class: **seam bugs at
  handoffs between subsystems, none catchable by unit tests because unit
  tests stub the handoffs.** They only execute at real feature
  boundaries — rare events the first true autonomous runs finally
  exercised. Rule: when a bug lives in the gap between two subsystems,
  the durable fix is not another unit test on either side — it is an
  end-to-end integration test that stubs ONLY the agent boundary and
  drives the real driver through the whole lifecycle (draft → pick →
  loop → terminal close on BOTH paths → archive). `test_lifecycle_integration.py`
  is that layer; it would have caught all three. This is the
  driver-side analogue of the deliverable-presence layering in
  [FEAT-2026-0022/G1-CLOSE] and the no-code-written guard in
  [FEAT-2026-0008/G1-CLOSE]: each closes a CLASS by adding the layer
  that runs at the real boundary, not by patching one instance.

- [FEAT-2026-0023/G1-CLOSE] Terminal-state flips must have exactly ONE
  driver-side owner called identically by every close path. #49 existed
  because two paths diverged: the dispatched-close path relied on the
  close WU's *agent* to flip `PLAN.md`, while the agent-less auto-close
  path ran no agent and `fire_terminal_flips` never touched PLAN. Fix
  (T01): fold the PLAN flip into `fire_terminal_flips` alongside the
  gate/roadmap/archive flips, gated on `verdict_permits_terminal_flips`,
  reading the verdict from disk (not in-memory `wu.verdict`, which the
  auto-close path leaves None). Corollary, now enforced in the
  `draft-feature` and `authoring-work-units` skills: do NOT add a "flip
  PLAN.md to done" acceptance criterion to a terminal `close` WU — the
  agent flip is redundant and re-opens the divergence. Recursive-dogfood
  close validated a fourth time: this feature's own close audited that
  its three WUs did not hollow-pass — single `fire_terminal_flips`
  definition, no competing PLAN-status writer, all three guard tests
  present and green (14 tests OK).

## FEAT-2026-0024/G2-CLOSE — a leak-guard feature can poison its own loop bookkeeping

- [FEAT-2026-0024/G2-CLOSE] A leak-scan pre-commit hook scanning the loop's OWN
  bookkeeping diff will flag structural-hit strings the driver itself recorded
  into `events.jsonl`. During this feature, `G1-PLAN` attempt 1 died with
  `squash_commit_failed`: the pre-commit `leak-scan` hook rejected the
  bookkeeping squash on `email: 'git@github.com'` — a config address the driver
  had embedded in a `failure_excerpt` it wrote into `events.jsonl` when T02's
  attempt 1 failed. The leak-guard feature thus poisoned its own loop
  bookkeeping, costing a full re-attempt (+$3.23). This is the
  `[FEAT-2026-0020/G2/leak-guard-surface-asymmetry]` insight one level up the
  stack: that entry says heuristic structural regexes belong on *diffs*, not
  whole-tree gates, because diffs of doc/config/fixture content carry benign
  hits (`git@github.com`, `/Users/<user>/`); here the *diff being committed is
  the driver's own event log*, whose `failure_excerpt` field faithfully captures
  whatever the failing gate printed — including a structural hit. Rule: any
  bookkeeping commit a driver makes to a leak-scanned tree must be exempt from
  the structural pre-commit scan over driver-owned state (`events.jsonl`,
  attempt notes), OR the driver must redact structural-hit patterns from
  `failure_excerpt` before persisting them. The CI `--all` gate already excludes
  structural regexes for exactly this false-positive class; the pre-commit hook
  over bookkeeping needs the same carve-out. Fixed driver-side in commit
  `02db0af` ("stop bookkeeping-commit crash on leak-scan self-poison");
  cataloged here so future leak-guard / log-recording features expect the
  self-poison and do not re-pay the re-attempt.

- [FEAT-2026-0024/G2-CLOSE] When a feature's headline acceptance can only run in
  an external execution environment (a live GitHub Action firing on a real
  issue/PR event), split the deliverable at the unit-testable seam and ship the
  oracle as operator-deferred — do NOT manufacture in-loop confidence with
  `act`/Docker emulation. Gate 2 shipped the behavioral runner
  (`leak_scan_content.py`, fully unit-tested over fixture event JSON) separately
  from its thin Action wrapper (`leak-scan-content.yml`), so the close honestly
  reports `partially_met`: surface built + seam verified in-loop, live trigger
  operator-confirmed post-merge. This is the
  `[FEAT-2026-0020/G2/out-of-loop-completion]` and
  `[FEAT-2026-0014/T01/gh-claudeP-broken]` precedents applied at design time
  rather than discovered at block time. Rule: for any WU whose true oracle is an
  external-environment trigger, (a) carve out a pure, importable runner that
  carries the behavioral test, (b) mark the live trigger operator-deferred in the
  PLAN's oracle section and the close WU's `## What the loop did NOT verify`, and
  (c) set the close verdict to `partially_met`/`met_locally` so the driver holds
  the terminal flips until the operator confirms — never `met` on an unconfirmed
  live oracle.

- [FEAT-2026-0019/G1] A feature that migrates the verification harness the driver
  itself runs to gate work (the test loader, `verification.yml` gate set, packaging
  of the driver code) cannot be decomposed into separately-gated loop WUs: each WU's
  exit oracle is the very surface being migrated, so no WU can pass alone and the
  driver thrashes (here: one T02 attempt burned ~$5.63 / 49 min on
  `ModuleNotFoundError: No module named 'specfuse'` before abandonment). Author such
  "harness migration" features as a SINGLE atomic change, or complete them
  interactively; do not split package-extraction + shim + test/coverage migration
  into three dispatched WUs gated by the half-migrated harness. Tell at draft time:
  if a WU edits `verification.yml`, the test loader, or how the driver's own code is
  imported, its sibling WUs share a broken oracle until all land together.

- [FEAT-2026-0028/G2] A feature gate whose work AND verification live in a SIBLING repo
  (here: the umbrella `specfuse` CLI in specfuse/specfuse, calling the driver's
  scaffold API) cannot be loop-dispatched — the driver runs in this repo and its cwd,
  git, and verification all target it. Draft such a gate's WUs as interactive specs
  (flag them cross-repo in Context), execute them by hand in the sibling repo, and have
  the terminal close record the real oracle result (tests run THERE) under "what the
  loop did NOT verify" with the sibling commit as evidence. Tell at draft time: if a
  WU's `produces:` paths or its test command live outside this repo, it is a cross-repo
  interactive WU, not a dispatchable one.

- [FEAT-2026-0027/G3] A WU that adds interactive `input()`/TTY-consent code, or that
  reads operator home-dir data, has two recurring failure modes the loop must defend:
  (1) its tests MUST mock `sys.stdin.isatty` + `builtins.input` (an unmocked prompt
  fails or — pre-fix — hangs the verify gate); (2) committed fixtures MUST be synthetic
  (no real home paths/identifiers), or the leak-scan rejects the squash and the captured
  finding self-poisons events.jsonl. The driver now hardens both: verify() runs gates
  with `stdin=DEVNULL` (input-reading gates EOF-fail fast, not hang) + a process-group
  kill on timeout (genuine hangs actually return). Tell at draft time: any WU touching
  `input()`/`isatty` or `~/.claude`-style reads needs an explicit "mock TTY + synthetic
  fixtures" acceptance criterion.

- [bugs #71/#74] The per-attempt `git reset --hard head_before` destroys ANY uncommitted
  `.specfuse/features/<active>/` state — and two real flows leave state uncommitted by
  design: `draft-feature` writes the whole folder UNTRACKED (#71), and `arm-gate` writes
  tracked-but-uncommitted status flips + AC revisions (#74). The old pre-flight dirty
  check caught only tracked modifications, so an all-untracked folder slipped through, got
  swept into the first squash (now tracked), then was deleted by the next failed attempt's
  reset — crashing the subsequent frontmatter write with a bare FileNotFoundError. The
  driver now pre-flights both: `require_feature_folder_committed` (untracked) +
  `require_feature_folder_unmodified` (tracked-uncommitted, excluding PLAN.md/events.jsonl/
  work/), each a hard-stop before `ensure_feature_branch`. Operator rule: commit the
  feature folder AND any arm-gate edits before running the loop — a committed folder is in
  `head_before` and survives every reset. Tell at authoring time: any state a skill writes
  but does not commit is one failed attempt away from being erased.

- [bugs #75/#76] A leak-scan pre-commit hook rejection is a cascading failure, not a point
  failure: the hook's FINDINGS text QUOTES the offending token; the driver captured that
  into events.jsonl as the attempt note; the next bookkeeping commit re-scanned the log and
  re-tripped on the quoted token (self-poison, #76); and the resulting BookkeepingCommitError
  propagated uncaught out of run() as a raw traceback (#75). Fixes: `redact_leak_findings`
  scrubs the quoted match to `<redacted:sha8>` before capture (keeps audit signal, kills the
  trigger), and run() catches BookkeepingCommitError → graceful halt. General rule: any text
  captured from a rejected-commit stderr into a re-scanned audit surface must be redacted at
  capture, and every commit the driver makes (squash AND bookkeeping) needs a rejection
  handler — the squash path having one is not enough.

- [test-authoring/leak-hygiene] Test files that must embed leak-trigger fixtures (emails,
  `/Users/...` paths, `*.internal` hosts) trip the structural PRE-COMMIT hook
  (`leak_scan --staged`) but PASS the CI `leak-scan` gate (`leak_scan --all` / `scan_repo` is
  structural-free — denylist + gitleaks only). Two rules: (1) for INCIDENTAL fixtures (e.g. a
  tmp-repo `git config user.email`), use an RFC-2606 allowlisted domain — `t@example.com`,
  not `t@test.com` — and the hook passes clean; (2) for tests that genuinely NEED a tripping
  token (e.g. a redaction test's input), commit with `git commit --no-verify` and rely on the
  CI gate — the established `tests/test_leak_scan.py` convention. Tell at authoring time: a WU
  whose tests carry leak fixtures must say which of the two applies, or it spuriously blocks
  on the local hook.

- [process/issue-triage] An open GitHub issue is NOT proof the work is undone. Before drafting
  a feature from one, `git log` for a prior feature that already shipped it: a squash merge
  whose `closes #N` lived only in a feature-BRANCH commit (not the PR body or a default-branch
  commit) does not auto-close the issue. Issue #46 ("issue/PR-body leak guard") sat open while
  FEAT-2026-0024 had shipped the Action + runner + docs the same day — its headline acceptance
  was also intentionally left as an operator post-merge live-oracle step. Rule: triage
  open→(read merge history + the feature that names the issue) before assuming a fresh feature
  is warranted; the fix may be "verify the deferred oracle and close," not "build it again."

- [FEAT-2026-0029/G1-CLOSE] A WU that authors a parser/consumer must have its input
  artifact's existence verified at draft time — not the format, the *existence*.
  FEAT-2026-0029/T01 was drafted to parse a `specfuse upgrade` "health report" string
  format that is implemented NOWHERE in the repo (described only in prose in
  `feature-conversion/SKILL.md`). The agent correctly blocked on attempt 1 rather than
  invent a grammar, but the block cost a dispatch (~$0.71) that a draft-time check would
  have avoided; the WU was re-scoped to a Python data-structure contract
  (`{"feature","ok","detail"}`) consuming `lint_plan.py`'s already-implemented per-feature
  exit code instead. Rule: before dispatching any WU whose acceptance criteria parse,
  consume, or extend an artifact produced by another tool, `grep`/`ls` for that artifact
  in the repo. If it does not exist, the WU's contract must be a code-level data structure
  against an in-repo signal, NOT a parse of a not-yet-emitted string. "The format is
  described in prose in a sibling skill" is not "the format exists."

- [FEAT-2026-0029/G1-CLOSE] Sandbox `mktemp -d` denial (`Operation not permitted`) is an
  environment limit that presents as a test failure and will consume the entire 3-attempt
  spinning budget if the WU spec doesn't pre-empt it. FEAT-2026-0029/T01's tmp-repo fixture
  for `collect_reports` spun 3 failed attempts on `mktemp: mkdtemp failed on /var/folders/...:
  Operation not permitted` before a re-arm found a working tmp-dir strategy — none of it a
  logic bug. Rule: any WU whose tests build a temp git repo or scratch dir MUST use the
  repo's established `tempfile.TemporaryDirectory` / `$TMPDIR` fixture pattern and the WU
  spec should name the sandbox tmp-dir constraint explicitly, so the agent doesn't
  rediscover the denial under the spinning budget. Pairs with the FEAT-2026-0013 tmp-repo
  fixture rules (gc.auto=0 + sync barrier + ignore_cleanup_errors).

- [FEAT-2026-0029/G1-CLOSE] Scope a wiring/registration WU's acceptance criteria to the
  artifact's actual *delivery model*, or it will block on an unrelated, out-of-scope defect
  in a different delivery path. FEAT-2026-0029/T03 (register a skill) blocked on attempt 1
  because an AC drove the agent into a `scaffold.py` skill-deploy defect (`init()`/
  `upgrade_specfuse()` deploy no skills for anyone) — but Specfuse skills ship via the Claude
  Code **plugin**, not the pip scaffold, so that defect was never on this WU's path. The
  agent correctly escalated instead of weakening the regression; the fix was to re-scope the
  WU (commit da81c27) to the plugin skill-delivery model (real dir in `.specfuse/skills/<name>/`
  + forward `.claude/skills/<name>` discovery symlink). Rule: a WU that wires/registers an
  artifact must name in its Context which delivery mechanism ships it (plugin vs pip scaffold
  vs generator) and bound its ACs to that mechanism's surfaces only; an AC that reaches into
  a sibling delivery path's internals is a mis-scope that will block or force a driver-internals
  edit.

- [FEAT-2026-0031/G1-CLOSE] *(operator-authored — the gate auto-closed, so no close session
  ran to write this; see the companion lesson below.)* An injected-runner seam that only
  **some** calls route through gives tests false confidence. `gh_backend.py`'s
  `on_feature_complete` took a `runner=` injection and had a `runner=stub_runner` test suite
  (`tests/test_gh_backend.py`) — but its `gh pr view` idempotency probe called
  `subprocess.run` **directly**, so the stub intercepted `gh pr create` while the probe
  escaped to the real binary. Every existing test passed; the probe was simply never
  exercised. Found by *reading* the module while drafting FEAT-2026-0031/T03, not by any
  test — a bypassed seam is invisible to the suite that assumes it. The fix widened
  `_default_runner(args, check=True)` to return the completed process, so the probe inspects
  `.returncode` without raising while side-effecting callers keep raise-on-failure
  (commit ed44c62). Rule: when a module takes a runner/client injection for testability, an
  audit that **every** external call goes through it is part of the seam's contract — grep
  the module for the raw call (`subprocess.run`, `requests.`, the SDK entrypoint) and assert
  zero direct hits. A partial seam is worse than none: it reads as covered.

- [FEAT-2026-0031/G1-CLOSE] Auto-close silently voids a close WU's `produces:` contract and
  every acceptance criterion in its body — the deliverable-presence gate (FEAT-2026-0022)
  cannot fire on a WU that is never dispatched. FEAT-2026-0031's `G1-CLOSE` declared
  `produces: [RETROSPECTIVE.md, .specfuse/LEARNINGS.md]` and carried explicit AC bullets for
  a `## Cost analysis` section, a `## What the loop did NOT verify` list (pre-populated with
  two known deferred `gh` oracles), and four candidate lessons. The gate stayed on-plan, so
  `evaluate_auto_close` fired (`predicate=v1, reasons=[], auto=True`): the WU closed
  `verdict: met` with `attempts: 0`, a 10-line stub retrospective was written, and
  `LEARNINGS.md` received **zero** entries. Nothing failed; the ceremony simply never ran,
  and the feature's only record of its deferred-verification gaps was the operator's session.
  This is §6 ceremony proportionality working as designed — but the design's cost is
  invisible at authoring time, because a carefully-written close WU looks like a contract and
  is actually a conditional. Rule: when drafting a feature whose close WU carries deliverables
  that matter **independently of reflection quality** (a deferred-verification list, a
  cross-repo handoff note, a security caveat), do not rely on the close WU to produce them —
  either put them in a substantive WU that always dispatches, or plan to write them by hand
  after an auto-close. Corollary for reviewers: `auto_close: true` + `attempts: 0` on a close
  WU means its body was never executed; read the WU's ACs as *unfulfilled*, not as evidence.

- [FEAT-2026-0032/G2-CLOSE] A gate-1 deferral that names a *later gate* as its verification
  venue is not closed just because that gate ships — the later gate has to actually exercise
  the deferred path. Gate 1 deferred T02's real-Windows timeout `taskkill` branch to "gate 2's
  gate execution." Gate 2's CI oracle (T08) does run a real gate command through Git-Bash on
  `windows-latest`, but that command **passes** (`… && echo GATE_OK`); nothing drives a gate to
  timeout, so the `CREATE_NEW_PROCESS_GROUP` + `taskkill` branch stayed unexercised. The
  deferral read as "gate 2 will close it," gate 2 closed the *happy path*, and the kill path
  silently rode into the close as still-open — caught only because WU-92 AC3 forced folding the
  gate-1 deferrals back in and asking "resolved?". Rule: when deferring an AC to a future gate,
  the deferral must name the **specific WU/oracle** that will exercise it (here: a CI leg that
  drives a gate to timeout and asserts the kill), not just the gate; and the future gate's close
  must verify each inherited deferral was *actually* exercised, not merely that the gate shipped.
  A deferral pointed at a gate is a promise the gate can silently break.

- [FEAT-2026-0032/T08] A CI-oracle WU whose real exit condition is a `windows-latest` (or any
  cross-OS) PR job is `done` in-loop the moment its `@skipUnless(sys.platform=="win32")` test is
  collected-and-skipped on the Linux sandbox and the wiring lints — which proves the wiring and
  the skip, NOT that the gate ran green on the target OS. Combined with `[FEAT-2026-0024/G2-CLOSE]`:
  such a feature's close must report `partially_met`/`met_locally` (never `met`) until the operator
  confirms the real-runner job is green, so `verdict_permits_terminal_flips` holds the terminal
  `PLAN status → done` flip. Tell at draft time: any WU whose oracle is a CI leg on an OS the loop
  sandbox is not, ships its real proof PR-deferred — enumerate it in the close's `## What the loop
  did NOT verify` and hedge the verdict.

- [FEAT-2026-0036] Pin a linter/formatter's RULESET explicitly (`[tool.ruff.lint] select`),
  not just its version. A bare ruff config inherits ruff's *implicit default* `select`; ruff
  0.16 broadened that default from the classic `E4,E7,E9,F` to a large opinionated set
  (B/SIM/PLW/RUF/I/…), so an unpinned `ruff>=0.6` flagged ~300 findings on code clean for
  months and broke the lint gate on every PR — zero code involved, purely a version bump
  redefining "default." A version pin (`<0.16`) only defers the surprise to the next bump; the
  durable fix is to write the intended ruleset down (`select = ["E4","E7","E9","F"]`) so the
  gate is version-independent. Adopting new rule families then becomes a deliberate choice, not
  an accident of upgrading. Same shape for any tool whose "default" behavior you rely on
  implicitly (formatters, type-checkers, test collectors).

- [FEAT-2026-0036/T01] A WU's gate verifies the gate's *tools*, not the WU's *premise*. T01's
  job was "make `ruff check` pass under ruff 0.16," but the `code` gate ran the repo's pinned
  ruff 0.15 (clean by the classic default), so the gate went green while the agent changed
  nothing — a hollow pass that only surfaced when T02 lifted the pin and 0.16's ruleset
  appeared. Two compounding causes: (1) a WU that targets a specific tool *version/ruleset*
  must run its gate under that exact version, or the gate can't enforce the goal; (2) T01
  declared no `produces:`, so the deliverable-presence floor had nothing to assert and the
  empty change slid through — do not wave off the `no produces:` WARN on a change-existing-files
  WU. Also: when a WU blocks, check whether the *plan* was wrong before re-arming — here the
  premise (300 real errors) was itself false, so re-arming would have spun forever.

- [FEAT-2026-0037] A lint/type-check **adoption** WU must record the PRE-FIX finding count
  per rule code (`ruff check --statistics --select <codes>` before the fix, quoted in the
  WU), not only the post-fix "reports zero findings". Zero-findings is exactly what a hollow
  pass shows too, and the close cannot reconstruct the delta — the result contract bars close
  sessions from running `git`, so the dirty tree is unreadable from there. Only the WU that
  had the findings in front of it can capture the number; without it the close's "how many
  were fixed" criterion degrades into an unverifiable claim. Same shape for any
  adopt-a-stricter-tool WU (new mypy strictness, new bandit codes, a raised coverage floor):
  capture the before-number at the moment it still exists.

- [FEAT-2026-0037/T01] `PLW1510` (`subprocess.run` without an explicit `check=`) on a SHARED
  runner helper wants a `check: bool = True` **parameter**, not a hardcoded literal. When one
  helper serves both probing callers (which must inspect `.returncode` without raising) and
  side-effecting callers (which want the raise), `check=True` breaks the probes and
  `check=False` re-hides exactly the silent-failure class the rule exists to surface. The
  per-site decision rule that scales: `check=False` only where the code already reads
  `.returncode` (handling visible at the call site), `check=True` everywhere else, and a
  parameter where one helper does both.

- [FEAT-2026-0037/T02] `BLE001` has a linter-satisfying escape hatch that leaves the swallow
  intact: `# noqa: BLE001` plus a reason comment turns the gate green without binding or
  logging the exception. A WU whose criterion reads "narrow the catch, OR bind-and-log where
  a catch-all is intentional" silently permits a third path it never named — and an
  intentional top-level driver guard is precisely where that `noqa` is most tempting. Assert
  the property, not the family: "no unbound catch-all remains" (or explicitly bless `noqa` +
  reason as policy) so the adoption cannot land green with the swallow untouched.

- [FEAT-2026-0051/G1-CLOSE] "Probe the oracle before trusting it as an oracle" generalizes
  well beyond gate sets. The invariant is not about gates; it is about any exit oracle whose
  verdict can change without the repo changing — a dependency audit whose advisory database
  updated, a linter release adding a rule, a compiler bump, a license scanner, a
  network-dependent fixture, or an acceptance criterion asserting on a regenerated artifact.
  Wherever an oracle is externally fed, measure it ONCE against the unchanged base tree
  before attributing any failure to a work unit; otherwise the first WU to run inherits the
  red oracle and spins its whole attempt budget against a failure it did not cause and often
  cannot fix. This is the actionable counterpart to the `[FEAT-2026-0007/G1-LESSONS]` family:
  those say "don't make a tool's own report the acceptance oracle," this one says what to do
  when you must depend on one anyway.

- [FEAT-2026-0051/G1-CLOSE] A pre-flight probe of the full `code` set is cheap enough that
  once-per-gate-entry needs no further debate — record the measurement so it is not
  re-derived: 118s wall-clock on this repo's nine `code` gates, 93% of it duplicated test
  execution (the same suite run bare and again under coverage), ZERO model tokens (it runs
  gate commands and dispatches no agent), and 0s on any resume at an unchanged sha. Against
  a gate whose dispatch wall-clock was 1783s of billed agent time that is 6.6%, paid once.
  General rule: when sizing a brake, compare CPU-seconds against BILLED agent time, not
  against other CPU-seconds — and expect probe cost to be dominated by whichever gates
  duplicate each other's work, which is a `verification.yml` authoring concern rather than a
  driver one.

- [FEAT-2026-0051/G1-CLOSE] A driver change to dispatch control flow does NOT take effect for
  the run that writes it: Python loads the driver module once at process start, and
  gate-entry code has already executed before the first WU is dispatched. This cuts both
  ways, so state it explicitly in any self-hosting hazard note. It defuses the hazard — a WU
  editing the dispatch path cannot break the run dispatching it — and it equally invalidates
  self-hosting as EVIDENCE: a feature cannot cite "it ran against our own gates" when the
  probe it added never executed. Phrase such notes as "takes effect on the NEXT driver
  invocation," and plan a separate observation point if the self-hosted run is meant to be
  part of the acceptance evidence.
- [FEAT-2026-0039/T04] A work unit that enumerates N hand-maintained "surfaces" in prose
  will get the enumeration missed, and the miss costs a whole attempt. T04's body listed
  five seeding surfaces in a numbered block with a per-surface explanation of what breaks
  if you skip it; the attempt edited its three `produces:` files and none of the five,
  reported `complete`, and went red on `tests` + `coverage`. Worse, the enumeration was
  ITSELF incomplete — the retry also had to touch a sixth file the WU never named, and the
  two sibling WUs that copied the same list inherited the same omission. A hand-written
  fan-out list reproduces the previous author's blind spots with perfect fidelity. Two
  fixes, in preference order: make the registry the single source and have the tests read
  from it (adding a seed file becomes one edit), or — when that is out of scope — derive
  the list mechanically at authoring time by grepping the repo for an existing member of
  the same family, never by copying a sibling WU's prose.

- [FEAT-2026-0039/G2-CLOSE] An auto-closed gate's skipped ceremony is a DEBT ENTRY, not a
  saving, and the close that inherits it should price it that way. Gate 1 auto-closed
  on-plan and spent $0.00 against a $5.00 close-intermediate — a 100% underrun that
  dominated the gate's headline −32% delta. What it actually did was move the
  per-criterion deferred-verification walk into the terminal close as an explicit
  acceptance criterion, and make it MORE expensive: the session doing the walk had not
  written those WUs and had to reconstruct their verification state from the WU files.
  General rule for any close reading an auto-closed predecessor: report the underrun, then
  say plainly which of it was deferral rather than efficiency, so the number is not read
  as estimation accuracy. General rule for auto-close predicates: a gate whose WUs carry
  criteria the predicate cannot classify as verified-or-deferred is not a candidate for
  auto-close.

- [FEAT-2026-0039/G2-CLOSE] Estimate `planned_cost_usd` from mechanical fan-out, not prose
  volume — overrun risk tracks RETRY probability, and retries come from missed
  enumerations, not from long documents. Across this feature's eight substantive WUs the
  pattern was unambiguous and ran opposite to the pre-registered prediction: the two WUs
  that edited a hand-maintained list in many places overran (+29%, +52%, the latter a full
  retry); the three that wrote a lot of content into few files all came in UNDER (−75%,
  −42%, −24%). The gate review had named the two highest-authoring-volume WUs as the
  likeliest overruns; one of them came in 24% under, and the actual worst overrun was a WU
  nobody flagged because its body was short. Count the surfaces a WU must touch, not the
  words it must write.

- [FEAT-2026-0039/G2-CLOSE] When a feature's definition of done is an OPERATOR
  EXPERIENCE — an interactive skill, a CLI someone runs by hand, anything whose target is
  a different repository — pre-declare `met_locally` as the ceiling in `PLAN.md` at draft
  time instead of discovering it at the arming review and confirming it at the close. A
  dispatched session has neither a human channel nor access to a target repo, so no gate
  sizing fixes it: splitting the gate three ways produces three gates carrying the same
  deferral. Corollary for the deferred-list threshold (>2 entries or >30% of criteria
  flags gate sizing): when the deferrals share ONE structural root cause, say so and name
  the root cause rather than filing it as an oversized gate — the threshold is calibrated
  for "this gate tried to do too much," and mis-attributing a structural limit to gate
  sizing sends the next plan to fix the wrong thing.

- [FEAT-2026-0039/G2-CLOSE] An acceptance criterion naming a test runner the repo does not
  have installed is not an oracle, and it fails silently. Six criteria across four WUs of
  this feature specified `python3 -m pytest <module>` in a repo whose `tests` gate is
  `python3 -m unittest discover` and whose venv has no pytest. Every one of them "passed"
  because the underlying `unittest` bodies run under the gate — so nobody has ever
  executed those criteria as written, and the close could only satisfy them by
  substituting a different runner. Before writing a command into a criterion, confirm it
  is the command the project's own `verification.yml` gate actually runs, or that it is
  installed; a criterion that cannot be executed verbatim is prose.

- [FEAT-2026-0069/G1-CLOSE-INTERMEDIATE] For any breaking change to a schema this repo's
  own gates validate, **expand → migrate → contract is the named default ordering — and
  the migrate step's acceptance criterion must be a tree-wide completeness command
  asserted at zero hits, never a prose enumeration of surfaces.** Flip-first is not merely
  risky, it is unsatisfiable by construction: the shipped example is validated by a `code`
  gate, so tightening the validator before migrating turns the gate red on a correct tree,
  and under FEAT-2026-0051's preflight baseline probe a red base gate halts the run before
  any WU dispatches. Every intermediate state must be independently green, because the
  driver squashes each WU with the full gate set required to pass. The ordering alone is
  not enough: this gate got the ordering right and still lost its only $5.26 to a migrate
  WU whose criterion tested "a component with the new field exists and validates" (a
  sample) where the flip needed "no non-conforming instance remains anywhere" (a sweep).
  It passed every criterion it carried, so no driver guard could catch it — a
  correctly-scoped WU and an under-scoped one are indistinguishable from outside. The flip
  WU then inherited a non-conforming tree, burned three attempts and a
  `spinning_signature_repeat` escalation, and the hygiene WU written with the sweep
  criterion passed first attempt for $0.83. Same failure as [FEAT-2026-0039/T04]
  (hand-written fan-out lists reproduce the author's blind spots) one level up, at the
  criterion rather than the body.

- [FEAT-2026-0069/G1-CLOSE-INTERMEDIATE] **A fixture that cannot express the bug class it
  guards is an authoring defect, and it is detectable at authoring time.** Ask of every
  fixture: what is the cardinality of the thing this is meant to catch, and does the
  fixture carry more than one of it? FEAT-2026-0039's discovery fixture had one trigger per
  deployable, so it structurally could not express the N-triggers-per-deployable failure —
  and the gap surfaced only on a real repo, twice, across two features. A fixture with
  cardinality 1 where the failure needs N is not a small fixture, it is a fixture testing a
  different question. When a WU's `produces:` includes a fixture, the acceptance criterion
  should name the cardinality the fixture must carry.

- [FEAT-2026-0069/G1-CLOSE-INTERMEDIATE] **A gate's definition of done must be decidable by
  that gate.** This gate carried a clause asserting a property of an artifact in a
  different, unwritten feature ("FEAT-2026-0040's adapter interface has a machine-checkable
  answer to X"), which is undecidable here and lands in the deferred-verification list as
  an entry no gate sizing can remove. Recast to what the gate actually proves ("the schema
  expresses and the validator enforces X") it is decidable, and the cross-feature intent
  survives as a binding constraint recorded in PLAN.md and the roadmap — which is where a
  claim about another feature belongs.

- [FEAT-2026-0069/G1-CLOSE-INTERMEDIATE] **A close reporting a gate-set result must state
  which sandbox each gate ran under.** Three of this repo's ten `code` gates are `bats`
  suites whose `setup` calls `mktemp -d`; under the agent session's default sandbox that
  returns `Operation not permitted` and all thirteen cases fail before a single assertion
  runs. Re-run with the sandbox disabled they are green. A close that reported "7/10" would
  have reported the sandbox and manufactured a regression. Cheap to say, and it is the
  difference between an oracle and a number. The consumer-side complement of
  [FEAT-2026-0029/G1-CLOSE], which covers the authoring side (name the tmp-dir constraint
  in the WU spec so an implementation WU doesn't spend its spinning budget rediscovering
  the denial); this one binds every close that re-runs oracles under §1.

- [FEAT-2026-0069/G1-CLOSE-INTERMEDIATE] **Do not measure a gate against a plan that was
  re-based onto its own failure.** When a WU is inserted mid-gate in response to a miss,
  the gate's planned cost rises by that WU's estimate, and reconciling actual spend against
  the *re-planned* figure reports the miss as estimating accuracy — here, a +8.6% overrun
  against the as-drafted $11.00 became a −8.1% "underrun" against the re-planned $13.00.
  Report both, and name the as-drafted figure as the honest one. Corollary: a gate whose
  WUs all come in 39–75% under except one 155% overrun did not overrun on estimation, it
  overran on one defect — say which, and price the defect rather than the estimate.

- [FEAT-2026-0069/GATE-1-ARM] **`planning-discipline.md` §5's flat $5.00 planning floor is
  wrong for `plan-next` specifically, and the error is large enough to invert a feature's
  cost verdict.** Two independent datasets now agree, and they separate cleanly by WU type
  rather than by feature:

  | WU type | observed actuals | §5 floor |
  |---|---|---|
  | `plan-next` | $15.65 (FEAT-2026-0049), **$16.44** (FEAT-2026-0069/G1-PLAN, 2 attempts) | $5.00 |
  | `close-intermediate` | $5.67 (FEAT-2026-0049), **$10.01** (FEAT-2026-0069, 2 attempts) | $5.00 |

  FEAT-2026-0069's gate 1 shows the consequence in isolation, because its substantive
  estimating was good: substantive WUs came in at **$11.94 against $11.00 planned (+8.6%,
  four of five under)**, while the two closing WUs came in at **$26.45 against $10.00
  (+165%)**. Gate 1 alone therefore cost **$38.39** against a **$34.00 whole-feature** plan
  — the feature reads as a 63% overrun caused entirely by a rule-supplied constant, not by
  anything the planner judged.

  Three rules follow. **(a)** Draft `plan-next` at a floor of **$12.00** and `close` /
  `close-intermediate` at **$8.00** until more data lands; the flat $5.00 is a floor for the
  cheapest observed case, never an expectation. **(b)** A gate's `cost_budget_usd` must be
  set against those figures plus one re-attempt of its largest WU — a budget summed from
  $5.00 planning estimates is the brake §5 already warns fires by construction, and it now
  has a second dataset. **(c)** When a feature's overrun traces to a floor the rules
  supplied rather than to a judgement the author made, the retrospective must say so and
  propose the floor revision. Otherwise the signal is recorded as "this feature overran"
  and the constant survives to mis-price the next one. This entry exists because
  FEAT-2026-0049 produced the same evidence and it was recorded as provenance for the
  $5.00 floor rather than as a reason to move it. Tracked as issue #260.

- [FEAT-2026-0069/G2-CLOSE] **The expensive `plan-next` bought the cheap gate — raise the
  §5 floor because planning costs that much and is worth it, not because planning is
  wasteful.** This is the counter-evidence that keeps [FEAT-2026-0069/GATE-1-ARM]'s floor
  revision from inviting the wrong correction. `G1-PLAN` cost **$16.44** against a $5.00
  floor, and its §4 runtime probe applied the re-key locally, ran the full 1473-test
  oracle twice, and pasted the resulting four-failure list **verbatim into the WU body**.
  The result, same feature and same author: gate 1, planned without a probe for its own
  WUs, ran **5 WUs / 8 attempts / 3 failures / 1 escalation, $11.94**; gate 2, whose
  hardest WU was handed an enumerated failure list, ran **4 WUs / 4 attempts / 0 failures,
  $4.43 against $12.00 (−63%)** — and the WU flagged most likely to need a second pass
  passed first try for $1.25. A revision framed as "planning WUs overspend" invites cheaper
  probes and costs the next feature a gate. Two riders on the floor itself: **(a)** both of
  this feature's overrunning closing WUs were **two-attempt** WUs whose first attempt was
  `closing_deliverable_missing` ($4.45+$5.57 and $8.61+$7.83) — roughly half the spend went
  to an attempt the driver refused, so the $5.00 floor is priced as if closing WUs pass
  first try, and neither did; **(b)** the rule change must reach
  `.specfuse/templates/WU.template.md` (which quotes the flat $5.00 verbatim at `:31-32`)
  and not only `planning-discipline.md` §5 — the template is the surface a drafting agent
  actually reads. Third dataset for issue #260: `plan-next` $16.44, `close-intermediate`
  $10.01.

- [FEAT-2026-0069/G2-CLOSE] **A grep-based acceptance criterion asserting a symbol's
  absence must anchor on the definition or use a word boundary — a bare substring grep is
  evidence of neither presence nor absence.** A WU asserted
  `grep -c "_with_subscriptions" <file>` returns `0`. Re-run fresh at the close it returned
  **`1`**, with the deliverable fully met: the hit was a substring inside the method name
  `test_message_consuming_with_subscriptions_emits_one_target_per_entry`, added by a *later
  WU in the same gate*. A close re-running the criterion literally would have escalated a
  naming coincidence. The mirror failure is worse and silent — the same criterion returns
  `0` if the symbol is **renamed** rather than deleted. Write
  `grep -c "def <symbol>"` or `grep -cE "\b<symbol>\b"`, and say which property is being
  asserted. Same family as [FEAT-2026-0039/G2-CLOSE] (a criterion naming a test runner the
  repo does not have): a command written into a criterion is an oracle only if it measures
  the thing the sentence claims. Corollary for closes: when a fresh re-run disagrees with a
  criterion, diagnose the *command* before escalating the *work* — the disagreement is as
  likely to be in the wording as in the tree.

- [FEAT-2026-0069/G2-CLOSE] **Any test whose assertion is a relation between two derived
  collections is vacuously true on empty inputs and must assert non-emptiness first.**
  Equal lengths, disjoint sets, stable ordering, round-trip identity — `len([]) == len([])`,
  `sorted([]) == sorted([])`, and two empty sets are disjoint. Two of this feature's
  provider-neutrality boundary tests — the ones guarding the property the whole feature
  exists to protect — passed against a discovery function returning **zero** components,
  and no gate could see it: the tests do real work and their assertions are real, they are
  just true of nothing. This is not the hollow-pass shape the driver already guards
  ([FEAT-2026-0022/G1-CLOSE]); it is a *vacuous-truth* shape and needs a different check.
  It was found only because a runtime probe's **passes** were read as carefully as its
  failures. Worth a sweep across a repo's boundary tests, not just the module that
  surfaced it.

- [FEAT-2026-0069/G2-CLOSE] **When a gate's definition of done is written in terms of a
  skill but its oracle is a test-local reference implementation, the gap between them is a
  real deferral — name it, or the green reads as "the skill is proven".** Gate 2's DoD said
  *"`/derive-monitoring`, run against a repo whose single deployable carries N triggers,
  emits 1 component with N targets"*. What the oracles prove is that the reference
  algorithm does (fresh, exit 0) and that the skill's prose describes that algorithm
  (fresh, exit 0). No test in the repo composes them, so "an agent following the prose
  reproduces the result on an unseen tree" is unverified. This is not pedantry: it is the
  exact gap that *created* this feature — FEAT-2026-0039's gates were green and its skill
  still emitted 30 components on its first real repo, because a passing fixture and an
  agent-executed skill are different oracles. Two fixes, and both are cheap. **Write the
  DoD as what the gate can decide** (the algorithm yields X, the prose describes it), so
  the wording artifact disappears and only the genuine gap remains; and **schedule the
  genuine gap as one named post-merge operator run against a named real repo** — several
  such deferrals usually collapse into a single run. Extends
  [FEAT-2026-0069/G1-CLOSE-INTERMEDIATE] (a gate's DoD must be decidable by that gate) from
  cross-*feature* claims to cross-*surface* ones.

- [FEAT-2026-0069/G2-CLOSE] **Reject a schema position while it is still unreleased; that
  window is the only time the conservative direction is free.** Gate 1 shipped `invariant`
  permitting `targets` by fall-through — absent from both lookup tables, decided by nobody.
  Gate 2 rejected it for $0.86, on the reasoning that `invariant` already carries
  `fingerprint_by` as its required enumeration key and permitting both would hand the
  downstream fingerprint model two competing keys with nothing in the schema saying which
  wins. The move was free **only because the permissive position had never been merged or
  released**, so no consumer had seen it; the same rejection after a release is a breaking
  change. The asymmetry is the rule: a rejected field can be permitted later without
  breaking anyone, and the reverse cannot. So when a close's contract-change table surfaces
  a position *"never an explicit decision"*, route it to the next gate rather than the next
  feature — the cost of deciding rises discontinuously at release, and an undecided
  fall-through is something a terminal close has to report as an open schema position
  either way.

- [FEAT-2026-0070/G1-CLOSE-INTERMEDIATE] **"Exactly one writer" is a property of the
  surface, not of the function — audit it by grepping the writes, in both directions, not
  the definition.** `[FEAT-2026-0023/G1-CLOSE]` requires terminal-state flips to have ONE
  driver-side owner, and the natural audit — `grep -c "def fire_terminal_flips"` returns
  `1` — proves only that the owner is not duplicated. Aiming the grep at each *surface*
  instead (`write_frontmatter_field(... "status" ...)`, `roadmap_path.write_text`, every
  `set_gate` call site and the value it passes) took the same minute and found
  `loop.py:4462`, which writes `PLAN.md` `status: complete` on the all-gates-passed poll —
  a value absent from `lint_plan.VALID_FEATURE_STATUS`, so re-running the driver on a
  finished feature overwrites the `done` the owner just wrote with a value plan-lint
  rejects and `/wrap-feature` refuses. No gate test could have caught it: tests assert what
  the owner *does*, never what else touches the bytes it owns. Rule: a one-owner audit
  enumerates writers of the surface and classifies each (owner / deliberate inverse /
  defect), and it must cover the reverse transition too — this repo's
  `revert_terminal_surfaces` is a legitimate second writer of the same bytes in the
  `done → active` direction, so an audit phrased as "nothing else writes these bytes" is
  unsatisfiable and will be quietly downgraded to the definition-count check that finds
  nothing.

- [FEAT-2026-0070/G1-CLOSE-INTERMEDIATE] **A skill may not own a state transition the
  driver owns: the driver exposes an entry point, the skill calls it, and the skill's
  *non*-writing is enforced by a grep-shaped test over the skill text with a positive
  control.** `[FEAT-2026-0023/G1-CLOSE]` established one owner across *close paths*; the
  operator-skill surface is the same hazard with a friendlier name, because a skill that
  hand-edits three files is indistinguishable in its effect from the divergence that cost
  issue #49. The shape that worked: order the WUs so the driver primitive lands first
  (`recheck_terminal_verdict` + a `--recheck-verdict` flag), then build the skill on it;
  state the prohibition in the skill text; and assert it as a **grep over SKILL.md** —
  never as prose in the WU body, which verifies nothing. The non-obvious half is the
  positive control: also assert the forbidden pattern *fires* on a purpose-built
  violating instruction, or the guard passes because its regex matches nothing rather than
  because the skill is clean. Corollary for planners: "skill needs a state transition" is
  always two WUs, and the primitive is the first one.

- [FEAT-2026-0070/G1-CLOSE-INTERMEDIATE] **When a contract is enforced at two moments, the
  earlier enforcer must either explain the later one's requirement or exempt the states
  the later one owns — otherwise it fails on the right tree with the wrong message.** One
  defect class, three incidents: `lint_plan`'s close-WU verdict check omitted
  `in_progress`/`in_review` from its exempt set, so a close WU mid-dispatch failed
  plan-lint with a message about the WU rather than about the missing verdict, while the
  real owner (`assert_verdict_well_formed`) runs at outcome time (this gate's T04);
  closing-guard literals were enforced in `loop.py`'s `assert_*` functions and documented
  nowhere, discoverable only by paying for a refusal (#265); and the outcome contract was
  enforced against a rule generalised from one feature with no surface explaining the
  population it came from (#272). The fix in each case is not more strictness — it is
  making the *earlier* enforcement point name the later one. Two questions at authoring
  time close the class: which other surface enforces this contract, and at what moment?
  If the answer is "a later one", the earlier check exempts the states that later one owns
  and its comment names it.

- [FEAT-2026-0070/G1-CLOSE-INTERMEDIATE] **An attempt killed before it reaches an outcome
  is invisible to every cost consumer — a close reconciling spend from `events.jsonl`
  reports a lower bound and must say so.** Cost lands in `events.jsonl` at
  `attempt_outcome`/`task_completed` time, so an infra kill, a Ctrl-C, or an OOM mid-attempt
  leaves the tokens spent and nothing recorded — and a recovery that resets the WU makes
  the run look clean in the record while the operator remembers otherwise. This gate's T03
  was killed mid-attempt and recovered; `events.jsonl` shows `attempts: 1, outcome:
  passed` and no trace of the cost. Every downstream consumer inherits the understatement:
  the close's cost analysis, `events_stats.py`'s medians, `/learnings-suggest`'s failure
  clusters. Rule: a close states its actual as a lower bound and names the killed attempts
  it knows about (a recovery commit in the gate's history is the usual evidence); and a
  failure-class breakdown reporting zero driver-recorded failures should say *recorded*
  rather than claiming every WU passed first try.

- [FEAT-2026-0070/G1-CLOSE-INTERMEDIATE] **An acceptance record that overwrites the field
  it records leaves no machine-readable trace of what was accepted — carry the
  accepted-from value forward in frontmatter.** `/accept-hedged-close` writes an auditable
  acceptance record and then, correctly, sets the close WU's `verdict` to `met` so the
  driver's one owner recognizes it (`verdict_permits_terminal_flips` is `met`-only, and
  broadening *it* would have been the worse fix). The cost: after acceptance the
  frontmatter is byte-identical to a close that genuinely met every criterion, and the
  hedge survives only in prose that nothing parses. Whenever an operator override mutates
  the very field that recorded the pre-override state, write the provenance alongside it —
  `verdict_accepted_from`, `_reason`, `_at` — so "met" and "hedged, accepted on a stated
  reason with follow-ups open" stay distinguishable to a query, not just to a reader.

- [FEAT-2026-0070/G2-CLOSE] **A machine-readable marker embedded in a prose artifact is
  forgeable by the prose that documents it — scope the scan, or make the token
  unquotable.** This gate shipped an auto-close debt marker written into `RETROSPECTIVE.md`
  and a guard that scans for it. The scan is plain text over the whole file with no
  awareness of code fences, so a retrospective that *quotes* the marker with a real gate
  number manufactures debt it must then reconcile. Observed, not reasoned: copying this
  feature's directory, appending the marker literal inside a fenced block, and running the
  guard returned `ok=False` with `autoclose_debt_unreconciled`. The population most likely
  to write that literal is exactly the one documenting the feature that ships it — the
  close, the migration note, the rule file's own example. The general rule: whenever a
  scanner's input is an artifact humans write prose into, the token it looks for must be
  either positionally constrained (first line of a named section), fence-aware, or
  unreproducible by quotation. "No one would write that string by accident" is false for
  precisely the readers who most need the feature explained.

- [FEAT-2026-0070/G2-CLOSE] **Cost variance tracks how many distinct things a work unit
  must prove, not whether its test file already exists.** Paired observation across one
  feature's two gates. Gate 1 came in **53.5% under** plan and concluded that a WU
  extending an existing guard test file is *cheaper*, not dearer, than the plan's premium
  for "touches driver internals". Gate 2 priced all four of its WUs on that lesson — all
  four extend existing test files — and came in **19.7% over**, with the deltas monotone in
  acceptance-criterion count (7 ACs −38.5%, 10 ACs −16.9%, 12 ACs +46.1%, 13 ACs +37.4%).
  The mechanism is legible without the statistics: the two overrunning WUs owed three named
  control tests, a registration-order assertion, a documentation row bound by a contract
  test, a tree-wide satisfiability re-probe, three degrade cases, and a truncation case —
  each a separate deliverable with its own oracle. Estimate by counting the distinct
  obligations and controls; treat "extends an existing test file" as a modifier on that
  count, not as the variable. A calibration lesson drawn from one gate's uniform miss is a
  hypothesis, and the next gate is its test — say so when promoting one.

- [FEAT-2026-0070/G2-CLOSE] **An arm-time reprice silently invalidates the close's
  as-drafted baseline whenever the resulting delta sits under the linter's threshold — a
  noise threshold is also an audit blind spot.** The gate-2 arming record reconciled the WU
  sum to `PLAN.md`'s `planned_cost_usd` at a delta of exactly $0.00. The operator then
  accepted a scope question at arming, repriced one WU $2.00 → $2.50, and nothing
  re-reconciled: plan-lint's cost-delta check warns above 10% and the drift was 1.5%. The
  terminal close discovered it by re-summing the frontmatter rather than reading the arming
  record. Two fixes, either sufficient: the arming step re-runs the sum and updates the
  record it just invalidated, or the linter reports the delta informationally at any
  magnitude and reserves the threshold for the WARN. Generally — when a check suppresses
  small deltas to avoid noise, something else must still record them, or "reconciles
  exactly" decays into "reconciled exactly, once, before the edits".

- [FEAT-2026-0070/G2-CLOSE] **A marker-gated guard that reports zero across all history is
  untested end-to-end by construction, and the close that ships it must not count its own
  vacuous pass as evidence.** The narrowing that makes such a guard *satisfiable* — only
  gates marked by the new writer count as debt — is the same property that makes it inert
  on every artifact that exists, so its first real firing is necessarily in someone else's
  future run. The terminal close of the feature that ships it will see the guard pass
  against itself and must say plainly that the pass is vacuous: no marker existed, the
  predecessor set was empty, the function short-circuited before evaluating anything. The
  real evidence is the negative control, the positive control, the no-marker control, and —
  cheapest of the missing pieces — one lifecycle test that lets the driver actually produce
  the marker and then dispatches the close that must read it. Unit fixtures prove the
  function; only a real sequence proves the guard. A green post-pass reported without that
  distinction is the hollow pass the guards exist to catch, one level up.

- [FEAT-2026-0046/G1-CLOSE] **A criterion that mandates a stub does not defer the
  integration risk — it removes it from the WU's scope, and the estimate must stop paying
  for it.** The WU that files GitHub issues was the gate's most expensive at $3.50, priced
  for the risk of discovering `gh` search and create syntax against a live API. Its own
  criterion 9 then forbade invoking the real `gh` binary, so that discovery never happened
  and the unit landed 80.5% under; the whole gate, uniformly stub-scoped, came in 73.4%
  under. Two rules follow, and the second matters more. **Pricing:** when a WU's criteria
  require an injected runner or fixture in place of the external system, price the unit for
  wiring a seam, not for negotiating with the system behind it. **Honesty:** a stub makes an
  unanswered question look answered, so the close must name what the stub declined to ask.
  Here the specific unknown is whether `gh issue list --search` matches an HTML comment —
  the idempotency key is `<!-- specfuse:escalation id=… -->`, and a search that returns
  nothing files a duplicate on every retry, defeating the one property the WU called
  load-bearing. That is invisible to a passing stub test and belongs in
  `## What the loop did NOT verify` with the exact re-run that settles it. Generally: pair
  every stub-mandating criterion with a named deferral in the close, or the gate's green is
  a statement about the seam and silently reads as a statement about the system.

- [FEAT-2026-0046/G1-CLOSE] **A close criterion that trips a threshold and then attributes a
  cause is asserting two things; the close must verify the attribution separately.** This
  gate's close carried a mechanical rule: more than two entries under
  `## What the loop did NOT verify` flags the feature's gate sizing. Four entries appeared
  and the flag fired correctly, but the attribution was wrong — every deferral traced to one
  declared scope boundary (no work unit touches live GitHub), which a two-gate split would
  have reproduced unchanged. What would actually have closed them is a different work unit,
  not a different gate count. A flag recorded without that check becomes evidence for a
  conclusion nobody tested, and the next planner reads "gate was too big" from a retrospective
  that never established it. Rule: when authoring a criterion of the form "if metric M exceeds
  N, flag cause C", require the close to state whether C actually explains the observation and
  to name the alternative if it does not. Thresholds are good at detecting; they are not
  evidence about why.

- [FEAT-2026-0071/G1-CLOSE] **An entry point that acquires its first subprocess or network
  call has made a consumer-visible contract change, even when its signature and return
  value are untouched.** `scaffold.init()` and `upgrade_specfuse()` were pure filesystem —
  that is why they worked offline, in CI containers, against non-GitHub remotes, and in
  directories that were not git repositories. Adding best-effort label provisioning kept the
  return type identical and could never fail the command, so the diff reads as purely
  additive; but consumers inherit new latency, new stderr, and outbound network calls in
  environments where "filesystem only" may have been an audited property. Rule: when a WU
  puts the first shell-out on a previously pure path, the close enumerates it as the
  headline contract change and the plan ships an opt-out in the same gate — never-fatal is
  a mitigation, not a reason to omit it from the list. Corollary observed here: because the
  wiring uses the real default runner, the pre-existing regression suites silently become
  live-binary probes, so budget for what a real invocation does in a test tmpdir.

- [FEAT-2026-0071/G1-CLOSE] **A registry that imports its vocabulary from consumer modules
  guards the names and nothing else — say so, or the drift test reads as broader than it
  is.** The label registry took its seven names from `escalation.py` and `gh_features.py`
  rather than retyping them, and a coverage test recomputes the set at test time, so a name
  added to a consumer without a registry entry fails. That is genuinely structural. But the
  colours and descriptions beside each name remain hand-kept literals with no upstream
  owner, and no test can detect them drifting from what the operator actually wants. Rule:
  when a WU claims a registry "cannot drift", the close states which fields the guard
  covers and which are unguarded by construction. A partial structural guard described as a
  total one is how the unguarded fields stop being reviewed.

- [FEAT-2026-0071/G1-CLOSE] **When a plan's scope boundary rejects an interface the roadmap
  already promised, correct the roadmap at the decision, not at the close.** The roadmap
  detail section said "`--no-labels` opts out" while `PLAN.md`, written for the same
  feature, had ruled a CLI flag out of scope in favour of an environment variable — because
  the flag lives in a different repository and would need a coordinated release. The two
  documents disagreed from day one and shipped that way; the close had to carry the
  mismatch as a deferral entry. The roadmap is the surface a consumer reads to learn what
  exists. Rule: a scope decision that changes the shipped interface is a roadmap edit in the
  planning WU that makes it, and any close that finds roadmap prose describing an interface
  that was never built records it under `## What the loop did NOT verify` rather than
  quietly rewriting it as though it had always matched.

- [FEAT-2026-0072/G1-CLOSE] **A new check added to a tree-walking linter is only "swept
  clean" for inputs the walk actually reached; a non-zero exit from an unrelated crash is
  not a result for the new check.** T03's criterion 11 required zero findings across every
  directory under `.specfuse/features/` — a deliberate sweep-not-a-sample, and the right
  call. The sweep returned 38 clean and one exit-1, and the exit-1 was a pre-existing
  unhandled `MiniYAMLError` in `read_frontmatter` on a feature whose work-unit files had
  lost their closing `---` fence. Because the new check is called *after* the work-unit loop
  that raised, it never ran for that feature at all. The tempting readings are both wrong:
  "38 of 39 clean" understates it, and "one failure, unrelated, ignore it" silently drops an
  input from the sweep the criterion said was total. Rule: when a WU adds a check to a
  linter that iterates over many inputs, the close's sweep must classify every non-zero exit
  as *this check fired* or *this check never ran*, and for the second class call the check
  function directly on that input rather than inferring the result. Corollary for linter
  authors: a validator that aborts the whole run on one malformed input cannot report on
  anything after the abort point, and its exit code cannot distinguish "found a problem"
  from "could not look" — that is its own defect, and a sweep is where it surfaces.

- [FEAT-2026-0072/G1-CLOSE] **An opt-out list for a new blocking check must live where the
  consumer can edit it, or the check is not adoptable — and the close must say which.**
  T03 shipped `DONE_FEATURE_GATE_EXCLUSIONS` as a module-level constant in
  `specfuse/loop/lint_plan.py`, with two entries whose inline reasons are genuinely
  load-bearing (without them the check fires on a bundled fixture, and the likely "fix" is
  someone mutating a shipped fixture to satisfy a linter). That is right for the repo that
  owns the file and wrong for every project that vendors it: a downstream project with an
  equally legitimate exclusion must patch vendored driver source, which the next upgrade
  erases. Rule: when a WU introduces a blocking check whose correctness depends on an
  exclusion list, the plan decides at draft time whether the list is a fact about *this*
  repo's history (constant is fine) or a fact about *any* consumer's tree (it belongs in
  project-local configuration), and the close enumerates the placement as part of the
  consumer-visible contract-change list. A blocking check plus an unreachable opt-out is a
  breaking change with no remedy, which reads as an additive diff.

- [FEAT-2026-0072/G1-CLOSE] **When a WU ships a fix for drift that has already been
  reconciled, the fix's active code path is unreachable on the correct tree — the close
  records it as unexercised rather than reading the green guard as coverage.** T02 taught
  `sync-scaffold.sh` to create missing `.claude/skills/` forward symlinks, but the four
  missing links had been restored by hand in a prior PR, so on the live tree all 23 links
  exist and the script reports "no missing links" — the create-branch never runs. Its four
  behavioural criteria are green, and green only against a bats fixture tree with
  `REPO_ROOT` overridden to a temp directory; the WU's own "Do not touch" correctly forbade
  manufacturing the gap on the real tree to exercise it. The guard test passing proves the
  *invariant* holds, not that the *repair* works where it matters. Rule: when a gate pairs
  "assert the invariant" with "reconcile the tree" and "automate the repair", the close
  states explicitly which of the three the real tree exercised, and gives the repair a
  natural-occurrence upgrade condition (here: the next skill added without a hand-made
  link) rather than counting the fixture run as verification on the live surface.

- [FEAT-2026-0072/G1-CLOSE] **A declared gate that needs a writable temp directory fails
  spuriously wherever the executor is sandboxed, and the failure is indistinguishable from
  a real one unless the close names the environment condition beside the exit code.** Both
  bats suites in this feature's gate set failed on first run with
  `mktemp: mkdtemp failed on …: Operation not permitted` — the sandbox denying temp-dir
  creation, not a defect in the script or the tests. Overriding `TMPDIR` did not help
  because bats resolves its own; the suites pass cleanly with the sandbox off, and reading
  the fixture first confirmed every path is rooted in `$TESTDIR` via a `REPO_ROOT` override
  so nothing in the real tree is touched. Rule: a WU whose verification shells out to
  `mktemp`, Docker, or any other privileged-ish primitive must name the environment
  precondition in its Verification section, and a close reporting such a failure must state
  whether it re-ran the oracle in a permitting environment and what it read to satisfy
  itself that doing so was safe. An exit code recorded without its environment is not
  evidence; it is a number that will be read as red by whoever sees it next — including the
  driver running the same gates.

- [FEAT-2026-0040/G2-CLOSE-INTERMEDIATE] **A completeness sweep whose file list is
  discovered by walking keeps being true as the gate writes new files; one scoped to a
  hand-written path tuple silently stops looking.** T04's tree-wide assertion ("no
  cron-carrying heartbeat target anywhere lacks a conforming dialect") enumerates its
  inputs via `git ls-files` rather than naming paths. When the close re-ran it, the sweep
  collected 14 targets across 4 files — but one of those files, `tests/test_heartbeat_adapter.py`,
  did not exist when T04 ran: T07 created it later in the same gate, and it carries the
  tree's only instance of the second dialect. A hand-written tuple would have gone on
  reporting "zero non-conforming" while never once looking at the file that exercises the
  case the enum was added for. Rule: a migrate-step criterion asserts over a **discovered**
  file set, and is paired with a non-vacuity assertion (collected count above a floor, plus
  named files that must appear) so "zero offenders" cannot be satisfied by an empty walk.
  Corollary for closes: re-run the sweep rather than inheriting the producing WU's pass —
  the tree it swept is not the tree at close time, and only the fresh run says which one
  the claim covers.

- [FEAT-2026-0040/G2-CLOSE-INTERMEDIATE] **A test fixture that builds a throwaway git repo
  must pin every commit-affecting setting, not just identity — otherwise it inherits the
  host operator's global config and fails for reasons that have nothing to do with the
  code under test.** `tests/test_autosync_no_cwd_leak.py` sets `user.name` and `user.email`
  on its temp repos and stops there, so each `git commit` inherited a global
  `commit.gpgsign = true` with `gpg.format = ssh`, and the signing agent socket is
  unreachable from a sandboxed session: `error: Couldn't get agent socket?` /
  `fatal: failed to write commit object`, exit 128, three errors in an otherwise green
  1753-test run. Confirmed by re-running the same module under
  `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false` → OK. This
  is a **different** failure from the already-recorded `mktemp`/sandbox one: that is the
  executor lacking a filesystem privilege, this is host configuration leaking into a
  fixture, and the two need different fixes. Rule: a fixture repo pins `commit.gpgsign`
  and `tag.gpgsign` to false alongside identity; and a close that meets a red gate checks
  whether the failing command reads *ambient host config* before recording the exit code
  as a regression.

- [FEAT-2026-0040/G2-CLOSE-INTERMEDIATE] **Do not re-price a gate off the previous gate's
  underrun when the two gates are made of different work; price the migration-and-severity-flip
  unit separately from the new-module units.** Gate 1's three units came in at $2.65
  against $9.50 (−72%), three for three, all first attempt, and the arming review faced an
  explicit temptation to scale gate 2's six units down by the same factor to roughly
  $10.00. It refused, on the stated grounds that gate 1's units were new modules with no
  tree to migrate, no severity flip, and no cross-file assertions to re-aim. Measured
  outcome: the three new-module adapter units did land near gate 1's shape (−62%, −70%,
  +9%), and **the one over-run was exactly the migration unit, at +39% ($4.50 → $6.25)**.
  On the scaled-down plan that unit would have carried ~$1.25 and the budget halt would
  have landed on the gate's first WU. Rule: an estimate is calibrated against work of the
  same *shape*, not the same feature; a WU that tightens a validator, migrates a tree, and
  re-aims existing assertions is a different distribution from a WU that adds a module, and
  a gate mixing both is priced per-unit rather than by one factor. A budget is a halt
  threshold, not a spend target — under-running it costs nothing, and a halt mid-gate costs
  the whole gate.

- [FEAT-2026-0040/G3-CLOSE] **A tree-wide sweep that walks `git ls-files` is blind to the
  new file of the WU that introduces it, so the offending WU always passes and the failure
  lands on whoever runs the suite next.** A gate-2 WU shipped a walk-discovered assertion
  over every tracked file; a gate-3 WU shipped a new YAML template that violates it. The
  gate-3 WU's own verification ran green, because at that moment its file was still
  **untracked** — the driver commits *after* the gate set passes, so a `git ls-files` walk
  cannot see the deliverable that made the WU dispatch. The file entered the walk's view
  only once the WU was `done`, and the failure surfaced two WUs later in the terminal
  close's fresh re-run. Rule: a sweep that discovers its own file list must walk the
  **working tree** (tracked plus untracked-not-ignored), not `git ls-files` alone —
  otherwise it structurally cannot fail on the change that introduces the violation. And
  the corollary for closes hardens from advice into a requirement: "the producing WU
  passed" is **no evidence at all** for a walk-discovered assertion, because that walk did
  not include the WU's own output. Re-run it at close time; that is the only run whose tree
  is the tree being shipped.

- [FEAT-2026-0040/G3-CLOSE] **A deliberately schema-agnostic structural predicate collides
  with foreign surfaces that happen to share its key, and the collision arrives exactly
  when the feature starts shipping its own config-shaped files.** The sweep above collects
  "every mapping carrying a `cron` key" — chosen on purpose, so a heartbeat target is found
  whether it lives in a shipped config, a discovery fixture, or a test assertion. Then the
  same feature shipped a CI workflow template whose `on.schedule` carries a `cron` the
  domain rule cannot possibly apply to: the required sibling field would make the workflow
  invalid. Both units were right by their own lights and the composite is red. Rule: scope
  a structural sweep by **where** a mapping lives (a named file set, or a required ancestor
  path such as `checks[].targets[]`), not by the bare presence of a key, and expect the
  first collision at the moment the feature ships YAML of its own. Reaching for a
  hand-written exclusion list instead is the regression the walk was built to prevent —
  fix the predicate, keep the walk and its non-vacuity floor.

- [FEAT-2026-0040/G3-CLOSE] **Gate padding sized as "one re-attempt of the largest WU"
  prices the retry at the drafted figure, which is the one number a retry disproves.** A
  gate drafted at $23.00 carried a $28.00 budget: $5.00 of padding for exactly one
  re-attempt of its $5.00 unit. That unit needed two failed attempts plus a re-arm and cost
  **$19.77 against $5.00 (+295%)**, while the gate's other three units all under-ran
  (−31% to −52%). The gate reached **97% of its halt threshold before the terminal close
  dispatched**. The failed attempts were not caused by that unit's difficulty at all — they
  died on a red base gate seeded by a *different, already-`done`* WU's test fixture, which
  no per-unit estimate can anticipate and no fresh session of the blocked unit could fix,
  because the offending file was outside its scope. Rule: when a WU fails on a base gate
  its own diff cannot clear, the driver-level response (escalate, fix out-of-band, re-arm)
  must be paired with a **budget re-baseline**, because attempts are billed and a re-arm
  restarts the attempt counter but not the spend. And padding is more honest as a
  proportion of the gate than as a copy of one unit's estimate: a retry costs what the
  retry costs, not what the plan hoped the unit would.

- [FEAT-2026-0054/G1-CLOSE] **When a contract gains an earlier enforcement moment, the
  *git state each moment reads* becomes part of the contract, and an equivalence test
  that does not reproduce the real dispatch ordering will report divergence that is not
  there.** A pre-squash lint necessarily inspects the **working tree**; the post-squash
  guard it mirrors inspects a **commit range**. They are the same check over two
  different views, so they are only comparable in the order a real attempt produces
  them: mutate the tree, lint the dirty tree, squash, then run the guard over
  `head_before..HEAD`. Two successive versions of this feature's end-to-end harness
  linted *after* committing, and both reported the lint refusing artifacts the guards
  accepted — a false divergence manufactured entirely by the harness, and one that on a
  worse day gets written up as the feature's core defect. Rule: an equivalence oracle
  between two enforcement moments must reproduce the sequencing of the real pipeline,
  not merely call both functions on the same directory; and it must assert agreement in
  **both** directions (approve/pass and refuse/refuse) on the same tree, because a lint
  that never approves and a lint that always approves both trivially "agree" with a
  guard on half the cases.

- [FEAT-2026-0054/G1-CLOSE] **Replacing a duplicated machine-detail table with a pointer
  removes the drift only if the pointer describes the mechanism's *trigger conditions*
  rather than the union of its branches.** This feature deleted a table of literal guard
  strings from a rule file precisely because a second copy of the requirements drifts —
  and the replacement sentence reintroduced the drift one layer up, promising that every
  closing work unit "starts its session with the guard-required files and headings
  already scaffolded in place" and naming five artifacts. Each stub is in fact
  conditional on WU type, on a next gate existing, or on parseable in-gate failures, and
  one of the five is never pre-created by design. For the most common shape — a terminal
  close on a clean gate — the mechanism creates nothing, which is exactly what happened
  on this feature's own close dispatch. Rule: prose that summarises a conditional
  mechanism must state when it fires, or make no coverage claim at all and defer to the
  checker ("run the lint to see what is still missing"). A best-case description is
  worse than no description, because it tells the reader they can skip the check.

- [FEAT-2026-0054/G1-CLOSE] **A guard scoped to "this gate" by parsing the gate out of a
  correlation ID silently exempts every ID shape the parser does not recognise — and the
  unrecognised shape is usually the common one.** The failure-class-breakdown guard
  restricts non-passing attempts to the current gate via a parser that matches only
  closing IDs of the form `G<n>-…`; an implementation-WU ID like `FEAT-2026-0054/T04`
  parses to nothing and is dropped. The consequence is that the retrospective section
  whose whole purpose is accounting for failed attempts cannot be required on a gate
  whose only failures were implementation work units — which is most gates. It fails
  open and silently: the guard and the skeleton writer read the same filter, so they
  stay consistent with each other while both under-fire, and no divergence test can see
  it. Rule: derive a work unit's gate from the plan's gate graph, which knows the
  answer, rather than from its ID's spelling; and when a guard is conditional on a
  derived scope, add a test that the guard actually FIRES for the common membership
  case, not only that it passes when satisfied.

- [FEAT-2026-0055/G1-CLOSE] **A rule that parses a document must be fixture-tested against the
  document shape the project's own template ships, not against a hand-written shape that happens
  to parse.** This feature's boundary check slices the `Do not touch` section with a helper that
  keeps only the lines *after* the heading line. That is correct for `## Do not touch` and wrong
  for `**Do not touch.** <content on the same line>` — the bold-preamble form used by 327 of 327
  work-unit bodies in this repo and prescribed by `WU.template.md`. Every fixture was authored in
  the ATX form, so the unit test suite was green while the rule could not fire on a single real
  work unit, and the motivating incident it was chartered on (FEAT-2026-0066/T04) would have
  armed clean. The sibling slicer for acceptance criteria already handles both forms, which is
  the tell: when two slicers over the same document disagree about what a section looks like, at
  least one of them is being tested against a shape nobody writes. Rule: for any rule whose input
  is a document, copy at least one fixture verbatim out of the shipped template, and reproduce
  the feature's motivating incident as a fixture asserting the rule FIRES — a paraphrase of "the
  T04 shape" satisfies the acceptance criterion and misses the defect.

- [FEAT-2026-0055/G1-CLOSE] **A cross-corpus sweep that a work unit's acceptance criteria require
  must be a driver-run gate, not an agent's self-reported observation.** The gate's definition of
  done required the new ERROR rule to report zero findings across every existing feature folder,
  and the producing work unit's criteria said "Any ERROR on an existing feature → stop,
  escalate". That unit reported `passed` on its first attempt. The close ran the same one-line
  sweep and found 15 ERRORs across 4 features — all false positives, all of which would have
  blocked arming on this repo's own work. A sweep is a single command with a countable output:
  the moment it is phrased as something an agent runs and describes, it is only as reliable as
  the agent's diligence on the attempt it was cheapest to skip. Rule: when a criterion is "rule R
  reports zero findings over corpus C", add it to `verification.yml` as a gate the driver
  executes, and treat any criterion whose evidence is a pasted command output as unverified until
  the close re-runs it.

- [FEAT-2026-0055/G1-CLOSE] **A rule that refuses work must fire only on certainty and degrade
  everything else to a warning — a rule that guesses is worse than the defect it hunts.** The
  boundary check's first shipped form matched `produces:` paths against every backtick token it
  found in a Do-not-touch section, which turned an allow-enumeration ("These files change: … and
  one new test file `tests/foo.py`") into a deny-list and read a semantic qualifier ("every
  *existing* `check_*` function") as a literal glob. The result was 15 refusals across 4
  legitimate features and zero on the deadlock it was chartered to catch. The fix was not a
  better guess: it was scoping extraction to prohibition clauses and routing anything the
  scoping could not classify to WARN, which took the tree to zero ERRORs while still surfacing
  four genuinely ambiguous boundaries as advisory findings a human can confirm at arm time.
  Rule: for any validation that can block work, split the outcome three ways — fire on an
  unambiguous violation, warn on a match the rule cannot classify, stay silent otherwise — and
  size the ERROR leg by what it can prove, not by what it can pattern-match. A false refusal
  costs a human's trust in the whole check; a WARN costs them ten seconds.

- [FEAT-2026-0055/G1-CLOSE] **A close whose gates pass but whose verdict is `not_met` is
  recorded as a passed attempt, so the rework it triggers is invisible to failure-class cost
  analysis.** Every `attempt_outcome` event in this feature carries `outcome: passed`,
  `failure_class: null`, `re_arm_count: 0` — and $11.08 of the $15.30 spent, 72% of the total,
  was a chartered repair work unit plus a discarded first close, both caused by a defect the
  first close found. Grouping portfolio spend by `failure_class` reports this feature as having
  cost nothing to rework. The under-run on the original implementation work (25% of estimate,
  four first-attempt passes) was the *signal* of the defect rather than a win: on a feature
  whose subject is rules that must actually fire, uniformly cheap first-attempt passes mean the
  gates are measuring the wrong thing. Rule: when reconciling planned against actual, count
  verdict-driven rework as its own line rather than letting it disappear into "passed" attempts,
  and treat a large uniform under-run on rule-authoring work as a prompt to check whether the
  rule has ever been observed firing on a real input.

- [FEAT-2026-0053/G1-CLOSE] **A work unit that wires new code into the driver cannot be
  verified by the driver run that wired it — so a gate whose definition of done asserts driver
  runtime behavior must name its observation point, and an absent signal must never be read as
  a false claim.** The driver imports `loop.py` once at process start. Edits a work unit lands
  mid-run are dead code for the remainder of that invocation, including for every closing unit
  that follows. Gate 1 wired two call sites into `run()` (a baseline write at first dispatch, an
  `arm_predicate_evaluated` emit at every `awaiting_review` flip) and neither could fire in the
  run that landed them: `PLAN.baseline.json` existed in 0 of 43 feature directories at close
  time, which is the corroborating tell that the running process predated the edit. The trap is
  not the deferral — it is the inference the gate file had already written down: *"No event =
  the claim is false — do not arm; escalate."* That reads a stale-process artifact as a defect
  and escalates a working mechanism. Rule: when a definition-of-done criterion asserts runtime
  behavior of the driver itself, write the observation point into the criterion at drafting
  ("verified at the next driver invocation", "verified by the human at the arming checkpoint"),
  and phrase any absence check to disambiguate first — did a process launched *after* the
  commit run this path? Only then is silence evidence.

- [FEAT-2026-0053/G1-CLOSE] **A reference snapshot captured at a lifecycle event is meaningless
  for the feature that installs the capture, because that feature is already past the event.**
  Gate 1 shipped an immutable `PLAN.baseline.json` written at a feature's first dispatch, so
  that later gates can measure plan drift against the as-activated graph. This feature's own
  first dispatch happened hours before the call site existed, so its baseline will instead be
  written at the next driver invocation — from a PLAN.md that by then contains the next gate's
  drafted work units. The graph recorded as "as-activated" will be the post-drift graph, the
  drift classes will report clean, and the report will mean nothing. Write-once immutability
  makes this permanent rather than self-correcting: the very property that stops drift
  detection being gamed also freezes the wrong reference in place. Rule: for any mechanism
  whose reference state is captured at a lifecycle event, check at close time whether the
  installing feature is already past that event; if it is, say so explicitly in the
  retrospective and forbid the successor gate from treating the installing feature's own
  snapshot as evidence the mechanism works. The first honest test is the first feature that
  starts after the mechanism merges.

- [FEAT-2026-0053/G1-CLOSE] **Sweep a new predicate over the whole real corpus at close, and
  read a uniformly not-evaluable result as an unproven approval path rather than a pass.**
  Running the new arm predicate over all 43 real feature directories cost one command and
  returned `would_arm: False` with every class `not_evaluable: no_baseline` on 43 of 43 — the
  designed fail-closed behavior, confirmed at scale instead of on fixtures, and worth having.
  But green-on-fixtures plus refuses-everything-on-real-input is precisely the evidence shape
  that hid FEAT-2026-0055's defect, where a document-parsing rule passed every hand-authored
  fixture and could not fire on a single real work unit. A refusal path proven on the corpus
  says nothing about the approval path, and the approval path is the one that will meet real
  frontmatter, real `events.jsonl`, and a real review file for the first time in production.
  Rule: run the sweep, record the counts, and when the corpus is uniformly not-evaluable, name
  the approval path as unverified in `## What the loop did NOT verify` and carry it into the
  successor gate's risk list — do not let "no findings across the corpus" read as coverage.

- [FEAT-2026-0053/G2-CLOSE] **A work unit that introduces a validation rule must be drafted
  against the fixtures that already exist, not only against real inputs — a sibling work unit's
  test fixture is an input too, and it is the one the gate actually runs against.** A WU added a
  new veto class requiring `planned_cost_usd` on every drafted work unit. The preceding WU's
  test fixture builder, written before that class existed, emitted frontmatter without the
  field. The new class therefore vetoed its sibling's fixture, and the failure surfaced as the
  *sibling's* test failing under a whole-suite signature — in a file the new WU's Do-not-touch
  clause forbade it to open. Three fresh sessions across two dispatch cycles each re-derived the
  same wrong hypothesis, because the evidence available to them was identical and pointed
  nowhere near a fixture builder; the driver escalated `spinning_signature_repeat` at $5.01 and
  774 seconds, and the fix was one field in one fixture. Note that the WU's satisfiability
  answer under `planning-discipline.md` §2 was present and correct — it reasoned about real
  inputs in their intended final state, which is what §2 asks for, and real inputs were never
  the problem. Rule: when a WU adds a rule that reads artifact X, grep the repo for existing
  fixtures that *produce* X and either confirm they satisfy the new rule or write the fixture
  amendment into the WU's scope at drafting time. Related: work units that touch disjoint source
  surfaces are not thereby independent — check fixture overlap before declaring them so.

- [FEAT-2026-0053/G2-CLOSE] **A cost or usage aggregate that reads a per-cycle field silently
  under-counts every re-armed unit, and the error concentrates in exactly the work the aggregate
  exists to catch.** A feature-level budget predicate summed each work unit's `cost_usd`. That
  field is per-dispatch-cycle: the driver's re-arm fold moves the prior cycle's spend into
  `cumulative_cost_usd` and zeroes it, and the operator re-arm path zeroes it while recording the
  prior spend only in `re_arm_history[].prior_cost_usd`. Reconciling the predicate against
  `events.jsonl` at close found it reading $35.89 of a true $42.12 — 14.8% low, all of it the
  two re-armed units, i.e. precisely the over-budget work a budget brake is for. A sibling
  aggregate that had already been fixed for the fold path (#199) was still blind to the operator
  path, because that path zeroes without folding, so the guard `cost_usd == 0 means already
  folded` reads a never-folded unit as a folded one. Rule: any aggregate over per-attempt cost,
  duration, or token counts must sum every field the lifetime is spread across — and a close
  reconciling planned against actual should compute the same total from `events.jsonl` and
  compare, because the event log is the only surface that never loses a cycle.

- [FEAT-2026-0053/G2-CLOSE] **An accumulation artifact with no reader delivers none of the
  value it was built to preserve — the gate that builds the writer must name the consumer or
  record a deferral with a home.** A feature whose whole premise was replacing four human gate
  reads with one PR read shipped, tested end to end, the mechanism that accumulates each
  unread gate's doubt into a feature-local review file. Nothing reads that file: a grep across
  every skill and every shipped template returned zero references outside the module that
  writes it and its own tests. Every acceptance criterion passed and the gate's definition of
  done was satisfied as written, because the criteria were scoped to accumulation. The
  checkpoint value the feature exists to preserve is nonetheless not delivered, and no gate
  owns the last hop. The shape is easy to miss precisely because writer-side tests are the
  natural ones to write and they all go green. Rule: when a gate ships a write-side mechanism
  whose purpose is to inform a later human or machine read, its definition of done must name
  the reading surface — or the close must enumerate the missing hop in `## What the loop did
  NOT verify` and hand it to the planning WU with a decision to make, rather than let a green
  gate imply an end-to-end path.

- [FEAT-2026-0053/G3-CLOSE] **A path-prefix approximation that is sound as a safety property
  can still make the feature's headline case unreachable, and "accepted v1 limit" in the docs
  is not the same as saying so.** An arming predicate refused to auto-arm any gate whose
  drafted work units produce a path under the driver package prefix — the rule that stops a
  work unit editing its own judge. Every documentation file in the repo is also mirrored into
  that package as shipped data, so the prefix test could not tell a mirrored doc from a change
  to the predicate itself, and *any* gate shipping documentation fired the class. It was
  predicted at arming, accepted as a v1 approximation, and documented with the correct clearing
  action ("the human arms it; do not patch the predicate"). All of that was right and none of
  it changed the consequence: the most probable first encounter an operator has with the new
  autonomy mode is it refusing to arm, for a path-prefix artifact rather than a hazard, on a
  feature whose whole premise is fewer human stops. Rule: when a known approximation blocks the
  *typical* case rather than an edge case, the close must state the reachability consequence in
  the verdict — not only the class, its clearing action, and the fact that it was accepted.
  Naming the limit in a reference page tells an operator what happened; only the verdict tells
  the person deciding whether to adopt it that the headline number is currently out of reach.

- [FEAT-2026-0053/G3-CLOSE] **A definition-of-done criterion must name the surface that
  *enforces* a property, not the one that *declares* it — a contract spread across registries
  that do not reference each other is satisfied exactly and still fails.** A work unit shipping
  a new documentation page had an acceptance criterion naming the drift guard's tracked-file
  set by variable and file. Three further test files each carried an independent copy of the
  same shipped-file list, and none of the four referenced the others. The first attempt did
  precisely what the criterion said, registered the page in the one named registry, and the
  suite refused it. Cost was one cheap attempt, and only because the assertion named the
  missing path directly — the same shape surfacing in a sibling work unit's fixture cost $5.01
  on the prior gate. Rule: before writing "verified by X" into a criterion, grep the repo for
  an existing member of the same list and count how many files match; name all of them, or name
  the whole suite rather than one member. Corollary for the close: a criterion satisfied to the
  letter that still failed the gate is a drafting defect worth recording even when its cost was
  trivial, because the cost is a property of how loudly the guard fails, not of the mistake.

- [FEAT-2026-0053/G3-CLOSE] **A budget brake evaluated only *before* each unit's dispatch cannot
  observe the unit that overruns, so a gate can exceed its declared budget while the brake reads
  clean.** A per-gate `cost_budget_usd` was checked by a halt predicate that runs ahead of each
  work-unit dispatch. Spend inside the final unit of a gate is therefore structurally invisible
  to it: the gate ended $4.94 (15.7%) over its declared budget and the brake never fired, and
  the same gate's close under-predicted the overrun by more than half because it assumed the
  closing pair would repeat the previous gate's actuals when closing units are the very units
  the brake cannot see. The defect was then documented in the *next* gate's budget comment
  rather than fixed, which converts a driver bug into folklore that each gate re-learns. Rule:
  a spend guard needs a post-unit reconciliation as well as a pre-dispatch check, or the field
  should be named for what it is — an estimate-checker, not a brake. Related: any close
  reconciling planned against actual should compute the total from `events.jsonl`, which is the
  only surface that never loses a cycle, and should state gate spend against the brake rather
  than against the plan.

- [FEAT-2026-0060/G1-CLOSE] **A registry derived from a corpus is derived from a lagging
  indicator: code paths that exist but have never executed are invisible to it by
  construction, and no amount of care in running the sweep recovers them.** A work unit was
  told to re-derive the driver's unsanctioned event types "from the corpus", did exactly
  that, found seven, and shipped an incomplete registry. Two further types — `gate_auto_armed`
  and `re_arm_rejected` — are emitted by real `build_event` call sites that have never fired
  in any recorded run. The next work unit derived from call sites, found both, and correctly
  blocked rather than editing the registry it exists to guard; the fix cost a full re-arm plus
  a gate-budget raise. The measurement decayed fast enough to make the point on its own: the
  roadmap row named 3 types, a deliberate corpus sweep one day before implementation found 7,
  the shipped union found 9 — 33% and 78% of the truth respectively. Rule: when a criterion
  asks for a set to be *computed*, name every source that can contribute a member and say
  which is authoritative when they disagree — "what has happened" (logs, corpus, telemetry)
  and "what can happen" (call sites, enum members, route tables) are different sets, and a
  guard built on the first silently under-covers. Corollary: bake the union into the guard
  itself, so a later derivation cannot regress to the cheap source.

- [FEAT-2026-0060/G1-CLOSE] **A code comment that records a known gap as *precedent* converts
  a defect into a convention, and every subsequent author learns the defect as house style.**
  `loop.py` documented an unvalidated event type with "…`gate_reached` and `attempt_outcome`
  are the existing precedent for driver-local event types outside the envelope enum and
  per-type registry." The gap was known, written down, and framed as a pattern to follow; four
  more unsanctioned types arrived after it, and by the time it was measured 34% of every event
  the driver had ever emitted failed validation. The comment was also the *only* hit for a
  mandatory existing-mechanism grep — the search found the admission, not a mechanism. Rule:
  when documenting a limitation in code, write it as a defect with its cost ("X is not
  validated; this is a gap, see ISSUE"), never as precedent or prior art. And when an
  existing-mechanism search returns a comment acknowledging the gap rather than a mechanism
  addressing it, that is evidence the gap is load-bearing and under-owned, not evidence the
  decision was already made.

- [FEAT-2026-0060/G1-CLOSE] **A close's consumer-visible contract list must be verified
  against the packaging manifest, not inferred from where a file lives — the one artifact
  whose entire job is accuracy about what consumers see is also the easiest to fill in from
  assumption.** This feature's close was instructed to treat a new `verification.yml` gate as
  the headline consumer-visible change, on the stated grounds that downstream projects
  upgrading the scaffold would gain a gate that could fail their builds. Checking the manifests
  rather than the file's plausible-looking location showed the gate script appears in no
  scaffold manifest and no shipped `verification.yml.example`, and a repo-wide grep returned
  three hits, all internal. The real shipped surface was a permissive schema plus three
  additive symbols: nothing downstream could go red. Rule: enumerate contract changes by
  grepping the packaging manifests and shipped templates for each changed path, and state the
  blast radius you measured rather than the one the work unit predicted. This cuts both ways —
  the same assumption that overstates risk here understates it when a file *is* shipped and
  nobody checked.

- [FEAT-2026-0060/G1-CLOSE] **A test that exercises a guard's helper function is not the guard
  observed failing; only driving the real assertion proves the guard is not cosmetic.** A
  drift guard shipped with a self-check named "the guard fails on an unregistered type", which
  called the comparison helper directly with a synthetic input and asserted on its return
  value. That verifies the helper's arithmetic; it does not verify that the guard's actual
  test method fails, names the offender, or is even wired to the same derivation. The close
  re-ran the check properly — importing the test module, monkeypatching its derivation
  out-of-tree to inject a synthetic type, and executing the real test method — and confirmed
  a `FAILED (failures=1)` naming the offender in its message. Rule: when a criterion says "the
  guard is confirmed to fail", the evidence must be the guard's own assertion raising, with
  the failure message quoted. A helper-level check is a useful unit test and a false close.
