---
project: specfuse-loop
---

# Archived feature details

This file holds the detail sections for features whose status has reached `done`
or `abandoned`. The main roadmap table in `.specfuse/roadmap.md` keeps a row for
every feature (across all statuses) and links here via a `Detail` cell for
graduated entries. Features with status `planned` or `active` keep their detail
sections inline in `roadmap.md`.

## Conventions

- **Anchor format.** Each archived feature's detail section is preceded by an
  anchor on its own line:

  ```
  <a id="feat-yyyy-nnnn"></a>
  ```

  Replace `yyyy` and `nnnn` with the feature's four-digit year and zero-padded
  sequence number (e.g. `feat-2026-0003`). The anchor must appear on a line by
  itself, immediately above the `## FEAT-YYYY-NNNN —` heading.

- **Back-link form.** The corresponding `Detail` cell in the main roadmap table
  contains exactly:

  ```
  [→ archive](roadmap-archive.md#feat-yyyy-nnnn)
  ```

  with the same lower-case `feat-yyyy-nnnn` fragment. Both strings are
  machine-read by the `roadmap-archive` and `roadmap-add` skills — do not alter
  their shape.

- **Which features are archived.** Only features with status `done` or
  `abandoned` are archived here. Features with status `planned` or `active`
  keep their detail sections inline in `roadmap.md`.

- **Append order.** Sections are appended in the order they are archived (not
  necessarily numeric order). The placeholder comment below marks the insertion
  point; T02 (`roadmap-archive` skill) and T04 (migration) append after it.

<!-- Archived sections appended below -->
<a id="feat-2026-0061"></a>
## FEAT-2026-0061 — Dependency-manifest coverage for non-Python ecosystems in `decision_class_paths`

