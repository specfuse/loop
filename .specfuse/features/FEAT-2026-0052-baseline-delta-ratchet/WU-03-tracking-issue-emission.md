---
id: FEAT-2026-0052/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
unsandboxed: true
unsandboxed_rationale: "The deliverable is a live `gh issue create` round-trip; a sandboxed session gets an invalid-token/TLS failure that reads like a broken feature. Per the CORRECTED LEARNINGS entry [FEAT-2026-0014/T01/gh-claudeP-broken], `unsandboxed: true` is the sanctioned lever and is confined to this one WU."
produces_driver_helper: emit_tracking_issue
produces:
  - specfuse/loop/escalation.py
  - specfuse/loop/labels.py
  - specfuse/loop/loop.py
  - tests/test_tracking_issue.py
model: sonnet
effort: medium
---

# File the waived baseline as a tracked `waived-baseline` issue

**Objective.** Make a waived baseline always recorded on GitHub rather than
silently accepted: add a `waived-baseline` label to the registry, add
`emit_tracking_issue` beside the existing escalation seam, and call it from the
proceed path T02 built — auto-creating the issue when `gh` is reachable and
printing the exact `gh issue create` command for the operator when it is not.

**Context.** Third WU of FEAT-2026-0052; read `PLAN.md` in this folder first, in
particular the existing-mechanism verdict, which is **reusing** for this WU. T02
built the proceed path; this WU makes it leave a record.

**Most of this is already built. Read it before writing anything.**
`specfuse/loop/escalation.py` already contains the whole find-then-create
machinery, and its `emit_escalation` docstring states the property you need:

> Idempotent: searches for an open issue carrying the ``needs-human`` label and
> this correlation ID's marker before creating; a second call for the same
> ``correlation_id`` returns the existing issue's identifier instead of filing a
> duplicate.

Reuse `_find_existing_issue`, `_correlation_marker`, `_extract_issue_number`,
`_default_runner` and `CREATED_NUMBER_UNKNOWN`. Three hard-won behaviors live in
that module and must be preserved in the sibling, not rediscovered: the assignee
flag is **omitted** rather than passed empty (#1762 — an unassignable placeholder
made `gh issue create` exit 1 and the whole escalation was lost); the runner is
called with `check=False` and a raising runner is caught (#2170 — a reporting
failure must never destroy the run it is reporting on); and a created issue whose
number could not be parsed is **not** the same as an uncreated one.

**Do not modify `emit_escalation` itself.** It is shipped and has a live caller
(`specfuse/agent/run.py:293`). Add a sibling.

**The tracking issue is deliberately NOT a `needs-human` escalation.** A waived
baseline parks nothing — the run proceeds. Labelling it `needs-human` would file
a *running* feature into the `/attention` skill's blocked-work inbox and
misreport it as stalled. Hence a distinct `waived-baseline` label, added to
`LABEL_REGISTRY` in `specfuse/loop/labels.py:31` so the existing
`provision_labels` (`labels.py:192`) creates it on repos that lack it. Note the
failure mode `bug_lane_run.py:287` records: a label in the registry but never
created on the repository raises — which is exactly why the registry entry and
the provisioning path are one change, not two.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`) apply. Do not restate them.

**Acceptance criteria.**

- `tests/test_tracking_issue.py::test_second_waiver_does_not_file_a_duplicate`
  exists and **fails on HEAD before this WU's edits** (the module does not yet
  exist). Two calls for the same correlation ID file one issue; the second
  returns the first's identifier. Driven through an injected runner, not a live
  `gh`.
- After this WU's edits that same test passes, and so does
  `tests/test_tracking_issue.py::test_gh_unavailable_prints_the_command` — when
  the runner reports `gh` unusable, no exception escapes, the return value
  signals "not filed", and the exact `gh issue create` command (repo, title,
  body, label) is printed for the operator to run by hand.
- `emit_tracking_issue` is importable: `python3 -c "from
  specfuse.loop.escalation import emit_tracking_issue"` exits 0.
- `waived-baseline` is present in `LABEL_REGISTRY`, and `provision_labels`
  creates it. A test asserts the registry entry exists and that provisioning
  includes it in the missing-label set for a repo without it.
- The filed issue does **not** carry `NEEDS_HUMAN_LABEL`. A test asserts the
  label list passed to the runner contains `waived-baseline` and does not contain
  `needs-human`. This is the criterion that keeps `/attention`'s inbox honest;
  assert it explicitly rather than relying on the call site.
- The issue body names, at minimum: the feature ID, the gate number, the baseline
  sha, and every waived `(gate, failure_class, failure_signature)` entry. A test
  asserts each waived entry's gate name appears in the rendered body — a tracking
  issue that does not say what was waived tracks nothing.
- `emit_escalation` is unmodified. Assert mechanically:
  `git diff HEAD -- specfuse/loop/escalation.py` shows no edit inside
  `emit_escalation`'s body, and the existing escalation tests pass untouched.
- **Live round-trip, run in this session** (this is what the `unsandboxed` flag
  is for): `gh auth status` prints `Logged in to github.com`; a real issue is
  created against a scratch issue on this repo, read back, and closed. Dump the
  **raw stdout+stderr** of each `gh` call between BEGIN/END markers in your
  RESULT and grep the dump for `Logged in to github.com` — per
  `[FEAT-2026-0014/T01/preflight-must-dump-raw]`, never report an external tool's
  behavior from your own classification of it when the raw output exists.
- The proceed path T02 built calls `emit_tracking_issue`, and a failure to file
  does **not** abort the run. A test asserts the run proceeds when the emitter
  returns "not filed".
- Every new `subprocess.run` declares `check=` explicitly (`PLW1510`).

**Do not touch.** `emit_escalation`, `annotate_escalation`, `NEEDS_HUMAN_LABEL`
and `CATEGORY_LABELS` (shipped, live caller in `specfuse/agent/run.py`);
`verify()`; T01's subtraction and T02's waiver storage (call them, do not edit
them); the operator message text (T04 owns it). `.git/`, secrets — and note that
this WU runs unsandboxed, so the never-touch list is doing real work rather than
being backstopped by the sandbox. See `.specfuse/rules/never-touch.md` and
`.specfuse/rules/security-boundaries.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
symbol-import check and the raw-output round-trip above. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if `gh auth status` fails even
with `unsandboxed: true` — the CORRECTED LEARNINGS entry says the flag is
sufficient for this surface, and if that is wrong on this machine a human needs
to know rather than have you fall back to a stub. Do **not** substitute a stubbed
round-trip for the live one and report complete: `[FEAT-2026-0046/G1-CLOSE]`
records exactly that substitution making a WU look verified while the integration
risk went untested. Also block if the `waived-baseline` label cannot be created
on this repository (a permissions question, not a code question). If
`emit_tracking_issue` is absent from the files you edited, emit `status: blocked`
— do not claim complete. Blocked is respectable (`result-contract.md` rule 4).
