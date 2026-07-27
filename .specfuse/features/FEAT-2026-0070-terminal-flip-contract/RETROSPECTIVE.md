# RETROSPECTIVE — FEAT-2026-0070, terminal-flip contract

Feature-level record, written across two passes.

- **`G1-CLOSE-INTERMEDIATE`** (gate 1, non-terminal) wrote everything from *Gate 1* down
  to *Lessons promoted — gate 1*. That content is preserved verbatim below; only its
  section headings were suffixed `— gate 1` by the terminal close, so the feature-level
  sections that follow are unambiguous. Nothing in it was revised after the fact.
- **`G2-CLOSE`** (gate 2, terminal — this pass) added the *Gate 2* record and every
  feature-arc section from *One-owner audit — feature arc* onward, including the verdict.

**Feature-arc verdict: `met_locally`.** Every substantive criterion is met and every
oracle re-ran green in this session; two obligations cannot be discharged by a dispatched
session at all, and five verification gaps are carried forward. The full record is in
*Hedged follow-up record*, and the recursion is not lost on this close: the path out of a
standing `met_locally` is `/accept-hedged-close`, which this feature is the one that
shipped. The feature's central constraint — one driver-side owner for the terminal flips —
is audited fresh in *One-owner audit — feature arc* § *Ruling*, and it held.

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

## One-owner audit — gate 1 (`[FEAT-2026-0023/G1-CLOSE]`)

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

## Cost analysis — gate 1

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

## What the loop did NOT verify — gate 1

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

## Consumer-visible contract changes — gate 1 (`close-discipline.md` §3)

> **Acknowledged.** This list was routed to the gate-1 review-and-arm checkpoint, and that
> checkpoint ran: `GATE-01.md` is `status: passed`, `GATE-02-REVIEW.md` § 11 open question 6
> put the list in front of the reviewer, and the arming produced substantive rulings
> (open question 3 accepted, adding `T06` AC12 and repricing `T06` $2.00 → $2.50). The
> gate-2 list in *Consumer-visible contract changes — feature arc* below is the one still
> awaiting a signature.

> **Original routing note, as written at gate-1 close.** **This list is submitted for human
> acknowledgment at the gate-1 review-and-arm
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

## What I'd change — gate 1

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

## Lessons promoted — gate 1

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

---

## Gate 2 — an auto-closed gate's skipped ceremony is a visible debt, not a silent saving

Gate 2 shipped four work units against **#241**. Every one passed on its first recorded
attempt, and the chain was strictly linear by construction: T06 cannot enumerate without
T05's slicer, T07 reads a marker only T06 writes, T08 predicts a guard only T07 defines.

| WU | type | attempts | planned | actual | delta | duration | output tokens | outcome |
|---|---|---|---|---|---|---|---|---|
| T05 `shared-wu-section-slicers` | implementation | 1 | $1.00 | $0.614522 | −38.5% | 362.9s | 5,708 | passed |
| T06 `autoclose-debt-enumeration` | implementation | 1 | $2.50 | $3.436137 | **+37.4%** | 541.3s | 26,609 | passed |
| T07 `autoclose-debt-invariant` | implementation | 1 | $2.25 | $3.288034 | **+46.1%** | 926.6s | 37,328 | passed |
| T08 `arm-time-debt-prediction` | implementation | 1 | $1.25 | $1.039360 | −16.9% | 463.8s | 12,175 | passed |
| **substantive subtotal** | | **4** | **$7.00** | **$8.378054** | **+19.7%** | 2,294.6s | 81,820 | |
| G2-CLOSE | close | 1 (this session) | $5.00 | not yet recorded | — | — | — | in progress |

`T06`'s `planned_cost_usd` reads $2.50, not the $2.00 `GATE-02-REVIEW.md` § 9 drafted: the
operator repriced it at arming when accepting open question 3, which added AC12. Against
the original $2.00 draft the overrun is **+71.8%**. See *Cost analysis — feature arc*.

### T05 — the slicers become a leaf module

**What shipped.** `specfuse/loop/_wu_sections.py`, exporting `slice_acceptance_criteria`
and `slice_wu_section`, with `lint_plan._slice_ac_section` / `_slice_section` kept as
one-line delegating shims so none of their six call sites — including
`tests/test_lint_oracle_env.py:117` — needed an edit.

**What worked.** The leaf property is the whole point and it is checkable in one command:
`grep -nE "^(from|import)" specfuse/loop/_wu_sections.py` shows only `from __future__` and
`import re`. That is what lets `loop.py` read a WU's criteria without the second parser
`authoring-work-units` §10 exists to prevent, and without the `lint_plan → loop` cycle
(`lint_plan.py:35`) that made the direct import impossible.

**What failed.** Nothing. $0.61 against $1.00, the cheapest WU of the feature.

**Worth noting for future extractions.** The red-test exemption was the right call and the
WU said why in one line rather than asserting the exemption silently: a pure extraction has
no new behavior to assert red, so the regression oracle *is* the acceptance criterion.

### T06 — auto-close writes the worklist (#241, option 1)

**What shipped.** `build_autoclose_debt_enumeration(feature_dir, gate_number) -> str` in
`loop.py`, called by **both** stub writers — `append_stub_retrospective_intermediate` and
`write_stub_retrospective_terminal`. One builder, two callers, which is
`[FEAT-2026-0023/G1-CLOSE]`'s one-owner rule applied to a *format* rather than to a state
transition. It emits the machine-readable marker, then one `deferred:` line per criterion,
grouped under each substantive WU's ID and file name.

**What worked, and it is verifiable in one run.** This close built the enumeration against
gate 1 of this very feature, live:

```
$ python3 -c "...build_autoclose_debt_enumeration(fd, 1)"   # first line of the block
<!-- specfuse:autoclose-debt gate=«1» wus=T01,T02,T03,T04 criteria=37 predicate=v1 -->
    37 `deferred:` lines; WUs named: T01, T02, T03, T04
    G1-CLOSE-INTERMEDIATE and G1-PLAN correctly absent (AC4's ceremony filter)
```

