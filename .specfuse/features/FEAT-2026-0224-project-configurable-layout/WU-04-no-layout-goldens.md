---
id: FEAT-2026-0224/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.00
produces:
  - tests/test_layout_no_layout_goldens.py
  - tests/fixtures/layout_goldens/**
  - tests/test_layout_end_to_end.py
model: sonnet
effort: medium
gate_set: code
---

# T04 — no-layout goldens, recorded before any consumer changes

**Objective.** Oracle clause 1 (except the template, which T07 adds) is proven by
committed goldens on deterministic surfaces only, recorded against HEAD's
`lint_roadmap` before T05 edits it.

**Context.** `tests/fixtures/layout_goldens/` holds: three fixture repos (each a
`.specfuse/roadmap.md` + `roadmap-archive.md` + any linked files, no `layout.yml`) —
one clean, one with a blocked row whose `docs/adr/…` link resolves, one with a
blocked row whose link does not resolve and an orphan section (so ERROR and WARN
findings both appear); and the expected outputs as plain text files.
**No fixture link carries a `#fragment`** (PLAN decision 5).

`tests/test_layout_no_layout_goldens.py` asserts, with no `layout.yml`:
- `python3 -m specfuse.loop.layout get <key>` stdout for every key equals the golden.
- `python3 -m specfuse.loop.layout link` for the `block-feature` example equals the
  golden.
- `lint_roadmap(<fixture>)` findings, rendered one per line as
  `severity file:line message`, equal the golden for each fixture.

Goldens are generated once in this unit by running the code on HEAD and committing
the output; the test never regenerates them (no `--update` flag in the test path).
Un-skip `NoLayoutGoldens` in the oracle module (runs the same assertions on the
non-clean fixture).

**Acceptance criteria.**

1. `tests/test_layout_no_layout_goldens.py` passes on this unit's tree and its
   `lint_roadmap` cases were generated before any edit to `lint_roadmap.py` in this
   feature (`git log --oneline -- specfuse/loop/lint_roadmap.py` shows no
   FEAT-2026-0224 commit at this unit's HEAD), and
   `tests/test_layout_end_to_end.py::NoLayoutGoldens` passes.
2. Positive control: the dangling-link fixture's golden contains at least one ERROR
   and one WARN line — a golden of `[]` everywhere would prove nothing — and `grep -rn "#" tests/fixtures/layout_goldens/*/.specfuse/roadmap.md | grep -E "\]\([^)]*\.md#"`
   returns nothing.

**Red-test exemption (§12).** Goldens pin HEAD's behaviour, so they pass on HEAD by
design; the red-then-green proof for this unit is T05's criterion 2 (goldens pass
unchanged after the consumer edit).

**Do not touch.** `specfuse/` (this unit adds tests and fixtures only).

**Verification.** The narrow tier for `implementation`.

**Escalation triggers.** If `lint_roadmap` output is non-deterministic across runs
(ordering, absolute paths in messages), stop: normalise in the test only by
escalating — the finding text is user-visible.
