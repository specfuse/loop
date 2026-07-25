<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# RETROSPECTIVE — FEAT-2026-0037, adopt ruff's correctness rule families

Single-gate feature: two substantive WUs (T01 subprocess, T02 exceptions) plus
this terminal close. Written by `FEAT-2026-0037/G1-CLOSE`.

## Oracles re-run fresh (close-discipline §1)

Every command below ran **in this close session**, exit code read directly —
nothing inherited from T01/T02's self-report.

| oracle | command | observed |
|--------|---------|----------|
| ruff version ≥ 0.16 | `ruff --version` | `ruff 0.16.0` |
| lint gate | `ruff check specfuse .specfuse/scripts tests scripts` | `All checks passed!`, exit `0` |
| suite | `python3 -m unittest discover -s tests -q` | `Ran 1295 tests in 38.142s` / `OK (skipped=3)`, exit `0` |
| ruleset | `grep -A25 '^\[tool.ruff.lint\]' pyproject.toml` | `pyproject.toml:61` → `select = ["E4", "E7", "E9", "F", "PLW1510", "B", "BLE001", "S110", "TRY004"]` |

All five added codes (`PLW1510`, `B`, `BLE001`, `S110`, `TRY004`) are in
`select`, and the gate that enforces them is clean — so the adoption is
enforced, not decorative. No escalation trigger fired: no selected rule still
fires, no test fails, no code is missing from `select`.

## Gate 1

### T01 — subprocess correctness (`WU-01-subprocess-correctness.md`)
- **Attempts:** 1 (passed first try). Cost `$2.261393` (events.jsonl).
- **Fix surface:** 21 files per the driver-recorded `files_touched` — 18 of them
  code/test files, plus `pyproject.toml` (the `select` edit) and bookkeeping.
  The bulk was `tests/` (13 files): the test suite shells out as much as the
  driver does, and no `per-file-ignores` carve-out was taken, deliberately.
- **Surprises:** none blocking. `PLW1510`'s fix is mechanical in shape (add an
  explicit kwarg) but semantic in content (which value), and the split fell out
  of the call site itself: anything that already reads `.returncode` took
  `check=False`, everything else `check=True`.

### T02 — exception correctness (`WU-02-exception-correctness.md`)
- **Attempts:** 1 (passed first try). Cost `$0.826306` (events.jsonl).
- **Fix surface:** 5 files per `files_touched` — `specfuse/loop/loop.py`,
  `specfuse/loop/validate_event.py`, `tests/test_loop_gate_budget.py`,
  plus `pyproject.toml` and its own WU file.
- **Surprises:** narrowing was cheap where the raising call was obvious
  (`validate_event.py` now catches `(OSError, json.JSONDecodeError)`,
  `SchemaError`, `json.JSONDecodeError` — no catch-all left in that module),
  but three catch-alls in `loop.py` are *intentional driver guards* and were
  resolved with a justified `noqa: BLE001` rather than a narrowing. See
  "genuinely ambiguous" below and follow-up **FU-1**.

### Failure-class breakdown

(no non-passing attempts in scope)

Both substantive WUs passed on attempt 1; the only non-passing attempts in this
feature are this close WU's own two prior attempts (excluded from the breakdown
by design, issue #145 — and, separately, absent from `events.jsonl`; see
**Cost analysis**).

## Retrospective

### How many findings were fixed

The five codes report **zero** findings today (fresh run above). The honest
per-code *pre-fix* count is **not reconstructible in this session**: neither
producing WU recorded its finding count, and this close is barred from running
`git` (the driver owns git), so the pre-fix tree is not readable from here. What
is measurable and reported instead:

- **Post-fix invariant:** `0` findings for `PLW1510`, `B`, `BLE001`, `S110`,
  `TRY004` across all four gate directories.
- **Fix surface** (driver-recorded `files_touched`, not self-report): T01 = 18
  code/test files; T02 = 3 code/test files. That bounds where the findings were.
- **Suppression census** (measured today): exactly **3** `noqa: BLE001` in the
  whole tree (`specfuse/loop/loop.py:2217`, `:4670`, `:5043`), and **zero**
  `noqa` for `PLW1510`, `B`, `S110`, or `TRY004`. Nothing was silenced wholesale.

This gap is the feature's most useful lesson — see **Lessons**, entry 1.

### `check=True` vs `check=False`

AST census over `specfuse`, `.specfuse/scripts`, `tests`, `scripts` (this
session): **232** `subprocess.run` call sites —

| shape | count |
|-------|------:|
| `check=True` | 184 |
| `check=False` | 47 |
| explicit-by-parameter | 1 |
| implicit (no `check=`) | **0** |

`check=False` concentrates where exit codes are data, not failure:
`specfuse/loop/loop.py` (21 sites — probing `git` state, running gate commands
whose non-zero exit *is* the verdict, dispatching the agent), the leak-scan and
upgrade-merge-gate scripts (5), and tests that assert on `returncode` (22).
Every one of the non-test `check=False` sites passes `capture_output=True` and
inspects the result — the pattern the WU required, visible at the call site.

