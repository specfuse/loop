---
id: FEAT-2026-0002/T04
type: implementation
effort: medium
status: pending
attempts: 0
---

# Cover _miniyaml.py error arms

**Objective.** Raise `.specfuse/scripts/_miniyaml.py` per-file coverage
from 87% to ≥ 90% by adding error-arm fixtures for the parser's
escape-handling and indent-error branches. Tests only; no production
code changes.

**Context.** This is `FEAT-2026-0002/T04`. Measured uncovered lines
(via `coverage report -m --include=.specfuse/scripts/_miniyaml.py`):

- `123, 126` — top-level / mapping indent error arms.
- `211, 241-247` — sequence-parser indent / continuation arms.
- `276, 305, 327` — scattered scalar / list arms.
- `391-393, 395-400, 402-404` — flow-list double-quoted-string escape
  handling (`_parse_flow_list_items`, around lines 385-419 of the
  source).
- `414, 418` — flow-list unterminated-string and empty-item errors.
- `432, 436, 438, 443, 445` — `_decode_double_quoted` escape decode
  (`\\` and `\"`) plus unsupported-escape, dangling-backslash, and
  unescaped-quote-inside-string error arms.

Existing test file `tests/test_miniyaml_negative.py` is the right home
for the new error fixtures — extend it. `tests/test_miniyaml_equivalence.py`
already covers many positive cases; do not duplicate them.

Reference the binding rules under `.specfuse/rules/`. Edit files only.

**Acceptance criteria.**

1. `tests/test_miniyaml_negative.py` is extended (existing file edit)
   with at least one new test method per cluster above. Cluster-to-
   method mapping is at the author's discretion as long as every
   uncovered line is exercised by at least one fixture.
2. Each new error fixture asserts that `_miniyaml.parse(...)` raises
   `MiniYAMLError` with a message naming the offending construct (escape
   char, unterminated string, indent column, etc.) and the line number
   (`lineno`) where it occurred.
3. Positive-path coverage of the escape decode: at least one test
   asserts `_miniyaml.parse('key: "a\\\\b"')` round-trips to the string
   `a\b` (exercises line 436's `out.append("\\")` arm), and at least
   one test asserts `_miniyaml.parse('key: "a\\"b"')` round-trips to
   the string `a"b` (exercises line 438's `out.append('"')` arm).
4. Flow-list escape path: at least one test asserts
   `_miniyaml.parse('xs: ["a\\\\b", "c\\"d"]')` yields the list
   `["a\\b", 'c"d']` (exercises the in-string + escape arms at
   389-404).
5. **Per-file coverage AC.** `coverage run --source=.specfuse/scripts
   -m unittest discover -s tests && coverage report
   --include=.specfuse/scripts/_miniyaml.py --fail-under=90` exits 0.
6. **Existence check** (per LEARNINGS `[FEAT-2026-0007/G1-LESSONS]`):
   `python3 -c "import tests.test_miniyaml_negative"` succeeds AND
   `grep -c "def test_" tests/test_miniyaml_negative.py` returns a
   count strictly greater than the count present before this WU
   (record the delta in your RESULT block notes).

**Do not touch.** Exactly 1 file changes (edit only):
`tests/test_miniyaml_negative.py`. No edits to:
`.specfuse/scripts/_miniyaml.py` (production code stays untouched),
`tests/test_miniyaml_equivalence.py` (positive-equivalence cases are
its concern, not error arms), `.specfuse/scripts/loop.py`,
`.specfuse/scripts/lint_plan.py` (T03 owns it),
`.specfuse/scripts/validate-event.py` (T02 owns it), `.specfuse/rules/`,
`.specfuse/verification.yml`, secrets, `.git/`.
See `.specfuse/rules/never-touch.md`.

If a test reveals a real bug in `_miniyaml.py` that cannot be
unit-tested without a fix, **emit `status: blocked`** with the bug
evidence rather than touching production code in this WU.

**Verification.** The `code` gate set in `.specfuse/verification.yml`,
PLUS the per-file coverage AC 5, PLUS the existence check AC 6. Declare
`files_changed: [tests/test_miniyaml_negative.py]` in the RESULT block.

**Escalation triggers.**

1. **Completeness.** If `tests/test_miniyaml_negative.py` shows no new
   test methods compared to HEAD-before, emit `status: blocked`.
2. **Per-file floor not met.** If `coverage report
   --include=.specfuse/scripts/_miniyaml.py --fail-under=90` exits
   non-zero, emit `status: blocked` naming the lines still uncovered.
3. **Spec ambiguity in unsupported-escape contract.** If the question
   "is `\\n` newline-decoded or rejected?" cannot be answered from
   reading `_miniyaml.py` alone, emit `status: blocked` — do not
   invent the contract. The existing code's behavior IS the contract;
   match it in the test, do not change it.
