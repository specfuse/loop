---
name: unblock-wu
description: Re-arm one or more `blocked_human` work units after a fix (credentials, spec ambiguity, missing dep, etc.) so the loop driver retries them. Flips each WU `status: blocked_human` → `pending` and `attempts: 0`; if the WU's gate is `awaiting_review` (driver left it stuck after the block), flips the gate back to `open`. Per-WU propose-and-confirm. Prints the resume command.
---

# Unblock work unit (interactive, propose-and-confirm)

Counterpart to `/arm-gate`. `/arm-gate` is for gate-boundary draft
review. This skill is for **mid-gate** recovery: the driver halted
on one or more WUs that escalated to `status: blocked_human`, you
have addressed the root cause (or want to retry as-is), and you want
the driver to pick them up on the next run.

Posture mirrors `/arm-gate`: propose-and-confirm-per-WU. The skill
writes nothing without your explicit decision on each blocked unit.

**Run interactively.** Per-WU prompts are the whole point; `claude
-p` with redirected stdin falls back to a degraded "list blocked
WUs and stop" mode.

## Hard rules

- **Per-WU decision required.** No batch-re-arm-all by default —
  each blocked WU is its own retry/abandon/skip decision. (A
  `--all` shortcut may grow later when evidence shows the
  per-WU prompt is friction without value; today, no.)
- **Modify only the WU `status` + `attempts` fields and, if needed,
  the gate file's `status`.** No body edits, no PLAN graph surgery,
  no roadmap edits. If a blocked WU needs spec changes, exit the
  skill and edit the WU file directly, then re-run.
- **Do not retry without acknowledging the root cause.** Before
  flipping a WU to `pending`, the user must confirm what changed
  (credentials updated, spec amended, dep installed, environment
  fixed) or explicitly choose "retry as-is, I want another attempt
  from a clean slate".
- **`attempts: 0` is mandatory.** Without the reset, the next failure
  trips the spinning escalation immediately because the prior
  `MAX_ATTEMPTS` block-paths already incremented the counter.

## When to invoke

When `python3 .specfuse/scripts/loop.py` printed:

```
Gate N halted: M work unit(s) need human attention.
  - FEAT-YYYY-NNNN/TNN
      reason: <why>
```

— or any time a WU file under the active feature sits at `status:
blocked_human` and you've fixed the cause.

If no blocked WU exists, the skill stops with a hint (probably you
wanted `/arm-gate` for a gate-boundary draft, or `/gate-status` for
a diagnosis pass).

## Method

### 1. Detect the state

- Find the active feature (roadmap `status: active`; if multiple, ask
  via `--feature` or pick interactively).
- Walk PLAN.md's gates graph. For each WU file, read frontmatter.
  Collect every WU with `status: blocked_human` — these are the
  candidates. Note which gate each belongs to and that gate's status.
- If no blocked WU exists, stop and explain.

### 2. Surface the diagnosis context

For each blocked WU, before asking the user, pull and quote:

- The WU's `id`, `file`, `attempts`, `cost_usd`, `duration_seconds`.
- The latest `human_escalation` event for that correlation_id in
  `events.jsonl` — quote `blocked_reason` and `reason`.
- If `work/<wu_id>/attempt-N.md` notes exist, quote the tail of the
  most recent one.
- The matching gate file's `status` (for the gate-reopen step).

This is diagnostic context, not a decision. The user already knows
why they're here; this is a sanity-check that the right WUs are
being touched.

### 3. Per-WU re-arm / abandon / skip

> **Write-ordering invariant (BEFORE driver dispatch).** For `r` and
> `u` choices, the frontmatter write — `status: pending`, `attempts: 0`,
> incremented `re_arm_count`, and appended `re_arm_history` entry — MUST
> complete before the operator runs `loop.py`. The driver's
> `detect_rearm_dispatch` reads `re_arm_count` from disk on the first
> dispatch of the new cycle; if the write has not landed, the cumulative
> fold misfires. The "Print the resume command" step (§5) follows this
> write; do not print the resume command before the frontmatter write is
> confirmed.

