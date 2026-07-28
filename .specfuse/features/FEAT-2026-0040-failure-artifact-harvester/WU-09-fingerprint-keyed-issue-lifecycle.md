---
id: FEAT-2026-0040/T09
type: implementation
status: draft
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
produces:
  - specfuse/monitor/issues.py
  - tests/test_monitor_issue_lifecycle.py
model: sonnet
effort: high
gate_set: code
---

# One fingerprint, one issue — the finding lifecycle

**Objective.** Ship the fingerprint-keyed GitHub issue lifecycle: find-or-create one
issue per fingerprint, update its occurrence count on repeat sightings under a
throttle, and annotate a fingerprint that has gone quiet — **without ever closing
it**.

**Context.** Correlation ID `FEAT-2026-0040/T09`. Gate 3, no dependencies — every
input it needs is `done`: `T02`'s `fingerprint_artifact`, `T03`'s `redact_artifact`,
and the adapters of gate 2. This is the step where the feature's whole point lands:
"a poison message becomes one evidence-rich issue within a polling cycle,
deduplicated across thousands of occurrences" (`PLAN.md`'s `roadmap_goal`).

**`escalation.py` is reused, not reimplemented — with one deliberate exception, and
that exception is the point of this unit.** `PLAN.md`'s existing-mechanism search
recorded the verdict `found, reusing`:
`grep -n "^def \|marker" specfuse/loop/escalation.py` surfaces `_correlation_marker`,
`_find_existing_issue`, `_default_runner`, `_extract_issue_number`, and idempotent
find-then-create. This unit reuses:

- **the injected-runner seam** — a `runner(args, check=...)` callable defaulting to
  `_default_runner`, which is what makes every test in this unit stub-driven;
- **`_extract_issue_number`** — the `/issues/(\d+)` parse of `gh issue create`'s
  stdout;
- **the HTML-comment marker convention** and the **find-then-create ordering**,
  including the `marker in body` re-check on every candidate row.

**What it does NOT reuse is `_find_existing_issue`'s search strategy, because
FEAT-2026-0046's own retrospective records it as unsafe for exactly this use.**
Verbatim from that retrospective: *"`_find_existing_issue` passes an HTML comment to
GitHub's `--search`, and GitHub's issue search index does not reliably tokenise HTML
comment content. The code does re-check `marker in issue["body"]` on each returned
row, so a search that matches too broadly degrades safely; a search that returns
**nothing** does not — it silently files a duplicate on every retry."*

