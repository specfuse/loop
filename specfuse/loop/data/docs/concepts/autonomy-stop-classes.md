# The eight stop classes: an operator-facing reference

`specfuse/loop/arm_eval.py` evaluates eight classes every time a gate closes,
to decide whether the drafted successor gate may arm without a human. This
page is the per-class detail: what each class measures, what makes it fire,
whether it can only veto, and — the thing an operator actually needs when a
feature parks at `awaiting_review` — the concrete action that clears it.

For the conceptual framing (why arming is a separate decision from closing,
why model-authored signals may only veto), see `methodology.md` §9. This page
does not restate that; it documents the eight classes themselves, in the
order `CLASS_NAMES` defines them.

## Three statuses, not two

Each class returns one of three verdicts: `fired`, `clean`, or
`not_evaluable`. `fired` blocks the arm. `clean` means the class found nothing
to object to. `not_evaluable` is the fail-closed path: the class had no basis
to evaluate at all, and `would_arm` is `False` regardless of what any other
class found.

The case an operator will actually meet is `not_evaluable: no_baseline` —
every class returns this together when `PLAN.baseline.json` does not exist for
the feature. Read `not_evaluable` as "this feature cannot arm, full stop," not
as "nothing wrong here." A feature stuck at `not_evaluable` needs its baseline
captured before arming can ever succeed; there is no per-class fix.

## The eight classes

### 1. `budget_projection`

**Measures:** whether the feature's projected total spend (spend to date plus
remaining planned cost) stays under a ceiling derived from the baseline plan.

**Fires when:** projected spend exceeds `BUDGET_PROJECTION_MULTIPLIER` (2.0)
times the baseline's total planned cost.

**Veto channel:** no — mechanical, both approves and blocks on its own.

**Clearing action:** the operator must either reduce the drafted successor
gate's planned cost, or explicitly re-baseline the feature (accepting the
higher spend) before re-running the arm evaluation. This class cannot be
cleared by editing driver code; it clears by changing the plan's numbers.

### 2. `judge_editing`

**Measures:** whether any drafted work unit in the successor gate produces a
file under a judge-path surface — paths that would let a work unit edit its
own verification.

**Fires when:** a drafted WU's `produces:` list contains a path matching one
of `JUDGE_PATHS` — `.specfuse/verification.yml`, `.specfuse/hooks/`,
`.specfuse/rules/`, `.github/workflows/`, or `pyproject.toml` (matched
whole-file) — or a WU declares `produces_driver_helper`.

`JUDGE_PATHS` also covers the driver's own decision modules and the package
data that seeds a judge surface downstream, but **only in the repository that
holds the driver source**; a project that installed Specfuse has no
`specfuse/loop/` path, so those entries never match there. That set used to be
the blanket prefix `specfuse/loop/`, which covered all 44 modules and every
shipped document — so in the driver's own repository no gate shipping
documentation could arm. It is now the named list in
`arm_eval.JUDGE_MODULES` / `JUDGE_DATA_PREFIXES`, with every unlisted module
and data entry carrying a written reason in `NON_JUDGE_MODULES` /
`NON_JUDGE_DATA_ENTRIES`. Shipped documentation under
`specfuse/loop/data/docs/` is the deliberate exclusion: no predicate reads it.

**Veto channel:** no.

**Clearing action:** normally, route the WU so it does not produce a path
under these prefixes.

**Resolved: the documentation-blocks-arming limit (open question 2).** This
class used to fire on *any* path under the `specfuse/loop/` prefix. Every
documentation file in this repository is mirrored into
`specfuse/loop/data/docs/` by the scaffold sync, so under `auto` **no gate
shipping a documentation file could arm** — the prefix test could not
distinguish a mirrored doc from a change to `arm_eval.py` itself. FEAT-2026-0053
shipped that as an accepted v1 limit whose clearing action was "the human arm,
not a code change", and recorded that narrowing the prefix "needs a decision
with evidence, not a one-line prefix edit".

