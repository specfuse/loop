---
id: FEAT-2026-0051/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 6.00
oracle_env: macos_local
auto_close_disabled: true
---

# Gate 1 close — Pre-flight baseline gate probe

**Objective.** Terminal close: re-run the oracles fresh, record retrospective +
lessons + docs note + verdict in one session, and confirm the brake genuinely
fires on a red baseline and genuinely does nothing on a green one — not that the
tests are shaped like it does.

**Context.** Terminal close of FEAT-2026-0051. Depends on T01 (probe + halt), T02
(persistence + kill-switch), T03 (message + evidence). Binding rules in
`.specfuse/rules/` (`result-contract.md`, `close-discipline.md`) apply. The driver
owns the terminal `PLAN.md status -> done` flip — do NOT add a status-flip
acceptance criterion.

**Acceptance criteria.**
- A `## Retrospective` section: whether the probe fired on this repo's own gates
  during the feature (the self-hosting case named in PLAN.md's Notes), what one
  probe run actually costs in wall-clock against this repo's `code` set, and
  whether the resume-skip policy behaved. Plus `## What I'd change`.
- A `## Lessons` section with any durable rule worth promoting to
  `.specfuse/LEARNINGS.md` — in particular whether "probe the oracle before
  trusting it as an oracle" generalizes beyond gate sets, and whether the
  measured probe cost changes the once-per-gate-entry decision.
- A `## Docs` note: confirm whether `docs/methodology.md` needs the
  `preexisting_gate_failure` halt documented alongside the other escalation
  reasons, or name the doc touched.
- A `## Cost analysis` section reconciling `planned_cost_usd` (PLAN + per-WU)
  against actual spend (events.jsonl), delta named.
- A `## What the loop did NOT verify` section enumerating any deferred criterion
  (with why + where it actually happens); required even when empty — write
  `(nothing — every acceptance criterion was verified in-loop)`. Expect at least
  one entry: the probe's value is proven by a *downstream* project hitting a red
  baseline, which cannot happen inside this loop.
- **Oracles re-run fresh** (close-discipline §1), read directly and not from any
  WU's self-report: `python3 -m unittest discover -s tests -q` reports `OK`;
  `python3 -c "from specfuse.loop.loop import probe_baseline,
  read_gate_baseline, write_gate_baseline, baseline_probe_enabled,
  format_preexisting_gate_failure, baseline_evidence_diffstat"` exits 0; the full
  `code` gate set passes.
- **End-to-end red-baseline proof**, run fresh in this session and not inherited
  from T01's unit test: with a deliberately failing gate configured, a gate entry
  halts with `preexisting_gate_failure`, dispatches zero WUs, records the
  baseline in the gate file, and prints a message naming the gate, the signature,
  and the base-tree comparison. Quote the message verbatim in the close record —
  it is the feature's actual deliverable and a human should read it once before
  this ships.
- **Green-baseline no-op proof**: with all gates green, dispatch behavior is
  unchanged from pre-feature behavior. This is the escalation-predicate check
  (PLAN.md §2) verified at close, not just at T01.
- **Kill-switch proof**: `--no-baseline-probe` produces zero probe runs.
- **Consumer-visible contract changes** (§3): enumerate them — a new
  `human_escalation` reason string (`preexisting_gate_failure`), a new gate
  frontmatter key (`baseline:`), a new CLI flag, and a new `verification.yml`
  key. All four are additive, but they are surfaces downstream projects and the
  scaffold linter observe, so list them explicitly and block on human
  acknowledgment rather than writing `n/a`.

**Do not touch.** Source and test files (T01/T02/T03 own those), `.git/`,
secrets. This WU writes only its close record. The driver owns git and the
terminal PLAN flip. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext`/close gates plus a fresh re-run of the oracles
above. See `.specfuse/skills/verification/SKILL.md`. On a hedged outcome, record
the follow-up per close-discipline §2.

**Escalation triggers.** Emit `status: blocked` if the end-to-end red-baseline
proof disagrees with T01's unit tests — a brake that passes its own tests but
does not stop a real dispatch is precisely the hollow pass this criterion exists
to catch. Also block if the probe measurably slows this repo's own gate entries
enough to change the once-per-gate-entry decision; that is a design fact the
close should surface, not absorb. Blocked is respectable (`result-contract.md`
rule 4).
