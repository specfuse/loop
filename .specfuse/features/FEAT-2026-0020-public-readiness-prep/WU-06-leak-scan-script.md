---
id: FEAT-2026-0020/T15
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 2.50
produces_driver_helper: ["scan_text", "scan_staged", "load_allowlist"]
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Leak-scan detector — one detector, callable from staged / CI / history (the guard core)

**Objective.** Implement `.specfuse/scripts/leak_scan.py`: a single leak-detection module
that scans text for secrets, `/Users/<user>/` path shapes, non-allowlisted emails, private
hostnames, and a private-org denylist — with an allowlist that exempts legitimate samples.
This is the **core** of the operator-requested leak-prevention guard (`GATE-02.md` Required
deliverable); WU-07 wires it into the three callers (pre-commit hook, CI, history audit).

**Context.** Part of FEAT-2026-0020 gate 2. Gate 1 had to rewrite history
(`history-scrub/scrub-history.sh`) to expunge private-org names, personal paths, and a
leaked cross-poll folder; without an automated guard the same leaks recur on the next
commit (`GATE-02.md` Required deliverable rationale; LEARNINGS
`[FEAT-2026-0020/history-scrub/*]`). This WU factors the pattern-matching out of
`scrub-history.sh --verify-only`'s `build_pattern`/`verify` logic into a reusable Python
detector so the same logic backs all three surfaces. Correlation ID `FEAT-2026-0020/T15`.

Grounding: `history-scrub/scrub-history.sh` (the existing `--verify-only` pattern logic to
factor out), `history-scrub/replace-text.txt` (the literal mappings — these contain the
private strings and MUST NOT be committed as a denylist), `tests/_loop_loader.py` /
`tests/test_adopt_feature.py` (the `load_module` import convention for `.specfuse/scripts`
modules), `.specfuse/rules/correlation-ids.md` (`INIT-2026-0001` is the canonical
orchestrated-ID *sample*, NOT a leak — must be allowlisted). `gitleaks` 8.30.1 is on PATH
(used in T01).

Binding rules in `.specfuse/rules/` apply — especially `security-boundaries.md` and
`never-touch.md` §2: **do not commit literal private-org names**. The committed detector
carries only generic structural regexes; any literal org-name denylist is read from a
gitignored / hashed source, never inlined.

**Acceptance criteria.**

1. `tests/test_leak_scan.py::test_flags_planted_user_path` exists and **fails on HEAD
   before this WU runs** (the test file and `leak_scan.py` do not yet exist — red).
2. `.specfuse/scripts/leak_scan.py` defines `scan_text(text, allowlist=...)` returning the
   list of structural-pattern hits (secrets via `gitleaks`, `/Users/<user>/` path shapes,
   non-allowlisted emails, private hostnames, denylist entries), and `scan_staged()` for
   the staged-diff surface.
3. The committed module contains **only generic structural regexes** — no literal
   private-org name appears in `leak_scan.py` or any committed file (the denylist of
   literal org names is loaded from a gitignored / hashed source via `load_allowlist`'s
   companion, never inlined). `git grep` for any known gate-1-redacted literal returns
   nothing in this WU's diff.
4. An **allowlist** exempts legitimate samples; `INIT-2026-0001` (canonical orchestrated
   correlation-ID sample per `.specfuse/rules/correlation-ids.md`) is exempted and does
   NOT trip the scanner.
5. `tests/test_leak_scan.py::test_flags_planted_user_path` **passes after** this WU's
   edits; companion tests prove (a) a clean diff yields zero hits and (b) the allowlist
   exempts `INIT-2026-0001`.
6. `code` gates pass: `coverage` ≥ 90% on the new module, `ruff` clean, `bandit -ll`
   clean (any `subprocess`/`shell` use for `gitleaks` carries a narrow `# nosec` with a
   reason, matching the `loop.py` precedent).

**Do not touch.**

- `.specfuse/verification.yml`, `scripts/smoke-test.sh`, `.github/workflows/ci.yml`, the
  pre-commit hook — the CI/hook wiring is **WU-07's** scope, not this WU's.
- `history-scrub/*.txt` config files (read-only reference; they hold private literals).
- Sibling gate-2 WU outputs (README/CONTRIBUTING/SECURITY/templates/dependabot/checklist).
- Generated directories, secrets, `.git/`. The driver owns all git — edit files only.
- See `.specfuse/rules/never-touch.md`.

**Verification.**

- Red→green proof (scoped): `python3 -m unittest tests.test_leak_scan -v` — red before,
  green after.
- Symbol-existence: load the module the way `tests/` does and confirm the symbols —
  `python3 -c "import importlib.util as u; s=u.spec_from_file_location('leak_scan','.specfuse/scripts/leak_scan.py'); m=u.module_from_spec(s); s.loader.exec_module(m); assert hasattr(m,'scan_text') and hasattr(m,'scan_staged')"`.
- `code` gates per `.specfuse/verification.yml` (tests, lint `ruff check`, `bandit -ll`,
  `coverage --fail-under=90`).
- No-literal-leak check: the WU's own diff contains no gate-1-redacted private literal.
- Oracle environment: `macos_local`.

**Escalation triggers.**

1. **Symbol/test absent.** If `scan_text` or `scan_staged` is absent from `leak_scan.py`,
   or `tests/test_leak_scan.py` was not written, emit `status: blocked` — do not claim
   complete (`/authoring-work-units` §9 completeness trigger).
2. **Cannot avoid committing a literal.** If the only way you can make the detector work is
   to inline a literal private-org name into a committed file, STOP and emit
   `status: blocked` — the denylist-not-committed constraint is itself an acceptance
   criterion (`GATE-02.md`); commit only structural regexes and load literals from a
   gitignored/hashed source.
3. **`gitleaks` unavailable in the gate environment.** If `gitleaks` is not callable where
   the `code` gate runs, emit `status: blocked` rather than silently dropping the secret
   surface — the secret detector is load-bearing.