That decision has since been made and the limit is gone. The prefix is replaced
by a named registry — `JUDGE_MODULES` for the driver modules a verdict reads,
`JUDGE_DATA_PREFIXES` for the package data that seeds a judge surface
downstream — with every unlisted module and data entry carrying a written
reason in `NON_JUDGE_MODULES` / `NON_JUDGE_DATA_ENTRIES`, and a registry test
that fails when a new file appears in neither. Shipped documentation is
excluded on the evidence that no predicate reads it.

The whole-surface approximation documented for `pyproject.toml` above still
stands: it is matched whole-file, because this predicate has no diff.

### 3. `decision_class_paths`

**Measures:** whether any drafted WU touches a dependency-manifest surface,
since dependency changes are a decision class that should not auto-arm. The
covered surface is a fixed table in `arm_eval.py`
(`DEPENDENCY_MANIFEST_COVERED`), matched by `fnmatch` against the produced
path's basename: `pyproject.toml`, `package.json`, `pom.xml`,
`build.gradle`, `build.gradle.kts`, `Cargo.toml`, `go.mod`, `Gemfile`,
`composer.json`, `requirements*.txt`, `*.csproj`. Verified by reading
`DEPENDENCY_MANIFEST_COVERED` directly: `python3 -c "from specfuse.loop.arm_eval
import DEPENDENCY_MANIFEST_COVERED as c; print(c)"`.

**Fires when:** a drafted WU's `produces:` list contains a path whose
basename matches one of the covered patterns above. Precedence: a covered
hit fires the class even when an undecidable path (see below) is also
present in the same WU's `produces:` list — a definite dependency hit is
never masked by a sibling the predicate cannot classify.

**`not_evaluable` triggers.** Two paths report `not_evaluable` instead of
`clean`, each fail-closed the same as `fired`:

1. **Named-uncovered manifest.** The produced path's basename matches one of
   the named-uncovered table (`DEPENDENCY_MANIFEST_NAMED_UNCOVERED`) —
   manifests the driver recognises by name but does not yet cover, each with
   a stated reason:

   | Pattern | Reason |
   | --- | --- |
   | `mix.exs` | Elixir manifest; Elixir is not yet a Specfuse target ecosystem |
   | `pubspec.yaml` | Dart/Flutter manifest; not yet a Specfuse target ecosystem |
   | `Podfile` | CocoaPods manifest; not yet a Specfuse target ecosystem |
   | `*.gemspec` | Ruby gemspec; `Gemfile` is covered above, gemspec is not yet |
   | `*.cabal` | Haskell manifest; not yet a Specfuse target ecosystem |
   | `package-lock.json` | lockfile derived from the covered `package.json`, not the dependency declaration itself; out of this feature's scope |
   | `poetry.lock` | lockfile derived from the covered `pyproject.toml`, not the dependency declaration itself; out of this feature's scope |
   | `Cargo.lock` | lockfile derived from the covered `Cargo.toml`, not the dependency declaration itself; out of this feature's scope |
   | `go.sum` | checksum file derived from the covered `go.mod`, not the dependency declaration itself; out of this feature's scope |
   | `Gemfile.lock` | lockfile derived from the covered `Gemfile`, not the dependency declaration itself; out of this feature's scope |
   | `yarn.lock` | lockfile derived from the covered `package.json`, not the dependency declaration itself; out of this feature's scope |

   Operator action: review the manifest by hand — the driver has no basis to
   call it clean or fired — and arm manually if it is not a decision-class
   change.

2. **Glob or directory in `produces:`.** A drafted WU's `produces:` entry is
   a glob or a directory (contains `*`, `?`, `[`, or ends in `/`) rather than
   a concrete file path, so the class cannot test it against the covered or
   named-uncovered tables at all. Operator action: review what the glob or
   directory actually expands to, and either narrow the WU's `produces:` to
   concrete paths or arm manually once the expansion is confirmed
   dependency-free.

**Veto channel:** no.

**Clearing action:** the operator reviews the dependency change by hand and
arms manually; there is no automatic clearance for this class by design.

**v1 limit.** Coverage is a fixed list compiled into the driver
(`DEPENDENCY_MANIFEST_COVERED` in `arm_eval.py`), not project configuration.
An ecosystem's manifest that is absent from both tables above is invisible to
this class — it reports `clean`, not `not_evaluable`, exactly as a Maven
`pom.xml` did before this table added it. Extending coverage to a new
ecosystem means shipping a driver release that edits
`DEPENDENCY_MANIFEST_COVERED` (or, as a stopgap, naming the manifest in
`DEPENDENCY_MANIFEST_NAMED_UNCOVERED` so it at least reports
`not_evaluable`); a project cannot widen this surface from its own
`.specfuse/` configuration.

