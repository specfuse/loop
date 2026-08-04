<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0064: "what changed, and will it break me", answerable from one document

Single terminal gate, three implementation work units, one close. Every WU passed on
its first attempt with no escalations and no re-arms, and the gate's substantive spend
came in at **$9.64 against $11.00**.

The feature's real test is not in the suite. T02 makes the close ceremony a collection
point, so **this close is the first entry ever written into the document this feature
built** — the section
[Duplicated work, or a relocated artifact?](#duplicated-work-or-a-relocated-artifact)
reports what that was actually like, because the design's central bet is that
appending costs nothing and no test can measure that.

## Gate 1 — the document, both collection points, and the release stamp

### What was built

**T01 — the document, its schema, and a parser that reads it back (`done`, 1 attempt,
$1.721612 against $4.00).** `CHANGELOG.md` at the repository root in Keep-a-Changelog
shape, with an `Unreleased` section and a comment a reader meets before the first entry
explaining why fifty-one prior features are absent. `specfuse/loop/changelog.py` parses
it: `ENTRY_CLASSES` (`added` / `changed` / `fixed` / `breaking`), `parse_changelog`
returning a `ParseResult` of `ChangelogSection`s and `ChangelogEntry`s plus a `findings`
list, and a trace regex requiring every entry to carry a `FEAT-YYYY-NNNN` (optionally
with a WU suffix) or `#<issue-number>`. Malformed input produces findings, never a
traceback. The module imports nothing from `loop.py`. Oracle:
`tests/test_changelog_schema.py`, red on HEAD before the WU ran because the module did
not exist.

**T02 — two collection points, because bugs have no close ceremony (`done`, 1 attempt,
$5.031107 against $4.00).** `close-discipline.md` §3 gains the append obligation, worded
to say explicitly that it is the *same* material §3 already requires rather than a
second write — and that an `n/a` close appends nothing, because a changelog padded with
"no user-facing change" trains readers to skip it. `fix-bug`'s SKILL.md (both copies,
byte-identical) gains a mandatory pre-PR step appending one `Unreleased` entry carrying
`#<issue-number>`, in the same commit as the fix. `closing_requirements.py` gains
`close-k` plus the three helpers it needs (`find_consumer_visible_section`,
`consumer_visible_section_is_na`, `changelog_has_entry_for`), enforced pre-squash by
`assert_changelog_entry_for_contract_changes` in `loop.py` and by
`_check_changelog_entry_for_contract_changes` in `lint_closing.py`. Oracle:
`tests/test_changelog_collection.py`, red on HEAD because `fix-bug` prescribed no
append at all.

**T03 — cutting a version stamps the section, and freezes it (`done`, 1 attempt,
$2.884429 against $3.00).** `stamp_release` turns `Unreleased` into a released heading
carrying version, date, and a **required** umbrella version, and opens a fresh empty
`Unreleased` above it so the next append has a home nobody creates by hand. A second
stamp of the same version raises rather than silently re-stamping. `append_entry`
refuses any `section` other than `"Unreleased"`, which is how immutability is enforced
rather than asked for. `scripts/bump_version.py` reads `.specfuse/release.yml` for
`tag_prefix` and the `version_sources` list — this repository's values as the fallback,
so a target project sets its own — and stamps the changelog in the same call that sets
all four version sources. Oracle: `tests/test_changelog_release_wiring.py`, red on HEAD
because no stamp existed.

**One design compromise T03 made, recorded because a consumer will meet it.** The
umbrella version is packed *inside* the heading's version field as
`<version>+umbrella.<umbrella>`, not appended after the date. T01's
`_RELEASED_HEADING_RE` requires the date to be the last token on the line, so there was
no room after it; the version field is `[^\]]+`, so a semver-build-metadata-shaped
separator fits without touching T01's regex. `split_version_field` is the accessor, and
it returns `(field, None)` for a heading with no umbrella suffix. The compromise is
sound but it means **the release heading is not plain semver**, and anything parsing
that heading with a naive semver reader will get `0.9.0+umbrella.1.4.0`. No release has
been cut yet, so nothing downstream depends on it — this is the moment to notice it.

### Oracles re-run fresh (close-discipline §1)

Re-run in this session, unsandboxed, exit codes read directly — not inherited from any
WU's self-report.

