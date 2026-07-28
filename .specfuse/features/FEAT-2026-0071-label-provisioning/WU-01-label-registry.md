---
id: FEAT-2026-0071/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces:
  - specfuse/loop/labels.py
  - tests/test_label_registry.py
produces_driver_helper:
  - LABEL_REGISTRY
  - FEATURE_LABEL
---

# Declare every label specfuse reads in one registry

**Objective.** Ship `specfuse/loop/labels.py` carrying `LABEL_REGISTRY` — the
single declaration of every GitHub label this package reads, with name, colour,
description, and the consumer that reads it — plus the test that fails when the
registry and the escalation vocabulary drift apart.

**Context.** Correlation ID `FEAT-2026-0071/T01`. This is the data layer; T02
provisions from it and T03 wires provisioning into the scaffold.

**The seven entries and where each name comes from.**

- `specfuse:feature` — read by `gh_features.py` to discover loop-feature
  candidates. Today it is a hardcoded string literal at
  `specfuse/loop/gh_features.py:28`. Extract it to a module-level
  `FEATURE_LABEL` constant in `gh_features.py` and have both that call site and
  the registry use the constant, so the string exists once.
- `needs-human` — `escalation.NEEDS_HUMAN_LABEL`.
- `gate-review`, `blocked-wu`, `triage-question`, `drafting-needed`,
  `merge-approval` — the five members of `escalation.CATEGORY_LABELS`.

**Import the escalation names; do not retype them.** `escalation.py` already owns
that vocabulary. Two hand-kept lists of the same seven strings drift, and the
drift is silent — provisioning would create a label nothing queries, or miss one
the emitter needs. Criterion 6 is the guard: it recomputes the escalation label
set from `escalation.py` and asserts the registry covers it exactly.

**Colours and descriptions.** These labels already exist on this repository and
their current values are the intended ones — read them rather than inventing new:

| Label | Colour | Description |
|---|---|---|
| `needs-human` | `d93f0b` | The loop stopped and needs a human decision |
| `gate-review` | `fbca04` | A gate is at awaiting_review and needs review-and-arm |
| `blocked-wu` | `e99695` | A work unit stopped and needs an operator decision |
| `triage-question` | `c5def5` | An inbound issue needs categorising before it can be routed |
| `drafting-needed` | `bfd4f2` | A queued feature has no folder yet and needs /draft-feature |
| `merge-approval` | `0e8a16` | A pull request is green and waiting on a merge decision |
| `specfuse:feature` | `1d76db` | A roadmap-candidate feature request specfuse discovery reads |

Colours are six hex digits with no leading `#` — the form `gh label create
--color` accepts.

**Do not add `specfuse-monitor`.** `PLAN.md`'s scope boundary excludes it: its
only consumer is FEAT-2026-0040's harvester, which does not exist. A registry
entry for an unbuilt consumer is the `[FEAT-2026-0029/G1-CLOSE]` failure.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_label_registry.py::TestLabelRegistry::test_registry_covers_every_escalation_label`
   exists and **fails on HEAD before this WU runs** (the test file does not yet
   exist, which counts as red).
2. `specfuse/loop/gh_features.py` defines a module-level `FEATURE_LABEL`
   constant equal to `specfuse:feature`, and the `gh issue list` call at that
   module's runner uses the constant rather than a literal.
3. `specfuse/loop/labels.py` defines `LABEL_REGISTRY` as a sequence of exactly 7
   entries.
4. Every registry entry exposes a name, a colour, and a description, each a
   non-empty `str`.
5. Every registry entry's colour matches `^[0-9a-f]{6}$` — six lowercase hex
   digits, no leading `#`.
6. The set of registry entry names equals
   `{escalation.NEEDS_HUMAN_LABEL} | set(escalation.CATEGORY_LABELS) | {gh_features.FEATURE_LABEL}`
   — computed from those modules at test time, not restated as a literal in the
   test.
7. `specfuse-monitor` is **not** a registry entry name.
8. Registry entry names are unique — no duplicates.
9. `python3 -m pytest tests/test_label_registry.py -q` exits zero after this WU's
   edits (the same file named in criterion 1).
10. `python3 -c "from specfuse.loop.labels import LABEL_REGISTRY; from specfuse.loop.gh_features import FEATURE_LABEL"`
    exits zero.

**Do not touch.** `specfuse/loop/escalation.py` — this WU imports from it and must
not edit it. `specfuse/loop/scaffold.py` — T03 owns that wiring. Any behaviour of
`gh_features.py` beyond extracting the literal to a constant. Generated
directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Plus the scoped red/green run
in criteria 1 and 9, and the symbol-existence import in criterion 10.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`escalation.py` does not export `NEEDS_HUMAN_LABEL` or `CATEGORY_LABELS` under
those names; extracting `FEATURE_LABEL` would change `gh_features.py`'s behaviour
rather than only its spelling; or the seven names computed in criterion 6 do not
number seven. If `specfuse/loop/labels.py` is absent from the files you edited,
emit `status: blocked` — do not claim complete.
