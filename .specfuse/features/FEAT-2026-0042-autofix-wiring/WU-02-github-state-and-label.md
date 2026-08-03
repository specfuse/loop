---
id: FEAT-2026-0042/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
produces:
  - specfuse/monitor/autofix_state.py
  - specfuse/loop/labels.py
  - tests/test_autofix_state.py
produces_driver_helper:
  - AUTOFIX_FAILED_LABEL
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-08-03T22:38:30.799757+00:00
duration_seconds: 1195.123
cost_usd: 2.735571
input_tokens: 94
output_tokens: 36548
---

# GitHub is the state: attempt records, the daily cap, and the failure label

**Objective.** Ship the durable state autofix needs — a record of which fingerprints
have had an attempt, and a daily-cap query — held on the GitHub issue itself, plus
registration of the `auto-fix attempted, failed` label in the existing label registry.

**Context.** Correlation ID `FEAT-2026-0042/T02`. Read `PLAN.md` first, especially the
trap about ephemeral runners. Do not reopen that decision.

**The trap, stated so it is not rediscovered.** The harvester's runners are
**ephemeral** — FEAT-2026-0040 ships a GitHub Actions runner and FEAT-2026-0043 will
add an AKS CronJob. A state file on local disk is gone by the next invocation, so
"one fix run per fingerprint" would fire once per *run* and the daily cap would never
bind. It would fail **silently**, which is the worst shape available: the guardrail
reads as present in the code and does nothing in production.

**Follow `issues.py`; do not invent a second convention.** That module already holds
state on the issue body and reads it back:

```
_MARKER_TEMPLATE = "<!-- specfuse:finding fingerprint={fingerprint} -->"
_META_TEMPLATE   = "<!-- specfuse:finding-meta occurrences={occurrences} last_seen={last_seen} -->"
_QUIET_MARKER    = "<!-- specfuse:finding-quiet-annotated -->"
_parse_meta(body)
```

Autofix attempt state is the same shape. Mirror the marker convention and the
client-side re-check discipline — the documented rule there is that the marker in the
body, re-checked client-side, is the sole authority.

**Register the label; do not hardcode it at a call site.** `specfuse/loop/labels.py`
owns `LABEL_REGISTRY` (FEAT-2026-0071). FEAT-2026-0040 shipped code that queried a
label the registry did not declare, and `gh issue create` rejected **every** finding
until someone made it by hand — issue #300, a whole feature's output blocked on one
missing declaration. Add the failure label to the registry.

**Every external call goes through the injected runner.** `LEARNINGS
[FEAT-2026-0031/G1-CLOSE]`: a *partial* seam is worse than none, because it reads as
covered. `gh_backend.py` took a `runner=` injection but called `subprocess.run`
directly in one probe, so the stub intercepted the create and the probe escaped to the
real binary — every test passed and the probe was never exercised. Audit this module
for raw calls and assert zero direct hits.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

## The contract

Two readers and one writer, all taking an injected runner:

- **has an attempt been recorded for this fingerprint** — reads the issue body marker.
- **how many autofix attempts today** — the daily cap query, over recently-labelled
  issues rather than a counter anyone has to trust.
- **record an attempt** — writes the marker, idempotently. Recording twice for one
  fingerprint must not produce two markers or two counted attempts.

**Define "daily" explicitly** — the roadmap row does not. State the timezone and the
boundary semantics (rolling 24h window, or calendar day in UTC) in the module
docstring and hold it as a test. Leaving each caller to assume is how two callers
disagree.

**Acceptance criteria.**

1. `tests/test_autofix_state.py::TestAutofixState::test_attempt_record_is_idempotent`
   exists and **fails on HEAD before this WU runs** (`specfuse/monitor/autofix_state.py`
   does not exist, which counts as red).
2. That test records an attempt for one fingerprint twice against a stub runner and
   asserts the body carries exactly **one** marker and the attempt counts once. It
   passes after this WU's edits.
3. A test asserts the fingerprint check reads the marker from the issue body and
   re-checks client-side — a too-broad search result that does not carry the marker
   is not treated as a match.
4. A test asserts the daily-cap query's boundary at both edges: an attempt just
   inside the window counts, one just outside does not. The window's definition is in
   the module docstring and this test holds it.
5. A test asserts `AUTOFIX_FAILED_LABEL` is present in `LABEL_REGISTRY` with a name,
   colour, and description — and that `tests/test_label_registry_covers_consumers.py`
   passes, which is the guard that would have caught #300.
6. **Zero raw external calls.** Assert with
   `grep -n "subprocess\.\|requests\.\|urllib\|os\.system" specfuse/monitor/autofix_state.py`
   and quote the output — every GitHub call goes through the injected runner. A
   partial seam fails this criterion even if all tests pass.
7. A test asserts a runner that raises produces a clear negative rather than an
   exception escaping to the caller — a state read that crashes the harvester is
   worse than one that reports "unknown", which T01 treats as fail-closed.
8. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `specfuse/monitor/autofix.py` — T01 owns the predicate; this module
is the state it reads through an injected reader. `specfuse/monitor/issues.py` — mirror
its convention, do not edit it; the finding-issue lifecycle is FEAT-2026-0040's.
`.specfuse/skills/fix-bug/` — T03 owns it. `specfuse/monitor/diagnosis.py`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Criterion 6 is load-bearing and
is a *grep*, not a test — the defect it guards against is invisible to a passing
suite by construction, which is exactly how `[FEAT-2026-0031/G1-CLOSE]` was missed.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
daily cap cannot be answered from GitHub without a query that would be rate-limited
in normal operation (say so, name the call volume — do not fall back to local state,
which is the trap this WU exists to avoid); the marker convention collides with
`issues.py`'s existing markers; or registering the label breaks an existing
`LABEL_REGISTRY` consumer. Do **not** invoke `fix-bug`, create a branch, open a pull
request, or make any writing `gh` call against a real issue from this work unit —
gate 1 fires nothing and all tests here use a stub runner.
