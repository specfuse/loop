---
id: FEAT-2026-0040/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces:
  - specfuse/monitor/fingerprint.py
  - tests/test_fingerprint.py
produces_driver_helper:
  - fingerprint_artifact
---

# Fingerprint an artifact on its target's coordinates, not only its component

**Objective.** Ship `fingerprint_artifact`: a stable fingerprint over component,
failure class, failure signature, **and the target key**, so two targets on one
component never collapse into one issue.

**Context.** Correlation ID `FEAT-2026-0040/T02`. Depends on `T01` for
`FailureArtifact` and its target coordinates. Gate 3 uses this fingerprint as the
issue-dedupe key.

**This is the constraint FEAT-2026-0069 paid two gates for, restated as its own
closing obligation and inherited here.** From the roadmap, verbatim:

> Enumeration runs over `check["targets"]` when present and over the component
> otherwise, and a finding derived from a target must fingerprint on that target's
> coordinates (`subscription` + `function` for `dlq`, `name` for `heartbeat`) — not
> only the component name. `invariant` is the deliberate exception: `targets` is
> rejected there, so 0040 reads `fingerprint_by` for `invariant` and `targets` for
> everything else. **Without this, 20 DLQ targets collapse into one issue with every
> gate green, and the attribution this feature paid two gates for is lost at the
> last step.**

"With every gate green" is the part that matters: a component-only fingerprint is
not a crash, it is a silent, plausible wrong answer. No code gate detects it.
Criterion 5 is the test that does — two artifacts identical except for their target
must not share a fingerprint.

**Why `invariant` is different, and must not be "fixed" into consistency.** 0069
rejected `targets` on `invariant` precisely so this feature would not be handed two
competing enumeration keys with nothing in the schema saying which wins. An
`invariant` artifact fingerprints on the check's `fingerprint_by`. Making it uniform
with the others would re-open the ambiguity 0069 closed.

**Stability is a property, not an implementation detail.** The same failure observed
on two different runs must produce the same fingerprint, or dedupe fails and every
poll files a new issue. That means no timestamps, no run IDs, no set iteration order,
and no `hash()` — which is salted per process in Python and would produce a different
value on every invocation.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_fingerprint.py::TestFingerprint::test_distinct_targets_produce_distinct_fingerprints`
   exists and **fails on HEAD before this WU runs** (the test file does not yet
   exist, which counts as red).
2. `specfuse/monitor/fingerprint.py` defines `fingerprint_artifact(artifact)`
   returning a stable `str`.
3. A `dlq` artifact's fingerprint incorporates both `subscription` and `function`
   from its target coordinates.
4. A `heartbeat` artifact's fingerprint incorporates the target's `name`.
5. **Two artifacts identical in every field except their target coordinates produce
   different fingerprints.** This is the criterion the whole constraint reduces to.
6. An `invariant` artifact's fingerprint is derived from the check's `fingerprint_by`
   and **not** from target coordinates, which T01 guarantees it does not carry.
7. Two artifacts identical in component, failure class, failure signature, and target
   coordinates produce the **same** fingerprint — dedupe works.
8. Calling `fingerprint_artifact` twice on the same artifact in **separate Python
   processes** yields the same value: `grep -n "hash(" specfuse/monitor/fingerprint.py`
   returns no match, and the implementation uses a stable digest.
9. The fingerprint is insensitive to the ordering of the target-coordinates mapping.
10. `python3 -m pytest tests/test_fingerprint.py -q` exits zero after this WU's edits
    (the same file named in criterion 1).
11. `python3 -c "from specfuse.monitor.fingerprint import fingerprint_artifact"`
    exits zero.

**Do not touch.** `specfuse/monitor/artifact.py` and `adapters.py` — T01 owns them;
this WU consumes `FailureArtifact` and must not extend it. If a needed coordinate is
absent from the model, that is a blocking finding against T01, not a licence to edit
it. Files owned by T03. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set: `tests`, `lint`, `security`, `coverage`
(≥90%), `leak-scan`. Plus the scoped red/green run in criteria 1 and 10, the
symbol-existence import in criterion 11, and criterion 8's cross-process stability
check — a fingerprint that is stable within one process and not across them passes
every ordinary test and fails in production on the second poll.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`FailureArtifact` cannot supply the coordinates criteria 3–4 need — report it as a
T01 defect rather than editing T01; the schema's per-check-type coordinate mapping
disagrees with this WU's Context; or `fingerprint_by` is not reachable from an
`invariant` artifact, which would mean criterion 6 is unsatisfiable as written. If
`specfuse/monitor/fingerprint.py` is absent from the files you edited, emit
`status: blocked` — do not claim complete.