**Why.** `decision_class_paths` is one of the eight arm-predicate stop classes shipped by [FEAT-2026-0053](roadmap-archive.md#feat-2026-0053), and its job is to stop an `auto` feature before it adds a dependency without a human seeing it. It recognises exactly three manifest shapes: `_DEPENDENCY_MANIFEST_EXACT` matches `pyproject.toml` and `package.json`, and `_REQUIREMENTS_RE` matches `requirements*.txt`. Every other ecosystem is invisible. Found while scoping the first `auto` ride against the Specfuse Generator, which is a Maven repository: a work unit there adding a Java dependency to `pom.xml` arms without stopping, and the class reports `clean` while doing it — a false negative, not a gap the operator can see. `build.gradle`, `build.gradle.kts`, `Cargo.toml`, `go.mod`, `Gemfile`, `*.csproj`, and `composer.json` are all in the same position. The class is at its least trustworthy exactly where its value is highest, because a repo whose manifests it cannot read is a repo where it silently never fires.

**Goal.** Extend the manifest surface to the ecosystems Specfuse targets, with the recognition rules stated in one place rather than spread across two module-private constants and a regex. Decide as part of this feature whether coverage is a fixed list or a declared surface a target project can extend in `.specfuse/verification.yml` — the fixed list is simpler and cannot drift out of sync with a project's real build files; a declared surface handles the polyglot monorepo the fixed list will eventually meet. Whichever is chosen, an unrecognised-but-plausible manifest should be surfaced rather than silently passed: a class that cannot evaluate its input should report `not_evaluable`, which the predicate already treats as fail-closed, instead of `clean`. Add the coverage list to `docs/concepts/autonomy-stop-classes.md`, which currently documents the class without naming what it can and cannot see.

**Benefits.** The dependency-addition guard works in the repositories Specfuse is actually used in, rather than only in Python ones. Removes a false-negative class from the autonomy predicate — the most dangerous failure shape it has, because a stop class that reports `clean` on an input it cannot parse is worse than one that is absent, which at least an operator would notice. Unblocks trusting `auto` in the Generator and any other JVM, .NET, Go, or Rust target.

**Status: active.** Single terminal gate, 2 substantive WUs plus close ($11.50 planned, $16.50 gate budget). Both chartered decisions were settled at draft time: coverage is a **fixed list** in `arm_eval.py`, not a declared surface in `.specfuse/verification.yml` — the predicate reads nothing outside `feature_dir` today and a config read would add a new failure mode to a class whose whole defect is reporting a status it cannot justify. `not_evaluable` gets **two triggers**: a named-uncovered manifest list whose every entry must justify why it is not simply covered (it may legitimately end up empty), and a glob or directory in `produces:` that the class cannot decide — the latter measured at 0 of 169 corpus entries, so it is fail-closed without being unsatisfiable.

<a id="feat-2026-0053"></a>
## FEAT-2026-0053 — Autonomous feature mode (auto gate-arming with mechanical stop conditions)

**Why.** The methodology's autonomy field (`auto` / `review` / `supervised`) is written to PLAN.md frontmatter and never read — zero consumers — so every feature stops at every gate boundary exactly like a `review` feature, and a four-gate feature costs four human touches regardless of how routine its gates are. Operator history across features shows those gate reviews are near-universal rubber-stamps whose accepted changes are additive (new work units at gate check, occasionally a new gate), so the per-gate checkpoint spends latency without buying review value; the operator's real read happens at PR review, and merge is always human.

**Goal.** Implement `auto` end-to-end: the driver arms drafted gates and accepts plan-next's additive plan adjustments on its own, stopping only on mechanical conditions. Stop classes: (1) projected budget breach — spent plus planned-remaining exceeds 2× the feature budget; (2) objective-at-risk proxies — hedged close verdict (stays human, unchanged), remaining-work count failing to shrink across two consecutive gate closes, attempt-per-WU trend decay; (3) plan-drift caps — cumulative added WUs above 50% of the original skeleton (counted in planned dollars as well as units), a second added gate, any retroactive edit to passed gates, any addition lacking machine-readable provenance citing the retrospective item or failure event that triggered it; (4) judge-editing — any draft touching verification config, test thresholds, CI workflows, hooks, or the driver itself; (5) decision-class registry hits — human-authored path/keyword registry covering public API shape, schema or data migrations, security posture, dependency additions; (6) model self-flagged must-be-human decisions (self-flags may only subtract autonomy, never grant it). Supporting mechanics: budget projection over the existing per-attempt cost capture in events.jsonl and the per-gate budget brake, tag-before-arm revert points, per-gate doubt summaries accumulated into a FEATURE-REVIEW.md surfaced in the PR body, LEARNINGS entries staged to a pending file promoted at PR review, and a shadow mode that logs would-have-armed / would-have-stopped verdicts on attended features before the dial goes live. Dial read from per-feature frontmatter; policy-file layering may tighten later, never loosen.

**Benefits.** A four-gate feature drops from four human touches to one (the PR review, now fed by the accumulated doubt summaries); unattended runs progress overnight with blast radius bounded by construction — caps, revert tags, and hard floors on judge-editing and retroactive edits — rather than by judgment; shadow-mode telemetry replaces guesswork when tuning stop thresholds; and the declared-but-dead autonomy field finally does what the methodology has promised since it was specified.

**Gate 1 — shipped, and it changes no arming behavior anywhere.** Four substantive work units `done`. `specfuse/loop/plan_baseline.py` writes an immutable `PLAN.baseline.json` snapshot of a feature's as-activated plan graph at first dispatch — write-once by construction, because a refreshable baseline is a drift detector that can be gamed by drifting. `specfuse/loop/arm_eval.py` is the predicate: pure, side-effect-free, mirroring `gate_eval.py`'s shape without sharing its code, returning a per-class verdict (fired / clean / not_evaluable, each with a reason) across seven classes — budget projection, judge-editing, decision-class paths, retroactive edits, drift caps, missing provenance, and open-questions/human-only — plus an overall `would_arm`. The three machine-readable plan-next contract fields (`open_questions`, `human_only`, `provenance`) are documented in both `WU.template.md` copies and covered by **warn-only** lint; the flip to blocking under `auto` is gate 2's, and it is a severity flip needing its own satisfiability answer and runtime probe. Wiring is passive: the driver evaluates and appends one `arm_predicate_evaluated` event at every `awaiting_review` flip, and its control flow after the append is verdict-independent — a predicate exception degrades to an `evaluation_error` payload rather than crashing a gate close. **The organizing principle held.** Only the two veto classes carry model-authored input, and both can only subtract; every approval input is a counter, a path, or a hardcoded constant. Substantive spend **$8.35 against $13.00 drafted (−35.8%)** — three first-attempt passes at roughly 45–48% of estimate, the third consecutive feature to under-run implementation by about a third (issue #260, no per-feature response). The one blocked attempt cost **$1.22**: T04 stopped on discovering that the per-type event-schema registry and the envelope `event_type` enum are both unowned by this repo, which is now **[FEAT-2026-0060](roadmap.md#feat-2026-0060)**; the operator narrowed T04's criteria to follow the existing `gate_reached` / `attempt_outcome` precedent rather than answer the registry question inside a shadow-mode work unit.

**Consumer-visible additions from gate 1, all additive.** Two new modules; three template-documented frontmatter fields; the new `arm_predicate_evaluated` event type on `events.jsonl` (deliberately outside the envelope enum and the per-type registry, matching existing driver-local precedent); and the new per-feature `PLAN.baseline.json` artifact, committed by the driver, which every Specfuse project on a driver at or past 0.7.1 will start seeing appear in its feature folders. Nothing was removed or renamed. Full enumeration and the deferred-verification list are in the feature's `RETROSPECTIVE.md`.

**Gate 1 deliberately did not prove** that either wired call site fires, and the reason generalizes: a work unit that wires new code into the driver cannot be verified by the driver run that wired it — `loop.py` is imported once at process start, so mid-run edits are dead code for the rest of that invocation. `PLAN.baseline.json` existed in **0 of 43** feature directories at close time. Two consequences the arming checkpoint must handle. First, `GATE-01.md`'s first-firing check reads an absent `arm_predicate_evaluated` event as proof the wiring claim is false; on this gate it is more likely a stale process, so **disambiguate before escalating** — did a driver launched after the wiring commit close the gate? Second, this feature's own baseline will be captured at the *next* invocation, from a PLAN.md that by then already contains gate 2's drafted work units, so the "as-activated" graph it records is the post-drift graph. **Gate 2 must not treat this feature's own baseline as evidence that drift detection works.** Relatedly, a close-time sweep of the predicate over all 43 real feature directories returned `would_arm: False` with every class `not_evaluable: no_baseline` on 43 of 43 — the designed fail-closed path confirmed on real input, and the approval path still unproven outside fixtures.

**Gate 2 — shipped. `auto` is real.** Five substantive work units `done`. `specfuse/loop/arm_txn.py` is the pure arm transaction: one function returns the complete write set an arm consists of — every gate-`N+1` draft work unit flipping to `pending`, gate `N` flipping `awaiting_review → passed`, `events.jsonl`, and the accumulated `FEATURE-REVIEW.md` — plus the revert tag *name*; the module performs no git operation at all, which is what makes the one-commit guarantee testable. The driver now reads `autonomy_default` at the single flip site that can arm, tags `pre-arm/<feature-id>/gate-<N>` at the pre-arm HEAD, and carries every write into the one existing bookkeeping commit. **Escalation overrides autonomy by control flow, not by a check**: the two escalation flip sites `return` before the dial is ever consulted. `plan_next_lint` joins the predicate as the **eighth class and the third veto class**, taking the contract-field lint from warn-only to arm-blocking under `auto` only — the CLI is unchanged and every non-`auto` feature is unchanged. Each auto-arm appends the gate's verbatim `open_questions`, verbatim `## Doubt` prose, and per-class verdict to an append-only `FEATURE-REVIEW.md` inside that same commit, with the doubt prose still never an input to the predicate. And under `auto` a closing work unit that touches `.specfuse/LEARNINGS.md` fails a post-pass invariant (`learnings_not_staged`); lessons stage to a feature-local `LEARNINGS-pending.md` from a new shipped template, so **an unread gate cannot write a durable cross-feature rule**. 58 tests across seven suites, all green at close, including a run of the real `loop.run()` against a copy of this feature's own folder — real baseline, real frontmatter, real event log.

**Consumer-visible changes from gate 2 — larger than gate 1's, and not purely additive.** Ten items, three of which need a deliberate read. **`CLASS_NAMES` goes 7 → 8 and `VETO_CLASSES` 2 → 3, so every `arm_predicate_evaluated` payload's `classes` map now carries eight keys instead of seven** — an existing payload that changed shape, not a new one beside it. The `pre-arm/<feature-id>/gate-<N>` tags are real repo objects created with `-f`, one per armed gate. And the bookkeeping commit message changes under `auto`, from `chore(loop): gate N awaiting_review` to `chore(loop): gate N auto-armed gate N+1 (tag …)`, which any existing grep over the bookkeeping trail will miss. Also new: the `gate_auto_armed` event type (this feature's **second** unregistered type, raising rather than flattening the cost of [FEAT-2026-0060](roadmap.md#feat-2026-0060)), the `FEATURE-REVIEW.md` and `LEARNINGS-pending.md` per-feature artifacts, the `LEARNINGS-pending.template.md` template shipped to every downstream project, the `close-e` / `close-intermediate-e` closing requirements, and `docs/dev/auto-arm-recovery.md`. Full enumeration in the feature's `RETROSPECTIVE.md`.

**Gate 2 cost 58% more than drafted, and that reverses the pattern.** Substantive spend **$23.74 against $15.00 (+58.3%)**. One spin accounts for $5.01 — a new veto class firing on the *preceding* work unit's test fixture, surfacing as that unit's test failing under a whole-suite signature, in a file the new unit was forbidden to touch; three sessions chased it before the operator diagnosed the root cause and re-armed with the fixture amendment in scope. Strip it and the gate is still **+24.9%**, with two first-attempt passes landing 44% and 72% over. That is estimate error, not execution error, and it is the fourth data point on **issue #260** pointing the opposite way from the first three: gate 1's units were independent modules and ran a third under; gate 2's five all wire behavior into a live driver and into each other. **The rule should be scoped to independent-module work or it will underestimate every wiring gate.** Gate spend stands at 75.4% of `GATE-02.md`'s `cost_budget_usd: 31.50` with both closing units still to run.

**Gate 2 also resolved gate 1's two open questions, and found one defect of its own.** The first live `arm_predicate_evaluated` event fired on the next driver invocation, and `PLAN.baseline.json` appeared — so gate 1's disambiguation was right and the absent gate-1 event was a stale process, not a false claim. That baseline now contains gates 1, 2 **and** gate 3's placeholder, confirming gate 1's prediction exactly: **this feature's own clean `drift_caps` verdict measures nothing and must not be cited as evidence drift detection works.** The defect: the predicate's `budget_projection` class sums only each unit's per-cycle `cost_usd`, never `cumulative_cost_usd` nor `re_arm_history[].prior_cost_usd`, so it reads **$35.89 of this feature's true $42.12 lifetime spend — 14.8% low, all of it the two re-armed units.** No verdict flips here (the projection stays far under its 2× cap), but the error concentrates in exactly the over-budget re-armed work a budget brake exists to catch. Two small fixes, neither in gate 2's scope.

**Gate 2 deliberately did not prove** that any of it runs in production. No live arm happened — this feature runs `review` by decision, so the whole arm path is verified by tests and by no production ride. `plan_next_lint`'s *firing* path has never executed on a real feature folder (a sweep of all 43 returns 0 fired / 1 clean / 42 not-evaluable, the one clean being this feature, the only one with a baseline). The `LEARNINGS-pending.md` promotion procedure has never been performed by a human. And **`FEATURE-REVIEW.md` is written and never read**: a grep across every skill and shipped template returns zero references outside the module that writes it. Accumulation shipped; the last hop into the PR body is unbuilt and unowned — which on a feature whose premise is replacing four gate reads with one PR read is the checkpoint value silently not being delivered. `G2-PLAN` scopes it into gate 3 or records a deferral with a home.

**Status: active.** Gates 1 and 2 closed; gate 3 (docs and methodology rewrite, migration guidance, plus whatever gate 2's retrospective surfaces) is drafted by `G2-PLAN` and armed by the human. This feature itself runs `autonomy_default: review` — per `[FEAT-2026-0007/G2-LESSONS]`, an enforcement mechanism cannot be exercised by the gate that builds it, so the first live `auto` ride belongs to a successor feature after this branch merges.

<a id="feat-2026-0055"></a>
## FEAT-2026-0055 — Arm-time WU contract lint: produces satisfiability + boundary consistency

**Why.** FEAT-2026-0066/T04 burned $11.43 across 3 attempts plus a human escalation on a `produces:` path already fully delivered by T03 — unsatisfiable by construction and detectable before dispatch. The same WU's Do-not-touch barred `src/main/**` while its acceptance criteria required an artifact only `src/main/**` could hold — a deadlock no lint catches today. And `assert_declared_deliverables` (literal paths only) vs `assert_produces_in_diff` (literal or fnmatch glob) have divergent path semantics that WU authors now document via folklore comment blocks in every feature (FEAT-2026-0065/T01 paid $10.43 learning it; 0066 re-quoted the warning verbatim). Portfolio cost of the produces/deliverable mismatch classes: ~$55.

**Goal.** At gate-arm time (and in `specfuse-lint`), validate every WU in the arming gate: refuse a `produces:` path that a prior WU's squash already fully delivered; refuse a `produces:` path or acceptance-criteria deliverable that the WU's own Do-not-touch section forbids; unify the path semantics of the two deliverable gates so a single declaration form satisfies both. Refusal happens before any attempt is dispatched, with the conflict named.

**Benefits.** The `produces_not_in_diff` / `no_deliverable_files` / `deliverable_missing` waste class dies at arm time instead of after 3 burned attempts and an escalation; per-WU folklore comments explaining the dual-gate trap become deletable; arm-gate review gets a mechanical consistency report instead of relying on operator eyeballing.

**Status: active — gate 1 close returned `met_locally` (2026-07-30), awaiting operator acknowledgment.** Attempt 1 of the close returned `not_met`: the ERROR leg was blind to the `**Do not touch.** <content>` bold-preamble form used by all 327 work-unit bodies in this repo, so the motivating FEAT-2026-0066/T04 deadlock armed clean, while the continuation lines it could read yielded 15 false ERRORs across 4 existing features. T05 fixed the extraction — `slice_wu_section` now returns label-line content for the bold form, and boundary patterns are prohibition-scoped with ambiguous matches degraded to WARN. Re-verified fresh at the second close: the deadlock fixture in the canonical body form ERRORs and names `assert_produces_in_diff`; the tree-wide sweep reports **zero ERRORs across 43 feature folders** (was 15), with 4 advisory produces-class WARNs on 2 features enumerated; the WARN leg and the unified literal/glob semantics for `assert_declared_deliverables` / `assert_produces_in_diff` hold with negative observations; full suite, ruff, bandit, and coverage all exit 0. Hedged rather than `met` on two counts, both with recorded upgrade conditions: the portfolio measure (zero produces-class refusals) is a measurement over a future generator-class feature's event log, and the consumer-visible contract changes await an operator's acknowledgment. Terminal flips stay withheld until then — next step is `/accept-hedged-close`. One open follow-up worth scheduling as real work: promote the tree-wide sweep from a close-time criterion an agent reports to a `verification.yml` gate the driver runs. Separately noted, not this feature's doing: `specfuse-lint` crashes on `FEAT-2026-0020-public-readiness-prep` with a `MiniYAMLError` on an HTML comment in a WU's frontmatter. Evidence and consumer-visible contract changes: `.specfuse/features/FEAT-2026-0055-arm-time-wu-contract-lint/RETROSPECTIVE.md`.

<a id="feat-2026-0054"></a>
## FEAT-2026-0054 — Close-ceremony skeleton + in-session closing lint

**Why.** Portfolio telemetry (2026-07-30 review, 25 generator features + cross-repo data): 28% of all closing-WU spend is driver refusals. The `closing_deliverable_missing` class cost ~$42 and `assert_gate_review_exists` alone $53.11 across 15 refusals (issue #261). The guards check literal artifact shape (headings, frontmatter fields, file names) *after* the attempt, so a $4–10 verification pass is re-bought over a missing `### Failure-class breakdown` heading or a misnamed review file. Close-WU prompts now spend ~40% of their text restating guard strings defensively — machine contract leaking into prose, re-paid in tokens on every attempt.

**Goal.** The driver pre-creates the ceremony skeleton at close/close-intermediate/plan-next dispatch: `RETROSPECTIVE.md` with every conditionally-required heading stubbed, a `verdict: TBD` frontmatter placeholder that lints as incomplete, and the correctly-named `GATE-{N+1}-REVIEW.md` stub. Ship `specfuse-lint --closing` so the agent validates the full closing-assertion set in-session before ending its attempt; the post-squash driver assertions become a cheap recheck of surfaces that were pre-created, not a discovery mechanism.

**Benefits.** The format-guard refusal class becomes structurally near-impossible to hit (~$95 of measured portfolio waste to date); close attempts spend their budget on verification substance instead of artifact-shape compliance; the guard-defensive boilerplate can be deleted from `WU.template.md` and every drafted close WU, shrinking both authoring effort and per-attempt input tokens.

**What shipped, where it differs from the goal above.** Delivered: `closing_requirements.py` (the registry both the post-squash guards and the new lint read), `specfuse-lint --closing`, dispatch-time skeleton pre-creation, and the `close-discipline.md` §4 / `WU.template.md` prose rewrite. Two deliberate departures from the drafted goal: (1) **no `verdict: TBD` placeholder** — `lint_plan` fails a dispatched close WU mid-flight on an invalid verdict value, so the skeleton leaves the field absent and the lint reports the absence as an actionable finding instead; (2) the `RETROSPECTIVE.md` stubs are **conditional, not exhaustive** — each section is written only when it is derivable from on-disk state at dispatch time, so a terminal close on a gate with no failures is pre-created nothing at all. `close-discipline.md` §4 currently describes the exhaustive version; correcting it is follow-up D3 in the retrospective.

**Status: gate 1 closed `met_locally` on 2026-07-30.** All ten gate-1 acceptance criteria verified fresh in-session; the load-bearing *lint-approves ⇒ guards-pass* property was observed on nine fixture dispatch scenarios with zero divergence. Hedged on two items that no in-repo session can settle: the human acknowledgment close-discipline §3 requires for the consumer-visible contract-change list (D1), and the portfolio success measure — zero closing-format refusals — which verifies on the next generator feature (D2). Two defects found and escalated rather than patched, both inside the work unit's do-not-touch boundary: D3 above and D4 (the failure-class guard cannot fire on implementation-WU failures). The row status stays `active` because the terminal flip is verdict-gated and driver-owned; see `.specfuse/features/FEAT-2026-0054-close-ceremony-skeleton/RETROSPECTIVE.md`.

<a id="feat-2026-0040"></a>
## FEAT-2026-0040 — Failure-artifact harvester CLI (detect + report; local and gh-actions runners)

**Why.** Detection must be deterministic, cheap, and LLM-free: enumerate discrete failure artifacts (DLQ messages, error-log entries, 5xx traces, missed heartbeats, invariant violations) and report them as deduplicated GitHub issues. Laser focus on component misbehavior — not metrics or infra (that is Datadog's job) — catching functional issues before platform alerts fire.

**Goal.** A CLI (`specfuse-monitor run [--component X] [--env Y] [--dry-run]`) implementing the FEAT-2026-0039 schema behind a provider-adapter interface (telemetry adapter + broker adapter, each normalizing to the neutral artifact model — core logic never sees provider types); v1 ships the Azure pair: Service Bus DLQ peek adapter and App Insights KQL adapters for the built-in check types; fingerprinting (component + failure class + signature, e.g. exception type + top app stack frame); context collection by correlation ID; redaction pass before any artifact text lands in an issue; issue lifecycle — search by `specfuse-monitor` label + fingerprint marker, create with diagnosis-ready artifact section, update occurrence count throttled, annotate "quiet for N runs — candidate for close" (humans close; no quiet-based auto-close ever). State principle: everything derivable from GitHub issues or safely losable — issues are the fingerprint registry; watermarks are best-effort per-host cache with lookback-window fallback; idempotency comes from fingerprint dedupe. Ships local runner mode plus the GH Actions workflow surface; all env access read-only.

**Benefits.** Autonomy level 1 (detect + report) live end to end: a poison message becomes one evidence-rich GitHub issue within a polling cycle, deduplicated across thousands of occurrences, feeding the existing fix-bug/roadmap triage loop. Deterministic detection keeps the alerting path auditable and free of LLM cost/flakiness.

**Unblocked 2026-07-26.** [FEAT-2026-0069](roadmap.md#feat-2026-0069) landed the check-target axis and is `done`; [FEAT-2026-0039](roadmap.md#feat-2026-0039) shipped the schema before it. The contract this feature builds against is now settled and machine-checkable.

**Binding constraint inherited from FEAT-2026-0069 — do not lose it.** **Fingerprints must include the target key.** Without it, 20 DLQ targets collapse into one issue and the per-subscription attribution 0069 paid two gates for is destroyed at the last step. 0069's terminal close restates this as its own closing obligation; it is this feature's to honour.

**Two open schema questions this feature will be first to feel**, neither blocking: [#262](https://github.com/specfuse/loop/issues/262) — telemetry binds per environment, so components in one environment cannot resolve to different telemetry instances; and the cron-dialect ambiguity 0069's real-repo run surfaced — `cron` is opaque to the schema, and a heartbeat check computing "should this have fired?" cannot tell a 5-field expression from a 6-field one. Decide both when the adapter interface forces the question, not before.

**Both questions are now answered — decided at the point the adapter interface forced them, as intended.** [#262](https://github.com/specfuse/loop/issues/262) is deferred **through a seam** rather than left in the shape it warns about: gate 1's `resolve_telemetry(component, environment)` resolves telemetry *for a component*, and its only implementation today reads the environment binding. No schema change and no migration, and when per-component bindings land they add a resolver implementation instead of reshaping every adapter — which is exactly the cost #262 named ("if per-component bindings arrive after adapters exist, the adapter interface changes rather than extends"). Gate 2's four adapters are the seam's first real consumers and all call it with the component, asserted per adapter. The cron-dialect ambiguity is **decided: the dialect is declared, never inferred.** Inference by field count was considered and rejected by the operator — it degrades silently exactly when a new dialect arrives, which is the worst moment for a monitoring tool to start guessing.

**Gate 1 — shipped, auto-closed on-plan.** Three work units `done`, each on its first attempt, **$2.65 against $9.50 planned**. A failure can be modelled, fingerprinted, and redacted with no provider reachable from the core: `FailureArtifact` plus the `TelemetryAdapter`/`BrokerAdapter` protocols and the `resolve_telemetry` seam (`specfuse/monitor/artifact.py`, `adapters.py`); `fingerprint_artifact` over a canonically-ordered SHA-256 payload that incorporates `target_coordinates` — the binding constraint inherited from 0069, asserted rather than assumed; and `redact_artifact` with its own pattern set (deliberately **not** `leak_scan`'s, which is repo-internal tooling absent in consumer projects) reusing only the `<redacted:sha8>` convention so the same secret stays correlatable across occurrences without the live value surviving. The gate auto-closed at `attempts: 0`, so its close ceremony never ran and its 32 acceptance criteria went unenumerated; gate 2's close reconciled that debt and found the deferred list **legitimately empty** — every criterion was in-loop verifiable and 29 of the 32 were re-run green at close time.

**Gate 2 — shipped.** Four work units `done`, each on its first attempt, no escalations, **$13.33 against $16.50 planned for the implementation half** (gate budget $33.00). The Azure adapters now produce artifacts and a schedule declares its dialect. `T04` shipped the `dialect` contract — a `standard-5`/`seconds-first-6` enum, four ERROR-severity validator rules (cron without dialect, dialect out of enum, arity disagreement, dialect without cron), both example copies migrated, and the `derive-monitoring` reference implementation emitting the field so the next generated config is conforming by construction. Expand → migrate → contract ran in that order inside one work unit, because `.specfuse/monitoring.yml.example` is itself a code gate and a flip-first ordering would turn a base gate red and halt the run before any unit dispatched. The migrate criterion is a **walk-discovered sweep**, not a sample: at close time it collected 14 cron-carrying targets across 4 files with zero non-conforming, and one of those files was created by a *later* work unit in the same gate — a hand-written path list would have stopped looking at it. `T05` added the Service Bus DLQ peek adapter, read-only proven by a recorded-call assertion (no `receive`, `complete`, `abandon`, `dead_letter`, `defer`, or `renew_lock`), carrying `subscription` + `function` so two targets on one component never collapse into one fingerprint. `T06` added the App Insights KQL adapters for `error-logs`, `http-5xx`, and `invariant`. `T07` added `specfuse/monitor/schedule.py` — a stdlib-only cron evaluator over both arities with real timezone and DST arithmetic, taking the reference time as an argument and never reading the clock — plus the heartbeat adapter, which **refuses** on arity disagreement rather than falling back, so the declared-dialect position holds outside the lint path too. Every transport is injected at construction and every SDK import is lazy, so the package keeps its zero-runtime-dependency property and the modules import on a clean checkout with no cloud SDK installed. Provider agnosticism was verified as a property of the tree rather than only as a passing test: `grep -rniE "azure|appinsights|servicebus|kusto" specfuse/monitor/` returns 29 matches, **all of them under `specfuse/monitor/providers/`**, and nothing outside `providers/` imports from it. `queue-stalled` deliberately has no adapter yet — decided into gate 3 at arming so it reads as a decision rather than an oversight.

**What gate 2 did not verify, stated rather than glossed.** Every adapter was exercised **only against stub transports**. No live Service Bus namespace and no live App Insights workspace was reached, and no DST transition was observed in production — this repo "is a CLI tool with no deployable components and will never carry a real monitoring.yml," so that is structural, not a shortcut. The oracle that discharges those eight deferred items is an operator run against the downstream .NET backend, the same oracle 0069 used for its own follow-ups, and it is planned. `GATE-02.md`'s definition of done was written so that none of it is a clause in the gate.

**Breaking change for consumers, gate 2.** A `heartbeat` target that carries `cron` must now also carry `dialect`. A downstream `monitoring.yml` with a cron-carrying heartbeat target lints clean today and will not after upgrade. Migration is mechanical: count the expression's whitespace-separated fields and add `dialect: standard-5` (5) or `dialect: seconds-first-6` (6); projects that generate the file can instead re-run `/derive-monitoring`, which now emits it from the discovered trigger registration. Cron-less heartbeat targets stay valid and `cron` itself remains optional, so the rule fires on no correct input.

**Gate 3 — shipped, and this is where the parts met for the first time.** Four work units `done`, **$27.15 against $23.00 drafted** (gate budget $28.00). `T08` closed the last check type: a `queue-stalled` broker adapter reading queue depth **and** age-of-oldest, deciding staleness from age with depth as evidence — a deep queue that is draining is not stalled — with a `<integer><s|m|h|d>` threshold grammar that **refuses** unparseable values rather than guessing, and a target with no `stall_after` skipped with a recorded reason that reaches the run summary instead of being silently monitored by nobody. `T09` shipped `specfuse/monitor/issues.py`: find-or-create keyed on the fingerprint, reusing `escalation.py`'s injected-runner seam, its issue-number parse, and its HTML-comment marker convention — but **replacing** its `--search` finder, which FEAT-2026-0046's own retrospective records as unsafe for a deduplicating consumer because GitHub's index does not reliably tokenise HTML-comment content and a search returning nothing silently files a duplicate. The replacement filters client-side over an explicitly `--limit`ed listing and **raises** rather than reporting not-found when a full page comes back with no match, closing the same defect by its other route. Occurrence counts bump under a throttle, a quiet fingerprint is annotated, and **nothing ever closes an issue** — humans close, per the roadmap's own standing decision. `T10` shipped `specfuse-monitor run`: config load, enumeration on the 0069 target axis, registry-driven dispatch over opaque provider strings, telemetry through the `resolve_telemetry` seam, watermark fallback that degrades to a lookback window on a missing, unreadable, or corrupt cache instead of failing the run, and a summary naming what was skipped and why. `T11` shipped the two runner surfaces — the local runner and a GitHub Actions workflow that ships as a **template** under `specfuse/loop/data/`, deliberately not installed into this repo, with `permissions: {issues: write, contents: read}` and no literal secret — plus the `runner` dial, which now routes: a component belonging to another surface is named in the summary rather than silently unmonitored, and `in-cluster` is reported as unhandled-by-design with FEAT-2026-0043 named.

**The binding constraint was proven end to end, and that is the thing worth reporting.** One component, one `dlq` check, two targets whose findings differ *only* in their target coordinates: the composed cycle recorded **two `gh issue create` calls with two distinct fingerprints**, and a second harvest of the same two findings created nothing. Enumeration, fingerprinting, and the issue lifecycle — built across three gates and never run together until now — agree. That is proof of the composition against a stub runner, not proof of GitHub.

**What gate 3 never executed, stated plainly.** `gh` returns auth errors inside a work-unit session, so **no issue was ever filed against a real repository**: the whole issue lifecycle is stub-runner evidence, and the shipped workflow was asserted structurally and **has never run anywhere**. Three deferred items (a second harvest against a real repository files no duplicate; a real run files the issues its dry run predicted; the installed workflow completes a scheduled run) join gate 2's eight adapter deferrals, all of which stand — no live Service Bus namespace or App Insights workspace has been reached and no DST transition has been observed in production. The named oracles are an operator run against the downstream .NET backend plus a scratch GitHub repository, both planned, recorded in `OPERATOR-JOURNAL.md` in the feature folder; that journal does not exist yet.

**One real defect found by the terminal close's fresh re-run, and left unfixed on purpose.** Gate 2's walk-discovered cron sweep now flags gate 3's shipped workflow template: the sweep collects every tracked mapping carrying a `cron` key, and a GitHub Actions `on.schedule` cron cannot carry the `dialect` the rule requires. Both units are correct by their own lights and the `tests` gate (and with it `coverage`, whose command chains on it) is **red at HEAD**. The introducing unit could not have caught it — the sweep walks `git ls-files` and its own template was untracked at verification time. The close reports it rather than patching a `done` unit's work; the fix is to scope the sweep's discovery, on a bug branch.

**Unblocks.** **FEAT-2026-0038** (DLQ quarantine harvesting extends the peek-mode adapter this feature shipped), [FEAT-2026-0041](roadmap.md#feat-2026-0041) (diagnosis reads the finding/issue contract this feature defines), **FEAT-2026-0042** (autofix consumes diagnosed findings), and **FEAT-2026-0043** (the in-cluster runner is the third surface alongside the two shipped here). Each has a detail section below; only 0041 carries an explicit anchor today, so the other three are named rather than linked.

**Status: active — terminal close ran with verdict `partially_met`.** Hedged deliberately: the fourteen-item consumer-visible contract-change list (entry 1, the `dialect` requirement, is breaking) is **awaiting operator acknowledgment**; eleven deferred items await the two planned operator runs; and the cron-sweep defect above means two shipped acceptance criteria do not hold on the tree as it stands. `/accept-hedged-close` is the path once the acknowledgment is signed; the verdict upgrades toward `met` as the operator-journal entries land.

<a id="feat-2026-0072"></a>
## FEAT-2026-0072 — Structural-invariant guards: declared surfaces that nothing asserts on

**Why.** Three defects found in one day share a single shape: **a surface the repo declares, that nothing checks, drifting silently until something unrelated stumbles over it.** [#257](https://github.com/specfuse/loop/issues/257) — two bats suites existed and were wired to no gate; one had been red for weeks while CI stayed green. [#284](https://github.com/specfuse/loop/issues/284) — `CLAUDE.md` states that `.claude/skills/` holds forward symlinks so discovery finds skills, but nothing creates them; four skills sat invisible for seven weeks, including one shipped the same day. [#287](https://github.com/specfuse/loop/issues/287) — three `done` features carry a terminal gate that is not `passed`, and `lint_plan` has no check that a done feature's gates are closed. None was caught by a gate, because in each case the gate set did not know the invariant existed. #257 is fixed and its guard (`tests/test_bats_suites_gated.py`) is the working precedent this feature generalises.

**Goal.** Ship the two missing guards, in the shape #257 proved: assert the invariant in both directions, and make the assertion itself falsifiable. (a) **Skill discovery** — every directory under `.specfuse/skills/` has a `.claude/skills/` entry symlinking to it, and something creates a missing one rather than leaving it to a human; `scripts/sync-scaffold.sh` is the natural owner since it already documents the contract it does not enforce. (b) **Done-feature gate consistency** — a feature at `status: done` has every gate `passed`, checked in `lint_plan`. Both ship with the reconciliation of the state already on disk: four symlinks (landed in [#285](https://github.com/specfuse/loop/pull/285)) and three stale gate files.

**The two traps that make this less mechanical than it looks.** Both are recorded because the obvious implementation is wrong in each case. **The skill-symlink check cannot be symmetric:** seven entries in `.claude/skills/` point at `../../.agents/skills/` (local operator tooling, untracked), so `set(.specfuse/skills/*) == set(.claude/skills/*)` reports non-zero on a correct tree. The guard must assert the forward direction completely and filter the reverse to links resolving inside `.specfuse/skills/`. **The done-feature check must exclude `FEAT-2026-0001`:** it is `status: done` with both gates `open`, and that is correct — it is the bundled worked-example fixture, a template that ships to target projects and was never executed. A naive assertion fires on it, which is an unsatisfiable predicate under `planning-discipline.md` §2, and the likely "fix" is someone mutating the shipped fixture to satisfy a linter.

**Benefits.** The next skill added without a symlink, and the next feature closed without its gate flipped, fail a check on the first run instead of being discovered months later by accident. `/attention` stops reporting permanent false noise, which matters because an inbox that is always wrong trains its reader to ignore it. And the three incidents stop being three separate cleanups and become one enforced property: a declared surface is asserted on, or it is not declared.

**What shipped** (gate 1, terminal — three work units, all first-try green). **[#284](https://github.com/specfuse/loop/issues/284) is resolved by T01 + T02**: `tests/test_skill_discovery_links.py` asserts the forward direction completely — every directory under `.specfuse/skills/` has a `.claude/skills/` entry that is a symlink resolving to it — and filters the reverse to links resolving inside `.specfuse/skills/`, so the seven operator-tooling entries pointing at `../../.agents/skills/` do not trip it. It carries an `_INTENTIONALLY_UNLINKED` mapping, empty as shipped, whose entries would each require a written reason and a live target. `scripts/sync-scaffold.sh` now creates any missing forward link instead of describing the contract in two comments and enforcing it in neither: existing entries are left byte-identical, entries resolving outside `.specfuse/skills/` are neither modified nor removed, and a second run creates nothing. It is covered by `tests/sync_scaffold_symlinks.bats`, registered as the `sync-scaffold-symlinks-bats` gate in `.specfuse/verification.yml` — a registration #257's guard required in the same work unit, which is the precedent check doing its job on this feature's own work. **[#287](https://github.com/specfuse/loop/issues/287) is resolved by T03**: `check_done_feature_gates` in `specfuse/loop/lint_plan.py` is a blocking error when a `status: done` feature has any `GATE-NN.md` that is not `status: passed` (`GATE-NN-REVIEW.md` artifacts are skipped by name), and it landed together with the reconciliation of the tree it ships into — `FEAT-2026-0007`/`GATE-02` and `FEAT-2026-0008`/`GATE-01` flipped `awaiting_review` → `passed` because both genuinely completed under closing machinery that predated the terminal flip.

**How the two traps resolved.** The asymmetric-symlink trap held as written: the guard is forward-complete and reverse-filtered. The done-feature trap turned out to need **two** exclusions, not one — the drafted `FEAT-2026-0001-health-endpoint` (the bundled worked-example fixture, `done` with both gates `open` by design) and also `FEAT-2026-0036-adopt-ruff-016`, which was executed directly as a config-only fix after a loop run on a flawed plan blocked, so its close ceremony deliberately never ran and flipping its gate would assert a ceremony that did not happen. Both are excluded by ID with an inline reason. That mapping is currently a module-level constant in vendored driver source, so a downstream project cannot declare an exclusion of its own without patching a file the next upgrade overwrites — a known sharp edge recorded in the retrospective, not yet addressed.

**Consumer note.** The new `lint_plan` error is blocking and repo-wide: a project that upgrades its scaffold while holding a `done` feature with an unclosed gate will start failing its plan-lint gate on the first run after upgrade, with no change of its own. The remedy is the reconciliation T03 performed — flip gates that genuinely completed, exclude by ID and written reason any whose close deliberately never ran.

**Status: active.**

<a id="feat-2026-0071"></a>
## FEAT-2026-0071 — Label registry + provisioning on init/upgrade

**Why.** Specfuse ships code that queries GitHub labels it never creates. `gh_features.py:28` has run `gh issue list --label specfuse:feature` since FEAT-2026-0003, and [FEAT-2026-0046](roadmap-archive.md#feat-2026-0046) added six more (`needs-human` plus the five escalation categories) whose emitter fails outright on an unknown label — `gh issue create` rejects one. Seven labels, zero provisioning: every consumer repo has to be told to create them by hand, and 0046's own retrospective had to record that as a required operator step rather than something the tool does. Each new label repeats the gap, so the fix is a declared registry rather than a hardcoded list.

**Goal.** Ship (a) a single label registry — name, colour, description, and the consumer that reads it — as the one place a label is declared, with the seven current entries; and (b) provisioning on `specfuse init` and `specfuse upgrade` that creates any missing label and leaves existing ones untouched.

**The constraint that shapes it.** `scaffold.py` has no subprocess, network, or `gh` call today: init and upgrade are pure filesystem, which is why they work offline, in CI containers, and against non-GitHub remotes. Provisioning must not change that contract. It is **best-effort and never fatal** — no `gh`, not authenticated, remote is not GitHub, not a git repo at all, or any per-label failure reports what it would have done and the command still exits zero. An upgrade must never fail because a label could not be created. Idempotent by construction: existing labels are skipped, never `--force`d over an operator's edited colour or description. The opt-out is the `SPECFUSE_NO_LABELS` environment variable plus a `no_labels=True` keyword argument — **not** a `--no-labels` CLI flag, which would need a coordinated umbrella release because `specfuse/cli.py` lives in the umbrella repository. A future umbrella change can add the flag reading the same variable.

**Scope boundary.** `specfuse-monitor` is **out**: it appears only in [FEAT-2026-0040](#feat-2026-0040)'s framing, its harvester does not exist, and provisioning a label whose sole consumer is unbuilt repeats the `[FEAT-2026-0029/G1-CLOSE]` failure 0039 recorded — shipping a surface whose entry point is nonexistent. 0040 adds its own entry when it ships. Renaming `specfuse:feature` to match the kebab-case of the six newer labels is also out: the inconsistency is real, but a rename orphans issues already carrying the label in every consumer repo.

**Benefits.** The escalation queue works on a fresh repo without a setup checklist, closing the operator step 0046 had to defer. `specfuse:feature` discovery stops depending on an undeclared label. And the next feature that needs a label adds one registry entry instead of rediscovering that nothing creates it.

**What shipped.** One terminal gate, three work units, all passing first attempt. `specfuse/loop/labels.py` carries `LABEL_REGISTRY` — seven frozen `LabelSpec` entries whose *names* are imported from `escalation.NEEDS_HUMAN_LABEL`, `escalation.CATEGORY_LABELS`, and a new module-level `gh_features.FEATURE_LABEL` constant (the literal formerly inlined at the `gh issue list` call site), with a test that recomputes that set at test time so the registry cannot drift from what the consumers query. The same module ships `provision_labels(target, *, runner=None)`, following the injectable-runner seam `gh_backend.GitHubBackend` and `escalation.emit_escalation` already use: it lists first and creates only what is missing, never passes `--force`, and returns a `ProvisionReport` (created / already_present / failed / skipped / reason) on every degradation path rather than raising. `scaffold.init()` and `scaffold.upgrade_specfuse()` call it through a `_provision_labels_best_effort()` wrapper that swallows even unexpected exceptions and reports to **stderr only** — the returned list of written `.specfuse/` relpaths is unchanged, which 64 pre-existing scaffold tests assert. Provisioning is wired into `init()`, not `init_specfuse()`.

**Deferred to a post-merge operator step.** No work unit invoked a real GitHub repository — every `gh` interaction ran through an injected stub, so the real `gh label create` argument vector and the successful `gh label list` JSON parse are unverified. This repository's seven labels already existed before the feature was drafted, which makes it an oracle for the idempotent-skip path and not for the create-a-missing-label path. The one real-binary observation is the not-a-git-repository degradation, which the regression suites exercise incidentally. See `RETROSPECTIVE.md` §`What the loop did NOT verify` for the exact re-runs that settle each.

**Status: active.**

<a id="feat-2026-0046"></a>
## FEAT-2026-0046 — Escalation contract: needs-human issues (assigned, structured) + /attention inbox skill

**Why.** An autonomous agent is only trustworthy if what it cannot handle surfaces reliably, with enough context to act on in minutes. Escalations need one queue with an audit trail — GitHub issues, not chat threads — plus a fast local view. Useful immediately with today's manual loop (blocked WUs, awaiting_review gates, blocked features, stale PRs), before any agent exists.

**Goal.** Ship (a) the escalation contract: a `needs-human` labeled GH issue per escalation, auto-assigned to the configured `assignee` (per-category assignee map supported) so escalations surface in native GH inbox/filters; body in plain English — context, options with pros/cons, a recommendation, numbered answers ("reply `1`, `2`, or prose") so the agent can parse replies unambiguously; category labels (gate-review, blocked-wu, triage-question, drafting-needed, merge-approval); answered issues are parsed, acted on, and closed by the next agent run. (b) The `/attention` skill: local inbox over the same label set plus repo-state sweep (gate-status generalized repo-wide), presenting everything needing the human in priority order — the interactive counterpart of the issue queue, never a second source of truth.

**Benefits.** One escalation queue, two views (GH native + rich local session); nothing the agent parks goes silent; the operator's check-in ritual becomes "open /attention, work top-down".

**Delivered** (gate 1, terminal — see [RETROSPECTIVE](features/FEAT-2026-0046-escalation-contract/RETROSPECTIVE.md)). `specfuse/loop/escalation.py`: `NEEDS_HUMAN_LABEL`, the five-member `CATEGORY_LABELS` frozenset (gate-review, blocked-wu, triage-question, drafting-needed, merge-approval), `render_escalation_body` producing the six-part body from `operator-escalation.md` plus a `Reply with a number` section and the `<!-- specfuse:escalation id=… -->` correlation marker, `validate_escalation_body` holding the renderer to that shape, and `emit_escalation` — idempotent per correlation ID via find-then-create over an injectable runner, mirroring `gh_backend.GitHubBackend`'s `_runner` seam. The `/attention` skill ships canonical at `plugins/specfuse/skills/attention/SKILL.md`, vendored byte-identically into `.specfuse/skills/`, sweeping blocked WUs, `awaiting_review` gates, `blocked` features and stale PRs into one priority-ordered view and delegating per-feature depth to `gate-status`. Its read-only claim is enforced by a grep guard with a positive control over both copies, not by prose. 21 tests across four new modules, plus the 4-test vendoring guard.

**Deviations from the goal above, each deliberate.** Assignment is a single `assignee` parameter defaulting to `DEFAULT_ASSIGNEE`; the per-category assignee map is not built — no caller needed one, and the parameter is the seam that would carry it. Parsing an answered issue and closing it is [FEAT-2026-0049](roadmap.md#feat-2026-0049), which lists this contract as its blocker. Outbound notification is [FEAT-2026-0047](roadmap.md#feat-2026-0047). `emit_escalation` is invoked, never auto-fired: no call site exists in `loop.py`, asserted by a grep, per `[FEAT-2026-0003/G3-LESSONS]` on live-mutation work inside the dispatch loop.

**Operator step before first real use.** No work unit touched live GitHub — every `gh` interaction ran through an injected stub. Create the six labels in the target repository and run one real emission twice to confirm the create call and the idempotency search; the retrospective's `## What the loop did NOT verify` section carries the detail and the fallback if the marker search does not match.

**Status: active.**

<a id="feat-2026-0070"></a>
## FEAT-2026-0070 — Terminal-flip contract: hedged-verdict acceptance, row-status breadth, auto-close debt

**Why.** Three issues, one symptom: **a correctly-closed feature whose recorded state lies.** [#226](https://github.com/specfuse/loop/issues/226) — an `autonomy: auto` feature self-dispatches from a `planned` row, but `fire_terminal_flips` only handles `active -> done`, so the row never flips and the `roadmap_row_not_done` invariant escalates on a correct close. [#243](https://github.com/specfuse/loop/issues/243) — a close writing `verdict: met_locally` leaves every WU `done`, the gate `awaiting_review`, and PLAN + roadmap `active`, with no supported path to `done`; for some features `met_locally` is the ceiling by construction, not by accident, and `/wrap-feature` refuses them by hard rule. [#241](https://github.com/specfuse/loop/issues/241) — an auto-closed gate skips the per-criterion deferred-verification walk and nothing downstream is obliged to reconcile it. All three were observed on real closes in this repo.

**Goal.** Gate 1 makes a correctly-closed feature reach `done` **through the driver** from every legitimate starting state: broaden the row flip to any non-`done` status (#226); add a driver-side primitive that re-evaluates a completed close WU's verdict and fires the flips when it now permits them; build `/accept-hedged-close` on that primitive so accepting a standing hedge leaves an auditable record instead of three hand-edits (#243); and land the pre-registered `lint_plan` verdict-exempt fix from `[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]`. Gate 2 makes an auto-closed gate's skipped ceremony a visible debt rather than a silent saving (#241), drafted by `plan-next` once the flip contract has settled.

**Benefits.** Terminal state stops being hand-edited — which happened twice in one session on FEAT-2026-0069 and left no record of why. The `autonomy: auto` path stops escalating on correct closes. And the honest hedged verdict stops being a dead end, so a feature whose ceiling is `met_locally` by construction can ship without either overstating its verdict or lying on the roadmap.

**The constraint that outranks everything else.** `[FEAT-2026-0023/G1-CLOSE]`: **terminal-state flips have exactly ONE driver-side owner, called identically by every close path** — issue #49 existed because two paths diverged. `/accept-hedged-close` must therefore call the driver primitive, never write the three surfaces itself. A WU that hand-writes a terminal surface has failed this feature even with every gate green, and both closes audit it explicitly.

**Held at drafting, deliberately not built.** #243's candidate 2, a roadmap status between `active` and `done` (`done_hedged`): a new status value is a contract every downstream project, every skill, and `lint_plan`'s row parser reads, and `done` carrying an open-follow-up count gets most of the benefit without a new enum member. And #243's candidate 3, pre-declaring the `met_locally` ceiling at draft time: real value, but it is prevention rather than repair and does not help the features already in the dead end — the natural follow-up feature if gate 1 lands cleanly.

**Outcome.** Both gates shipped; all eight substantive work units passed on their first recorded attempt, across two gates and ten dispatched sessions. Terminal verdict **`met_locally`** — see `.specfuse/features/FEAT-2026-0070-terminal-flip-contract/RETROSPECTIVE.md` § *Hedged follow-up record* for the seven-entry record and the exact condition that upgrades each one.

- **[#226](https://github.com/specfuse/loop/issues/226) — resolved.** `fire_terminal_flips` now replaces whatever non-`done` value the roadmap row's Status cell holds, instead of handling only the `active -> done` transition. An `autonomy: auto` feature that self-dispatched from a `planned` row reaches `done` rather than escalating `roadmap_row_not_done` on a correct close. Three tests, including a regression guard proving `active -> done` is bit-identical to before.
- **[#243](https://github.com/specfuse/loop/issues/243) — resolved via candidate 1, with a second defect closed that the issue did not report.** `recheck_terminal_verdict(feature_dir, repo_root)` plus `--recheck-verdict FEATURE_ID` re-reads a *completed* close WU's verdict from disk and calls the existing `fire_terminal_flips` when it now permits the flips; `/accept-hedged-close` is the operator path built on top of it. The unreported defect: `fire_terminal_flips` runs at close-WU-*outcome* time, so a verdict legitimately upgraded after the close WU reached `done` was never re-read — which is what forced FEAT-2026-0069's three surfaces to be hand-flipped. **The constraint held:** the skill calls the primitive and writes no terminal surface, audited fresh at both closes.
- **[#241](https://github.com/specfuse/loop/issues/241) — resolved via options 1 and 3.** Both auto-close stub writers now enumerate the gate's unwalked acceptance criteria as a concrete `deferred:` worklist and emit a machine-readable debt marker; the post-pass invariant `assert_autoclose_debt_reconciled` refuses a terminal close that ignores a marked predecessor's debt; and a `lint_plan` WARN predicts that refusal at arm time so the guard costs a lint line rather than a re-dispatch. The invariant is **marker-gated**: the obvious form fires on 6 of the 11 correctly-closed features that have auto-closed a gate, and was rejected at arming as unsatisfiable; the shipped form reports zero across all 36 features on disk, re-verified at the terminal close.

**Still held — open, not closed by this feature.** Restated so that holding them does not read as resolving them. Both remain #243 candidates and both are the natural content of the flip-contract follow-up feature, alongside `/accept-hedged-close`'s laundered hedge (accepting a hedge overwrites `verdict: met_locally` with `met`, so an accepted hedge is byte-identical to a clean one — `verdict_accepted_from` / `_reason` / `_at` is the fix) and the missing `--recheck-verdict` CLI-level test:

- **#243 candidate 2 — a roadmap status between `active` and `done`** (`done_hedged` or similar). Still open. The reasoning for holding it is unchanged and was not re-tested by this feature: a new status value is a contract every downstream project, every skill, and `lint_plan`'s row parser reads. Revisit only if the acceptance path proves insufficient in practice — which, with `/accept-hedged-close` not yet run against a real hedged feature, is not yet knowable.
- **#243 candidate 3 — pre-declaring the `met_locally` ceiling at draft time.** Still open. It is a `/draft-feature` interview change, prevention rather than repair, and it does not help features already in the dead end. This feature's own `met_locally` verdict is a live argument for it.

**Status: active** — the terminal flips are withheld by design on a hedged verdict. `PLAN.md`, the gate, and this row stay un-flipped until an operator accepts the close through `/accept-hedged-close`, which is the path this feature shipped. The driver owns that flip; it is not hand-edited.

<a id="feat-2026-0051"></a>
## FEAT-2026-0051 — Pre-flight baseline gate probe + preexisting_gate_failure halt

**Why.** A `code`-set gate that is already red on the feature's base commit becomes every work unit's exit oracle, so each WU spins to `spinning_signature_repeat` / `spinning_detected` against a failure it did not cause and could not fix. A live run burned roughly $8 of attempt budget across two WUs — one of them a zero-dependency file — on a dependency-audit advisory published after the base tree was last green, with the lockfile byte-identical to the integration branch. This is the time-varying-oracle failure mode already recorded in LEARNINGS (`[FEAT-2026-0007/G1-CLOSE]`); dependency audits are the canonical case, but it generalizes to any externally-fed gate whose verdict changes without a code change.

**Goal.** Run the `code` gate set once at gate entry, before the gate's first WU is dispatched, and record the failing gates plus their signatures as the gate's baseline in `GATE-NN.md` frontmatter. A non-empty baseline halts pre-dispatch under a new `preexisting_gate_failure` reason — distinct from the spinning escalations, which fire only after attempts are spent — with zero work units dispatched. The halt message states in plain language which gate is red, the exact failing signature, and the `git diff <integration-branch>...HEAD --stat` proof that the base tree is unchanged, so no WU caused it. The baseline is re-measured only when the tree moves, keeping resume cheap, and `--no-baseline-probe` (plus a `verification.yml` opt-out) restores today's behavior exactly — a switch that disables the probe, not a mute that suppresses any gate's verdict.

**Benefits.** Repo-wide debt stops charging rent per work unit: one gate-set run replaces a full attempt budget burned per WU, and the operator gets the conclusion — pre-existing, not yours — in the first escalation instead of deriving it by hand after several spurious ones. Enforcement is untouched: every WU is still gated on the full set with unchanged pass/fail semantics.

**Scope note.** The baseline-delta ratchet, the waiver that lets a feature proceed against a red baseline, and `gh` tracking-issue emission are deliberately deferred to [FEAT-2026-0052](roadmap.md#feat-2026-0052) — the ratchet rewrites the pass/fail semantics of the driver's own exit oracle, and the `gh` surface produces no in-loop evidence. Landing the brake first lets that work be designed against real baseline data. Filed from issue #234.

**Status: planned.**

<a id="feat-2026-0037"></a>
## FEAT-2026-0037 — Evaluate adopting ruff 0.16's expanded default ruleset (opt-in the valuable families)

**Why.** FEAT-2026-0036 pinned the lint `select` to the classic `E4,E7,E9,F` to stop a version bump from silently changing the gate — the right move for stability, but it deliberately declined the ~300 findings ruff 0.16 now surfaces by default. Some of those families are genuinely valuable and worth adopting on purpose: `PLW1510` (`subprocess.run` without `check=` — a real correctness smell in a driver that shells out constantly), `RUF059` (unused unpacked bindings), `SIM117`/`SIM102` (nested-`with` / collapsible-`if`), `LOG015` (root-logger use), `B`/`S` (bugbear / security). This feature decides — deliberately, family by family — which to add, and does the fixes.

**Goal.** Triage ruff 0.16's expanded default families against this codebase: for each, decide adopt / decline (with a one-line reason), add the adopted ones to `[tool.ruff.lint] select`, and fix the findings — the semantic ones (e.g. `subprocess check=`) reviewed individually, not blanket-autofixed. Land per-family or in small reviewable batches, not one 300-line sweep. Some findings are in `tests/` and low-stakes; prioritise the `specfuse/` driver and `.specfuse/scripts/` surfaces.

**Benefits.** Turns an accident (an upstream default change) into an intentional quality bar; catches real defects (unchecked subprocesses especially matter in the driver); keeps the ruleset a considered choice rather than either "whatever the classic default was" or "whatever ruff decides to add next."

**Status: planned.**

<a id="feat-2026-0032"></a>
## FEAT-2026-0032 — Non-WSL Windows execution (native driver + Git-Bash)

**Why.** Loop requires WSL on Windows today. WSL is blocked on many corporate-managed devices and too heavy for non-technical users, excluding exactly the population that needs turnkey execution.

**Goal.** Run the loop driver on native Windows (no WSL): make the driver importable and runnable, route gate commands through Git-Bash, and prove it with a windows-latest CI leg.

**Benefits.** Removes the WSL prerequisite; unblocks corporate-managed and non-technical Windows users; driver is already stdlib-only so port surface is ~6 call sites (fcntl lock, killpg/SIGKILL timeout, python3 literal, shell=True gate semantics, bare-claude PATHEXT resolution, POSIX-only home-redaction regex); Git-Bash absorbs shell/bats/&&-exit gates for free.

**Status: done.**

<a id="feat-2026-0031"></a>
## FEAT-2026-0031 — Configurable integration branch

**Why.** A feature branch is cut from whatever HEAD happens to be — `ensure_feature_branch`
runs a bare `git checkout -B <branch>` with no base ref — and the GH backend hardcodes
`gh pr create --base main`. Teams working off a long-lived integration or release branch
therefore cannot use the loop without wrong-target PRs (or a `gh` failure where no `main`
exists). Cutting from a non-default base does work today, but only by accident: nothing
validates that HEAD is the intended base, nothing records what the base was, and the
staleness guard's rebase hint points at the current branch rather than a configured one.

**Goal.** Make a feature's base branch an explicit, recorded property instead of implicit
operator state. Add an optional `base` key to PLAN.md frontmatter, linted alongside the
existing required `branch` key; thread it into `checkout -B <branch> <base>` and into the
PR-create call in place of the literal `main`; resolve the staleness guard and its rebase
hint against the same base. Default to the existing repo-default detection helper rather
than a hardcoded string. Settle precedence explicitly: frontmatter is the truth (base is a
property of the feature, surviving across driver runs and operators), an optional CLI flag
overrides, repo-default detection is the fallback — HEAD-implicit stops being load-bearing.

**Benefits.** Unblocks release- and integration-branch workflows, which the loop currently
cannot serve. Removes the last hardcoded `main` from the PR path. Makes the base auditable
across driver runs and operators instead of dependent on which branch the human happened to
have checked out, which also closes the silent-wrong-base failure mode.

**Status: active.**

<a id="feat-2026-0025"></a>
## FEAT-2026-0025 — LEARNINGS curation + archival (bound planning-context growth)

**Why.** `.specfuse/LEARNINGS.md` is append-only and loaded **whole** into
planning context by `/draft-feature`, `/pick-feature`, `plan-next`, and
`/authoring-work-units`. After ~20 features it is already ~86 entries / ~24k
tokens (~4 entries/feature, growing unbounded). The driver enforces appends
(`assert_learnings_appended_or_noop`) but nothing prunes: there is no
archival/compaction counterpart the way `roadmap.md` has `roadmap-archive.md` +
`auto_archive_feature`, and `learnings-suggest` only ADDS candidates. Left
unchecked this inflates every planning session's context cost and dilutes signal
as superseded/duplicate rules accumulate. Surfaced reviewing FEAT-2026-0024
(whose `LEARNINGS.template.md` split already separated portable methodology
wisdom from this repo's feature-specific history).

**Goal.** A curation/archival mechanism that bounds the planning-loaded LEARNINGS
to the active, durable set: (1) a `LEARNINGS-archive.md` + a curation step that
moves feature-specific or obsolete entries out of the planning-loaded file
(mirroring `auto_archive_feature`); (2) promotion of broadly-applicable rules
into the binding `.specfuse/rules/*.md` (curated, small, always-loaded), leaving
LEARNINGS as a staging area; (3) a `/learnings-curate` skill — the
read/compaction counterpart to `learnings-suggest` — that merges duplicates,
retires superseded entries, and flags promotion candidates for the operator;
(4) later, indexed retrieval so consumers load only the relevant slice instead
of the whole file.

**Benefits.** Planning-context cost stays bounded as the repo scales to hundreds
of features. Higher signal — a curated durable set beats append-only sprawl when
the planner (human or agent) is hunting the rule that applies. Durable rules
graduate into binding contracts. Portable methodology wisdom stays cleanly
separated from feature-specific history. Closes the missing half of the
methodology's feedback loop: today it can only grow, never compact.

**Status: planned.**

<a id="feat-2026-0030"></a>
## FEAT-2026-0030 — Driver-side sanitization of agent-authored text before events.jsonl staging

**Why.** The loop driver writes agent-authored free-text (blocked reasons,
failure notes) into `events.jsonl`, then stages and commits that audit trail. When
the text happens to contain a token the repo's structural leak-scan flags — e.g. an
absolute home-directory path (a `~`-expanded checkout location) the agent mentioned
while explaining where it searched — the pre-commit hook rejects the bookkeeping commit and the gate halts
mid-run. Observed live on FEAT-2026-0029/T01 (driver 0.3.6): the agent's
`blocked_reason` quoted a local checkout path, tripping `user-path` findings on
`events.jsonl` lines 29-30. This is the same failure family as the now-closed #76
(which redacted the leak hook's *own* FINDINGS text) and #73 (the general form),
but a distinct, still-uncovered source: **agent-authored** note text, not
hook-captured FINDINGS. #76's fix does not cover it.

**Goal.** A single driver-side sanitization pass applied to *all* agent-authored
strings before they are written into `events.jsonl` (or at minimum before the
bookkeeping commit is staged): redact absolute home-directory prefixes (the
`~`-expanded macOS and Linux forms) and any other token the structural leak-scan
flags, to a placeholder,
preserving the audit signal without re-embedding the trigger. Retires the residual
per-token allowlist band-aids and closes the systemic self-poison class for note
text, not just captured-FINDINGS text.

**Benefits.** Bookkeeping commits stop halting the gate on benign local paths that
leak into agent prose; the audit trail still records *that* and *why* a WU blocked;
one sanitization chokepoint replaces scattered redaction. Removes a recurring
operator-recovery chore (manual redact-and-commit) from real runs. Small, driver-
local (`loop.py`), test-backed (feed a note containing a user path → assert the
staged events.jsonl passes `leak_scan.py --staged`).

**Status: planned.**

<a id="feat-2026-0029"></a>
## FEAT-2026-0029 — One-command Specfuse scaffold upgrade skill

**Why.** Upgrading a project's Specfuse scaffold today means a human hand-runs
`specfuse upgrade` then repeats the same git choreography every time — branch off
origin/main, run the upgrade, commit, push, open a PR, merge. It's repetitive,
easy to get wrong (upgrading a dirty tree, branching off a stale local main), and
there's no single entrypoint.

**Goal.** A Claude Code skill that performs a scaffold upgrade end-to-end on a
target project: (1) dry-run mode reports what the upgrade would change without
writing; (2) live mode opens a chore branch off the latest origin/main, runs
`specfuse upgrade`, commits, pushes, opens a PR, and merges on green.

**Benefits.** One command replaces a multi-step manual ritual; always branches off
fresh origin/main (no stale-base bugs); dry-run preview before any write. The
merge step is gated on BOTH CI-green AND a clean post-upgrade health report — if
the upgrade flags conformance FAILs, the skill halts before merge and hands off to
`/feature-conversion` rather than landing a broken scaffold. It wraps the existing
`specfuse upgrade [--dry-run]` CLI, so it adds orchestration only, not new upgrade
logic.

**Status: planned.**

<a id="feat-2026-0026"></a>
## FEAT-2026-0026 — Scaffold-data in the pip package: `specfuse init` replaces init.sh

**Why.** FEAT-2026-0019 shipped the pip driver (`specfuse-loop`), the `specfuse`
umbrella CLI, and the Claude Code plugin — but `specfuse init` cannot yet scaffold a
new repo from pip alone: the scaffold data (`templates/`, `rules/`,
`verification.yml.example`, `roadmap.template.md`, `LEARNINGS.template.md`) still lives
in the loop repo and ships only via the bash `init.sh`. So `init.sh` remains the
bootstrap and carries a v1.0 deprecation banner it cannot yet honor — v1.1 cannot
delete it until pip-native scaffolding exists. Surfaced in FEAT-2026-0019's gate-4
retrospective (terminal verdict's recommended follow-up).

**Goal.** Ship the scaffold data inside the `specfuse-loop` (or `specfuse`) package and
have `specfuse init <repo>` lay down a target's `.specfuse/` from package resources,
fully replacing `init.sh`.

- Package the templates/rules/examples as package data, loaded via
  `importlib.resources` (no reliance on a source checkout).
- `specfuse init` writes `.specfuse/` (templates, rules, verification.yml seed,
  roadmap + LEARNINGS seeds, `.specfuse/VERSION` stamp) and wires `.claude/` — the
  `init.sh` behavior, in-process and pip-delivered.
- `specfuse upgrade` overlays the versioned scaffold from the installed package
  version (the `--upgrade` path), so upgrades follow `pip install -U`.
- Delete `init.sh` (v1.1) once parity is proven; keep a thin curl-bash bootstrap only
  for the no-pip first-touch case if still needed.

**Benefits.** `init.sh`'s deprecation becomes real (v1.1 deletion unblocked). One
delivery channel (pip) for both code and scaffold; offline/sandboxed installs work
from the wheel; version-skew between scaffold and driver collapses to the package
version. Closes the last gap between FEAT-2026-0019's vision and what shipped.

**Gate sketch (drafted at /draft-feature time).**
- G1 — package the scaffold seed (templates, rules, examples, roadmap/LEARNINGS
  templates, gitignore lines, VERSION) + a resource-loading API via
  `importlib.resources`. Decision: `specfuse-loop` owns the data; the umbrella CLI
  calls into it.
- G2 — `specfuse init <repo>` writes a fresh `.specfuse/` (+ `.gitignore`, VERSION
  stamp, `.claude` wiring) from package resources — parity with `init.sh` INIT.
- G3 — `specfuse upgrade <repo>` overlays versioned files (parity with `--upgrade`:
  preserve user-authored, prune internal, stamp); deprecate then delete `init.sh`
  (v1.1).

**Status: active.** Depends on FEAT-2026-0019 (the package + CLI it extends).
Packaging/harness-coupled — per LEARNINGS `[FEAT-2026-0019/G1]`, expect to run this
interactively (atomic), not per-WU loop dispatch.

<a id="feat-2026-0024"></a>
## FEAT-2026-0024 — Hashed denylist + issue/PR-body leak guard

**Why.** Closes the two leak-guard surface gaps FEAT-2026-0020's review
surfaced (GitHub issues #45, #46), both rooted in LEARNINGS
`[FEAT-2026-0020/G2/leak-guard-surface-asymmetry]`. (1) `leak_scan.py`'s
denylist (`leak_denylist.txt`) is gitignored — committing the literals to a
public repo would re-leak them — so in CI the `--all` gate enforces gitleaks
secrets only, NOT org-name re-introduction. (2) The pre-commit hook scans git
commits only; GitHub issue/PR titles, bodies, and comments are a separate
public surface it can't see — exactly where the FEAT-2026-0020 leaks landed.

**Goal.** Two gates. Gate 1 (#45): a committed, salted-SHA-256 hashed denylist
(`leak_denylist.hashes`) that CI loads, giving `scan_repo`/`--all` org-name
coverage without exposing the literals; a `leak_scan.py --hash-denylist`
generator keeps it in sync with the gitignored plaintext. Gate 2 (#46): a
GitHub Action triggered on `issues` + `pull_request` (open/edit) that runs the
scanner + hashed denylist over titles/bodies/comments and fails/comments on a
hit.

**Shape.** Hashing can't substring-match, so the chosen design normalizes each
literal (lowercase, strip non-alphanumeric) and matches via a char-sliding
window at a committed distinct-length set — preserving the plaintext denylist's
substring fidelity (`acmewidget` ⊂ `AcmeWidgetApp`) while leaking only a
handful of small integers, never content. Honest caveat: low-entropy names + a
public salt = obfuscation, not secrecy; the guard catches accidental
re-introduction. Gate-1 substantive WUs are `opus`/`high`, red-test-first
(leak-guard correctness path). `autonomy: review` halts at the gate boundary.

**Scope OUT.** Expunging GitHub edit-history (GitHub retains body revisions —
the Action stops new leaks only; documented limitation). Replacing the plaintext
denylist (stays as local-convenience source). Hashing the pre-commit `--staged`
surface (plaintext present locally). `act`/Docker Action emulation in-loop
(gate-2 live trigger is operator-verified post-merge). Cost levers.

**Status: planned.** Two gates, both independently shippable; gate 2 consumes
gate 1's committed hashed denylist. `planned_cost_usd: 11.50` covers the five
WUs that exist now; `plan-next` revises when gate 2's Action WUs are drafted.

<a id="feat-2026-0023"></a>
## FEAT-2026-0023 — Lifecycle integration test + consolidate terminal-state ownership

**Why.** Three driver bugs surfaced in a single session (2026-06-16), all of
the same shape — **seam bugs at handoffs between subsystems**, none catchable
by the existing 749 unit tests because unit tests stub the handoffs:

- **#47** (fixed in #47) — `/draft-feature` emits a roadmap row only;
  `auto_archive_feature` assumed an inline detail section, so an auto-closed
  drafted feature halted on `archive_anchor_missing`.
- **#48** — `ensure_feature_branch` crashes with a raw traceback when a dirty
  working tree (the `/pick-feature` status flips) or a stale pre-existing
  branch blocks the checkout.
- **#49** — terminal **auto-close** leaves `PLAN.md status: active`: the normal
  close path relies on the close WU's *agent* to flip PLAN.md, and the
  auto-close path runs no agent while `fire_terminal_flips` never touches
  PLAN.md.

Root pattern: the methodology's machinery (auto-close predicate 0018,
draft-feature skill, archive automation 0010) grew faster than its integration
coverage, and the gaps only execute at real feature boundaries — rare events
that the first true end-to-end **autonomous** runs (`autonomy: auto` / predicate
close) finally exercised without a human silently papering over each seam.

**Goal.** Close the class, not the three instances.

1. **End-to-end lifecycle integration test.** A test harness that drives a
   synthetic feature through the full lifecycle in one run — draft → pick →
   loop dispatch → terminal close (BOTH the dispatched-close and the
   auto-close-predicate paths) → archive → wrap-ready — and asserts the
   terminal invariant holds: `PLAN.md=done`, `GATE=passed`, roadmap row `done`,
   archive anchor present, RETROSPECTIVE present. Parameterized over close path
   (normal vs auto-close) and feature shape (single-gate vs multi-gate;
   row-only vs detail-section). This is the layer that would have caught all
   three bugs before they hit a live run.

2. **Consolidate terminal-state ownership.** Today the PLAN/GATE/roadmap/archive
   flips are scattered across the close WU's agent, `fire_terminal_flips`, and
   `auto_archive_feature` — #49 exists precisely because one flip lived in the
   agent for one path and nowhere for the other. Make a single driver-side
   function the authoritative owner of every terminal flip (PLAN.md included),
   called identically by both close paths, idempotent, with the hedged-verdict
   revert kept consistent. Subsumes the #49 fix.

3. **Harden the branch seam (#48).** `ensure_feature_branch` surfaces git's
   stderr instead of a traceback, carries expected `/pick-feature` flips onto
   the new branch, and detects a stale/divergent existing branch. May fold in
   here or ship as the standalone #48 bug fix — decide at draft time.

**Scope OUT.** New lifecycle *features* (this adds test + refactor coverage of
the existing lifecycle, not new behavior). Rewriting the auto-close predicate
itself (0018 stands). The per-bug hotfixes that are cheaper as standalone bug
branches (#48 especially) if they're needed before this feature is pulled.

**Status: planned.** Likely single gate: WU per lifecycle-path test +
terminal-ownership consolidation WU + closing ceremony. Pull before the next
feature that exercises an untested close-path combination.

<a id="feat-2026-0021"></a>
## FEAT-2026-0021 — Ceremony proportionality + slim WU template

_No inline detail section was recorded for this feature; stub written at archive time._

<a id="feat-2026-0022"></a>
## FEAT-2026-0022 — Deliverable-presence gate: machine-enforce per-WU `produces:` + empty-files escalation

**Goal.** The driver refuses to commit an implementation WU as `done` when a
declared deliverable is absent or empty, or when the WU touched zero files —
closing the zero/partial-deliverable hollow-pass class FEAT-2026-0008/0015 left
open. Filed from GitHub issue #41 and LEARNINGS
`[FEAT-2026-0020/G2/hollow-pass-presence-gates]` (T16 passed `done` touching
zero files at ~$1.48; T12 created `SECURITY.md` but not the bundled
`CODE_OF_CONDUCT.md`).

**Shape.** Single terminal gate, three driver-side guards + `close`, mirroring
FEAT-2026-0008. T01 adds the `produces:` WU frontmatter field (parse +
`WorkUnit.produces` + advisory lint WARN). T02 (`assert_declared_deliverables`)
blocks a `complete` whose declared `produces:` path is absent or empty. T03
(`assert_implementation_touched_files`) blocks an `implementation` WU whose
attempt touched zero deliverable files, independent of `produces:`.

**Scope OUT.** Symbol-level presence (`grep -q`), retrofitting `produces:` onto
existing WUs, broadening the verification contract, cost levers.


<a id="feat-2026-0003"></a>
## FEAT-2026-0003 — GitHub feature-pick for the loop

**Why.** Teach the loop to adopt a feature dispatched by the Specfuse
Orchestrator — so an orchestrator can hand a feature to a component repo's loop
and the loop grinds it through its gate cycle — in addition to today's
locally-authored `.specfuse/features/` flow. Full brief:
[`docs/handoff-github-feature-pick.md`](../docs/handoff-github-feature-pick.md).

**Gate 1 (passed).** The read path: extended the loop's correlation-ID grammar
to admit orchestrated `INIT-YYYY-NNNN/FNN[/TNN]` IDs alongside `FEAT-…`
component-local IDs (rule + linter + tests); added
`.specfuse/scripts/gh_features.py`, a discovery script that lists a target
repo's `specfuse:feature` issues as feature candidates (injectable `gh` runner
for fully offline unit testing). Both implementation WUs completed in one
attempt with no escalations. GATE-01 status: `passed`.

**Gate 2 (passed).** The write/adopt path: `.specfuse/scripts/adopt_feature.py`
scaffolds a dispatchable loop-feature folder from a picked `specfuse:feature`
issue — PLAN.md frontmatter (including `source_issue_url` and `initiative` when
present), GATE-01/02 files, WU-01 seeded verbatim from the raw issue body, and
gate-1 closing WUs 90–93 with generic placeholder bodies. `gh_features.py`
widened by one line to expose issue `body`. The `/adopt-feature` interactive
skill wraps the script as a pick-list-then-adopt flow. Both implementation WUs
completed in one attempt with no escalations. GATE-02 status: `passed`.

**Gate 3 (passed).** Report-back and smoke: `Backend` seam widened with three lifecycle
hooks (`on_feature_start`, `on_gate_passed`, `on_feature_complete`) and a `make_backend(feat_fm)`
factory (T05); `GitHubBackend(Backend)` label-transition backend in `gh_backend.py` using the
canonical `state:ready → state:in-progress → state:done` scheme, factory selects it when
`source_issue_url` is present in PLAN.md frontmatter (T06); live smoke of `INIT-2026-0001/F06`
(`example-org/example-app#287`) run out-of-loop by human operator — discovery, adopt, and
report-back all PASS, `#287` fully restored post-smoke (T07). **Finding:** the adopted folder
failed `lint_plan.py` because orchestrator issue bodies use `## ATX` headings; the linter only
recognised `**bold**`/plain. Fix delivered in gate 4. GATE-03 status: `passed`.

**Gate 4 (passed).** ATX-heading linter fix: broadened `lint_plan.py`'s mandatory-section
detector to a union pattern (`^(?:#+\s*|\**)`) that accepts both Markdown ATX headings
(`## Context`) and the existing bold-preamble (`**Context.**`) form (T08). The adopted
`INIT-2026-0001-F06-…` folder now passes `lint_plan.py` exit-0, and existing bold-headed WU
bodies remain clean (regression guard). GATE-04 status: `passed`.

**Status: done.** All four gates passed. All four pipeline mechanisms — discover, adopt,
report-back, lint-clean grind — are proven live against `example-org/example-app#287`. The
`roadmap_goal` is met. See `RETROSPECTIVE.md §Feature-arc retrospective` and
`SMOKE-INIT-2026-0001-F06.md`.

<a id="feat-2026-0004"></a>
## FEAT-2026-0004 — Single-driver working-tree lock

**Why.** Two `loop.py` drivers sharing one working tree clobber each other: the
driver's per-WU `git reset --hard` and `git checkout -B` are tree-global, so any
interleaving corrupts WU state and mixes commits across units. Observed during the
FEAT-2026-0003 dogfood: a sandboxed `ps` falsely reported the first driver as dead,
a second was launched, and competing resets produced commits mixing multiple WUs'
work plus contradictory WU statuses. True parallelism across features uses separate
`git worktrees` — each worktree has its own working tree and therefore its own lock.

**Gate 1 (passed).** Advisory lock on the working tree: `loop.py`'s `run()` acquires
a non-blocking exclusive `fcntl.flock` on `.specfuse/.loop.lock` before any
git-mutating call; a contending driver exits non-zero with a clear stderr message and
touches no git or WU/GATE state; the lock auto-releases on process exit including
SIGKILL (no stale-lock cleanup path). `--dry-run` is exempt (no mutation; inspecting
while a real run is active must stay allowed). `init.sh` adds the targeted
`.specfuse/.loop.lock` gitignore line to every destination repo it sets up (idempotent,
without ignoring the rest of `.specfuse/`). Both this repo's `.gitignore` and every
`init.sh`-initialized repo ignore the lock file. Tests cover kernel-level exclusion
and release-on-close without spawning a real `claude -p`. All six acceptance criteria
met in one attempt ($0.89, ~5 min). GATE-01 status: `passed`.

**Status: active.** Single-gate feature; closing sequence in progress.

<a id="feat-2026-0005"></a>
## FEAT-2026-0005 — Combined close for single-gate features

**Why.** The four closing ceremonies (retrospective → lessons → docs → plan-next)
cost four dispatches — including an Opus `plan-next` — even on a one-WU feature
where `plan-next` is terminal boilerplate with no next gate to forward-design.

**Gate 1 (passed).** A new `close` WU type collapses all four closing ceremonies
into one session, accepted by `lint_plan.py` and `loop.py` only for single-gate
features (multi-gate features keep the four-WU sequence, where forward-design
`plan-next` earns its cost). The linter enforces the single-gate constraint and
rejects `close` on any feature with two or more gates. `loop.py` maps `close` to
the `plannext` verification gate set (structural lint on the feature post-close),
and treats a passing `close` WU as completing the gate. `CORRELATION_ID_RE` gained
a `CLOSE` segment so `G1-CLOSE`-style correlation IDs pass validation. Three tests
cover: lint accepts single-gate close, rejects multi-gate close, and still passes
the four-WU sequence (regression). All acceptance criteria met in one attempt
($1.23, ~7 min). GATE-01 status: `passed`.

This feature itself closes with the four-WU sequence — the `close` type does not
exist when this feature's driver loads `loop.py`. FEAT-2026-0006 is the first
feature to use the new `close` WU.

**Status: done.** Single-gate feature. FEAT-2026-0006 is the first feature to use
the new `close` WU.

<a id="feat-2026-0006"></a>
## FEAT-2026-0006 — WU execution-time tracking

**Why.** The loop already captured cost per WU; wall-clock execution time was missing.
Adding duration alongside cost gives operators a complete picture of WU weight (both
money and time) in `events.jsonl` and the WU frontmatter.

**Gate 1 (passed).** `loop.py` measures each attempt's wall-clock time with
`time.monotonic()` (start at dispatch, stop after verification) and records
`duration_seconds` per-attempt in `events.jsonl`'s `attempts_usage` list. Cumulative
`duration_seconds` (rounded to 3 decimals) is written to the WU's frontmatter at
outcome time (PASS / BLOCKED / SPINNING), independent of the `cost_tracking` setting.
`WU.template.md` documents the field as driver-owned. Tests cover per-attempt capture,
cumulative summing across a failed-then-passed sequence, frontmatter write, and
`cost_tracking: false` independence. All acceptance criteria met in one attempt (~$1.00,
~5 min). GATE-01 status: `passed`.

This feature is also the first live use of FEAT-2026-0005's `close` WU type —
closing in a single dispatch rather than the four-WU sequence. The combined close
ceremony worked correctly.

**Status: done.** `roadmap_goal` met — the loop records each work unit's wall-clock
execution time alongside the cost it already captures. See
`RETROSPECTIVE.md §Feature-arc retrospective`.

<a id="feat-2026-0007"></a>
## FEAT-2026-0007 — Dispatch cost controls

**Why.** Per-WU dispatch cost was growing with no lever to control it. Three
mechanisms were missing: model-family aliasing (so WU specs don't pin model
versions), effort-tier control (so cheap work doesn't burn expensive thinking
budget), and a retry ladder that escalates compute rather than repeating the same
failed attempt.

**Gate 1 (closing).** Substantive delivery:

- **T01** — Model family aliases: `sonnet`/`opus`/`haiku` in WU frontmatter resolve
  at dispatch to the latest model in that family; full model IDs still accepted to
  pin a specific release.
- **T02** — `effort:` field (`low`/`medium`/`high`/`xhigh`/`max`) wired to
  `claude -p --effort`; default `medium` when field is absent. `WU.template.md`
  documents the field as author-controlled.
- **T03** — Tier-gated caveman preamble: `low`/`medium` effort WUs receive a
  terseness directive in the dispatched session; `high`+ do not.
- **T05** — Failure-note size cap: 200 lines / 8000 characters with head+tail
  truncation and a plain-ASCII truncation marker.

**T04 gap.** The retry escalation ladder (T04) was declared complete and driver
verification passed, but no production code was written. Required symbols
(`EFFORT_LADDER`, `effort_for_attempt`, `terseness_for_attempt`) are absent from
`loop.py`. The `code` gate passed because no new tests were registered and existing
tests make no assertion about absent functions. This failure mode is documented in
`RETROSPECTIVE.md`; two `[FEAT-2026-0007/G1-LESSONS]` entries in `LEARNINGS.md`
cover the completeness-guard and function-existence verification gaps. T04's
implementation was deferred to Gate 2 (T08H).

**Gate 2 (closing sequence in progress).** Substantive delivery:

- **T06** — Defaults-by-WU-type policy: `MODEL_BY_TYPE` and `EFFORT_BY_TYPE`
  tables in `loop.py` give every WU type a model and effort default; `model:` and
  `effort:` frontmatter fields become optional overrides rather than required
  fields. `lint_plan.py` updated to accept absent `model:`. `WU.template.md`
  frontmatter comments updated. Haiku guidance added to
  `.specfuse/skills/authoring-work-units/SKILL.md`. Landed in one attempt.
- **T07** — Per-gate cost budget: `cost_budget_usd` in `GATE-NN.md` sets a
  cumulative cost ceiling; `gate_budget_usd` / `gate_spent_usd` helpers in
  `loop.py`; halt-between-WUs semantics (current WU runs to terminal outcome,
  brake fires before the next dispatch — including closing-sequence WUs).
  `GATE.template.md` documents the field. Landed in one attempt.

**T08H / T08 gap.** T08H (re-land T04's retry-ladder code) and T08 (telemetry:
`resolved_model`, `cache_hit_rate`, `gate_summary`) both repeated T04's failure
mode: each session billed 0 input/output tokens, the driver committed only the WU
frontmatter status flip, and `status: done` advanced the dependency frontier
despite no symbols landing. After Gate 2: `EFFORT_LADDER`, `effort_for_attempt`,
`terseness_for_attempt`, `cache_hit_rate`, and `gate_summary` are absent from
`loop.py`. The retry escalation ladder and gate-level telemetry are undelivered.
Two `[FEAT-2026-0007/G2-LESSONS]` entries in `LEARNINGS.md` cover the 0-token
session gap and the limit of agent-side safeguards.

**Status: done.** Four `roadmap_goal` levers (model alias, effort tier, terseness,
per-gate budget) all landed and importable; type-default policy layered on top.
T04 retry ladder and T08 telemetry deferred — three reland attempts (T04, T08H, T08)
all silently no-op'd via the same 0-token-session failure path. The fix is
driver-side (refuse-commit on 0 tokens / empty diff / failed smoke-import), not
spec-side, so it belongs in a successor feature rather than a Gate 3. **Strongly
recommended next feature: FEAT-2026-0008 "Driver completeness-guard."** See
`RETROSPECTIVE.md §Feature-arc verdict` for the full terminal rationale and the
G4-LESSONS three-test analysis.

<a id="feat-2026-0008"></a>
## FEAT-2026-0008 — Driver completeness-guard

**Why.** FEAT-2026-0007 shipped four cost-control levers but T04 / T08H / T08
all reported `status: done` while landing no production code (hollow passes,
each via a 0-token session that the driver committed because the WU
frontmatter status flip was the only staged change). Agent-side safeguards
(smoke-import AC, completeness escalation triggers) are bypassed when the
agent session crashes or produces 0 tokens. The fix is driver-side.

**Gate 1 (passed).** Three independent driver-side guards landed in one
attempt each, all wired into the attempt loop in `run()`:

- **T01** — Zero-token attempt guard: `is_zero_token_attempt(usage)` at
  `loop.py:711`, called at `loop.py:885` before RESULT-block parse. A
  session billing `input_tokens: 0` is treated as a failed attempt; three
  in a row escalate to `blocked_human` with `reason: "all_attempts_zero_token"`.
  `usage is None` (cost tracking disabled) does NOT trigger the guard.
- **T02** — `files_changed` diff guard: `verify_files_changed(result,
  head_before)` at `loop.py:622`, called at `loop.py:901` between
  `parse_result_block` and `squash_commit`. Any agent-claimed `files_changed`
  path that does not differ from HEAD fails the attempt before squash.
  Empty / absent `files_changed` opts out (pre-existing-WU compatibility).
- **T03** — WU-Verification smoke-import runner: `extract_smoke_imports` /
  `run_smoke_imports` at `loop.py:669` / `:684`, called at `loop.py:1110`-`:1112`
  between successful verify+squash and the status-flip-to-done. Conservative
  import-form regex only (no free-form `python3 -c` execution). A failing
  smoke check rolls back the squash via `git reset --hard <head_before>`
  and counts as a verification failure.

All three landed in one attempt each (T01 $2.61 / T02 $1.75 / T03 $1.66,
~17 min total). GATE-01 status: `passed`.

**Status: done.** `roadmap_goal` met — all three guards present in `loop.py`
AND wired into the attempt loop in `run()`. Per the FEAT-2026-0007 verdict's
mandatory recommendation, any one of the three would have caught T04/T08H/T08;
all three together close the gap structurally. The deferred FEAT-2026-0007
work (T04 retry escalation ladder, T08 telemetry) can now be relanded under
FEAT-2026-0009 — a third silent-no-op is structurally impossible. See
`RETROSPECTIVE.md §Feature-arc verdict` for the audit and the recursive
close-ceremony check.

<a id="feat-2026-0010"></a>
## FEAT-2026-0010 — Roadmap restructure: add + archive

**Why.** The roadmap file currently mixes detail sections for every
feature — done, abandoned, planned, active — into one document. As
done features accumulate, `pick-feature` (and any other reader of the
roadmap) loads ~70% irrelevant context every invocation. The file has
also been edited entirely by hand; there is no skill to append a new
planned entry, and no mechanism to graduate detail sections out of the
hot file when work completes.

**Goal.** Land the structural changes that let the roadmap stay lean
without losing history:

- Split `.specfuse/roadmap.md` so detail sections cover only `planned`
  and `active` features; move `done` and `abandoned` detail sections
  to a new `.specfuse/roadmap-archive.md` (table rows stay in the
  main file with a link to the archive anchor).
- Migrate FEAT-2026-0003..0008's existing detail sections to the
  archive as the first dogfooding pass.
- Ship a `roadmap-add` skill: interactive append of a new planned
  row + detail section, auto-picking the next FEAT-YYYY-NNNN ID,
  honoring reserved IDs in repo history.
- Ship a `roadmap-archive` skill: given a FEAT-ID (or auto-detected
  done/abandoned rows with detail still inline), cut the detail
  section and append to the archive, leaving the table row intact.
- Hook the driver: when `loop.py` flips `PLAN.md` status to
  `complete`, suggest (or auto-fire) `roadmap-archive` for that
  feature. Manual-first cut; auto a follow-up if the manual flow is
  reliable.

**Benefits.** Reduce hot-path context for every roadmap reader.
Make adding a planned entry a one-command operation, removing the
friction that causes ad-hoc shorthand to leak into the table.
Preserve full history in a file that's never loaded on the hot
path. Foundation for FEAT-2026-0011, which adds new columns and
scoring data the table can't carry while it's still hand-edited.

**Verification.** `pick-feature` invoked against the restructured
roadmap loads strictly less context than today (measure: line count
of the file it reads). `roadmap-add` writes a row + detail section
that round-trips through the archive flow without losing data.
`roadmap-archive` is idempotent (running twice does not duplicate
the archive entry). Migration of 0003..0008 leaves the table
unchanged in shape; archive contains 6 detail sections matching
the originals byte-for-byte except for the new archive header.

**Status: active. Gate 1 (passed).** Gate 1 shipped: `roadmap-archive.md` created, `Detail` column added to the table, `roadmap-archive` skill shipped, `roadmap-add` skill shipped, FEAT-2026-0003..0008 detail sections migrated to the archive. Main roadmap shed 223 lines (647 → 424); archive grew to 275 lines. **Gate 2 (passed).** Driver auto-archive hook shipped: `loop.py` now calls `auto_archive_feature` after flipping `PLAN.md` status to `complete`, automatically archiving the feature's roadmap detail section on feature close. Tests cover happy path, idempotency, and refusal. 1 WU (T05), 2 attempts, $2.05.

<a id="feat-2026-0002"></a>
## FEAT-2026-0002 — Driver run-loop test coverage

**Why.** This repo's own `code` coverage gate ships at `--fail-under=35`,
deliberately below the methodology's ≥ 90% default
(`.specfuse/verification.yml`). The gap is concentrated in the orchestration
paths of `loop.py`: `run()` (the attempt loop and gate-completion flow),
`squash_commit`, `log_event`, `find_feature`, `load_graph`, `load_wu`,
`require_git_ready`, the `dispatch` subprocess invocation, and the
`blocked_human` escalation flow end-to-end. The parse/decide/verify core is
already covered by the existing 27 unit tests.

**Goal.** Land integration tests that exercise the run-loop without
spawning a real `claude -p`, then raise this repo's `--fail-under` floor
toward 90. Specifically:

- `run()` happy path (a single passing WU lands a squashed commit and
  flips status to `done`).
- `run()` failed-then-passed path (attempt 1 fails verify, attempt 2
  passes; assert the failure note is written, the attempt counter is
  written to frontmatter, and only one squashed commit ends up on HEAD).
- `run()` agent-reported-blocked path (assert single attempt, `blocked_human`
  status, `human_escalation` event with `agent_reported_blocked` reason,
  `git reset --hard` ran).
- `run()` spinning-detection path (three failed verify cycles → `blocked_human`,
  `human_escalation` with `spinning detected` reason).
- `squash_commit` against a temp git repo: produces one commit with the
  correct trailer, folds away any commits the (stub) agent made.
- `log_event` round-trip: appends a single line of valid JSON with the
  expected fields.
- `find_feature` with zero/one/multiple actives.
- `require_git_ready` happy + missing-commits + non-repo (already covered
  manually after the original fix; promote to unit tests).

**Gate 1 (passed).** Single-gate feature, five substantive WUs:

- **T01** — `tests/test_loop_orchestration.py` raised `loop.py` from 87%
  to ≥ 95% by covering `squash_commit` soft-reset, `find_feature` 0/1/many,
  `require_git_ready`, dispatch error arms, lock contention, gate-budget
  halt, and `main()` argparse. Landed in 2 attempts (high effort).
- **T02** — `tests/test_validate_event.py` raised `validate-event.py` from
  0% to 97% by covering schema accept/reject and a real-event regression.
  First attempt blocked (AC 4 polarity error: the spec asserted the schema
  *accepts* a driver-emitted event, but the orchestrator's schema
  intentionally rejects `source: "driver"`); re-arm inverted the AC and
  added `jsonschema` to dev deps. Landed in 1 attempt post-re-arm.
- **T03** — `tests/test_lint_plan_errors.py` raised `lint_plan.py` from
  79% to 99% by covering the 11 named error arms + a regression on the
  bundled FEAT-2026-0001 fixture. First dispatch spun 3 attempts on a
  ruff F401 (`import sys` unused); re-arm added pre-flight lint discipline.
  Landed in 1 attempt post-re-arm.
- **T04** — `tests/test_miniyaml_negative.py` extended raised `_miniyaml.py`
  from 87% to 100% with escape-handling and indent-error fixtures. Landed
  in 1 attempt.
- **T05** — `.specfuse/verification.yml` and `scripts/smoke-test.sh`
  flipped from `--fail-under=70` to `--fail-under=90`; deviation comment
  removed. Landed in 1 attempt (45 s).

Post-gate coverage: TOTAL = **97%** (was 78% at feature start), with each
targeted module at or above its per-WU threshold (`loop.py` 97%,
`validate-event.py` 97%, `lint_plan.py` 99%, `_miniyaml.py` 100%). The
two-site `--fail-under` floor (`.specfuse/verification.yml` +
`scripts/smoke-test.sh`) reads `=90` and matches the methodology default.
GATE-01 status: `passed`.

**Status: done.** `roadmap_goal` met — this repo's coverage floor now
matches the methodology default (≥ 90%), with measured TOTAL at 97% and
no module under 90%. See `RETROSPECTIVE.md §Feature-arc verdict`.

<a id="feat-2026-0013"></a>
## FEAT-2026-0013 — CI integration_workspace cleanup race fix

**Why.** The repo's CI suite intermittently fails with
`OSError: [Errno 39] Directory not empty: '/tmp/.../.git/objects'`
when `tests/test_driver_integration.py::integration_workspace`'s
`tempfile.TemporaryDirectory()` context manager exits and Python 3.12's
`shutil.rmtree` races against leftover file descriptors holding parts
of `.git/objects`. Three observed occurrences:

- 2026-06-10 push, `test_no_files_changed_in_result_block_runs_squash_as_today`
  — root cause was an unclosed `.specfuse/.loop.lock` fd; fixed by the
  `try/finally` close in `loop.py::run()` (commit `7abc809`).
- 2026-06-11 PR #7 first run,
  `test_cumulative_duration_written_to_frontmatter` — same OSError, but
  the prior fix doesn't touch the test that's failing now. A second
  unclosed handle (or git subprocess that hasn't exited yet) is still
  leaking inside `integration_workspace`.

A subsequent CI run on the same PR passed without code changes,
confirming the race is timing-dependent and not deterministic. CI
flakes erode the verification-as-oracle property even when each
individual failure has a reproducible root cause, and the team has
now spent two halt-and-investigate cycles on the same symptom shape.

**Goal.** Eliminate the race so the integration-test path is
deterministic on Python 3.12 CI runners.

Likely fix paths to evaluate:

- `tempfile.TemporaryDirectory(ignore_cleanup_errors=True)` in
  `integration_workspace` (Py 3.10+). Suppresses the symptom; doesn't
  fix the underlying leak.
- Audit `integration_workspace` for unclosed git subprocess handles
  and add explicit `subprocess.run` `check=True` + completion-wait at
  exit points. Fixes the root cause.
- Move `.specfuse/.loop.lock` open-then-flock pattern out of test
  paths that don't need it (the lock isn't load-bearing inside a
  TemporaryDirectory the test owns).

A single substantive WU per fix-path; recursive audit at close runs
the suite 50× in a loop and asserts zero flakes.

**Gate 1 (passed).** T01 audited `integration_workspace` and applied
two coupled fixes in one attempt (362.795 s, $0.327): (a) `git -c
gc.auto=0` on every `git` invocation inside the fixture body, killing
gc.autoDetach's post-parent-exit background-subprocess class; (b) a
`git -C <root> rev-parse HEAD` sync barrier in a `finally:` block
after the `yield root` line, forcing index-lock flush and pending
writer release before `TemporaryDirectory` teardown. `subprocess.run`
calls inside the fixture use `check=True` with completion-wait;
fixture remains a `@contextmanager` yielding `Path` (no API break).
50× local audit at T01 close: 50/50 clean. GATE-01 status: `passed`.

**Status: done.** `roadmap_goal` met — the close-session 50×
recursive audit, post-T01-squash on HEAD `2a9e2aa`, shows 50/50
unittest exits 0 with no `OSError: Directory not empty`, no
`FAILED`, no `ERROR`. `tail -1 | sort | uniq -c` returned one
distinct line across 50 runs (driver stdout from an inner
integration test, not unittest's verdict — see RETROSPECTIVE.md
"Reading the output"); exit-code count confirmed PASS:50 FAIL:0.
The race is eliminated locally; CI on a Py 3.12 runner is the
field test (next PR run). Two `[FEAT-2026-0013/G1-CLOSE]` entries
landed in LEARNINGS.md covering the gc.auto=0 + sync-barrier rule
and the `tail -1` oracle fragility. See `RETROSPECTIVE.md
§Feature-arc verdict`.

<a id="feat-2026-0014"></a>
## FEAT-2026-0014 — GitHub Actions Node.js 20 deprecation bump

**Why.** GitHub will force Node.js 20 actions to Node.js 24 on
2026-06-16; Node 20 removed from runners 2026-09-16. CI's
`actions/checkout@v4` and `actions/setup-python@v5` both emit the
deprecation warning today. Without action, the forced upgrade lands
during a normal CI run with no warning of which workflows will break
their action pinning behavior — exactly the failure mode this repo's
methodology is meant to surface before merge, not after.

**Goal.** Bump `.github/workflows/ci.yml` to action versions that
support Node 24 natively (currently: `actions/checkout@v5`,
`actions/setup-python@v6` — verify the major-version compatibility at
WU author time, not assume).

Single substantive WU: edit `ci.yml` action `uses:` lines; trigger a
CI run on the PR and confirm no deprecation warning fires; assert
both jobs still pass against the existing test suite.

**Status: done.** `roadmap_goal` met — `.github/workflows/ci.yml`
pins `actions/checkout@v6` and `actions/setup-python@v6`; no stale
`@v[0-5]` pins remain. Five days of deadline margin (closed
2026-06-11; forced upgrade 2026-06-16). T01 landed in 1 attempt
after a WU re-arm; the original ACs coupled the WU to the
operator's `gh` CLI auth state and burned 5 dispatches before the
re-arm dropped the host-coupled checks. See
`RETROSPECTIVE.md §Feature-arc verdict`.

<a id="feat-2026-0012"></a>
## FEAT-2026-0012 — Closing-WU deliverable guard

**Status: abandoned 2026-06-13 — folded into FEAT-2026-0015.** Scope
preserved here for audit; implementation moved into 0015 to avoid
building guards against a 4-WU taxonomy that 0015 then collapses.
See FEAT-2026-0015 detail section's `## Subsumed scope` for the
hollow-pass guard work this feature originally proposed.

---

**Why.** FEAT-2026-0008 closed the hollow-pass surface for
`type: implementation` WUs via three driver-side guards (zero-token,
`files_changed` diff, smoke-import). Closing-sequence WUs
(`plan-next`, `close`, `retrospective`, `lessons`, `docs`) have the
same hollow-pass surface and none of the three FEAT-2026-0008 guards
catch them:

- Zero-token misses: the agent billed real tokens.
- `files_changed` diff guard misses: per FEAT-2026-0008/T02, empty or
  absent `files_changed` opts out, and closing WUs typically emit
  empty lists.
- Smoke-import misses: closing WUs produce prose deliverables, not
  importable symbols.

Observed live in an external (IaC) project's feature dogfood: a
terminal-gate `plan-next` WU billed `cost_usd: 0.90`,
`output_tokens: 4389`, emitted RESULT `status: complete`, and the
driver flipped `attempts: 1` / `status: done` while the agent had
never invoked `Write` / `Edit`: `GATE-NN-REVIEW.md` absent,
`PLAN.md status: active` unchanged, roadmap row unchanged. The
driver believed an honest RESULT block without confirmation.

Also encountered locally during FEAT-2026-0002/G1-CLOSE: the close
agent correctly flipped PLAN.md status, roadmap row, and wrote
RETROSPECTIVE.md — but only because the WU spec told it to. If the
agent had emitted PASS without writing, the driver would have
believed it and FEAT-2026-0002 would have closed hollow. The same
gap blocks reliable auto-progression of the roadmap row on feature
close (current behavior depends entirely on the close-agent
following the WU AC).

**Goal.** A driver-side guard, analogous in shape to FEAT-2026-0008's
three guards, that asserts type-keyed closing-deliverable existence
between successful verify+squash and the status-flip-to-done.
Type-keyed assertion table:

- `retrospective` → `<feature_dir>/RETROSPECTIVE.md` exists +
  size > N bytes (small floor, ~200).
- `lessons` → `git diff head_before -- .specfuse/LEARNINGS.md`
  shows ≥1 added line.
- `docs` → at least one file in `<feature_dir>` or
  `.specfuse/roadmap.md` shows a diff against `head_before`.
- `plan-next` → `<feature_dir>/GATE-<N>-REVIEW.md` exists +
  non-empty AND one of: (a) next gate's `work_units` non-empty
  in PLAN.md, (b) PLAN.md `status: done`, (c) roadmap row `done`.
- `close` → RETROSPECTIVE.md exists + non-empty AND LEARNINGS.md
  diff AND PLAN.md `status: done` AND roadmap row `done`.
- `implementation` → unchanged; FEAT-2026-0008's three guards
  already cover.

Failure rolls back via `git reset --hard head_before`, records an
`attempt_outcome` event with `outcome: "closing_deliverable_missing"`
naming the failed assertion, and counts as a verification failure
in the attempt loop — three in a row escalate to `blocked_human`.

**Verification.** New tests under `tests/test_loop_closing_guard.py`
covering negative case (agent emits PASS without writing the
type-keyed deliverable, guard fires, attempt fails) and positive
case (agent writes everything, guard passes). Recursive audit per
LEARNINGS [FEAT-2026-0008/G1-CLOSE]: the close ceremony for this
feature must run the new guard against itself — if any deliverable
is missing, the close WU emits `status: blocked`, not `complete`.

**Status: planned.** Independent of FEAT-2026-0010/0011. Detail the
first gate's WUs when ready to start. Single gate, one substantive
WU (`closing-deliverable-guard`) + `close` ceremony — mirrors
FEAT-2026-0008's shape.

<a id="feat-2026-0015"></a>
## FEAT-2026-0015 — Closing-ceremony restructure + hollow-pass guard

**Subsumes FEAT-2026-0012** (filed 2026-06-12, abandoned 2026-06-13
when this feature was scoped). 0012 proposed a driver-side closing-WU
deliverable guard against the 4-WU taxonomy. That investment would be
partially obsoleted by this feature's collapse of the taxonomy from
4 WU types to 2-3. Building the guard against the NEW taxonomy from
day 1 is cheaper end-to-end. The hollow-pass guard work is folded
into this feature's `## Subsumed scope` section below.

**Why.** The current 4-WU closing sequence (`retrospective → lessons →
docs → plan-next`) consistently consumes ~50% of feature cost despite
the inner three WUs (RETRO, LESSONS, DOCS) being summary+append work
on overlapping context. Live evidence from FEAT-2026-0010:

- Gate 1 close: $3.17 of $6.15 (52%); cache-creation across 4 WUs
  ≈ 209k tokens (each fresh session re-bootstraps the same context).
- Gate 2 close: $2.23 of $4.28 (52%); same shape.
- LESSONS WUs frequently produce 0-1 entries; DOCS WUs often produce
  empty diffs or `files_changed_mismatch` on the same file the close
  ceremony already touched.

The single-gate `close` alternative (FEAT-2026-0005) proved a combined
session works for terminal-of-single-gate: $0.83 on FEAT-2026-0014;
$1.84 on FEAT-2026-0013 v3-a3. Multi-gate features have no equivalent
shortcut today; their terminal gate also pays the full 4-WU tax even
though no `plan-next` is needed (terminal = nothing to plan).

**Goal.** Restructure the closing contract to two patterns:

- **Terminal gate (any feature, single- or multi-gate)**: single
  combined `close` WU. Folds retrospective + lessons + docs +
  feature-arc verdict into one session. Extends FEAT-2026-0005's
  pattern from single-gate-only to any-feature-terminal-gate.
- **Intermediate gate (multi-gate only)**: 2-WU close.
  `close-intermediate` (new type) folds RETRO + LESSONS + DOCS into
  one session; `plan-next` remains separate as today (high-stakes,
  opus, drafts next gate's WUs against fresh context).

Per-feature estimated savings: $1.50-3.00 + ~100k cache-creation
tokens per closed gate. Wall-time: 4 sessions → 2 per intermediate
gate, 4 → 1 per terminal gate.

**Scope.**

- New `close-intermediate` WU type in `loop.py` (`MODEL_BY_TYPE` +
  `EFFORT_BY_TYPE` + `GATES_FOR_TYPE` + verification routing).
- Update `.specfuse/templates/WU.template.md` and PLAN.md template to
  use 2-WU intermediate and 1-WU terminal patterns by default.
- Update `lint_plan.py` to accept the new shapes; reject the old
  4-WU sequence as deprecated (with a grandfather window for
  in-flight features so this PR doesn't break existing branches).
- Update `.specfuse/skills/authoring-work-units/SKILL.md` to document
  the new contract.
- Update `/draft-feature` skill to emit the new patterns.
- The `close-intermediate` WU type's prompt must demand explicit
  subsections: `## RETROSPECTIVE`, `## LEARNINGS to promote`,
  `## Docs reconciled` — the audit trail per-step the old per-WU
  sequence provided implicitly.

**Scope OUT.**

- Backfilling already-closed features (their 4-WU history stays as
  precedent).
- Changing `plan-next`'s shape — keep its dedicated session.
- Single-gate's existing `close` alternative — already correct
  shape; just rename `close-terminal` for clarity or leave as-is.

**Verification.** A dogfood feature (FEAT-2026-0016 or this feature
itself) closed under the new contract shows: (a) terminal-gate cost
≤ $1 (matches G1-CLOSE precedent); (b) intermediate-gate close cost
≤ $1 (close-intermediate, no plan-next); (c) lint accepts the new
shapes and rejects the old (modulo grandfather). `tests/test_lint_*`
updated.


<a id="feat-2026-0017"></a>

## FEAT-2026-0017 — Close-WU wiring-race guard

**Why.** FEAT-2026-0015/T06 shipped `fire_terminal_flips` driver-side
+ wired it into the close path. Wiring looked correct on inspection
and on test (T06's own tests). The recursive dogfood (G2-CLOSE) ran
clean, wrote `verdict: met` to its WU frontmatter, and the driver
flipped PLAN.md to `done`. But the terminal gate stayed
`awaiting_review` and the roadmap row stayed `active`. Auto-archive
never fired.

Root cause: `wu.verdict` was populated by `load_wu` BEFORE dispatch
(value: `None`). Agent wrote `verdict: met` to the frontmatter DURING
dispatch. The driver's check at the close-path squash compared the
IN-MEMORY `wu.verdict` (still `None`) against the threshold. Check
returned False. `close_wu_for_terminal` stayed `None`.
`fire_terminal_flips` never invoked.

Race between WorkUnit-in-memory and agent's frontmatter write.

None of today's hollow-pass guards (FEAT-2026-0008's three +
FEAT-2026-0015/T07's four) caught this:

- Zero-token guard: T06 ran productively.
- `files_changed` guard: T06 listed `loop.py` + the test file; both
  changed.
- Smoke-import guard: `fire_terminal_flips` symbol existed +
  imported.
- Closing-deliverable guards (T07): T07 didn't model wiring-race —
  it asserts on file existence and content shape post-pass, not on
  driver-state invariants that should fire as a CONSEQUENCE of the
  WU's effect.

**Delivered.** Driver-side post-pass invariant check, type-keyed.
For close-type WUs with `verdict: met`, asserts terminal gate
`passed`, roadmap row `done`, archive anchor present. On failure:
reset, attempt_outcome event, retry within budget. T02 added the
`produces_driver_helper` WU frontmatter field + lint warning for
implementation-WUs whose body claims driver-wiring without
declaring the symbol(s) produced. Recursive dogfood: G1-CLOSE was
intended to exercise the new guard against itself.

**Bonus deliverables surfaced by dogfood.** Three pre-existing
hollow-pass / methodology surfaces were also closed in this
feature's branch:

- `tests/test_loop_files_changed_guard.py` +
  `tests/test_loop_orchestration.py` `_init_git` helpers now run
  `git config commit.gpgSign false` after `git init`, matching the
  pattern at `tests/_workspace.py:36`. 20 pre-existing test errors
  (operator-global SSH signing + tempdir-git incompatibility)
  fixed.
- `assert_doc_or_roadmap_diff` (loop.py) now also accepts
  `.specfuse/LEARNINGS.md` and `RETROSPECTIVE.md` — resolves the
  T06 (driver owns roadmap flip) ↔ T07 (close-deliverable guard
  requires roadmap.md or docs/) contract contradiction surfaced
  by the post-T06 close-contract.
- `assert_closing_deliverables` diff-only-touches-wu bypass
  removed. Previously silently passed hollow close-ceremony
  attempts where only the driver's bookkeeping write touched the
  WU file. New regression test
  `test_close_fails_when_diff_only_touches_wu_file`.

**Verdict.** `met` — original wiring-race surface closed by T01;
three bonus hollow-pass surfaces also closed; Opus 4.7
verdict-flip blind-spot logged for deep-analysis. Full RETROSPECTIVE
+ cost analysis in
`.specfuse/features/FEAT-2026-0017-wiring-race-guard/RETROSPECTIVE.md`.
Actual cost $39.37 vs planned $3.20 — 12.3× overrun, all on
dogfood-surfaced bug discovery cycles where the agent worked
correctly but verify-gates failed for reasons outside WU scope.

<a id="feat-2026-0016"></a>
## FEAT-2026-0016 — Per-attempt outcome events + re-arm contract + audit trail

**Why.** FEAT-2026-0013 burned $13.50 across 5 dispatches (v1, v2,
v3-attempt-1, v3-attempt-2, v3-attempt-3) before the fix held. Each
re-arm required the operator to manually compute cumulative
`historical_cost_usd`, `historical_duration_seconds`, etc., and write
them into WU frontmatter to preserve audit. The driver does NONE of
this; the `/unblock-wu` skill spec mentions the pattern but does not
automate it. /gate-status reports "this WU is blocked" but does NOT
surface "this WU has been re-armed 2 times". The audit signal for
re-arm history is invisible to every other skill.

Failure modes the gap surfaces:

- Operator under-estimates feature cost because each /unblock-wu
  resets `cost_usd: 0` and visible `attempts: 0`. FEAT-2026-0013's
  $13.50 was only visible by manually summing five events.jsonl
  blocks plus three commit messages.
- Re-arm rationale is captured in commit messages (FEAT-2026-0013
  history) but not in frontmatter — so /gate-status can't surface
  "this is re-arm 3; prior reasons: gh-auth, gpg-config, scope-miss".
- Methodology drift: the `historical_*` field naming was invented
  ad-hoc during 0013; no template, no lint, no driver awareness.

**Goal.** Standardize the re-arm contract end-to-end.

WU frontmatter additions:

- `re_arm_count: <int>` — number of times this WU has been re-armed
  from `blocked_human` (or `done` post-CI-fail) back to `pending`.
  Initialized 0; incremented by driver on next dispatch after an
  `/unblock-wu` write.
- `re_arm_history: [{timestamp, prior_status, prior_attempts,
  prior_cost_usd, prior_duration_seconds, reason}]` — append-only
  list. Operator (or /unblock-wu skill) writes one entry per
  re-arm.
- `cumulative_cost_usd`, `cumulative_duration_seconds`,
  `cumulative_input_tokens`, `cumulative_output_tokens` —
  cross-attempt sums INCLUDING all re-arms. Driver maintains;
  /unblock-wu does not touch.

Driver changes:

- On `/unblock-wu` re-arm write (detected: WU was `blocked_human`,
  now `pending` with `re_arm_count` incremented), driver fold prior
  attempt's `cost_usd` / `duration_seconds` into the cumulative
  fields BEFORE resetting `cost_usd: 0`.
- New event `re_arm_dispatched` written to `events.jsonl` carrying
  re-arm number + rationale.
- `task_started` event carries `re_arm_count` so dashboards can
  group attempts across re-arms.

Skill changes:

- `/unblock-wu` prompts for one-line re-arm rationale (already
  recommended in the skill spec; now MANDATORY). Writes the new
  `re_arm_history` entry.
- `/gate-status` surfaces "re-arm N (last reason: ...)" prominently
  on any WU with `re_arm_count > 0`.
- `/wrap-feature` executive recap (§3 plan-adherence) reads
  `re_arm_count` per WU instead of grep'ing events.jsonl.

**Scope OUT.**

- Changing the `/unblock-wu` decision vocabulary (re-arm /
  abandon / skip stays as-is).
- Driver auto-deciding when to abandon a WU after N re-arms
  (would be a separate retry-ceiling feature).
- Cross-feature cost rollup — that belongs to FEAT-2026-0011
  (scoring framework consumes per-feature cumulative cost).

**Verification.** Recursive: dogfood this feature's own close
ceremony exercises the new frontmatter fields. Tests cover the
driver's cumulative-fold logic, /unblock-wu's mandatory-rationale
prompt, and /gate-status's re-arm surfacing.

**Status: planned.** Independent of FEAT-2026-0015. Can land
in parallel. Probably small (one substantive WU for the driver
fold-logic, one for /unblock-wu + /gate-status updates, one for
WU template/lint changes).
