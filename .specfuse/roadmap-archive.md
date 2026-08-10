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
<a id="feat-2026-0044"></a>
## FEAT-2026-0044 — agent-policy.yml schema + groom-backlog skill (priority queue, rules, dials)

**Why.** The specfuse-agent (FEAT-2026-0049) must know the operator's priorities ahead of time: priority is policy, not intelligence — the agent selects work *within* a declared policy and escalates ties, never guesses intent. That policy needs one auditable, versioned surface, plus a periodic ritual that keeps it fed as the backlog evolves.

**Goal.** Ship (a) the `.specfuse/agent-policy.yml` schema + example: ordered `queue:` of FEAT-IDs (validated against the roadmap every agent run; drift escalates, never guessed around), class rules (`bugs: {preempt, min_severity, automerge}`, `features: {gate_review: human|auto per-feature override, wip_limit}`), budgets (`max_tokens_per_run`, `max_open_prs`, daily caps), and escalation config (webhook, `assignee`, quiet hours, SLA); (b) the `/groom-backlog` skill: reads roadmap planned set, open triaged issues, blocked chains, LEARNINGS, and the current queue; surfaces queue-hygiene findings (done entries to remove, blocked-upstream reorders, triaged feature-class issues not yet on the roadmap) and per-candidate trade-offs in the pick-feature style; proposes a new ordered queue and writes agent-policy.yml only on explicit accept. Empty queue = agent works bugs only and asks for priorities.

**Benefits.** The operator's role shifts from per-decision operator to policy-setter: one file review changes agent behavior; a ten-minute periodic grooming session keeps the agent autonomous between check-ins. Every autonomy dial decided across the monitoring and agent initiatives gets its declared home.

