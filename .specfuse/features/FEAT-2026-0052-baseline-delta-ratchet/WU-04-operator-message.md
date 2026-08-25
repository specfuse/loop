---
id: FEAT-2026-0052/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
oracle_env: macos_local
produces_driver_helper: format_baseline_waived_proceed
produces:
  - specfuse/loop/loop.py
  - tests/test_waiver_messages.py
model: sonnet
effort: medium
---

# Tell the operator the third exit exists, and what proceeding cost them

**Objective.** Make both operator-facing messages true: the
`preexisting_gate_failure` halt must offer the waiver as a real third option
instead of stating no way past exists, and the proceed path must print what was
waived, against which baseline, and where it is tracked.

**Context.** Final substantive WU of FEAT-2026-0052; read `PLAN.md` in this
folder first. T01 built the subtraction, T02 the waiver and the proceed path, T03
the tracking issue. This WU owns every line of operator-facing prose those three
deliberately left minimal — the same split FEAT-2026-0051 used, where T01 emitted
a minimal factual message and T03 owned the text. That split paid off there and
is repeated here for the same reason: message text is the feature's actual
deliverable and rewriting it three times mid-gate produces three-way merge noise.

`format_preexisting_gate_failure` (`loop.py:3862`) is the function to edit. It
currently ends with a paragraph this feature exists to delete:

> There is no way to proceed past this halt in this version. A waiver that lets a
> feature continue against a red baseline is future work tracked as
> FEAT-2026-0052; it does not exist yet.

Two things in it must survive your edit, because both were built deliberately and
neither is yours to simplify:

- **The resumed-gate branch (#360).** When work units of this gate have already
  landed, the function says so and explicitly warns that the baseline includes
  the feature's own work — *"do NOT assume it predates the feature"*. A waiver
  offered on a resumed gate is far more dangerous than on a fresh one, because
  the operator may be waiving a failure their own feature just introduced. The
  third exit must be presented differently on that branch, or not at all.
- **The degraded-evidence path.** `baseline_evidence_diffstat` returns `None`
  rather than raising when the base cannot be resolved, and the message degrades
  to a "base-tree comparison unavailable" line. Keep it degrading.

Binding rules in `.specfuse/rules/` apply, and `human-output.md` is the
load-bearing one for this WU: plain English first, no bare internal symbols
leading a line. Do not restate them.

**Acceptance criteria.**

- `tests/test_waiver_messages.py::test_halt_message_offers_the_waiver` exists and
  **fails on HEAD before this WU's edits** (the module does not yet exist). On a
  fresh gate the rendered halt message contains the `--waive-baseline` command
  the operator would run and does **not** contain the string
  `does not exist yet`.
- After this WU's edits that same test passes, and so does
  `tests/test_waiver_messages.py::test_resumed_gate_warns_before_offering_a_waiver`
  — on a resumed gate (`done_unit_ids` non-empty) the message still carries the
  #360 warning that the baseline includes this feature's own landed work, and the
  waiver is presented only after it, never as the first option.
- `format_baseline_waived_proceed` is importable: `python3 -c "from
  specfuse.loop.loop import format_baseline_waived_proceed"` exits 0.
- The proceed message names every waived `(gate, failure_class)` pair, the
  baseline sha, and the tracking issue — its number when T03 filed one, or the
  literal `gh issue create` command when it could not. Three tests, one per case:
  filed, unfiled, and number-unknown (`CREATED_NUMBER_UNKNOWN`).
- The proceed message states plainly that newly-introduced failures still block.
  A test greps the rendered text for that claim. An operator who reads "proceeding
  past failing checks" and infers the gates are off has been misled by this
  feature, which is the outcome the whole design is arranged to avoid.
- **No message leads with a bare internal symbol.** A test asserts no rendered
  line begins with a raw identifier such as a failure-signature sentinel.
  Note: 0051's own follow-up 1 (rendering plain English when
  `_is_noninformative_signature()` is true) is **out of scope** — see PLAN.md's
  scope boundary. Do not fix it here; do not regress it either.
- The existing `format_preexisting_gate_failure` tests still pass, or their
  changes are limited to the removed no-way-past paragraph. A diff that alters
  the resumed-gate or degraded-evidence assertions is a scope breach.
- Every new `subprocess.run` (if any) declares `check=` explicitly (`PLW1510`).

**Do not touch.** T01's subtraction, T02's waiver storage and CLI flag, T03's
`emit_tracking_issue` and label registry — call them, do not edit them;
`baseline_evidence_diffstat` and the resumed-gate branch's warning semantics
(edit the text around them, not their behavior); `verify()`. `.git/`, secrets.
The driver owns git. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
symbol-import check above, plus T01–T03's test modules still green. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if offering the waiver on the
resumed-gate branch cannot be made safe in prose — an operator waiving a failure
their own feature introduced is a worse outcome than one more halt, and that is a
design decision for a human, not a wording problem for you to solve. Also block
if removing the no-way-past paragraph breaks a test asserting on it in a way that
suggests another consumer reads that text. If `format_baseline_waived_proceed` is
absent from the files you edited, emit `status: blocked` — do not claim complete.
Blocked is respectable (`result-contract.md` rule 4).
