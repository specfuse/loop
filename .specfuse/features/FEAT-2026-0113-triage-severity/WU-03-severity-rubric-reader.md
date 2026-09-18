---
id: FEAT-2026-0113/T03
type: implementation
status: draft
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

The rubric is the operator's own words: the repository's `severity:<value>` label
**descriptions** are what T05's classification prompt will carry. A repository
that defines no `severity:*` label has an empty rubric, and that emptiness is the
whole opt-out mechanism — see `GATE-02.md`.

**Acceptance criteria.**

1. `tests/test_severity_rubric.py::SeverityRubric::test_rubric_reads_label_descriptions`
   fails on HEAD before this unit runs (the module does not exist) and passes after.
2. `grep -c '"label", "list"' specfuse/loop/labels.py` returns `1`: the extracted
   helper is the single site issuing the listing, and `provision_labels` obtains
   its existing-label set from it with every fail-soft branch unchanged —
   `tests/test_provision_labels.py` and
   `tests/test_label_provisioning_runner_contract.py` pass unedited.
3. The rubric reader returns `{severity_value: description}` for each
   `severity:<value>` label whose value is in `agent_policy.SEVERITY_VALUES`, and
   `{}` when the repository defines none.
4. An absent `gh` binary, a non-zero `gh label list` exit, and unparseable output
   each return `{}` rather than raising — asserted case by case with an injected
   runner, never a live `gh` query.

**Do not touch.** `LABEL_REGISTRY` — no `severity:*` entry is added to it, since
not defining those labels is how a project opts out. Every write path in
`labels.py` (`gh label create` stays registry-only). `specfuse/loop/triage.py`
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
