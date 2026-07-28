---
id: FEAT-2026-0071/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces:
  - specfuse/loop/scaffold.py
  - tests/test_scaffold_label_provisioning.py
produces_driver_helper:
  - init
  - upgrade_specfuse
---

# Provision labels from init and upgrade, without letting them fail

**Objective.** Call `provision_labels` from `scaffold.init()` and
`scaffold.upgrade_specfuse()`, guarantee neither can fail because provisioning
did, and ship the `SPECFUSE_NO_LABELS` opt-out.

**Context.** Correlation ID `FEAT-2026-0071/T03`. Depends on `T02`, which supplies
a `provision_labels` that already returns rather than raises on every degradation
path it knows about. This WU adds the belt to that braces: even an unexpected
exception must not escape into the caller.

**Why the opt-out is an environment variable and not a CLI flag.** The
`specfuse init` and `specfuse upgrade` commands live in the **umbrella**
repository's `specfuse/cli.py`, which calls into this package's `scaffold` module.
Adding a flag would need a coordinated umbrella release; adding provisioning
inside these two functions needs none, because the umbrella already calls both.
So the opt-out is `SPECFUSE_NO_LABELS` in the environment plus a keyword argument
for programmatic callers. A future umbrella change can add `--no-labels` that
reads the same variable. This is recorded in `PLAN.md`'s scope boundary.

**Preserve the existing contract.** These two functions return a sorted list of
`.specfuse/` relpaths written. Provisioning writes no files, so **that return
value must not change** — every existing caller and test depends on it. Report
provisioning outcomes some other way (stderr, or a separate accessor); do not
append label names to the returned path list.

**Flag-scope table** — the `SPECFUSE_NO_LABELS` opt-out.

| Code path | Gated by flag? | Why |
|---|---|---|
| `scaffold.init()` label provisioning | yes | The flag's purpose: a caller who wants the pre-0071 pure-filesystem init |
| `scaffold.upgrade_specfuse()` label provisioning | yes | Same, for upgrade — the path the roadmap goal names |
| `scaffold.init()` file writing | no | Provisioning is additive; the flag must not change which files are written |
| `scaffold.upgrade_specfuse()` file writing, pruning, manifest | no | Same — the flag turns off labels, not the upgrade |
| `labels.provision_labels()` called directly | no | The flag gates the scaffold's *call sites*, not the function; a direct caller asked for it explicitly |
| `escalation.emit_escalation()` | no | Different feature, different surface; it consumes labels, it does not create them |

**Headline claim this table must support:** the opt-out turns off label creation
and changes nothing else about init or upgrade.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_scaffold_label_provisioning.py::TestScaffoldLabelProvisioning::test_upgrade_survives_provisioning_raising`
   exists and **fails on HEAD before this WU runs** (the test file does not yet
   exist, which counts as red).
2. `scaffold.init()` calls `provision_labels` on a normal run.
3. `scaffold.upgrade_specfuse()` calls `provision_labels` on a normal run.
4. When `provision_labels` raises an arbitrary exception, `scaffold.init()` still
   completes and returns its normal path list — the exception does not escape.
5. When `provision_labels` raises an arbitrary exception,
   `scaffold.upgrade_specfuse()` still completes and returns its normal path list.
6. With `SPECFUSE_NO_LABELS` set to a truthy value in the environment, neither
   function calls `provision_labels`.
7. With `SPECFUSE_NO_LABELS` set, both functions still write exactly the same
   files they wrote before this WU — asserted against the returned path list.
8. The list returned by `init()` and by `upgrade_specfuse()` contains no label
   names and is unchanged in shape from before this WU.
9. Every existing test in `tests/test_scaffold_init.py`,
   `tests/test_scaffold_upgrade.py`, and `tests/test_init_integration.py` passes
   unchanged — provisioning must not perturb them. Those suites do not stub `gh`,
   so provisioning must degrade silently in their environment rather than failing
   or emitting noise that breaks an assertion.
10. `python3 -m pytest tests/test_scaffold_label_provisioning.py -q` exits zero
    after this WU's edits (the same file named in criterion 1).
11. `python3 -m pytest tests/test_scaffold_init.py tests/test_scaffold_upgrade.py tests/test_init_integration.py -q`
    exits zero.

**Do not touch.** `specfuse/loop/labels.py` — T01 and T02 own it; this WU calls
it. `specfuse/loop/escalation.py`. The file-writing, pruning, and manifest logic
in `scaffold.py` — this WU adds a call and a guard, and changes nothing about what
files an upgrade produces. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set: `tests`, `lint`, `security`, `coverage`
(≥90%), `leak-scan`. Plus the scoped red/green run in criteria 1 and 10, and
criterion 11's regression run over the three existing scaffold suites — those are
the ones most likely to break, because they exercise `init` and `upgrade` in an
environment where `gh` may be present, absent, or unauthenticated.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
the existing scaffold suites cannot pass without stubbing `gh` inside them, which
would mean provisioning is not degrading as silently as T02 claims — report that
rather than editing those suites to accommodate it; or preserving the return-value
contract in criterion 8 conflicts with reporting provisioning outcomes. If
`scaffold.py` is absent from the files you edited, emit `status: blocked` — do not
claim complete.
