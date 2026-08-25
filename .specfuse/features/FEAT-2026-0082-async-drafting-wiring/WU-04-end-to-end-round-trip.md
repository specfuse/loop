---
id: FEAT-2026-0082/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 6.00
oracle_env: macos_local
unsandboxed: true
unsandboxed_rationale: "The deliverable is a live gh round-trip — post a real question issue, comment a reply, read it back — which a sandboxed session cannot perform: it fails with an invalid-token or TLS error that reads like a broken feature. Per the CORRECTED LEARNINGS entry [FEAT-2026-0014/T01/gh-claudeP-broken], `unsandboxed: true` is the sanctioned lever, confined to this one WU."
produces:
  - tests/test_drafting_round_trip.py
  - .specfuse/features/FEAT-2026-0082-async-drafting-wiring/ROUND-TRIP.md
model: sonnet
effort: high
---

# Prove a queue entry reaches a drafted folder without an interactive session

**Objective.** Run the whole path for real, once: a `specfuse-agent` run over a
queue holding one undrafted `planned` feature posts a real question issue; a
reply is added; a later run reads it and produces a drafted feature folder; and
`events.jsonl` shows `needs_drafting` resolving to a **completed drafting
dispatch, not an escalation**. Record it in `ROUND-TRIP.md` with raw output.

**Context.** Final substantive WU of FEAT-2026-0082. Read `PLAN.md` for the
scope boundary and — before you write a single criterion off — read `GATE-01.md`
§ *What this gate must not claim*. Depends on T01, T02 and T03; this unit adds no
production code, it exercises theirs.

**Why this unit exists at all.** FEAT-2026-0050 shipped seven work units, every
one green on its first attempt, and delivered something its own retrospective
calls *"green in isolation and connected to nothing."* Every unit's oracle was
its own module. This unit's oracle is the outcome. `[FEAT-2026-0046/G1-CLOSE]`
states the rule directly: *"a criterion that mandates a stub does not defer the
integration risk — it removes it from the WU's scope."*

**The claim you must NOT make.** 0050 carried two follow-ups. This unit
discharges the first. The second is *"one real operator reply... and that reply's
verbatim text fed to `parse_reply_answers`"* — it requires **a human to type
something**. The reply you post in this round trip is a **scripted** reply that
proves the machinery. It is not an operator. Recording it as one would
manufacture evidence that reads as verified rather than as absent, which is worse
than 0050's honest *"none, ever."* Say "scripted reply" in `ROUND-TRIP.md`, in
those words.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`) apply — and note this WU runs unsandboxed, so
`never-touch.md` is doing real work rather than being backstopped by the sandbox.

**Acceptance criteria.**

- `gh auth status` prints `Logged in to github.com`. Dump the **raw
  stdout+stderr** of every `gh` call in this unit between unforgeable BEGIN/END
  markers in `ROUND-TRIP.md` and grep the dump for that signature. Per
  `[FEAT-2026-0014/T01/preflight-must-dump-raw]`, never report an external
  tool's behavior from your own classification of it when the raw output exists.
- **Leg 1 — the question issue is posted for real.** An agent run over a queue
  holding one undrafted `planned` feature files a real issue on this repository
  carrying `needs-human` + `drafting-needed`. Record its number and quote its
  rendered body verbatim in `ROUND-TRIP.md`. A human should read that body once
  before this ships — it is what an operator will actually be asked to answer.
- **Leg 2 — a second run with no reply posts no second issue.** Run again before
  replying. Assert zero new issues and quote the run's own report of what it did.
  This is the state a real queue sits in most of the time.
- **Leg 3 — a scripted reply is read back.** Comment an answer to every question
  using the answer-template shape the issue itself specifies. Quote the comment
  verbatim.
- **Leg 4 — the drafted folder exists.** A later run produces a feature folder,
  and `python3 -m specfuse.loop.lint_plan <folder>` exits 0. Record the folder's
  path and the lint output.
- **Leg 5 — the events say dispatch, not escalation.** Quote the `events.jsonl`
  lines showing `needs_drafting` resolving to a **completed drafting dispatch**.
  A run that drafts a folder while still emitting a `human_escalation` for that
  entry has not met this gate's definition of done.
- **The drafted folder lands `status: planned` and unarmed**, in both PLAN
  frontmatter and its roadmap row. Assert it; the async path must produce exactly
  what the interactive path produces, not something pre-armed.
- `tests/test_drafting_round_trip.py` exists and drives the same five legs
  through injected runners, so the sequence is regression-covered without a
  network. The real run is the evidence; the test is the guard.
- `ROUND-TRIP.md` names every artifact left on the repository — issue numbers,
  comment, any drafted folder or branch — so somebody can clean them up.
- **`ROUND-TRIP.md` states in plain words that the reply was scripted, not from
  an operator**, and that 0050's second carried-forward follow-up therefore
  stays open.

**Do not touch.** Production source — T01, T02 and T03 own all of it; this unit
exercises what they shipped and edits none of it. If a leg fails because their
code is wrong, that is a block, not a patch. `.git/`, secrets. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus every leg
above with its raw output recorded. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if any leg fails — a failing leg
means the seams are still not closed, and the whole feature exists to close them;
patching production code from this unit would hide which unit was wrong. Block if
`gh auth status` fails even with `unsandboxed: true`, rather than falling back to
a stubbed round trip and reporting complete: `[FEAT-2026-0046/G1-CLOSE]` records
exactly that substitution making a unit look verified while the integration risk
went untested, and it is the failure mode this whole feature is a correction for.
**Block rather than post a reply and describe it as an operator's.** If
`ROUND-TRIP.md` is absent from the files you edited, emit `status: blocked` — do
not claim complete. Blocked is respectable (`result-contract.md` rule 4).
