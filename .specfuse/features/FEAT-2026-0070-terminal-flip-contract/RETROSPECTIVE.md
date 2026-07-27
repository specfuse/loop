# RETROSPECTIVE — FEAT-2026-0070, terminal-flip contract

Feature-level record. This pass closes **gate 1 only** — a non-terminal close. No
feature-arc verdict is written here, no terminal surface is flipped, and `PLAN.md`
stays `active` by design. Gate 2 (#241, auto-close's skipped deferred-verification
enumeration) is drafted by `G1-PLAN` immediately after this WU, and the terminal
`G2-CLOSE` writes the feature-arc verdict and reconciles the whole-feature cost.

---

## Gate 1 — a correctly-closed feature reaches `done` through the driver, from any legitimate starting state

Gate 1 shipped four work units against three issues (#226 row breadth, #243 the
`met_locally` dead end, and the pre-registered `lint_plan` exempt-set fix from
`[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]`). Every one passed on its first recorded
attempt.

| WU | type | attempts | planned | actual | delta | outcome |
|---|---|---|---|---|---|---|
| T01 `row-flip-breadth` | implementation | 1 | $2.50 | $0.914345 | −63.4% | passed |
| T02 `verdict-recheck-primitive` | implementation | 1 | $3.50 | $1.203202 | −65.6% | passed |
| T03 `accept-hedged-close-skill` | implementation | 1 | $2.50 | $1.543230 | −38.3% | passed |
| T04 `lint-verdict-exempt-set` | implementation | 1 | $1.50 | $0.988023 | −34.1% | passed |
| **substantive subtotal** | | **4** | **$10.00** | **$4.6488** | **−53.5%** | |
| G1-CLOSE-INTERMEDIATE | close-intermediate | 1 (this session) | $4.50 | not yet recorded | — | in progress |
| G1-PLAN | plan-next | 0 | $6.00 | not yet run | — | pending |

Dispatch order was **T01 → T02 → T04 → T03**, not T01–T04: T03 is the only WU with a
dependency (`depends_on: [T02]`), and T04 had none, so the driver took T04 first. T03
then hit an infra kill and was recovered before its recorded attempt — see the
failure-class breakdown below.

### T01 — row flip from any non-`done` status (#226)

**What shipped.** `fire_terminal_flips` previously flipped the roadmap row only on the
`active → done` transition. It now reads the row's current Status cell and replaces
whatever non-`done` value it finds (`specfuse/loop/loop.py:3200-3218`), so an
`autonomy: auto` feature that self-dispatched from a `planned` row reaches `done`
instead of escalating `roadmap_row_not_done` on a correct close.

**What worked.** The change is four lines and three tests
(`TestRowFlipBreadth`: `planned → done`, `active → done` still fires, second call on a
`done` row is a no-op). Passing first try at 37% of estimate is what a well-scoped
precondition-broadening WU should look like.

**What failed.** Nothing.

**Unclaimed edge, found at close, not a regression.** The replacement is
`status_cell.replace(current_row_status, "done", 1)`. When the Status cell is **empty**,
`current_row_status` is `""` and `str.replace("", "done", 1)` inserts `done` at offset 0
of the cell rather than replacing anything — it happens to produce the right text here
(an empty cell plus `done`), but it is right by accident, not by construction. No test
covers an empty Status cell. Low severity; noted so a future reader does not have to
re-derive it.

### T02 — the out-of-band verdict-recheck primitive

**What shipped.** `recheck_terminal_verdict(feature_dir, repo_root)` at
`specfuse/loop/loop.py:3281`, plus the `--recheck-verdict FEATURE_ID` CLI flag at
`loop.py:5723`. It locates the terminal gate's `type: close` WU, re-reads its verdict
**from disk**, and — only if `verdict_permits_terminal_flips` says yes — calls the
existing `fire_terminal_flips` unchanged (`loop.py:3339`). It writes no surface itself.