```
$ .venv/bin/python -m unittest discover -s tests
Ran 2244 tests in 93.822s
OK (skipped=3)
TESTS_EXIT=0

$ .venv/bin/ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
LINT_EXIT=0

$ .venv/bin/bandit -r specfuse .specfuse/scripts -ll
Total issues (by severity):  Medium: 0   High: 0
SEC_EXIT=0

$ .venv/bin/coverage run --source=specfuse -m unittest discover -s tests \
      && .venv/bin/coverage report --fail-under=90
TOTAL   7169   469   93%
COV_EXIT=0

$ python3 .specfuse/scripts/leak_scan.py --all
leak-scan: gitleaks 8.30.1
leak-scan: clean
LEAK_EXIT=0

$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 50 events.jsonl file(s), 1164 event(s) checked
EVENT_GATE_EXIT=0

$ python3 .specfuse/scripts/roadmap_link_gate.py
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 8 warning(s)
ROADMAP_GATE_EXIT=0

$ python3 .specfuse/scripts/arm_sweep_gate.py
evaluable=11 evaluated=11 could_not_evaluate=0 excluded_no_baseline=42
ok: 11 evaluable feature(s) swept clean, no not_evaluable verdicts
ARM_SWEEP_EXIT=0

$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
MONITORING_EXIT=0

$ for b in leak_scan_hook sync_scaffold sync_scaffold_symlinks init_sh_shim \
           init_skills_idempotent hookspath_conflict; do bats tests/$b.bats; done
all six suites EXIT=0
```

The eight `roadmap_link_gate` warnings are pre-existing and unrelated to this feature —
`—` Detail cells on FEAT-2026-0050 and FEAT-2026-0052 and six siblings. WARN findings
deliberately do not fail that gate; see the gate's comment in `verification.yml`.

**The feature's own document parses clean against its own parser**, asserted rather
than claimed — the close's six appended entries were written *through* `append_entry`,
not by hand, and re-parsed afterwards:

```
$ .venv/bin/python -c "…parse_changelog(Path('CHANGELOG.md').read_text())…"
findings: []
  [added]    FEAT-2026-0064/T01
  [added]    FEAT-2026-0064/T03
  [added]    FEAT-2026-0064/T03
  [breaking] FEAT-2026-0064/T03
  [breaking] FEAT-2026-0064/T02
  [changed]  FEAT-2026-0064/T02
  [changed]  FEAT-2026-0064/T02
```

