---
id: FEAT-2026-0045/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
produces:
  - specfuse/loop/triage.py
  - tests/test_triage_apply.py
oracle_env: macos_local
---

# The write path and the `auto` dial: marker first, label best-effort

**Objective.** Ship `apply_triage(runner, repo, decisions, *, auto=False)` — the half of
triage that records decisions: marker first, label projection best-effort, idempotent on
re-run, and gated by an explicit `auto` argument that applies only high-confidence
categorisations.

**Context.** Correlation ID `FEAT-2026-0045/T02`. Depends on T01, which owns the
vocabulary, the marker pair, the route map, and the scan. Read `PLAN.md` first for the
two settled decisions this WU implements: **the marker is authoritative and the label is
a projection**, and **the dial is an argument, not a config file**. Do not read or create
`.specfuse/agent-policy.yml`; FEAT-2026-0044 owns it and it does not exist yet.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `verification-discipline.md`.

**The write order is load-bearing, not stylistic.** Marker first, then the label. The
marker is the idempotency key: if it lands and the label write fails, the issue is
correctly triaged and merely lacks a swatch. If the order were reversed and the marker
write failed, the issue would carry a category label while still scanning as untriaged —
triaged and not-triaged at once.

**A failed label write must never raise.** `[FEAT-2026-0042/G2/registered-is-not-provisioned]`
records the live crash this prevents: a label was added to `LABEL_REGISTRY` a full gate
ahead of its consumer *specifically* to avoid a known failure, and the first live run
still died on `gh issue edit --add-label` exiting non-zero — because registering a name
in code does not create it on the repository. PLAN.md names which of the rule's two
options this feature takes: **tolerate absence.** A repository that never ran
`provision_labels` still gets correct triage. Record the failure in the returned report;
do not propagate it.

**What `auto` actually gates.** With `auto=True`, a decision whose confidence is not
`high` is **recorded as the `question` category** and routed to `needs-human`, rather
than applied as its proposed category. It is still marked — that is the point. With
`auto=False` (the default, and the interactive path) the operator has already confirmed
each decision, so every one is applied as given.

**Flag-scope table** (`.specfuse/rules/planning-discipline.md` §3). Headline claim:
*"`auto` applies only high-confidence categorisations and leaves the rest for human
triage."*

| Code path | Gated by flag? | Why |
|---|---|---|
| `apply_triage` — category application | **yes** | This is the flag's entire purpose: under `auto`, a non-`high` confidence is downgraded to `question`/`needs-human` instead of being applied as proposed. |
| `apply_triage` — marker write | no | The marker is the idempotency key. A dial that skipped it would leave the issue scanning as untriaged forever, re-triaged on every run — a token-cost and signal-to-noise failure, not a safety win. |
| `apply_triage` — label projection | no | The projection follows whatever category the marker records, including a downgraded one. Gating it would let marker and label disagree, breaking the declared precedence. |
| `apply_triage` — failed-label tolerance | no | Absence-tolerance is a property of the repository's provisioning state, not of who decided. It must hold identically on both paths. |
| `triage.list_untriaged` | no | The scan predicate is the marker's absence. It answers "what needs triage", which is independent of how any decision was made. |
| `triage.route_for` / `render_marker` / `parse_marker` | no | Pure functions over the closed vocabulary. No I/O, no policy. |

**Acceptance criteria.**

1. **Red first.** `tests/test_triage_apply.py::test_auto_dial_skips_low_confidence` exists
   and **fails on HEAD before any source edit**. Record the failing output.
2. `python3 -c "from specfuse.loop.triage import apply_triage"` exits 0.
3. `test_auto_dial_skips_low_confidence` **passes** after the edits: with `auto=True`, a
   `low`-confidence `bug` decision is recorded as `question` and routed to
   `needs-human` — and is still marked, not skipped.
4. A test asserts that with `auto=False`, the same `low`-confidence `bug` decision is
   applied as `bug` — proving the dial, and only the dial, changes the outcome.
5. A test asserts write **order** by inspecting the injected runner's recorded call
   sequence: the body/marker edit precedes the `--add-label` call for the same issue. Not
   "both calls happened."
6. A test asserts that a runner raising on the `--add-label` call still returns a report
   marking that issue's marker write as succeeded and its label write as failed, and that
   `apply_triage` **does not raise**.
7. A test asserts idempotency: calling `apply_triage` twice over an issue whose body
   already carries a triage marker performs no second write for that issue.
8. A test asserts a decision naming a category outside `CATEGORIES` raises rather than
   being written.
9. Every test injects a fake runner. `grep -rn "subprocess" tests/test_triage_apply.py`
   returns nothing, and no test in this WU invokes `gh`.
10. The `code` gate set in `.specfuse/verification.yml` passes: tests, lint, security,
    coverage ≥ 90%, leak-scan, event-type-gate, roadmap-link-gate, arm-sweep-gate.

**Do not touch.** `.git/`, secrets, `.specfuse/agent-policy.yml` (does not exist; not
this feature's), T01's vocabulary and marker functions beyond importing them, T03's skill
files. Do not invoke `/fix-bug`, create roadmap rows, or close any issue — PLAN.md's
scope boundary puts acting on a route out of this feature entirely. The driver owns all
git operations. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, run per
`.specfuse/skills/verification/SKILL.md`, plus the symbol-existence check in AC2.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:

- `apply_triage` is absent from the files you edited when you believe you are done — do
  not claim complete.
- Asserting write order (AC5) turns out to be impossible against the runner shape T01
  built. That is a real seam problem worth a human decision, not something to paper over
  by weakening the criterion to "both calls happened."
- Implementing the dial appears to require reading a config file. It does not; if you
  believe it does, stop — PLAN.md's decision is settled and a config surface here
  collides with FEAT-2026-0044.
- The `question` downgrade appears to need a distinct "downgraded" marker state to be
  correct. That is a vocabulary change owned by T01 and a scope question for the operator.

Blocked is a respectable outcome — `result-contract.md` rule 4.
