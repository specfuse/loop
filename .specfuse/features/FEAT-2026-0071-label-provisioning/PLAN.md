---
feature_id: FEAT-2026-0071
title: Label registry + provisioning on init/upgrade
slug: label-provisioning
branch: feat/FEAT-2026-0071-label-provisioning
roadmap_goal: Declare every GitHub label specfuse reads in one registry, and create the missing ones during init and upgrade on a best-effort basis that can never fail the command — so the escalation queue and feature discovery work on a fresh repo without a manual setup checklist.
autonomy_default: review
status: done
planned_cost_usd: 14.50
---

# Plan: Label registry + provisioning on init/upgrade

Specfuse ships code that queries GitHub labels it never creates. `gh_features.py`
has run `gh issue list --label specfuse:feature` since FEAT-2026-0003.
FEAT-2026-0046 added six more, and its `emit_escalation` fails outright on an
unknown label because `gh issue create` rejects one. Seven labels, zero
provisioning — so every consumer repo must be told to create them by hand, and
0046's retrospective had to record that as a required operator step rather than
something the tool does.

The fix is a **registry**, not seven `gh label create` calls. Each new label
otherwise repeats the gap. One declared list, and provisioning reads it.

## The constraint that shapes this feature

`scaffold.py` today contains **no subprocess, network, or `gh` call** — `init`
and `upgrade_specfuse` are pure filesystem. That is why they work offline, in CI
containers, and against remotes that are not GitHub. Provisioning must not take
that away.

So it is **best-effort and never fatal.** Missing `gh`, unauthenticated `gh`, a
non-GitHub remote, no git repository at all, or any per-label failure: report what
would have been done and exit zero. An upgrade must never fail because a label
could not be created. Provisioning is idempotent by construction — an existing
label is skipped, never `--force`d over an operator's edited colour or
description.

## Scope boundary

**IN.** The registry with its seven current entries; a `provision_labels`
function with an injectable runner and full degradation handling; wiring into
`init` and `upgrade_specfuse`; and an opt-out.

**OUT — `specfuse-monitor`.** It appears only in FEAT-2026-0040's framing and its
harvester does not exist. Provisioning a label whose sole consumer is unbuilt
repeats the `[FEAT-2026-0029/G1-CLOSE]` failure: shipping a surface whose entry
point is nonexistent. 0040 adds its own entry when it ships.

**OUT — renaming `specfuse:feature`.** It uses a colon where the six newer labels
use kebab-case. The inconsistency is real, but a rename orphans issues already
carrying the label in every consumer repo.

**OUT — a `--no-labels` CLI flag.** The `specfuse init` / `specfuse upgrade` CLI
lives in the **umbrella** repository (`specfuse/cli.py`), which calls into this
package's `scaffold` module. Adding a flag needs a coordinated umbrella release;
putting provisioning inside `scaffold.init()` and `scaffold.upgrade_specfuse()`
needs none, because the umbrella already calls both. The opt-out is therefore an
environment variable (`SPECFUSE_NO_LABELS`) plus a keyword argument, and the CLI
flag is left to a future umbrella change that can read the same variable.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:**
  `grep -rn '\-\-label\|"label"\|LABEL\b\|label=' specfuse/ .specfuse/scripts/ | grep -v test`
- **Verdict:** `no existing mechanism, building new`

The grep returns exactly one hit — `specfuse/loop/gh_features.py:28`,
`"--label", "specfuse:feature"`, a hardcoded string literal inside a runner
function. Nothing declares a label, nothing creates one, and there is no registry
to extend. FEAT-2026-0046's `escalation.py` declares label *names*
(`NEEDS_HUMAN_LABEL`, `CATEGORY_LABELS`) as vocabulary for its emitter, but
carries no colour, no description, and no creation path — it is a consumer of the
vocabulary, not a provisioner of it.

**Reusing that vocabulary rather than restating it.** The registry imports those
names from `escalation.py` instead of retyping them, and T01 asserts every name in
`CATEGORY_LABELS` plus `NEEDS_HUMAN_LABEL` has a registry entry. Two hand-kept
lists of the same seven strings is precisely the drift that guard exists to catch.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

- **What does the rule report on an input already in its intended final state?**
  Zero.

The one predicate-shaped check is T01's registry-coverage test: on a correct tree,
every escalation label has a registry entry and the set difference is empty. It
fires only when someone adds a label name to `escalation.py` without a registry
entry, which is the drift it exists to catch. `provision_labels` run against a
repository whose labels already exist creates nothing and reports every label as
already present — the idempotent no-op, asserted directly in T02.

## Task graph

```yaml
# Single terminal gate: 3 substantive WUs, under the ceremony proportionality
# threshold (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0071/T01
        file: WU-01-label-registry.md
        depends_on: []
      - id: FEAT-2026-0071/T02
        file: WU-02-provision-labels.md
        depends_on: [FEAT-2026-0071/T01]
      - id: FEAT-2026-0071/T03
        file: WU-03-wire-into-init-upgrade.md
        depends_on: [FEAT-2026-0071/T02]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0071/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0071/T01
          - FEAT-2026-0071/T02
          - FEAT-2026-0071/T03
```

Strictly linear: the registry is the data, provisioning consumes it, and the
scaffold wiring calls provisioning.

## Notes

- No work unit touches a real GitHub repository. Every `gh` interaction runs
  through an injected runner, the seam `gh_backend.GitHubBackend` and
  `escalation.emit_escalation` both already use. The cost is the same one
  FEAT-2026-0046 recorded: nothing here proves the real `gh label create`
  invocation works, and the close must name it under
  `## What the loop did NOT verify` as an operator post-merge step.
- The seven labels already exist on **this** repository, created manually before
  this feature was drafted. That makes this repo a poor oracle for the
  create-a-missing-label path and a good one for the idempotent-skip path.