(The gate number is written `«1»` here on purpose — see *The surprise* below.) The
`_NON_SUBSTANTIVE_TYPES` filter is imported from `gate_eval` rather than forked, so the
ceremony WUs drop out of the worklist without a second copy of the type set.

**What failed.** Nothing, but it cost 37% over plan. The AC12 idempotency guard the
operator added at arming is a real part of that, and it was the right addition: after the
enumeration lands, a second unguarded call to the terminal writer appends the whole
criterion list again, which on an 8-WU gate is a hundred lines of *false* debt that T07
would then read as real. The guard turns a pre-existing ~10-line cosmetic duplication into
a non-issue precisely at the moment it stopped being cosmetic.

### T07 — the post-pass invariant, and the only severity flip in the feature

**What shipped.** `assert_autoclose_debt_reconciled` (`loop.py:4513`), registered in
`POST_PASS_INVARIANTS_BY_TYPE["close"]` **after** `assert_terminal_flips_fired`, plus its
row in `close-discipline.md` §4's guard table and a `(close-g)` docstring tag so
`tests/test_closing_guard_contracts.py::TestEveryClosingGuardIsListed` binds the
documentation to the source mechanically.

**What worked — the design decision that was made at plan time and held.** The obvious
form of this invariant fires on 6 of the 11 features in this repo that have auto-closed a
gate, every one of them `status: done` and correctly closed. `GATE-02-REVIEW.md` § 4 found
that *before* the WU was drafted, and the shipped form is marker-gated instead. This close
re-ran the enumeration against the tree rather than inheriting the claim (AC12, below):
**zero markers across 36 features and 33 retrospectives, zero invariant failures across 29
`type: close` WUs.**

Its controls are the guard's real evidence and they are both present:
`test_marked_predecessor_debt_unmentioned_fails` (negative),
`test_marked_predecessor_debt_mentioned_passes` (positive), and
`test_unmarked_autoclose_is_not_debt_and_does_not_fire` (the satisfiability gate itself,
named so its purpose survives a future refactor). Re-run fresh this session: `Ran 6 tests`
`OK`.

**What failed.** Nothing, but at $3.29 against $2.25 it is the single largest overrun of
the feature and the longest-running substantive WU (926.6s, 37,328 output tokens — more
output than any other WU in either gate).

### T08 — the guard and its prediction, shipped together

**What shipped.** `check_autoclose_debt_prediction(feature_dir, gates)` in `lint_plan.py`,
called from the same place `check_closing_guard_literals` is called, printing `WARN:` and
never touching the exit code. A sibling function rather than a fourth row in
`_GUARD_LITERAL_PREDICTIONS`, because every entry in that table is a static per-type regex
and this prediction is conditional on feature state — a static `close` row would warn on
every terminal close in every project, and noise is how a WARN stops being read.

**What worked.** This is the first time this repo has shipped a new blocking condition and
its arm-time prediction *in the same gate* rather than after the first refusal.
`close-discipline.md` §4 priced the alternative: three guards with no authoring surface
account for $99.30, 45% of all closing-WU refusal waste, `assert_gate_review_exists` alone
at $53.11 over 15 fires — while `assert_verdict_well_formed` fired 10 times for $0.00
because it is checked before the agent spends anything. T08 is the difference between the
two kinds, bought for $1.04.

**What failed.** Nothing. The cheapest overrun-free WU of gate 2, −16.9% against plan.

### Failure-class breakdown

**Driver-recorded non-passing attempts across gate 2: zero.** All four `attempt_outcome`
events carry `outcome: passed`, `attempt: 1`, `re_arm_count: 0`. No re-attempt, no
`blocked`, no closing-guard refusal, and — unlike gate 1 — no infra kill either.

| failure class | count | WUs |
|---|---|---|
| *(any driver-recorded class)* | 0 | — |
| infra kill, no `attempt_outcome` emitted | 0 | — |

Feature-wide the honest statement is gate 1's: **one** killed attempt (T03), invisible to
`events.jsonl` by construction, so the feature's recorded actual is a lower bound.

### Surprises

