# Retrospective — FEAT-2026-0110, language-aware narrow test selection

Single gate, three substantive work units, one terminal close. The feature makes
the per-attempt `tests`-gate selector configurable through an optional
`narrow_selection` block on a `code` gate, so a project whose tests are not
Python files under `tests/` can narrow its per-attempt run instead of paying the
full suite on every attempt.

## Measurements

Every command below was run fresh in this close session, in the repository root,
against the working tree as this close found it. Exit codes are read directly
from the shell, not inferred from output text.

### feature_oracle: PASS

`GATE-01.md` declares `feature_oracle: "python3 -m unittest tests.test_language_aware_narrow_selection -v"`.

```
$ python3 -m unittest tests.test_language_aware_narrow_selection -v
test_gradle_shape_uses_item_template_for_repeated_flag ... ok
test_maven_shape_resolves_through_narrow_command ... ok
test_no_narrow_selection_key_is_byte_identical_to_today ... ok
test_path_format_renders_entries_verbatim ... ok
test_unknown_format_is_a_configuration_error_naming_the_gate ... ok
Ran 5 tests in 0.032s
OK
exit 0
```

### The three shapes, as literal resolved commands

The gate's definition of done is not "the tests pass" — it is that a unit whose
`produces:` names tests outside `tests/` resolves to a narrow command its own
runner accepts. What follows is the literal output of calling
`loop.resolve_narrow_command(gate, wu)` in a fresh Python process against the
working tree, printed with `repr()` so whitespace is visible. This is the
feature's actual product, not a restatement of an assertion.

| shape | `produces:` | `narrow_selection` | resolved command |
|---|---|---|---|
| Maven | `src/test/java/com/acme/FooTest.java`, `src/test/java/com/acme/BarTest.java` | `test_roots: ["src/test/java/"]`, `format: class_name`, `separator: ","` | `./mvnw test -Dtest=FooTest,BarTest` |
| Gradle | same two paths | `test_roots: ["src/test/java/"]`, `format: class_name`, `item_template: "--tests {module}"`, `separator: " "` | `./gradlew test --tests FooTest --tests BarTest` |
| JS | `__tests__/foo.test.js`, `__tests__/bar.test.js` | `test_roots: ["__tests__/"]`, `format: path` | `jest __tests__/foo.test.js __tests__/bar.test.js` |
| none declared | `tests/test_declared.py` | (absent) | `python3 -m unittest tests.test_declared` |

Raw session output:

```
$ python3 -c '<construct each WorkUnit + gate, call loop.resolve_narrow_command, print repr>'
Maven (class_name + comma separator)
  -> './mvnw test -Dtest=FooTest,BarTest'
Gradle (item_template repeated flag)
  -> './gradlew test --tests FooTest --tests BarTest'
JS (format: path)
  -> 'jest __tests__/foo.test.js __tests__/bar.test.js'
No narrow_selection declared (today's behaviour)
  -> 'python3 -m unittest tests.test_declared'
exit 0
```

The fourth row is the load-bearing one: `GATE-01.md`'s absent-key table claims a
`verification.yml` declaring no `narrow_selection` behaves byte-for-byte as it
did before this feature existed. The resolved string is
`python3 -m unittest tests.test_declared` — the same dotted module name the
pre-feature `_test_module_name` produced.

### The refusal, as a literal message

An unknown `format` is a `CONFIGURATION ERROR`, not a silent fallback to the
gate's full `command`. Observed by calling `loop.verify()` with an injected
config declaring `format: typo_format`:

```
ok=False
report="CONFIGURATION ERROR: gate 'tests' declares `narrow_selection.format: 'typo_format'` which is not one of ['class_name', 'path', 'python_module'] in .specfuse/verification.yml. This is not a work-unit failure — fix verification.yml and re-run."
```

The message names both `.specfuse/verification.yml` and the offending gate's
`name`, which is what T02's criterion 3 asked for. This is a negative
observation: a purpose-built bad input seen being rejected, not a reading of the
source.

### Fresh oracle re-runs, per acceptance criterion