For an escalation that fires a handful of times, a duplicate is noise. **For a
harvester whose entire value proposition is deduplication across thousands of
occurrences, a finder that intermittently returns nothing is the one defect that
makes the feature worthless while every gate stays green.** 0046 named the fix in
the same paragraph — *"drop `--search` and filter `gh issue list --label needs-human
--json number,body` client-side, which the existing body re-check already makes
correct"* — and this unit implements it, plus two hardenings that same failure mode
suggests:

- **An explicit `--limit`.** `gh issue list` pages, and a truncated list is
  indistinguishable from "no existing issue" — the identical failure by a different
  route. The limit is explicit and, when the returned row count equals it, the
  finder must not report "not found"; it either pages on or refuses. Silence on a
  truncated page is what this criterion exists to prevent.
- **The fingerprint in the issue title as well as the marker.** GitHub *does* index
  titles, so a title-scoped narrowing stays available for large repositories — but
  correctness never rests on it. The marker in the body, re-checked client-side, is
  the authority; the title is an optimization and is asserted as such.

**Quiet-based auto-close stays out — no exception.** The roadmap's own words: a
finding may be annotated *"quiet for N runs — candidate for close"*, but **humans
close**. `PLAN.md`'s scope boundary lists this as OUT by deliberate design. A
lifecycle that closes an issue because nothing fired for a while is out of scope,
not a nice extra: it is the failure mode where a monitoring tool erases the evidence
of an intermittent fault. Criterion 9 is a negative observation over the recorded
call set, not a code review.

**Redaction is already done, and this unit must not undo it.** Artifacts arrive
redacted at the adapter boundary (`T03`, exercised by every gate-2 adapter). This
unit writes artifact text into an issue body — a public surface — so it re-asserts
the property at the point of egress rather than trusting the upstream. See
`security-boundaries.md`.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**In-loop evidence — read this before the acceptance criteria.**
`[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]` records that `gh` returns auth errors
inside `claude -p`. **This unit therefore produces no in-loop evidence about the
real GitHub surface**, and it is scoped accordingly:

- **Scope: stubbed runner.** Every criterion below is decidable against an injected
  stub that records the argument lists it is handed and returns canned JSON. That
  proves the lifecycle's branch logic, its argument construction, and its
  dedupe behaviour — which is real evidence about this unit's code.
- **Named deferred criterion (D-9), carried into `G3-CLOSE`.** *"A second harvest of
  the same fingerprint against a real repository creates no second issue."* The stub
  cannot prove it, because the stub returns whatever the test hands it; that is
  precisely the shape 0046's deferred item 2 took, and it is the one this unit is
  built to fix. **Its verification proxy is an operator-journal artifact**: the
  operator runs the harvester twice against a scratch repository with a planted
  finding, records both invocations and the resulting issue list in the feature
  folder's operator journal, and `G3-CLOSE` cites that record. A green stub suite is
  not evidence for D-9 and must not be reported as such.
- The forbidden shortcut is invoking the real `gh` binary from a test to manufacture
  evidence. Do not.

**Acceptance criteria.**

1. `tests/test_monitor_issue_lifecycle.py::TestFindingLifecycle::test_second_sighting_of_one_fingerprint_creates_no_second_issue`
   exists and **fails on HEAD before this WU runs** (the test file does not yet
   exist, which counts as red).
2. `specfuse/monitor/issues.py` defines a find-or-create entry point taking a
   fingerprint, a `FailureArtifact` (or a small finding record built from one), a
   repository, and an **injected `runner`** defaulting to `escalation.py`'s
   `_default_runner`. No test in this unit invokes the real `gh` binary.
3. **Reuse is asserted, not claimed.** A test asserts `specfuse/monitor/issues.py`
   obtains `_extract_issue_number` and the default runner from
   `specfuse.loop.escalation` rather than redefining them, and `grep -n "def "
   specfuse/monitor/issues.py` shows no re-implementation of the issue-number parse.
4. **The finder does not pass the marker to `--search`.**
   `grep -n '"--search"' specfuse/monitor/issues.py` returns no match. A test
   asserts the recorded `gh issue list` argument list contains `--label` and
   `--json number,body,title` and **no** `--search`, and that the marker match is
   performed client-side over the returned bodies.
5. **The `marker in body` re-check is load-bearing.** Given a listing containing one
   row whose body carries the marker and one whose body does not, the finder returns
   the first and only the first. Given a listing whose rows all lack the marker, it
   reports not-found and the create path runs.
6. **A truncated page is never reported as not-found.** The list call passes an
   explicit `--limit`. **Negative observation:** with a stub returning exactly
   `--limit` rows, none carrying the marker, the finder does **not** silently return
   not-found — it pages on, or raises with a message naming the truncation. A test
   asserts the chosen behaviour explicitly; whichever is chosen, "assume there is
   nothing more" is not it.
7. **Idempotence, the property this whole unit exists for.** Two consecutive
   lifecycle calls for the same fingerprint, against a stub whose listing reflects
   the first call's create, produce **exactly one** `gh issue create` in the recorded
   call set and return the same issue number twice.
8. **Distinct fingerprints do not collapse.** Two artifacts differing only in their
   target coordinates — the binding constraint inherited from FEAT-2026-0069 —
   produce two distinct fingerprints and **two** create calls. This is the same
   assertion `T02` and `T05` make, re-made at the surface where losing it is
   irreversible.
9. **Occurrence count updates, under a throttle, and nothing closes.** A repeat
   sighting updates the existing issue's occurrence record (a comment or a body
   edit — the unit chooses and documents which), and a second sighting inside the
   throttle window produces **no** further update call. **Negative observation:**
   across every path in this unit — new, repeat, throttled, and quiet — the recorded
   call set contains no `gh issue close`, no `--state closed`, and no
   `state:closed` label transition. Quiet-based auto-close is out by design; a test
   that only checks the happy path would not notice it being added.
10. **The quiet annotation annotates and stops there.** A fingerprint absent for N
    runs yields exactly one annotation whose text names it as a candidate for close,
    and the same negative observation as criterion 9 holds on that path. N is a
    named parameter, not a magic number.
11. **Redaction at egress.** A finding whose `observed_text` carries a planted
    synthetic secret yields an issue body in which no occurrence of that value
    survives; the redacted span reads as `<redacted:` + a short digest. Use a
    synthetic value that is not a real credential and not a denylisted token (see
    `security-boundaries.md`; the `leak-scan` pre-commit form is stricter than its
    CI form).
12. **`escalation.py` is not modified and not regressed.**
    `python3 -m unittest tests.test_escalation_emit tests.test_escalation_contract`
    exits zero, and `specfuse/loop/escalation.py` appears in no diff from this WU.
13. `python3 -m unittest tests.test_monitor_issue_lifecycle -v` exits zero after
    this WU's edits, and the `code` gate set passes in full — `tests`, `lint`,
    `security`, `coverage` (≥90%), `leak-scan`, `monitoring-example-lint`, and the
    `bats` suites.

**Do not touch.** `specfuse/loop/escalation.py` — this unit **reuses** it and
criterion 12 asserts it is unchanged. If its public shape cannot carry this reuse,
that is a cross-feature contract question and an escalation, not an edit.
`specfuse/monitor/artifact.py`, `fingerprint.py`, `redaction.py`, `schedule.py`,
`adapters.py`, and everything under `specfuse/monitor/providers/` — gates 1 and 2
own them and `T08` extends one of them; this unit consumes their output.
`specfuse/loop/gh_backend.py` — a different lifecycle on a different object.
The `specfuse-monitor run` CLI — `T10` owns it. Generated directories, secrets,
`.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, in declared
order. Plus the scoped red/green run in criteria 1 and 13, the greps in criteria 3
and 4, and the four negative observations in criteria 6, 9, 10, and 11 —
`verification-discipline.md` §3 requires the rule be observed rejecting a
purpose-built bad input, and every one of those four is a property that stays true
until someone adds a convenience. Note the `bats` `mktemp` sandbox effect recorded in
`[FEAT-2026-0072/G1-CLOSE]`: report which sandbox each gate ran under rather than
reporting a manufactured regression. **Report the D-9 deferral explicitly in the
RESULT block** — a `complete` that does not say the real `gh` surface was never
reached is the failure this unit's scoping exists to prevent.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
reusing `escalation.py`'s helpers requires changing its public shape — renaming a
helper, widening a signature, moving a constant — which is a cross-feature contract
question and not this unit's to settle; `FailureArtifact` cannot carry what an issue
body needs without a new field, which is `T01`'s model; criterion 6 cannot be
satisfied because `gh issue list`'s paging behaviour cannot be determined without
invoking the real binary (report it rather than guessing a limit); or satisfying
criterion 7 requires the stub to model GitHub's listing semantics precisely enough
that the test becomes a test of GitHub rather than of the lifecycle.