For each candidate, ask:

```
Re-arm sandboxed (r) / Re-arm UNSANDBOXED (u) / Abandon (a) / Skip (s)
  — FEAT-YYYY-NNNN/TNN ?
  attempts: <N>  cost: <$X>  duration: <Ys>
  blocked_reason: "<...>"
  re-arm rationale (required for r and u — one line):
```

- **Re-arm sandboxed (default)** — prompt the operator for a one-line
  rationale. If the operator submits an empty string or whitespace-only
  input, print:

  ```
  re-arm rationale required — type a one-line reason or choose s/a
  ```

  and re-prompt the same WU. Do NOT proceed to any frontmatter write
  with an empty rationale. A non-empty rationale is the audit signal;
  `events.jsonl` already carries the prior escalation context.

  On accept of a non-empty rationale (trimmed), perform ONE frontmatter
  write that atomically sets all of the following:

  1. `status: blocked_human` → `pending`
  2. `attempts: N` → `attempts: 0`
  3. `re_arm_count`: read existing value (default `0` when absent),
     write back `re_arm_count + 1`.
  4. Append to `re_arm_history` list (initialise to `[]` when absent):

     ```yaml
     -
       timestamp: <ISO 8601 UTC, e.g. 2026-06-15T12:34:56+00:00>
       prior_status: blocked_human
       prior_attempts: <int — the WU's pre-re-arm `attempts`>
       prior_cost_usd: <float — the WU's pre-re-arm `cost_usd`, default 0.0 when absent>
       prior_duration_seconds: <float — the WU's pre-re-arm `duration_seconds`, default 0.0>
       reason: "<operator's one-line rationale, trimmed>"
     ```

  The `reason` field in the new `re_arm_history` entry is the string the
  driver's `re_arm_dispatched` event reads via `re_arm_history[-1].reason`.
  A re-arm without this write produces a `re_arm_dispatched` event with
  `reason: ""` — treat that as a bug in the skill execution, not expected
  behaviour. WU dispatches under the normal claude-p sandbox on next run.

- **Re-arm UNSANDBOXED** — sandbox-escape escalation. Use ONLY when
  diagnosis pinpoints the sandbox itself as the block (e.g. `gh
  auth status` succeeds in the operator shell but fails inside
  `claude -p`; an MCP tool that needs unrestricted network; a
  filesystem path outside the allowlist). Process:
  1. Quote the diagnostic evidence that points at sandbox (the
     same evidence the operator just confirmed in `/gate-status`
     or via direct probe like `echo … | claude -p`).
  2. Ask the operator for an explicit one-line **rationale** (this
     is written to the WU frontmatter — it is the durable audit
     signal, not a per-run comment). The rationale must name the
     specific blocked surface: "gh CLI auth requires unsandboxed
     subprocess" beats "needs unsandboxed". Apply the same
     mandatory-rationale rule as the sandboxed branch: empty or
     whitespace-only input prints `re-arm rationale required — type
     a one-line reason or choose s/a` and re-prompts.
  3. Surface the security implication: an unsandboxed agent has
     full shell. The `Do not touch` clause + driver `git reset
     --hard` on failed attempts contain blast radius but do not
     eliminate it. Require explicit yes/no.
  4. On yes: perform ONE frontmatter write that atomically sets:
     - `unsandboxed: true`
     - `unsandboxed_rationale: "<one-line>"` (the rationale the
       operator typed — unchanged, not truncated)
     - `status: pending`, `attempts: 0`
     - `re_arm_count`: incremented by 1 (same rule as sandboxed)
     - `re_arm_history`: append one entry with the same five-field
       shape as the sandboxed branch. The `reason` field is THE
       SAME rationale string the operator typed — one input, two
       homes: `unsandboxed_rationale` for the driver's sandbox gate;
       `re_arm_history[-1].reason` for the cross-cycle audit trail.
     Driver will refuse to dispatch if `unsandboxed_rationale` is
     missing — both `unsandboxed` fields are mandatory. The driver
     emits an `unsandboxed_dispatch` event in `events.jsonl` before
     each attempt.
  5. Append a learning entry to `.specfuse/LEARNINGS.md` (if not
     already there) tagged with the sandbox-trigger pattern so
     future WU drafts anticipate this surface at plan time rather
     than discover it via block-then-rearm cycle.