Twelve criteria across T01/T02/T03. All twelve required re-verification this
attempt (nothing carried forward — this is the gate's first close). Per-criterion
oracle, kind, and state are recorded in `GATE-01-CRITERIA.md`; the commands and
exit codes are:

| oracle | exit | criteria it proves |
|---|---|---|
| `python3 -m unittest tests.test_language_aware_narrow_selection -v` | 0 (5 tests) | T01#1, T02#4 |
| `...LanguageAwareNarrowSelectionTests.test_maven_shape_resolves_through_narrow_command -v` | 0 | T01#2 |
| `...test_gradle_shape_uses_item_template_for_repeated_flag -v` | 0 | T02#1 |
| `...test_path_format_renders_entries_verbatim -v` | 0 | T02#2 |
| `...test_unknown_format_is_a_configuration_error_naming_the_gate -v` | 0 | T02#3 |
| `...test_no_narrow_selection_key_is_byte_identical_to_today -v` | 0 | T01#3 (unit half) |
| `python3 -m unittest tests.test_tiered_verification_e2e -v` | 0 (5 tests) | T01#3, T02#4 (regression half) |
| `grep -n "narrow_selection" specfuse/loop/loop.py` | 0 (11 hits) | T01#4 |
| `grep -c "narrow_selection" .specfuse/verification.yml` | 1, printed `0` | T01#4 |
| `grep -c "narrow_selection" .specfuse/verification.yml.example` | 0, printed `3` | T03#1 |
| `grep -n "tests/ path" specfuse/loop/loop.py` | 1, no output | T03#2 |
| `diff .specfuse/verification.yml.example specfuse/loop/data/verification.yml.example` | 0 | T03#3 |
| `python3 -m unittest tests.test_scaffold_data_in_sync -v` | 0 (4 tests) | T03#4 |

Two of those exit codes are non-zero *by design* and read as passes:
`grep -c` returning 1 on `.specfuse/verification.yml` is the criterion's own
assertion that this repo's live gate set declares no `narrow_selection`
(`[FEAT-2026-0019/G1]`'s hazard, avoided), and `grep -n "tests/ path"` returning
1 with no output is T03#2's assertion that the removed prompt sentence is gone.

### One environment artifact, named so it is not mistaken for a defect

`python3 -m unittest tests.test_tiered_verification_e2e -v` fails with 5 errors
inside this session's default sandbox and passes with exit 0 outside it. The
error is `PermissionError: [Errno 1] Operation not permitted:
'/Users/<redacted>/.claude/session-env/.specfuse-preflight-probe-...'`, raised by
`require_session_env_writable` — the driver's own pre-flight probe, which the
sandbox's write deny-list covers. The recorded exit code above (0) is the
unsandboxed run. Nothing in this feature touches that path; the module is red
under the sandbox on any tree.

### Per-criterion state

`GATE-01-CRITERIA.md` records all twelve criteria as `state: pass`,
`kind: narrow`, `attempt: 1`. Every criterion in this gate has a knowable scope —
a scoped test nodeid, a countable grep, or a `diff` — so none is classified
`broad`. The gate's `feature_oracle` re-runs on every close attempt regardless of
that classification, per `close-discipline.md` §1.

The gate's own once-per-gate broad run is recorded in `GATE-01.md`'s
`broad_run:` block: `ok: true`, `failing: []`, `ran_at: 2026-09-10T00:47:07Z`.
That run is the driver's and was not re-executed in this session.

## Retrospective

Three units, three passing first attempts, no re-arms, no blocked units, no
driver halts. That is the least eventful gate in this repository's recent
history, and the reason is a planning decision rather than luck: every key the
feature adds is optional and every default was chosen to reproduce the previous
behaviour byte-for-byte, so no unit had to edit `.specfuse/verification.yml` and
every unit kept a working exit oracle. `PLAN.md` names that explicitly as
avoidance of `[FEAT-2026-0019/G1]` — a feature that migrates the verification
harness the driver itself runs cannot be decomposed into separately-gated WUs.
The avoidance held.

The one thing this gate got wrong was the enumeration of documentation surfaces.
T03 was scoped from `PLAN.md`'s list of three: `.specfuse/verification.yml.example`,
the dispatched-session prompt text in `loop.py`, and
`.specfuse/rules/verification-discipline.md` (correctly escalated rather than
edited, since it is vendored from the methodology core). The list was written
from memory and missed `plugins/specfuse/skills/verification/SKILL.md`, the
verification skill every dispatched session is pointed at, which stated the old
`tests/`-and-dotted-module rule as universal in two places. This close fixed it
in the canonical plugin copy and re-vendored via `bash scripts/sync-scaffold.sh`
(`.specfuse/skills/` is a derived copy; `plugins/` is canonical, and the two are
byte-identical again). The durable version of that lesson is in `LEARNINGS.md`.

### Contract surface gate 1 changed

Enumerated for the section below, which is the reviewed claim.

## Consumer-visible contract changes

Four additive keys and one new refusal. All are optional; a `verification.yml`
that declares none of them resolves exactly as it did before this feature
existed, so no existing project file needs an edit.

1. **`narrow_selection.test_roots`** (list of path prefixes, default
   `["tests/"]`) on a `code:` gate. Which `produces:` entries the per-attempt
   selection keeps. Replaces the hard-coded `p.startswith("tests/")`.
2. **`narrow_selection.format`** (default `python_module`; also `class_name` and
   `path`). How a selected path is rendered: dotted Python module name, bare
   file stem (`FooTest.java` → `FooTest`, what a JVM runner's `-Dtest=` wants),
   or the path verbatim.
3. **`narrow_selection.item_template`** (default `"{module}"`). Rendered per
   selected test, which is what expresses a *repeated* flag
   (`--tests A --tests B`) that no join character can produce.
4. **`narrow_selection.separator`** (default `" "`). How the rendered items are
   joined into `{selected_test_modules}`.
5. **A `format` value outside `{python_module, class_name, path}` is now a
   `CONFIGURATION ERROR`** naming `.specfuse/verification.yml` and the offending
   gate, refused before any gate runs. Previously no such value existed. This is
   the only way a project can newly go red without editing anything — and only
   if it declares the new key with a typo.

Documentation surfaces updated to match: `.specfuse/verification.yml.example`
(and its packaged copy under `specfuse/loop/data/`), the dispatched-session
prompt text in `loop.py`, and the `verification` skill.

## Cost analysis

`PLAN.md` frontmatter names `planned_cost_usd: 15.00`, which is the exact sum of
the four work units' own `planned_cost_usd` (T01 $4.00, T02 $3.50, T03 $2.50,
G1-CLOSE $5.00). No discrepancy to reconcile between the two figures.

Actuals below are read from this feature's `events.jsonl` `attempt_outcome`
payloads — every attempt, not the WU frontmatter, which carries only the last
attempt's cost. Every `done` unit has exactly one `attempt_outcome`, all with
`outcome: passed`.

| WU | Planned | Actual | Delta | Attempts | Wall clock |
|---|---|---|---|---|---|
| T01 walking skeleton (config + `class_name`) | $4.00 | $0.747519 | −$3.2525 (−81.3%) | 1, passed | 160.1s |
| T02 formats + refusal | $3.50 | $0.773930 | −$2.7261 (−77.9%) | 1, passed | 142.9s |
| T03 document the contract | $2.50 | $0.733010 | −$1.7670 (−70.7%) | 1, passed | 460.7s |
| **substantive subtotal** | **$10.00** | **$2.254459** | **−$7.7455 (−77.5%)** | 3 attempts, 0 re-arms | 763.8s (12m44s) |
| G1-CLOSE (this attempt) | $5.00 | not yet recorded | — | 1, in flight | — |
| **feature total so far** | **$15.00** | **$2.254459** | **−$12.7455** | this attempt not yet priced | — |

**The delta, named.** Every substantive unit came in between 70% and 82% under
its estimate, and the subtotal is 77.5% under. The estimates were not
recalibrated for this feature's shape: three units that each add an optional key
with a behaviour-preserving default, against a plan that had already done the
design work (the four-key split, the absent-key table, the existing-mechanism
search) before the first dispatch. T03 cost the least per dollar planned and took
by far the most wall clock (460.7s, 60% of the gate's substantive time) — it ran
`sync-scaffold.sh` and its guards, which is I/O time, not model time.

**Restart count: 3, none halting.** Three `driver_staleness_detected` events, one
after each unit, all carrying `reason: driver_restart_required` and
`halted: false` with a `next_pin_tree` — the non-halting pinned-run shape
FEAT-2026-0109 added. Each of T01, T02 and T03 edited `specfuse/loop/loop.py`, so
three is exactly the predictable count. No unit's attempts were consumed by them.

**Re-arm count: 0.** No `re_arm_dispatched` event, and no `re_arm_count` in any
WU's frontmatter.

### Failure-class breakdown

(no non-passing attempts in scope)

## What the loop did NOT verify

Three claims this gate makes or touches that its own machinery could not settle,
each with the criterion, the reason, and where it actually gets checked.

1. **That the changed-file half of the selection honours the new
   `test_roots`.** Criterion: none — `PLAN.md`'s scope boundary puts it
   explicitly OUT. Reason: `select_tests_for_changed_files` ships behind
   `CHANGED_FILE_SELECTION_ENABLED = False` and nothing writes
   `.specfuse-changed-file-test-map.json`, so code keyed on `test_roots` there
   could not be exercised end to end; an acceptance criterion for it would have
   had to be asserted against a mechanism that never runs. It remains
   `tests/`-shaped. Where it gets checked: whoever flips that constant. The
   contract they inherit is recorded in `PLAN.md` § *Scope boundary — explicitly
   OUT*: **the map must key on the same `test_roots` this feature adds**, or a
   non-Python project will narrow on its declared half and silently fall back on
   its changed-file half — the exact half-narrowing this feature exists to
   remove.
2. **That narrowing recovers the 8–11 minutes per attempt #3281 measured.**
   Criterion: none in this gate — `PLAN.md` puts it OUT. Reason: the figure was
   measured in one Maven consumer's repository, from that repo's `events.jsonl`
   across ~47 full-suite runs per feature. Re-measuring it needs that consumer's
   repo, its toolchain and a feature's worth of attempts; nothing in this
   repository can produce the number, and a fixture cannot. Where it gets
   checked: post-merge, in that consumer, once it declares `narrow_selection` on
   its `tests` gate. Filed as a `## Post-merge checklist` entry in `PLAN.md`,
   which the driver files as one `specfuse:post-merge` issue at close — not as
   an acceptance criterion, per `close-discipline.md` §2.
3. **That the three resolved commands are accepted by the runners they name.**
   Criterion: T01#2, T02#1, T02#2 assert the resolved *string*, and that is all
   they assert. Reason: no `mvnw`, `gradlew` or `jest` is invoked anywhere in
   this feature — the fixtures are Python dicts and `WorkUnit` objects, and this
   repository has no JVM or Node toolchain to run them against. `-Dtest=A,B`,
   `--tests A --tests B` and a bare path list are the documented invocations for
   those runners, but this gate verified string equality, not runner acceptance.
   Where it gets checked: the first consumer to declare the block. This is the
   same post-merge observation as bullet 2 and rides the same checklist entry.

## Lessons

Two promoted to `.specfuse/LEARNINGS.md`; both are recorded there in full and
summarised here.

1. **A documentation surface list written from memory misses the surfaces that
   state the old rule in their own words.** T03's three-surface list came from
   `PLAN.md`; the verification skill — the one document every dispatched session
   is pointed at — was not on it and stated the superseded rule twice. The new
   key cannot be grepped for at drafting time because it does not exist yet; the
   *behaviour being replaced* can.
2. **An optional key whose absent-key default reproduces current behaviour
   byte-for-byte is what lets a harness-migrating feature be decomposed at all.**
   This is the reusable escape from `[FEAT-2026-0019/G1]`, and this gate is its
   clean demonstration: three units, three first-attempt passes, no edit to the
   live `verification.yml`.

## Verdict

Recorded in this work unit's `verdict:` frontmatter field. It is advisory: this
is the feature's terminal gate, so the verdict that advances the feature is
written by a fresh judge session reading `## Measurements`, the gate's definition
of done, `GATE-01-CRITERIA.md` and the gate's diff — not this section, which is
stripped from the judge's evidence before it sees it.
