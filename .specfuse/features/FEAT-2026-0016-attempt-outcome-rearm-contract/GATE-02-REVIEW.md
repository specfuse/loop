# Gate 2 review — FEAT-2026-0016

Drafted by `FEAT-2026-0016/G1-PLAN` (Opus). Read this before arming.
This file is **advisory**. It owns no state. Status lives in WU
files; the graph lives in `PLAN.md`. If you change a decision, edit
the WU and the graph directly.

---

## Gate-1 summary

Gate 1 (data-layer foundation) landed within plan: substantive
total $5.21 actual vs $5.80 planned (-10%); gate predicate
`gate_total_cost: $4.37` (predicate sums terminal-cycle `cost_usd`
only — T03's pre-re-arm $0.84 sits in `prior_attempts` outside
the predicate's view, a known v1 limitation surfaced in
`RETROSPECTIVE.md`). T01 confirmed the **bootstrap-gap pattern**
exactly: events.jsonl lines 1–6 carry only legacy
`task_started`/`task_completed`/`human_escalation` shapes (the
driver dispatching T01 ran pre-T01 code); first WU with the full
v1 `attempt_outcome` payload is T03 line 8. Predicate self-check
on this gate-1 (run below) returns `auto=False` solely on
`blocked_human_in_chain: T03 escalated 2026-06-14` — T03's correct
spec-bug diagnosis, recovered via revised AC7e per
`[driver/files_changed-guard]` LEARNINGS. For an intermediate
close, the predicate verdict is informational; the operator
chose re-arm with revised spec rather than abandon.

## Gate-2 substantive WUs

### T04 — Spinning-detector active driver hook ($2.00, high)

Adds `detect_spinning_signature_repeat(current, prior) -> bool`
to `loop.py` and wires it into the per-WU attempt loop's
`outcome == "failed"` branch (around line 2602 today). Maintains
a per-dispatch local `prior_failure_signature` tuple; halts on
attempt 2 at the earliest when the `(failure_class,
failure_signature)` tuple repeats. Emits a `human_escalation`
event with reason `spinning_signature_repeat` carrying the
repeated signature. Orthogonality with the existing
`all_attempts_zero_token` shape is preserved by defending the
detector against `None` elements (zero-token outcomes do NOT
update `prior_failure_signature`). Replaces this session's
manual Monitor + TaskStop intervention pattern.

### T05 — `/gate-status` per-attempt + re-arm surfacing ($1.20, medium)

Skill-side read of `events.jsonl`'s `attempt_outcome` records for
the active feature's blocked WUs, rendered as a per-attempt table
(`attempt | outcome | failure_class | failure_signature |
duration | cost`). Adds `#### Per-attempt outcomes` and
`#### Re-arm history` subsections under §4 of the skill body.
Re-arm history reads WU frontmatter `re_arm_count` +
`re_arm_history[-1].reason` directly. Legacy-event safe (renders
"no per-attempt events" when absent rather than raising).
Removes the operator's "grep driver stdout via my session"
workaround.

### T06 — `/unblock-wu` mandatory rationale + `re_arm_history` write ($1.50, high)

Skill-side write that closes the audit loop T02 opened. Makes
the existing "what changed?" prompt **non-empty mandatory** (re-prompts
on whitespace-only input). On accept, appends a structured entry
to WU frontmatter `re_arm_history` (five fields: timestamp,
prior_status, prior_attempts, prior_cost_usd,
prior_duration_seconds, reason) and increments `re_arm_count`.
T02's already-shipped driver `detect_rearm_dispatch` reads the
incremented count on next dispatch and fires
`fold_cumulative_on_rearm` automatically — the handshake is
**skill writes frontmatter → operator runs driver → driver
detects on first dispatch**. The skill's `u` (unsandboxed)
branch keeps its existing `unsandboxed_rationale` field; the
operator's one rationale input writes to two homes.

## Open verifications

Pre-arm checks the operator runs before flipping these from
`draft` to `pending`. Each is a quick read, not a re-implementation.

### Spinning-detection edge cases — zero-token vs failure-signature repeat

The for-else block at loop.py ~line 2624 distinguishes
`all_attempts_zero_token` (all attempts billed 0 input tokens,
indicating CLI/quota/connectivity not a verification fail) from
`spinning_detected` (≥1 attempt with output that failed verify).
T04 fires earlier (attempt 2) on the latter; the former is
untouched. **Confirm by reading T04 AC3 + the pre-existing
for-else code.** A `[failed(sig=A), zero_token, failed(sig=A)]`
shape correctly trips at attempt 3 (zero_token doesn't reset
prior); a `[zero_token, zero_token, failed]` shape correctly
does NOT trip (no prior to compare against).

### `/gate-status` skill-discovery symlink

The skill body lives at `.specfuse/skills/gate-status/SKILL.md`;
discovery requires the symlink at `.claude/skills/gate-status`.
Already in place (`ls -la .claude/skills/` shows it). T05 reads
the body file directly; the discovery surface is not touched.
**Confirm before arming**: `test -L .claude/skills/gate-status`.
Same shape for T06 (`.claude/skills/unblock-wu`).

### `/unblock-wu` re-arm refusal flow is non-bypassable

