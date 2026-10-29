---
id: FEAT-LOOP-2026-0203/T05
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - .specfuse/rules/design-for-diagnosis.md
  - specfuse/loop/data/rules/design-for-diagnosis.md
  - plugins/specfuse/skills/derive-monitoring/SKILL.md
  - plugins/specfuse/skills/derive-monitoring/PROMPT.md
  - .specfuse/skills/derive-monitoring/SKILL.md
  - .specfuse/skills/derive-monitoring/PROMPT.md
  - tests/test_derive_monitoring_discovery.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.27.1
started_at: 2026-10-15T03:40:06.444619+00:00
duration_seconds: 91.879
cost_usd: 0.3346
input_tokens: 24
output_tokens: 7365
---

# T05 — derive-monitoring proposes the check where a version is stamped

**Objective.** The design-for-diagnosis rule requires a deployable to stamp a service
version that changes on every deployment, and `/derive-monitoring` proposes
`http-status-regression` for HTTP-serving components that do, and reports a gap for
those that do not.

**Context.** `FEAT-LOOP-2026-0203/T05`, gate 1. The check's deployment signal is the first
appearance of a new `AppVersion` (PLAN.md decision 1), so a component that stamps no
version, or stamps the same one every release, can never be evaluated. That is a
design-for-diagnosis property in the same family as the role-name rule and #3470's
heartbeat-emission section: add a section beside them, provider-neutral in wording
(the rule doc's own test bans vendor words), stating the property and why the check
needs it.

`derive-monitoring` follows the precedent #3470 and #3475 set. Its source copies live
under `plugins/specfuse/skills/derive-monitoring/` and are synced to
`.specfuse/skills/derive-monitoring/` by `scripts/sync-scaffold.sh`. Its reference
implementation lives in `tests/test_derive_monitoring_discovery.py`: the check mapping
at l.145 (`if component.get("http_serving")`) and `audit_diagnosability`. Add the
mapping (HTTP-serving **and** version-stamping evidence: propose the check with
`deploy_signal: {kind: app-version}` and a `window_after_deploy`) and a
`version-stamping` audit finding (HTTP-serving, no evidence: no check, one WARN). The
evidence markers come through a pattern table, as #3470's `heartbeat_emission_markers`
do, so the CORE slice stays vendor-free.

**Acceptance criteria.**

1. `tests/test_derive_monitoring_discovery.py::TestHttpStatusRegressionProposal::test_proposed_only_with_version_evidence`
   fails on HEAD and passes after: an HTTP-serving component with version-stamping
   evidence gets an `http-status-regression` check that passes `validate_monitoring`,
   and one without gets none plus a single `version-stamping` finding.
2. Both design-rule copies carry the new section and stay byte-identical, and the
   rule doc's existing vendor-word test still passes.
3. `bash scripts/sync-scaffold.sh` leaves `git status --porcelain` unchanged after
   this unit's edits (copies already in sync), and both SKILL.md copies name
   `http-status-regression` and `version-stamping`.

**Do not touch.** The adapter and the lint rules (T03, T04). The `heartbeat-emission`
and `credential-reuse` audit findings shipped by #3470 and #3475, which are
extended beside, not reworded. The never-propose-`invariant` assertion in the
discovery tests.

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_derive_monitoring_discovery tests.test_monitoring_fenced_blocks tests.test_heartbeat_emission_contract -b`.

**Escalation triggers.** If no evidence pattern can distinguish "stamps a version
that changes per deployment" from "stamps a constant version string", stop and
escalate with what discovery can and cannot see rather than proposing the check on
weaker evidence. If the design-rule wording cannot pass the vendor-word test while
naming the signal, escalate rather than weakening that test.
