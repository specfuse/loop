---
id: FEAT-2026-0224/T05
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
produces:
  - tests/test_lint_roadmap.py
  - tests/test_layout_end_to_end.py
  - specfuse/loop/lint_roadmap.py
model: sonnet
effort: medium
gate_set: code
---

# T05 — `lint_roadmap` checks a decision link's fragment, anchor and location

**Objective.** Oracle clause 3 goes green: a fragment link to a decision record is
checked as file + anchor, and, when `decisions:` is declared, must point under
`decisions.location`.

**Context.** In `_check_blocked_by` (`specfuse/loop/lint_roadmap.py:346`), for each
link that is neither a FEAT ref (`_REF_RE`) nor an http(s) URL:

1. `layout.split_link(href)` (T03) → path + fragment. File check on the path only.
   **Applies with or without a layout** (PLAN decision 5).
2. If the file exists and ends `.md` and a fragment is present: the fragment must
   equal an explicit `<a id="…">` / `<a name="…">` value or the GitHub heading slug
   of a heading in that file, exact match (PLAN decision 6). Otherwise ERROR:
   `"{id}'s Blocked-by link '{href}' points at '{path}', which has no anchor '{frag}'"`.
   Non-`.md` targets (e.g. `.yaml`): file check only.
3. **Only when `layout.yml` declares a `decisions:` block** (PLAN decision 4): the
   resolved path must be under the resolved `decisions.location`, else ERROR naming
   both. Scope unit (state it in the test docstring): one Blocked-by link that is not
   a FEAT ref and not a URL.

`_lint_roadmap_impl` appends `layout.validate(repo_root)` findings. Add a general
anchor reader beside `_find_anchors` (which only knows `feat-NNNN-NNNN`); do not
widen `_find_anchors`.

Tests go beside the existing Blocked-by cases in `tests/test_lint_roadmap.py`
(around line 93 and 207): fragment + existing anchor → no finding; fragment + missing
anchor → ERROR naming it; heading-slug anchor → no finding; `.yaml#id` with file
present → no finding; entries layout + link outside location → ERROR; **no layout +
link outside `docs/adr` → no finding** (decision 4's positive control); no layout +
`x.md#frag` with anchor → no finding (decision 5). Un-skip `LintChecksDecisionLinks`.

**Acceptance criteria.**

1. Each case above is a named test in `tests/test_lint_roadmap.py`; the missing-anchor,
   outside-location and fragment-with-anchor tests fail on HEAD and pass after.
2. `tests/test_layout_no_layout_goldens.py` passes **unchanged**: this unit does not
   edit that file (its fixtures and goldens are constants there), and
   `python3 .specfuse/scripts/roadmap_link_gate.py` exits 0 on this repository.
3. `tests/test_layout_end_to_end.py::LintChecksDecisionLinks` passes.

**Do not touch.** `tests/test_layout_no_layout_goldens.py` (T04's goldens). `layout.py` beyond calling it.

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_layout_no_layout_goldens -b` and
`python3 .specfuse/scripts/roadmap_link_gate.py`.

**Escalation triggers.** If a golden would have to change to make a test pass, stop —
that is a no-layout regression, not a golden to update.
