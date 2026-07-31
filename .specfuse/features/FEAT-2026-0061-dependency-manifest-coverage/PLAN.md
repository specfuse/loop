---
feature_id: FEAT-2026-0061
title: Dependency-manifest coverage for non-Python ecosystems in decision_class_paths
slug: dependency-manifest-coverage
branch: feat/FEAT-2026-0061-dependency-manifest-coverage
roadmap_goal: Extend the arm predicate's dependency-manifest surface to the ecosystems Specfuse targets, stated in one place, so the decision_class_paths stop class stops reporting `clean` in repositories whose build files it cannot read.
autonomy_default: review
status: active
planned_cost_usd: 11.50
---

# Plan: Dependency-manifest coverage for `decision_class_paths`

`decision_class_paths` is one of the eight arm-predicate stop classes shipped by
FEAT-2026-0053. Its job is to stop an `auto` feature before it adds a dependency
without a human seeing it. It recognises exactly three manifest shapes —
`_DEPENDENCY_MANIFEST_EXACT` matches `pyproject.toml` and `package.json`, and
`_REQUIREMENTS_RE` matches `requirements*.txt` (`arm_eval.py:62-63`). Every other
ecosystem is invisible.

Found while scoping the first `auto` ride against the Specfuse Generator, which is
a Maven repository: a work unit there adding a Java dependency to `pom.xml` arms
without stopping, and the class reports `clean` while doing it. That is a **false
negative, not a visible gap** — the operator reading the arm record sees a verdict
that looks like coverage. `build.gradle`, `build.gradle.kts`, `Cargo.toml`,
`go.mod`, `Gemfile`, `*.csproj`, and `composer.json` are all in the same position.
The class is at its least trustworthy exactly where its value is highest, because a
repository whose manifests it cannot read is a repository where it silently never
fires.

## The two decisions this feature was chartered to make

The roadmap deferred both to this feature. Both are settled here, before drafting.

**Fixed list, not a declared surface.** Coverage is a table in `arm_eval.py`, not a
key a target project declares in `.specfuse/verification.yml`. `arm_eval` reads
**nothing** outside `feature_dir` today — its only imports are `_miniyaml`,
`closing_requirements`, and `plan_baseline`. A declared surface would couple the
predicate to project layout for the first time and add a new failure mode (absent
or malformed config) to a class whose entire defect is reporting a status it cannot
justify. The polyglot monorepo the declared surface would serve is a future
meeting, not a present one; the fixed list ships correct for every target on day
one with nothing for an operator to configure.

**`not_evaluable` has two triggers, and the second is the load-bearing one.** A
class that cannot evaluate its input must report `not_evaluable` — which the
predicate already treats as fail-closed — rather than `clean`.

1. **A named-uncovered manifest.** An explicit list of manifests we know exist and
   deliberately do not cover. This trigger is only as good as its rationale, and
   T01's acceptance forces one per entry: an entry that cannot justify being
   uncovered gets covered instead. The list may legitimately empty out.
