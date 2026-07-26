---
id: FEAT-2026-0039/T06
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
produces:
  - .specfuse/monitoring.overrides.yml.example
  - .specfuse/monitoring-secrets-checklist.md
  - specfuse/loop/data/monitoring.overrides.yml.example
  - specfuse/loop/data/monitoring-secrets-checklist.md
  - tests/test_monitoring_bootstrap_artifacts.py
produces_driver_helper: gitignore.snippet entry for .specfuse/monitoring.overrides.yml
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.4.0
started_at: 2026-07-26T04:49:51.322017+00:00
duration_seconds: 493.89
cost_usd: 1.835641
input_tokens: 78
output_tokens: 17034
---

# Ship the local-runner bootstrap artifacts and seed them

**Objective.** Add the two artifacts that make the first local `--dry-run` minutes
away after the interview ends — `.specfuse/monitoring.overrides.yml.example` (the
machine-local overrides shape, whose live counterpart is gitignored) and
`.specfuse/monitoring-secrets-checklist.md` (the env-var names the operator must
export, never their values) — and seed both into scaffolded projects.

**Context.** This is `FEAT-2026-0039/T06` of gate 2, following T04. Read `PLAN.md`
in this folder — its **scope boundary** section is what puts these artifacts in
scope while moving the GitHub Actions workflow out, and its **Notes** section
records the filename constraint below. Also read `GATE-02.md`'s definition of done.

**These are data files, and that is deliberately the whole of it.** Their eventual
consumer is `specfuse-monitor run`, a CLI FEAT-2026-0040 ships. `PLAN.md` moved the
GitHub Actions workflow to 0040 precisely because a workflow's *body invokes* that
nonexistent binary and would be broken on day one — the
`[FEAT-2026-0029/G1-CLOSE]` failure. These two files are different in kind: each is
valid, inspectable, and machine-checkable standing alone. Keep them that way. Do
**not** write a runner script, a `Makefile` target, or any invocation of a binary
that does not exist yet; each artifact's header says in one line that merge and
execution semantics land in FEAT-2026-0040.

**`monitoring.overrides.yml.example` uses gate 1's schema, unchanged.** Same
top-level `environments:` / `components:` shape, so `validate_monitoring` is its
validator too and this feature ships exactly one monitoring schema rather than two.
Its content is the machine-local slice an operator edits: which environment a local
run targets, the credential **env-var names** available on that machine, and
`runner: local` on every component. Read
`.specfuse/monitoring.yml.example` first and mirror its comment density and its
placeholder discipline.

**The filename must carry no `.local.` segment — this is a hard constraint, not
taste.** `.specfuse/scripts/leak_scan.py` classifies any `<word>.local` token as a
private-host finding (`\b[a-zA-Z0-9-]+\.(?:local|internal|corp|lan|intranet|localdomain)\b`),
and the pre-commit hook runs the structural scan on the staged diff. The driver
commits every WU squash **without** `--no-verify`, so a diff containing
`monitoring<dot>local<dot>yml` (spelled here with placeholders precisely so this WU
file does not itself trip the hook) would be rejected three times and this WU would
block on `spinning_detected`. `monitoring.overrides.yml` is the name `PLAN.md`
picked; use it unless you find a strictly better one that also has no `.local.`
segment, and record the choice in the artifact's header comment. **Do not write the
matching token into any file you produce, including comments and test fixtures** —
the hook scans the whole staged diff, not just the artifact.

**The secrets checklist is read-only by construction.** It enumerates
`UPPER_SNAKE_CASE` env-var **names** and where to obtain each value; it holds no
value, no placeholder that looks like a value, and no instruction to write values
into any tracked file. See `.specfuse/rules/security-boundaries.md`.

**Seeding two new files touches seven enumerated surfaces.** All are explicit
hand-maintained lists; missing one fails a green suite. Update every one:

1. `specfuse/loop/data/monitoring.overrides.yml.example` and
   `specfuse/loop/data/monitoring-secrets-checklist.md` — the packaged copies, byte
   identical to the canonical `.specfuse/` files.
2. `scripts/sync-scaffold.sh` — the `FILES=()` array (both entries). Not
   `CORE_FILES`.
3. `tests/test_scaffold_data_in_sync.py` — the `TRACKED` set.
4. `tests/test_scaffold_resources.py` — its expected-relpath list.
5. `tests/test_init_integration.py` — its expected set.
6. `tests/sync_scaffold.bats` — its `setup()` writes one fixture per `FILES` entry;
   `sync-scaffold.sh` runs under `set -euo pipefail` and `sync_file()` returns 1 on
   a missing canonical source, so a `FILES` entry with no bats fixture turns
   `[ "$status" -eq 0 ]` red.
