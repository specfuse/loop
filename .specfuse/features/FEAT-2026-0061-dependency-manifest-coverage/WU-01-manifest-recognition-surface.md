---
id: FEAT-2026-0061/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
produces:
  - specfuse/loop/arm_eval.py
  - tests/test_arm_eval.py
produces_driver_helper:
  - _matches_dependency_manifest
oracle_env: macos_local
---

# One stated recognition surface, two `not_evaluable` triggers, a self-describing `clean`

**Objective.** Replace `arm_eval.py`'s two module-private constants with a single
stated recognition table covering the ecosystems Specfuse targets; make
`decision_class_paths` report `not_evaluable` on inputs it cannot decide instead of
`clean`; and make the `clean` reason name the coverage scope it was decided against.

**Context.** Correlation ID `FEAT-2026-0061/T01`. The surface today is three lines:

```python
_DEPENDENCY_MANIFEST_EXACT = ("pyproject.toml", "package.json")
_REQUIREMENTS_RE = re.compile(r"(^|/)requirements[^/]*\.txt$")
```

consumed by `_matches_dependency_manifest` (`arm_eval.py:138`) and used at exactly
one call site, the class-3 block at `arm_eval.py:249-258`. A WU producing `pom.xml`
reports `clean` today — a false negative, which is the worst failure shape a stop
class has, because the operator reading the arm record sees what looks like
coverage.

Read `PLAN.md` for the two decisions this WU implements and why the alternatives
were declined. Do not reopen them: coverage is a fixed list in this module, and the
predicate reads nothing outside `feature_dir`.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

## The three-way verdict, and its precedence

`_matches_dependency_manifest` returns a bool today. It becomes tri-state —
`covered` / `undecidable` / `no` — and the class-3 block resolves in this order:

1. **Any covered hit → `fired`.** Unchanged behaviour, wider table.
2. **Else any undecidable path → `not_evaluable`.**
3. **Else `clean`**, with the coverage scope named in the reason string.

Precedence matters and is easy to get backwards: a definite dependency hit must
never be masked by an undecidable sibling path in the same work unit. A WU
producing both `pom.xml` and `src/**` fires; it does not report `not_evaluable`.

## Covered

Exact basename match (`path == p or path.endswith("/" + p)`), extending the
existing two: `pyproject.toml`, `package.json`, `pom.xml`, `build.gradle`,
`build.gradle.kts`, `Cargo.toml`, `go.mod`, `Gemfile`, `composer.json`.

Pattern match, extending the existing `requirements*.txt`: `*.csproj`.

## Undecidable — trigger 2, the load-bearing one

A `produces:` entry containing a glob character (`*`, `?`, `[`) or ending in `/`.
The WU contract permits globs — `.specfuse/templates/WU.template.md` states *"a
glob needs ≥1 existing non-empty match"* — and the class cannot know whether a
manifest falls inside `src/**` or a bare `config/`. Reporting `clean` there is the
same false negative in a different costume.

This trigger reports zero on the current corpus (0 of 169 unique `produces:`
entries use either form), so it is fail-closed without being unsatisfiable.

## Undecidable — trigger 1, which must earn itself

A named list of manifests we know exist and deliberately do not cover, seeded with
`mix.exs`, `pubspec.yaml`, `Podfile`, `*.gemspec`, `*.cabal`.

**This list is only as good as its rationale, and the acceptance below forces one
per entry.** "We know this manifest exists but won't cover it" invites the obvious
question *why not just cover it* — and if the honest answer for an entry is "we
should", that entry belongs in the covered table instead. **The list may
legitimately end up empty**, and that is a correct outcome, not a failure: trigger
2 keeps the `not_evaluable` branch live either way. Do not pad the list to justify
the branch.

## Lockfiles — state the treatment, do not leave it silent

`package-lock.json`, `poetry.lock`, `Cargo.lock`, `go.sum`, `Gemfile.lock`, and
`yarn.lock` are dependency changes by any reasonable reading, but they were not part
of this feature's chartered scope. Decide explicitly and record the decision in a
comment beside the table — covered, or named-uncovered with a written reason.
Leaving them undiscussed is exactly how the original three-shape list became a false
negative.