**What worked.** This is the WU that carries the feature's central constraint, and its
shape honours it exactly: a *caller*, not a second writer. The docstring says so, the
implementation does so, and the close audit below confirms it independently.

**It closes a gap none of the three issues reported.** `fire_terminal_flips` runs at
close-WU-*outcome* time, inside the dispatch loop. Once the close WU is `done` the
driver never re-dispatches it, so a verdict legitimately upgraded post-close is never
re-read — which is exactly what happened to FEAT-2026-0069 and forced three surfaces to
be hand-flipped. That defect existed before #243 was filed and had no issue of its own.

**What failed.** Nothing.

### T03 — `/accept-hedged-close`

**What shipped.** A propose-and-confirm operator skill
(`plugins/specfuse/skills/accept-hedged-close/SKILL.md`, byte-identical vendored copy
under `.specfuse/skills/`), plus 19 assertions in
`tests/test_accept_hedged_close_skill.py`. It surfaces the close-discipline §2 follow-up
record, requires a one-line operator reason and explicit acknowledgment of the standing
follow-ups, writes an acceptance record into `RETROSPECTIVE.md`, sets the close WU's
`verdict` to `met`, and then hands the flip to `--recheck-verdict`.

**What worked.** The load-bearing criterion — *the skill does not write terminal state* —
was expressed as a **grep-shaped assertion over the skill text**, not as prose in the WU
body, and the test suite carries a positive control
(`test_forbidden_pattern_fires_on_a_real_positive_instruction`) proving the forbidden
pattern actually fires on an instruction that would violate the rule. That control is the
difference between a guard and a guard-shaped no-op.

**What failed.** One infra kill mid-attempt, recovered by the operator (branch commit
`aa20e4a`); the gate baseline was re-probed clean (`cc4cdc6`, matching `GATE-01.md`'s
`probed_at: 03:00:23`) before the re-dispatch that passed.

**The surprise, and it is the one worth carrying forward.** Step 5 of the skill edits the
close WU's `verdict:` frontmatter **from `met_locally` to `met`** so that
`verdict_permits_terminal_flips` — which returns `True` for `met` and nothing else
(`loop.py:133-135`) — recognizes it. That is a legitimate way to reuse the one owner
without weakening it. But it means the accepted hedge survives **only in prose**: after
acceptance, the WU frontmatter is byte-identical to a close that genuinely met every
criterion. Nothing machine-readable distinguishes "met" from "hedged, accepted by an
operator on a stated reason". See *What I'd change*.

### T04 — `lint_plan`'s dispatch-state exemption

**What shipped.** `in_progress` and `in_review` added to the close-WU verdict-exempt set
in `specfuse/loop/lint_plan.py:626-635`, with a comment naming the real owner
(`assert_verdict_well_formed`, which runs at outcome time). Three tests in
`tests/test_lint_plan_verdict_exempt.py`.

**What worked.** The satisfiability probe the plan deferred into this WU's own acceptance
criteria was the right call: `lint_plan` on a tree in its intended final state reports
zero new findings, because a close WU is only `in_progress` mid-dispatch and every
committed close WU in this repo is `done`.

**What failed.** Nothing. $0.99 against $1.50.

**Why it is not a strictness change.** The defect was **diagnostics**: a close WU that had
not yet written its verdict failed plan-lint mid-dispatch with a message about the WU,
not about the missing verdict. The contract was enforced in two places and the earlier
one could not explain the later one's requirement. Promoted as a named defect class — see
`LEARNINGS.md`.

### Failure-class breakdown

**Driver-recorded non-passing attempts: zero.** All four `attempt_outcome` events in
`events.jsonl` carry `outcome: passed`, `failure_class: null`, `failure_signature: null`,
`re_arm_count: 0`. No WU consumed a second attempt; no `blocked` was emitted; no
closing-guard refusal occurred.

| failure class | count | WUs |
|---|---|---|
| *(any driver-recorded class)* | 0 | — |
| infra kill, no `attempt_outcome` emitted | ≥1 | T03 |

