<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

<!--
PROMPT.md — the agent instruction for the derive-agent-policy skill.

INTENDED USE: run interactively. Start `claude` in the target repo root and
ask it to run the derive-agent-policy skill, or paste this prompt's body into
the session. The skill's whole value is conducting the batched question round
in Step 2 (gate_review, wip_limit, preempt, min_severity, automerge, and the
whole escalation block); piping this file via `claude -p < PROMPT.md` consumes
stdin so the skill cannot ask and silently degrades to the non-interactive
`[gap]` fallback — that fallback exists for CI / dispatched sessions where no
user is reachable, not as the intended invocation.

This prompt operationalizes the method documented in
.specfuse/skills/derive-agent-policy/SKILL.md. Read both before changing either.
-->

You are drafting the `rules`, `budgets`, and `escalation` blocks of
`.specfuse/agent-policy.yml` for the repository you are currently invoked in.
Your job: **draft** the three blocks based on repo evidence plus the
operator's answers, present them **one block at a time for a staged accept**,
and produce a reconciliation report. You do NOT write the file to disk. You
print each block to stdout for the operator to review and confirm before
moving to the next.

Read these in the loop scaffold under this repo's `.specfuse/` before acting:

- `.specfuse/skills/derive-agent-policy/SKILL.md` — the binding method.
- `.specfuse/agent-policy.yml.example` — the file shape, every field's type,
  and the shipped defaults to fall back on when no proposal exists.
- `specfuse/loop/policy_proposals.py` — `propose_policy_defaults`, the
  function this prompt calls for evidence; read its module docstring for the
  scope boundary (four fields only: `max_tokens_per_run`, `max_items_per_day`,
  `max_open_prs`, `test_paths`).
- `specfuse/loop/agent_policy.py` — `validate_agent_policy` and the
  `^[A-Za-z_][A-Za-z0-9_]*$` env-var-name pattern `webhook_env` must satisfy.
- `specfuse/loop/notify.py` — `resolve_webhook_url`, and why an unset or
  unexported `webhook_env` silently posts nothing.

## Method (strict order — propose from evidence first, ask only what evidence
cannot answer, never blur the two)

### Step 1 — Evidence gathering via `propose_policy_defaults`

Call `propose_policy_defaults(repo_root)`. It returns a dict with up to four
keys — `max_tokens_per_run`, `max_items_per_day`, `max_open_prs`,
`test_paths` — each shaped `{value, evidence}`, present only when the repo
actually carries evidence. A missing key means no proposal: fall back to
`.specfuse/agent-policy.yml.example`'s shipped default for that field and
label it plainly as a default when you present it, never as though the repo
suggested it.

Do not hand-derive any of these values yourself. `propose_policy_defaults`
already reads `events_stats.collect`, `gate_commands.iter_code_gates`, and
(if you pass a `runner`) `gh pr list --state open` — call it once and use its
output verbatim, including the evidence string.

### Step 2 — Ask the operator — only what evidence cannot resolve

None of the fields below have repo evidence by construction. Batch all of
them into **one round**, grouped by the block they belong to, each with a
one-line explanation of what it controls:

**`rules.bugs`:** `preempt` (bool), `min_severity`
(`low`|`medium`|`high`|`critical`), `automerge` (`"off"`|`"on"`).

**`rules.features`:** `gate_review` (`human`|`auto`), `wip_limit` (int ≥ 1).

**`escalation`** (ask this group last): `provider`
(`discord`|`slack`|`teams`|`none`), `webhook_env`, `assignee`, `quiet_hours`
(`"HH:MM-HH:MM"` or empty), `sla_hours` (int > 0), `silence_hours` (optional
int > 0, defaults to 24).

**The webhook question, verbatim:** ask *"What environment variable holds
your webhook URL?"* — never *"What's your webhook URL?"* or any phrasing that
invites a pasted URL. When the operator answers, validate the answer against
`^[A-Za-z_][A-Za-z0-9_]*$` before drafting it into the block:

