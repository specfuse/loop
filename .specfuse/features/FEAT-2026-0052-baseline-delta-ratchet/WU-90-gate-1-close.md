---
id: FEAT-2026-0052/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
auto_close_disabled: true
model: opus
effort: high
produces:
  - .specfuse/features/FEAT-2026-0052-baseline-delta-ratchet/RETROSPECTIVE.md
  - .specfuse/LEARNINGS.md
---

# Gate 1 close — Baseline-delta ratchet, waiver, and tracking-issue emission

**Objective.** Terminal close: re-run the oracles fresh, record retrospective +
lessons + docs note + verdict in one session, and prove the ratchet genuinely
subtracts only what the baseline recorded and genuinely still fails a new
failure — not that the tests are shaped like it does.

**Context.** Terminal close of FEAT-2026-0052. Depends on T01 (subtraction at the
outcome layer), T02 (waiver storage + proceed path), T03 (tracking issue +
label), T04 (operator messages). Binding rules in `.specfuse/rules/`
(`result-contract.md`, `close-discipline.md`, `human-output.md`) apply. The driver
owns the terminal `PLAN.md status -> done` flip — do **not** add a status-flip
acceptance criterion.

> Run `specfuse lint --closing` and confirm it exits 0 before this WU reports
> `complete` — see `.specfuse/rules/close-discipline.md` §4.

**Acceptance criteria.**

- A `## Retrospective` section covering: whether the ratchet ran against this
  repo's own gates during the feature (and if not, why — PLAN.md's Notes predict
  it cannot, because `loop.py` loads once at process start; 0051's PLAN got this
  exact question wrong and its retrospective corrected it, so answer it from
  observed evidence, not from the prediction); whether the sha-and-set pinning
  behaved under a real second probe; and whether the serialized T01→T04 chain
  produced merge friction. Plus `## What I'd change`.
- A `## Lessons` section with any durable rule worth promoting to
  `.specfuse/LEARNINGS.md` — in particular whether "subtract a recorded set,
  never mute a check" generalizes beyond gate sets, and whether splitting a
  behavior change from its operator-facing prose into separate WUs (0051's shape,
  repeated here) is worth stating as a rule.
- A `## Docs` note: confirm whether `docs/methodology.md` needs the waiver and
  the ratchet documented alongside `preexisting_gate_failure`, or name the doc
  touched. 0051 left an open follow-up asking §6 to express a gate that
  terminates at entry having dispatched nothing; say whether this feature changes
  that answer.
- A `## Cost analysis` section reconciling `planned_cost_usd` (PLAN's $25.00 and
  the per-WU estimates) against actual spend read from `events.jsonl`, delta
  named. If the delta does not blend across WU types, say so rather than
  reporting one average.
- A `## What the loop did NOT verify` section enumerating every deferred
  criterion with why and where it actually gets checked; required even when empty
  — write `(nothing — every acceptance criterion was verified in-loop)`. Expect
  at least one entry: the feature's *value* is proven by a downstream project
  waiving a genuinely externally-caused failure, which cannot happen inside this
  loop. 0051 recorded the same class of entry for the same reason.
- **Oracles re-run fresh** (close-discipline §1), read directly and never from a
  producing WU's self-report: `python3 -m unittest discover -s tests -q` reports
  `OK`; `python3 -c "from specfuse.loop.loop import subtract_baseline_failures,
  baseline_waiver_active, read_gate_waiver, write_gate_waiver,
  waiver_covers_baseline, format_baseline_waived_proceed"` exits 0;
  `python3 -c "from specfuse.loop.escalation import emit_tracking_issue"` exits
  0; the full `code` gate set passes.
- **End-to-end waived-proceed proof**, run fresh in this session and not
  inherited from any WU's unit test: against a real temp repo with a
  deliberately failing gate, gate entry halts; `--waive-baseline` records the
  waiver; the next entry proceeds; a work unit failing **only** on the waived
  gate is not classified `failed`. Quote the proceed message verbatim in the
  close record — it is the feature's actual deliverable and a human should read
  it once before this ships.
- **New-failure proof, in the same temp repo:** with the waiver still active,
  introduce a **second** failing gate and assert the work unit is classified
  `failed` and the gate halts again on the next entry. This is the criterion that
  distinguishes this feature from the per-gate mute issue #234 rejected. If this
  proof disagrees with T01's or T02's unit tests, that is a block, not a
  reconciliation exercise.
- **No-waiver no-op proof:** with no waiver present, classification is unchanged
  from pre-feature behavior. This is PLAN.md's escalation-predicate answer
  verified at close, not only at T01.
- **Consumer-visible contract changes** (§3): enumerate them and block on human
  acknowledgment rather than writing `n/a`. Expect at least a new gate
  frontmatter key (`waiver:`), a new CLI flag (`--waive-baseline`), a new
  `LABEL_REGISTRY` entry (`waived-baseline`), a new public symbol in
  `escalation.py`, and a changed attempt-outcome payload. Each is additive, but
  all are surfaces downstream projects and the scaffold linter observe — 0051's
  close found the gate-frontmatter row carried the only real breakage risk (an
  unknown key rejected by the linter) and **tested** it rather than assuming.
  Do the same for `waiver:`.
- On a hedged outcome, record the follow-up per close-discipline §2, with a
  `kind:` per unmet criterion.

**Do not touch.** Source and test files (T01–T04 own those), `.git/`, secrets.
This WU writes only its close record. The driver owns git and the terminal PLAN
flip. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext`/close gates plus a fresh re-run of the oracles
above. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if the end-to-end waived-proceed
proof disagrees with T01/T02's unit tests — a ratchet that passes its own tests
but lets a real new failure through is precisely the hollow pass this criterion
exists to catch, and it is the most dangerous failure direction this feature has.
Also block if the `waiver:` block turns out to break the scaffold linter or
0051's shipped `baseline:` reader: that is a shipped-contract regression a human
must weigh, not something to patch inside a close. Blocked is respectable
(`result-contract.md` rule 4).