The section is written rather than omitted because "every WU passed first try" is true of
the **record** and not quite true of the run. T03 was killed mid-attempt by
infrastructure, not by a gate: the branch carries an explicit recovery commit
(`aa20e4a`, *"recover T03 after an infra kill mid-attempt"*), and the ten-minute gap
between T04's completion (02:52:15Z) and T03's `task_started` (03:02:19Z) is that
recovery plus the clean baseline re-probe.

**The measurement consequence is the durable part.** An attempt terminated before it
reaches an outcome emits no `attempt_outcome` event, so its tokens are invisible to every
consumer of `events.jsonl` — this retrospective's cost analysis, `events_stats.py`, and
`/learnings-suggest` alike. Gate 1's actual spend is therefore a **lower bound**,
understated by one killed T03 session of unknown size. Promoted to `LEARNINGS.md`; a
close that reconciles cost from `events.jsonl` should say so rather than present the sum
as complete.

### Surprises

1. **The one-owner property held, but the audit that proved it found a different
   defect.** `grep -c "def fire_terminal_flips"` returns `1` and the `→ done` transition
   really does have exactly one writer — but grepping the *surface* rather than the
   *function* surfaced `loop.py:4462`, which writes `PLAN.md` `status: complete`. See the
   one-owner audit below. This is the single most valuable thing this close produced, and
   no gate test could have produced it: the tests assert what the owner does, not what
   else touches the surface it owns.
2. **The acceptance path launders the hedge.** T03 works exactly as specified and still
   loses information — the frontmatter that recorded `met_locally` is overwritten with
   `met` (T03 section above).
