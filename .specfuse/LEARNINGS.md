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
  events.jsonl"; the agent correctly identified that the orchestrator's
  schema rejects driver-emitted events by design (the schema's source
  enum is the orchestrator protocol; loop-driver events use
  `source: "driver"` and follow a different contract owned by `loop.py`).
  The re-arm fix inverted the AC to "rejects this real event" — semantically
  the right boundary evidence, polarity corrected. Rule: every AC of the
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