### 4. `retroactive_edits`

**Measures:** whether any work unit belonging to an already-passed gate has
been altered or removed from the plan graph since that gate closed — a
retroactive rewrite of settled history.

**Fires when:** a baseline WU whose gate is `status: passed` has changed
`type`, changed `goal`, or disappeared from the current plan graph entirely.

**Veto channel:** no.

**Clearing action:** revert the retroactive edit — restore the WU's original
`type`/`goal`/presence in the plan graph. If the change was intentional,
escalate to a human to decide whether the passed gate should be reopened;
this class does not resolve by editing the predicate.

### 5. `drift_caps`

**Measures:** how much the current plan has grown past what the baseline
declared — new work units, new planned cost, and new gates added since the
baseline was captured.

**Fires when:** added WU count exceeds `DRIFT_CAP_RATIO` (0.5) times the
baseline's total WU count, added planned cost exceeds `DRIFT_CAP_RATIO` times
the baseline's total planned cost, or the number of gates added since baseline
exceeds `ADDED_GATE_CAP` (1).

**Veto channel:** no.

**Clearing action:** trim the drafted additions back under the caps, or have
the operator explicitly accept the drift and arm manually. A feature that
needs to grow past these caps routinely should have its baseline recaptured
rather than repeatedly clearing this class by hand.

### 6. `missing_provenance`

**Measures:** whether every work unit added since the baseline carries a
`provenance` field explaining where it came from.

**Fires when:** an added WU has no `provenance` field.

**Veto channel:** yes (`VETO_CLASSES`) — this class can only withhold arming,
never approve it; a clean verdict here means "nothing to veto," not "this WU
is good."

**Clearing action:** add a `provenance` field to the WU's frontmatter stating
where it came from (which decision, which prior finding, which operator
request), then re-run the arm evaluation.

### 7. `open_questions_human_only`

**Measures:** whether the successor gate's review file declares its open
questions resolved, and whether any drafted WU is flagged `human_only`.

**Fires when:** the successor gate's `GATE-NN-REVIEW.md` is missing, is
missing its `open_questions` field, or has a non-empty `open_questions` list;
or any drafted WU in that gate has `human_only: true`.

**Veto channel:** yes.

**Clearing action:** write the missing review file (or add the
`open_questions` field), resolve and clear every open question to an empty
list, and remove `human_only: true` from any WU that no longer needs a human.
A WU that genuinely requires a human stays `human_only: true` and this class
stays fired by design — the clearing action is a human arm, not an edit.

### 8. `plan_next_lint`

**Measures:** whether the drafted successor gate passes the plan-next
contract lint (`lint_plan_next_draft`) — the same structural checks the
`plan-next` skill enforces on a human-authored draft.

**Fires when:** the lint reports any finding, or the lint itself raises an
exception (a malformed frontmatter degrades to a fired verdict rather than
crashing the gate close).

**Veto channel:** yes.

**Clearing action:** fix each lint finding in the drafted gate's WU files
(malformed frontmatter, missing required fields, whatever the lint names),
then re-run the arm evaluation. An exception from the lint itself is an
escalation — read the exception message, fix the file that caused it.

## The v1 constants

These are hardcoded in `arm_eval.py` for v1; there is no per-feature or
per-project override yet. Tuning them is expected to graduate to
`agent-policy.yml` ([FEAT-2026-0044](../../.specfuse/roadmap.md)) as a
**tighten-only** knob — a project may lower these caps, never raise them.

