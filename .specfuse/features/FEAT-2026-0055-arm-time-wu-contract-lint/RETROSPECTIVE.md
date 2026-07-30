# RETROSPECTIVE — FEAT-2026-0055, arm-time WU contract lint

**Verdict: `not_met`.**

The gate-1 close re-ran every oracle fresh and executed each shipped rule against a
purpose-built fixture. Three of the four work units hold up. The fourth —
`check_produces_boundary`, the ERROR leg and the reason this feature exists — is
**inverted against the canonical work-unit body shape**: it is blind to the boundary line
every real WU actually writes, and it fires false ERRORs on lines that are not boundaries.
The satisfiability sweep the gate's definition of done requires to report *zero* ERRORs across
the existing tree reports **15 ERRORs across 4 features, all false positives**.

The gate's escalation trigger names this outcome explicitly: *"If the satisfiability sweep
ERRORs on any existing feature, that is the feature's core defect: `not_met`, name the
finding."* This document names it.

---

## 1. Oracles re-run fresh (close-discipline §1)

Every command below was run in this close session against the working tree. Exit codes read
directly; no work unit's self-report was inherited.

| Oracle | Command | Exit | Observed |
|---|---|---|---|
| tests | `python3 -m unittest discover -s tests -v` | **0** | `Ran 1898 tests in 61.938s` / `OK (skipped=3)` |
| lint | `ruff check specfuse .specfuse/scripts tests scripts` | **0** | `All checks passed!` |
| security | `bandit -r specfuse .specfuse/scripts -ll` | **0** | `No issues identified.` (89 low, 0 medium, 0 high) |
| coverage | `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90` | **0** | `TOTAL 5575 367 93%` |

**Environment note, recorded so the next session does not re-diagnose it.** The first suite run
in this session failed with 11 errors, every one of them
`git commit ... returned non-zero exit status 128` inside a test's throwaway temp repo. The
swallowed stderr was `error: Couldn't get agent socket?` — the sandbox blocks the ssh-agent
socket, and the operator's global git config signs commits with an ssh key. The failure is an
artifact of the sandbox, not of the tree: re-run with the sandbox disabled, the same command
exits 0 with 1898 tests green. `GIT_CONFIG_GLOBAL=/dev/null` does *not* work around it. Any
future close running these gates in a sandbox will hit the same 11 errors.

## 2. End-to-end fixture execution (fresh, this session)

Each rule was executed against a fixture built this session under the session temp directory
and run through the real `specfuse-lint` entry point. No behavior below is argued from reading
source.

### 2a. Deadlock fixture (T02's ERROR rule) — **FAILS**

Fixture: a `pending` WU declaring `produces: src/main/java/Reconciler.java` whose Do-not-touch
section forbids `src/main/**`. This is the exact FEAT-2026-0066/T04 shape the feature was
chartered on, written in the **canonical body form the shipped template prescribes**:

```markdown
**Do not touch.** `src/main/**` (T03 owns it); other features' folders; `.git/`.
```

Result — `specfuse-lint <fixture>`:

```
OK — /<tmp>/fx-deadlock is structurally valid.
LINT_EXIT=0
```

**No ERROR. Exit 0. The deadlock is armable.**

Two controlled variants isolate the cause:

| Variant | Do-not-touch form | Exit | ERROR fires? |
|---|---|---|---|
| `fx-deadlock` | `**Do not touch.** \`src/main/**\` …` (all on the label line) | 0 | **no** |
| `fx-atx` | `## Do not touch` heading, pattern on a following line | 1 | yes |
| `fx-cont` | `**Do not touch.** Other features' folders;` + pattern on the **next** line | 1 | yes |

Root cause, confirmed by executing the extractor directly:

```
DNT SLICE: '\n'
PATTERNS: []
```

`check_produces_boundary` calls `_slice_section(body, "Do not touch")`
(`specfuse/loop/lint_plan.py:559`), which resolves to `slice_wu_section`
(`specfuse/loop/_wu_sections.py:35-44`). That helper matches the heading, then takes content
**from the next line onward** (`nl = body.find("\n", m.end())`). For an ATX heading that is
correct. For the bold-preamble form — `**Do not touch.** <content on the same line>` — the
entire content *is* the heading line, so the slice discards it. The sibling slicer for
acceptance criteria (`slice_acceptance_criteria`) handles both forms; this one does not.

Scale of the blind spot in this repo:

```
grep -c '^\*\*Do not touch' .specfuse/features/*/WU-*.md   → 327
grep -c '^## Do not touch'  .specfuse/features/*/WU-*.md   → 0
```

327 work-unit bodies use the bold form; zero use the ATX form.
`.specfuse/templates/WU.template.md:126` prescribes the bold form. The rule therefore sees only
whatever a boundary happens to spill onto a continuation line — an accident of line wrapping,
not a contract.

When the rule *does* fire, its message is correct and complete, and it names the post-attempt
guard as the FEAT-2026-0070 rule requires:

```
ERROR: WU-04-deadlock.md: FEAT-2026-0099/T04 declares produces path
'src/main/java/Reconciler.java', which its own Do-not-touch section forbids via
'src/main/**'. This is a structural deadlock — assert_produces_in_diff would refuse it
after a full dispatch attempt. Drop the path from produces, narrow the Do-not-touch
pattern, or add an explicit 'except' carve-out. See FEAT-2026-0066/T04, FEAT-2026-0070.
```

The message is right. The trigger is wrong.

### 2b. Delivered-path fixture (T01's WARN rule) — **passes**

Fixture: a `done` WU declaring `produces: src/main/resources/reconcileListProperty.mustache`
and a `pending` WU re-declaring the same path.

```
WARN: WU-04-redeclares.md: FEAT-2026-0098/T04 declares produces path
'src/main/resources/reconcileListProperty.mustache', but done WU FEAT-2026-0098/T03
(WU-03-delivers.md) already delivered it. Drop the path, or state the incremental edit
this WU makes to it in the body.
OK — /<tmp>/fx-delivered is structurally valid.
EXIT=0
```

Both WUs named, authoring response stated, WARN-only (exit 0) as specified. T01's rule reads
frontmatter only and never touches the section slicer, which is why it is unaffected by 2a.

### 2c. Unified literal/glob semantics (T03) — **passes**

A dispatch-shaped fixture repo with a real WU file loaded through `loop.load_wu`, real
non-empty files on disk, and a `git diff --name-only`-shaped touched list. Both guards called
with the same `WorkUnit`, cwd at the fixture repo root:

```
loaded WU produces = ['src/main/resources/*.mustache']
assert_declared_deliverables: (True, '')
assert_produces_in_diff:     (True, '')
```

One declaration form, both gates. Negative observations (the rules seen refusing purpose-built
bad input, per verification-discipline §3):

```
NEG glob-no-match declared: (False, 'declared deliverable glob matched no existing non-empty
                                     file: src/main/resources/*.java')
NEG glob-no-match in-diff:  (False, "declared produces path(s) not in this WU's squash diff:
                                     src/main/resources/*.java")
NEG directory:              (False, 'declared deliverable is a directory: src/main/resources —
                                     directories are not valid produces: entries under the
                                     unified literal/glob contract …')
```

The glob requires ≥1 existing match on both sides, and the directory form is refused with a
message naming the unified contract rather than silently passing one gate and failing the
other. T03's deliverable holds.

### 2d. Prose handoff (T04) — **passes, as prose**

`grep "passes presence and fails diff" .specfuse/templates/WU.template.md` returns nothing; the
template, `arm-gate`, and `authoring-work-units` point at `specfuse-lint`. The prose is
accurate about T01 and T03. It is currently inaccurate about the boundary check in the sense
that it tells an author the arm-time lint covers a class it does not in fact cover on the body
shape the same template prescribes — the fix belongs in the lint, not in the prose (which is
exactly T04's own escalation rule, read the other way round).

## 3. Satisfiability sweep — **FAILS the gate's definition of done**

`specfuse-lint` over all 43 feature folders in this repo. The gate requires **zero ERROR
findings**. Observed: **15 ERRORs across 4 features**, plus 1 folder the lint cannot evaluate.

| Feature | ERRORs | Character |
|---|---|---|
| `FEAT-2026-0023-lifecycle-integration-test` | 3 | false positive |
| `FEAT-2026-0024-hashed-denylist-leak-guard` | 7 | false positive |
| `FEAT-2026-0069-monitoring-check-targets` | 3 | false positive |
| `FEAT-2026-0070-terminal-flip-contract` | 2 | false positive |
| `FEAT-2026-0020-public-readiness-prep` | — | lint crashes (pre-existing, unrelated) |

Every one of the 15 is a **false ERROR**, and they share one cause with 2a: the extractor reads
the wrong half of the section. Two representative shapes:

- **An allow-list read as a deny-list.** `FEAT-2026-0023/T01`'s section opens
  `**Do not touch.** These files change: … and one new test file
  \`tests/test_terminal_flip_ownership.py\`. Do NOT modify …`. The enumeration of files the WU
  *does* change wraps onto continuation lines — the only lines the slicer keeps — so the lint
  extracts the WU's own deliverables as forbidding patterns and ERRORs on it declaring them.
  The actual prohibitions sit on the label line and are invisible.
- **A qualifier the extractor cannot see.** `FEAT-2026-0070/T08` writes
  `every existing \`check_*\` function`. The rule matches the new helper
  `check_autoclose_debt_prediction` against `check_*` and calls the WU a deadlock — the WU whose
  entire purpose was to add that helper. "existing" is semantic, and
  `_extract_do_not_touch_patterns` has no way to honor it.

This is the disease the WU's own escalation trigger warned about: *"a boundary rule that
guesses will refuse legitimate arms, which is worse than the disease."* Shipped as-is, arming a
gate on four of this repo's own features is refused for no reason, while the deadlock the
feature exists to catch arms clean.

`FEAT-2026-0020-public-readiness-prep` is separate and **not** this feature's doing: the lint
raises `MiniYAMLError: line 14: not a 'key: value' line — got '<!--'` on an HTML comment inside
a WU's frontmatter. Pre-existing, in code this feature did not touch; recorded so it is not
rediscovered.

**Expected WARNs.** The gate requires the feature's own T01/T02 `lint_plan.py` overlap to appear
in the sweep. It does **not** appear, and cannot: `check_produces_satisfiability` fires only for
dispatchable statuses (`pending`/`ready`/`draft`), and both T01 and T02 are now `done`. The WARN
was correct at arm time and is unobservable at close time. The rule was verified instead on the
equivalent fresh fixture in 2b. This criterion is a close-time impossibility written into the
gate, not a defect in T01 — see §6.

## 4. This feature's own lint status

```
specfuse-lint .specfuse/features/FEAT-2026-0055-arm-time-wu-contract-lint
OK — … is structurally valid.
SELF_LINT_EXIT=0
```

Exit 0 — but note this is weak evidence given §2a: this feature's five WU bodies all use the
bold form, so the boundary check largely does not inspect them.

## 5. Cost analysis

Planned (PLAN.md `planned_cost_usd: 22.00`; gate budget 27.00) against `events.jsonl` actuals.

| WU | Planned | Actual | Attempts | Delta |
|---|---|---|---|---|
| T01 produces-satisfiability WARN | $5.00 | $1.132481 | 1 | −$3.87 |
| T02 boundary-consistency ERROR | $4.00 | $1.374473 | 1 | −$2.63 |
| T03 unify produces semantics | $5.00 | $1.037655 | 1 | −$3.96 |
| T04 surfacing + folklore deletion | $3.00 | $0.675363 | 1 | −$2.32 |
| **Implementation subtotal** | **$17.00** | **$4.219972** | 4 | **−$12.78 (−75%)** |
| G1-CLOSE (this WU) | $5.00 | recorded by the driver at `task_completed` | 1 | — |
| **Feature total** | **$22.00** | **$4.22 + this close** | | under budget |

**Delta named.** Implementation came in at 25% of plan — every WU passed first attempt with
zero re-arms, and the per-WU estimates were sized for a 2–3 attempt lint-authoring cycle that
never materialised. The estimate error is uniform (−72% to −79% per WU), which points at a
systematic over-estimate for "add a `check_*` function plus its fixture tests to an existing
lint module", not at four independent lucky runs. The cheap implementation is also, in
hindsight, the signal that was available and unread: four first-attempt passes on a feature
whose whole subject is *rules that must actually fire* is precisely the shape where the gates
are measuring the wrong thing — every WU's fixture tests were authored in the ATX form the
rule can see, so the suite is green and the rule is dead on the real corpus.

### Failure-class breakdown

Zero non-passing attempts in this gate. All five `attempt_outcome` events in `events.jsonl`
carry `"outcome": "passed"`, `"failure_class": null`, `"failure_signature": null`,
`re_arm_count: 0`. No failure classes to break down — the entire cost of this feature's defect
landed in the close, not in attempt churn.

## 6. What the loop did NOT verify

1. **Portfolio measure — zero produces-class refusals downstream.** *Criterion (PLAN.md
   Notes, verbatim):* "Portfolio success measure (verified downstream, not here):
   `produces_not_in_diff` / `no_deliverable_files` / `deliverable_missing` attempts at zero on
   the next generator-class feature run under a driver carrying this feature."
   *Why unverifiable here:* it is a measurement over a future feature's `events.jsonl`; no such
   run exists.
   *Exact re-run condition:* after the next generator-class feature completes gate 1 under a
   driver carrying this branch, grep that feature's `events.jsonl` for
   `failure_class` in {`produces_not_in_diff`, `no_deliverable_files`, `deliverable_missing`};
   zero occurrences upgrades this entry. **Note this measure is currently meaningless for the
   boundary class** — §2a shows the ERROR rule cannot fire on real WU bodies, so a zero count
   would prove nothing until §7's fix lands.

2. **The self-WARN on this feature's own T01/T02 overlap.** *Criterion (verbatim):*
   "Satisfiability sweep re-run: `specfuse-lint` over every feature folder in this repo — zero
   ERROR findings, expected WARNs enumerated (including this feature's own T01/T02 overlap,
   which must appear)."
   *Why unverifiable here:* the WARN is scoped to dispatchable statuses; T01 and T02 are `done`
   by close time, so the observation window has closed. Verified on an equivalent fresh fixture
   instead (§2b).
   *Exact re-run condition:* observe the WARN on a feature folder whose earlier WU is `done`
   while a later WU is still `pending` — i.e. run `specfuse-lint` at the arm boundary, not at
   close. The next feature that arms a gate with a shared `produces:` path upgrades this entry
   from live state.

Two entries, 2 of 10 criteria (20%) — under both the ">2 entries" and the ">30% of criteria"
thresholds, so single-gate sizing is not flagged on this axis. §7 says what should change
anyway.

## 7. What I'd change

- **Test the shape the template actually ships.** T02's fixtures were authored with
  `## Do not touch` ATX headings while every real WU — and the template T04 edits in the same
  gate — uses `**Do not touch.**`. The suite was green and the rule was inert. A rule whose
  input is a document shape must have at least one fixture copied verbatim from the shipped
  template, not hand-written in a shape that happens to parse.
- **Require the motivating case as a fixture, by construction.** This feature was chartered on
  one concrete incident (FEAT-2026-0066/T04). Reproducing that incident's *actual body text* as
  a fixture and asserting the rule fires would have failed T02 immediately. "Fixture tests
  cover: the T04 shape" was in T02's acceptance criteria and was satisfied by a paraphrase of
  the shape, not the shape.
- **Make the sweep an implementation-WU gate, not a close-time criterion.** T02's own
  acceptance criteria required the zero-ERROR sweep and said "Any ERROR on an existing feature →
  stop, escalate". T02 reported `passed`. Whatever T02 ran, it was not the sweep this close ran;
  the sweep is a one-line command and belongs in `verification.yml` as a gate the driver
  executes, where an agent's self-report cannot stand in for it.
- **Do not write close-time criteria that depend on mid-dispatch state.** The "T01/T02 overlap
  WARN must appear" criterion was unsatisfiable the moment T02 flipped to `done` (§6.2). Arm-time
  observations belong to an arm-time check.

## 8. Consumer-visible contract changes — awaiting operator acknowledgment

These reach every consumer of the scaffold, not only this repo. **Not `n/a`.** This list is
recorded for a human to acknowledge; the terminal flips stay withheld until then, and on a
`not_met` verdict they stay withheld regardless.

1. **`assert_declared_deliverables` accepts globs (T03, `specfuse/loop/loop.py`).** Previously
   literal-path existence only. Now a `produces:` entry containing `*`, `?`, or `[` is satisfied
   by ≥1 existing non-empty match. **Widening** — every previously-passing declaration still
   passes. Consumer impact: WU authors on any Specfuse project may now declare glob deliverables
   that satisfy both gates.
2. **Directory `produces:` entries are now refused outright (T03).** Previously a directory
   silently passed the presence gate and then failed `assert_produces_in_diff` at squash time.
   Now it is refused with a message naming the unified contract. **Behavior change, not a pure
   widening**: a WU that declared a directory previously reached the diff gate and failed there;
   it now fails earlier with a different message. Any downstream project with a directory in a
   `produces:` list sees a new refusal text.
3. **`WU.template.md` `produces` note rewritten (T04, `.specfuse/templates/`, mirrored to
   `specfuse/loop/data/templates/`).** The literal-vs-glob warning block is deleted and replaced
   by a one-line statement of the unified contract. Every project that scaffolds a WU from the
   template gets the new text; projects that copied the old warning into existing WUs keep stale
   prose that is now wrong in the direction of being over-cautious.
4. **Skill prose (T04, `plugins/specfuse/skills/`, mirrored to `.specfuse/skills/`).**
   `authoring-work-units` now points at `specfuse-lint`'s satisfiability/boundary checks as the
   arm-time verification; `arm-gate` step 3 gains a "run `specfuse-lint` before walking drafts"
   line. **Caveat the operator should weigh:** per §2a and §3, the boundary half of what this
   prose promises does not currently work on real WU bodies, and the satisfiability half emits
   15 false ERRORs on this repo's own features. Shipping the prose ahead of the fix tells every
   consumer to trust a check that is simultaneously blind and noisy.
5. **New lint findings (T01, T02, `specfuse/loop/lint_plan.py`).** `specfuse-lint` gains a WARN
   class and an ERROR class. The ERROR class changes `specfuse-lint`'s **exit code** to 1 on
   affected features — any consumer CI running `specfuse-lint` in a blocking position will start
   failing on the false positives in §3.

## 9. Lessons

Promoted to `.specfuse/LEARNINGS.md` (two entries, this gate). Not `nothing generalizes`.

## 10. Recommended disposition

Fix-forward in this feature rather than reverting: T01 and T03 are sound and independently
valuable, and the defect is localised to one function plus its fixtures. The shape of the fix —
teach `slice_wu_section` the bold-preamble form (the sibling acceptance-criteria slicer already
does), then re-derive the boundary patterns from the whole section and re-run the sweep to zero
— is a small, well-bounded work unit. It is deliberately **not** applied here: this close's
Do-not-touch bars `specfuse/loop/**`, and a verification-found defect escalates rather than
gets patched by the session that found it.
