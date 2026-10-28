---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_layout_end_to_end -v -b"
cost_budget_usd: 26.00
---

# Gate 1 — a project can declare its decision records, and nothing changes without one

## Definition of done

**Stated as an outcome.** Driven through `python3 -m specfuse.loop.layout` and
`lint_roadmap` against fixture repositories:

1. With no `.specfuse/layout.yml`, `layout get` prints today's default for every
   `decisions.*` key (`adr`, `docs/adr`, `{path}`); the rendered blocker link, the
   `lint_roadmap` findings on fixture roadmaps and the rendered roadmap template are
   byte-identical to HEAD's.
2. With `decisions: {style: entries, location: docs/decisions, link:
   "{location}/decisions.md#{id}"}`, `layout get` returns those values and
   `layout link` renders `[D-0007: …](../docs/decisions/decisions.md#D-0007)` from
   `.specfuse/`.
3. `lint_roadmap` accepts that Blocked-by link when `docs/decisions/decisions.md`
   carries the anchor, reports an ERROR naming the anchor when it does not, and an
   ERROR when a decision link's target is outside `decisions.location`.
4. A layout with an absolute path, `..`, a Windows drive or backslash form, or a
   symlink escaping the repository is an ERROR; a `paths:` block is a WARN naming the
   authoring follow-up.
5. With the entries style, the rendered roadmap template's Blocked-by example uses an
   entries link, and that example passes `lint_roadmap`.

The `feature_oracle` proves 1–5 end to end. It is red on the current tree (the module
does not exist); `FEAT-2026-0224/T01` is the walking skeleton that creates it and
turns clause 1's `get` half and clause 2's `get` half green, with every other clause
`unittest.skip` naming its owner (T02, T03, T04, T05, T07). A skip surviving to the
close is a hollow oracle.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Goldens before consumers.** T04 records `lint_roadmap` findings on HEAD's
  behaviour; T05 may not start until T04 is `done` (graph edge). A golden regenerated
  inside T05 proves nothing.
- **From source, with a positive control** (`[FEAT-2026-0056/G1-CLOSE-INTERMEDIATE]`).
  Every criterion invokes `python3 -m specfuse.loop.layout`, never an installed
  console script; every "no findings" assertion is paired with a fixture that fires.
- **Exemption scope** (`[FEAT-2026-0058/G1-CLOSE]`). The location check's scope unit
  is "a Blocked-by link that is not a FEAT ref and not an http(s) URL, only when
  `decisions:` is declared" — T05 states it as a criterion.
- **Expected `judge_editing` halt.** T01 edits `arm_eval.py`'s registry (PLAN
  decision 3).

## Reflection notes

<Written by the human at review time.>
