---
id: FEAT-2026-0076/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 5.00
oracle_env: macos_local
produces:
  - plugins/specfuse/skills/derive-agent-policy/SKILL.md
  - plugins/specfuse/skills/derive-agent-policy/PROMPT.md
  - tests/test_derive_agent_policy_skill.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.10.0
started_at: 2026-08-10T15:07:05.710507+00:00
duration_seconds: 489.065
cost_usd: 1.903363
input_tokens: 78
output_tokens: 19671
---

# Ship the `derive-agent-policy` skill

**Objective.** Author `plugins/specfuse/skills/derive-agent-policy/SKILL.md` and
`PROMPT.md` — the interview that fills `agent-policy.yml`'s `rules`, `budgets`
and `escalation` blocks — vendor them, and ship the structural test that holds
the prose to the algorithm T01 built.

**Context.** Correlation ID `FEAT-2026-0076/T02`. Depends on
`FEAT-2026-0076/T01`: the prose must describe an algorithm that exists.

**Copy the shape of the two siblings.** Read
`plugins/specfuse/skills/derive-verification/SKILL.md` and
`derive-monitoring/SKILL.md` first. Both are ~360–390 lines with the same spine —
*Why this exists*, *Hard rules*, *The method (in strict order)*, the report
sections, *Seams*, *What this skill does not do* — and both ship a `PROMPT.md`
alongside. Match that structure; do not invent a third shape.

Their shared posture is the contract here too: **evidence first, ask only what
the repo cannot answer, draft and never auto-write, staged per-block accepts.**

**What is proposed versus what is asked.** T01 draws the line and this prose must
not blur it. `budgets.max_tokens_per_run`, `budgets.max_items_per_day`,
`budgets.max_open_prs`, and `rules.bugs.test_paths` are **proposals** — present
the value with the evidence that produced it and let the operator disagree.
Everything else — `gate_review`, `wip_limit`, `preempt`, `min_severity`,
`automerge`, and the whole `escalation` block — is **asked**, because no repo
evidence answers it. Presenting an invented value as evidence-backed is the
failure `[FEAT-2026-0039]` shipped.

Where T01 proposes nothing, the skill presents the shipped default and **says
plainly that it is a default**, never as though the repo suggested it.

**The one constraint that must not be lost.** The webhook prompt collects an
**environment-variable name, never a URL.** An incoming-webhook URL is a bearer
credential; `escalation.webhook_env` is validated against
`^[A-Za-z_][A-Za-z0-9_]*$` precisely so one cannot enter a committed file. An
interview that prompts *"paste your webhook URL"* hand-feeds the credential the
validator exists to refuse, in the one flow an operator trusts most. If a drafted
value fails that shape, re-prompt and explain — never write it and let the
validator catch it later. Note also that an unset variable makes
`resolve_webhook_url` return `None` and no-op **silently**, indistinguishable
from "no webhook configured" unless the interview says so.

**Skills are canonical in `plugins/specfuse/skills/`.** Author there, then run
`scripts/sync-scaffold.sh`, which vendors into `.specfuse/skills/` and creates
the `.claude/skills/` discovery link. `tests/test_skills_vendored_in_sync.py` and
`tests/test_skill_discovery_links.py` both fail if you edit or link by hand.

**A prose artifact passes every code gate trivially** (`[FEAT-2026-0003/G2-LESSONS]`).
The structural test is the only falsifiable check that exists here — write it to
assert on load-bearing literals and required sections, not on wording.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because the skill
file does not exist.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_derive_agent_policy_skill.py::TestDeriveAgentPolicySkill::test_skill_file_exists`
   exists and **fails on HEAD before this WU runs**.
2. `plugins/specfuse/skills/derive-agent-policy/SKILL.md` exists with YAML
   frontmatter carrying `name: derive-agent-policy` and a `description:` naming
   the trigger phrases, and carries the Apache-2.0 header every sibling uses.
3. `plugins/specfuse/skills/derive-agent-policy/PROMPT.md` exists, matching the
   siblings' pairing.
4. A test asserts the body names `propose_policy_defaults`,
   `validate_agent_policy`, and `.specfuse/agent-policy.yml` as **exact-match
   literals** — the skill must reference the real API, not describe it
   approximately.
5. A test asserts the body names all four proposed values
   (`max_tokens_per_run`, `max_items_per_day`, `max_open_prs`, `test_paths`) and
   states that they are **proposed from evidence**, distinguishing them from the
   asked values.
6. A test asserts the body states that where no proposal is available the shipped
   default is presented **as a default**.
7. A test asserts the webhook constraint is present: the prose requires an
   environment-variable **name** and explicitly refuses a pasted URL. This is the
   security-critical assertion — it must match on the requirement, not on
   incidental wording.
8. A test asserts the body carries **staged per-block accepts** and the
   **draft-never-auto-write** rule.
9. A test asserts the body carries the escalation-framing section referencing
   `.specfuse/rules/operator-escalation.md`, matching every sibling skill.
10. A test asserts the body carries a "What this skill does NOT do" section.
11. `scripts/sync-scaffold.sh` has been run;
    `.specfuse/skills/derive-agent-policy/SKILL.md` and `PROMPT.md` are
    byte-identical to the canonical copies, and `.claude/skills/derive-agent-policy`
    resolves to the vendored directory.
12. `python3 -m unittest tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
    exits zero after this WU's edits.

**Do not touch.** `plugins/specfuse/skills/derive-verification/` and
`derive-monitoring/` — read them for shape, do not edit them.
`plugins/specfuse/skills/groom-backlog/SKILL.md` — T03 owns the boundary edit;
do not pre-empt it here. `specfuse/loop/policy_proposals.py` — T01 owns it; this
WU describes it. `specfuse/loop/agent_policy.py`. `.specfuse/skills/` directly —
author the canonical `plugins/` copy and let the sync script vendor it.
Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, `agent-policy-example-lint`.
Plus the scoped run in criterion 12.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`scripts/sync-scaffold.sh` fails or reports drift in surfaces this WU did not
touch; the sibling skills' structure has diverged enough that "match the shape"
is ambiguous (report what differs rather than inventing a third shape); or the
prose cannot describe T01's algorithm because T01 shipped a different one — that
is a spec mismatch worth surfacing, not working around. If
`plugins/specfuse/skills/derive-agent-policy/SKILL.md` is absent from the files
you edited, emit `status: blocked` — do not claim complete.
