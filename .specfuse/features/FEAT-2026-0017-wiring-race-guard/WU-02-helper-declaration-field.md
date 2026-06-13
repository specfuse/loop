---
id: FEAT-2026-0017/T02
type: implementation
model: claude-sonnet-4-6
effort: low
status: pending
attempts: 0
planned_cost_usd: 0.50
produces_driver_helper:
  - produces_driver_helper
---

# Add `produces_driver_helper` WU frontmatter field + lint warning

**Objective.** Add an optional `produces_driver_helper: <symbol>` (or
list of symbols) WU frontmatter field. Lint warns when an
`implementation` WU's body mentions driver-wiring keywords without
declaring the symbol(s) the WU produces. Closes the spec-time half of
the wiring-race surface: T01 catches at run time; this catches at
WU author time.

**Context.** This is `FEAT-2026-0017/T02`. Independent of T01 — both
WUs can dispatch in parallel.

FEAT-2026-0015/T06's hollow-pass surface was visible at WU author time
in retrospect: the WU body described `fire_terminal_flips` being wired
into the squash path, but no field linked the helper symbol to the WU
header. A reviewer scanning the WU couldn't tell at a glance what
symbol the WU was meant to PRODUCE in the driver. This WU adds the
declaration field + lint that fires when an `implementation` WU
mentions wiring without declaring.

Existing `WorkUnit` dataclass: read `.specfuse/scripts/loop.py` at
`load_wu` to see the frontmatter parsing pattern.

Reference binding rules under `.specfuse/rules/`. The driver owns
all git; edit files only.

**Acceptance criteria.**

1. `WorkUnit` dataclass gains a field
   `produces_driver_helper: list[str] = field(default_factory=list)`.
   `load_wu` reads `fm.get("produces_driver_helper")`, normalizes:
   - `None` / missing → `[]`.
   - Single string → `[string]`.
   - List of strings → as-is.
   - Other types → raise ValueError naming the field.
2. `lint_plan.py` gains a detector module/function
   `detect_driver_wiring(wu_body: str) -> list[str]` that returns
   matched wiring-keyword strings. Initial regex catalog:
   - `\bloop\.py\b`
   - `\bdriver-side\b`
   - `\bMODEL_BY_TYPE\b`, `\bEFFORT_BY_TYPE\b`, `\bGATES_FOR_TYPE\b`
   - `\bCLOSING_ASSERTIONS_BY_TYPE\b`, `\bPOST_PASS_INVARIANTS_BY_TYPE\b`
   - `\bfire_terminal_flips\b`, `\bassert_terminal_flips_fired\b`
     (FEAT-2026-0017 surface symbols)
   - `\bsquash_commit\b`, `\breset_preserving_events\b`
   - `\bcommit_bookkeeping\b`
   Each pattern compiled with `re.IGNORECASE`.
3. `lint_plan.py` per-WU pass: if WU `type == "implementation"` AND
   `detect_driver_wiring(body)` returns ≥1 match AND `produces_driver_helper`
   frontmatter is empty/missing, emit WARN:
   `WARN: <wu_file>: implementation WU mentions driver wiring ({matched_keywords}) but `produces_driver_helper` frontmatter is empty. Declare the symbol(s) this WU produces in the driver. See authoring-work-units §9 + FEAT-2026-0017.`
   Lint exits 0 (warning only).
4. `WU.template.md` frontmatter notes section gains a paragraph
   documenting `produces_driver_helper`: optional, list of strings,
   recommended for `implementation` WUs touching `loop.py` /
   `lint_plan.py`.
5. New tests in `tests/test_lint_produces_driver_helper.py`:
   - `test_implementation_wu_with_wiring_mention_and_declaration_passes_silently`:
     WU declares `produces_driver_helper: ["foo"]` and body mentions
     `loop.py`. No WARN.
   - `test_implementation_wu_with_wiring_mention_no_declaration_warns`:
     WU body mentions `MODEL_BY_TYPE` but declaration empty. WARN
     emitted with the matched keyword.
   - `test_close_wu_with_wiring_mention_no_declaration_no_warn`:
     non-implementation type (e.g. `close`) is exempt.
   - `test_empty_body_no_warn`: no wiring mentions → no WARN
     regardless of declaration.
   - `test_load_wu_accepts_string_or_list_produces_driver_helper`:
     `load_wu` normalizes both shapes to list.
6. **Existence check** before declaring complete:
   `python3 -c "from lint_plan import detect_driver_wiring; from loop import WorkUnit; wu_kwargs = dict(wu_id='X/T01', file='/tmp/x', depends_on=[], type='implementation', model='sonnet', status='pending', attempts=0, title='t', body='b'); wu = WorkUnit(**wu_kwargs); assert wu.produces_driver_helper == []"`
   exits 0.

**Do not touch.** Exactly 3 files change:
- `.specfuse/scripts/lint_plan.py` (additions: detector + per-WU
  check + import for `_implementation_wu_mentions_wiring`).
- `.specfuse/scripts/loop.py` (additions: 1 dataclass field +
  load_wu normalization; this is small surgical add, NOT a
  refactor — T01 owns the other loop.py additions).
- `tests/test_lint_produces_driver_helper.py` (new file).

Plus 1 file:
- `.specfuse/templates/WU.template.md` (frontmatter-notes addition
  only — no body changes).

No edits to: skill files, production WUs, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** `code` gate set + AC6 existence check. T01 and T02
may both edit `loop.py`; if a merge conflict surfaces during squash,
emit `status: blocked` (T01 dispatch likely landed first; rebase the
1-field add manually post-hoc).

**Escalation triggers.**

1. **Existing-WU false positives.** If running lint against
   `FEAT-2026-0015/T01` (which mentions `MODEL_BY_TYPE`) WITHOUT a
   `produces_driver_helper` declaration produces a WARN that the
   operator considers backfill-required, list it in the RESULT block.
   Do NOT backfill existing WUs in this dispatch — that's a separate
   hygiene WU's job.
2. **Helper-duplication.** Per authoring-work-units §10: before
   adding the regex catalog, run `grep -rn "loop\.py\b" .specfuse/`
   to see how prevalent the keyword is across the repo's own docs.
   The regex must not match documentation files (it operates on WU
   body text only, per AC3 wiring).
3. **Loop.py concurrent edit.** T01 also edits `loop.py`. If both
   WUs target the same file region (around `WorkUnit` dataclass or
   `load_wu`), and a sequential dispatch ordering can't be inferred
   from `depends_on`, the driver may pick one before the other.
   Either WU should remain idempotent on the other's prior edits.
   If your edit would clobber T01's `POST_PASS_INVARIANTS_BY_TYPE`
   constant or `assert_terminal_flips_fired` function (both are
   T01's territory), emit `status: blocked`.
