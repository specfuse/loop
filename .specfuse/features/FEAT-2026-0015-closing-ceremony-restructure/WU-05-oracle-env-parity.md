---
id: FEAT-2026-0015/T05
type: implementation
model: claude-sonnet-4-6
effort: medium
status: done
attempts: 3
planned_cost_usd: 1.00
duration_seconds: 1023.008
cost_usd: 2.382919
input_tokens: 79
output_tokens: 44385
---

# Add `oracle_env` frontmatter field and lint warning

**Objective.** Add an `oracle_env:` frontmatter field on WU files
that declares the environment in which the WU's verifying oracle
runs (macOS local, Linux Docker, GitHub Actions CI, or a named
environment). Lint emits a WARN when a WU's Acceptance criteria
section mentions oracle-like verbs but the field is missing.

**Context.** This is `FEAT-2026-0015/T05`. Depends on T04 only
for sequencing (verdict + oracle_env together comprise the
close-time evidence contract); no symbolic dependency.

Per LEARNINGS `[FEAT-2026-0013/G1-CLOSE/oracle-environment]` (the
durable rule) and PLAN.md roadmap detail § "Oracle environment-
parity declaration": FEAT-2026-0013 v1 reported the goal met on
macOS-local audit alone; the same fix failed on the next CI run
because macOS APFS hides the race Linux ext4 surfaces. The rule
is "oracle environment must match goal environment" and it
currently lives in prose alone — nothing enforces it.

The lexicon (allowed values for `oracle_env`):

- `macos_local` — developer macOS shell. APFS, BSD utils.
- `linux_docker` — Docker container, Linux kernel, glibc.
- `github_actions_ci` — GitHub Actions runner (Ubuntu image
  unless WU spec narrows further).
- `<any other string>` — operator-named environment for cases
  not covered above (e.g. `windows_powershell`, `alpine_musl`).
  Lint accepts; the operator is responsible for matching it
  to the goal env at close time.

T05 ships the FIELD + the LINT WARN. T07 (hollow-pass guard)
will read the field at close time to enforce env-parity. The
two are decoupled so a lint failure doesn't fire at dispatch
time (warn is non-blocking).

Oracle-verb detection (the trigger for the WARN). Heuristic
pattern matching against the WU body's `Acceptance criteria`
section (case-insensitive):

- `test loop` / `test loops` / `loops of tests`
- `audit` (any tense, when applied to behavior or runs)
- `recursive run` / `run N times` / `N consecutive runs`
- `smoke test` / `smoke-test` (as a verb, not a noun)
- `oracle` (the word itself)
- `integration test` / `e2e`
- explicit `bash` blocks invoking `for i in $(seq` or
  `repeat N times` shapes

If ANY of these match in the AC section AND `oracle_env` is
missing from frontmatter AND the WU's `type` is NOT a closing
type already exempted (lessons / docs / retrospective, where
the oracle is the gate review process itself), emit WARN.

Reference binding rules under `.specfuse/rules/`. Driver owns git.

**Acceptance criteria.**

1. `WU.template.md` documents the optional `oracle_env:`
   frontmatter field in the frontmatter-notes comment block,
   listing the four accepted forms (`macos_local`,
   `linux_docker`, `github_actions_ci`, operator-named string)
   and citing LEARNINGS `[FEAT-2026-0013/G1-CLOSE]` as the
   rationale.
2. `lint_plan.py` defines a module-level constant
   `ORACLE_VERB_PATTERNS = (...)` — a tuple of compiled
   `re.Pattern` objects covering at least the seven oracle-
   verb shapes named in this WU's Context section. Use
   `re.IGNORECASE`.
3. `lint_plan.py` defines a pure helper
   `def detect_oracle_verbs(ac_section_text: str) -> list[str]`
   returning the list of matched verb strings (or the empty
   list). The function takes only the AC-section slice, not
   the whole WU body, so a stray "audit" elsewhere does NOT
   trigger.