### Genuinely ambiguous

1. **`specfuse/loop/gh_backend.py:23`** — `_default_runner(args, check: bool = True)`
   passes `check=check` through. Neither literal is right for the whole helper:
   the `gh pr view` idempotency probe must inspect `.returncode` without
   raising, while side-effecting callers want the raise. Resolved by making
   `check` a parameter with a `True` default — explicit at the boundary, decided
   per caller. This is the durable pattern (Lessons, entry 2), not a workaround.
2. **The three `loop.py` catch-alls.** `:2217` (parse of agent stdout — the
   least-trusted input in the system; must degrade to "verify() decides", never
   crash), `:4670` (a warn-only lint hook — binds `_exc` and surfaces it in the
   warning, the shape T02's criterion actually asked for), `:5043` (malformed
   `.specfuse/config` → treat as absent). Two of the three (`:2217`, `:5043`)
   satisfy the linter via `noqa` + a reason comment but do **not** bind or log
   the exception, which is the strictest reading of T02's criterion. The
   catch-alls are correct as *behavior* (a driver guard must not crash); what is
   unmet is the "bind and log" half. Recorded as **FU-1** rather than fixed here
   — this WU writes only its close record and must not touch source.
3. **No latent bug was exposed.** No `check=True` addition made a previously
   passing test fail, and no `check=False` site turned out to be masking a real
   failure: every one already inspected `.returncode`. The rule's value here is
   prospective (the *next* silently-ignored subprocess is now a lint error), not
   a bug caught today. Saying otherwise would overstate the return.

## What I'd change

1. **Require the pre-fix count as an acceptance criterion.** T01/T02 each
   asserted "reports zero findings" — an invariant a hollow pass satisfies
   identically. `ruff check --statistics --select <codes>` *before* the fix,
   quoted in the WU, costs one command and makes the close's arithmetic real.
