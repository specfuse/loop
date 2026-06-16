## Gate 1 — auto-closed (predicate=v1)

On-plan intermediate close; full close-intermediate ceremony
skipped per `evaluate_auto_close`. `plan-next` WU dispatched
to draft gate 2.

- feature_id: FEAT-2026-0024
- predicate_version: v1
- gate_total_cost: $4.69
- gate_budget: <unset>
- reasons: [] (auto=True)

## Gate 2

The issue/PR-body leak guard (#46). Two substantive WUs, both single-attempt,
both passed clean. Evidence cited from `events.jsonl`.

### FEAT-2026-0024/T03 — content-scan runner (`leak_scan_content.py`)

- **What worked.** Passed on attempt 1 (`attempt_outcome` 2026-06-16T21:36:19Z,
  `outcome: passed`, cost $1.24, 236s). The `depends_on: []` framing held: gate 1
  was the real barrier — the committed `leak_denylist.hashes` and the
  `load_hashed_denylist` / `hashed_denylist_hits` / `scan_text` primitives
  already existed, so the runner reused `leak_scan` as a library rather than
  re-deriving the scanner. Red→green proof landed (`test_leak_scan_content.py`),
  and the self-leak escalation (trigger 3) was respected: the planted denylist
  hit and `.hashes` were built in `tmp_path`, so no committed fixture carries a
  denylisted string and `leak-scan --all` stayed clean.
- **What failed.** Nothing. 0 re-arms, 1 attempt.
- **Attempt count.** 1.

### FEAT-2026-0024/T04 — Action workflow + docs

- **What worked.** Passed on attempt 1 (`attempt_outcome`
  2026-06-16T21:38:31Z, `outcome: passed`, cost $0.72, 133s — the cheapest WU in
  the feature). It only wired the T03 seam to `.github/workflows/leak-scan-content.yml`
  (triggers `issues`/`pull_request` opened+edited, `issue_comment`
  created+edited; `permissions: contents: read`, no write scope) and authored
  `docs/leak-scan-content-action.md`. The red-test exemption was correct: the
  behavioral test lives in T03; the live trigger is operator-deferred.
- **What failed.** Nothing. 0 re-arms, 1 attempt.
- **Attempt count.** 1.

### Cross-gate note — G1-PLAN leak-scan self-poison (gate 1's closing sequence)

Not a gate-2 WU, but the feature's most instructive failure and the source of a
durable lesson. `G1-PLAN` attempt 1 hit `outcome: squash_commit_failed`
(2026-06-16T20:50:23Z): the pre-commit `leak-scan` hook rejected the bookkeeping
squash with `leak-scan: FINDINGS  line 97: email: 'git@github.com'`. The
offending string was the `git@github.com` config address embedded in a
`failure_excerpt` the driver had recorded **into `events.jsonl`** on T02's
attempt-1 failure — i.e. the leak-guard feature poisoned its own loop
bookkeeping. Attempt 2 passed ($2.52). Driver fix `02db0af` ("stop
bookkeeping-commit crash on leak-scan self-poison") closes the class. See the
durable lesson below.

## Guard-helper existence audit

Per AC2 and the recursive-dogfood discipline ([FEAT-2026-0008/G1-CLOSE]): an
unwired or absent deliverable is a hollow pass. Every gate-2 shipped surface was
checked on disk; **all present, none hollow.**

| Surface | Path | Result |
| --- | --- | --- |
| Action workflow | `.github/workflows/leak-scan-content.yml` | ✅ present, 42 lines |
| Scan-runner | `.specfuse/scripts/leak_scan_content.py` | ✅ present, 159 lines |
| Runner unit tests | `tests/test_leak_scan_content.py` | ✅ present, 136 lines |
| Runner docs | `docs/leak-scan-content-action.md` | ✅ present, 95 lines |

Symbol-existence (the wiring check, not only the file):

- `PYTHONPATH=.specfuse/scripts python3 -c "import leak_scan_content as m; ..."`
  → `scan_event True  main True` — both runner entry points exist and import.
- `grep 'leak_scan_content.py' .github/workflows/leak-scan-content.yml` → the
  Action invokes the runner (the workflow is wired to the seam, not a dead file).
- `docs/leak-scan-content-action.md` carries `edit history` (§ Limitation, line
  58) and `event payload` (lines 27, 81) — the documented limitation is real.

No absence found. The verdict below is therefore eligible to claim the surfaces
shipped; it does **not** claim the *live* oracle is met (see AC6).

## Cost analysis

Planned vs actual, reconciled from `events.jsonl` (sum of `cost_usd` across all
attempts per WU). Full planned set = PLAN.md's original five ($11.50) **plus**
the two gate-2 substantive WUs G1-PLAN drafted (T03 $2.50 + T04 $2.00) = **$16.00**.

| WU | Planned | Actual | Attempts | Delta |
| --- | --- | --- | --- | --- |
| T01 (hashed-denylist core) | $2.50 | $1.42 | 1 | −$1.08 |
| T02 (CI wiring + generator) | $2.50 | $3.27 | 2 | +$0.77 |
| G1-CLOSE-INTERMEDIATE | $2.00 | $0.00 | auto (no agent) | −$2.00 |
| G1-PLAN (plan-next) | $2.00 | $5.23 | 2 | +$3.23 |
| T03 (content-scan runner) | $2.50 | $1.24 | 1 | −$1.26 |
| T04 (Action workflow + docs) | $2.00 | $0.72 | 1 | −$1.28 |
| G2-CLOSE (this WU) | $2.50 | (recorded by driver post-attempt) | 1 | — |
| **Total (excl. G2-CLOSE)** | **$13.50** | **$11.88** | | **−$1.62** |

Per-gate:

- **Gate 1** (T01 + T02 + G1-CLOSE-INTERMEDIATE + G1-PLAN): planned $8.50, actual
  **$9.92**, over by **+$1.42**. The overage is entirely G1-PLAN's second attempt
  (+$3.23 vs plan): the leak-scan self-poison squash failure (above) forced a
  re-attempt. Offset partly by the $0 auto-closed intermediate and a cheap T01.
  Note the $4.69 in the Gate-1 stub above is T01+T02 only — it was computed at
  intermediate auto-close time, *before* G1-PLAN ran, so it under-counts gate 1.
- **Gate 2** (T03 + T04): planned $4.50, actual **$1.96**, under by **−$2.54** —
  both single-attempt, T04 trivially cheap (pure wiring + prose).

Feature actual to date = **$11.88** (excluding this close WU). Against the full
$16.00 planned set the feature is comfortably under even before G2-CLOSE lands.

## Docs reconciliation

- The **edit-history limitation** is documented — `docs/leak-scan-content-action.md`
  § "Limitation: edit history is not expunged" (lines 58–77): the guard stops
  *new* leaks on open/edit but cannot expunge already-published body revisions
  (GitHub retains edit history); removal stays a delete+recreate / GitHub-Support
  operation. Full-comment-history scanning is documented out of scope (§ lines
  79–82). Authored by T04; confirmed present here, not rewritten (T04 owns it).
- The **`.specfuse/roadmap.md` row** is **not hand-flipped**. The driver flips it
  only on `verdict: met`; this close emits `verdict: partially_met` (live oracle
  operator-deferred), so the row stays `active` until the operator confirms the
  live Action run post-merge. Reconciled in the verdict, not edited here.

## What the loop did NOT verify

| Criterion | Why deferred | Where it actually happens |
| --- | --- | --- |
| Issue #46 headline: the live `issues`/`pull_request`-triggered Action flags a planted denylisted string in a real issue/PR body on open/edit | Runs only in a real GitHub Actions environment; in-loop coverage is unit tests over the runner against fixture JSON. No `act`/Docker emulation in-loop (PLAN.md "Gate-2 oracle"; precedent `[FEAT-2026-0020/G2/out-of-loop-completion]`). | Operator, post-merge: open a test issue/PR with a planted placeholder denylisted string and confirm the `leak-scan-content` check fails; then a clean issue passes. Recorded as the load-bearing oracle for #46. |

One deferred entry (issue #46's live trigger). Gate 2 has 12 substantive
acceptance criteria (T03 ×8, T04 ×4); 1/12 ≈ 8% deferred, ≤ 2 entries and < 30% —
**within bounds, no sizing flag required** under `## What I'd change`.

## What I'd change

- The G1-PLAN self-poison cost a full re-attempt (+$3.23). It is now fixed at the
  driver level (`02db0af`) and captured as a durable lesson, so future leak-guard
  features will not pay it again. Nothing else in the gate-2 arc warrants change —
  both substantive WUs landed first-try, clean.

# Feature-arc verdict

**`verdict: partially_met`** (frontmatter). The driver fires terminal flips only
on `met`; it holds them here pending the operator's live-Action confirmation.

`roadmap_goal`: *"CI catches re-introduction of private org-names (not just
gitleaks secrets) in both tracked files and GitHub issue/PR bodies, without
committing the literal private strings to the public repo."* Assessed across both
surfaces, citing the AC2 audit (all surfaces present, none hollow):

- **Surface 1 — tracked files (#45): MET, in-loop.** Gate 1 shipped the
  salted-SHA-256 sliding-window hashed denylist and wired it into `scan_repo` /
  `leak-scan --all`, so CI gains private-org-name coverage using only the
  **committed** `leak_denylist.hashes` — the gitignored plaintext literals never
  reach the public repo. Verified by T01/T02 tests passing and `--all` clean.
- **Surface 2 — issue/PR bodies (#46): SHIPPED, oracle operator-deferred.** The
  runner (`leak_scan_content.py`, unit-tested: planted hit → non-zero, clean → 0,
  fail-closed on missing payload) and the Action (`leak-scan-content.yml`,
  triggers on issue/PR/comment open+edit, fails the check on a hit) are both
  present and wired (AC2 audit). What is **not** confirmed in-loop is the *live*
  GitHub Actions run flagging a planted string — that oracle is operator-deferred
  (AC6) and runs only in a real Actions environment.

Both surfaces are **built and the no-self-leak constraint is satisfied** (no
committed literal private string; `leak-scan --all` clean throughout). The goal
is therefore **partially met**: fully met and in-loop-verified for tracked files;
shipped-but-live-unconfirmed for issue/PR bodies. Per AC7 / escalation trigger 3,
the honest verdict while the live Action is unconfirmed is `partially_met`, not
`met` — the driver holds the `PLAN.md status -> done`, gate `passed`, roadmap
row, and archive flips until the operator confirms the live run. No raced-close
conflict: `roadmap.md` row 42 still reads `active`.
