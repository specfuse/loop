---
id: FEAT-2026-0040/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: done
attempts: 0
planned_cost_usd: 4.50
oracle_env: macos_local
auto_close: true
auto_close_reasons: []
---

# Close gate 1 — retrospective, lessons, docs

**Objective.** Fold the retrospective, the lessons promotion, and the docs/roadmap
update into one session for gate 1. This is a non-terminal gate, so `G1-PLAN` runs
next and drafts gate 2; this unit records no terminal verdict.

**Context.** Correlation ID `FEAT-2026-0040/G1-CLOSE-INTERMEDIATE`. Depends on T01,
T02, and T03.

**Read `.specfuse/rules/close-discipline.md` §4 before writing anything.** Its guards
are matched literally and checked *after* this unit runs, so a mismatch costs a full
re-dispatch. The rows that apply here: `assert_retrospective_exists`;
`assert_retrospective_gate_section`, which requires a heading matching `^#{1,3} Gate 1`
— **`## Gate 1`, not "Gate one", not a bold line**; `assert_learnings_appended_or_noop`;
`assert_doc_or_roadmap_diff`; and
`assert_failure_class_breakdown_when_failures_present`, which wants a literal
`### Failure-class breakdown` heading with **three** hashes, only if this gate had a
failed attempt.

`assert_verdict_well_formed` does **not** apply — that guard is `close`-only, and a
terminal verdict for this feature belongs to `G3-CLOSE`.

**Close obligations.**

1. **Oracles re-run fresh (§1).** Every oracle T01–T03 name, run again here with full
   commands and exit codes read directly — never a producing unit's self-report.
2. **Consumer-visible contract changes (§3).** Enumerate every addition across
   T01–T03, or write exactly `n/a — no consumer-visible contract change`. Gate 1 adds
   a new `specfuse.monitor` package that nothing imports yet, so this list is
   expected to be short and additive — say so rather than padding it.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists in the feature directory, is non-empty, and contains a
   heading matching `^#{1,3} Gate 1`.
2. A `## Cost analysis` section is present, reconciling `planned_cost_usd` — $20.00
   for this gate, per-unit $4.00 / $3.00 / $2.50 / $4.50 / $6.00 — against actual
   spend read from `events.jsonl`, with the delta named.
3. A `## What the loop did NOT verify` section is present, enumerating each
   acceptance criterion whose verification was deferred, with why and where it is
   actually verified. **Gate 1 was scoped so this list can legitimately be empty** —
   no provider, no GitHub, everything in-loop. If it is empty write
   `(nothing — every acceptance criterion was verified in-loop)`; if it is not, that
   is a finding worth stating plainly, because it means the gate cut did not hold.
   More than 2 entries or 30% of criteria requires flagging the sizing under
   `## What I'd change`.
4. Every oracle named by T01–T03 is re-run in this session with its command and exit
   code recorded: `python3 -m pytest tests/test_failure_artifact_model.py -q`,
   `tests/test_fingerprint.py`, `tests/test_artifact_redaction.py`, the three
   symbol-existence imports, and the four greps — T01's provider-leakage and
   schedule-field checks, T02's `hash(` check, and T03's `leak_scan` check.
5. The provider-agnosticism claim is verified **as a property of the tree**, not
   only as a passing test: `grep -rniE "azure|appinsights|servicebus|kusto"
   specfuse/monitor/` reports only matches inside comments or docstrings, and any
   match is named in the retrospective.
6. A consumer-visible contract-change enumeration is present per close obligation 2.
7. Generalizable lessons are appended to `.specfuse/LEARNINGS.md`, or
   `RETROSPECTIVE.md` contains the exact phrase `nothing generalizes`.
8. The roadmap detail section for FEAT-2026-0040 reflects what gate 1 actually built.
9. If any work unit in this gate recorded a failed attempt, a literal
   `### Failure-class breakdown` heading is present with the classes named.

**Do not touch.** Source files owned by T01–T03 — this unit closes the gate, it does
not patch the work. `PLAN.md`'s `status` field. Gate 2's WUs — `G1-PLAN` drafts
those. Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set for closing units, plus the oracle re-runs
in criterion 4 and the tree-wide grep in criterion 5, which are this unit's real
verification surface.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: an
oracle named in criterion 4 cannot be re-run; `events.jsonl` lacks the cost data
criterion 2 reconciles against; or criterion 5's grep finds a provider identifier in
`specfuse/monitor/`, which would mean gate 1's central claim is false and is a
finding to report rather than to edit away.