T06 AC1 + Escalation #4 lock in: no `--rationale=...` flag, no
env var, no piped-stdin trick that fills the prompt unprompted.
The skill is "Run interactively" per its existing hard rules.
**Confirm by reading T06 AC1 against `SKILL.md` after T06
lands** — a hidden bypass would silently erode the audit signal.

### Driver `detect_rearm_dispatch` handshake

T02's `detect_rearm_dispatch(wu)` returns True when
`re_arm_count > 0 AND cost_usd > 0`. T06 writes the incremented
count BEFORE the operator runs `loop.py`. **Confirm by reading
T06 AC4 + T02's helper at loop.py line ~639**: the
`/unblock-wu` "Print the resume command" step must run AFTER
the frontmatter write. If T06's ordering is reversed, the
driver's first dispatch sees `re_arm_count == 0` and skips the
fold — silent data loss on the cumulative fields.

### `parse_gate_failure_signature` regex coverage

events.jsonl line 11 (G1-CLOSE-INTERMEDIATE attempt 1) records
`failure_class: "other", failure_signature: "no_gate_marker"` —
the underlying failure was `### plan-lint: FAIL` but the parser's
`^### (\w+): FAIL` regex doesn't match `plan-lint` (hyphen not
in `\w`). T04 will halt on the SECOND such failure if it recurs;
two unrelated `plan-lint`-class failures would falsely look like
a repeat. **Confirm acceptable risk** before arming T04: the
conservative behavior (false-positive halt) is cheaper than
three-attempt waste, but the operator may prefer to extend T01's
regex in a separate WU first. Decision recorded in this review
either way.

## Cross-repo contracts

Invented values introduced by this gate. The "Source" column is
where the contract lives; the "Used by" column lists the
consumers downstream. Verify each before arming.

| Value | Type | Source | Used by | Status |
|-------|------|--------|---------|--------|
| `spinning_signature_repeat` | `human_escalation.reason` string | T04 introduces; documented in this WU AC2 | future `/gate-status`-on-this-reason consumer (out of scope here), future predicate-v2 | **unverified** — first use; lock at v1 string literal |
| `(timestamp, prior_status, prior_attempts, prior_cost_usd, prior_duration_seconds, reason)` | `re_arm_history` entry shape | T02 documented in `WU.template.md` frontmatter notes | T06 writes; T05 reads `re_arm_history[-1].reason`; driver's `re_arm_dispatched` event reads same | **verified** against `WU.template.md` (T02-shipped) |
| `re_arm_count`, `re_arm_history`, `cumulative_*` field names | WU frontmatter | T02 documented in `WU.template.md` | T05 reads, T06 writes, driver folds | **verified** against `WU.template.md` (T02-shipped) |
| `attempt_outcome.payload.{failure_class, failure_signature, ...}` field names | `events.jsonl` event payload | T01 documented in PLAN.md § "Event payload shape — `attempt_outcome` v1" | T05 reads, T04 hooks on the same parser output | **verified** against events.jsonl lines 8/11/12 (T01-shipped, terms match) |
| `re_arm_dispatched.payload.reason` field | `events.jsonl` event payload | T02 documented in WU-02 AC5 | T06's `re_arm_history[-1].reason` is the upstream source | **verified** against loop.py line ~2362 (T02-shipped) |

## Predicate self-check

```
FEAT-2026-0016  predicate=v1
  G01  auto=False
    reasons:
      - blocked_human_in_chain: T03 escalated 2026-06-14
    metrics:
      gate_total_cost: $6.61
      gate_budget: $10.00
```

First run where the predicate has REAL `attempt_outcome` data
(T01 produced lines 8 / 11 / 12 of events.jsonl on this gate's
own substantive + closing WUs). The auto-false comes from T03's
prior `blocked_human` state — an intermediate close where the
operator chose re-arm with revised spec (T03's correct
spec-bug diagnosis). For an intermediate close, the predicate
verdict is informational; cost ($6.61 vs $10.00 budget; the
T03 pre-re-arm $0.84 not aggregated by v1) sits comfortably
within budget. No predicate flip recommended; v2 design (relaxed
check-1, structured check-7, prior_attempts aggregation) belongs
to a future feature once data accumulates.

## Summary

Three substantive WUs (T04 spinning-detector hook, T05
`/gate-status` per-attempt surface, T06 `/unblock-wu` rationale +
history write) consuming the gate-1 data layer. T04 is the only
forward-design WU here (driver control-flow edit; high effort,
$2.00); T05 + T06 are skill-side prose edits scoped to one file
each. All three depend only on the gate-1 contracts (T01's event
shape, T02's frontmatter schema, T02's driver fold) — no inter-WU
ordering required, all three can dispatch in parallel from the
ready frontier. G2-CLOSE-INTERMEDIATE then folds T04/T05/T06's
retro + lessons + docs into one session; G2-PLAN drafts gate 3's
substantive WUs (T07 close-ceremony cost-analysis enhancement,
T08 LEARNINGS auto-suggester, T09 docs + roadmap-archive of
folded 0016 scope).

The Cross-repo contracts table's single **unverified** entry is
T04's new `spinning_signature_repeat` reason string — lock it at
v1 in T04 itself; future consumers branch on the exact literal.