2. **A glob or directory in `produces:`.** The WU contract explicitly permits a
   glob (`.specfuse/templates/WU.template.md`: *"a glob needs ≥1 existing non-empty
   match"*). The class cannot decide whether a dependency manifest falls inside
   `src/**` or a bare `config/`, so reporting `clean` there is the same false
   negative in a different costume. This trigger is principled rather than guessed,
   and it keeps the `not_evaluable` branch live even if trigger 1 empties.

**Precedence:** a covered hit `fired`s. `not_evaluable` only applies when nothing
covered matched — a definite dependency change must never be masked by an
undecidable sibling path in the same WU.

Alongside both, the `clean` reason string becomes self-describing: it names the
coverage scope the verdict was made against, so an operator reading an arm record
sees what `clean` actually meant.

## Scope boundary

**IN.** The recognition table in `arm_eval.py`, the two `not_evaluable` triggers,
the self-describing `clean` reason, their tests, and the coverage documentation in
`docs/concepts/autonomy-stop-classes.md` §3 plus its `specfuse/loop/data/docs/`
mirror.

**OUT — the `pyproject.toml` double-fire.** A produced `pyproject.toml` fires both
`judge_editing` and `decision_class_paths`. That is an accepted v1 approximation,
already documented at `arm_eval.py:47-50`. This feature does not relitigate it.

**OUT — any read outside `feature_dir`.** No repo-ecosystem probe, no
`verification.yml` key. Both were considered and declined above. A repo probe would
additionally report `not_evaluable` on *every* gate in an uncovered repository,
blocking all auto arming rather than dependency-touching work — bluntness the
`LEARNINGS FEAT-2026-0053/G1-CLOSE` entry warns about directly.

**OUT — the other seven stop classes**, and FEAT-2026-0062's cost-read blindness.
That is its own roadmap row.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep commands run:**
  `grep -rniE "pom\.xml|build\.gradle|Cargo\.toml|go\.mod|Gemfile|csproj|composer\.json" specfuse/ .specfuse/scripts/ tests/`
  and `grep -rn "manifest" specfuse/loop/*.py`
- **Verdict:** `no existing mechanism, extending arm_eval.py's two module-private constants`

The first returns nothing outside the mirrored `specfuse/loop/data/docs/` tree — no
module anywhere in the package recognises a non-Python, non-JavaScript build file.
The second returns only `scaffold.py`'s `.scaffold-manifest`, which is the
scaffold-sync ownership record and unrelated to dependency manifests; its
docstring (`scaffold.py:77`) describes it as *"the ownership record: a versioned-dir
file is provably…"*, confirming a different concern. There is nothing to reuse.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

This feature adds a fail-closed branch to a predicate, so the check applies.

- **What does the rule report on an input already in its intended final state?**
  **Zero.** A work unit producing literal source paths reports `clean` under both
  triggers.

Measured rather than asserted: **0 of 169** unique `produces:` entries across every
WU in `.specfuse/features/` contains a glob character or a trailing slash, so
trigger 2 reports zero on the entire real corpus as it stands. Trigger 1 reports
zero unless a WU literally produces one of the named-uncovered manifests. The
widened covered table only converts existing `clean` verdicts to `fired` on paths
that genuinely are dependency manifests — it cannot fire on an ordinary path.

**The residual risk is the opposite one**, and T01's acceptance carries it: a
covered-table entry so broad it fires on ordinary files. `*.csproj` is the only
pattern-matched entry beyond the pre-existing `requirements*.txt`, and it is
narrow.

## Task graph

```yaml
# Single terminal gate: 2 substantive WUs, under the ceremony proportionality
# threshold of 4 (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0061/T01
        file: WU-01-manifest-recognition-surface.md
        depends_on: []
      - id: FEAT-2026-0061/T02
        file: WU-02-stop-class-doc-coverage.md
        depends_on: [FEAT-2026-0061/T01]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0061/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0061/T01
          - FEAT-2026-0061/T02
```

T02 depends on T01 so the documentation describes shipped behaviour rather than
intended behaviour — the coverage list in the doc must be read off the code, not
written in parallel with it.

## Notes

- **Lockfiles are an open question T01 must answer explicitly, not silently.**
  `package-lock.json`, `poetry.lock`, `Cargo.lock`, `go.sum`, `Gemfile.lock`, and
  `yarn.lock` are dependency changes by any reasonable reading, but they were not
  part of the scope this feature was chartered with. T01's acceptance requires the
  covered table to state its treatment of them either way — covered, or
  named-uncovered with a written reason. What it must not do is leave them
  undiscussed, which is how the original three-shape list became a false negative
  in the first place.
- **T02 is `type: implementation`, not `type: docs`.** `docs` is a closing type
  that routes to the `doc` gate set; this WU's edit must run under the `code` gate
  set so `tests/test_scaffold_data_in_sync.py` verifies the
  `specfuse/loop/data/docs/` mirror. A documentation deliverable that ships as part
  of the feature is substantive work, not closing ceremony.
- **`autonomy_default: review` is structural, not a preference.**
  `specfuse/loop/` is a `JUDGE_PATHS` prefix (`arm_eval.py:57`), so every gate of
  this feature fires `judge_editing` and `auto` is unreachable by construction.
- This feature modifies the arm predicate that would evaluate its own successor
  gates. Gate 1 is terminal, so there is no successor gate to evaluate and no
  bootstrap problem — but the close should note the shape, because the next feature
  to touch `arm_eval.py` in a multi-gate shape will have one.