1. **A retrospective that *quotes* the debt marker manufactures the debt.** This is the
   most important thing gate 2's close found, and it was found by executing, not by
   reading. `_AUTOCLOSE_DEBT_MARKER_RE` is a plain text scan over `RETROSPECTIVE.md`;
   it has no notion of a fenced code block. Observed:

   ```
   probe: copy this feature dir, append the marker literal inside a ``` fence, run
          assert_autoclose_debt_reconciled on G2-CLOSE
   -> ok=False
      autoclose_debt_unreconciled: gate(s) 1 carry an unreconciled auto-close debt
      marker not named in the terminal close's '## What the loop did NOT verify' section
   ```

   The population most likely to write that literal into a retrospective is exactly the
   population documenting the feature that ships it — which is why this close writes the
   gate number as `«1»` above and never emits the raw token. The trap is partly
   self-limiting (a deferral section that *does* discuss gate 1 satisfies the check even
   on a forged marker), but "partly, by luck of what the prose happens to mention" is not a
   contract. Promoted to `LEARNINGS.md`; fix proposed in *What I'd change — feature arc*.

2. **Gate 2's estimates missed in the opposite direction from gate 1's, after gate 1's own
   lesson was applied.** Gate 1 came in 53.5% under and concluded "an existing test file to
   extend makes a driver-internals WU cheaper, not dearer." `GATE-02-REVIEW.md` § 9 priced
   all four gate-2 WUs on that lesson — and gate 2 came in **19.7% over**, with T07 at
   +46.1% and T06 at +37.4%. The lesson was true and second-order. See *Cost analysis*.

3. **The runtime probe's green suite meant the opposite of what green usually means, and
   the arming record said so.** `GATE-02-REVIEW.md` § 5 recorded that both the satisfiable
   and the unsatisfiable form of the invariant left all 1,568 tests passing, and read that
   as proof the suite was blind to the surface rather than as proof the invariant was safe.
   That reading is why T07 shipped with three named control tests. Gate 2 added 20 tests
   (1,568 → 1,588); the three controls are the ones that would have caught the wrong
   variant.

4. **The guard is registered, documented, controlled — and has never fired on a marker a
   driver actually wrote.** Auto-close has not run in this repo since T06 shipped, so the
   marker count on disk is zero. Every test uses a synthetic fixture. This close's
   round-trip probe (T06's builder → T07's regex, above) covers two thirds of the chain;
   the third third — the driver auto-closing a real gate and a later terminal close being
   refused — is in *What the loop did NOT verify — feature arc*.

---

## One-owner audit — feature arc (`[FEAT-2026-0023/G1-CLOSE]`)

The feature's central constraint is that terminal-state flips have exactly **one**
driver-side owner called identically by every close path. Gate 1 audited it and gate 2 is
its last checkpoint. Every command below was executed in this session against the merged
tree; nothing is inherited from gate 1's audit.

| check | command | observed |
|---|---|---|
| single definition | `grep -c "def fire_terminal_flips" specfuse/loop/loop.py` | **`1`** |
| every `write_frontmatter_field(..., "status", ...)` in `specfuse/`, mapped to its enclosing function by AST rather than by eye | `grep -rn 'write_frontmatter_field(' specfuse/ \| grep -i status`, then an `ast` walk | 7 sites — see the table below |
| roadmap writers | `grep -rn "roadmap_path.write_text" specfuse/loop/` | 3 — `auto_archive_feature` (`:3057`, Detail cell only), `revert_terminal_surfaces` (`:3124`), `fire_terminal_flips` (`:3224`) |
| terminal gate `passed` writers | `grep -n "set_gate(" specfuse/loop/loop.py` | `set_gate`'s 4 call sites (`4786`, `4821`, `5557`, and the `4909` comment) **all pass `"awaiting_review"`**; the only `status: passed` write is `loop.py:3183`, inside `fire_terminal_flips` |
| **gate 2's new symbols write no terminal surface** | AST scan of `build_autoclose_debt_enumeration`, `assert_autoclose_debt_reconciled`, `check_autoclose_debt_prediction` for `write_frontmatter_field` / `roadmap_path` / `set_gate(` / `write_text` / `fire_terminal_flips` | **no write or flip call in any of the three.** The two stub writers T06 edits touch `RETROSPECTIVE.md` only (`loop.py:3578`, `:3581`, `:3741`, `:3744`) — not a terminal surface |
| T05's module is a leaf | `grep -nE "^(from\|import)" specfuse/loop/_wu_sections.py` | `from __future__ import annotations`, `import re`. Nothing else |
| the skill still writes nothing | `grep -nEi "PLAN\.md.*status\|roadmap.*row\|set_gate\|fire_terminal_flips" .specfuse/skills/accept-hedged-close/SKILL.md` | 9 hits, **every one a negative statement** ("does not write…", "never calls…", "those three remain untouched"). No imperative to write any of the three |
| both skill copies agree | `diff .specfuse/skills/accept-hedged-close/SKILL.md plugins/specfuse/skills/accept-hedged-close/SKILL.md` | no output, exit `0` |
| the skill's guard tests | `python3 -m unittest tests.test_accept_hedged_close_skill` | `Ran 19 tests` `OK` |

**The seven `status` writers, by enclosing function:**

| site | function | surface | verdict |
|---|---|---|---|
| `loop.py:630` | `set_gate` | a `GATE-NN.md` `status` | the backend's gate writer; every caller passes `awaiting_review` |
| `loop.py:3114` | `revert_terminal_surfaces` | `PLAN.md` → `active` | by design (#195), the deliberate inverse of `fire_terminal_flips` |
| `loop.py:3183` | **`fire_terminal_flips`** | terminal gate → `passed` | **the owner** |
| `loop.py:3266` | **`fire_terminal_flips`** | `PLAN.md` → `done` | **the owner** |
| `loop.py:3596` | `mark_close_wu_auto_closed` | a **WU**'s `status` | not a feature surface |
| `loop.py:3809` | `maybe_auto_close_intermediate` | a **WU**'s `status` | not a feature surface |
| `loop.py:4673` | `run` | `PLAN.md` → **`complete`** | **the defect, still present** |

### Ruling

**The one-owner property holds for the `→ done` transition, and gate 2 did not weaken it.**
Nothing this feature added — not `recheck_terminal_verdict`, not `/accept-hedged-close`,
not any of gate 2's three new functions, not the two stub writers gate 2 edited — writes
`PLAN.md`'s `status`, a gate's `status`, or the roadmap row. AC5's literal question ("no
skill or entry point *added by this feature* writes …") answers **no** on an executed
audit, not on assumption.

**The `loop.py:4673` defect is unfixed and is reported, not smoothed away.** It was
`loop.py:4462` when gate 1 found it; the line moved, the write did not. `run()` writes
`PLAN.md status: complete`, which is not in
`lint_plan.VALID_FEATURE_STATUS = {"planned", "active", "blocked", "deferred", "done",
"abandoned"}`, so re-running the driver against a finished feature overwrites the `done`
that `fire_terminal_flips` just wrote with a value the rest of the system rejects. It is a
gate-1-family bug on a surface gate 2 is adjacent to; `GATE-02-REVIEW.md` § 8 item 1 routed
it to `/fix-bug` at arming and named it in T07's *Do not touch* so no session would repair
it in passing. **That routing was a human decision made at the arming checkpoint, and this
close honours it rather than re-opening it.**

**On the escalation trigger.** `WU-92`'s trigger is "AC5's audit finds more than one
terminal-state writer." Read literally over every write of those bytes in any direction,
it is unsatisfiable on arrival — `revert_terminal_surfaces` predates this feature by
several gates and writes the same surfaces by design. Gate 1 read it as governing the
`→ done` transition (what `[FEAT-2026-0023/G1-CLOSE]` names and what #49 broke), and this
close keeps that reading and states it so a reviewer can overrule it. Under that reading:
one writer, trigger not fired. **A feature that shipped every WU green while splitting
terminal-state ownership would have failed**; this one did not split it.

---

## Oracles re-run fresh (`close-discipline.md` §1)

Every oracle the feature's criteria name, re-run in this session, exit codes read directly.
No producing WU's self-report is carried.

| gate | command | result | exit |
|---|---|---|---|
| tests | `python3 -m unittest discover -s tests` | `Ran 1588 tests in 49.063s` — `OK (skipped=3)` | `0` |
| lint | `ruff check specfuse .specfuse/scripts tests scripts` | `All checks passed!` | `0` |
| security | `bandit -r specfuse .specfuse/scripts -ll` | `High: 0`, `Medium: 0` (77 Low, below the `-ll` threshold) | `0` |
| coverage | `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90` | `TOTAL  4164  261  94%` | `0` |
| leak-scan | `python3 .specfuse/scripts/leak_scan.py --all` | `leak-scan: gitleaks 8.30.1` / `leak-scan: clean` | `0` |
| monitoring-example-lint | `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` | `OK — monitoring config is structurally valid (or absent).` | `0` |
| bats | `bats tests/init_skills_idempotent.bats` | `ok 1` | `0` |
| bats | `bats tests/leak_scan_hook.bats` | 3 `ok` | `0` |
| bats | `bats tests/sync_scaffold.bats` | 5 `ok` | `0` |
| bats | `bats tests/init_sh_shim.bats` | 5 `ok` | `0` |
| plan-lint (AC10) | `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0070-terminal-flip-contract` | `OK — … is structurally valid.`, no WARN | `0` |

**Sandbox.** The first bats gate ran under the default session sandbox. The other three
failed in `setup` with `mktemp: mkdtemp failed … Operation not permitted` — the sandbox
denial `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` documents and every gate-2 WU repeats in a
sandbox note — and were re-run unsandboxed, where all 13 assertions pass. The failure is
the sandbox, not the gates; reported rather than hidden because a reader who runs them
sandboxed will see the same three reds.

**Test-count reconciliation.** `GATE-02-REVIEW.md` § 5's arming probe recorded `Ran 1568
tests` on gate-1 HEAD. Gate 2 added **20** tests (1,568 → 1,588), consistent with T06's 10
new, T07's 6, and T08's small additions.

**Scoped re-runs, fresh:** `tests.test_loop_post_pass_invariant.TestAutoCloseDebtReconciled`
`Ran 6` `OK`; `tests.test_autoclose_deferral_visibility` `Ran 13` `OK`;
`tests.test_closing_guard_prediction` `Ran 18` `OK`;
`tests.test_accept_hedged_close_skill` `Ran 19` `OK`; `tests.test_terminal_flips` `Ran 18`
`OK`; `tests.test_closing_guard_contracts` `Ran 6` `OK`;
`tests.test_scaffold_data_in_sync` `Ran 3` `OK`.

**No oracle re-run disagreed with any WU's self-report.** The escalation trigger for a
disagreement did not fire.

---

## AC11 — T07's invariant, run against this close

This is the terminal close of the feature that ships `assert_autoclose_debt_reconciled`,
so the guard runs against its own feature. Executed here rather than waiting for the
driver's post-pass:

```
assert_autoclose_debt_reconciled(G2-CLOSE, FEAT-2026-0070-terminal-flip-contract, …)
-> ok=True   reason=''
```

**That pass is vacuous, and saying so is the point of this section.** Gate 1 did not
auto-close — `WU-90-gate-1-close-intermediate.md` carries `auto_close_disabled: true` and
ran a real 985-second session — so `RETROSPECTIVE.md` carries no debt marker, the
predecessor-gate set is empty, and the invariant short-circuits `(True, "")` before it
evaluates anything. **A green post-pass here is evidence of nothing about the guard.** The
guard's real evidence is T07's three controls (negative, positive, and the no-marker
satisfiability test), re-run fresh above, plus this close's round-trip probe showing T06's
builder emits a marker T07's regex actually matches. A vacuous pass counted as a second
piece of evidence would be exactly the hollow-pass shape this repo's guards exist to catch.

## AC12 — the satisfiability claim, re-checked against the tree

Not inherited from `GATE-02-REVIEW.md`. The invariant's own marker regex and the invariant
itself were run across every feature on disk in this session:

```
features scanned:                       36
features carrying a debt marker:         0
type: close WUs checked:                29
invariant failures:                      0
grep -rl "specfuse:autoclose-debt" .specfuse/features/*/RETROSPECTIVE.md | wc -l   ->  0
   (33 RETROSPECTIVE.md files on disk)
```

**Same answer as plan time, on a wider population.** `GATE-02-REVIEW.md` § 4a enumerated
11 features with an auto-closed gate and reported zero; this scan covers all 36 features
with a `PLAN.md` and reports zero markers and zero failures on all 29 close WUs. Nothing
changed between arming and close, so there is no finding here — but the check was run, not
assumed, because a different answer would have been one.

---

## Cost analysis

**Baseline: the as-drafted figure, unadjusted.** `PLAN.md` `planned_cost_usd: $32.00`.
Per `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`, no re-baselining onto the feature's own
overrun.

**First finding: the WU sum on disk is $32.50, not $32.00.**

| | planned |
|---|---|
| gate 1 — T01 $2.50, T02 $3.50, T03 $2.50, T04 $1.50 | $10.00 |
| gate 1 ceremony — `G1-CLOSE-INTERMEDIATE` $4.50, `G1-PLAN` $6.00 | $10.50 |
| gate 2 — T05 $1.00, T06 **$2.50**, T07 $2.25, T08 $1.25 | $7.00 |
| gate 2 ceremony — `G2-CLOSE` $5.00 | $5.00 |
| **sum of every WU's `planned_cost_usd`** | **$32.50** |
| `PLAN.md` `planned_cost_usd` | $32.00 |
| **delta** | **+$0.50 (+1.5%)** |

`GATE-02-REVIEW.md` § 9 reconciled to **$0.00** against $32.00 with T06 at $2.00. The
operator repriced T06 to $2.50 at arming when accepting open question 3 (the AC12
idempotency guard), and nothing re-reconciled: plan-lint's cost-delta check has a 10%
threshold and 1.5% sits under it, so the drift was invisible. Small in dollars, but the
mechanism generalises — see *What I'd change*.

**Actual, from `events.jsonl` `attempt_outcome` / `task_completed` payloads:**

| | planned | actual | delta |
|---|---|---|---|
| gate 1 substantive (T01–T04) | $10.00 | $4.648801 | **−53.5%** |
| gate 1 ceremony (`G1-CLOSE-INTERMEDIATE` $6.371276, `G1-PLAN` $7.503196) | $10.50 | $13.874472 | **+32.1%** |
| **gate 1 total** | **$20.50** | **$18.523273** | **−9.6%** |
| gate 2 substantive (T05–T08) | $7.00 | $8.378054 | **+19.7%** |
| gate 2 ceremony (`G2-CLOSE`, this session) | $5.00 | not yet recorded | — |
| **feature, recorded so far** | **$32.50** | **$26.901326** | open until this WU completes |

Recorded dispatch time across the ten completed WUs: **6,349s ≈ 106 minutes**.

### The variance, split by cause

A single blended percentage would report "−17% so far" and hide all four signals below.

**Cause 1 — gate 1's substantive estimates were high, uniformly (−53.5%).** No gate-1 WU
exceeded 66% of its estimate. `PLAN.md` had priced them *above* the observed $1.33 median
on the grounds that all four touch driver internals with existing guard tests; the opposite
was true.

**Cause 2 — gate 2's substantive estimates were low, and they were low *because* they
applied gate 1's correction (+19.7%).** This is the finding of the feature's cost record.
`GATE-02-REVIEW.md` § 9 priced all four gate-2 WUs on gate 1's lesson ("an existing test
file to extend makes the work cheaper") and noted "all four gate-2 WUs extend existing test
files, and are priced accordingly." They came in over. Ordered by acceptance-criterion
count, the deltas are monotone:

| WU | ACs | planned | actual | delta |
|---|---|---|---|---|
| T05 | 7 | $1.00 | $0.614522 | −38.5% |
| T08 | 10 | $1.25 | $1.039360 | −16.9% |
| T07 | 12 | $2.25 | $3.288034 | **+46.1%** |
| T06 | 13 | $2.50 | $3.436137 | **+37.4%** |

Four points is not a model, and the monotonicity may be coincidence. But the *mechanism* is
legible without statistics: T07's 12 criteria include three named control tests, a
registration-order assertion, a `close-discipline.md` table row bound by a contract test,
and a tree-wide satisfiability re-probe — six deliverables, each with its own oracle. T06's
13 include a >40-criteria truncation case, three degrade cases, a marker-literal assertion,
and the arming-added idempotency guard. Whether the test *file* already exists is
second-order next to how many distinct things the WU must prove. **Estimate by
criterion-and-control count; treat "extends an existing test file" as a modifier, not the
variable.**

**Cause 3 — ceremony overran, again, and it is the larger absolute miss (+32.1%,
+$3.37).** `G1-CLOSE-INTERMEDIATE` $6.37 against $4.50 (+41.6%); `G1-PLAN` $7.50 against
$6.00 (+25.1%). `GATE-02-REVIEW.md` § 9 predicted this and flagged that
`[FEAT-2026-0069/GATE-1-ARM]`'s two `plan-next` observations ($15.65, $16.44) made $6.00
look low. $7.50 landed between the floor and those observations. The #266 per-type floors
are floors, not estimates, and three of this feature's four completed ceremony/close WUs
have now exceeded theirs.

**Cause 4 — one attempt is missing from the actual entirely.** Gate 1's T03 was killed by
infrastructure mid-attempt and recovered (branch commit `aa20e4a`); a terminated attempt
emits no `attempt_outcome`, so its tokens appear in no consumer of `events.jsonl`.
**$26.901326 is a lower bound**, understated by one session of unknown size.

### Projection for the feature total

This close is not in the sum. If it lands near `G1-CLOSE-INTERMEDIATE`'s $6.37 — the
closest comparable, a load-bearing close with `auto_close_disabled: true` — the feature
finishes near **$33.3, about 4% over** the $32.00 plan, with the substantive half 23.4%
under ($13.03 against $17.00) and the ceremony half well over. Labelled a projection, not a
result: the actual lands in `events.jsonl` after this session ends and a reader should take
it from there, not from here.

---

## What the loop did NOT verify

Seven entries. Each names the criterion, why verification was deferred, and where it
actually happens. Five are carried forward from gate 1 and remain open; two are gate 2's
own.

**1. `WU-92` AC7 — human acknowledgment of the consumer-visible contract list.**
*Why deferred:* a dispatched session has no human in it. This is structural, not a gap in
the work. *Where it happens:* the `met_locally` verdict leaves the gate `awaiting_review`
and all three terminal surfaces un-flipped, so an operator must come through and either
accept (via `/accept-hedged-close`, whose confirm step is the acknowledgment) or reject.
Unlike gate 1 — which could route its list to the mandatory `/arm-gate` checkpoint — a
terminal close has no gate to arm, and the hedged-acceptance path is the only remaining
mandatory human step. That is a reason to hedge the verdict, not a reason to self-sign.

**2. `/accept-hedged-close`'s behavioural criteria (T03 AC4–AC9) — a skill is verified by
an operator running it.** The entry `WU-92` AC3 named at drafting time.
*Verified and genuinely so:* the directory exists with valid frontmatter, both copies are
byte-identical, the text contains no instruction to write any terminal surface, the
forbidden-pattern matcher is proven to fire on a real positive instruction, and 19 tests
pass. *Not verified:* that an agent executing the skill actually refuses on `met` /
`not_met` / a non-`done` close WU, actually re-prompts on an empty rationale, actually
carries every follow-up forward verbatim, and actually leaves the three surfaces untouched
while the flips fire. All 19 assertions are over SKILL.md **text**; they prove the prose
says the right thing, not that an agent following it does the right thing.
*Where it happens:* one operator run against a real feature standing at `met_locally`.

**3. `--recheck-verdict`'s firing path through the CLI.** Carried from gate 1 unchanged;
gate 2 did not touch it. Gate 1 smoke-ran the refusal path only
(`FEAT-2026-0070/G2-CLOSE status is 'draft' (not done)`, exit `0`). The flag →
`_resolve_feature_dir` → primitive → `fire_terminal_flips` → `Modified:` chain is still
covered by no test. *Where it happens:* one CLI-level test over a temp feature tree — or,
incidentally, the first real `/accept-hedged-close` run, which goes through exactly that
path.

**4. `loop.py:4673`'s `status: complete` write is a code-reading, not a reproduction.**
The write, the invalid value, and `lint_plan.py`'s rejection of it are all established from
source; the end-to-end sequence (close a feature, re-run the driver against it, observe
`PLAN.md` flip `done → complete`, watch plan-lint fail) has still not been executed.
*Where it happens:* the red test of the `/fix-bug` branch `GATE-02-REVIEW.md` § 8 routed it
to.

**5. `/arm-gate`'s missing terminal-gate guard is unexercised.** No test asks what
`/arm-gate` does when pointed at a terminal gate; the claim is read from the skill text.
Carried from gate 1.

**6. `assert_autoclose_debt_reconciled` has never been evaluated against a marker the
driver wrote.** Gate 2's own. Every T07 test builds its marker by hand in a fixture; this
close's round-trip probe built one with T06's real builder and matched it with T07's real
regex, which covers the format contract but still not the *sequence*. The untested chain
is: the driver auto-closes a real intermediate gate → `append_stub_retrospective_intermediate`
writes the enumeration and marker into a real `RETROSPECTIVE.md` → a later terminal close
omits the gate → the driver refuses the close WU. *Why deferred:* no gate in this repo has
auto-closed since T06 shipped, and manufacturing one inside a close WU would be the
"while I was here" drift `result-contract.md` §2 forbids. *Where it happens:* the first
feature that auto-closes an intermediate gate on driver ≥ this build — or a deliberate
end-to-end lifecycle test, which is the cheaper and more honest option (see *What I'd
change*).

**7. T06's enumeration has never been written by a real auto-close either.** Same root
cause as 6, different deliverable: the degrade paths (missing file, unreadable file, no
`**Acceptance criteria.**` section), the >40-criterion truncation line, and the AC12
idempotency guard are all fixture-verified only. The strongest non-fixture evidence is this
close's live build against gate 1 of this feature (37 criteria, 4 WUs, ceremony WUs
correctly excluded), which exercises the happy path and none of the degrades.
*Where it happens:* the same first real auto-close, or the same lifecycle test.

**On the sizing trigger.** `WU-92` AC3 says to flag gate sizing under *What I'd change* if
this list exceeds 2 entries or 30% of the feature's criteria. Seven entries **exceeds the
count trigger**; against 79 substantive acceptance criteria (37 in gate 1, 42 in gate 2)
it is **8.9%, well under the percentage trigger**. Flagged as required, with the caveat
that five of the seven are inherited gate-1 items or structural impossibilities rather
than gate-2 sizing — see *What I'd change — feature arc* item 4.

---

## Hedged follow-up record (`close-discipline.md` §2)

**Verdict: `met_locally`.** One entry per criterion that is not fully `met`, with the exact
condition that upgrades it.

**The recursion, stated plainly rather than left as irony.** This feature exists to build
the supported path out of a standing `met_locally` — that is #243, that is `T02`'s
primitive and `T03`'s skill — and it is closing on `met_locally` itself. The thing that
discharges this hedge is `/accept-hedged-close`, which this feature is the one that
shipped. That is not a defect in the verdict; it is the mechanism working on its first
real subject. It does mean the first production invocation of the skill and the acceptance
of the feature that produced it are the **same act**, so a failure of either is entangled
with the other. The operator should note the outcome of that run either way — if the skill
misbehaves on FEAT-2026-0070, the finding is worth more than the acceptance.

| # | criterion (verbatim, abridged where noted) | why unverifiable here | exact re-run condition that upgrades it to `met` |
|---|---|---|---|
| **H1** | `WU-92` AC7: *"Consumer-visible contract changes (§3): enumerate every addition, removal, and rename across the whole feature … Block on human acknowledgment."* | No human is present in a dispatched session, and unlike gate 1 there is no downstream `/arm-gate` checkpoint to route to — this is the terminal close | An operator reads *Consumer-visible contract changes — feature arc* below (**item 8 is the behaviour change**) and either runs `/accept-hedged-close FEAT-2026-0070` with a one-line reason, or rejects this close. The skill's explicit-acknowledgment step **is** the §3 signature |
| **H2** | `WU-03` AC4–AC9 (behavioural): the skill *refuses* on a wrong verdict or a non-`done` close WU, *re-prompts* on an empty rationale, *writes* the acceptance record carrying follow-ups forward verbatim, and *leaves the three surfaces untouched* while the flips fire | An interactive propose-and-confirm skill's oracle is an operator at a terminal; 19 text assertions prove the prose, not the behaviour | One operator run of `/accept-hedged-close` against a feature standing at `met_locally` — **FEAT-2026-0070 is now exactly that feature**, so H1's run discharges H2 in the same act. Record what the skill actually did |
| **H3** | `WU-02`'s CLI wiring: flag → `_resolve_feature_dir` → `recheck_terminal_verdict` → `fire_terminal_flips` → the `Modified:` line | Exercising the *firing* path needs a feature whose terminal close WU is `done` with `verdict: met` and whose surfaces are still un-flipped — which did not exist until this WU completed | Either one CLI-level test over a temp feature tree, or the `--recheck-verdict` call that H1's `/accept-hedged-close` run makes; the latter observes it in production and should be reported as such |
| **H4** | `WU-92` AC5's adjacent finding: `loop.py:4673` writes `PLAN.md status: complete`, an invalid feature status that overwrites a correct `done` | Established from source in both closes; neither executed the sequence, and executing it inside a close WU is the drift `result-contract.md` §2 forbids | The red test on the `/fix-bug` branch: close a feature, re-run the driver against it, assert `PLAN.md` still reads `done` and plan-lint still passes. Needs an issue filed (see below) |
| **H5** | Gate 1's finding that `/arm-gate` carries no terminal-gate guard, so on a terminal gate it would be a second writer of the gate status | Read from the skill text; no test exercises `/arm-gate` against a terminal gate | One test or one explicit refusal clause added to the skill, plus an operator run confirming it refuses |
| **H6** | `WU-07` AC1/AC3's claim, at the level of the *sequence* rather than the *function*: a terminal close that ignores a real auto-closed predecessor's debt is refused by the driver | No gate in this repo has auto-closed since T06 shipped, so the marker count on disk is zero (AC12) and no driver-written marker exists to test against | An end-to-end lifecycle test that lets the driver auto-close an intermediate gate, then dispatches a terminal close whose deferral section omits it, and asserts the refusal — or the first real feature that auto-closes a gate on this build and is then observed |
| **H7** | `WU-06` AC7/AC8/AC12: the >40-criterion truncation line, the three degrade paths, and the idempotency guard, as produced by a real auto-close | Same root cause as H6; verified by fixtures and, for the happy path only, by this close's live build against gate 1 | The same lifecycle test or the same first real auto-close |

**None of these blocks a merge.** H1 blocks the *terminal flip*, which is the correct
behaviour and the whole point of the hedged-verdict contract: the driver holds `PLAN.md`,
the gate, and the roadmap row un-flipped until a human accepts. H2–H7 are follow-up work
with named homes.

---

## Consumer-visible contract changes — feature arc (`close-discipline.md` §3)

> **This list is submitted for human acknowledgment and is not self-acknowledged.**
> Gate 1's six items (table above) were acknowledged at the `/arm-gate` checkpoint. Gate 2's
> seven are new and have had no human pass. There is no further gate to arm, so the
> acknowledgment happens at the hedged-verdict acceptance — see H1. **Item 8 is a new
> blocking condition on every `type: close` WU in every project that upgrades. Read it
> first.** A reviewer may reject this close on the list alone.

**This is not `n/a`.** The feature makes **thirteen** consumer-visible changes: gate 1's
six, carried forward verbatim from the table above (roadmap-row flip breadth; the
`--recheck-verdict` flag; `recheck_terminal_verdict`; the `/accept-hedged-close` skill;
`lint_plan`'s widened verdict-exempt set; the packaged docs seed), plus gate 2's seven:

| # | surface | change | breaking? | evidence |
|---|---|---|---|---|
| **7** | driver Python surface | **New public function `build_autoclose_debt_enumeration(feature_dir, gate_number) -> str`**, returning the deferred-verification worklist block. Called by both auto-close stub writers | additive | `loop.py`; `tests/test_autoclose_deferral_visibility.py` (13 tests) |
| **8** | **driver close-WU contract** | **New post-pass invariant `assert_autoclose_debt_reconciled`, registered in `POST_PASS_INVARIANTS_BY_TYPE["close"]`.** A `type: close` WU now **fails** when `RETROSPECTIVE.md` carries an auto-close debt marker for a gate earlier than the terminal one and the terminal `## What the loop did NOT verify` section never names that gate | **behaviour change — a new blocking condition.** Marker-gated: fires on **0 of 36** features on disk and cannot fire on any gate auto-closed before this build. Short-circuits when the close WU is itself `auto_close: true` | `loop.py:4513`; `tests/test_loop_post_pass_invariant.py::TestAutoCloseDebtReconciled` (6 tests: negative, positive, no-marker, terminal-gate-marker, terminal-auto-close, registration order); tree scan in AC12 |
| **9** | auto-close stub output | **Both stub writers now emit a criterion-by-criterion `deferred:` worklist and a `specfuse:autoclose-debt` HTML-comment marker** into `RETROSPECTIVE.md`, beneath the existing prose rather than replacing it. Anything parsing those stubs sees new content, and the marker is a new parseable token | additive-content; the pre-existing headings, `Gate 2's close` line, and `gate_total_cost:` line are unchanged and still asserted by the three original tests | `loop.py:3523` (marker), `:3578`/`:3741` (writers); live build in *Gate 2 → T06* |
| **10** | auto-close behaviour | **`write_stub_retrospective_terminal` gained the idempotency guard its intermediate sibling already had.** A second call no longer appends a duplicate section | **behaviour change — strictly fewer writes.** Nothing that depended on the duplicate could have wanted it | T06 AC12; test calls the writer twice and asserts one section |
| **11** | driver Python surface | **New module `specfuse/loop/_wu_sections.py`** exporting `slice_acceptance_criteria(body)` and `slice_wu_section(body, section_name)`. `lint_plan._slice_ac_section` / `_slice_section` keep their exact names, signatures, and outputs as delegating shims | additive — **nothing renamed or removed**; all six existing call sites unedited, which is what makes the extraction behaviour-preserving | `specfuse/loop/_wu_sections.py`; T05 AC1's before/after regression run |
| **12** | `lint_plan` output | **New `check_autoclose_debt_prediction(feature_dir, gates)`** printing a `WARN:` when a feature has a marked auto-closed gate and its terminal close WU's body never instructs the agent to reconcile it | additive-advisory — **never changes the exit code**, and emits nothing on a feature with no marker (i.e. every feature that closed before this build) | `lint_plan.py`; `tests/test_closing_guard_prediction.py` (18 tests); zero WARNs on this feature and repo-wide |
| **13** | packaged rules seed | **`.specfuse/rules/close-discipline.md` §4's guard table gains the `assert_autoclose_debt_reconciled` row**, and the seed copy under `specfuse/loop/data/rules/` is in sync. A project running `specfuse upgrade` receives the updated rule | additive; content-only, no file added, removed, or renamed | `diff` against the seed → identical; `tests/test_scaffold_data_in_sync.py` `Ran 3` `OK`; `tests/test_closing_guard_contracts.py` `Ran 6` `OK` binds the row to the function |

**Removals and renames across the whole feature: none.** No function, flag, file, skill,
frontmatter field, or status value was removed or renamed in either gate.

**Migration required: none.** Every change either accepts more input than before, adds a
surface that did not exist, or emits additional content into an artifact nothing parses
strictly.

**Two caveats the reviewer should weigh, both new to gate 2.**

1. **Item 8 is the first new *blocking* condition this feature adds**, and its safety rests
   entirely on the marker gate. `GATE-02-REVIEW.md` § 4a showed the unmarked form fires on
   6 of 11 correctly-closed features; the shipped form fires on 0 of 36 and this close
   re-verified that against the tree. If a future change ever widens the marker match, that
   6-of-11 result is what it widens toward.
2. **Documenting the marker forges the marker.** The scan is plain text over the whole
   retrospective with no awareness of code fences, so a close that quotes the literal token
   with a real gate digit creates debt it must then reconcile. Observed, not theorised
   (*Gate 2 → Surprises* item 1). This close deliberately never emits the raw token. Anyone
   writing project documentation, a migration note, or a blog post *inside* a
   `RETROSPECTIVE.md` will hit it.

**Still open, and deliberately not closed by this feature** (`GATE-02-REVIEW.md` § 8):
`/accept-hedged-close`'s laundered hedge (`verdict_accepted_from` / `_reason` / `_at`), the
`--recheck-verdict` CLI test, the `.claude/skills/` symlink drift, and
`sync-scaffold.sh` not syncing `docs/`. The symlink drift was re-checked in this session
and is unchanged: `accept-hedged-close`, `adopt-feature`, and `migrate-to-auto-close` are
all still absent from `.claude/skills/` while present in both `.specfuse/skills/` and
`plugins/specfuse/skills/`.

---

## What I'd change — feature arc

**1. Make the debt marker unforgeable by prose, or teach the scan about code fences.**
The highest-value follow-up gate 2 produced. Three options, cheapest first: strip fenced
blocks before scanning; require the marker to be the first line of an
`## What the loop did NOT verify (gate N)` section rather than accepting it anywhere in
the file; or give it a form a quotation cannot reproduce. The first is three lines and a
test. Today the only thing standing between a documentation paragraph and a refused close
is whether the prose happens to also mention the gate number.

**2. Estimate WUs by acceptance-criterion and control count, not by whether the test file
exists.** Gate 1 concluded "existing test file → cheaper" from a −53.5% quarter; gate 2
priced on that lesson and came in +19.7%, monotone in AC count. The correction is not to
discard gate 1's lesson but to demote it: count the distinct things the WU must *prove*
(each control test, each degrade case, each documentation row bound by a contract test),
and treat the existing-file discount as a modifier on top. See *Cost analysis* cause 2.

**3. Re-reconcile the as-drafted total whenever arming reprices a WU.** T06 went $2.00 →
$2.50 at arming and the review document's "delta $0.00" silently became "+$0.50", invisible
to plan-lint because 1.5% is under its 10% threshold. Either `/arm-gate` should re-run the
sum and update the arming record's reconciliation table, or the linter should report the
delta as an informational line at any magnitude rather than only above a threshold — a
threshold designed to suppress noise also suppresses the audit trail.

**4. Scope the deferral-count sizing trigger to the gate being closed.** `WU-92` AC3's
"more than 2 entries" fired on a list of seven, five of which are inherited gate-1 items or
structural impossibilities (no human in a dispatched session). The percentage trigger — 30%
of criteria — did not fire, at 8.9%, and was the better signal. Either count only *this
gate's* new deferrals against the count trigger, or drop the count trigger and keep the
percentage.

**5. Write the end-to-end auto-close lifecycle test.** H6 and H7 have the same root cause
and the same fix: nothing in 1,588 tests lets the driver auto-close a gate and then
dispatch a terminal close against the result. `GATE-02-REVIEW.md` § 5 already found this —
both the satisfiable and the unsatisfiable form of the invariant left the suite green,
which proved the suite blind to the surface. Gate 2 closed the unit-level gap with three
controls and left the sequence-level gap open. One lifecycle fixture closes both.

**6. File the `loop.py:4673` issue.** `GATE-02-REVIEW.md` § 8 item 1 says it needs one and
neither close could file it (no network to GitHub from a dispatched session; `gh` fails
with a TLS error here). It has now survived two closes as a documented finding with no
tracking artifact, which is how findings get lost.

**Gate 1's seven items, restated with their status:** items 1 (frontmatter-marked accepted
hedge), 2 (`loop.py:4673`), 3 (`--recheck-verdict` CLI test), 4 (`.claude/skills/` symlink
drift), 6 (`/arm-gate` terminal guard), and 7 (`sync-scaffold.sh` does not sync `docs/`)
are **all still open** — none was in gate 2's scope, and `GATE-02-REVIEW.md` § 8 routed
1, 3, and 4 out deliberately. Item 5 (estimate driver-internals WUs below the median) was
**applied in gate 2 and is superseded by item 2 above.**

---

## Lessons promoted

Four entries appended to `.specfuse/LEARNINGS.md`, tagged `[FEAT-2026-0070/G2-CLOSE]`:

1. **A machine-readable marker embedded in a prose artifact is forgeable by the prose that
   documents it** — scope the scan, or make the token unquotable. Executed evidence, not a
   hypothetical.
2. **Cost variance tracks how many distinct things a WU must prove, not whether its test
   file already exists** — with both gates' data as the paired observation, including the
   correction of gate 1's own lesson.
3. **An arm-time reprice silently invalidates the close's as-drafted baseline when the
   resulting delta sits under the linter's threshold** — a noise threshold is also an audit
   blind spot.
4. **A marker-gated guard that reports zero across all history is untested end-to-end by
   construction, and its terminal close must not count its own vacuous pass as evidence** —
   the fixtures prove the function; only a real sequence proves the guard.

Not promoted, deliberately: the `/accept-hedged-close` reflexivity (the skill's first real
invocation being on the feature that shipped it) — it is a one-off consequence of ordering,
not a rule, and it is recorded in the hedged follow-up record where an operator will meet
it. Also not promoted: the sizing-trigger scoping and the missing issue, both single-site
process fixes that live in *What I'd change* where a fix can find them.