2. **Split the census from the fix.** T01 touched 18 files across driver and
   suite in one WU; a 5-minute census WU ("how many sites, which dirs, which
   already explicit") would have sized T01 honestly — it was planned at `$8.00`
   and cost `$2.26`.
3. **Make "no unbound catch-all remains" its own criterion.** T02's BLE001
   criterion offered "narrow **or** bind-and-log"; `noqa` + comment is a third
   path the linter accepts and the criterion did not name. Name the third path
   explicitly — allow it or forbid it, but decide at draft time.
4. **Enumerate the doc surfaces that copy gate commands.** `CONTRIBUTING.md`
   carries its own copy of the ruff command and it had already drifted (see
   **Docs**). The repo's "change all three" note lists three surfaces; there are
   four.

## Lessons

Three entries appended to `.specfuse/LEARNINGS.md` (tagged `[FEAT-2026-0037]`,
`[FEAT-2026-0037/T01]`, `[FEAT-2026-0037/T02]`):

1. **A lint-adoption WU must record its pre-fix finding count.** The post-fix
   invariant ("zero findings") is exactly what a hollow pass also shows, and the
   close cannot reconstruct the delta — it is git-barred by the result contract.
   The count must be captured by the WU that had the dirty tree in front of it.
2. **`PLW1510` on a shared subprocess helper wants a `check: bool = True`
   parameter, not a literal.** When one runner serves both probing and
   side-effecting callers, either literal is wrong for half the callers:
   `check=True` breaks the probes, `check=False` re-hides the failures the rule
   exists to surface.
3. **`BLE001` has a linter-satisfying escape hatch that leaves the swallow
   intact.** `noqa: BLE001` + a reason comment turns the gate green without
   binding the exception. A WU that intends "narrow, or bind-and-log" must
   assert "no unbound catch-all remains" as its own criterion.

## Docs

**No contributor doc should enumerate the ruleset.** The rationale and the
authoritative list live in `pyproject.toml` `[tool.ruff.lint]` (a 9-line comment
explaining why the `select` is pinned explicitly, extended by this feature);
copying the code list into prose would create the exact drift surface
FEAT-2026-0036 was about. Docs touched by this close: **`RETROSPECTIVE.md`**
(this file) and **`.specfuse/LEARNINGS.md`**.

One real drift found while checking, **not fixed here** (out of scope — this WU
writes only its close record): `CONTRIBUTING.md:69` documents the lint gate as
`ruff check .specfuse/scripts tests scripts`, missing the `specfuse` directory
that `.specfuse/verification.yml:20` and `scripts/smoke-test.sh:51` both
include. Pre-existing, unrelated to this feature's ruleset change, and the
narrower documented command would *hide* findings in the driver package.
Recorded as **FU-2**.

## Follow-ups

- **FU-1** — `specfuse/loop/loop.py:2217` and `:5043`: intentional catch-alls
  suppressed with `noqa: BLE001` without binding/logging the exception. Bind and
  log (the `:4670` shape) or accept the `noqa` as policy and say so in the
  ruleset comment. Small, source-touching; belongs in a bug-fix branch, not this
  close.
- **FU-2** — `CONTRIBUTING.md:69`: lint command missing the `specfuse` directory;
  out of sync with `.specfuse/verification.yml` and `scripts/smoke-test.sh`. Fix
  alongside a note that four surfaces (not three) copy the gate commands.

## Cost analysis

Planned from per-WU `planned_cost_usd` frontmatter; actual from `events.jsonl`.

| unit | planned | actual | delta |
|------|--------:|-------:|------:|
| T01 subprocess | $8.00 | $2.261393 | −$5.74 (−72%) |
| T02 exceptions | $4.00 | $0.826306 | −$3.17 (−79%) |
| **substantive total** | **$12.00** | **$3.087699** | **−$8.91 (−74%)** |
| G1-CLOSE (this WU, 3rd attempt) | $5.00 | not in `events.jsonl` | unmeasurable (see below) |
| **feature total** | **$17.00** | **≥ $3.09** | **≤ −$13.91 (−82%)** |

Per-WU planned sum (`$8.00 + $4.00 + $5.00 = $17.00`) matches `PLAN.md
planned_cost_usd: 17.00` — the plan was internally consistent.

**Delta named: the plan overestimated by ~4× on the substantive work.** Two
causes, both estimation, not scope: (a) T01 was sized as "review ~230 subprocess
call sites by hand," but the review collapsed to a one-bit decision per site
(does this code already read `.returncode`?), which is cheap; (b) the ruleset was
scoped narrowly on purpose (specific codes, not whole `S`/`TRY` families), so
finding volume stayed small — the scope discipline that kept the feature safe
also made the estimate too big.

**Gap in the event log, reported not smoothed over:** `events.jsonl` holds 6 rows,
all for T01/T02; there is **no** `attempt_outcome` row for `FEAT-2026-0037/G1-CLOSE`
even though this WU's frontmatter reads `attempts: 2`. So this close's own spend
(two failed attempts plus this one) is not reconcilable from the event log — the
`≥` and `≤` in the table are literal. Even sizing the three close attempts at
T01/T02-class cost (~$1–2 each) lands the feature near $6–9, still well under the
$17.00 plan.

## What the loop did NOT verify

Three items. Each names why, and where it actually gets verified.

1. **Test-count equality with pre-feature `HEAD`** (T01 AC4: "the full suite
   passes with the SAME test count as HEAD"). This close observed `Ran 1295
   tests … OK (skipped=3)` but cannot compare against the pre-feature count —
   that needs `git`, which the result contract bars this session from running.
   Inherited from T01's self-report, not re-verified. **Upgrade condition:** the
   PR's CI run plus the operator's diff review (a deleted or silenced test would
   appear in the diff).
2. **Pre-fix per-code finding counts.** Not recorded by T01/T02 and not
   reconstructible here (same git bar). The close verified the invariant that
   matters for enforcement — zero findings under the selected codes — but cannot
   state the fixed-count arithmetic. **Upgrade condition:** operator review of
   the two commits on the PR; prevented in future by Lessons entry 1.
3. **Runtime behavior of the added `check=True` on live failure paths.** Adding
   `check=True` changes behavior (raise instead of continue) on paths the suite
   does not drive to failure — real `git`/`gh`/gate-command non-zero exits in a
   live driver run. The suite is the declared regression oracle (§12 carve-out)
   and it is green, but "a real subprocess actually failed and the driver raised
   sensibly" is not in-loop evidence. **Upgrade condition:** the next real
   driver run on this branch (which is itself a `git`-heavy exercise of these
   call sites) plus CI on the PR.

## Consumer-visible contract changes

`n/a — no consumer-visible contract change`

The feature adds rule codes to a dev-lint `select` and makes existing
`subprocess.run` calls declare `check=` explicitly. No API surface, CLI flag,
scaffold file, published schema, or event shape was added, removed, or renamed.
The one behavioral change is internal and intentional (a previously-ignored
non-zero exit now raises inside the driver); no consumer-facing contract moved.

## Terminal verdict — `met`

Every acceptance criterion of this close is satisfied in-session: the four
required sections exist, the oracles were re-run fresh with exit codes read
directly (`ruff 0.16.0`; lint clean; 1295 tests `OK`; all five codes in
`select`), the cost reconciliation names its delta and its one gap, the deferred
list is enumerated with upgrade conditions, and the contract-change line is the
reviewed `n/a`. The three deferrals above are bookkeeping and
live-path-observation gaps inherited from T01/T02 — none of them is this
feature's own oracle, and this feature's oracle (the lint gate the ruleset now
pins, plus the suite) ran green here. Hence `met` rather than `met_locally`.
