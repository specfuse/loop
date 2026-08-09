---
id: FEAT-2026-0045/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.50
produces:
  - specfuse/loop/triage.py
  - specfuse/loop/labels.py
  - specfuse/monitor/issues.py
  - tests/test_triage.py
oracle_env: macos_local
---

# The triage mechanism: vocabulary, marker, and the untriaged scan

**Objective.** Ship `specfuse/loop/triage.py` — the deterministic half of issue triage:
the closed category vocabulary, the category→route map, the triage marker's render/parse
pair, harvester-issue recognition, and the scan that answers "which open issues are
untriaged" — plus the four new label registrations.

**Context.** Correlation ID `FEAT-2026-0045/T01`. Read `PLAN.md` first. It records three
decisions that are **settled and must not be reopened**: the marker is authoritative and
the label is a projection of it; the module owns mechanism while the agent owns
judgment; and the `auto` dial is a function argument, not a config file.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `verification-discipline.md`. Run gates
per `.specfuse/skills/verification/SKILL.md`.

**Follow the existing convention; do not invent a second one.** PLAN.md's
existing-mechanism search found five independent `gh issue list` call sites, every one of
which takes an **injectable runner** and filters **client-side**. The closest sibling to
what this WU builds is:

```
specfuse/monitor/issues.py:141   _list_findings(runner, repo, limit)   the list shape
specfuse/monitor/issues.py:161   find_finding_issue(...)               client-side re-check
specfuse/monitor/autofix_state.py:85  has_prior_attempt(...)           marker-over-label precedence
```

Read `has_prior_attempt`'s docstring before writing the scan. It states the exact rule
this WU needs: re-check the marker client-side rather than trusting the listing, so a
too-broad or coincidental match that does not carry the marker is never treated as a hit.

**What to build.**

1. **Vocabulary** — `CATEGORIES = ("bug", "feature", "duplicate", "question", "wontfix")`
   and `CONFIDENCES = ("high", "low")`, both closed tuples. No sixth category, no third
   confidence. `OUTCOMES` in `monitor/autofix_invoke.py` is the shape to copy: a closed
   tuple with a docstring saying it is closed.

2. **Routes** — a mapping from every category to its route string:
   `bug` → `fix-bug`, `feature` → `roadmap-add`, `duplicate` → `link-and-close`,
   `question` → `needs-human`, `wontfix` → `close`. Expose `route_for(category)`. It must
   be **total over `CATEGORIES`** and raise on anything else.

3. **Labels** — the category→label projection:
   `bug` → `triage:bug`, `feature` → `triage:feature`, `duplicate` → `triage:duplicate`,
   `wontfix` → `triage:wontfix`, and `question` → the **existing** `triage-question`
   (already in the registry, consumer `escalation.py`). Do not mint a second label for
   the question route, and do not reuse GitHub's conventional `wontfix` — PLAN.md's
   scope boundary explains why.

4. **Marker** — `<!-- specfuse:triage category={category} confidence={confidence} -->`,
   with `render_marker(category, confidence)` and `parse_marker(body)` returning the
   parsed pair or `None`. Mirror `issues.py:60`'s `_MARKER_TEMPLATE` convention exactly;
   this is the same idea applied to a different lifecycle.

5. **Harvester recognition** — add a narrow public predicate
   `has_finding_marker(body)` to `specfuse/monitor/issues.py` and call it from
   `triage.py`. Do **not** re-type the marker literal in `triage.py`: two copies of one
   string is the drift this repository has been bitten by repeatedly, and `issues.py`
   owns that vocabulary. The predicate is a one-liner over the existing `_marker` helper.

6. **The scan** — `list_untriaged(runner, repo, limit)`. Lists open issues with
   `--json number,title,body,labels`, and returns those whose body carries **no** triage
   marker. The predicate is the marker's absence, evaluated client-side. An issue that
   carries a finding marker is still returned, but flagged as already-structured so the
   caller can skip re-categorising it — that is the row's "fingerprint-aware" clause, and
   it is a flag on the result, not an exclusion from it.

7. **Registry** — four new `LabelSpec` entries in `specfuse/loop/labels.py`. Import the
   names from `triage.py` rather than retyping them; the registry's own module docstring
   states this rule ("Names are imported from the modules that own the vocabulary … so
   the registry cannot drift from what those consumers actually query"). Pick colours
   distinct from the existing eight.

**Acceptance criteria.**

1. **Red first.** `tests/test_triage.py::test_untriaged_excludes_marked_issue` exists and
   **fails on HEAD before any source edit** — the module does not exist yet, so this is
   an import error, and that counts. Record the failing output.
2. `python3 -c "from specfuse.loop.triage import CATEGORIES, CONFIDENCES, route_for, render_marker, parse_marker, list_untriaged"`
   exits 0.
3. `python3 -c "from specfuse.monitor.issues import has_finding_marker"` exits 0.
4. `test_untriaged_excludes_marked_issue` **passes** after the edits.
5. A test asserts `route_for` is total over `CATEGORIES` — every member returns a route,
   and a non-member raises. Not "spot-check two categories."
6. A test asserts `parse_marker(render_marker(c, k)) == (c, k)` for every
   `(category, confidence)` pair in the product of the two closed tuples.
7. A test asserts an issue whose body carries a **finding** marker is returned by
   `list_untriaged` **and** flagged as already-structured — not silently dropped.
8. A test asserts every category's label appears in `LABEL_REGISTRY`, resolved through
   the projection map rather than by retyping the label strings in the test.
9. Every test injects a fake runner. `grep -rn "subprocess" tests/test_triage.py` returns
   nothing, and no test in this WU invokes `gh`.
10. The `code` gate set in `.specfuse/verification.yml` passes: tests, lint, security,
    coverage ≥ 90%, leak-scan, event-type-gate, roadmap-link-gate, arm-sweep-gate.

**Do not touch.** `.git/`, secrets, the vendored schemas under
`specfuse/loop/data/schemas/`, any other work unit's files in this gate (T02 owns the
write path; T03 owns the skill). Do not write `apply_triage` — that is T02, and building
it here makes T02's red test unsatisfiable. The driver owns all git operations. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, run per
`.specfuse/skills/verification/SKILL.md`. Plus the two symbol-existence checks in AC2 and
AC3 — the code gate passes when no test asserts a symbol exists and cannot detect its
absence, which is exactly the hole those checks fill.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:

- `specfuse/loop/triage.py` or `specfuse/monitor/issues.has_finding_marker` is absent from
  the files you edited when you believe you are done — do not claim complete.
- Adding `has_finding_marker` to `issues.py` would require changing any existing public
  behaviour in that module. It must be purely additive; if it cannot be, stop and say so.
- The coverage gate cannot reach 90% without a test that calls live `gh`. It should not
  come to this — every path here is runner-injectable — but if it does, that is a design
  problem to escalate, not to solve by weakening the gate.
- The category vocabulary appears to need a sixth member. That is a scope change and the
  operator's call.

Blocked is a respectable outcome — `result-contract.md` rule 4.