**A gate-report artefact met while re-running, recorded so the next close does not
misread it.** The first re-run piped `unittest` through `tail -5` and produced a window
containing neither `OK` nor `FAILED` — it ended on
`Gate 1 complete (retro, lessons, docs, plan-next); terminal gate but PLAN.md not yet 'done'`,
which is output from `FEAT-2026-9301`, a test fixture. This is exactly the defect
[FEAT-2026-0068](../../roadmap.md#feat-2026-0068) is on the roadmap to fix, observed
here on a *passing* run. The verdict was recovered by writing the full log to a file
and grepping `^(OK|FAILED)|^Ran ` out of it. Any close obliged to re-run oracles in
this repository should capture to a file and grep for the verdict rather than tailing.

### Consumer-visible contract changes

Six items across the three WUs. Two are `breaking`; both are enumerated first here for
the same reason `breaking` is its own entry class — the consumer's actual question is
"will this break me", and that answer should not require reading to the end.

**1. `scripts/bump_version.py` now requires `--umbrella-version` (breaking, T03).**
`python3 scripts/bump_version.py 0.9.0` used to work and now raises before any file is
written. The refusal is deliberate per `PLAN.md` decision 3: `pipx upgrade specfuse`
resolves through the umbrella package, so a driver version nobody can install is half a
release, and the omission had to be impossible rather than discouraged. The operator
running the release that follows this feature is the first person to meet this.

**2. `close-k` is a new closing requirement (breaking, T02).** A close whose
`Consumer-visible contract changes` section names a real change now fails **pre-squash**
unless `CHANGELOG.md`'s `Unreleased` gained an entry tracing to that feature's FEAT-ID.
`close-discipline.md` ships in the scaffold data payload, so every project that runs
`specfuse upgrade` inherits the obligation and the check together. **And it inherits
them without the file**: `specfuse init` copies `specfuse/loop/data/` into `.specfuse/`
and writes `.gitignore`, `CLAUDE.md`, and `.claude/settings.json` — it does not create a
root `CHANGELOG.md`, and `close-k` reads `<repo_root>/CHANGELOG.md`. A downstream
project's first close with a real §3 enumeration therefore fails with
`CHANGELOG.md does not exist` until someone adds one. See
[What the loop did NOT verify](#what-the-loop-did-not-verify), item 3 — this was found
by this close, not by any acceptance criterion, and it is the most consequential line
in this enumeration.

**3. `CHANGELOG.md` and `specfuse/loop/changelog.py` are new (added, T01).** The module
is importable driver surface: `ENTRY_CLASSES`, `parse_changelog`, `ChangelogEntry`,
`ChangelogSection`, `ParseResult`. It imports nothing from `loop.py`, so a consumer can
use it without pulling in the driver.

**4. `changelog.py` gains `stamp_release`, `append_entry`, `split_version_field`
(added, T03).** Appending to any section other than `Unreleased` raises; re-stamping a
released version raises. The release-heading version field is
`<version>+umbrella.<umbrella>`, readable only through `split_version_field`.

**5. `.specfuse/release.yml` is a new optional config file (added, T03).**
`tag_prefix` and `version_sources`; absent means this repository's four sources and a
`v` prefix. A target project overrides either without editing the script.

**6. `close-discipline.md` §3 and `fix-bug` both gain an append step (changed, T02).**
The rule ships via the loop package's data payload; the skill ships via the
`specfuse@specfuse` plugin. Both reach downstream projects on upgrade.

**What did NOT change, stated so nobody looks for it.** No `git tag`, `git push`, or
PyPI upload was added — `bump_version.py` gained a changelog step, not a release
pipeline. The umbrella repository is untouched; this feature makes its version
*representable and required*, and the operator supplies the value. No already-`done`
feature's records were read or modified.

<a id="duplicated-work-or-a-relocated-artifact"></a>
### Duplicated work, or a relocated artifact?

The honest answer is **neither cleanly, and the distinction the design rests on is
slightly wrong**. It was one act of understanding rendered twice at two different
compression levels, and the second rendering was cheap only because of the order it was
done in.

What was *not* duplicated: the thinking. Deciding that `close-k` is breaking rather
than additive, that the umbrella flag is a real break for the operator about to cut a
release, that `.specfuse/release.yml` is additive and uninteresting — that work happened
once and served both surfaces.

What *was* genuinely twice: the writing. §3 above wants context, cause, and evidence;
a changelog entry is one line with no room for any of it. Item 2 is six sentences here
and one clause there. That is not a second understanding, but it is a second act of
composition, and the compression is where the loss lives — the one-liner is the only
thing a consumer reads, and the paragraph holding the reasoning is linked to it by
nothing but the FEAT-ID trace.

**The finding worth more than the green gate: order decides whether it feels free.**
The entries were written **first**, through `append_entry`, and §3 was written around
them afterwards. That made §3 *better*, because the one-line constraint forces you to
decide what the change actually **is** before you can write the paragraph explaining
why it matters. Had §3 been written first and the entries "extracted" from it, the
entries would have been summaries of my own prose — one more lossy hop, and exactly the
degradation `PLAN.md` says a release-time generator produces, just performed by hand.

`close-discipline.md` §3 currently says the append is "the same material… not a second
write". That is the right *intent* and it is imprecise as guidance: it is the same
material and it **is** a second write, and the way to make that second write near-free
is to do it first. That belongs in the rule, and it is promoted as a lesson below
rather than edited into `close-discipline.md` here, because that file is T02's
deliverable and this close does not own it.

### Was classifying easier than prose?

**This close does not hedge, so no `kind:` was written** — FEAT-2026-0059's `close-j`
never fires here and the sample the WU brief hoped to grow does not grow from this
feature. Saying so plainly is better than manufacturing a hedge to produce evidence.

The adjacent question does have an answer, from the same session. Every one of the six
enumeration items had to be classified into T01's four entry classes, and five were
instant. The sixth was not, and it is informative: **is a new lint check `added` or
`breaking`?** From the diff it is unambiguously an addition — a new `Requirement`
record, new helpers, new tests. From a downstream project's chair it is a check that
begins failing on a close that would have passed last week. It was classified
`breaking`, and the rule that settled it is that **an entry class is a property of the
consumer's experience, not of the diff** — which is the same principle as `breaking`
being its own class rather than a flag, applied one level down. If a future entry is
hard to classify, that is the question to ask, and T01's class docs do not currently
say so.

## Cost analysis

Reconciled against `events.jsonl`, which is authoritative. Three `attempt_outcome`
events, one per WU, every one `outcome: passed` at `attempt: 1`. Each WU's frontmatter
`cost_usd` matches its event to six decimal places; there are no re-arms, so no
`cumulative_cost_usd` field exists on any WU and the two-fold-paths ambiguity
[FEAT-2026-0067](../../roadmap.md#feat-2026-0067) describes does not arise here.
**The sum reconciles exactly; there is no gap to report.**

| WU | planned | actual (`events.jsonl`) | delta | attempts |
| --- | --- | --- | --- | --- |
| T01 — schema and parser | $4.00 | $1.721612 | −57.0% | 1 |
| T02 — two collection points | $4.00 | $5.031107 | +25.8% | 1 |
| T03 — release wiring and portability | $3.00 | $2.884429 | −3.9% | 1 |
| **Implementation subtotal** | **$11.00** | **$9.637148** | **−12.4%** | **3** |
| G1-CLOSE (this WU) | $5.00 | not yet in `events.jsonl` | — | 1 |
| **WU sum (`PLAN.md` `planned_cost_usd`)** | **$16.00** | — | — | — |
| **Gate budget (`GATE-01.md`)** | **$21.00** | **$9.637148 consumed** | **45.9% used** | — |

The close's own `attempt_outcome` is written by the driver *after* this session ends,
so its actual cost cannot appear here without inventing a number. The $21.00 gate
budget is the $16.00 WU sum plus $5.00 of defensive padding for one re-attempt of the
close, per the GATE template while the closing-WU retry defect (#260) is open. That
padding went unused: nothing re-attempted.

**Where the one overrun came from.** T02 is the only WU over its estimate, by $1.03. It
carried the widest surface of the three — two rule copies, two skill copies, a new
requirement record, two enforcement sites (driver and lint), and a test file asserting
the no-backfill scoping — against an estimate equal to T01's, which built one module and
one document. The estimate was wrong at draft time, not the execution: T02 passed first
try with no escalation. The lesson is narrow enough that it is not being promoted — "a
WU touching six files across four subsystems is not the same size as a WU building one
module" is already what the planning floor exists to encode.

### Failure-class breakdown

**No failures.** Zero non-passing attempts across the gate: three WUs, three attempts,
three `passed`. No `failure_class`, no `failure_signature`, no escalation, no re-arm.
Nothing to break down, and the section is present rather than omitted so a reader does
not have to infer the difference between "no failures" and "nobody looked".

<a id="what-the-loop-did-not-verify"></a>
## What the loop did NOT verify

**1. Fifty-one `done` features and every prior bug PR are not in the document, and this
is a scope decision, not a claim that nothing changed.** `grep -l "^status: done"
.specfuse/features/*/PLAN.md | wc -l` returns **51**. Every one of them, plus every bug
PR ever merged in this repository, predates `CHANGELOG.md` and is deliberately absent.
`PLAN.md`'s escalation-predicate answer explains why: a check demanding retrospective
coverage would be red on arrival and could only pass by fabricating fifty-one summaries
from commit archaeology — the exact low-quality re-derivation this feature exists to
prevent, wearing the authority of a release note. **The early document is thin because
history was not audited.** Where it gets checked: nowhere, permanently, by design. This
is not deferred work.

**2. Entry prose quality is not machine-checkable, and a green lint is not a review.**
The lint asserts an entry exists, carries one of four classes, and traces to a FEAT-ID
or issue number. Whether the sentence is *useful* to a consumer is a human read, and
`PLAN.md` scoped it out precisely because a linter pretending otherwise would invite
writing for the linter. The six entries this close appended have been checked for
schema and not for prose. Where it gets checked: a human reading `CHANGELOG.md` before
the release that follows.

**3. `specfuse init` does not create a root `CHANGELOG.md`, so a downstream project
inherits `close-k` before it has the file.** Found by this close while enumerating §3,
asserted by reading `specfuse/loop/scaffold.py` (`init_specfuse` copies
`iter_scaffold_files()`, which walks `specfuse/loop/data/` into `.specfuse/`;
`wire_claude` writes `.gitignore`, `CLAUDE.md`, `.claude/settings.json`) and
`find specfuse/loop/data -iname "*CHANGELOG*"`, which returns nothing. The failure is
loud and self-describing — `close-k` reports `CHANGELOG.md does not exist` — and the fix
is one file with one heading, so this is a papercut, not a silent break. But nothing in
this feature closes it, and no acceptance criterion asserted it. Why not verified
in-loop: no WU criterion covered target-project scaffolding of the document itself;
T03's portability criterion covered the tag convention and version-source list, which
*are* delivered. Where it actually gets checked: the next `specfuse upgrade` of a
downstream project followed by a close with a real §3 enumeration. It is named in the
roadmap detail section so it is not lost, and it is stated in the `breaking` changelog
entry so a consumer meets it before it bites them.

**4. The release stamp has never run for real.** `stamp_release` and
`bump_version.py`'s changelog step are covered by
`tests/test_changelog_release_wiring.py` and by the coverage gate; neither has cut an
actual release. Why not verified in-loop: a WU cannot tag or publish, and `PLAN.md`
explicitly scoped `git tag`, `git push`, and PyPI upload OUT. Where it gets checked:
the release the operator has stated follows immediately after this feature — the first
real invocation is `python3 scripts/bump_version.py <v> --umbrella-version <u>`, and it
is also the first time a human sees a stamped heading carrying
`<version>+umbrella.<umbrella>`.

**5. The bug-side collection point has never been exercised.** `fix-bug`'s new step is
asserted as *prescribed text* by `tests/test_changelog_collection.py`; no bug has landed
since T02 shipped, so no agent has ever executed it. This is the weaker half of the
"two collection points" decision by construction: the feature side runs under a
mechanical check (`close-k`), the bug side runs under an instruction in a skill. Why
not verified in-loop: it requires a real bug fix, which is a different workflow with its
own branch and PR. Where it gets checked: the next `/fix-bug` run.

**6. No predecessor auto-close debt to reconcile.** `grep -rn "autoclose-debt"` over the
feature directory returns nothing: this feature has one gate, it did not auto-close, and
no earlier gate deferred obligations into this close. `close-g` is checked post-pass and
has nothing to find; the absence is recorded here rather than left to be inferred.

**7. Entry-class section order is insertion order.** `append_entry` creates a
`### <Class>` heading the first time a class is used, so `Unreleased` currently reads
Added, Breaking, Changed — a consumer scanning top-down for breakage meets three
additions first. Nothing in the schema fixes an order and nothing asserts one. Not
changed here because `CHANGELOG.md` and its schema are T01's deliverable and this close
does not own them. Where it gets checked: a human reading the document, or a future
feature that decides section order is part of the contract.

## Lessons promoted

Two, both tagged `[FEAT-2026-0064/G1-CLOSE]` in `.specfuse/LEARNINGS.md`.

**`write-the-compressed-artifact-first`.** The generalization of this feature's own
subject, sharpened by the ordering finding above: when a ceremony already produces
material one audience needs and a second audience re-derives it worse, relocate it
rather than commissioning a second write — and name the second audience, because an
artifact with no named reader is the failure being repeated. The operational half is
the order: write the compressed rendering first and the prose around it, never the
reverse.

**`patch-the-instance-ask-why`.** Promoted on the WU brief's instruction even though it
is not this feature's subject, because it is the most transferable rule the session
produced and there is no better home for it. The claim was verified against
`tests/test_no_pytest_subprocess.py`'s own docstring rather than taken from the brief,
and the numbers differ: **five instances across three work units in two features**
(FEAT-2026-0042/T02, FEAT-2026-0059/T02, FEAT-2026-0059/T03), with the guard written
after the third work unit, not the third feature. The rule survives the correction
intact — arguably it is sharper, because the second and third batches landed in the
*same* feature, which is as close as this repository gets to being told twice in one
sitting and still patching instances.

## Closing state

- Gate 1 definition of done: met. `CHANGELOG.md` exists with an `Unreleased` section;
  both surfaces that ship work append to it; `bump_version.py` stamps a version, a
  date, and a required umbrella version, after which that section is immutable and a
  fresh `Unreleased` sits above it.
- Every implementation WU: `done`, first attempt.
- `RETROSPECTIVE.md`: this file.
- `.specfuse/LEARNINGS.md`: two entries appended, tagged `[FEAT-2026-0064/G1-CLOSE]`.
- `.specfuse/roadmap.md`: detail section reconciled against what was built, including
  the two-collection-points decision that widened the row and the scaffolding gap in
  item 3 above.
- `CHANGELOG.md`: six entries appended by this close, through `append_entry`, parsing
  clean.
- Verdict: `met`. Every acceptance criterion of all four work units was verified in
  this session against a re-run oracle. The three findings that surfaced during the
  close — the missing scaffolded `CHANGELOG.md`, the unexercised bug path, the
  never-run release stamp — are recorded above with where each gets checked; none is an
  unmet criterion, and hedging on findings no criterion asserted would blur a
  distinction `LEARNINGS [FEAT-2026-0059/G1-CLOSE/never-vs-not-here]` was written to
  keep sharp.
- Terminal flips (`GATE-01.md` → `passed`, roadmap row → `done`, `PLAN.md` →
  `done`, roadmap detail archived) are the driver's, fired by `fire_terminal_flips`
  after this WU's squash. This close writes none of them.