**Inherited handoff — one dial is already waiting for this file
(`[FEAT-2026-0045/G1-CLOSE]`).** [FEAT-2026-0045](roadmap-archive.md#feat-2026-0045) shipped triage's `auto`
dial as an explicit keyword argument, `apply_triage(runner, repo, decisions, *,
auto=False)`, reading no configuration of any kind — deliberately, because
`agent-policy.yml` is this feature's core deliverable and did not exist, and building a
minimal reader there would have taken this feature's scope and left it shipping against a
partial schema someone else authored. **This feature must wire its policy file to that
parameter.** The parameter exists, is tested at both settings, and its semantics are
fixed: under `auto=True` a decision whose confidence is not `high` is recorded as the
`question` category and routed to `needs-human`, **still marked**, never skipped. Supply
the value; do not redesign the semantics, and do not re-litigate where the dial lives. The
`autofix` dial was already assessed as a precedent and rejected — it is per-*component* in
`monitoring.yml`, and inbound issues are not components. See that feature's
[RETROSPECTIVE](features/FEAT-2026-0045-issue-triage/RETROSPECTIVE.md).

**What shipped (gate 1, four work units).** `.specfuse/agent-policy.yml` and its
example, with a structural validator
`specfuse.loop.agent_policy.validate_agent_policy(path=None) -> list[str]` and a
new `agent-policy-example-lint` CI gate that runs it against both the example
and this repo's live policy file. A reader API — `load_policy(path=None) -> dict`,
which raises rather than returning defaults when the file is absent, and
`resolve_triage_auto(path=None) -> bool`. A new public
`lint_roadmap.roadmap_statuses(repo_root=None) -> dict` behind the queue check.
The `/triage-issues` skill now obtains `apply_triage`'s `auto` argument from
`rules.triage.auto` instead of prompting the operator each run; the default is
unchanged (`False` when the file or the key is absent). And `/groom-backlog`,
a propose-and-confirm skill that writes only `.specfuse/agent-policy.yml`, only
on explicit accept, with no `--auto` mode.

**Queue-drift severity, as delivered.** The three-way split matters to anyone
adopting the gate, and it is not the two-way rule the Goal paragraph above
originally sketched. A queue entry naming a FEAT-ID with **no row in
`roadmap.md`** is an `ERROR: ` and fails the gate — unresolvable without a
human. An entry whose feature has gone **`done` or `abandoned`** is a `WARN: `
that prints and does **not** fail — normal backlog evolution, which
`/groom-backlog` proposes cleaning up. `planned`, `active`, `blocked` and
`deferred` are all silent; `deferred` is included deliberately, as a legitimate
parked slot in the status legend. A uniformly fatal check would turn the gate
red on a correct tree the first time any queued feature completed.

**Status: done.**

<a id="feat-2026-0045"></a>
## FEAT-2026-0045 — issue-triage skill: categorize and route incoming GH issues (manual → auto dial)

**Why.** Issues arrive from the monitoring harvester, the orchestrator, and third parties. Before anything can be fixed or planned, each needs categorizing (bug / feature request / question / duplicate / won't-fix) and routing (fix-bug, roadmap-add candidate, needs-human, close). Today that triage is implicit human work; the agent needs it as an explicit, dial-controlled step — and it is useful standalone long before the agent exists.

**Goal.** A `/triage-issues` skill: scans untriaged issues (no triage label), proposes per-issue category + route with a one-paragraph rationale — bug → labeled and queued for fix-bug (severity assessed against the fix-bug small-scope contract; large/risky proposes feature promotion instead), feature → proposed roadmap-add draft, duplicate → linked and proposed close, question/unclear → needs-human. Interactive propose-and-confirm first; headless mode behind an `auto` dial applies only high-confidence categorizations and leaves the rest labeled for human triage. Fingerprint-aware: recognizes harvester-created issues (already structured) and skips re-categorizing them.

**Benefits.** Every inbound issue lands in exactly one lane with an audit trail; the agent's bug pipeline (FEAT-2026-0048) gets a clean, machine-readable intake; the human only sees the issues that genuinely need judgment.

**Shape (drafted 2026-08-09).** Single gate, 3 substantive WUs + terminal close, $18.00
planned. The seam is **module = mechanism, agent = judgment**: `specfuse/loop/triage.py`
owns the closed category vocabulary, the category→route map, the marker pair, and the
untriaged scan; `/triage-issues` owns classifying free text. Three decisions were settled
at draft time — a triaged issue carries **both** an authoritative body marker
(`<!-- specfuse:triage category=… confidence=… -->`) and a best-effort category label
projected from it, marker-first and marker-wins; the `auto` dial is an **explicit
argument** at the headless entry point rather than a config surface, because
[FEAT-2026-0044](#feat-2026-0044) owns `agent-policy.yml` and does not exist yet; and
`duplicate` ships judgment-only with no detection mechanism.

**Scope boundary — OUT.** Acting on a route (invoking `/fix-bug`, writing roadmap rows,
closing duplicates — that is [FEAT-2026-0048](roadmap.md#feat-2026-0048) for bugs and the operator
otherwise); `.specfuse/agent-policy.yml` in any form; refactoring the five existing
`gh issue list` call sites into a shared client; re-triaging an issue that already carries
a marker.

**Expected verdict `met_locally`.** Two surfaces are unreachable from inside a dispatched
session: triage against live GitHub (the `gh`-in-sandbox constraint), and "an agent
following the skill's prose reproduces the module's routing on an unseen issue" — the
skill test binds prose to constants and proves drift-freedom, not correctness.

**Delivered** (gate 1, terminal — see
[RETROSPECTIVE](features/FEAT-2026-0045-issue-triage/RETROSPECTIVE.md)).
`specfuse/loop/triage.py`: the closed `CATEGORIES` / `CONFIDENCES` tuples, the total
category→route map behind `route_for`, the category→label projection behind `label_for`,
the `render_marker` / `parse_marker` pair over
`<!-- specfuse:triage category=… confidence=… -->`, `list_untriaged` filtering
client-side on the marker's absence over an injected runner (a harvester issue is returned
flagged `already_structured`, not excluded), and `apply_triage(..., auto=False)` writing
marker-first, projecting the label best-effort, idempotent on an already-marked body, and
recording a failed label write rather than raising. Four new `LabelSpec` entries importing
their names from `triage.py`; one new public predicate `has_finding_marker` in
`specfuse/monitor/issues.py` so the marker literal has one home. `/triage-issues` ships
canonical at `plugins/specfuse/skills/triage-issues/SKILL.md`, vendored byte-identically
and discovery-symlinked, with a drift test binding its documented vocabulary and routes to
the module's constants — which proves prose has not drifted from code, and deliberately
does not claim the skill classifies correctly.

**Verdict `met_locally`, as predicted — three open follow-ups.** Triage against a live
GitHub repository is `externally-verifiable-later` (an operator run post-merge upgrades
it); "an agent following the prose reproduces the routing" is `inherent` (no in-repo
oracle can ever assert it, so `met` is unreachable through it); the consumer-visible
contract list awaits human acknowledgment. `duplicate` shipped judgment-only, with no
detection mechanism, by decision. Terminal flips are withheld on a hedged verdict —
`PLAN.md`, the gate, and this row stay un-flipped until an operator accepts through
`/accept-hedged-close`. The driver owns that flip; it is not hand-edited.

**Status: done.** Accepted 2026-08-10 via `/accept-hedged-close`; the driver fired the
terminal flips through `--recheck-verdict`. D1 was discharged by a live triage run against
this repository's own issues before the acceptance; D2 (`inherent`) and D3 are carried
forward in `RETROSPECTIVE.md`.

<a id="feat-2026-0075"></a>
## FEAT-2026-0075 — Driver-editing work units cannot take effect in the process that dispatches them

**Why.** Python caches modules in `sys.modules` at first import, so a work unit that edits the driver cannot change behaviour for any work unit the same driver process dispatches afterwards — including the close that judges it. This is not hypothetical and it is not cheap. FEAT-2026-0057 paid for it twice in one gate. Its T04 wired a pre-dispatch call site into `loop.py` at 13:58 UTC; the driver process had imported `loop.py` at 13:30, so the close dispatched one second later ran the pre-T04 function, received nothing, and could not make the observation that would have cleared its follow-up — a $5.33 close that closed `met_locally` for want of a restart. The second occurrence is one layer down: `execute_unit_attempt` imports `prerun_capture` at call time but calls it for **every** work unit, so the first dispatch of any process caches it. That round was deliberately split into two driver invocations to dodge the hazard, and the sequencing cost was paid for nothing because the fix it protected turned out to be defective for an unrelated reason. The methodology has no name for this and no guard against it; both times it was diagnosed after the money was spent. It is the self-hosting form of the harness-migration hazard `.specfuse/LEARNINGS.md` already warns about, and it will keep taxing every driver-editing feature until something detects or prevents it. Tracked as issue #757.

**Goal.** Make the hazard visible or impossible rather than rediscovered. The design is genuinely open and should be settled in gate 1 rather than assumed here; at least three shapes are viable and they are not mutually exclusive. **Detect and warn** — at gate completion, if any work unit in the gate declared `produces:` naming a file under `specfuse/loop/`, print that later units in the same run executed against the pre-edit modules and that a fresh process is required before any close can verify the change; cheapest, and it converts a silent tax into a visible one. **Isolate the dispatch** — run each work-unit attempt in a subprocess so every attempt re-imports; strongest guarantee, largest blast radius, and it interacts with the driver's tree-reset and event-buffer bookkeeping in ways that need real design. **Refuse at arm time** — detect a driver-editing unit scheduled ahead of a close in the same gate and refuse to arm, forcing the two-invocation split the operator currently has to know to perform by hand. Whichever is chosen, the feature should also give the two-invocation pattern a sanctioned name: holding a close at `status: draft` does **not** work (the arm check rejects an entire gate containing any draft unit), and `blocked_human` is the only usable hold today, which reads as a failure in `/attention` and every other consumer.

**Benefits.** The most expensive class of work unit stops paying a tax nobody budgeted for: two close cycles were lost to this in a single feature, and closes are already the costliest attempt type in the portfolio. A hazard that currently depends on an operator remembering it becomes a property of the system. And the sanctioned hold removes the last hand-improvised step in a driver-editing feature, so a run that must span two invocations says so in its plan instead of being discovered mid-gate.

**Status: done.** Terminal close ran with verdict `met_locally`; the operator accepted the hedge via `/accept-hedged-close` on 2026-08-08, carrying four follow-ups forward — the contract-change acknowledgment (discharged by the acceptance), gate 1's central claim (`externally-verifiable-later`), and two `routed-finding` entries left untracked at acceptance. **The benefit is built and tested but has never been observed:** `driver_staleness_detected` has fired zero times repo-wide, because gate 1's diagnostic never executed and gate 2's halt is not live in the process that shipped it. The re-run condition is the next driver-editing gate under a `T06`-carrying driver, which writes a durable event rather than a printed line. Cost **$45.55** against $32.00 planned; gate 2's budget was re-baselined $17.50 -> $31.00 by operator decision. Gate 1 shipped a diagnostic that never fired — occurrence four of the feature's own subject — and its first terminal close was itself occurrence five.

<a id="feat-2026-0056"></a>
## FEAT-2026-0056 — Per-criterion DoD state + incremental re-close

**Why.** A close returning `not_met` triggers fix WUs and a re-dispatched close that re-verifies the entire DoD from scratch. FEAT-2026-0066 ran G2-CLOSE 3 times and G3-CLOSE across 5 attempts — $48.50 of close spend, each pass re-running the full 2200-test suite, full regen, and the real-SQL-Server scenario matrix, including criteria already proven green on prior attempts. Close attempts are the costliest attempt type portfolio-wide ($4.2 avg vs $3.5 implementation) and 4 of the 10 most expensive WUs are closes.

**Goal.** GATE files carry the DoD as a per-criterion checklist; each close attempt records per-criterion pass/fail state. A re-dispatched close re-verifies only failed and newly-added criteria plus a regression check scoped to the diff landed since the last close attempt. Terminal closes keep a full-walk option (flag or default) for the final pass, so end-to-end freshness is still available where it matters.

**Benefits.** This repository's `tests` gate (`python3 -m unittest discover -s tests -v -b`) is a `broad` oracle with no diff awareness, so it re-runs in full on every close attempt — the design does not reduce that cost. What it saves is the per-criterion agent reasoning, the regeneration, and the scenario matrix that a re-dispatched close otherwise redoes from scratch on criteria already proven green. A cheaper `not_met` keeps closes honest: the incentive pressure toward optimistic `met` verdicts drops when finding a defect no longer re-prices that portion of the ceremony.

**Status: done.** Terminal close ran with verdict `met_locally`; the operator accepted the hedge via `/accept-hedged-close` on 2026-08-07, carrying three follow-ups forward — the contract-change acknowledgment (discharged by the acceptance itself), the `events.jsonl` assertion (discharged post-close at `04fbc80`, `T05#6` flipped to `pass`), and the red-before-green observation (`inherent`, never upgradeable). **The cost saving is built and wired end-to-end but remains unmeasured:** the terminal close was a first attempt, whose carry-forward set is empty by construction, so it skipped 0 of 44 criteria. The operator's accepted reason records that the next feature exercises the worklist on repeat closes, which is where the claim actually gets tested.

<a id="feat-2026-0057"></a>
## FEAT-2026-0057 — Executable oracle contract for gates: scripted verification + environment prep

**Why.** FEAT-2026-0066's closes hand-drove the same verification stack at least four times — consumer clone sync, regen, `dotnet build`, six real-SQL-Server scenarios, full generator suite — from prose instructions, at $8–12 per pass. A consumer clone that had drifted stale cost one entire close cycle: the environment-prep step (`git reset --hard origin/main` before a Hard Rule #2 proof) lived in agent memory and LEARNINGS prose, not in anything enforced. Deterministic work re-derived by a frontier model every attempt is the single biggest recurring close cost in generator-class repos.

**Goal.** A work unit's environment prep and verification oracles run deterministically *before* its session starts, with the captured output as the agent's input — so a close interprets machine-produced evidence instead of re-deriving the same commands from prose every attempt. Two opt-in frontmatter keys, `prep:` (fail-fast, distinct halt class) and `oracles:` (capture-all, injected under a byte budget that preserves verdicts), both resolving against `verification.yml` set names. Target-project harness scripts (e.g. the generator's SQL Server scenario matrix) stay in the target repo; the loop ships the contract, dispatch, and capture.

**Scope narrowed at draft time (2026-08-05).** The existing-mechanism search found most of the originally-framed goal already shipped: `verification.yml` sets are already named and ordered and readable by any name (`gate_commands.py`); `extra_gates` (`loop.py:212`, issue #62) already selects arbitrary sets per work unit; `_run_gate_set` (`loop.py:2753`) already executes and captures with timeout, process-group kill, and Windows routing; FEAT-2026-0068 already made capture verdict-aware. All of it runs at **exit** — `verify()` calls itself "the exit oracle" — so an agent needing results before writing a verdict still hand-drives, and a fail-fast prep step has nowhere to live. This feature therefore builds only the pre-dispatch timing hook and reuses the rest unchanged. **Dropped:** oracle declarations in GATE frontmatter (per-work-unit selection already exists — a second declaration surface would duplicate a working one). **Still out:** per-criterion binding, which remains FEAT-2026-0056's.

**Benefits.** Close attempts become script-run plus interpretation — cheaper, reproducible, and viable on a smaller model tier; environment-freshness lessons become enforced steps instead of prose that each new close may or may not recall; verification evidence gains a consistent, machine-captured form across features.

**Shipped hedged.** Closed at `verdict: met_locally`, accepted by the operator on 2026-08-05 with four follow-ups carried forward open — see the feature's `RETROSPECTIVE.md` § *Hedged verdict accepted*. Tracked as specfuse/loop#758 (prep halt path unobserved), #756 (captured-oracle banner), #723 (ruff verdict unrecognised), #757 (driver-editing units need a fresh process).

**Status: done.**

<a id="feat-2026-0067"></a>
## FEAT-2026-0067 — Re-arm fold divergence: one cost-fold path, or a frontmatter contract that admits two

**Why.** A re-armed work unit's prior-cycle spend lands in one of two different places depending on a condition nobody chose deliberately. `fold_cumulative_on_rearm` moves it into `cumulative_cost_usd` and zeroes `cost_usd`, but it runs only when `detect_rearm_dispatch` returns true — and that helper requires `cost_usd > 0` at dispatch time. When a re-arm path zeroes `cost_usd` before the driver next dispatches, detection fails, the fold never runs, and the spend survives only in `re_arm_history[].prior_cost_usd`. Both shapes exist in this repository right now:

```
WU-02 (FEAT-2026-0020)  cost=0.539  cum=0.473  priors=[0.473]   fold ran
WU-03 (FEAT-2026-0069)  cost=2.384  cum=5.261  priors=[5.261]   fold ran
WU-07 (FEAT-2026-0053)  cost=4.282  cum=—      priors=[5.01]    fold never ran
WU-04 (FEAT-2026-0020)  cost=0.163  cum=—      priors=[0.163]   fold never ran
```

[FEAT-2026-0062](roadmap-archive.md#feat-2026-0062) made the two cost *consumers* shape-independent, so nothing the driver decides is wrong today because of this. It deliberately scoped the fold itself OUT: fixing what gets **written** changes every future work unit's frontmatter, a different blast radius from fixing what gets **read**. That deferral was right for that feature and is not a reason to leave this permanently.

What remains is a frontmatter contract that means two different things with no way to tell which. A reader — human or code — cannot distinguish "this unit was never re-armed" from "this unit was re-armed and the fold silently did not run", because both present as an absent `cumulative_cost_usd`. The divergence also guarantees that `cumulative_duration_seconds`, `cumulative_input_tokens`, and `cumulative_output_tokens` carry the identical split; no consumer gates on them yet, so it is invisible rather than absent. And `detect_rearm_dispatch`'s `cost_usd > 0` guard is itself the shape `LEARNINGS [FEAT-2026-0053/G2-CLOSE]` warns about — a guard inferring "already folded" from a zero it cannot distinguish from "never had a cost".

**Goal.** Decide whether the frontmatter has one fold path or two, and make the code and the contract agree either way. Two shapes are viable and the feature should choose one rather than splitting the difference. **Converge:** make the fold run on every re-arm regardless of the `cost_usd` value — replacing the value-inferred guard with an explicit signal such as a fold marker or a re-arm-cycle counter — so `cumulative_*` is always the lifetime accumulator and `re_arm_history[].prior_*` becomes a pure audit record. **Or admit two paths:** state in the frontmatter contract that prior spend lives in either place, and give readers one documented helper that resolves it — which is close to what FEAT-2026-0062 already shipped in `wu_lifetime_cost_usd`, and would mean promoting that function from a cost-specific reader to the contract's canonical accessor. Whichever is chosen, existing work units carrying the fold-never-ran shape must be handled explicitly — migrated, or left alone with the reason recorded — not silently outlived.

**Benefits.** The frontmatter stops encoding a distinction nobody intended, so the next person to read `cumulative_cost_usd` is not misled the way FEAT-2026-0062's drafting was. The same fix covers the duration and token accumulators before a consumer starts gating on them and inherits the defect. And a value-inferred "already done" guard — a recurring source of defects in this driver — is removed rather than worked around.

**Status: done.** Terminal close ran twice: `partially_met` on the first cycle, then `met` on the second after the hedge was fixed rather than accepted. Four implementation work units, all `done`, all passing first attempt at $5.95 against $11.50 planned; feature total $14.05 recorded against a $20.00 gate budget, excluding the second close cycle.

**Converge was chosen**, not admit-two-paths. `detect_rearm_dispatch` no longer reads `cost_usd`'s value: a new `folded_through_re_arm` frontmatter integer is compared against `re_arm_count`, and `fold_cumulative_on_rearm` stamps it in the same write set as the four accumulators, so a re-arm whose prior cycle cost $0.00 still folds and a second call for one re-arm is a proven no-op. `cumulative_*` is now unconditionally the lifetime accumulator and `re_arm_history[].prior_*` a pure audit record; `WU.template.md` — both shipped copies — and `cost.py`'s docstring say so. `wu_lifetime_cost_usd` keeps its behaviour and its events-first precedence; only its fallback's documentation changed. The two fold-never-ran units named above were **migrated, not annotated** — the migration ships as `specfuse/loop/rearm_migration.py` so a downstream project can run it against its own records rather than hand-editing them. All 9 re-armed work units in this repository now carry `folded_through_re_arm` equal to their `re_arm_count`.

**The contract is verified by a production run of itself.** The close work unit was re-armed between its two cycles, so the driver's fold ran on `WU-90-gate-1-close.md` unattended: $8.102319, 953.536s, 140 input and 60331 output tokens moved into `cumulative_*`, the per-cycle fields reset, the marker stamped — matching the prior `attempt_outcome` event exactly. The changed path is proven on a real work unit in ordinary operation, not only on fixtures.

**One defect found and fixed inside the feature.** The migration's fold-never-ran branch folded `re_arm_history[].prior_cost_usd` into `cumulative_cost_usd` without resetting `cost_usd` — right for a unit re-armed and re-dispatched, a double-count for one re-armed and never re-dispatched, which is WU-04 (FEAT-2026-0020), `completed_out_of_loop: true`. The first close found it by reconciling every re-armed WU against its own `events.jsonl`, could not repair it inside its own **Do not touch** boundary, and recorded FU-1 with an executable re-run condition. The operator armed **WU-04 (FEAT-2026-0067/T04)** against that text instead of accepting the hedge; it landed the one-branch fix with a regression test for the re-dispatched case, repaired the record, and passed first try at $1.38. The re-armed close re-ran the reconciliation: every re-armed WU's `cost_usd + cumulative_cost_usd` now equals its `attempt_outcome` sum. This is also the value-with-two-meanings defect class the feature exists to remove, reproduced by its own fix — the module docstring now carries the warning where the next offline reader of `cost_usd` would make the same mistake.

**Known and deliberately not fixed.** WU-01 (FEAT-2026-0060)'s `cumulative_cost_usd` under-counts its lifetime by $9.23 — the old value guard's damage, frozen in a `done` record. `PLAN.md` scoped back-filling `done` features' cost records out before any work began, so this is a pre-existing condition rather than an unmet criterion, and a candidate for a future feature. No consumer reads it: `wu_lifetime_cost_usd` is events-first and only falls back to frontmatter for a WU with no `attempt_outcome` events at all.

**Not verified here.** No downstream project has been migrated. `rearm_migration.py` ran against exactly one tree — this one — and every branch it handles beyond that tree's two real shapes is exercised only by fixtures. That distinction is not hypothetical: the one real shape its fixtures did not model is precisely the one it got wrong. A project that upgrades and never runs the migration is safe, because an absent marker reads as `0` and the next dispatch-time fold is correct regardless.

<a id="feat-2026-0064"></a>
## FEAT-2026-0064 — Release-notes document maintained as work lands, tied to versions and tags

**Why.** This repository has shipped eight tagged releases (`v0.4.0` through `v0.8.0`) and has no release-notes document of any kind — `find . -iname "CHANGELOG*"` returns nothing, and `grep -rniE "changelog|release.?note"` over `specfuse/`, `scripts/`, `.specfuse/skills/`, and `docs/` returns nothing outside mirrored package data. The only record of what a version changed is the git log and a list of PR titles. Someone running `pipx upgrade specfuse` cannot find out what moved, and more importantly cannot find out whether anything that moved will break them.

The material already exists and is thrown away at release time. Every feature's close ceremony is *required* by `.specfuse/rules/close-discipline.md` §3 to enumerate consumer-visible contract changes or write the explicit `n/a` line; every feature carries a roadmap detail section and a `RETROSPECTIVE.md`; every bug is one branch and one PR by convention. The loop already produces a structured, human-written statement of user-facing impact for every unit of work it completes — and nothing collects it. [FEAT-2026-0061](roadmap-archive.md#feat-2026-0061) is the live example: its close enumerated a real behaviour change (a downstream project running `auto` begins halting for human arming where it previously armed silently) that reaches no user-facing document today and will surprise the first person it happens to.

The gap widens under autonomy. As more work lands via `auto` features and the bug pipeline, fewer changes pass under a human's eye at all, and the release note becomes the only place a consumer-visible change is stated in prose someone actually reads.

**Goal.** Maintain a release-notes document per project, written incrementally as features and bug fixes land rather than reconstructed at release time, and tie its sections to the version tags they shipped in. Four parts. First, the **document and its schema**: a `CHANGELOG.md` in Keep-a-Changelog shape with an `Unreleased` section, entries classified (added / changed / fixed / **breaking**), each carrying its FEAT-ID or issue number so the entry traces to its evidence. Second, the **collection point**: decide whether entries are appended by the close ceremony as each feature finishes — which is where the consumer-visible enumeration is already written and therefore costs nothing extra — or generated at release time by walking merged PRs and close records. Prefer the former; a release-time generator re-derives from commit subjects what a human already stated more precisely, and that is how breaking changes get downgraded into one-liners. Third, the **release wiring**: `scripts/bump_version.py` already sets all four version sources atomically and is the natural hook — cutting a version stamps the `Unreleased` heading with the version and date, and a released section becomes immutable. Fourth, it must **work for a target project**, not only this one, since it ships in the scaffold; the tag-name convention and the version-source list are this repo's, and both need to be configuration rather than a hardcode.

Two decisions to settle when this is drafted, both noted here so they are not discovered mid-gate. Whether the document is a driver-maintained artifact (mechanically appended, lint-enforced) or a human-authored one the driver merely reminds about — the first is enforceable and risks unreadable prose, the second reads well and rots. And how the specfuse umbrella package's own bump-and-tag relates: releasing `specfuse-loop` requires bumping *and* tagging the umbrella before `pipx upgrade` re-resolves the driver, so a release note that documents only the driver's version describes half the release.

**Benefits.** A consumer can answer "what changed, and will it break me" from one document instead of a commit range. Breaking changes get stated once, in prose, at the moment the person who made them still remembers why — which is the only moment that statement is cheap. The close ceremony's consumer-visible enumeration stops being write-only. And every project the scaffold installs into inherits the same discipline rather than reinventing a changelog convention per repo.

**Gate 1 — shipped.** Three work units `done`, each on its first attempt, no escalations and no re-arms, **$9.64 against $11.00 planned (−12.4%)** — 45.9% of the $21.00 gate budget. `CHANGELOG.md` exists at the repository root in Keep-a-Changelog shape; `specfuse/loop/changelog.py` parses it back (four entry classes, a required `FEAT-YYYY-NNNN` or `#<issue>` trace per entry, findings rather than tracebacks on malformed input, no import of `loop.py`); `close-discipline.md` §3 and `fix-bug` both append; `closing_requirements.py`'s new `close-k` fires when a close names a real contract change and `Unreleased` gained no entry for its FEAT-ID; and `scripts/bump_version.py` stamps the section in the same call that sets all four version sources. Three oracles, all red on HEAD before their WU ran: `tests/test_changelog_schema.py`, `tests/test_changelog_collection.py`, `tests/test_changelog_release_wiring.py`.

**Two collection points, not the one this row described.** The row says "the collection point", singular, and describes only the close ceremony. Bugs have no close ceremony — `1 bug = 1 branch = 1 PR`, no feature folder, no §3 enumeration — and **four of the nine PRs merged 2026-08-03/04 were bugs**, including #473, which changed operator-facing halt output. A close-only collector would have dropped every one and the document would have looked complete while being wrong about half the release. So the feature shipped two: the close ceremony collects via §3 under a mechanical check, and `fix-bug` collects via a pre-PR step in the skill. The bug side is the weaker half by construction — an instruction, not a guard — and it has not yet been exercised by a real bug.

**The umbrella version is required, and it is packed into the version field.** `stamp_release` refuses to stamp without `--umbrella-version`, because `pipx upgrade specfuse` resolves through the umbrella package and a driver version nobody can install is half a release. T01's released-heading regex requires the date to be the last token on the line, so there was no room after it; the umbrella version is packed inside the version field as `<version>+umbrella.<umbrella>` and read back with `split_version_field`. The heading is therefore **not plain semver**, which no release has yet met — the release that follows this feature is the first.

**One gap found at close, not by any acceptance criterion.** `specfuse init` does not create a root `CHANGELOG.md` — it copies `specfuse/loop/data/` into `.specfuse/` and writes `.gitignore`, `CLAUDE.md`, and `.claude/settings.json`, and `find specfuse/loop/data -iname "*CHANGELOG*"` returns nothing. But `close-discipline.md` ships in that payload and `close-k` reads `<repo_root>/CHANGELOG.md`, so **a downstream project inherits the obligation and the check before it has the file**, and its first close with a real §3 enumeration fails with `CHANGELOG.md does not exist` until someone adds one. The failure is loud and self-describing and the fix is one file with one heading, so this is a papercut rather than a silent break — but nothing in this feature closes it. Named here so it is not lost, and stated in the shipped `breaking` changelog entry so a consumer meets it before it bites.

**No backfill, deliberately.** Fifty-one `done` features and every prior bug PR predate this document and are not represented in it. A check demanding retrospective coverage would have been red on arrival and could only pass by fabricating fifty-one summaries from commit archaeology — the exact low-quality re-derivation this feature exists to prevent, wearing the authority of a release note. The early document is thin because history was not audited, and the file says so in a comment a reader meets before the first entry.

**Status: done.** Terminal close ran with verdict `met`, every acceptance criterion verified against a re-run oracle in the close's own session. The close's §3 enumeration — six items, two `breaking` (the required `--umbrella-version` flag and the new `close-k` check) — was appended to `CHANGELOG.md`'s `Unreleased` through `append_entry` rather than by hand, making this close the first entry ever written into the document the feature built. The retrospective reports what that was actually like: the thinking happened once and served both surfaces, the writing genuinely happened twice at two compression levels, and the order is what made the second one cheap. Three findings with no unmet criterion behind them — the missing scaffolded `CHANGELOG.md`, the unexercised bug path, and a release stamp that has never run for real — are recorded in the retrospective with where each gets checked.

<a id="feat-2026-0059"></a>
## FEAT-2026-0059 — Hedged-close ergonomics: classified follow-ups, verdict-ceiling headline, routed-finding tracking

**Why.** First live run of `/accept-hedged-close` (FEAT-2026-0054, 2026-07-30) showed the operator-facing gap: the skill quotes the raw D-entry follow-up record and demands a one-line reason, but never answers the operator's actual questions — *why couldn't this close `met`, and what kind of reason is expected?* On 0054 the answer was derivable but buried: two entries were unclosable in-repo by construction (an operator-signature entry and a future-rate-in-other-repos entry) and two were findings routed to other owners — meaning `met_locally` was the structural ceiling and no rework alternative existed. The operator had to reverse-engineer that from four verbose entries. Routed findings also currently survive only as retrospective prose, with no tracking surface.

**Goal.** (1) `close-discipline.md` §2's hedged-verdict record gains a required `kind:` per entry — `acceptance-discharged` / `externally-verifiable-later` / `routed-finding` — written by the close WU, which has the context. (2) `/accept-hedged-close` reads the classification and leads with a verdict-ceiling headline ("no in-repo rework can raise this verdict" vs "rework exists: <what>"), states the explicit alternative (accept now vs stay hedged until the named upgrade conditions, then recheck), and scaffolds the reason prompt from the classification while still requiring the operator's own words (`operator-escalation.md`'s never-author rule intact). (3) At acceptance, each `routed-finding` entry prompts for a tracking surface — existing issue/roadmap row, or offer `/roadmap-add` / `gh issue create` — so accepted follow-ups land in a queue instead of dying in prose.

**Benefits.** The operator's accept/rework decision becomes a choice between two named options instead of a blank-line prompt after a wall of quotes; acceptance reasons get sharper because the skill names what is being accepted; routed findings stop leaking; the classification lives in the §2 contract (one home) so the skill re-derives nothing.

**Gate 1 — shipped.** Three work units `done`, each on its first attempt, no escalations, **$6.12 against $9.50 planned (−35.6%)**. `close-discipline.md` §2 gains a required per-entry `kind:`; `closing_requirements.py` holds the four values and the one function that turns a set of kinds into a verdict ceiling; `lint_closing.py`'s `close-j` refuses a hedged close whose own record has an entry with no `kind:` or an unrecognised one. `/accept-hedged-close` reads the classification, prints the ceiling headline **before** any entry detail, scaffolds the reason prompt from that ceiling without pre-filling a word of it, and prompts each `routed-finding` entry for a tracking surface — non-blocking, so the skill stays single-confirm. Three oracles, all red on HEAD before their WU ran: `tests/test_hedged_kind_contract.py`, `tests/test_accept_hedged_close_headline.py`, `tests/test_routed_finding_tracking.py`.

**Four kinds, not the three this row proposed.** `inherent` was added deliberately. [FEAT-2026-0042](roadmap-archive.md#feat-2026-0042)'s close had already invented the category in prose — *"Fix correctness — **Inherent.** Not deferred, not scheduled, not a gap. **Never.**"* — because the contract had no slot for it. Shipping three would force the next close to invent it again in different words, and leave a reader with no mechanical way to tell "nobody has done this yet" from "this can never be done". The ceiling rule is unaffected: only `externally-verifiable-later` implies rework exists; `inherent` collapses to the same ceiling as the other two, for a different reason.

**The lint is scoped to the close under lint, and that is load-bearing.** Two hedged records already exist ([FEAT-2026-0041](roadmap-archive.md#feat-2026-0041), [FEAT-2026-0042](roadmap-archive.md#feat-2026-0042)) and neither carries `kind:`. A corpus sweep over `.specfuse/features/*/RETROSPECTIVE.md` would have been red on arrival and unfixable without rewriting closed features' history. `close-j` reads only the feature directory currently being linted; a test plants a malformed record in another feature and asserts it produces no finding.

**Status: done** — terminal close ran with verdict `met_locally`; the operator accepted it, discharging both follow-ups' acknowledgment half. The two entries were classified under the contract this feature ships: the §3 consumer-visible contract-change list (`acceptance-discharged`, eight items), and whether the ceiling headline actually helps a human decide faster (`externally-verifiable-later`). **That second one was answered, and the answer was negative** — the operator's verdict on this feature's own headline was *"it didn't help much, perhaps because the feature itself is quite abstract"*. The record explicitly invited a plain "no" as better evidence than the tests supply, and this is the least favourable case available: the feature's own hedge is a rule contract, abstract by construction, where FEAT-2026-0042's was concrete. Re-evaluation on a concrete hedge is filed rather than left in prose. Enumeration and both entries are in the feature's `RETROSPECTIVE.md`.

<a id="feat-2026-0073"></a>
## FEAT-2026-0073 — Envelope `correlation_id` pattern rejects closing-sequence and hygiene work-unit IDs

**Why.** The vendored event envelope constrains `correlation_id` with

```
^(FEAT|INIT)-\d{4}-\d{4}(/F\d{2})?(/T\d{2})?$
```

which accepts a substantive work unit (`/T01`) and nothing else. `.specfuse/rules/correlation-ids.md` §31-41 documents two further shapes as valid: closing-sequence units use `G<n>-<NAME>` (`RETRO`, `LESSONS`, `DOCS`, `PLAN`, `CLOSE`, `CLOSE-INTERMEDIATE`), and hygiene units use `TNNH[N…]`. The envelope accepts neither, so **every event a closing work unit has ever emitted fails validation**.

Measured across the corpus: **279 failures in 36 of 45 feature folders**. The distribution is exactly what the gap predicts — `G1-CLOSE` 61, `G1-PLAN` 59, `G2-PLAN` 24, `G1-CLOSE-INTERMEDIATE` 20, `G2-CLOSE` 18, `G3-CLOSE` 13. This is not drift: the rules file and the schema have disagreed since closing units were given their own ID shape.

Found by [FEAT-2026-0060](roadmap-archive.md#feat-2026-0060)/T01, which escalated rather than proceed. That WU's registry work resolved cleanly — **zero `event_type` errors corpus-wide** — but its acceptance demanded zero *total* validator errors while its Do-not-touch list forbade the vendored schema, the only file that could deliver them. The two criteria contradicted each other and the work unit could not pass as written. The contradiction was authored, not discovered: FEAT-2026-0060's recon measured `event_type` failures only and never ran the validator's other checks, so its satisfiability answer was wrong. Cost of finding out: one blocked attempt, $4.48.

**Goal.** Make the envelope accept the correlation-ID shapes the methodology documents, or move the driver's ID vocabulary somewhere this repository owns — and decide which, because the same question was answered for `event_type` and the answer may differ here. **Extend the vendored pattern** is simplest and arguably correct at the source, since the orchestrator has closing-sequence work units too and its own logs presumably carry the same IDs; but the file's `$id` points at another repository and its `$comment` is that repository's changelog, so the edit is a cross-repo change that a vendor sync will revert. **Override `correlation_id` in the driver-local registry** keeps ownership local and matches what FEAT-2026-0060 chose for `event_type`; but ID *format* is more plausibly a shared protocol concern than event vocabulary is, and forking it risks the two diverging in a way that breaks a consumer reading both logs. Whichever is chosen, `.specfuse/rules/correlation-ids.md` and the schema must end up stating the same contract, since the whole defect is that they do not.

**Benefits.** The driver's event log validates end to end rather than in the `event_type` dimension alone — the state FEAT-2026-0060 was believed to reach and did not. Unblocks that feature's real-log verification gate, which cannot be green while 279 events fail on a field the gate has no opinion about. And it closes a documented-versus-enforced disagreement that has been silently true for every closing work unit this repository has ever run.

**Status: done.** One gate, two implementation WUs, one terminal close. **The driver-local override was chosen**, extending the mechanism FEAT-2026-0060 built for `event_type` rather than editing the vendored pattern. The deciding evidence was inside the vendored file itself: its `$comment` — the orchestrator's changelog — *already records a prior upstream widening of this exact field*, which makes it a file with live upstream history, and an edit here a fork the next vendor sync reverts **silently**, reinstating every failure with no signal that anything regressed. The row's counter-argument stands and was answered rather than dismissed: ID format really is more plausibly a shared protocol concern than event vocabulary is, so the close **filed the upstream need** at [specfuse/orchestrator#81](https://github.com/specfuse/orchestrator/issues/81) — the override is a documented bridge, not a silent divergence, and the issue records that the driver-local `correlation_id` block should be retired in whichever vendor sync picks up the widened envelope.

Shipped: a `correlation_id` block in `specfuse/loop/data/schemas/driver-event.schema.json` (`closing_names`, `hygiene_suffix_pattern`) read by a new `load_driver_correlation_patterns`, applied in `load_validator`'s existing deep-copy fall-through so the vendored file is never written — `git diff --exit-code specfuse/loop/data/schemas/event.schema.json` exits 0 against both the working tree and `main`. `.specfuse/rules/correlation-ids.md` was reconciled in the same WU, since the defect was the two surfaces disagreeing and widening one alone would have shifted that rather than closed it; a test enumerates the shapes from each and compares them mechanically. `.specfuse/scripts/event_type_gate.py` then widened from `event_type` errors to the whole envelope, and its stale scoping paragraph — plus the matching `verification.yml` comment claiming 279 correlation_id errors remain — went with the change. The gate keeps its name; renaming it is a follow-up bug.

Corrected count: the row's **279 in 36 of 45 folders** was a dated measurement. Re-measured at close time under the same methodology: **288 errors across 39 folders**, still `{'correlation_id': 288, 'other': 0}` — `G<n>-CLOSE` 101, `G<n>-PLAN` 87, `G<n>-CLOSE-INTERMEDIATE` 28, `G<n>-DOCS` 23, `G<n>-RETRO` 22, `G<n>-LESSONS` 20, plus 7 hygiene `TNNH`. The growth is entirely closing units emitted by features that closed in the interim; no new error class ever appeared, which is the condition the gate's satisfiability answer rested on. After the fix: `ok: no validation errors across 47 events.jsonl file(s), 1102 event(s) checked`, exit 0.

Cost: **$12.10 of implementation spend against $7.50 planned**, of which **63% ($7.64) went to four non-passing attempts that all failed the same mechanical guard** — a `produces:` path showing no diff. Three of those were T02 spinning on an authoring defect (its body invited a rename its own `produces:` list forbade) and cost $5.47 before escalating; the amended body then passed first try at $1.65. Residual risk, recorded rather than resolved: nothing in this repository detects the local and upstream `correlation_id` definitions drifting apart. See `RETROSPECTIVE.md`.

<a id="feat-2026-0034"></a>
## FEAT-2026-0034 — Roadmap link-integrity lint: resolvable Blocked-by links, anchor adjacency, cross-file ID uniqueness

**Why.** The `blocked` feature status (shipped in loop 0.3.24) is only meaningful if a blocked feature actually names its unmet dependency — an ADR or an upstream FEAT — and links to it. Nothing enforces that today: `lint_plan` validates feature dirs, PLAN frontmatter, and the gate/WU graph, not the roadmap-table prose. So a row can sit at `status: blocked` with no `**Blocked by.**` block at all (silently collapsing the deliberate `blocked`-vs-`deferred` distinction — `deferred` is the no-named-blocker park), or with a link that has rotted: an ADR path that moved, or a `#feat-yyyy-nnnn` anchor whose target was archived.

A 2026-07-30 manual audit of `roadmap.md` + `roadmap-archive.md` found four distinct rot shapes and 19 instances, only some of which a resolution-only check would catch. (1) **Unresolvable refs** — 10 prose links to archived features still using the bare `#feat-…` form after the section moved to `roadmap-archive.md`, plus 5 in the archive pointing the other way at sections that live in `roadmap.md`; the rot is bidirectional, so a one-file linter misses half of it. (2) **Missing anchors** — `blocked` rows 0041 and 0047 whose Detail cells linked to sections that never carried an `<a id>`. (3) **Misattached anchors** — the anchor above the 0053 section read `feat-2026-0069`, so 0053's Detail cell was dead *and* 0069's ref silently landed on the wrong feature. (4) **Duplicate IDs across files** — `/roadmap-archive` dragged the preceding live feature's anchor along with each section it moved, leaving `feat-2026-0041` and `feat-2026-0047` defined in *both* files; those refs resolved cleanly to the wrong section, which is strictly worse than a dead link because nothing visibly breaks. Shapes 3 and 4 are the archiver misfiring on every run, so they recur until linted.

**Goal.** A roadmap link-integrity lint pass (extend `lint_plan.py` or a sibling roadmap linter, wired into the same gate) reading `roadmap.md` and `roadmap-archive.md` as one link graph, checking four invariants. **Blocked-by presence and resolution** — every `blocked` row's detail section carries a `**Blocked by.**` block with at least one link; each link resolves (ADR path exists on disk or is a well-formed URL; a feature link points at a live `<a id="feat-…">` anchor in either file). Symmetrically WARN on a `**Blocked by.**` block attached to a non-`blocked` row. **Ref resolution, both directions** — every `#feat-…` ref in either file resolves against the anchor set of the file it names, with a bare `#…` resolving same-file; an ERROR names the correct cross-file form as the fix, since the mechanical repair is a prefix rewrite. **Anchor adjacency** — every `<a id="feat-YYYY-NNNN">` is immediately followed (blank lines allowed) by a `## FEAT-YYYY-NNNN` heading whose ID matches; an anchor followed by a different feature's heading, or by another anchor, is an ERROR. This is the check that catches shape 3 and the archiver's stray-anchor output. **Cross-file ID uniqueness** — no `feat-…` ID is defined in both files, and none twice within a file. Round out with a WARN for a row whose Detail cell is `—` while a detail section for that ID exists (the reverse of link rot: a live section nothing points at).

**Benefits.** Makes `blocked` trustworthy: the roadmap cannot display `blocked` without stating, resolvably, what it waits on. Catches all four rot shapes at lint time rather than when a human clicks a dead link — or worse, follows a resolvable link to the wrong feature and reasons from it. Adjacency and uniqueness turn `/roadmap-archive`'s stray-anchor defect from a silent recurring corruption into a failing check the next archive run trips immediately, which is the durable fix; repairing the current instances by hand is not. Keeps the machine-checkable invariants ahead of the prose conventions.

**What was built.** A **sibling** linter, not an extension of `lint_plan.py` — `lint_plan` is feature-scoped and the roadmap belongs to no feature, so folding a repo-scoped check into it would mean either N identical findings or a second mode on a single-job tool. `specfuse/loop/lint_roadmap.py` ships in the package (every Specfuse project has a roadmap and archives features, so every one grows this rot) and exposes `lint_roadmap(repo_root) -> list[Finding]`, returning structured findings rather than raising — a linter that crashes in a gate cannot distinguish "found a problem" from "could not look". `.specfuse/scripts/roadmap_link_gate.py` is the thin entry point, wired into `verification.yml`'s `code` set as `roadmap-link-gate`, following the `event_type_gate.py` / `arm_sweep_gate.py` precedent. ERROR findings fail the gate; the two WARN classes (a `**Blocked by.**` block on a non-`blocked` row, an orphan detail section) print and deliberately do not — a gate red for tidiness gets ignored, which is how this rot survived long enough to need a linter. All four invariants plus the orphan WARN shipped as scoped. The lint reads the same anchor/heading pairing `auto_archive_feature` writes but does not import it: a check sharing its subject's parser inherits its bugs.

**Correction to the "Why" above, found at close time.** The 2026-07-30 audit's shapes **3 and 4** (misattached anchors, cross-file duplicate IDs) are **no longer produced** — `auto_archive_feature` was fixed in the interim; its section regex now stops at the next `<a id="` and it strips its own preceding anchor. Driving the real archiver over a copy of the real corpus for all 9 archivable features produced zero instances of either shape. What is still live is **shape 1**: the archiver moves a detail section without rewriting the refs pointing at it or carried inside it, so 2 of those 9 archives each introduced two dead refs, one in each direction. The new gate catches all four. Fixing the archiver's ref rewrite remains outstanding and is bug-shaped (one branch, one PR), not a feature — and it is now covered by a check that fails loudly the moment it regresses.

**Scope explicitly out.** Fixing `auto_archive_feature` (the failing check is the durable fix, per the Benefits above). Repairing rot instances — two live violations were repaired in a commit *ahead* of this feature so its "exits 0 on this tree" criterion was satisfiable on arrival; consequently every red-before test is a purpose-built fixture, not live rot. Roadmap prose beyond the link graph (no row-ordering, status-vocabulary, or detail-content rules). **ADR approval state** — a `**Blocked by.**` ADR link is checked for existence, never for acceptance; that is deliberate and not a gap.

**Status: done.** Shipped as `specfuse/loop/lint_roadmap.py` + `.specfuse/scripts/roadmap_link_gate.py`, gated as `roadmap-link-gate`. Note for downstream projects: this gate is inherited on upgrade, so a project whose roadmap already carries ERROR-severity rot starts failing a gate it did not previously have.

<a id="feat-2026-0042"></a>
## FEAT-2026-0042 — Autofix wiring: headless fix-bug from diagnosed findings behind per-component dial

**Why.** With detection (FEAT-2026-0040) and diagnosis (FEAT-2026-0041) in place, the remaining step to a self-healing repo is launching the existing fix-bug skill (1 bug = 1 branch = 1 PR, test-first) from a diagnosed finding — guarded, because a wrong diagnosis can produce a confidently-wrong PR and an incident storm can flood the repo.

**Goal.** Per-component `autofix: on|off` (default off). Auto-fire headless `/fix-bug NN` only when the diagnosis self-reports confident + `fix_scope: small`; `large`/`external` findings route to human triage or roadmap promotion instead. One fix run per fingerprint, daily auto-fix cap, and an "auto-fix attempted, failed" label so refusals and failures surface instead of dying silently. Human merge on a protected branch is the default floor; auto-merge is governed by the agent-level dial and hardcoded guardrails defined in FEAT-2026-0048 (supersession recorded 2026-07-25 — small test-first bug diffs are cheap to revert, so bugs may graduate to auto-merge; features never do here).

**Benefits.** Autonomy level 3: wake up to a ready test-first PR for known-small failures, on components that earned the dial. Guardrails (confidence gate, caps, failure labels) keep bad diagnoses and storms from eroding trust in the pipeline.

**Built (reconciled at the terminal close, `FEAT-2026-0042/G2-CLOSE`, verdict `partially_met`).** Two gates. Gate 1 shipped the decision layer with no caller: `specfuse/monitor/autofix.py` (`decide()` over `FIRE`/`ROUTE_TO_HUMAN`/`DECLINE`, `CONFIDENCE_THRESHOLD = 0.8` as a module constant), `specfuse/monitor/autofix_state.py` (attempt state as a marker on the finding issue, `DAILY_CAP = 5` over a rolling 24h window, both failing closed), the `auto-fix-attempted-failed` label in `LABEL_REGISTRY`, and a headless mode for the `fix-bug` skill — which this row's goal assumed already existed and did not. Gate 2 shipped the firing path: `specfuse/monitor/autofix_invoke.py` (builds the headless invocation, classifies its result into `refused`/`could_not_proceed`/`completed`) and `specfuse/monitor/autofix_run.py` (read the diagnosis, decide, record the attempt **before** firing, invoke, label).

**Where the goal's phrasing is now true, and where it is not.** "Headless `/fix-bug NN`" is true: the mode exists and a real session was launched from a real diagnosed finding. "**Auto**-fire" is **not** true. The firing path lives behind its own entry point, `python3 -m specfuse.monitor.autofix_run`, deliberately *not* wired into the harvest cycle and not registered as a console script — so nothing fires on a schedule and a human or a later feature must call it. And the chain's last link is unobserved: the one live end-to-end run decided `FIRE`, recorded the attempt, launched the session, and returned `could_not_proceed`, so **no pull request has ever been produced by this path**. Fix correctness is an inherent, permanent non-guarantee, not deferred work. See `RETROSPECTIVE.md` for the raw evidence, the residue report, and the follow-up record naming what a re-armed live run would have to show to upgrade the verdict.

**Status: done.** Two gates. Gate 1 shipped the decision layer, the GitHub-held rate-limit state and a headless `fix-bug` mode — all inert. Gate 2 made the dial live and fired it once for real. Closed `partially_met` and accepted by the operator: the single live fire returned `could_not_proceed` (the planted bug was too thin for `fix-bug` to reduce to a falsifying test), so the mechanism is proven end to end but **no pull request has yet been produced** — that follow-up is carried forward open. Auto-merge remains impossible here; FEAT-2026-0048 owns it.

<a id="feat-2026-0041"></a>
## FEAT-2026-0041 — diagnose-issue skill: root-cause diagnosis of harvester findings (manual + headless)

**Why.** A harvester finding carries the artifacts; the unique value of a repo-resident agent is joining them with source code to name the root cause ("DLQ message failed because OrderMapper.cs:142 throws on null DiscountCode") — the thing external monitoring can never do. Diagnosis must earn trust interactively before running unattended.

**Goal.** A `/diagnose-issue NN` skill: pulls artifact section + correlation-ID-linked telemetry from the finding issue, reads the component source, and posts a structured diagnosis comment — root cause, evidence trail, candidate fix, plus machine-readable `confidence` and `fix_scope: small|large|external` fields (the gate FEAT-2026-0042 consumes). Identical comment format from both entry points: interactive first, headless second. Redaction rules apply to diagnosis prose.

**Scope narrowed at draft time (recorded in `PLAN.md`).** The auto-trigger — harvester firing diagnosis on new fingerprints, the per-component `diagnose: auto` dial, one diagnosis per fingerprint rather than per occurrence — was cut from this feature by operator decision and is now [FEAT-2026-0074](roadmap.md#feat-2026-0074). The seam is that the dial is a *scheduling* concern, not a *diagnosis* concern: FEAT-2026-0042 consumes only the output contract and does not care how the diagnosis came to be written, and building the auto-trigger first would have automated a diagnosis quality nobody had read yet.

**Shipped.** `specfuse/monitor/diagnosis.py` (the `Diagnosis` model, `render`, `parse`, one `<!-- specfuse:diagnosis confidence=... fix_scope=... -->` marker; prose redacted at the render boundary via `redaction.redact_text`, promoted from module-private); the `/diagnose-issue` skill on all three surfaces; `specfuse/monitor/diagnose_cli.py` as the headless entry point, rendering exclusively through the same renderer with byte-identical output asserted; and a live `gh` round-trip — create, comment, read back, parse, close — verified against a real scratch issue rather than a stub, which refuted the `gh` ban in `LEARNINGS [FEAT-2026-0014/T01/gh-claudeP-broken]`. **Diagnosis correctness itself is not verified and cannot be in-loop**; the gate asserts format, contract, and round-trip fidelity only.

**Benefits.** Autonomy level 2 groundwork: a finding can be turned into a structured, machine-readable diagnosis by hand or headlessly, in one format, so FEAT-2026-0042 has a contract to gate on. The per-component manual-to-auto dial (FEAT-2026-0074) then lets diagnosis quality be proven with a human watching before automation, component by component.

**Status: done.**

<a id="feat-2026-0063"></a>
## FEAT-2026-0063 — Branch-observation sweep for the arm predicate

**Why.** [FEAT-2026-0061](roadmap-archive.md#feat-2026-0061) widened `decision_class_paths` and added two `not_evaluable` triggers — a named-uncovered manifest, and a glob or directory in `produces:` the class cannot decide. Both are proven only on fixtures. The same is true of `budget_projection`'s firing branch after [FEAT-2026-0062](roadmap-archive.md#feat-2026-0062): no baselined feature has been over budget, so the branch that fix exists to correct has never fired on real input.

**A correction, recorded because the original framing of this row was wrong and was nearly drafted against.** This row previously argued that a sweep of `evaluate_arm_predicate` across all 44 feature folders returned 42 `not_evaluable — no_baseline`, and concluded the predicate could not be verified against real input at all. That measurement is misleading. Those 42 features predate `write_baseline_if_absent`, which shipped with [FEAT-2026-0053](roadmap-archive.md#feat-2026-0053); they are `done` and will never be dispatched again, so they will never carry a baseline. Sweeping them is asking the predicate about work that no longer exists, and `no_baseline` is the correct answer rather than blindness.

Restricted to the features that actually carry a `PLAN.baseline.json`, the picture inverts (re-measured 2026-08-03; the sample grows by one per baselined feature, so these figures are dated by construction):

```
FEAT-2026-0053  g1  arm=False  fired=[judge_editing, retroactive_edits, open_questions_human_only]
FEAT-2026-0053  g2  arm=False  fired=[judge_editing, retroactive_edits, open_questions_human_only]
FEAT-2026-0053  g3  arm=False  fired=[retroactive_edits]
FEAT-2026-0060  g1  arm=True   fired=-
FEAT-2026-0061  g1  arm=True   fired=-
FEAT-2026-0062  g1  arm=True   fired=-

4 baselined features; class-verdict totals: 41 clean, 7 fired, 0 not_evaluable
```

The **approval path is proven on real input** — `would_arm: True` on three real features with real frontmatter — and three classes fire on real input. `LEARNINGS [FEAT-2026-0053/G1-CLOSE]` warned that a refusal path proven on fixtures says nothing about the approval path; that warning has since been answered by the corpus itself, and this row should not keep citing it as open.

**What actually remains — wider than this row previously stated.** A per-class sweep of which *branches* have been observed on real input, rather than which classes exist, gives:

```
budget_projection          clean            NEVER fired, NEVER not_evaluable
decision_class_paths       clean            NEVER fired, NEVER not_evaluable
drift_caps                 clean            NEVER fired, NEVER not_evaluable
missing_provenance         clean            NEVER fired, NEVER not_evaluable
plan_next_lint             clean            NEVER fired, NEVER not_evaluable
judge_editing              clean, fired     NEVER not_evaluable
retroactive_edits          clean, fired     NEVER not_evaluable
open_questions_human_only  clean, fired     NEVER not_evaluable
```

**Five of the eight stop classes have never fired on real input**, and `not_evaluable` has never been observed for *any* class — so the fail-closed path this row is named for is entirely unexercised outside fixtures. All firing evidence comes from a **single feature**, FEAT-2026-0053: the same three classes fire at each of its gates and nothing else has ever fired anywhere. This row previously named only two unverified branches (`decision_class_paths`' two `not_evaluable` triggers and `budget_projection`'s firing branch); the real figure is five never-fired classes plus eight never-`not_evaluable` ones. Scope the work to the measured list, not the remembered one.

Two caveats on the sample. It is **four features**, which is thin, though it grows by one per baselined feature with no work from us. And a sweep run over all feature folders reports false blindness by including the 42 that structurally cannot be evaluated, which is how this row acquired its original wrong premise in the first place.

**Goal.** Make the sweep honest and standing rather than ad-hoc. Exclude baseline-less features so the sweep stops reporting `no_baseline` as though it were a finding. Record, per class and per branch, which have fired on real input and which have not, so "unverified" is a named list rather than an assumption — and so a branch that can never fire becomes visible as dead. Decide where that report lives permanently: a `verification.yml` gate the driver runs, or a close-ceremony criterion an agent reports. Prefer the gate — FEAT-2026-0055's close raised the same choice and flagged promoting its tree-wide sweep from a close-time criterion to a driver-run gate as an open follow-up, and this would be the second instance, which is when the pattern earns the tooling. The first `auto` ride against the Specfuse Generator remains the strongest single source of live input, but it is no longer a precondition for this row.

**Benefits.** A sweep that reports only what it can actually evaluate, so its output is evidence instead of noise. A named list of never-fired branches, which is the honest form of "unverified" and the thing a human can act on. And the report becomes a mechanism rather than something a human runs by hand at wrap time — which is how the original mistaken figure survived long enough to reach this roadmap.

**Status: done.** Pulled to `active` on 2026-08-02 and returned to `planned` the same day: drafting recon showed the 42-of-44 figure this row was built on was an artifact of sweeping features that predate baselines, and the operator chose to re-pick rather than draft against a corrected and much smaller premise.

Re-measured 2026-08-03 before the second draft attempt, and the premise had drifted again: FEAT-2026-0060 shipped and carries a baseline, so the sample is four features rather than three (41 clean / 7 fired / 0 `not_evaluable`, `would_arm: True` on three). More materially, the per-*branch* sweep above shows the unverified surface is **five never-fired classes and eight never-`not_evaluable` ones**, not the two branches this row named. Both corrections are folded in above. That this row's figures went stale twice in two days is itself the argument for its Goal: a premise re-derived by hand at pick time is a premise that will be wrong again.

<a id="feat-2026-0060"></a>
## FEAT-2026-0060 — Driver-local event schema registry: sanction the three unsanctioned event types

**Why.** The loop driver emits `gate_reached` and `attempt_outcome` on every run, and FEAT-2026-0053/T04 adds `arm_predicate_evaluated`. None of the three appear in the envelope `event_type` enum in `specfuse/loop/data/schemas/event.schema.json` (a closed 28-entry list this repo does not own), and none have a per-type payload schema — `PER_TYPE_SCHEMA_DIR` holds four schemas, all core-orchestrator types vendored from another repo. The gap is invisible today only because the driver's emit path (`build_event` / `flush_events` in `loop.py`) never invokes the validator: `validate_event.py` is a standalone CLI. So every driver-emitted event is unvalidated in practice, and anyone who does run `validate_event.py` over a real `events.jsonl` gets failures on the driver's own output. FEAT-2026-0053/T04 blocked on discovering this and was unblocked by narrowing its scope, deliberately deferring the question rather than answering it inside a shadow-mode WU.

**Goal.** Decide and implement where driver-local event schemas live, then bring all three types into conformance so `validate_event.py` passes over a real driver-produced `events.jsonl`. Two candidate shapes, to be chosen as part of this feature: (a) extend the vendored registry and envelope enum in the core repo, keeping one registry — correct but cross-repo; or (b) sanction an explicitly-named loop-local schema tier, with manifest entries in the scaffold sync script and its orphan-file test, leaving the core enum alone. Also decide whether emit-time validation should be wired into `build_event` / `flush_events`, or whether `validate_event.py` stays a CI/manual check — an unvalidated emit path is what let three types drift unnoticed.

**Benefits.** The driver's own event stream becomes machine-checkable, which every downstream consumer (`gate-status`, `learnings-suggest`, the harvester, FEAT-2026-0053's shadow telemetry) implicitly assumes today. Removes a standing trap where a WU touching events discovers the gap mid-attempt and blocks, as T04 did at a cost of one wasted 210-second attempt.

**What was actually built — and it was nine types, not the three this section's title names.** Gate 1 closed on 2026-08-03. Both candidate shapes in the Goal above were weighed and **(b) was chosen**: a driver-local registry, `specfuse/loop/data/schemas/driver-event.schema.json`, with an `$id` under `specfuse.dev/loop/` that does not claim the orchestrator namespace. The vendored `event.schema.json` was never edited — confirmed clean against `main` at close — because its `$id` points at another repository and its `$comment` is that repository's changelog, so any edit here would be reverted or silently diverged by the next vendor sync. Resolution is **fall-through, not duplication**: `validate_event.py` resolves an event's `event_type` against the vendored enum first and only falls through to the driver-local registry for types absent there, unioning the two on an in-memory deep copy. `task_started`, `task_completed`, and `human_escalation` were already sanctioned and are deliberately *not* duplicated into the new file. A missing or unreadable registry degrades to vendored-only validation rather than raising, matching `load_per_type_validator`'s additive contract.

**The count corrections, in the order they were found.** This section's title names three types. A corpus sweep on 2026-08-02 found **seven** — four had arrived after this row was filed. The shipped registry holds **nine**: the union of every `build_event` call site with the corpus found `gate_auto_armed` and `re_arm_rejected`, both emitted by real code paths that have never fired in a recorded run and therefore invisible to any corpus sweep. Measured effect: 359 of 1043 corpus events (34%) failed envelope validation on `event_type` before; zero do now, across all 43 feature logs.

**Emit-time validation was declined, deliberately.** The Goal above left it open; the answer is no. Events are buffered and flushed at *outcome* time, so a raise inside `build_event` would destroy the audit record of the work unit that just ran — turning a schema nit into lost diagnostic data at the worst possible moment. The check moved to CI instead: a drift guard (`tests/test_driver_event_registry_covers_emitters.py`) that derives the emitted-type set at test time from call sites ∪ corpus and fails naming the offender, plus an `event-type-gate` in this repository's `.specfuse/verification.yml` running the validator over every `.specfuse/features/*/events.jsonl`. Both are repo-internal; the registry schema is the only part shipped into target scaffolds, and it is permissive, so no downstream build can go red from this feature.

**Scoped out, on purpose.** Per-type payload schemas for the nine — the guard covers type *names* only, and payload shapes are unguarded by construction. And `correlation_id` conformance: **279 errors remain across 36 files** because the vendored pattern rejects the `G<n>-CLOSE` / `G<n>-PLAN` closing-sequence and `TNNH` hygiene ID shapes that `.specfuse/rules/correlation-ids.md` documents as valid. Fixing that means editing the vendored file this feature exists to avoid touching; it is filed as [FEAT-2026-0073](#feat-2026-0073) and is why the gate is scoped to `event_type` errors, to be widened once 0073 lands.

**Status: active — closed `met_locally`, awaiting operator acceptance.** All sixteen close criteria verified on fresh in-session oracle runs; the one hedge is the corpus-wide validator's *total* error count, which reads 279 rather than zero for the `correlation_id` reason above. `event_type` errors are zero, and this feature's own `events.jsonl` validates clean on every class — 12 of its 24 events are types that could not have validated before the feature landed. See `RETROSPECTIVE.md` for the follow-up record and the exact re-run condition that upgrades the verdict to `met`.

**Filing-time status, kept for the record.** Pulled 2026-08-02 with the premise re-verified against the tree that day, not taken from this section's filing-time evidence: the envelope enum is still 28 entries, `gate_reached` / `attempt_outcome` / `arm_predicate_evaluated` are all absent from it, and the emit path still never invokes the validator. The gap is also now shaping design rather than merely sitting there — [FEAT-2026-0062](roadmap-archive.md#feat-2026-0062)/T03 was authored with an explicit constraint to reuse `human_escalation` with a new `reason` value rather than mint a fourth unsanctioned type.

<a id="feat-2026-0062"></a>
## FEAT-2026-0062 — Lifetime-cost reads for `budget_projection` and the per-gate brake

**Why.** Two independent cost consumers read only a work unit's current-dispatch-cycle spend. `budget_projection`, the arm-predicate class that stops a feature heading past 2× its baseline, and `gate_spent_usd`, which drives the per-gate budget brake, both read frontmatter `cost_usd` and neither reads `cumulative_cost_usd` or `re_arm_history[].prior_cost_usd`. A re-arm resets `attempts` to `0` and folds prior spend into the cumulative fields, so **every re-armed work unit is invisible to both**. Measured on [FEAT-2026-0053](roadmap-archive.md#feat-2026-0053) itself, recorded in its gate-2 Findings §1: the projection under-read by **$6.23** and the gate spend by **$5.01**. The bias is not random — it under-reports precisely the work units that have already failed and been retried, which are the ones most likely to be heading toward a budget breach. The brake has a second, separate blind spot found in the same feature: `_should_halt_for_budget` is evaluated *before* each dispatch, so an overrun inside the final work unit of a gate cannot be seen at all. Gate 2 closed **$4.94 over** its $31.50 brake without the brake firing.

**Goal.** Make both consumers read lifetime spend — frontmatter `cumulative_cost_usd` plus the current cycle, or the `attempt_outcome` event sum from `events.jsonl`, which is the source of truth the close ceremony already treats as authoritative. Decide which is canonical and use it in both places rather than letting them diverge again. Separately, decide what the per-gate brake should do about a final-work-unit overrun: a post-dispatch check that reports the breach after the fact is honest and cheap; a projected-cost pre-check that refuses to dispatch a unit whose planned cost would breach is stricter and changes dispatch behaviour. State the choice, because "the brake did not fire" currently means two different things.

**Benefits.** The autonomy budget stop class stops the features it exists to stop, instead of systematically under-reading the retried ones. The per-gate brake's reported number matches what the gate actually spent, so a close ceremony reconciling against it is comparing like with like. Both are prerequisites for trusting `auto` on an unattended run, where a budget stop is one of the few mechanical brakes standing between a stuck feature and an unbounded spend.

**Status: done.**

<a id="feat-2026-0061"></a>
## FEAT-2026-0061 — Dependency-manifest coverage for non-Python ecosystems in `decision_class_paths`

**Why.** `decision_class_paths` is one of the eight arm-predicate stop classes shipped by [FEAT-2026-0053](roadmap-archive.md#feat-2026-0053), and its job is to stop an `auto` feature before it adds a dependency without a human seeing it. It recognises exactly three manifest shapes: `_DEPENDENCY_MANIFEST_EXACT` matches `pyproject.toml` and `package.json`, and `_REQUIREMENTS_RE` matches `requirements*.txt`. Every other ecosystem is invisible. Found while scoping the first `auto` ride against the Specfuse Generator, which is a Maven repository: a work unit there adding a Java dependency to `pom.xml` arms without stopping, and the class reports `clean` while doing it — a false negative, not a gap the operator can see. `build.gradle`, `build.gradle.kts`, `Cargo.toml`, `go.mod`, `Gemfile`, `*.csproj`, and `composer.json` are all in the same position. The class is at its least trustworthy exactly where its value is highest, because a repo whose manifests it cannot read is a repo where it silently never fires.

**Goal.** Extend the manifest surface to the ecosystems Specfuse targets, with the recognition rules stated in one place rather than spread across two module-private constants and a regex. Decide as part of this feature whether coverage is a fixed list or a declared surface a target project can extend in `.specfuse/verification.yml` — the fixed list is simpler and cannot drift out of sync with a project's real build files; a declared surface handles the polyglot monorepo the fixed list will eventually meet. Whichever is chosen, an unrecognised-but-plausible manifest should be surfaced rather than silently passed: a class that cannot evaluate its input should report `not_evaluable`, which the predicate already treats as fail-closed, instead of `clean`. Add the coverage list to `docs/concepts/autonomy-stop-classes.md`, which currently documents the class without naming what it can and cannot see.

**Benefits.** The dependency-addition guard works in the repositories Specfuse is actually used in, rather than only in Python ones. Removes a false-negative class from the autonomy predicate — the most dangerous failure shape it has, because a stop class that reports `clean` on an input it cannot parse is worse than one that is absent, which at least an operator would notice. Unblocks trusting `auto` in the Generator and any other JVM, .NET, Go, or Rust target.

**Status: done.** Single terminal gate, 2 substantive WUs plus close ($11.50 planned, $16.50 gate budget). Both chartered decisions were settled at draft time: coverage is a **fixed list** in `arm_eval.py`, not a declared surface in `.specfuse/verification.yml` — the predicate reads nothing outside `feature_dir` today and a config read would add a new failure mode to a class whose whole defect is reporting a status it cannot justify. `not_evaluable` gets **two triggers**: a named-uncovered manifest list whose every entry must justify why it is not simply covered (it may legitimately end up empty), and a glob or directory in `produces:` that the class cannot decide — the latter measured at 0 of 169 corpus entries, so it is fail-closed without being unsatisfiable.

<a id="feat-2026-0053"></a>
## FEAT-2026-0053 — Autonomous feature mode (auto gate-arming with mechanical stop conditions)

**Why.** The methodology's autonomy field (`auto` / `review` / `supervised`) is written to PLAN.md frontmatter and never read — zero consumers — so every feature stops at every gate boundary exactly like a `review` feature, and a four-gate feature costs four human touches regardless of how routine its gates are. Operator history across features shows those gate reviews are near-universal rubber-stamps whose accepted changes are additive (new work units at gate check, occasionally a new gate), so the per-gate checkpoint spends latency without buying review value; the operator's real read happens at PR review, and merge is always human.

**Goal.** Implement `auto` end-to-end: the driver arms drafted gates and accepts plan-next's additive plan adjustments on its own, stopping only on mechanical conditions. Stop classes: (1) projected budget breach — spent plus planned-remaining exceeds 2× the feature budget; (2) objective-at-risk proxies — hedged close verdict (stays human, unchanged), remaining-work count failing to shrink across two consecutive gate closes, attempt-per-WU trend decay; (3) plan-drift caps — cumulative added WUs above 50% of the original skeleton (counted in planned dollars as well as units), a second added gate, any retroactive edit to passed gates, any addition lacking machine-readable provenance citing the retrospective item or failure event that triggered it; (4) judge-editing — any draft touching verification config, test thresholds, CI workflows, hooks, or the driver itself; (5) decision-class registry hits — human-authored path/keyword registry covering public API shape, schema or data migrations, security posture, dependency additions; (6) model self-flagged must-be-human decisions (self-flags may only subtract autonomy, never grant it). Supporting mechanics: budget projection over the existing per-attempt cost capture in events.jsonl and the per-gate budget brake, tag-before-arm revert points, per-gate doubt summaries accumulated into a FEATURE-REVIEW.md surfaced in the PR body, LEARNINGS entries staged to a pending file promoted at PR review, and a shadow mode that logs would-have-armed / would-have-stopped verdicts on attended features before the dial goes live. Dial read from per-feature frontmatter; policy-file layering may tighten later, never loosen.

**Benefits.** A four-gate feature drops from four human touches to one (the PR review, now fed by the accumulated doubt summaries); unattended runs progress overnight with blast radius bounded by construction — caps, revert tags, and hard floors on judge-editing and retroactive edits — rather than by judgment; shadow-mode telemetry replaces guesswork when tuning stop thresholds; and the declared-but-dead autonomy field finally does what the methodology has promised since it was specified.

**Gate 1 — shipped, and it changes no arming behavior anywhere.** Four substantive work units `done`. `specfuse/loop/plan_baseline.py` writes an immutable `PLAN.baseline.json` snapshot of a feature's as-activated plan graph at first dispatch — write-once by construction, because a refreshable baseline is a drift detector that can be gamed by drifting. `specfuse/loop/arm_eval.py` is the predicate: pure, side-effect-free, mirroring `gate_eval.py`'s shape without sharing its code, returning a per-class verdict (fired / clean / not_evaluable, each with a reason) across seven classes — budget projection, judge-editing, decision-class paths, retroactive edits, drift caps, missing provenance, and open-questions/human-only — plus an overall `would_arm`. The three machine-readable plan-next contract fields (`open_questions`, `human_only`, `provenance`) are documented in both `WU.template.md` copies and covered by **warn-only** lint; the flip to blocking under `auto` is gate 2's, and it is a severity flip needing its own satisfiability answer and runtime probe. Wiring is passive: the driver evaluates and appends one `arm_predicate_evaluated` event at every `awaiting_review` flip, and its control flow after the append is verdict-independent — a predicate exception degrades to an `evaluation_error` payload rather than crashing a gate close. **The organizing principle held.** Only the two veto classes carry model-authored input, and both can only subtract; every approval input is a counter, a path, or a hardcoded constant. Substantive spend **$8.35 against $13.00 drafted (−35.8%)** — three first-attempt passes at roughly 45–48% of estimate, the third consecutive feature to under-run implementation by about a third (issue #260, no per-feature response). The one blocked attempt cost **$1.22**: T04 stopped on discovering that the per-type event-schema registry and the envelope `event_type` enum are both unowned by this repo, which is now **[FEAT-2026-0060](#feat-2026-0060)**; the operator narrowed T04's criteria to follow the existing `gate_reached` / `attempt_outcome` precedent rather than answer the registry question inside a shadow-mode work unit.

**Consumer-visible additions from gate 1, all additive.** Two new modules; three template-documented frontmatter fields; the new `arm_predicate_evaluated` event type on `events.jsonl` (deliberately outside the envelope enum and the per-type registry, matching existing driver-local precedent); and the new per-feature `PLAN.baseline.json` artifact, committed by the driver, which every Specfuse project on a driver at or past 0.7.1 will start seeing appear in its feature folders. Nothing was removed or renamed. Full enumeration and the deferred-verification list are in the feature's `RETROSPECTIVE.md`.

**Gate 1 deliberately did not prove** that either wired call site fires, and the reason generalizes: a work unit that wires new code into the driver cannot be verified by the driver run that wired it — `loop.py` is imported once at process start, so mid-run edits are dead code for the rest of that invocation. `PLAN.baseline.json` existed in **0 of 43** feature directories at close time. Two consequences the arming checkpoint must handle. First, `GATE-01.md`'s first-firing check reads an absent `arm_predicate_evaluated` event as proof the wiring claim is false; on this gate it is more likely a stale process, so **disambiguate before escalating** — did a driver launched after the wiring commit close the gate? Second, this feature's own baseline will be captured at the *next* invocation, from a PLAN.md that by then already contains gate 2's drafted work units, so the "as-activated" graph it records is the post-drift graph. **Gate 2 must not treat this feature's own baseline as evidence that drift detection works.** Relatedly, a close-time sweep of the predicate over all 43 real feature directories returned `would_arm: False` with every class `not_evaluable: no_baseline` on 43 of 43 — the designed fail-closed path confirmed on real input, and the approval path still unproven outside fixtures.

**Gate 2 — shipped. `auto` is real.** Five substantive work units `done`. `specfuse/loop/arm_txn.py` is the pure arm transaction: one function returns the complete write set an arm consists of — every gate-`N+1` draft work unit flipping to `pending`, gate `N` flipping `awaiting_review → passed`, `events.jsonl`, and the accumulated `FEATURE-REVIEW.md` — plus the revert tag *name*; the module performs no git operation at all, which is what makes the one-commit guarantee testable. The driver now reads `autonomy_default` at the single flip site that can arm, tags `pre-arm/<feature-id>/gate-<N>` at the pre-arm HEAD, and carries every write into the one existing bookkeeping commit. **Escalation overrides autonomy by control flow, not by a check**: the two escalation flip sites `return` before the dial is ever consulted. `plan_next_lint` joins the predicate as the **eighth class and the third veto class**, taking the contract-field lint from warn-only to arm-blocking under `auto` only — the CLI is unchanged and every non-`auto` feature is unchanged. Each auto-arm appends the gate's verbatim `open_questions`, verbatim `## Doubt` prose, and per-class verdict to an append-only `FEATURE-REVIEW.md` inside that same commit, with the doubt prose still never an input to the predicate. And under `auto` a closing work unit that touches `.specfuse/LEARNINGS.md` fails a post-pass invariant (`learnings_not_staged`); lessons stage to a feature-local `LEARNINGS-pending.md` from a new shipped template, so **an unread gate cannot write a durable cross-feature rule**. 58 tests across seven suites, all green at close, including a run of the real `loop.run()` against a copy of this feature's own folder — real baseline, real frontmatter, real event log.

**Consumer-visible changes from gate 2 — larger than gate 1's, and not purely additive.** Ten items, three of which need a deliberate read. **`CLASS_NAMES` goes 7 → 8 and `VETO_CLASSES` 2 → 3, so every `arm_predicate_evaluated` payload's `classes` map now carries eight keys instead of seven** — an existing payload that changed shape, not a new one beside it. The `pre-arm/<feature-id>/gate-<N>` tags are real repo objects created with `-f`, one per armed gate. And the bookkeeping commit message changes under `auto`, from `chore(loop): gate N awaiting_review` to `chore(loop): gate N auto-armed gate N+1 (tag …)`, which any existing grep over the bookkeeping trail will miss. Also new: the `gate_auto_armed` event type (this feature's **second** unregistered type, raising rather than flattening the cost of [FEAT-2026-0060](#feat-2026-0060)), the `FEATURE-REVIEW.md` and `LEARNINGS-pending.md` per-feature artifacts, the `LEARNINGS-pending.template.md` template shipped to every downstream project, the `close-e` / `close-intermediate-e` closing requirements, and `docs/dev/auto-arm-recovery.md`. Full enumeration in the feature's `RETROSPECTIVE.md`.

**Gate 2 cost 58% more than drafted, and that reverses the pattern.** Substantive spend **$23.74 against $15.00 (+58.3%)**. One spin accounts for $5.01 — a new veto class firing on the *preceding* work unit's test fixture, surfacing as that unit's test failing under a whole-suite signature, in a file the new unit was forbidden to touch; three sessions chased it before the operator diagnosed the root cause and re-armed with the fixture amendment in scope. Strip it and the gate is still **+24.9%**, with two first-attempt passes landing 44% and 72% over. That is estimate error, not execution error, and it is the fourth data point on **issue #260** pointing the opposite way from the first three: gate 1's units were independent modules and ran a third under; gate 2's five all wire behavior into a live driver and into each other. **The rule should be scoped to independent-module work or it will underestimate every wiring gate.** Gate spend stands at 75.4% of `GATE-02.md`'s `cost_budget_usd: 31.50` with both closing units still to run.

**Gate 2 also resolved gate 1's two open questions, and found one defect of its own.** The first live `arm_predicate_evaluated` event fired on the next driver invocation, and `PLAN.baseline.json` appeared — so gate 1's disambiguation was right and the absent gate-1 event was a stale process, not a false claim. That baseline now contains gates 1, 2 **and** gate 3's placeholder, confirming gate 1's prediction exactly: **this feature's own clean `drift_caps` verdict measures nothing and must not be cited as evidence drift detection works.** The defect: the predicate's `budget_projection` class sums only each unit's per-cycle `cost_usd`, never `cumulative_cost_usd` nor `re_arm_history[].prior_cost_usd`, so it reads **$35.89 of this feature's true $42.12 lifetime spend — 14.8% low, all of it the two re-armed units.** No verdict flips here (the projection stays far under its 2× cap), but the error concentrates in exactly the over-budget re-armed work a budget brake exists to catch. Two small fixes, neither in gate 2's scope.

**Gate 2 deliberately did not prove** that any of it runs in production. No live arm happened — this feature runs `review` by decision, so the whole arm path is verified by tests and by no production ride. `plan_next_lint`'s *firing* path has never executed on a real feature folder (a sweep of all 43 returns 0 fired / 1 clean / 42 not-evaluable, the one clean being this feature, the only one with a baseline). The `LEARNINGS-pending.md` promotion procedure has never been performed by a human. And **`FEATURE-REVIEW.md` is written and never read**: a grep across every skill and shipped template returns zero references outside the module that writes it. Accumulation shipped; the last hop into the PR body is unbuilt and unowned — which on a feature whose premise is replacing four gate reads with one PR read is the checkpoint value silently not being delivered. `G2-PLAN` scopes it into gate 3 or records a deferral with a home.

**Status: done.** Gates 1 and 2 closed; gate 3 (docs and methodology rewrite, migration guidance, plus whatever gate 2's retrospective surfaces) is drafted by `G2-PLAN` and armed by the human. This feature itself runs `autonomy_default: review` — per `[FEAT-2026-0007/G2-LESSONS]`, an enforcement mechanism cannot be exercised by the gate that builds it, so the first live `auto` ride belongs to a successor feature after this branch merges.

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

**Unblocks.** **FEAT-2026-0038** (DLQ quarantine harvesting extends the peek-mode adapter this feature shipped), [FEAT-2026-0041](#feat-2026-0041) (diagnosis reads the finding/issue contract this feature defines), **FEAT-2026-0042** (autofix consumes diagnosed findings), and **FEAT-2026-0043** (the in-cluster runner is the third surface alongside the two shipped here). Each has a detail section below; only 0041 carries an explicit anchor today, so the other three are named rather than linked.

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

**Status: done.**

<a id="feat-2026-0071"></a>
## FEAT-2026-0071 — Label registry + provisioning on init/upgrade

**Why.** Specfuse ships code that queries GitHub labels it never creates. `gh_features.py:28` has run `gh issue list --label specfuse:feature` since FEAT-2026-0003, and [FEAT-2026-0046](roadmap-archive.md#feat-2026-0046) added six more (`needs-human` plus the five escalation categories) whose emitter fails outright on an unknown label — `gh issue create` rejects one. Seven labels, zero provisioning: every consumer repo has to be told to create them by hand, and 0046's own retrospective had to record that as a required operator step rather than something the tool does. Each new label repeats the gap, so the fix is a declared registry rather than a hardcoded list.

**Goal.** Ship (a) a single label registry — name, colour, description, and the consumer that reads it — as the one place a label is declared, with the seven current entries; and (b) provisioning on `specfuse init` and `specfuse upgrade` that creates any missing label and leaves existing ones untouched.

**The constraint that shapes it.** `scaffold.py` has no subprocess, network, or `gh` call today: init and upgrade are pure filesystem, which is why they work offline, in CI containers, and against non-GitHub remotes. Provisioning must not change that contract. It is **best-effort and never fatal** — no `gh`, not authenticated, remote is not GitHub, not a git repo at all, or any per-label failure reports what it would have done and the command still exits zero. An upgrade must never fail because a label could not be created. Idempotent by construction: existing labels are skipped, never `--force`d over an operator's edited colour or description. The opt-out is the `SPECFUSE_NO_LABELS` environment variable plus a `no_labels=True` keyword argument — **not** a `--no-labels` CLI flag, which would need a coordinated umbrella release because `specfuse/cli.py` lives in the umbrella repository. A future umbrella change can add the flag reading the same variable.

**Scope boundary.** `specfuse-monitor` is **out**: it appears only in [FEAT-2026-0040](#feat-2026-0040)'s framing, its harvester does not exist, and provisioning a label whose sole consumer is unbuilt repeats the `[FEAT-2026-0029/G1-CLOSE]` failure 0039 recorded — shipping a surface whose entry point is nonexistent. 0040 adds its own entry when it ships. Renaming `specfuse:feature` to match the kebab-case of the six newer labels is also out: the inconsistency is real, but a rename orphans issues already carrying the label in every consumer repo.

**Benefits.** The escalation queue works on a fresh repo without a setup checklist, closing the operator step 0046 had to defer. `specfuse:feature` discovery stops depending on an undeclared label. And the next feature that needs a label adds one registry entry instead of rediscovering that nothing creates it.

**What shipped.** One terminal gate, three work units, all passing first attempt. `specfuse/loop/labels.py` carries `LABEL_REGISTRY` — seven frozen `LabelSpec` entries whose *names* are imported from `escalation.NEEDS_HUMAN_LABEL`, `escalation.CATEGORY_LABELS`, and a new module-level `gh_features.FEATURE_LABEL` constant (the literal formerly inlined at the `gh issue list` call site), with a test that recomputes that set at test time so the registry cannot drift from what the consumers query. The same module ships `provision_labels(target, *, runner=None)`, following the injectable-runner seam `gh_backend.GitHubBackend` and `escalation.emit_escalation` already use: it lists first and creates only what is missing, never passes `--force`, and returns a `ProvisionReport` (created / already_present / failed / skipped / reason) on every degradation path rather than raising. `scaffold.init()` and `scaffold.upgrade_specfuse()` call it through a `_provision_labels_best_effort()` wrapper that swallows even unexpected exceptions and reports to **stderr only** — the returned list of written `.specfuse/` relpaths is unchanged, which 64 pre-existing scaffold tests assert. Provisioning is wired into `init()`, not `init_specfuse()`.

**Deferred to a post-merge operator step.** No work unit invoked a real GitHub repository — every `gh` interaction ran through an injected stub, so the real `gh label create` argument vector and the successful `gh label list` JSON parse are unverified. This repository's seven labels already existed before the feature was drafted, which makes it an oracle for the idempotent-skip path and not for the create-a-missing-label path. The one real-binary observation is the not-a-git-repository degradation, which the regression suites exercise incidentally. See `RETROSPECTIVE.md` §`What the loop did NOT verify` for the exact re-runs that settle each.

**Status: done.**

<a id="feat-2026-0046"></a>
## FEAT-2026-0046 — Escalation contract: needs-human issues (assigned, structured) + /attention inbox skill

**Why.** An autonomous agent is only trustworthy if what it cannot handle surfaces reliably, with enough context to act on in minutes. Escalations need one queue with an audit trail — GitHub issues, not chat threads — plus a fast local view. Useful immediately with today's manual loop (blocked WUs, awaiting_review gates, blocked features, stale PRs), before any agent exists.

**Goal.** Ship (a) the escalation contract: a `needs-human` labeled GH issue per escalation, auto-assigned to the configured `assignee` (per-category assignee map supported) so escalations surface in native GH inbox/filters; body in plain English — context, options with pros/cons, a recommendation, numbered answers ("reply `1`, `2`, or prose") so the agent can parse replies unambiguously; category labels (gate-review, blocked-wu, triage-question, drafting-needed, merge-approval); answered issues are parsed, acted on, and closed by the next agent run. (b) The `/attention` skill: local inbox over the same label set plus repo-state sweep (gate-status generalized repo-wide), presenting everything needing the human in priority order — the interactive counterpart of the issue queue, never a second source of truth.

**Benefits.** One escalation queue, two views (GH native + rich local session); nothing the agent parks goes silent; the operator's check-in ritual becomes "open /attention, work top-down".

**Delivered** (gate 1, terminal — see [RETROSPECTIVE](features/FEAT-2026-0046-escalation-contract/RETROSPECTIVE.md)). `specfuse/loop/escalation.py`: `NEEDS_HUMAN_LABEL`, the five-member `CATEGORY_LABELS` frozenset (gate-review, blocked-wu, triage-question, drafting-needed, merge-approval), `render_escalation_body` producing the six-part body from `operator-escalation.md` plus a `Reply with a number` section and the `<!-- specfuse:escalation id=… -->` correlation marker, `validate_escalation_body` holding the renderer to that shape, and `emit_escalation` — idempotent per correlation ID via find-then-create over an injectable runner, mirroring `gh_backend.GitHubBackend`'s `_runner` seam. The `/attention` skill ships canonical at `plugins/specfuse/skills/attention/SKILL.md`, vendored byte-identically into `.specfuse/skills/`, sweeping blocked WUs, `awaiting_review` gates, `blocked` features and stale PRs into one priority-ordered view and delegating per-feature depth to `gate-status`. Its read-only claim is enforced by a grep guard with a positive control over both copies, not by prose. 21 tests across four new modules, plus the 4-test vendoring guard.

**Deviations from the goal above, each deliberate.** Assignment is a single `assignee` parameter defaulting to `DEFAULT_ASSIGNEE`; the per-category assignee map is not built — no caller needed one, and the parameter is the seam that would carry it. Parsing an answered issue and closing it is [FEAT-2026-0049](roadmap.md#feat-2026-0049), which lists this contract as its blocker. Outbound notification is [FEAT-2026-0047](roadmap.md#feat-2026-0047). `emit_escalation` is invoked, never auto-fired: no call site exists in `loop.py`, asserted by a grep, per `[FEAT-2026-0003/G3-LESSONS]` on live-mutation work inside the dispatch loop.

**Operator step before first real use.** No work unit touched live GitHub — every `gh` interaction ran through an injected stub. Create the six labels in the target repository and run one real emission twice to confirm the create call and the idempotency search; the retrospective's `## What the loop did NOT verify` section carries the detail and the fallback if the marker search does not match.

**Status: done.**

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

**Status: done.** — the terminal flips are withheld by design on a hedged verdict. `PLAN.md`, the gate, and this row stay un-flipped until an operator accepts the close through `/accept-hedged-close`, which is the path this feature shipped. The driver owns that flip; it is not hand-edited.

<a id="feat-2026-0051"></a>
## FEAT-2026-0051 — Pre-flight baseline gate probe + preexisting_gate_failure halt

**Why.** A `code`-set gate that is already red on the feature's base commit becomes every work unit's exit oracle, so each WU spins to `spinning_signature_repeat` / `spinning_detected` against a failure it did not cause and could not fix. A live run burned roughly $8 of attempt budget across two WUs — one of them a zero-dependency file — on a dependency-audit advisory published after the base tree was last green, with the lockfile byte-identical to the integration branch. This is the time-varying-oracle failure mode already recorded in LEARNINGS (`[FEAT-2026-0007/G1-CLOSE]`); dependency audits are the canonical case, but it generalizes to any externally-fed gate whose verdict changes without a code change.

**Goal.** Run the `code` gate set once at gate entry, before the gate's first WU is dispatched, and record the failing gates plus their signatures as the gate's baseline in `GATE-NN.md` frontmatter. A non-empty baseline halts pre-dispatch under a new `preexisting_gate_failure` reason — distinct from the spinning escalations, which fire only after attempts are spent — with zero work units dispatched. The halt message states in plain language which gate is red, the exact failing signature, and the `git diff <integration-branch>...HEAD --stat` proof that the base tree is unchanged, so no WU caused it. The baseline is re-measured only when the tree moves, keeping resume cheap, and `--no-baseline-probe` (plus a `verification.yml` opt-out) restores today's behavior exactly — a switch that disables the probe, not a mute that suppresses any gate's verdict.

**Benefits.** Repo-wide debt stops charging rent per work unit: one gate-set run replaces a full attempt budget burned per WU, and the operator gets the conclusion — pre-existing, not yours — in the first escalation instead of deriving it by hand after several spurious ones. Enforcement is untouched: every WU is still gated on the full set with unchanged pass/fail semantics.

**Scope note.** The baseline-delta ratchet, the waiver that lets a feature proceed against a red baseline, and `gh` tracking-issue emission are deliberately deferred to [FEAT-2026-0052](roadmap.md#feat-2026-0052) — the ratchet rewrites the pass/fail semantics of the driver's own exit oracle, and the `gh` surface produces no in-loop evidence. Landing the brake first lets that work be designed against real baseline data. Filed from issue #234.

**Status: done.**

<a id="feat-2026-0037"></a>
## FEAT-2026-0037 — Evaluate adopting ruff 0.16's expanded default ruleset (opt-in the valuable families)

**Why.** FEAT-2026-0036 pinned the lint `select` to the classic `E4,E7,E9,F` to stop a version bump from silently changing the gate — the right move for stability, but it deliberately declined the ~300 findings ruff 0.16 now surfaces by default. Some of those families are genuinely valuable and worth adopting on purpose: `PLW1510` (`subprocess.run` without `check=` — a real correctness smell in a driver that shells out constantly), `RUF059` (unused unpacked bindings), `SIM117`/`SIM102` (nested-`with` / collapsible-`if`), `LOG015` (root-logger use), `B`/`S` (bugbear / security). This feature decides — deliberately, family by family — which to add, and does the fixes.

**Goal.** Triage ruff 0.16's expanded default families against this codebase: for each, decide adopt / decline (with a one-line reason), add the adopted ones to `[tool.ruff.lint] select`, and fix the findings — the semantic ones (e.g. `subprocess check=`) reviewed individually, not blanket-autofixed. Land per-family or in small reviewable batches, not one 300-line sweep. Some findings are in `tests/` and low-stakes; prioritise the `specfuse/` driver and `.specfuse/scripts/` surfaces.

**Benefits.** Turns an accident (an upstream default change) into an intentional quality bar; catches real defects (unchecked subprocesses especially matter in the driver); keeps the ruleset a considered choice rather than either "whatever the classic default was" or "whatever ruff decides to add next."

**Status: done.**

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

**Status: done.**

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

**Status: done.**

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

**Status: done.**

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

**Status: done.**

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

**Status: done.** Depends on FEAT-2026-0019 (the package + CLI it extends).
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

**Status: done.** Two gates, both independently shippable; gate 2 consumes
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

**Status: done.** Likely single gate: WU per lifecycle-path test +
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

**Status: done.** Single-gate feature; closing sequence in progress.

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

**Status: abandoned.** Independent of FEAT-2026-0010/0011. Detail the
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

**Status: done.** Independent of FEAT-2026-0015. Can land
in parallel. Probably small (one substantive WU for the driver
fold-logic, one for /unblock-wu + /gate-status updates, one for
WU template/lint changes).