- **Abandon** — flip `status: blocked_human` → `abandoned`. The WU
  stays in the PLAN graph (no graph surgery here); the loop skips
  it. If abandoning makes the gate uncloseable (a substantive WU
  whose deliverable is required), warn the user but do not block —
  the user owns that call. (For full feature-level abandon, use
  `/abandon-feature` instead.) Does NOT write `re_arm_history` and
  does NOT increment `re_arm_count` — abandon is not a re-arm.
- **Skip** — leave at `blocked_human`, move to next. If any skipped
  WUs remain at the end, the driver will halt again at the same
  point on next run; tell the user so explicitly. Does NOT write
  `re_arm_history` and does NOT increment `re_arm_count` — skip is
  not a re-arm.

### 4. Reopen the gate (if needed)

After per-WU decisions, look at each gate that had a re-armed WU:

- If the gate's `status: awaiting_review` (the driver flipped it
  during the block path), flip it back to `status: open`. Without
  this flip, the driver's closing-sequence dispatch logic still
  thinks the gate is closing and may behave unpredictably.
- If `status: open` already, leave alone.

### 5. Print the resume command

- One active feature: `python3 .specfuse/scripts/loop.py`
- Multiple active features: `python3 .specfuse/scripts/loop.py
  --feature FEAT-YYYY-NNNN-<slug>` (name the chosen feature).

Mention: `--dry-run` confirms the ready-set before dispatch.

End with the RESULT block per
[`../../rules/result-contract.md`](../../rules/result-contract.md).
`status: complete` means every blocked WU was decided (re-armed,
abandoned, or knowingly skipped) and any necessary gate-reopen
flips wrote.

## What this skill does NOT do

- **Does not edit WU bodies.** Spec fixes are a direct-edit task,
  not an interactive prompt loop. The skill assumes the spec is
  already correct (or you've decided to retry as-is).
- **Does not run verification.** Just flips status fields. The
  driver runs the gates on the next attempt.
- **Does not touch PLAN.md graph or roadmap.** Mid-gate recovery
  doesn't change feature shape; only WU + gate statuses move.
- **Does not run the loop.** Prints the command; the user runs it.

## Version

**v0.2.** Mandatory rationale on `r` and `u` re-arm choices: empty
or whitespace-only input is rejected with `re-arm rationale required
— type a one-line reason or choose s/a` and the same WU is
re-prompted. On accept, the skill writes a `re_arm_history` entry
(five fields: `timestamp`, `prior_status`, `prior_attempts`,
`prior_cost_usd`, `prior_duration_seconds`, `reason`) and increments
`re_arm_count` atomically with the existing `status`/`attempts`
flip. The `reason` field feeds the driver's `re_arm_dispatched`
event via `re_arm_history[-1].reason`. Abandon (`a`) and skip (`s`)
are unchanged — they are not re-arms and do not touch these fields.
Write ordering: frontmatter write BEFORE the resume command is
printed (see §3 invariant note).

**v0.1.** Five steps; re-arm / abandon / skip is the entire per-WU
decision vocabulary today. Expected to grow once real recoveries
surface needs that don't fit it — e.g. "retry once with a different
model" (a one-shot model override on the WU frontmatter), "retry
with attempts ceiling raised to 5" (a one-shot `MAX_ATTEMPTS`
override) — which are real possibilities but deferred until evidence
warrants. Shared methodology craft (loop is near-term author).
