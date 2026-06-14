---
gate: 1
status: awaiting_review
cost_budget_usd: 10.00
---

# Gate 1 — Data layer: attempt_outcome emission + re-arm WU frontmatter contract

## Definition of done

- `attempt_outcome` events are emitted on EVERY dispatch outcome
  (passed, failed, blocked, zero_token, files_changed_mismatch,
  post_pass_invariant_failed, closing_deliverable_missing,
  smoke_import_failed). Payload shape is uniform across all
  emission sites per PLAN.md `attempt_outcome v1`.
- `failure_class` derivation from gate stdout is implemented
  (parses `### {gate}: FAIL` markers) and tested across all gate
  names (tests / lint / security / coverage / symbol_existence /
  bandit / other).
- `failure_signature` extraction is deterministic and stable across
  attempts on the same underlying failure (first failing test name,
  first lint error code, first malformed-WU id, etc.).
- `failure_excerpt` captures ≤500 chars verbatim from the failing
  gate's stdout.
- `files_touched` is captured from `git diff --name-only
  head_before HEAD` at attempt end.
- WU frontmatter gains `re_arm_count`, `re_arm_history`,
  `cumulative_cost_usd`, `cumulative_duration_seconds`,
  `cumulative_input_tokens`, `cumulative_output_tokens`. Lint
  accepts them; driver maintains them.
- WU template (`.specfuse/templates/WU.template.md`) documents the
  new frontmatter fields.
- Driver's cumulative-fold logic fires on `/unblock-wu` re-arm
  detection (status: blocked_human → pending with re_arm_count
  incremented).
- Unit tests cover every attempt_outcome emission branch and the
  cumulative-fold logic.
- Retrospective + LEARNINGS + cost-analysis section written
  (close-intermediate ceremony).
- Gate 2's substantive WUs (T04 spinning-detector hook,
  T05 /gate-status surface, T06 /unblock-wu rationale)
  drafted; GATE-02-REVIEW.md written.

The closing sequence (close-intermediate → plan-next) is enforced
by the linter. Driver halts at gate boundary for review-and-arm.

## Reflection notes

<Written by the human at review time. Especially: did the
attempt_outcome emission cover every code path? Did the
failure_signature extraction prove stable enough to drive a
spinning-detector in gate 2? Did the bootstrap gap show up cleanly
in T01's own events?>
