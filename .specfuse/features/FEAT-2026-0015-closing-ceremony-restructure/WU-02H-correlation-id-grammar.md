---
id: FEAT-2026-0015/T02H
type: implementation
model: claude-sonnet-4-6
effort: low
status: done
attempts: 2
planned_cost_usd: 0.50
duration_seconds: 383.343
cost_usd: 0.984542
input_tokens: 47
output_tokens: 13305
---

# Hygiene: extend correlation-ID grammar to include `CLOSE-INTERMEDIATE`

**Objective.** Update `CORRELATION_ID_RE` in `lint_plan.py` and the
matching documentation in `.specfuse/rules/correlation-ids.md` so
the new `close-intermediate` WU type (introduced by T01, accepted by
T02's closing-shape lint) carries its own valid correlation-ID
suffix: `G<n>-CLOSE-INTERMEDIATE`.

**Context.** This is `FEAT-2026-0015/T02H`. Hygiene WU per
authoring-work-units §7, inserted between T02 and T03 after T03's
agent surfaced the spec gap in T02. Evidence:

- T02 added `close-intermediate` to `VALID_TYPES` and the
  closing-shape lint logic but DID NOT update the regex
  `CORRELATION_ID_RE` (`lint_plan.py:62-64`). Current regex
  accepts `RETRO|LESSONS|DOCS|PLAN|CLOSE` as `G<n>-<NAME>`
  suffixes only. Agent confirmed:
  `CORRELATION_ID_RE.match('FEAT-2026-0000/G1-CLOSE-INTERMEDIATE')
  → False`.
- `.specfuse/rules/correlation-ids.md:26-29` documents the closing-
  suffix lexicon and mirrors the regex on line 61.
- T03's AC5 demands `lint_plan.py` accept the updated `PLAN.template.md`
  example without warnings. That template will use
  `G1-CLOSE-INTERMEDIATE` IDs; without this fix, T03 cannot pass.

Out of scope (per agent's audit, handled elsewhere):
- `gate-status/SKILL.md:81`, `feature-conversion/SKILL.md:90`
  legacy-closing-ID mentions → G1-DOCS (AC1 already scopes them).
- `correlation-ids.md` lines 28-29 + 153-155 prose mentions → THIS
  WU owns the rule-doc edits per its AC2 below.

Reference binding rules under `.specfuse/rules/`. The driver owns
all git; edit files only.

**Acceptance criteria.**

1. `lint_plan.py::CORRELATION_ID_RE` updated to accept
   `CLOSE-INTERMEDIATE` as a valid `G<n>-<NAME>` suffix. New regex:
   ```
   ^(FEAT-\d{4}-\d{4}(/(T\d{2}(H\d*)?|G\d+-(RETRO|LESSONS|DOCS|PLAN|CLOSE|CLOSE-INTERMEDIATE)))?|
   INIT-\d{4}-\d{4}/F\d{2}(/(T\d{2}(H\d*)?|G\d+-(RETRO|LESSONS|DOCS|PLAN|CLOSE|CLOSE-INTERMEDIATE)))?)$
   ```
   Note: `CLOSE-INTERMEDIATE` MUST appear AFTER `CLOSE` in the
   alternation OR be ordered with `CLOSE-INTERMEDIATE` first (longest
   alternative first) to avoid the regex matching `CLOSE` greedily
   and leaving `-INTERMEDIATE` orphan. Recommend
   `CLOSE-INTERMEDIATE|CLOSE` order (longest-first) per the Bash
   tool's documented `find -regex` warning pattern.
2. `.specfuse/rules/correlation-ids.md` updated to document the new
   suffix:
   - Line ~26-29 prose: extend "one of `RETRO`, `LESSONS`, `DOCS`,
     `PLAN`" to include the new closing taxonomy from
     FEAT-2026-0015. Specifically state: "two-WU intermediate close
     uses `CLOSE-INTERMEDIATE` and `PLAN`; one-WU terminal close
     uses `CLOSE`. Legacy four-WU sequence (`RETRO`, `LESSONS`,
     `DOCS`, `PLAN`) accepted by lint but warned."
   - Line ~61 regex example: update to match the new
     `CORRELATION_ID_RE`.
   - Lines ~126-128 prose about closing-sequence IDs: update to
     describe the two-WU intermediate pattern + extended one-WU
     terminal pattern alongside the legacy.
3. New unit tests in `tests/test_lint_correlation_id.py` (or a new
   `tests/test_lint_correlation_id_close_intermediate.py` if the
   first file exists and pollution is undesirable):
   - `test_correlation_id_re_accepts_g1_close_intermediate` —
     `CORRELATION_ID_RE.match('FEAT-2026-0042/G1-CLOSE-INTERMEDIATE')`
     truthy.
   - `test_correlation_id_re_accepts_g1_close_after_extension` —
     existing `FEAT-2026-0042/G1-CLOSE` still matches (no
     regression).
   - `test_correlation_id_re_accepts_init_g1_close_intermediate` —
     `INIT-2026-0001/F06/G1-CLOSE-INTERMEDIATE` truthy.
   - `test_correlation_id_re_rejects_unknown_suffix` —
     `FEAT-2026-0042/G1-CLOSE-FOO` falsy (defensive — confirms
     alternation didn't open a gap).
4. Symbol-existence check (per authoring-work-units §9):
   `python3 -c "from lint_plan import CORRELATION_ID_RE; assert CORRELATION_ID_RE.match('FEAT-2026-0042/G1-CLOSE-INTERMEDIATE')"`
   exits 0.

**Do not touch.** Exactly 2 files change:
- `.specfuse/scripts/lint_plan.py` (the regex line only — do NOT
  touch closing-shape logic, VALID_TYPES, or other constants; T02
  owns those).
- `.specfuse/rules/correlation-ids.md` (the prose + regex example
  on the lines named in AC2 only).

Plus 1 new test file:
- `tests/test_lint_correlation_id_close_intermediate.py` (new) OR
  appended block in `tests/test_lint_correlation_id.py` if extension
  is cleaner.

No edits to: `loop.py` (T01 territory, already closed), other
`lint_plan.py` constants beyond the regex, templates (T03 territory),
skills, production WUs / features, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`
(tests, lint, security, coverage) must pass. Plus the existence
check named in AC4.

**Escalation triggers.**

1. **Regex greedy-match gotcha.** If the test
   `test_correlation_id_re_rejects_unknown_suffix` reveals that
   `CLOSE-INTERMEDIATE|CLOSE` ordering still allows
   `CLOSE-INTERMEDIATE` to match as `CLOSE` + orphan `-INTERMEDIATE`
   in some path (Python's `re` is left-most longest, but
   alternation order matters in the `(...|...)` group), pin
   `re.fullmatch` or anchor the suffix end-of-string explicitly.
   If the gotcha cannot be resolved without behavior change to
   already-passing test cases for legacy IDs, emit `status: blocked`.
2. **Helper-duplication.** Per authoring-work-units §10: before
   editing `correlation-ids.md`, run
   `grep -rn "RETRO|LESSONS|DOCS|PLAN|CLOSE)" .specfuse/`
   to enumerate every other site that mentions the regex's
   alternation. If any other rule file, skill, or template
   independently carries the same alternation pattern, name them
   in the RESULT block as out-of-scope for this WU and recommend a
   follow-on hygiene WU. Do NOT silently edit them.
3. **Cross-repo contract drift.** If the `INIT-…` orchestrated
   correlation-ID grammar (from FEAT-2026-0003) shows separate
   per-component contracts that this WU's regex would break, emit
   `status: blocked`. The orchestrated path stays parallel to the
   component-local path.
