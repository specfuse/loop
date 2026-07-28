---
id: FEAT-2026-0071/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
produces:
  - specfuse/loop/labels.py
  - tests/test_provision_labels.py
produces_driver_helper:
  - provision_labels
model: sonnet
effort: medium
gate_set: code
driver_version: 0.5.0
started_at: 2026-07-28T11:32:24.309910+00:00
duration_seconds: 697.414
cost_usd: 1.200377
input_tokens: 76
output_tokens: 13013
---

# Provision missing labels — idempotent, best-effort, never raising

**Objective.** Add `provision_labels(...)` to `specfuse/loop/labels.py`: it
creates the registry labels a repository is missing, skips those it already has,
and returns a report instead of raising on any failure.

**Context.** Correlation ID `FEAT-2026-0071/T02`. Depends on `T01` for
`LABEL_REGISTRY`. T03 calls this from the scaffold.

**Never raising is the load-bearing property, and it is most of the work.**
`scaffold.py` has no subprocess or network call today — `init` and
`upgrade_specfuse` are pure filesystem, which is why they work offline, in CI
containers, and against non-GitHub remotes. T03 puts this function on that path.
If it can raise, an upgrade can fail because a label could not be created, and
that is a strictly worse tool than the one that shipped without provisioning at
all. Every degradation path below returns a report; none propagates an exception.

**Follow the existing runner seam.** `gh_backend.GitHubBackend` takes an
injectable `_runner` defaulting to a real `gh`-invoking implementation, and
`escalation.emit_escalation` mirrors it. Match that shape a third time rather
than inventing a convention. Read both before writing.

**Idempotency without `--force`.** List the repository's existing labels first
and create only what is missing. Never pass `--force`: an operator who edited a
label's colour or description owns that choice, and overwriting it on every
upgrade is a silent hostile edit. A label present with different colour or
description counts as present.

**The degradation paths, all of which return rather than raise:** `gh` not on
PATH; `gh` present but unauthenticated; the directory is not a git repository;
the remote is not GitHub; the label-list call fails for any reason; a single
`gh label create` fails while others succeed. The last one matters most — a
partial failure must not abandon the remaining labels.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_provision_labels.py::TestProvisionLabels::test_missing_gh_binary_returns_report_without_raising`
   exists and **fails on HEAD before this WU runs** (the test file does not yet
   exist, which counts as red).
2. `specfuse/loop/labels.py` defines `provision_labels(...)` accepting an
   injectable runner argument defaulting to a real `gh`-invoking implementation,
   in the same shape `gh_backend.GitHubBackend.__init__` uses for `_runner`.
3. With a stub runner reporting no existing labels, `provision_labels` issues one
   create call per `LABEL_REGISTRY` entry, and each create call's arguments carry
   that entry's name, colour, and description.
4. With a stub runner reporting every registry label already present,
   `provision_labels` issues **zero** create calls — the idempotent no-op.
5. With a stub runner reporting a subset present, create calls are issued for
   exactly the missing names and no others.
6. No code path passes `--force` to `gh label create`:
   `grep -c '\-\-force' specfuse/loop/labels.py` returns 0.
7. A label present with a different colour or description than the registry's is
   treated as present — no create call, no update call.
8. When the runner raises `FileNotFoundError` (no `gh` on PATH),
   `provision_labels` returns a report and does not raise.
9. When the runner reports an authentication failure, `provision_labels` returns
   a report and does not raise.
10. When the runner reports the directory is not a git repository or the remote
    is not GitHub, `provision_labels` returns a report and does not raise.
11. When one `gh label create` fails and the others would succeed,
    `provision_labels` still attempts every remaining label, and the returned
    report names the failed one.
12. The returned report distinguishes, per label, between created, already
    present, and failed.
13. No test in `tests/test_provision_labels.py` invokes the real `gh` binary:
    every test injects a stub runner.
14. `python3 -m pytest tests/test_provision_labels.py -q` exits zero after this
    WU's edits (the same file named in criterion 1).
15. `python3 -c "from specfuse.loop.labels import provision_labels"` exits zero.

**Do not touch.** `specfuse/loop/scaffold.py` — T03 owns the wiring; this WU only
provides the function. `specfuse/loop/gh_backend.py` and
`specfuse/loop/escalation.py` — read them for the runner shape, do not modify.
`LABEL_REGISTRY` itself, beyond reading it. Generated directories, secrets,
`.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set: `tests`, `lint`, `security`, `coverage`
(≥90%), `leak-scan`. Plus the scoped red/green run in criteria 1 and 14, the
symbol-existence import in criterion 15, and the grep in criterion 6 — no code
gate detects an accidental `--force`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
distinguishing "unauthenticated" from "not a GitHub remote" requires observing
real `gh` output that cannot be determined without invoking it, which criterion 13
forbids — in that case report what you could not distinguish rather than guessing;
or the coverage floor cannot be met without a test that invokes the real binary.
If `provision_labels` is absent from the files you edited, emit `status: blocked`
— do not claim complete.