- If it fails (contains `:`, `/`, `.`, whitespace, or starts with a digit),
  do **not** draft it. Re-prompt: explain that `escalation.webhook_env` holds
  an environment-variable *name*, that a pasted URL is a bearer credential a
  committed YAML file must never hold, and ask again for the variable name
  instead.
- If the operator leaves it empty, or names a variable, tell them plainly:
  `resolve_webhook_url` returns `None` whenever the named variable is unset or
  the field is empty, and every escalation post is silently skipped as a
  result — this is not an error state, but it is worth knowing before moving
  on.

**Forbidden questions.** Anything `propose_policy_defaults` already answered
with evidence. If Step 1 returned a `max_tokens_per_run` proposal with
evidence, do not ask the operator to supply one from scratch — present the
proposal and ask only whether they want to override it.

**Non-interactive fallback.** If no operator can answer (CI invocation,
dispatched session, no stdin), still produce a draft: every unanswered
question becomes an explicit `[gap]` line in the report, and every
`escalation` field defaults to its safest value (`provider: none`,
`webhook_env: ""`) rather than a guess.

### Step 3 — Output, staged per block

Present, **in this order, each as its own accept/edit/reject decision** — do
not move to the next block until the operator has responded to the current
one:

1. **`rules`** — `bugs.preempt`, `bugs.min_severity`, `bugs.automerge`,
   `bugs.test_paths` (proposed or default), `features.gate_review`,
   `features.wip_limit`.
2. **`budgets`** — `max_tokens_per_run`, `max_open_prs`, `max_items_per_day`
   (each proposed or default).
3. **`escalation`** — `webhook_env`, `provider`, `assignee`, `quiet_hours`,
   `sla_hours`, `silence_hours`. Re-validate `webhook_env` against the
   env-var-name pattern one more time before printing this block.

Then print the reconciliation report, in this exact structure:

```
# Reconciliation report for <repo-name>

## Evidence inventory (propose_policy_defaults)
- max_tokens_per_run: <evidence string, or "no proposal">
- max_items_per_day: <evidence string, or "no proposal">
- max_open_prs: <evidence string, or "no proposal">
- test_paths: <evidence string, or "no proposal">

## Asked (no repo evidence exists for these)
- preempt → A: <answer>
- min_severity → A: <answer>
- automerge → A: <answer>
- gate_review → A: <answer>
- wip_limit → A: <answer>
- provider → A: <answer>
- webhook_env → A: <answer> (validated against ^[A-Za-z_][A-Za-z0-9_]*$)
- assignee → A: <answer>
- quiet_hours → A: <answer>
- sla_hours → A: <answer>
- silence_hours → A: <answer, or "shipped default 24 used">

## Shipped defaults presented as defaults (not proposals)
- <field>: <value> — no repo evidence

## Webhook note
- <"webhook_env left empty/unexported: escalations post nowhere and nothing
  errors" OR "resolves at runtime via <name>">

## Recommended next step
- Merge the three accepted blocks into `.specfuse/agent-policy.yml`,
  preserving `version`, `queue`, and `rules.triage` as they already stand,
  then run `validate_agent_policy(".specfuse/agent-policy.yml")` and confirm
  the finding list is empty.
```

## Closing rules

- You DRAFT; the operator CONFIRMS, per block. Never write
  `.specfuse/agent-policy.yml` from this prompt. End with a one-line reminder
  that the operator merges the accepted YAML themselves.
- Never draft a `webhook_env` value that fails
  `^[A-Za-z_][A-Za-z0-9_]*$` — re-prompt instead, every time, no exceptions.
- Use the **`status: blocked`** RESULT-block escape only if something
  fundamental prevents drafting at all (no `events.jsonl`, no
  `verification.yml`, and the operator is non-interactive, so even the
  evidence-backed fields have nothing to show). Otherwise produce a draft —
  even one full of `[gap]` markers and shipped defaults — and report.
- No prose summary beyond the report. The report is the summary.

End your turn with the RESULT block defined in
`.specfuse/rules/result-contract.md`. `status: complete` means "I produced a
staged, three-block draft plus report and showed it to the operator" —
verification is the operator reading and accepting it, not a command exit.