3. **`.claude/skills/` did not gain a symlink for the new skill.** The plugin copy and the
   vendored copy are both present and in sync, but this repo's local discovery directory
   has no `accept-hedged-close` entry — and it is missing `adopt-feature` and
   `migrate-to-auto-close` too, so the directory has been drifting for a while rather
   than failing on this feature. Not fixed here (outside T01–T04's `produces:` and outside
   this WU's scope); recorded as a follow-up.
4. **All four estimates were high, uniformly.** Not one WU exceeded 66% of its estimate.
   That is a calibration signal about *driver-internals* WUs with existing guard tests —
   the plan explicitly estimated them above the observed $1.33 median *because* they touch
   driver internals, and the opposite was true: an existing test file to extend makes the
   work cheaper, not dearer.

---

## One-owner audit (`[FEAT-2026-0023/G1-CLOSE]`)

This gate's central constraint is that terminal-state flips have exactly ONE driver-side
owner called identically by every close path. Audited fresh in this session.

**Result: the constraint holds for the `→ done` transition.** One adjacent pre-existing
defect on the same surface was found and is reported below rather than smoothed away.

| check | command | observed |
|---|---|---|
| single definition | `grep -c "def fire_terminal_flips" specfuse/loop/loop.py` | `1` |
| `PLAN.md status: done` writers | `grep -rn 'write_frontmatter_field(' specfuse/ \| grep -i status` | one — `loop.py:3260`, inside `fire_terminal_flips` |
| terminal gate `status: passed` writers | same grep, plus `grep -n "set_gate(" specfuse/loop/loop.py` | one — `loop.py:3177`, inside `fire_terminal_flips`. `set_gate` has 4 call sites (`4575`, `4610`, `5346`, and the `4698` comment) and **every one passes `"awaiting_review"`**; nothing calls it with `passed` |
| roadmap row `→ done` writers | `grep -rn "roadmap_path.write_text" specfuse/loop/` | one — `loop.py:3218`, inside `fire_terminal_flips`. `auto_archive_feature` (`loop.py:2945`) *reads* the Status cell and writes only the Detail cell + archive file |
| T02 is a caller, not a writer | read `recheck_terminal_verdict`, `loop.py:3281-3345` | writes nothing; single tail call to `fire_terminal_flips` at `loop.py:3339` |
| T03 writes no terminal surface | `python3 -m unittest discover -s tests -p test_accept_hedged_close_skill.py` | `Ran 19 tests` `OK` — includes the forbidden-pattern assertion and its positive control |
| CLI entry point reaches the primitive | `python3 .specfuse/scripts/loop.py --recheck-verdict FEAT-2026-0070` | `FEAT-2026-0070/G2-CLOSE status is 'draft' (not done)`, exit `0`, no file modified |

### Adjacent writers of the same surfaces — named so the next reader does not re-derive them

None of these participate in the `→ done` transition, so none splits ownership of the
flip. Two are by design; one is a defect.

- **`revert_terminal_surfaces` (`loop.py:3086-3125`) — by design.** Writes `PLAN.md`
  `done → active` and the roadmap cell `done → active` after a hedged verdict (#195).
  Strictly the inverse direction of the same surface set, deliberately kept symmetric with
  what `fire_terminal_flips` owns. Predates this gate; untouched by it.
- **`/abandon-feature` and `/arm-gate` — by design, with one soft edge.** `/abandon-feature`
  writes gates `passed` and PLAN/roadmap `abandoned`; it never writes `done` and explicitly
  refuses to touch `done` WUs or `passed` gates. `/arm-gate` marks the *completed*
  (intermediate) gate `passed` at the human checkpoint. The soft edge: `/arm-gate` carries
  no explicit terminal-gate guard, so on a terminal gate it would be a second writer of
  the terminal gate status. In practice the skill exists to arm a *next* gate and there is
  none on a terminal gate, but nothing refuses. Worth a one-line guard; not this WU's
  scope.
- **`loop.py:4462` — a defect, and it corrupts the surface `fire_terminal_flips` owns.**

  ```python
  gate = next((g for g in gates if g.status != "passed"), None)
  if gate is None:
      print(f"{feature_id}: all gates passed — feature complete.")
      backend.on_feature_complete(feature_id)
      write_frontmatter_field(feature_dir / "PLAN.md", "status", "complete")
      return 0
  ```

  `complete` is **not** a recognized feature status:
  `lint_plan.VALID_FEATURE_STATUS = {"planned", "active", "blocked", "deferred", "done",
  "abandoned"}` (`lint_plan.py:49`), and `lint_plan.py:498` raises
  `PLAN.md frontmatter status 'complete' is not a recognized feature status` on it.
  Re-running the driver against a finished feature (`--feature FEAT-XXXX`, or an
  `autonomy: auto` poll) therefore **overwrites the `done` that `fire_terminal_flips`
  just wrote with a value the rest of the system rejects** — plan-lint errors, and
  `/wrap-feature`, which refuses on any non-`done` PLAN, refuses a feature that was
  correctly closed. The roadmap row would still read `done`, so the two surfaces
  disagree: the exact failure shape #195 and #49 exist to prevent.

  **Evidence and its limits.** Established statically (the write, the valid-status set,
  the lint rule, and `find_feature`'s treatment of `complete` as merely not-`active`).
  No feature on disk currently carries it — `grep -h "^status:" .specfuse/features/*/PLAN.md`
  returns 33 `done`, 1 `active`, 1 `blocked`, and zero `complete` — and no test asserts
  the write (`tests/test_loop_orchestration.py:296` uses `"complete"` only as a
  convenient not-`active` fixture value). **This session did not execute the path**, so
  the finding is a confirmed code-reading, not an observed reproduction. It needs an
  issue and a one-line fix (write `done`, or drop the write — `fire_terminal_flips` has
  already set it); the reproduction belongs in the fix's red test, not here.

  Reported rather than fixed: this is a `close-intermediate`, T01–T04 did not introduce
  it, and repairing driver behaviour inside a retrospective WU is the "while I was here"
  drift `result-contract.md` §2 forbids.

**Verdict on AC6: the one-owner property held.** No close path, no skill, and no new
entry point writes a terminal surface outside `fire_terminal_flips`. The escalation
trigger ("more than one terminal-state writer") is read as governing the `→ done`
transition, which is what `[FEAT-2026-0023/G1-CLOSE]` names and what #49 broke; a literal
reading covering every write of those bytes in either direction would have been
unsatisfiable on arrival, since `revert_terminal_surfaces` predates this feature by
several gates. The `loop.py:4462` finding is raised here in full so a reviewer can
overrule that reading.

---

## Cost analysis

**Baseline: the as-drafted figure.** Gate 1 was planned at **$20.50** — T01 $2.50, T02
$3.50, T03 $2.50, T04 $1.50, `close-intermediate` $4.50, `plan-next` $6.00 (`PLAN.md`
§ Notes, *Cost note*). Per `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` no re-baselining is
applied: nothing was re-planned mid-gate, and this figure is the honest one.

**Actual, from `events.jsonl` `task_completed` payloads:**

| | planned | actual | delta |
|---|---|---|---|
| substantive (T01–T04) | $10.00 | **$4.6488** | **−$5.3512 (−53.5%)** |
| ceremony (this WU + `G1-PLAN`) | $10.50 | not yet recorded | — |
| **gate 1 total** | **$20.50** | **≥ $4.6488 so far** | open until `G1-PLAN` completes |

Per-WU actuals: T01 $0.914345 (405.2s, 6,708 output tokens), T02 $1.203202 (579.4s,
12,881), T03 $1.543230 (471.4s, 16,635), T04 $0.988023 (440.0s, 7,963). Total recorded
dispatch time 1,896s ≈ 31.6 min.

**The delta, named.** The substantive estimates were **too high by 53.5%, uniformly** —
actual spend came in at less than half of plan, and every
WU landed between 34% and 66% of its estimate, so this is a systematic bias, not one
lucky WU. `PLAN.md` justified estimates above the observed $1.33 median on the grounds
that all four touch driver internals with existing guard tests. That reasoning inverted
in practice: an existing test file to extend and a single well-located function to change
make a driver-internals WU **cheaper** than a greenfield one, not dearer. A future plan
should treat "extends an existing guard test file" as a discount, not a premium.

**Two caveats on the actual, both understating it.**

1. **The killed T03 attempt is not in the sum.** No `attempt_outcome` event, therefore no
   `cost_usd`. $4.6488 is a lower bound by one unknown session.
2. **The ceremony half is where this gate's cost will actually land, and $6.00 is
   probably low.** `[FEAT-2026-0069/GATE-1-ARM]` records two independent `plan-next`
   observations — $15.65 (FEAT-2026-0049) and $16.44 (FEAT-2026-0069/G1-PLAN) — against
   which the $6.00 planned here sits well below both, and two `close-intermediate`
   observations ($5.67, $10.01) against $4.50 here. If those hold, gate 1 closes *over*
   $20.50 despite the substantive half coming in at less than half of plan, and the
   overrun will be attributable entirely to ceremony. `G2-CLOSE` reconciles the whole
   feature against the $32.00 plan and should report the substantive and ceremony halves
   separately — a single blended number would hide both signals.

**The open plan-lint WARN is expected and documented.** `lint_plan` reports
`planned_cost_usd $32.00 differs from sum of WU planned costs $25.50 (delta 20%,
threshold 10%)`, because gate 2's substantive WUs do not exist until `G1-PLAN` drafts
them ($20.50 gate 1 + $5.00 `G2-CLOSE` = $25.50 against a $32.00 plan that anticipates
~$11.50 of gate 2). `PLAN.md` § Notes pre-declares this. Exit code is `0`.

---

## What the loop did NOT verify

Every criterion below was reported green by its WU and by the driver's gate set, and each
is genuinely green for what it asserts — the entries name the gap between what the
assertion proves and what the criterion claims.

**1. T03's behavioural criteria (AC4, AC5, AC6, AC7, AC9) — a skill is verified by an
operator running it.** This is the entry AC4 anticipated, and it is the honest one.

- **Verified structurally, and really verified:** the skill directory exists with valid
  frontmatter (`name`, `description`); both copies are byte-identical
  (`diff .specfuse/skills/accept-hedged-close/SKILL.md
  plugins/specfuse/skills/accept-hedged-close/SKILL.md` → no output; `cmp` semantics, and
  `tests/test_skills_vendored_in_sync` passes in the full run); the skill text contains no
  instruction to write `PLAN.md status`, a gate status, or the roadmap row, and the
  forbidden-pattern matcher is proven to fire on a real positive instruction; the text
  names `--recheck-verdict` as the mechanism and states it never calls
  `fire_terminal_flips` itself.
- **Awaiting a real invocation:** that the skill, executed by an agent, actually *refuses*
  on `met` / `not_met` / a non-`done` close WU; actually *re-prompts* on an empty
  rationale; actually *writes* an acceptance record carrying every follow-up forward
  verbatim; and actually *leaves the three surfaces untouched* while the flips fire. All
  19 tests are assertions over SKILL.md **text** — they prove the prose says the right
  thing, not that an agent following it does the right thing.
- **Why deferred:** no dispatched session can verify an interactive propose-and-confirm
  skill; its oracle is an operator at a terminal.
- **Where it actually gets verified:** one named operator run of `/accept-hedged-close`
  against a real feature standing at `met_locally`. This is the same gap
  `[FEAT-2026-0069/G2-CLOSE]` names for `/derive-monitoring` — "a passing fixture and an
  agent-executed skill are different oracles" — and the same remedy applies: schedule it
  as one post-merge operator run, not as another test.

**2. The `--recheck-verdict` CLI path had no test; this close ran it.** Every test in
`TestVerdictRecheck` (`tests/test_terminal_flips.py:515-645`) calls
`recheck_terminal_verdict()` directly. Nothing exercised `main()`'s argument parsing,
`_resolve_feature_dir`, the printed `reason`, or the `Modified:` line — the wiring between
the flag and the primitive was unverified. This session closed the gap for the refusal
path only: `python3 .specfuse/scripts/loop.py --recheck-verdict FEAT-2026-0070` printed
`FEAT-2026-0070/G2-CLOSE status is 'draft' (not done)` and exited `0`, writing nothing.
**Still unverified:** the *firing* path through the CLI — flag → `_resolve_feature_dir` →
primitive → `fire_terminal_flips` → the `Modified:` line — because exercising it requires
a feature whose terminal close WU is `done` with `verdict: met` and surfaces still
un-flipped. Cheapest fix: one CLI-level test over a temp feature tree, which belongs in
gate 2 or a follow-up, not in a retrospective.

**3. The `loop.py:4462` `status: complete` finding is a code-reading, not a
reproduction.** Stated in full in the one-owner audit above. The write, the invalid
value, and the lint rejection are all established from source; the end-to-end sequence
(close a feature, re-run the driver on it, observe PLAN.md flip `done → complete`, watch
plan-lint fail) was not executed. It gets verified in the red test of whatever fixes it.

**4. `/arm-gate`'s missing terminal-gate guard is likewise unexercised.** No test asks
what `/arm-gate` does when pointed at a terminal gate; the claim above is read from the
skill text.

---

## Consumer-visible contract changes (`close-discipline.md` §3)

> **This list is submitted for human acknowledgment at the gate-1 review-and-arm
> checkpoint; it is not self-acknowledged.** Gate 1 halts at `awaiting_review` and gate 2
> cannot be armed without a human passing through `/arm-gate` — that checkpoint is where
> the signature goes (`GATE-01.md` § *Reflection notes*, `GATE-02-REVIEW.md` § arming
> checklist). This mirrors the precedent set by FEAT-2026-0069's gate-1 close. A
> dispatched session cannot obtain the acknowledgment itself; routing it to the mandatory
> human checkpoint immediately downstream is not the same as closing on silence, and the
> reviewer may reject this close on the list alone. **Item 1 is a behaviour change for
> features already on disk — read it before arming gate 2.**

**This is not `n/a`.** Gate 1 makes four consumer-visible changes.

| # | surface | change | breaking? | evidence |
|---|---|---|---|---|
| **1** | roadmap row flip at terminal close | **The row now flips to `done` from *any* non-`done` status, not only from `active`.** A feature whose row reads `planned` (the `autonomy: auto` self-dispatch case) previously stayed `planned` through a correct close and escalated `roadmap_row_not_done`; it now reaches `done`. Anything downstream that relied on "a `planned` row is never rewritten by the driver" changes behaviour | **behaviour change, not an API break** — it makes the driver flip *more* rows, never fewer; an `active → done` close is bit-identical to before | `loop.py:3200-3218`; `TestRowFlipBreadth` (3 tests) incl. the `active → done` regression guard |
| **2** | driver CLI | **New flag `--recheck-verdict FEATURE_ID`.** Re-reads the named feature's terminal close WU verdict from disk and fires the terminal flips if it now permits them, without re-dispatching. Prints `reason` and, when it fires, `Modified: <paths>`; exits `0` on a refusal as well as on a fire | additive — new flag, nothing renamed or removed | `loop.py:5723-5739`; smoke-run this session, exit `0` |
| **3** | driver Python surface | **New public function `recheck_terminal_verdict(feature_dir, repo_root) -> dict`** returning `{fired: bool, reason: str, modified: list[Path]}`. `fire_terminal_flips`' signature and behaviour are unchanged | additive | `loop.py:3281` |
| **4** | skills catalog | **New skill `/accept-hedged-close`**, shipped in the `specfuse@specfuse` plugin and vendored to `.specfuse/skills/`. Projects installing or upgrading the plugin gain it. `/wrap-feature`'s refusal on non-`done` features is unchanged — this is the path that makes such a feature `done` first | additive — no existing skill changed behaviour | `plugins/specfuse/skills/accept-hedged-close/SKILL.md`; 19 tests |
| **5** | `lint_plan` | **`in_progress` and `in_review` close/close-intermediate WUs no longer ERROR on a missing `verdict`.** Both were previously rejected mid-dispatch with a message about the WU rather than about the missing verdict. Strictly fewer findings on the same tree | additive-permissive — **no tree that linted clean before lints dirty now** | `lint_plan.py:626-635`; `tests/test_lint_plan_verdict_exempt.py` (3 tests); satisfiability probe in T04's ACs reports zero new findings on a final-state tree |
| 6 | packaged docs seed | `specfuse/loop/data/docs/methodology.md` and `.../skills.md` changed content (this close's doc reconciliation). A project running `specfuse upgrade` receives the updated text | additive; content-only, no file added, removed, or renamed | `tests/test_scaffold_data_in_sync.py` → `Ran 3 tests` `OK` after re-seeding |

**Removals and renames: none.** No function, flag, file, skill, frontmatter field, or
status value was removed or renamed in gate 1.

**Migration required: none.** Every change either accepts more input than before (1, 5)
or adds a surface that did not exist (2, 3, 4). No project config, no WU frontmatter, and
no existing skill invocation needs to change.

**One semantic caveat the reviewer should weigh alongside item 4.** Accepting a hedge
through `/accept-hedged-close` rewrites the close WU's `verdict` from `met_locally` to
`met`. Downstream consumers that read `verdict` as "this feature met every criterion"
will now see `met` on features whose criteria were accepted-with-follow-ups. The audit
trail exists, but only in `RETROSPECTIVE.md` prose. See *What I'd change*.

---

## What I'd change

**1. Mark an accepted hedge in the frontmatter, not only in prose.** The highest-value
change on this list. `/accept-hedged-close` should write `verdict: met` **plus**
`verdict_accepted_from: met_locally`, `verdict_accepted_reason: "<operator line>"`, and
`verdict_accepted_at: <ISO 8601>`, so the acceptance is machine-readable and a later
reader can tell an accepted hedge from a clean met without reading prose. As shipped, the
skill's own audit record is the only trace, and the field it audits has been overwritten.
An audit trail that mutates the field it is auditing is half an audit trail.

**2. Fix `loop.py:4462`.** Write `done` (or nothing — `fire_terminal_flips` has already
set it) instead of the unrecognized `complete`. One line, plus a red test that re-runs the
driver against a completed feature and asserts `PLAN.md` still reads `done` and plan-lint
still passes. Needs an issue.

**3. Give `--recheck-verdict` a CLI-level test.** The flag→primitive wiring shipped
untested; this close smoke-tested only the refusal path. One test over a temp feature tree
covering the firing path closes it.

**4. Add the `.claude/skills/` symlink — and stop maintaining that directory by hand.**
`accept-hedged-close`, `adopt-feature`, and `migrate-to-auto-close` are all missing from
this repo's local discovery directory while present in both `.specfuse/skills/` and
`plugins/specfuse/skills/`. Three misses is a process, not an oversight: either
`scripts/sync-scaffold.sh` should create the symlink, or a test should assert the three
directories agree. The vendored-copy sync test already exists and passes — it just does
not cover this third surface.

**5. Estimate driver-internals WUs *below* the median, not above it, when they extend an
existing guard test file.** Gate 1's uniform 34–66%-of-estimate outcome is a calibration
correction worth carrying into gate 2's drafting, where the temptation will be identical
(auto-close internals, existing test files).

**6. Guard `/arm-gate` against terminal gates,** or state explicitly in the skill that a
terminal gate's `passed` flip belongs to `fire_terminal_flips`. Currently nothing refuses.

**7. `scripts/sync-scaffold.sh` does not sync `docs/`, but the test that catches the drift
says to run it.** Editing `docs/methodology.md` and `docs/skills.md` in this close failed
`test_scaffold_data_in_sync.test_package_docs_match_canonical` with
`Run: scripts/sync-scaffold.sh` — and running it reported *"Scaffold data already in sync
(25 files checked)"*, because its `FILES` array covers templates, rules, and schemas but
no `docs/` entry. The two seed copies under `specfuse/loop/data/docs/` had to be re-seeded
by hand. This is a small instance of the same defect class as T04 and #265 — a check whose
stated remediation does not remediate it — and the fix is three lines: add
`docs/methodology.md`, `docs/skills.md`, and the tracked `docs/concepts/` entries to the
script (its source root differs from `.specfuse/`, so the loop needs a second `SRC`, which
is presumably why they were left out).

---

## Lessons promoted

Five entries appended to `.specfuse/LEARNINGS.md`, tagged
`[FEAT-2026-0070/G1-CLOSE-INTERMEDIATE]`:

1. **"Exactly one writer" is a property of the surface, not of the function** — audit it
   by grepping the writes, in every direction, not the definition. This gate's audit found
   `loop.py:4462` precisely because the grep was aimed at the surface.
2. **A skill may not own a state transition the driver owns** — the driver must expose an
   entry point, and the skill's *non*-writing must be enforced by a grep-shaped test over
   the skill text carrying a positive control. Generalises
   `[FEAT-2026-0023/G1-CLOSE]`'s close-path rule to the operator-skill surface.
3. **A contract enforced at two moments: the earlier enforcer must explain the later
   one's requirement or exempt the states the later one owns.** Names T04, #265, and #272
   as one defect class rather than three incidents.
4. **An attempt killed before it reaches an outcome is invisible to every cost
   consumer** — a close reconciling spend from `events.jsonl` reports a lower bound and
   must say so.
5. **An acceptance record that overwrites the field it records leaves no machine-readable
   trace** — carry the accepted-from value forward in frontmatter.

Not promoted, deliberately: the empty-Status-cell `str.replace` edge (T01) and the
`/arm-gate` terminal guard — both are single-site repo defects with no rule behind them,
and they live in *What I'd change* above where a fix can find them.
