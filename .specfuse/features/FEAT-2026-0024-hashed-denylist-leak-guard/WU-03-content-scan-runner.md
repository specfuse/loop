---
id: FEAT-2026-0024/T03
type: implementation
model: opus
effort: high
status: draft
attempts: 0
planned_cost_usd: 2.50
oracle_env: macos_local
produces: [".specfuse/scripts/leak_scan_content.py", "tests/test_leak_scan_content.py"]
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Content-scan runner — scan a GitHub issue/PR event payload for leaks, exit non-zero on a hit

**Objective.** Ship `leak_scan_content.py`: a Python runner that reads a single
GitHub event payload (issue/PR title + body + the triggering comment), runs the
gate-1 leak scanner (structural patterns + plaintext denylist when present + the
committed hashed denylist + gitleaks) over each field, and exits non-zero on a
hit, naming the offending field. This is the unit-testable seam gate 2's Action
(T04) invokes. Closes the runner half of issue #46.

**Context.** This is `FEAT-2026-0024/T03`; `depends_on: []` — gate 1 is the
barrier (the hashed denylist core + the committed `leak_denylist.hashes` already
exist; see PLAN.md "The hashing design" and `leak_scan.py`). This WU does NOT
re-derive the scanner: it reuses `leak_scan.scan_text` (full structural +
plaintext denylist + gitleaks) and the hashed-denylist primitives
(`load_hashed_denylist`, `hashed_denylist_hits`) as a library.

GitHub Actions hands a workflow the event payload as a JSON file at
`$GITHUB_EVENT_PATH`. The fields this runner scans are exactly those present in
that payload for the triggering event:
- `issues` event → `issue.title`, `issue.body`.
- `pull_request` event → `pull_request.title`, `pull_request.body`.
- `issue_comment` / `pull_request_review_comment` event → `comment.body`.

Scanning the **full** comment history of an issue/PR would require `gh api` /
the REST API, which LEARNINGS `[FEAT-2026-0014/T01/gh-claudeP-broken]` flags as
unreliable inside dispatched subprocesses. So this runner is scoped to the
fields present in the single event payload — the new-content surface the Action
fires on per open/edit. Whole-history scanning is an Open Verification for the
operator (see `GATE-02-REVIEW.md`), not committed here.

Reference the binding rules under `.specfuse/rules/` (`result-contract.md`,
`never-touch.md`, `security-boundaries.md`). The driver owns all git; edit files
only.

**Acceptance criteria.**

1. **Red test (fails on HEAD).** New test file
   `tests/test_leak_scan_content.py::test_runner_exits_nonzero_on_planted_denylist_hit`
   builds, in a `tmp_path`, (a) a `leak_denylist.hashes` file via the gate-1
   generator helpers from a known placeholder literal (e.g. `acme-widget`) and
   (b) an event-payload JSON whose `issue.body` embeds that placeholder, then
   invokes the runner pointed at both and asserts a non-zero exit and a finding
   naming the `issue.body` field. This **fails on HEAD** because
   `leak_scan_content.py` does not exist. The placeholder literal and its hash
   are built in `tmp_path` only — **no committed fixture carries a denylisted
   string** (a committed hit would trip the `leak-scan --all` gate; see
   Escalation trigger 3).

2. `leak_scan_content.py` exposes `scan_event(payload: dict, ...) -> list[str]`:
   given a parsed event-payload dict, it extracts the present
   title/body/comment fields (missing fields skipped, never crash), scans each
   with the gate-1 scanner + hashed denylist, and returns a list of findings
   each prefixed with the originating field name
   (`issue.body: <finding>`, `pull_request.title: <finding>`, …). An empty list
   means clean.

3. The same test, fed a **clean** payload (no placeholder, no structural hit),
   asserts `scan_event` returns `[]` and the runner exits 0 — no false positive
   on ordinary issue/PR text. (`test_runner_exits_zero_on_clean_payload`.)

4. `main(argv) -> int` is the CLI entry: it reads the event-payload path (from
   an explicit `--event-path` argument, falling back to the `GITHUB_EVENT_PATH`
   environment variable by name — never by reading any secret), parses the JSON,
   calls `scan_event`, prints each finding on its own line, and returns 1 on any
   finding / 0 when clean. A missing or unparseable event file returns a
   non-zero exit with a diagnostic (fail closed — an unreadable payload is not a
   pass). Tested: `test_main_missing_event_path_fails_closed`.

5. The runner loads the committed hashed denylist via the gate-1
   `load_hashed_denylist`; when the `.hashes` file is absent it contributes
   nothing (no crash), mirroring `scan_repo`'s additive behavior. Tested:
   `test_scan_event_no_hashes_file_no_crash`.

6. **Symbol/file existence** before declaring complete:
   ```bash
   PYTHONPATH=.specfuse/scripts python3 -c "import leak_scan_content as m; assert hasattr(m, 'scan_event') and hasattr(m, 'main')"
   test -s .specfuse/scripts/leak_scan_content.py
   test -s tests/test_leak_scan_content.py
   ```
   All must succeed.

7. The same test from AC1 **passes after** this WU's edits
   (`python3 -m unittest tests.test_leak_scan_content` exits zero) — the
   red→green proof (`/authoring-work-units` §12).

8. The `code` gate set passes (tests, coverage ≥ 90% on touched lines, ruff
   lint, bandit security, `leak-scan --all` clean, `leak-scan-hook`). New
   behavior is covered by the AC1–AC5 tests.

**Do not touch.** This WU creates exactly **2 new files**
(`.specfuse/scripts/leak_scan_content.py`, `tests/test_leak_scan_content.py`)
and edits **0 existing files**. Reuse `leak_scan.py` as an imported library — do
**NOT** modify `leak_scan.py` (gate 1 owns it; re-authoring its helpers here is
out of scope), the committed `leak_denylist.hashes`, or `leak_denylist.txt`
(gitignored). Do NOT add the `.github/workflows/` file (T04 owns it). Do NOT
touch `verification.yml`, the gate-1 WU files, other features, secrets, `.git/`.
The driver owns all git — edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` — in
particular `leak-scan --all` must stay clean (no committed fixture carries a
denylisted string) — plus the red→green proof in AC1/AC7 and the existence
checks in AC6. The runner is Python, so the `code` gate set fully covers it; no
`shellcheck`/`bats` gate applies (`/authoring-work-units` §11 fires only on a
committed shell artifact).

**Escalation triggers.**

1. **Dependency absent.** If gate 1's `load_hashed_denylist` /
   `hashed_denylist_hits` / `scan_text` are not importable from `leak_scan`,
   emit `status: blocked` — do not re-implement the scanner here.

2. **Match-contract mismatch.** If the gate-1 scanner cannot be reused over an
   issue/PR field as a plain string (e.g. it only accepts a staged-diff format),
   STOP and emit `status: blocked` naming the contract gap — this is the gate-2
   scope-ambiguity boundary the operator owns (PLAN.md Escalation trigger 1), not
   a license to fork the scanner.

3. **Self-leak via fixture.** If making the red test pass would require
   committing a fixture file that contains a real denylisted org name or any
   email/user-path/private-host structural hit (which `leak-scan --all` /
   pre-commit would then flag), STOP and emit `status: blocked` — build the
   denylist and payload in `tmp_path` instead. Re-leaking a literal defeats the
   feature (`security-boundaries.md`).

4. **Completeness.** If `scan_event` or `main` is absent from
   `leak_scan_content.py` after your edits, or the AC1 test does not exist, emit
   `status: blocked` — do not claim complete.