| Constant | Value | Used by |
| --- | --- | --- |
| `BUDGET_PROJECTION_MULTIPLIER` | `2.0` | class 1, `budget_projection` |
| `DRIFT_CAP_RATIO` | `0.5` | class 5, `drift_caps` |
| `ADDED_GATE_CAP` | `1` | class 5, `drift_caps` |
| `JUDGE_PATHS` | `.specfuse/verification.yml`, `.specfuse/hooks/`, `.specfuse/rules/`, `.github/workflows/`, `pyproject.toml`, plus `JUDGE_MODULES` and `JUDGE_DATA_PREFIXES` (driver-source repository only) | class 2, `judge_editing` |
| `JUDGE_MODULES` | the 20 modules under `specfuse/loop/` a merge/arm/close verdict reads; every other module is registered in `NON_JUDGE_MODULES` with a reason | class 2, `judge_editing` |
| `JUDGE_DATA_PREFIXES` | `specfuse/loop/data/` subtrees seeding a judge surface downstream: `rules/`, `rules-local/`, `schemas/`, `templates/`, `workflows/`, `verification.yml.example` | class 2, `judge_editing` |

## Reading an `arm_predicate_evaluated` event

Every gate close appends one `arm_predicate_evaluated` event to
`events.jsonl`, carrying the full per-class verdict map and a `gate` field.

**What the `gate` field means:** the predicate was evaluated at a flip
involving gate N — one of the three flip sites in the driver (the normal
gate-close path, the operator re-arm path, or an escalation halt) fired the
evaluation while gate N was the gate under consideration.

**What it does not mean:** that gate N closed and would not arm gate N+1. The
event payload does not record which of the three flip sites emitted it, and
an escalation halt can fire the same event shape as a normal close.

This is a known trap, documented in `RETROSPECTIVE.md`'s gate-2 Findings §2:
the first live `arm_predicate_evaluated` event on this feature was emitted
from an *escalation* flip site — a `preexisting_gate_failure` halt at gate-2
entry — for a gate that had dispatched zero work units. Its payload read
`gate: 2`, with `open_questions_human_only` fired on `GATE-03-REVIEW.md
missing`. Read literally by gate number, that payload looks like "gate 2
closed and gate 3 would not arm." What it actually recorded was "the
predicate was evaluated at a flip involving gate 2," triggered by an
escalation before gate 2 had done any work. A consumer that groups these
events by gate number alone will misdiagnose which of the three flip sites
produced a given event — check the event's surrounding context (what halted,
what path invoked the evaluation) before drawing a conclusion from `gate`
alone.

## Observed on real input

Measured 2026-08-03 by `python3 .specfuse/scripts/arm_sweep_gate.py`, which sweeps
every feature folder under `.specfuse/features/` that carries a
`PLAN.baseline.json` and records which verdict branches `evaluate_arm_predicate`
has actually returned. Re-run that command to regenerate this table; its output
is the source of the rows below, not a hand-transcribed copy.

| Class | Observed on real input |
| --- | --- |
| `budget_projection` | `clean` only — **unverified**: never `fired`, never `not_evaluable` |
| `decision_class_paths` | `clean` only — **unverified**: never `fired`, never `not_evaluable` |
| `drift_caps` | `clean` only — **unverified**: never `fired`, never `not_evaluable` |
| `missing_provenance` | `clean` only — **unverified**: never `fired`, never `not_evaluable` |
| `plan_next_lint` | `clean` only — **unverified**: never `fired`, never `not_evaluable` |
| `judge_editing` | `clean`, `fired` — never `not_evaluable` |
| `retroactive_edits` | `clean`, `fired` — never `not_evaluable` |
| `open_questions_human_only` | `clean`, `fired` — never `not_evaluable` |

At measurement time, 5 of 5 evaluable features swept clean with no
`not_evaluable` verdicts; 42 features were excluded for predating
`PLAN.baseline.json` and cannot be evaluated at all. Every `fired` observation
in the corpus so far traces back to a single feature, FEAT-2026-0053.

Five of the eight classes above are marked **unverified**: they have never
fired on real input, and `not_evaluable` — the fail-closed path — has never
been observed for *any* class outside fixtures. A class reporting `clean` on
every real input to date is not the same as a class known to work; it means
this branch has not yet met an input that should trip it. This is not
evidence the branch is broken, and it is not evidence it works — it is an
honest gap. Do not read the all-`clean` rows as reassurance.

The sample is small — five evaluable features as of this writing — and grows
by one each time a new feature is baselined, with no additional work required
to keep it current. Re-run the command above to see the current counts.
