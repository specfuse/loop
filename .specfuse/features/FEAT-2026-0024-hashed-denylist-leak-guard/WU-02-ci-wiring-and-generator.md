---
id: FEAT-2026-0024/T02
type: implementation
model: opus
effort: high
status: done
attempts: 2
planned_cost_usd: 2.50
oracle_env: macos_local
produces_driver_helper: scan_repo
produces: [".specfuse/scripts/leak_scan.py", ".specfuse/scripts/leak_denylist.hashes", "tests/test_hashed_denylist_ci.py"]
duration_seconds: 736.182
cost_usd: 3.271526
input_tokens: 24271
output_tokens: 40023
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# CI wiring + generator — `--hash-denylist`, `scan_repo` org-name coverage, committed `.hashes`

**Objective.** Ship the operator-facing generator (`leak_scan.py
--hash-denylist`) that writes the committed `leak_denylist.hashes` from the
gitignored plaintext, wire the T01 hashed-match core into `scan_repo` so the CI
`--all` gate catches org-name re-introduction using **only** the committed
hashed file, and commit the generated `.hashes` for the current denylist. This
closes issue #45.

**Context.** This is `FEAT-2026-0024/T02`; depends on T01 (`normalize_token`,
`hash_token`, `load_hashed_denylist`, the sliding-window matcher). Read PLAN.md
"The hashing design" and T01's body for the `.hashes` format and the match
algorithm — this WU uses them, it does not re-derive them.

Today `scan_repo` (`leak_scan.py:228`) loads the plaintext `load_denylist()` and
substring-matches; in CI that list is empty (gitignored), so only
`_check_gitleaks_dir` runs. This WU adds the hashed-denylist check to
`scan_repo` so CI gains org-name coverage. The plaintext check stays as a
local-convenience supplement (when present it still runs; when absent the hashed
path covers CI). The CLI surface (`main`, `--staged`/`--all`) gains
`--hash-denylist`.

`--hash-denylist` reads `leak_denylist.txt` (gitignored plaintext), normalizes
each entry (T01's `normalize_token`), computes the distinct-length set, and
writes `leak_denylist.hashes` with the header (salt + lengths) and one
`hash_token` digest per literal. The salt is the committed default constant from
T01 (deterministic regeneration in CI). Running it now, against the current
plaintext denylist, produces the committed `.hashes` this WU ships.

Reference the binding rules under `.specfuse/rules/`. The driver owns git; edit
files only.

**Acceptance criteria.**
1. **Red test (fails on HEAD).** New test file
   `tests/test_hashed_denylist_ci.py::test_scan_repo_flags_org_name_via_hashed_file_only`
   creates a temp repo with a tracked file containing a denylisted org-name and
   a committed `leak_denylist.hashes` (built via the new generator/helpers), with
   `load_denylist` patched to return `[]` (plaintext **absent**, the CI
   condition) and `_check_gitleaks_dir` patched to `[]`. It asserts `scan_repo`
   returns a hit naming the file + line. This **fails on HEAD** because
   `scan_repo` has no hashed-denylist path. Issue #45's
   "`scan_repo`/`--all` flags a denylisted org-name in CI using only the hashed
   file" acceptance, made executable.
2. `main(["--hash-denylist"])` exists as a third mutually-exclusive mode (or an
   additive subcommand), reads the plaintext `leak_denylist.txt`, and writes
   `leak_denylist.hashes` in the T01 format. Tested: given a temp plaintext file
   with known entries, the written `.hashes` has a `# salt:` line, a `# lengths:`
   line listing the distinct normalized lengths, and one digest per entry that
   `load_hashed_denylist` round-trips and `hashed_denylist_hits` matches.
3. `scan_repo` loads `leak_denylist.hashes` (via T01's `load_hashed_denylist`)
   and, per tracked file, runs the sliding-window hashed match per line,
   appending `f"{rel}:{lineno}: denylist-hash"` hits. The existing gitleaks +
   plaintext-denylist behavior is preserved (additive). Tested:
   - AC1 (hashed hit with plaintext absent).
   - `test_scan_repo_clean_with_hashed_file` — a clean tree + committed `.hashes`
     returns `[]` (no false positive).
   - `test_scan_repo_missing_hashes_file_no_crash` — absent `.hashes` →
     `scan_repo` behaves as today (gitleaks/plaintext only), no crash.
4. **Committed `.hashes` shipped + clean.** `leak_denylist.hashes` exists at
   `.specfuse/scripts/leak_denylist.hashes`, generated from the current
   `leak_denylist.txt`, and is **committed** (NOT added to `.gitignore`).
   Running `python3 .specfuse/scripts/leak_scan.py --all` on the working tree
   exits 0 (clean) — the committed hashes do not false-positive on the repo's
   own tracked content. Verified by AC8's gate run.
5. **The plaintext file stays gitignored.** `.gitignore` still ignores
   `leak_denylist.txt`; this WU does NOT commit the plaintext literals. (Confirm
   by `git check-ignore .specfuse/scripts/leak_denylist.txt` → matched.)
6. The `.hashes` file header carries the obfuscation-not-secrecy caveat verbatim
   from T01's documented format, so a reader of the committed file understands
   the guarantee.
7. **Existence check** before declaring complete:
   ```bash
   PYTHONPATH=.specfuse/scripts python3 -c "import leak_scan, inspect; assert '--hash-denylist' in inspect.getsource(leak_scan.main)"
   test -s .specfuse/scripts/leak_denylist.hashes
   grep -qE '^# lengths:' .specfuse/scripts/leak_denylist.hashes
   git check-ignore -q .specfuse/scripts/leak_denylist.txt && echo "plaintext still ignored"
   ```
   All must succeed.
8. The `code` gate set passes (tests, coverage ≥ 90% on touched lines, lint,
   security, leak-scan `--all` clean, leak-scan-hook). New behavior covered by
   AC2/AC3 tests.

**Do not touch.** Paths that change: `.specfuse/scripts/leak_scan.py`
(additive — `scan_repo` wiring + `main` mode + generator; do NOT re-author T01's
core helpers, depend on them), the new committed
`.specfuse/scripts/leak_denylist.hashes`, and the new
`tests/test_hashed_denylist_ci.py`. You MAY edit `tests/test_leak_scan.py` only
if a pre-existing `scan_repo`/`main` test needs the new mode acknowledged — keep
edits minimal and additive. Do NOT modify `leak_denylist.txt` (gitignored), do
NOT add `leak_denylist.hashes` to `.gitignore`, do NOT touch `verification.yml`
(`--all` already runs), other WU files, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` — in
particular `leak-scan` (`--all`) must stay clean with the committed `.hashes`
present — plus the red→green proof in AC1/AC3 and the smoke checks in AC7.

**Escalation triggers.**
1. **Dependency.** If T01's `load_hashed_denylist` / `hash_token` /
   `normalize_token` / sliding-window matcher are absent, emit `status: blocked`
   — do not re-implement the core here.
2. **Self-leak.** If the committed `.hashes` causes `leak-scan --all` to flag
   the repo's own tracked content (a digest collides with normal text), do NOT
   loosen the matcher to silence it — investigate the collision and emit
   `status: blocked` if it cannot be resolved without weakening the guard.
3. **Completeness.** If `leak_denylist.hashes` is absent or empty after your
   edits, or `--hash-denylist` is not reachable from `main`, emit
   `status: blocked` — do not claim complete.
4. **Plaintext exposure.** If shipping the hashed file in any way commits the
   plaintext literals (e.g. an inline comment echoing an org name), STOP and
   emit `status: blocked` — re-leaking the literals defeats the feature.
