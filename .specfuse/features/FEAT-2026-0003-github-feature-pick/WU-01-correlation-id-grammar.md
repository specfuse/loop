---
id: FEAT-2026-0003/T01
type: implementation
model: claude-sonnet-4-6
status: done
attempts: 1
cost_usd: 0.54722
input_tokens: 14
output_tokens: 12615
---

# Admit orchestrated INIT-…/FNN[/TNN] correlation IDs in the rule and linter

**Objective.** Extend the loop's correlation-ID grammar so it admits
orchestrator-dispatched IDs (`INIT-YYYY-NNNN/FNN` and their task-level forms)
alongside today's component-local `FEAT-…` IDs — in the rule document and in the
linter — with tests proving both admission and rejection.

**Context.** This is `FEAT-2026-0003/T01`, gate 1 of the GitHub feature-pick
build. An orchestrator decomposes an *initiative* into *features* and dispatches
each to a component repo, where it becomes a loop feature; only the ID namespace
differs. The naming contract is in
[`docs/handoff-github-feature-pick.md`](../../../docs/handoff-github-feature-pick.md)
§2 — read it. The two grammars:

- Component-local (today, unchanged): `FEAT-YYYY-NNNN`, task-level
  `FEAT-YYYY-NNNN/(TNN[H…] | G<n>-(RETRO|LESSONS|DOCS|PLAN))`.
- Orchestrated (new): feature-level `INIT-YYYY-NNNN/FNN` (e.g.
  `example-feature`); task-level `INIT-YYYY-NNNN/FNN/(TNN[H…] |
  G<n>-(RETRO|LESSONS|DOCS|PLAN))` (e.g. `example-feature/T01`,
  `example-feature/G1-RETRO`). Origin is read from the ID root: `INIT-…` =
  orchestrated, `FEAT-…` = component-local.

Files to edit: `.specfuse/rules/correlation-ids.md` (the rule),
`.specfuse/scripts/lint_plan.py` (`CORRELATION_ID_RE`), and
`tests/test_lint_correlation_id.py` (extend the existing direct-regex tests —
see `TestHygieneIdAdmitted` for the shape). Reference the binding rules under
`.specfuse/rules/` rather than restating them; honor `result-contract.md`,
`never-touch.md`, `security-boundaries.md`.

**Acceptance criteria.**
1. `lint_plan.CORRELATION_ID_RE` matches `example-feature` (orchestrated
   feature-level).
2. It matches each of `example-feature/T01`, `example-feature/T02H`,
   `example-feature/T02H1`, and `example-feature/G1-RETRO` (orchestrated
   task-level: substantive, hygiene, hygiene-ordinal, closing).
3. It still matches every existing `FEAT-…` shape — `FEAT-2026-0042`,
   `FEAT-2026-0042/T07`, `FEAT-2026-0042/T02H`, `FEAT-2026-0042/G1-RETRO`
   (regression; the worked-example fixture must still lint clean).
4. It rejects malformed orchestrated IDs: `example-init/F6` (single-digit
   feature ordinal), `example-feature/T1` (single-digit task ordinal),
   `example-init/f06` (lowercase), and `example-init` (orchestrated root
   with no `/FNN` feature segment — a bare initiative is not a loop feature ID).
5. `.specfuse/rules/correlation-ids.md` documents both grammars, the
   origin-from-ID-root rule, and the updated combined regex, keeping the
   existing `FEAT-…` content intact.
6. New cases in `tests/test_lint_correlation_id.py` assert criteria 1–4 via
   direct `CORRELATION_ID_RE.match` calls (mirroring `TestHygieneIdAdmitted`).

**Do not touch.** `loop.py`, `_miniyaml.py`, the `FEAT-2026-0001-health-endpoint`
fixture folder, any other feature folder, generated directories, secrets,
`.git/`. The driver owns all git — edit files only. This WU produces edits to
exactly three files: `.specfuse/scripts/lint_plan.py`,
`.specfuse/rules/correlation-ids.md`, `tests/test_lint_correlation_id.py`.

**Verification.** The `code` gates in `.specfuse/verification.yml`: the full
test suite (`python3 -m unittest discover -s tests -v`), `ruff` lint, `bandit`
security scan, and coverage ≥ the floor. Run them yourself in order before
reporting.

**Escalation triggers.** If admitting the INIT grammar would require changing
how `lint_plan.py` splits feature-vs-task IDs anywhere beyond the
`CORRELATION_ID_RE` pattern in a way that breaks `FEAT-…` handling, stop and emit
`status: blocked` naming the conflict. If the handoff's grammar is ambiguous
about a shape not covered by the criteria above, block and name the gap rather
than inventing a rule.
</content>
