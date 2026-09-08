---
id: FEAT-2026-0101/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 8.00
oracle_env: macos_local
auto_close_disabled: true
produces:
  - .specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton/RETROSPECTIVE.md
model: opus
effort: high
gate_set: plannext
driver_version: 0.16.0
verdict: met
started_at: 2026-09-08T00:56:38.785925+00:00
duration_seconds: 942.257
cost_usd: 8.939306
input_tokens: 208
output_tokens: 62788
---

# Gate 1 close — audit that the oracle is wired, not merely defined

**Objective.** Terminal close of FEAT-2026-0101: demonstrate each behaviour in
`GATE-01.md`'s definition of done in this session, run the recursive
guard-wiring audit this kind of feature owes, and record the measurements.
Measure; a separate judge session reads the evidence and decides.

**Context.** Depends on T01-T04. Binding:
`.specfuse/rules/close-discipline.md` as T02 sharpened it. The driver owns the
terminal `PLAN.md` and roadmap flips. Run `specfuse lint --closing` before
reporting `complete`.

**The recursive audit is the point of this close.** Per
`[FEAT-2026-0008/G1-CLOSE]`, a feature that fixes a methodology failure mode
must verify at close that its guards **landed and are wired into the path they
were meant to intercept** — an unwired helper is a hollow pass with extra steps,
and hollow-passing the close of an anti-hollow-pass feature is the worst-case
recursive failure. Defining `read_gate_feature_oracle` is not evidence; a call
site inside `verify()` is.

**Do not let this gate's own green oracle stand in for that audit.** This gate
declares an oracle, so the oracle runs in this close's own verification. That
proves the mechanism runs *here*; it does not prove the lint, the closing
requirement, or the authoring surfaces are wired. Report the two separately.

**Acceptance criteria.**

- `RETROSPECTIVE.md` carries `## Gate 1` and a `## Measurements` table: for each bullet of `GATE-01.md`'s definition of done, the command run in this session and its exit status; and this gate's own `feature_oracle` verdict, which T02 makes a required entry.
- `## Guard-wiring audit`: for each symbol T01-T03 introduced, both a definition check and a **call-site** check — `grep -n "<helper>(" specfuse/loop/loop.py` returning a caller inside `verify()`, and the equivalent for the lint rule inside the plan-lint entry point and for the closing requirement inside the closing lint. Any check that finds a definition without a caller means the verdict may not claim the goal is met.
- The satisfiability sweep re-run fresh, with counts: zero ERRORs, exactly the four WARNs named in `GATE-01.md`. State the numbers, not "as expected".
- `## Cost analysis` reconciling `planned_cost_usd` ($19.00, per-WU) against `events.jsonl`, naming the delta and the restart count. FEAT-2026-0102's estimates ran 2.6× high; say whether this feature's recalibration held.
- `## What the loop did NOT verify`: at minimum, whether an oracle authored by a *future* `plan-next` for a gate 2 is stronger than gate 1's — unenforceable by construction (`PLAN.md` § known limit) and handled as a review-summary obligation. State criterion, reason, and where it actually gets checked, for each entry.
- `## Consumer-visible contract changes`: a new `GATE-NN.md` frontmatter key, a new plan-lint rule that is ERROR on active features, and a new closing-lint requirement. Enumerate them and add the `CHANGELOG.md` entry.
- `## Lessons`: at most two entries.
- Oracles re-run fresh: `python3 -m unittest discover -s tests -q` reports `OK`; `bash scripts/smoke-test.sh` exits 0; `specfuse lint` over every feature folder reports zero ERROR.

**Do not touch.** Source, tests, rules, templates, skills (T01-T04 own them);
the four WARN-ing gate files; `.git/`, secrets. This WU writes only its close
record and the CHANGELOG entry its criteria name.

**Verification.** The `plannext` gate set, plus this gate's own
`feature_oracle` and the fresh oracle re-runs named in the criteria above.

**Escalation triggers.** Emit `status: blocked` if any guard-wiring check finds
a definition with no call site in the named path — that is the exact failure
this close exists to catch, and reporting it as met would be the recursive
hollow pass. Also block if the satisfiability sweep disagrees with the four
recorded WARNs.
</content>