7. `.specfuse/gitignore.snippet` **and** `specfuse/loop/data/gitignore.snippet` —
   add `.specfuse/monitoring.overrides.yml` (the live file, not the `.example`).
   The snippet is itself a tracked seed file, so both copies must stay byte
   identical.

**Neither file gets a `_SEED_RENAME` entry.** Monitoring is opt-in — the same
decision T03 recorded for `monitoring.yml.example`. A rename would auto-create live
files in every scaffolded project, including ones that deploy nothing.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `verification-discipline.md`) apply. Do not restate them.

**Acceptance criteria.**

1. `tests/test_monitoring_bootstrap_artifacts.py::test_overrides_example_validates_clean`
   exists and **fails on HEAD before this WU's edits** (the artifact does not yet
   exist). It calls
   `specfuse.loop.lint_monitoring.validate_monitoring(".specfuse/monitoring.overrides.yml.example")`
   and asserts the finding list is empty.
2. After this WU's edits that test passes, and so does
   `test_both_artifacts_are_seeded_without_rename` — running the scaffold init path
   into a temporary directory, asserting both relpaths are written under their own
   names and that neither a live `monitoring.overrides.yml` nor a
   `monitoring-secrets-checklist` variant is created by a rename.
3. `test_live_overrides_file_is_gitignored` asserts `.specfuse/gitignore.snippet`
   contains `.specfuse/monitoring.overrides.yml` and that the two copies of the
   snippet (canonical and packaged) are byte identical.
4. `test_chosen_filename_has_no_dot_local_segment` asserts no path this WU ships
   matches leak-scan's private-host pattern. Cheap, and it is the guard that keeps a
   future rename from reintroducing the `spinning_detected` trap.
5. `test_secrets_checklist_names_no_values` asserts every credential token in
   `monitoring-secrets-checklist.md` is `UPPER_SNAKE_CASE` (matching
   `lint_monitoring._ENV_VAR_NAME_RE`) and that the file contains no
   connection-string-shaped or key-shaped literal. A negative case is required: feed
   the same assertion an inline-literal string built in the test and confirm it is
   rejected, so the check is seen firing rather than assumed to
   (`verification-discipline.md` §3).
6. Every environment name, host, workspace ID, queue name, and organization name in
   both artifacts is an obvious `acme-*` placeholder. `leak-scan` runs on this diff
   and the pre-commit hook is stricter than the CI gate.
7. Each artifact's header contains a one-line statement that merge and execution
   semantics land in FEAT-2026-0040 and that the file is a shape declaration only.
   A test greps for `FEAT-2026-0040` in both.
8. `python3 -m pytest tests/test_scaffold_data_in_sync.py tests/test_scaffold_resources.py tests/test_init_integration.py`
   exits 0 (surfaces 1, 3, 4, 5) and `bats tests/sync_scaffold.bats` exits 0
   (surfaces 2 and 6).
9. Nothing in this WU changes the pass/fail behavior of an existing gate; the full
   `code` set passes both before and after, with these files the only addition.
10. Every new `subprocess.run` call, if any, declares `check=` explicitly
    (`PLW1510`, enforced since FEAT-2026-0037).

**Do not touch.** `.specfuse/monitoring.yml.example` and
`specfuse/loop/lint_monitoring.py` (gate 1 shipped both; this WU consumes the
validator as its oracle — if the overrides example fails it, that is a real defect
in the example, not a validator to loosen); `_SEED_RENAME`'s existing entries;
existing lines in `.specfuse/gitignore.snippet` (append only);
`.specfuse/rules/design-for-diagnosis.md` (T04); the discovery reference
implementation (T05); the skill files (T07); the drift test (T08); `.git/`, secrets.
The driver owns all git operations. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` — `tests`,
`lint`, `security`, `coverage` ≥ 90%, `leak-scan`, `monitoring-example-lint`, and
the bats suites (`sync-scaffold-bats`, `init-sh-shim-bats`, `init-skills-bats`) —
must all pass, plus AC8's two commands run individually and
`python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.overrides.yml.example`
exiting 0. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if the overrides file cannot be
expressed in gate 1's schema without changing the validator — shipping a second
monitoring schema is a human decision about the feature's shape, not a drafting
workaround. Also block if seeding either artifact requires a `_SEED_RENAME` entry
(auto-creating live monitoring files in every scaffolded project is explicitly out of
scope), or if a `leak-scan` finding on this diff cannot be resolved by placeholder
substitution — a real leak is an escalation, never a `--no-verify`. If either
artifact is absent from the files you edited, emit `status: blocked` — do not claim
complete. Blocked is respectable (`result-contract.md` rule 4).
