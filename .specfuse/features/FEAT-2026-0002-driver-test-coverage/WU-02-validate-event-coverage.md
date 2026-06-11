---
id: FEAT-2026-0002/T02
type: implementation
effort: medium
status: done
attempts: 1
duration_seconds: 853.775
cost_usd: 2.138758
input_tokens: 682
output_tokens: 40865
---

# Cover validate-event.py

**Objective.** Raise `.specfuse/scripts/validate-event.py` per-file
coverage from 0% to ≥ 90% by adding `tests/test_validate_event.py`.
No production code changes; tests only.

**Context.** This is `FEAT-2026-0002/T02`. `validate-event.py` has no
existing test file. Read the script first to enumerate (a) the schema
it validates (event_type + payload shape per `events.jsonl`), (b) its
exit codes, (c) its error messages. Drive every documented branch from
a test.

**Dependency: `jsonschema`.** `validate-event.py` imports `jsonschema`
(`Draft202012Validator`). It is now declared in `pyproject.toml`'s
`[project.optional-dependencies].dev` (added alongside this WU's
re-arming). The CI environment installs it via `pip install -e '.[dev]'`
in `.github/workflows/ci.yml`. Local: `pip install jsonschema>=4.0` if
absent.

**Schema-source contract.** The script's schema defines `source` as
`^(human|specs|pm|qa|config-steward|merge-watcher|component:...)$` —
the Specfuse Orchestrator's event protocol. Loop-driver-emitted events
use `source: "driver"` and are intentionally NOT valid under this
schema; they follow a different contract owned by `loop.py`. Your tests
must respect this boundary (see AC 4).

LEARNINGS [FEAT-2026-0003/G2-LESSONS] (two-case linter pattern) and
[FEAT-2026-0005/G1-LESSONS] (regression case on existing valid fixture)
apply: every "rejects malformed input" test must be paired with an
"accepts valid input" test, and at least one regression test must
exercise a real event payload from an existing `events.jsonl` in the
repo (e.g. one drawn from `.specfuse/features/FEAT-2026-0008-driver-completeness-guard/events.jsonl`).

Reference the binding rules under `.specfuse/rules/`. Edit files only.

**Acceptance criteria.**

1. New file `tests/test_validate_event.py` exists.
2. Schema-valid input passes: at least one test class
   (`TestValidateEventValid`) runs the script against a payload that
   represents every event_type the script accepts; the script exits 0
   for each.
3. Schema-invalid input is rejected with a non-zero exit code: at least
   one test class (`TestValidateEventInvalid`) covers (a) missing
   required key per event_type, (b) wrong type for a known key, (c)
   unknown event_type, (d) malformed JSON line. Each rejection asserts
   the exact exit code and that the error message names the offending
   key or condition.
4. Schema-rejection regression on a real driver-emitted event: at least
   one test reads a real event line from
   `.specfuse/features/FEAT-2026-0008-driver-completeness-guard/events.jsonl`
   and asserts `validate-event.py` REJECTS it (exit != 0) because those
   events use `source: "driver"` which is intentionally NOT in the
   schema's `source` enum (`^(human|specs|pm|qa|config-steward|merge-watcher|component:...)$`).
   This pins the documented contract: driver-emitted events follow a
   different schema than the orchestrator/component-author event protocol
   the script validates. If the script's schema is later widened to admit
   `driver`, this test must be updated in the same change — that is the
   correct coupling.
5. **Per-file coverage AC.** `coverage run --source=.specfuse/scripts
   -m unittest discover -s tests && coverage report
   --include=.specfuse/scripts/validate-event.py --fail-under=90` exits 0.
6. **Existence check** (per LEARNINGS `[FEAT-2026-0007/G1-LESSONS]`):
   `python3 -c "from tests.test_validate_event import
   TestValidateEventValid, TestValidateEventInvalid"` succeeds.

**Do not touch.** Exactly 1 new file: `tests/test_validate_event.py`.
No edits to: `.specfuse/scripts/validate-event.py` (production code
stays untouched), `.specfuse/scripts/loop.py`, `.specfuse/rules/`,
`.specfuse/verification.yml`, `WU.template.md`, other test files
(T01/T03/T04 own theirs), the existing `events.jsonl` fixtures
(read-only), secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

If a test reveals a real bug in `validate-event.py` that cannot be
unit-tested without a fix, **emit `status: blocked`** with the bug
evidence rather than touching production code in this WU.

**Verification.** The `code` gate set in `.specfuse/verification.yml`,
PLUS the per-file coverage AC 5, PLUS the existence check AC 6. Declare
`files_changed: [tests/test_validate_event.py]` in the RESULT block.

**Escalation triggers.**

1. **Completeness.** If `tests/test_validate_event.py` is absent from
   the files you edited, emit `status: blocked`.
2. **Per-file floor not met.** If `coverage report
   --include=.specfuse/scripts/validate-event.py --fail-under=90` exits
   non-zero, emit `status: blocked` naming the lines still uncovered.
3. **Schema surface ambiguous.** If `validate-event.py`'s accepted
   event_type set or required-key contract is not statable from reading
   the script alone (no docstring, no schema constant), emit
   `status: blocked` — a test cannot be written against an undefined
   contract. Do not invent an event-type list.
