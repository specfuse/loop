---
id: FEAT-2026-0051/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
oracle_env: macos_local
produces_driver_helper: format_preexisting_gate_failure, baseline_evidence_diffstat
produces:
  - specfuse/loop/loop.py
  - tests/test_baseline_escalation_message.py
---

# Write the halt message a non-expert operator can act on

**Objective.** Turn T01's minimal halt into an escalation a non-expert operator
can act on without reading driver source: which gate is red, the exact failing
signature, proof the base tree is unchanged so no WU caused it, and what to do
next.

**Context.** Part of FEAT-2026-0051, third WU; depends on T02. Read `PLAN.md` for
the scope boundary — in particular that v1 has **no waiver**, so the message must
not offer a "proceed anyway" option that does not exist.

The failure this message is written for: an operator watched two WUs burn a full
attempt budget and had to diff a lockfile by hand to discover the failure
pre-dated the feature. The message's job is to hand them that conclusion, not the
raw evidence to re-derive it. A dump of the failing gate's stdout is **not** the
deliverable — that is what the driver already prints and what nobody could read.

Evidence payload: `git diff <integration-branch>...HEAD --stat`, where the
integration branch is resolved through FEAT-2026-0031's existing configurable
integration-branch mechanism (find it; do not hardcode `main`). An empty diffstat
for the files the failing gate reads is the strongest available proof that the
feature did not cause the failure — it is the exact evidence shape the original
report used.

Binding rules in `.specfuse/rules/` apply. Do not restate them.

**Acceptance criteria.**
- `tests/test_baseline_escalation_message.py::test_message_names_gate_signature_and_proof`
  exists and **fails on HEAD before this WU's edits**. It asserts the rendered
  message contains the failing gate's name, its failure signature, and the
  diffstat evidence section.
- After this WU's edits that test passes.
- The message states, in plain sentences, that **no work unit caused this
  failure** and that **zero work units were dispatched**. A test asserts both
  claims are present — they are the two facts that took an operator hours to
  establish by hand.
- The message lists the operator's actual v1 options: fix the debt on the
  integration branch (typically via `/fix-bug`, so the feature branch inherits
  it on rebase), or defer the feature. A test asserts the option list does not
  contain any resume-with-waiver instruction — the waiver is FEAT-2026-0052 and
  offering a flag that does not exist is worse than offering nothing.
- The message names FEAT-2026-0052 in one sentence as where the
  proceed-anyway path is tracked, phrased as future work rather than an
  available action.
- `baseline_evidence_diffstat()` resolves the integration branch through the
  existing configuration mechanism, not a hardcoded branch name. A test with a
  non-`main` integration branch asserts the configured value is used.
- When the diffstat cannot be produced (no integration branch configured, git
  failure, shallow clone), the message degrades to naming the gate and signature
  with an explicit "base-tree comparison unavailable" line, and the halt still
  fires. A test covers the degraded path. Evidence collection must never be the
  reason a halt fails to fire.
- The same rendered message text is written into the `human_escalation` event
  payload, so the audit log carries what the operator saw — asserted by a test
  reading the event.
- The message is legible to someone who has never read the driver source: no
  bare internal symbol names as the primary explanation, no raw stdout dump as
  the body.

**Do not touch.** The probe itself and the halt's control flow (T01); the
persistence and kill-switch (T02); `verify()`'s semantics. `.git/`, secrets. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus a symbol
check: `python3 -c "from specfuse.loop.loop import
format_preexisting_gate_failure, baseline_evidence_diffstat"` exits 0. Note the
leak-scan gate reads escalation prose — keep real paths, org names, and home
directories out of message templates and test fixtures. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if FEAT-2026-0031's integration
branch configuration cannot be read from the escalation site without threading
new state through the run loop — a hardcoded `main` would silently produce wrong
evidence on any project using a different integration branch, which is worse than
the degraded path. Also block if a leak-scan finding traces to the message
template itself and the fix is not obviously a placeholder substitution. If
either named symbol is absent from the files you edited, emit `status: blocked` —
do not claim complete. Blocked is respectable (`result-contract.md` rule 4).