4. `lint_plan.py` walks each non-closing-non-prose WU file:
   - Slices out the `**Acceptance criteria.**` section
     (from the bold-preamble line to the next `**` heading
     or EOF).
   - Calls `detect_oracle_verbs` on the slice.
   - If matches are non-empty AND frontmatter has no
     `oracle_env` field, prints `WARN: <wu_file>: AC mentions oracle-like work (matched: <verbs>) but frontmatter has no 'oracle_env' field. See LEARNINGS [FEAT-2026-0013/G1-CLOSE].`
   - Lint EXIT CODE is unaffected by this warning (warn-only;
     non-blocking).
5. WUs of type `lessons`, `docs`, `retrospective` are exempt
   from this check (their AC routinely says "audit" of the
   gate, but their oracle IS the close ceremony itself).
6. New unit tests in `tests/test_lint_oracle_env.py`:
   - `test_detect_oracle_verbs_finds_test_loop`
   - `test_detect_oracle_verbs_case_insensitive_audit`
   - `test_detect_oracle_verbs_finds_recursive_run_N_times`
   - `test_detect_oracle_verbs_skips_outside_ac_section`
   - `test_detect_oracle_verbs_returns_empty_on_unrelated_text`
   - `test_lint_warns_on_oracle_ac_without_env_field` — temp
     feature with an `implementation` WU whose AC mentions
     "test loop 50×"; assert lint stdout contains the WARN
     and exit code is 0.
   - `test_lint_no_warn_when_oracle_env_present` — same WU
     but with `oracle_env: linux_docker`; assert no WARN.
   - `test_lint_no_warn_for_lessons_type_even_with_oracle_verbs`
     — exempt type.
7. Symbol-existence:
   `python3 -c "from lint_plan import ORACLE_VERB_PATTERNS, detect_oracle_verbs; assert detect_oracle_verbs('run the test loop 50 times'); assert not detect_oracle_verbs('hello world')"` exits 0.
8. Existing test suite stays green:
   `python3 -m unittest discover tests` exits 0.
9. **Lint regression on existing fixtures** per
   `[FEAT-2026-0005/G1-LESSONS]`: running
   `python3 .specfuse/scripts/lint_plan.py
   .specfuse/features/FEAT-2026-0015-closing-ceremony-restructure`
   exits 0. New WARNs on this feature's own pre-existing WU
   files are acceptable (they predate the rule); FAILs are not.

**Do not touch.** Exactly 3 files change:
- `.specfuse/scripts/lint_plan.py` (new constant + helper + AC
  walker integration).
- `.specfuse/templates/WU.template.md` (frontmatter note for the
  new optional field).
- `tests/test_lint_oracle_env.py` (new file).

No edits to: `loop.py` (T07 will read the field at close time),
`/draft-feature` skill, other features' WU files, secrets,
`.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** `code` gate set in `.specfuse/verification.yml`
(tests, lint, security, coverage). Plus AC7's symbol-existence
check. Plus AC9's lint-regression check on this feature.

**Escalation triggers.**

1. **Completeness.** If `ORACLE_VERB_PATTERNS` or
   `detect_oracle_verbs` is absent from `lint_plan.py` after
   your edits, emit `status: blocked` — do not claim complete.
2. **§10 helper-duplication.** Run
   `grep -rn "oracle_env\|ORACLE_VERB" .specfuse/ tests/`
   and confirm no pre-existing definition. If found, name it
   and emit `status: blocked`.
3. **Regex over-fire.** If your AC-walker fires on prose
   contexts that name a verb without intending oracle work
   (e.g. someone wrote "audit trail" as a noun), tune the
   pattern AND add a test asserting non-fire. If the tradeoff
   is unclear, emit `status: blocked` with the ambiguous
   example named — do NOT ship a noisy lint that operators
   learn to ignore.
4. **AC-section slicing failure.** If a WU body uses ATX
   headings (`## Acceptance criteria`) instead of the bold-
   preamble convention (`**Acceptance criteria.**`), your
   slicer should handle both — per
   `[FEAT-2026-0003/G3-LESSONS]` the linter already widened
   for ATX in adopt_feature contexts. If you cannot match
   both forms safely, emit `status: blocked`.