**Acceptance criteria.**

1. `tests/test_arm_eval.py::ArmEvalTest::test_decision_class_paths_fires_on_maven_manifest`
   exists and **fails on HEAD before this WU runs** — a WU producing `pom.xml`
   reports `clean` today, so the test is red on the current tree.
2. That same test passes after this WU's edits, and
   `python3 -m unittest tests.test_arm_eval -v` exits zero.
3. The recognition surface is stated in **one place** — a single table or mapping
   with the covered and named-uncovered sets adjacent and commented — not spread
   across two module-private constants and a regex. `grep -n
   "_DEPENDENCY_MANIFEST_EXACT" specfuse/loop/arm_eval.py` reflects the new shape.
4. A test asserts `fired` for each covered exact-match manifest: `pom.xml`,
   `build.gradle`, `build.gradle.kts`, `Cargo.toml`, `go.mod`, `Gemfile`,
   `composer.json`, plus the two pre-existing `pyproject.toml` and `package.json`.
5. A test asserts `fired` for each covered pattern: a `*.csproj` path and the
   pre-existing `requirements*.txt`, including a nested form (`sub/dir/App.csproj`).
6. A test asserts `not_evaluable` for a `produces:` entry with a glob (`src/**`) and
   for one with a trailing slash (`config/`).
7. A test asserts the **precedence** rule directly: a WU producing both `pom.xml`
   and `src/**` reports `fired`, not `not_evaluable`.
8. A test asserts an ordinary source path (`specfuse/loop/foo.py`) still reports
   `clean` — the satisfiability guarantee from `PLAN.md`, held as a test rather than
   a claim.
9. The `clean` reason string names the coverage scope the verdict was decided
   against, and a test asserts the reason is non-empty and mentions at least one
   covered manifest name. The existing bare string `"no drafted WU touches
   dependency manifests"` is replaced.
10. The `not_evaluable` reason string names **which** produced path could not be
    decided and under which trigger, so the operator can act on it without reading
    the source.
11. Every entry remaining in the named-uncovered list carries a written reason, in
    a comment or a mapping value, for why it is not simply covered. A test asserts
    each entry has a non-empty reason. An empty list satisfies this criterion.
12. The lockfile treatment is stated explicitly in a comment beside the table, per
    the section above.
13. The pre-existing tests `test_decision_class_paths_fires_on_dependency_manifest`
    and `test_decision_class_paths_stays_clean_on_ordinary_path` still pass
    unmodified, or their modification is justified inline.
14. A tree-wide sanity sweep is run and its counts recorded in the result:
    `evaluate_arm_predicate` over the real feature corpus produces **no new
    `not_evaluable` verdict on `decision_class_paths`** attributable to this
    change — consistent with the 0-of-169 measurement in `PLAN.md`.
15. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
    `leak-scan`.

**Do not touch.** `JUDGE_PATHS` and the `judge_editing` class — the `pyproject.toml`
double-fire is an accepted v1 approximation documented at `arm_eval.py:47-50` and is
explicitly out of scope. The other seven stop classes. `CLASS_NAMES`, `VETO_CLASSES`,
and the `ArmDecision` / `ClassVerdict` dataclass shapes — this WU changes what class
3 decides, not the envelope it decides into. `docs/concepts/autonomy-stop-classes.md`
— T02 owns it. Anything reading outside `feature_dir`. Generated directories,
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Plus the scoped red/green run in
criteria 1–2 and the corpus sweep in criterion 14.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
red test in criterion 1 **passes** on HEAD, which would mean `pom.xml` is already
recognised and this feature's premise is wrong — report that rather than
manufacturing a different red test; the corpus sweep in criterion 14 produces new
`not_evaluable` verdicts, which would mean the glob trigger is broader than the
0-of-169 measurement predicted and the predicate is closer to unsatisfiable than
`PLAN.md` claims; or making the verdict tri-state requires changing `ClassVerdict`
or `CLASS_NAMES`, which is a contract change beyond this WU's scope. If
`specfuse/loop/arm_eval.py` is absent from the files you edited, emit `status:
blocked` — do not claim complete.
