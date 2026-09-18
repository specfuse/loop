---
id: FEAT-2026-0113/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces:
  - specfuse/loop/labels.py
  - tests/test_severity_rubric.py
---

# T03 — extract the label listing, and read the severity rubric from it

**Objective.** One reusable label-listing helper in `specfuse/loop/labels.py`, and a
severity rubric read from the `severity:*` labels a repository defines for itself.

**Context.** `PLAN.md`'s **Existing-mechanism search** is binding here:
`specfuse/loop/labels.py:267` already issues
`gh label list --json name,color,description --limit 1000` through an injected
runner, inside `provision_labels`, with fail-soft handling for an absent `gh`
binary, a non-zero exit and unparseable output. This unit **extracts** that call;
it does not add a second listing. The extraction gets two callers the moment it
lands — `provision_labels` itself and the new rubric reader — so
`tests/test_caller_check_ratchet.py` stays green, which is the concern
`PLAN.md`'s Assumptions flagged when it placed this reader in gate 2.

**Two rubric sources, and the repository always wins.** A repository that defines
any `severity:*` label is declaring its own scheme, and its label descriptions are
the rubric — specfuse provisions nothing and contributes nothing, so a repository
labelling `severity:major` / `severity:minor` is never handed a second overlapping
set. A repository that defines **none** gets specfuse's published default rubric
and the four labels provisioned on first use.

That second branch is the correction this unit was revised for. Reading absence as
"this project opted out" made the feature inert by default — a repository that
never invented its own severity labels would get no severity forever, so
`min_severity` would keep stranding exactly the issues #3352 measured. The
reasoning that produced it conflated two things: **where the floor sits**
(`rules.bugs.min_severity`) must be the operator's, because that is the decision
gating unattended merges, but **what `high` means** does not have to be. Every
severity scheme in wide use ships vendor-written definitions and lets the operator
choose the threshold against them. Only the first constraint is load-bearing, and
it is untouched by either branch.

Provisioning is required, not cosmetic: `gh issue edit --add-label severity:high`
fails against a label that does not exist. That is #3244's "registered is not
provisioned" lesson, and this unit reuses the **shape** that lesson established —
`gh label create <name> --color --description --force`, idempotent, never raised —
inside `labels.py`. It does **not** import or wire any driver helper: `labels.py`
imports the driver's siblings, never the driver, and that direction is not
negotiated here.

**Acceptance criteria.**

1. `tests/test_severity_rubric.py::SeverityRubric::test_rubric_reads_label_descriptions`
   fails on HEAD before this unit runs (the module does not exist) and passes after.
2. `grep -c '"label", "list"' specfuse/loop/labels.py` returns `1`: the extracted
   helper is the single site issuing the listing, and `provision_labels` obtains
   its existing-label set from it with every fail-soft branch unchanged —
   `tests/test_provision_labels.py` and
   `tests/test_label_provisioning_runner_contract.py` pass unedited.
3. The rubric reader returns `{severity_value: description}`. When the repository
   defines **any** `severity:*` label, the rubric is built from those labels alone
   — every value in `agent_policy.SEVERITY_VALUES` that the repository describes,
   and nothing specfuse authored. When it defines **none**, the rubric is the
   shipped `DEFAULT_SEVERITY_RUBRIC`: one entry per value in `SEVERITY_VALUES`,
   each with a published one-line definition. Asserted both ways.
4. A repository defining a `severity:*` label whose value is in `SEVERITY_VALUES`
   but whose description is empty gets the shipped definition **for that value
   only**; the rest of its own descriptions stand. Nothing escalates, and no
   repository-authored description is ever overwritten.
5. Provisioning is conditional and narrow: the four labels are created — through
   the existing `gh label create … --force` shape, never a bare `create` — only on
   the branch where the repository defined no `severity:*` label at all. Asserted
   by argv: the defines-its-own branch issues **zero** `gh label create` calls.
6. A failed label creation is reported and never raised, and leaves the rubric
   usable — same fail-soft posture as every other branch in this module.
7. An absent `gh` binary, a non-zero `gh label list` exit, and unparseable output
   each return `{}` rather than raising — asserted case by case with an injected
   runner, never a live `gh` query.

**Do not touch.** `LABEL_REGISTRY`'s existing entries and `provision_labels`'
registry-driven behaviour — the four `severity:*` specs are added as their own
named collection and provisioned on the empty-namespace branch only, so no
existing caller of `provision_labels` starts creating severity labels as a side
effect. `rules.bugs.min_severity` and `rules.bugs.severity_aliases`: where the
floor sits stays the operator's in both branches. `specfuse/loop/triage.py`
(T04), `specfuse/agent/triage_invoke.py` (T05),
`specfuse/agent/providers/triage.py` (T06). `agent_policy.py`'s severity readers
and its `SEVERITY_VALUES` / `SEVERITY_ORDER` vocabulary, which this unit reads
and does not extend.

**Verification.** The narrow tier for `implementation` — the `code` gates in
`.specfuse/verification.yml` minus those declaring `tier: broad`, with `tests`
narrowed to this unit's `produces:` modules. Plus, in this unit's session:
`python3 -m unittest tests.test_provision_labels tests.test_label_provisioning_runner_contract tests.test_caller_check_ratchet -b`,
and a symbol check per new symbol
(`python3 -c "from specfuse.loop.labels import <helper>, <reader>"`). If either
new symbol is absent from the files you edited, emit `status: blocked`.

**Escalation triggers.** If extracting the listing forces a change to
`provision_labels`' signature or to its injected-runner contract — the
`repo`-vs-`cwd` split #2081 documents at `labels.py:230` — stop: that contract
has already silently broken the on-demand provisioning path once, and widening
it is a different unit. If reading the rubric appears to need a live `gh` query
rather than an injected runner, stop; a test that needs the network is not this
gate's oracle.
