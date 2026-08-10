---
id: FEAT-2026-0047/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
oracles: [oracles]
---

# Close FEAT-2026-0047 — terminal gate

**Objective.** Close the feature: re-run every oracle fresh, prove no credential
can reach git or a log, reconcile cost, write the retrospective and lessons,
enumerate consumer-visible contract changes, and record an honest verdict.

**Context.** Correlation ID `FEAT-2026-0047/G1-CLOSE`. Terminal close of a
single-gate feature. Depends on T01–T04.

`auto_close_disabled: true` is set deliberately: this close re-runs oracles per
`close-discipline.md` §1, which makes it load-bearing (#189).

**This close carries one obligation the others do not: proving that a bearer
credential cannot escape.** The feature's entire security posture is that the
webhook URL lives in the environment and touches nothing else. Re-test it in
this session, from the shipped code — a close that only writes prose verifies
nothing:

1. `escalation.webhook` is rejected as an unknown key, and a literal URL in
   `escalation.webhook_env` is an `ERROR: ` finding.
2. The resolved URL appears in no return value, no exception text, and no log
   line, including on the failure paths.
3. This repo's own `.specfuse/agent-policy.yml` carries an **empty**
   `webhook_env`, and `leak-scan` is clean over the tree.

**Also record honestly:**

- This feature was **drafted solo, with no operator interview** (operator
  instruction, 2026-08-09). `PLAN.md` § *Assumed decisions* lists eight
  decisions — state which the implementation validated, which it strained, and
  which are unexercised.
- **T01 changed a field FEAT-2026-0044 shipped the same night**
  (`escalation.webhook` → `webhook_env`). Record what that cost and whether the
  rename-without-shim call held up.
- **The whole configured path is untested against a real provider.** Every test
  injects a poster. Say so plainly rather than letting green tests read as
  "notifications work."

The closing sections are scaffolded at dispatch (`close-discipline.md` §4 and
the registry in `specfuse/loop/closing_requirements.py`) — fill them with
substance rather than re-deriving the headings.

Binding rules apply by reference: `result-contract.md`, `close-discipline.md`,
`never-touch.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. **Oracles re-run fresh in this session** (`close-discipline.md` §1), exit
   codes read directly: the full `code` gate set from
   `.specfuse/verification.yml` — `tests`, `lint`, `security`, `coverage`,
   `leak-scan`, `event-type-gate`, `roadmap-link-gate`, `arm-sweep-gate`,
   `monitoring-example-lint`, `agent-policy-example-lint`. Each command and its
   exit code recorded in `RETROSPECTIVE.md`.
2. **Security claim 1 re-tested:** a policy carrying `escalation.webhook`
   produces an `ERROR: ` finding, and one carrying a literal `https://` URL in
   `webhook_env` produces an `ERROR: ` finding. Both run in this session and
   recorded.
3. **Security claim 2 re-tested:** with a fake webhook URL in the environment
   and a poster that raises, the URL appears in neither the raised text, the
   returned value, nor any captured log output. Recorded.
4. **Security claim 3 re-tested:** this repo's `.specfuse/agent-policy.yml`
   carries an empty `webhook_env`, and `leak-scan` over the tree is clean.
   Recorded.
5. **The composite oracle** no individual WU could run: a single simulated
   escalation, with an injected poster, produces exactly one notification on
   filing (T02), exactly one re-ping after the SLA window and a park on the
   second sweep (T03), and no post at all when `webhook_env` is empty. This is
   the feature-level assertion that the four units compose.
6. `RETROSPECTIVE.md` exists with a `## Cost analysis` section reconciling each
   WU's `planned_cost_usd` against actual from `events.jsonl` (including re-arm
   cycles via `cumulative_*`), per-WU delta, gate total against the $24.50
   budget, and feature total against `PLAN.md`'s $20.00. Any WU over 50%
   variance carries a one-paragraph cause.
7. `RETROSPECTIVE.md` records the three items in this WU's Context: the
   solo-drafting decision audit (all eight), the cost of the `webhook_env`
   rename against a same-night schema, and the untested-configured-path
   admission.
8. `.specfuse/LEARNINGS.md` gains at least one entry, or an explicit note that
   nothing generalized. The "config holds a name, environment holds the value"
   convention is a strong candidate if it generalizes beyond this feature.
9. **Consumer-visible contract changes** enumerated (`close-discipline.md` §3):
   the `escalation.webhook` → `webhook_env` **breaking rename**, the new
   `escalation.provider` and `escalation.silence_hours` keys, the new
   `escalation-parked` label, the new `<!-- specfuse:sla-repinged -->` marker,
   and the `/attention` skill's new staleness section — or exactly `n/a — no
   consumer-visible contract change` if genuinely empty, which it is not.
10. Documentation reflects what shipped: the roadmap's FEAT-2026-0047 detail
    section describes the delivered shape, and the row and detail status agree.
11. A verdict is recorded. `met` only if every acceptance criterion across
    T01–T04 was verified in-loop. Otherwise `met_locally` / `partially_met` with
    a `## Hedged-verdict follow-up record` carrying, per unmet criterion, the
    criterion verbatim, why it is unverifiable here, the exact re-run condition
    that would upgrade it, and a `kind:` written as `- **kind:** \`<value>\``.
12. `## What the loop did NOT verify` lists every deferred criterion with where
    it actually gets checked. **A live post to a real Discord/Slack/Teams
    webhook is expected to appear here** — every test injects a poster, so the
    end-to-end channel delivery is an operator-deferred oracle. Naming it
    honestly is required; green tests must not read as "notifications work".
13. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Any source file under `specfuse/` — this close verifies, it
does not implement; if an oracle fails, record it and emit `status: blocked`.
`.specfuse/agent-policy.yml`'s `webhook_env` — it stays empty; a close session
must not add a URL to exercise a path. Other features' folders.
`.specfuse/rules/`. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

Do **not** write `PLAN.md`'s `status` field — the driver owns the terminal flip
(`fire_terminal_flips`, gated on the verdict).

**Verification.** The `plannext` gate set plus the fresh full-`code` re-run in
criterion 1, the three security re-tests in criteria 2–4, the composite oracle
in criterion 5, and `specfuse lint --closing`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
any oracle in criterion 1 fails; **any of the three security claims in criteria
2–4 does not hold** — that is a feature that must not ship as-is, and the
verdict is `not_met`, not a hedge; the composite oracle in criterion 5 shows a
double re-ping or a post with an empty `webhook_env`; or `events.jsonl` lacks
the cost data criterion 6 needs.
