---
gate: 3
drafted_by: FEAT-2026-0109/G2-PLAN
open_questions:
  - "Q1 (WU-08): pin the build, or auto-re-exec from the fresh tree? Both remove the restart; they differ on whether a driver edit takes effect this run or the next."
  - "Q2 (WU-08, WU-90-gate-3-close): is 'a driver change takes effect at the next run' acceptable for a close whose own guards the gate just changed?"
  - "Q3 (PLAN.md, out of this unit's edit scope): planned_cost_usd is $26.00 against a WU sum of $56.00 — still the operator's number, flagged since gate 2's review."
  - "Q4 (no drafted WU — deliberately): T05's changed-file map is still never written, costing ~166s per driver-touching attempt. It does NOT belong in gate 3; where should it go?"
---

# Gate 3 review — the driver runs from a pinned build

Written by `FEAT-2026-0109/G2-PLAN` for the human who arms gate 3. Gate 3's
drafts are `WU-08` and the terminal close; both are `status: draft` and arming
is your act, not the driver's.

## Is gate 3 one unit? Yes.

**Gate 3 is drafted as exactly one substantive unit** — `FEAT-2026-0109/T08`,
`WU-08-installed-copy-driver.md` — plus its terminal close. `PLAN.md`'s gate 3
`work_units` list reads `T08` then `G3-CLOSE`, with `G3-CLOSE` depending on
`T08`.

I did not find a decomposition worth proposing. The migration's parts —
materializing the pin, entering execution from it, retiring the halt for the
pinned case, and teaching `build_provenance` a third state — are not separable
work: each one's exit oracle is the driver's own execution surface, so a unit
holding any subset cannot pass on its own and the driver thrashes, which is
exactly what `[FEAT-2026-0019/G1]` records costing $5.63 and 49 minutes before
abandonment. `WU-08`'s body says so in its own words so the constraint travels
with the unit rather than living only here.

The one thing that *would* have made a second unit tempting is Q4 below, and it
is not gate 3 work.

## If you check only three things, check these

1. **That T08 is still one unit when it dispatches.** This is the whole reason
   the feature is three gates instead of one, and it is the constraint most
   likely to be quietly relaxed at arm time — three tidy units in a graph look
   better than one large one and deadlock in execution. If T08 looks too big,
   the correct response is to cut its *scope* (drop a definition-of-done bullet)
   and re-plan, never to split the same scope across units.
