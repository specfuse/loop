---
id: FEAT-2026-0007/T08
type: implementation
model: claude-sonnet-4-6
effort: medium
status: done
attempts: 1
duration_seconds: 79.699
cost_usd: 0.280266
input_tokens: 14
output_tokens: 3257
---

# Telemetry extension: `resolved_model`, cache hit rate, gate summary

**Objective.** Extend the existing telemetry surface so each attempt
record carries the model alias *as resolved at dispatch* (the family
alias → full ID resolution that happens CLI-side today is invisible to
the log) and so a gate summary surfaces `cache_hit_rate` derived from
the already-recorded `cache_read_input_tokens` /
`cache_creation_input_tokens` / `input_tokens` fields.

**Context.** This is `FEAT-2026-0007/T08`. Reads:

- The per-attempt record assembly in `.specfuse/scripts/loop.py:782`
  (`attempt_record` dict; merges `usage` into it).
- The usage parse at `loop.py:524`-ish — `_parse_dispatch_result`
  already pulls `cache_read_input_tokens` and
  `cache_creation_input_tokens` when present.
- The `task_completed` event payload at `loop.py:823`.
- Depends on **T08H** because the `effort_used` and `terseness` fields
  T08H lands are the sibling fields to the new `resolved_model` and
  `cache_hit_rate` here. Without T08H, the per-attempt record schema is
  still T02-shape (no `effort_used`/`terseness`) and T08's tests would
  assert against a schema that doesn't match production.

Reference the binding rules under `.specfuse/rules/`. The driver owns
git; edit files only.

**Acceptance criteria.**
1. New helper `cache_hit_rate(usage: dict) -> float | None` returns
   `cache_read_input_tokens / (cache_read_input_tokens +
   cache_creation_input_tokens + input_tokens)` when all three keys
   are present and the denominator is non-zero; returns `None` when any
   key is absent or the denominator is zero. The denominator choice —
   reads vs reads-plus-creations-plus-fresh-input — is documented in
   `GATE-02-REVIEW.md`'s "Decisions & rationale" and is flagged as an
   open question for the human to confirm with first telemetry.
2. The per-attempt record assembled at `loop.py:782` gains a
   `resolved_model` string field equal to `wu.model` post-`load_wu`
   (which after T06 is the type-keyed default when frontmatter is
   absent, or the declared value when present). This captures the
   alias the CLI dispatched, not the further full-ID expansion CLI-side.
3. The `task_completed` event payload (`loop.py:823`) gains a
   `cache_hit_rate` field computed by `cache_hit_rate(usage)` for the
   final attempt's `usage`. When `None`, the field is omitted from the
   payload (per the existing "absent key" convention used by usage
   merging at line 785).
4. Aggregate gate summary: a new helper `gate_summary(events: list,
   gate_n: int) -> dict` returns
   `{total_cost_usd, total_duration_seconds, total_input_tokens,
   total_output_tokens, mean_cache_hit_rate, wu_count}` computed from
   the `task_completed` events for this gate. Used by
   `gate-status` / future gate review surfaces; not invoked by the
   dispatch loop directly.
5. Tests in `tests/test_loop_telemetry.py`:
   (a) `cache_hit_rate` with all keys present returns the expected
       fraction.
   (b) `cache_hit_rate` returns `None` when `cache_read_input_tokens`
       is missing.
   (c) `cache_hit_rate` returns `None` on zero denominator.
   (d) Integration: a stubbed dispatch with a known `usage` payload
       produces a `task_completed` event whose payload includes both
       `cache_hit_rate` (a float in [0,1]) and a per-attempt
       `resolved_model` matching the loaded WU.
   (e) `gate_summary` over a fixture of three `task_completed` events
       computes `total_cost_usd`, `wu_count == 3`, and a sensible
       `mean_cache_hit_rate` (mean over events where the field is
       present).
6. **Existence check** (per LEARNINGS `[FEAT-2026-0007/G1-LESSONS]`):
   `python3 -c "from loop import cache_hit_rate, gate_summary"` must
   succeed before claiming complete.

**Do not touch.** Exactly 2 files change: `.specfuse/scripts/loop.py`
and one new test file `tests/test_loop_telemetry.py`. No edits to:
`WU.template.md`, `.specfuse/rules/`, `.specfuse/verification.yml`,
the `events.jsonl` event_type set (the new fields ride inside an
existing event type), existing WU files, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`,
plus the existence smoke check in AC 6.

**Escalation triggers.**
1. **Completeness.** If `cache_hit_rate` or `gate_summary` is absent
   from `loop.py` after your edits, emit `status: blocked` — do not
   claim complete.
2. **Schema drift on `attempts_usage`.** This WU adds fields to the
   per-attempt record and the `task_completed` payload only — it does
   **not** modify the `attempts_usage` field schema landed by T08H.
   If implementing AC 2 requires changing the shape of
   `attempts_usage` (vs adding `resolved_model` alongside), stop and
   re-read T08H's AC 7.
3. **Denominator question.** AC 1's denominator (reads + creations +
   input) is the design call; the alternative is reads / (reads +
   input). If implementation reveals the chosen formula produces
   degenerate values on the real Gate 2 events (e.g. > 1.0 or all
   `None`), prefer to emit `status: blocked` and flag the choice rather
   than silently swap formulas — the human will pick from
   `GATE-02-REVIEW.md`'s open question.
4. **Dependency order.** If `effort_used` / `terseness` are absent from
   the per-attempt record at the time this WU dispatches (i.e. T08H
   did not land cleanly), stop and emit `status: blocked` rather than
   re-implementing T08H's contract here.