2. **The `build_provenance` third state — definition-of-done bullet 4.** T08
   makes an out-of-tree run the *sanctioned* mode, and `build_provenance` exists
   (#1040) precisely to warn that out-of-tree runs "return a plausible number"
   rather than failing — it cost a gate-1 arming probe a wrong answer and a
   terminal close 14 spurious reds. The cheap way to make a pinned run quiet is
   to suppress the warning. If T08 does that, gate 3 does not remove #1040's
   failure mode; it blesses it, permanently and silently. The warning must
   *learn the difference* between a recorded pin and an unidentified wheel, and
   keep firing on the second. This is the one decision in the gate that a later
   fix cannot recover, because the damage is silent — the same shape as gate 2's
   absent-key default.
3. **Whether you accept "one run late" — Q1 and Q2 below.** Under a pin, a
   driver change a unit lands takes effect on the *next* run rather than at this
   gate's close. Today's halt buys the opposite: the operator restarts and the
   close runs the new code. That trade is the substance of the gate and it is
   reversible — Q1 names a coherent alternative that keeps the immediate-effect
   property and still removes the restart. If you prefer it, T08 is the unit to
   rewrite, and it is cheaper than what is drafted.

## What gate 3 is worth — measured, in this session

Counted over every `.specfuse/features/*/events.jsonl` in this repo, on
`driver_staleness_detected` events carrying `halted: true`, with the dead time
taken as the gap between each halt and the next event in the same feature:

| Measure | Value |
|---|---|
| Halted restarts, repo-wide | **49** |
| Features that paid at least one | **14 of 71** |
| Worst | FEAT-2026-0100 (7), **FEAT-2026-0109 (7)** |
| This feature | 3 in gate 1, 4 in gate 2 |
| Median dead time per restart | **541s (9.0 min)** |
| Mean / p90 | 3440s / 8518s |
| Total dead time across all 49 | **46.8 hours** |
| This feature's dead time across its 7 restarts | **558s (9.3 min)** — 23s to 238s each |
| Agent dollars burned by a halt | **$0.00** — no dispatch is spent |

**Do not arm gate 3 expecting the wall-clock win gates 1 and 2 delivered.** Read
the last two rows together: with an operator watching, this feature paid 9.3
minutes total for seven restarts — less than gate 2 spent on a single 194.4s
broad run. The repo-wide *median* is 9 minutes and the *mean* is 57, and the
whole gap between those two numbers is halts that landed when nobody was at the
keyboard. What gate 3 buys is not seconds; it is **the property that a
self-hosting feature can be left alone**. If that is not worth $14.50 to you,
say so now — the measurement above is the honest case, and it does not make a
speed argument.

## Existing-mechanism search (`planning-discipline.md` §1)

Grep commands run in this session:

```
grep -n "driver_staleness_detected\|driver_restart_required\|staleness" specfuse/loop/loop.py
grep -n "driver_paths\|DRIVER_SOURCE\|driver_source_paths" specfuse/loop/loop.py
grep -rn "site-packages\|pip install\|venv\|PYTHONPATH" specfuse/loop/*.py
```

**Verdict: found two mechanisms, extending both; no pinning mechanism exists.**

- `specfuse/loop/driver_edit.py` (FEAT-2026-0075/T01) already **detects** driver
  edits, from a commit's real diff rather than from a WU's declarations. T08
  changes the *response* and leaves the detection alone — it is in T08's **Do
  not touch** for that reason.
- `specfuse/loop/build_provenance.py` (#1040) already **answers "which build am
  I running?"** — `running_package_dir()`, `source_tree_package_dir()`,
  `out_of_tree_warning()`. T08 extends it with a third state rather than
  building a parallel answer. Its docstring is also the argument against the
  shape T08's first escalation trigger forbids: "a rule a session must remember,
  a silent wrong answer when it forgets, and no signal telling the two apart".
- Nothing materializes, caches or content-addresses a copy of the package. The
  `site-packages` / `pip install` / `PYTHONPATH` grep returns only docstrings and
  an upgrade hint. T08's `pin_driver_build` is new.

## Runtime probe (`planning-discipline.md` §4)

Applied before drafting, not asserted. A copy of `specfuse/` was materialized
under `$TMPDIR` and the driver executed from it against this repository, under
`.venv`.

| Probe | Result |
|---|---|
| Import from the copy, read `REPO_ROOT` | `module file: <tmp>/snap/specfuse/loop/loop.py`; `REPO_ROOT: <the repo root>` — **the split the migration needs, with no path rewriting** |
| `PYTHONPATH=<copy>` with `python3 -c` | loaded **the working tree** — cwd is `sys.path[0]` for `-m` and `-c`, so `PYTHONPATH` alone cannot pin |
| A script inserting the copy at `sys.path[0]` | loaded **the copy** — a script invocation puts the script's own directory on the path, not the cwd |
| `main()` executed from the copy | parsed arguments and printed usage normally; `specfuse/loop/data/` travels inside the package |
| `build_provenance` on that run | fired: `"This command is measuring the INSTALLED build, not your checkout — results can be confidently wrong rather than failing."` |

Two of these are load-bearing and are written into `WU-08`'s body so they are
not rediscovered by failing. **`SPECFUSE_DIR = Path(".specfuse")` at
`loop.py:118` is cwd-relative**, which is the single fact that makes this
migration small rather than a path-rewriting project. And **the invocation form,
not the environment, is what decides which copy wins** — a design that exports
`PYTHONPATH` and expects a pin will silently keep running the working tree,
which is the failure this whole gate is about.

The fourth row is definition-of-done bullet 4, observed rather than predicted.

## Decisions, and why

### 1. A content-addressed pin materialized outside the working tree — not `pip install`

The roadmap says "installed copy". I read that as a property — *the running
import surface is decoupled from the working tree* — rather than as a
prescription of `pip install`. Materializing a copy keyed on `HEAD^{tree}`
delivers that property in milliseconds, with no build backend, no network, no
wheel, and no `site-packages` state to reconcile against the `.venv`'s existing
**editable** install of `specfuse_loop-0.11.0`, which resolves back to the
working tree and would otherwise have to be uninstalled first. If you want a
literal `pip install .` per run instead, that is a scope change to T08 and it
should be decided now, not discovered.

**Outside the working tree, not `.gitignore`d inside it.** Six repo-sweeping
surfaces would otherwise have to learn about the pin: `git add -A` in the squash
path, `leak-scan`, `ruff`, the deliverable-presence guard, `specfuse lint`'s
sweep — and, circularly, the `HEAD^{tree}` hash the pin is keyed on, which a
pin inside the tree would change. A `.gitignore` entry solves exactly one of the
six. **Affects T08.**

### 2. Detection stays; only the response moves

`driver_edit.py` keys on a commit's real diff precisely because a WU's
`produces:` and `produces_driver_helper` are author-supplied and WARN-only. That
reasoning is untouched by pinning, and a driver edit must still be *recorded* —
the gate-completion summary still needs to name every edit the gate made. T08
retires the **halt**, not the detection, and `driver_edit.py` is in its **Do not
touch**. **Affects T08.**

### 3. The unpinned path stays byte-identical

A downstream project with no `specfuse/loop/` in its working tree gets no pin,
no re-entry, no new event, no changed behaviour — the same
silence-by-construction posture `build_provenance` already takes. This is the
fail-safe direction: gate 3 *narrows* an existing halt, so the adjacent risk is
under-halting, and keeping the unpinned path exactly as it is bounds it.
**Affects T08** (definition-of-done bullets 3, 6 and two acceptance criteria).

### 4. The cost is announced, not inferred

Definition-of-done bullet 5 requires the driver to *say*, at the moment it
declines to halt, that the edit takes effect at the next run. An operator must
never have to infer from silence which build verified their gate — that
inference is the #1040 failure with extra steps. **Affects T08.**

### 5. Gate 3 pays exactly one restart, and that is by design

The driver running gate 3 is the pre-T08 driver. T08's squash touches
`specfuse/loop/loop.py` while `G3-CLOSE` is still pending, so the old halt fires
once and the operator restarts — and the restarted driver is the first one to
pin, which makes the terminal close the first close in this repository to run
from a pinned build. That is a good property, not an accident, and both `WU-08`
(so nobody tries to prevent it from inside the unit) and the close (which
reports the count against the prediction) say so. **Affects T08 and
WU-90-gate-3-close.**

## How gate 3's `feature_oracle` advances gate 2's

Gate 1: `python3 -m unittest tests.test_lazy_baseline_e2e -q`.
Gate 2: `python3 -m unittest tests.test_tiered_verification_e2e -q`.
Gate 3: `python3 -m unittest tests.test_installed_copy_driver_e2e -q`.

Gate 1's and gate 2's oracles both drive `loop.run()` **in process**, with
dispatch monkeypatched (`tests/_workspace.py`'s `integration_workspace`, and
`tests/_loop_loader.py`'s `load_loop`). That is what lets them assert richly on
*what the driver ran* — which gates, in which tier, in what order, and whether
the gate reached its close. It is also exactly what makes them blind to *which
build ran it*: the answer is fixed to the test process's own imports before the
first assertion executes. **An in-process oracle cannot observe its own
provenance.**

Gate 3's property *is* that provenance, so its oracle is the first in this
feature that cannot be in-process, and `GATE-03.md` makes out-of-process
construction binding on it: a real driver subprocess launched from a
materialized pin, over a temporary scaffold repo, with a stub `claude` on `PATH`
(`CLAUDE_CMD` at `loop.py:288` resolves `argv[0]` through `PATH`, so this needs
no new dispatch seam), asserting only on that subprocess's exit code and the
`events.jsonl` it writes. `WU-08` carries the check that keeps it honest —
`grep -n "import specfuse.loop.loop\|load_loop" tests/test_installed_copy_driver_e2e.py`
returns nothing — because an in-process assertion measures the working tree,
which is the copy this gate migrates away from.

Three claims it carries that gate 2's oracle cannot phrase:

1. **Identity of the executing build.** The run records the build it executed
   and that build is the pin, not the working tree. Gate 2's oracle has no
   vocabulary for this question.
2. **Absence of the halt across a real driver edit.** A unit whose squash
   actually touches `specfuse/loop/loop.py` is followed by the next unit's
   dispatch in the same process, with no `halted: true` event and no exit 3.
   Gate 2's oracle monkeypatches dispatch and never squashes a driver edit, so
   it never reaches the halt seam at all.
3. **A moving working tree does not move what the run executes.** Mutating
   `specfuse/loop/loop.py` mid-run leaves the pinned process's behaviour
   unchanged. This negative is what makes "pinned" mean something, and it is
   unstatable in an oracle whose subject and whose runner are the same import.

There is a fourth advance worth naming, because it is the one gate 2's own
retrospective asked for. Gate 2's lesson 2 records that its oracle "asserts on
which *gates* execute per attempt … rather than on whether an attempt ran less
than the whole suite, which is the thing the feature is for" — an oracle that
could not see T05's missing wiring. Gate 3's oracle asserts on the driver's
**observable process behaviour end to end** rather than on its scheduling
decisions, which is the class of assertion that could have caught it. That does
not retroactively fix T05 (see Q4), but it is the shape the feature converged
on, and it is worth stating that the convergence was forced by a defect rather
than designed.

## Roadmap-anchor check

`PLAN.md`'s `roadmap_goal` ends: "*and a unit that edits the driver no longer
halts the run.*" The roadmap detail section's `**Goal.**` is more specific:
"*The driver runs from an installed copy so a unit editing `specfuse/loop/` does
not halt the run.*"

| Drafted unit | Anchored to | Verdict |
|---|---|---|
| T08 installed-copy / pinned driver | "a unit that edits the driver no longer halts the run"; "runs from an installed copy" | **On anchor** |
| G3-CLOSE | methodology (terminal close), not the roadmap goal | n/a — closing unit |

Three findings:

1. **Gate 3 is the only gate in this feature with a one-to-one anchor.** Gate 2
   carried T07 off-anchor by operator decision; gate 3 carries nothing extra.
   That is a consequence of the atomicity constraint rather than a virtue, but
   it does mean there is no scope here to trim.
2. **"Installed copy" is read as a property, not as `pip install`.** Decision 1
   above. If you read the roadmap sentence literally, T08 as drafted does not
   satisfy it and you should say so at arm time; I believe the property is what
   the sentence is for, and the literal reading costs a build step per run for
   nothing.
3. **The roadmap row's title is still stale.** Row and detail heading both read
   "Tiered verification and a **cached** baseline probe"; `PLAN.md` and gate 1
   say **lazy**. `GATE-02-REVIEW.md` flagged this at gate 2's arming and it was
   not fixed. Editing the roadmap is outside this unit's `produces:`, so it is
   flagged again rather than fixed. It is a one-line edit whenever someone is in
   that file.

## Open questions

Each is answerable at arm time; none blocks drafting.

- **Q1 — pin the build, or auto-re-exec from the fresh tree?** *(affects
  `WU-08`.)* The drafted design pins at startup, so every unit in a gate runs
  the same build and a driver edit takes effect next run. The alternative is
  smaller: at the point the halt fires today, `os.execv` the resume command
  instead of returning exit 3. That also removes the operator interrupt, and it
  keeps the property that a driver edit takes effect immediately. It has no
  exec-loop risk — `driver_edits` is per-process and a fresh process starts
  empty. What it does *not* do is address #1040 at all, and it keeps the driver
  a moving target inside a gate: gate 2's retrospective shows T05 running a
  T04-only driver and T06/T07 a T04+T05 driver, which is why that gate's
  per-attempt tier path differed across its own attempts and made the
  measurement hard to read. **My recommendation is the pin**, on the
  commensurability argument — a gate's units should be measured by one build —
  but the re-exec is a coherent, cheaper choice and it is the one that keeps
  today's close semantics. This is the decision to make before arming, not
  after.
- **Q2 — is "one run late" acceptable for a close whose own guards the gate just
  changed?** *(affects `WU-08` definition-of-done bullet 5, and
  `WU-90-gate-3-close`.)* Under a pin, a gate that changes a driver `assert_*`
  guard is closed by the *previous* build's guards. This feature does not hit
  it — T08's own restart means gate 3's close runs the new driver (Decision 5) —
  so the question is about future gates. The narrow fix, if you want one, is to
  re-pin at the gate boundary rather than only at run start; that reintroduces
  one process transition per gate instead of one per driver-editing unit, which
  is 1 instead of 4 for a gate like gate 2. I did not draft it, because it is a
  scope addition to a unit whose atomicity is already the binding constraint.
- **Q3 — `planned_cost_usd`.** *(affects `PLAN.md`, not a WU.)* The frontmatter
  still says **$26.00** — gate 1's five units plus the then-scaffolded gate-3
  close. Gate 3's drafts add **$14.50** (T08 $6.50, close $8.00), taking the WU
  sum to **$56.00**; `lint_plan.py` WARNs at a 115% delta. Feature spend to date
  is $32.79 across gates 1 and 2, and gate 1's `arm_predicate_evaluated` already
  fired `budget_projection` against the $26.00 figure once. This is a stale plan
  figure, not an overrun — measured against the WU sums the drafts declare, gate
  1 came in 17.7% under and gate 2 16.9% under. `GATE-02-REVIEW.md` Q4 left the
  number to you and it is still unresolved; this unit's scope on `PLAN.md` is the
  gate-3 graph list and nothing else, so it is left to you again. $56.00 is the
  arithmetic.
- **Q4 — where does T05's dead changed-file map go? It is not gate 3.** *(affects
  no drafted WU — deliberately.)* Gate 2's `## What the loop did NOT verify`
  item 1 names this as "the natural first item for `G2-PLAN` to weigh against
  gate 3's atomicity constraint", so here is the weighing.

  The facts, from gate 2's own measurements: `write_changed_file_test_map` has
  exactly one occurrence in the repository — its own `def` line — so the map is
  never built, the changed-file half resolves to `None` on every attempt, and
  because an unresolvable half forces the *full* command rather than degrading
  to the declared set, it **cancels the working half**. Measured: 6.9s per
  attempt becomes 172.9s, plus +13.9s on every broad run and a 27× larger
  `.coverage` file for a map nothing reads. Gate 2 as run cost 38.4s more than
  having no tier at all. **Gate 3's own T08 attempt will pay that too**, since
  T08 touches `specfuse/`.

  **I did not draft it, and I recommend you do not arm it into gate 3.** Three
  reasons. It is unrelated to the migration, so folding it into T08 makes T08
  non-atomic in the one dimension `[FEAT-2026-0019/G1]` warns about. Gate 3's
  `feature_oracle` cannot observe it — the oracle asserts on which build runs,
  and the map has no bearing on that — so a second unit here would be a unit
  whose gate has no exit oracle for it, which is the hollow-pass shape gate 2
  just paid for. And adding a second substantive unit to gate 3 contradicts the
  constraint this feature was structured around; if you want it inside this
  feature it should be a **gate 4**, which would demote gate 3's close from
  terminal `close` to `close-intermediate` and add a third `plan-next`.

  My recommendation is a **follow-up feature**, and it is probably a one-line
  feature: gate 2's retrospective identifies the cheap fix as flipping T05's
  unresolvable-half behaviour from "run the full command" to "degrade to the
  declared set" — still strictly safe, still more than nothing, and worth ~166s
  per driver-touching attempt. Wiring `write_changed_file_test_map` into the
  broad run is the larger, correct fix. Either way the terminal close should
  carry it into `FOLLOW-UPS.md` if it has not landed by then. **This is a real
  cost the feature is choosing to leave on the table, and it is your call, not
  mine.**

## Lint state of the drafts

`python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0109-tiered-verification`
exits **0** with **zero ERROR findings**. The graph was re-read after the edit
and gate 3 reads `T08` (`WU-08-installed-copy-driver.md`, `depends_on: []`) then
`G3-CLOSE` (`WU-90-gate-3-close.md`, `depends_on: [FEAT-2026-0109/T08]`), both
files present on disk. `grep -n "feature_oracle" GATE-03.md` returns line 4.

The WARNs are known and none is a defect in the drafts:

- `WU-08` declares `produces` paths already delivered by `done` gate-1 and
  gate-2 units (`specfuse/loop/loop.py` by T01, the event schema by T06). Both
  are stated as incremental edits in `WU-08`'s body, which is the remedy the
  WARN names; gate 1's T02/T03 and every gate-2 unit carry the identical WARN.
- `WU-90-gate-3-close` declares `RETROSPECTIVE.md`, already delivered by
  `G1-CLOSE-INTERMEDIATE`. Its body states the incremental edit — one `## Gate N`
  section per close, gate 1's and gate 2's not editable.
- Ceremony proportionality: 8 substantive units across 3 gates. Gate 3's
  atomicity constraint is why this feature is three gates rather than one; the
  WARN has no bearing on the drafts.
- The `planned_cost_usd` delta — Q3 above.

The `oracle_env` WARN that `WU-90-gate-3-close` carried as a scaffold is gone;
the field is now set, along with the terminal-close obligations
(`close-discipline.md` §2's `FOLLOW-UPS.md` path, §3's three-gate enumeration and
`CHANGELOG.md` append, and §5's per-criterion state) that the placeholder body
did not name.
