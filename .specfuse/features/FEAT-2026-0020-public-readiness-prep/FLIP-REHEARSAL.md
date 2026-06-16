<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# FLIP-REHEARSAL — FEAT-2026-0020 (Public-readiness prep)

Correlation ID: `FEAT-2026-0020/T18`. Dry-run readiness record for
`FLIP-CHECKLIST.md`. This is a **readiness record only** — the actual visibility
flip and history force-push (Phases 1–3) are operator-side and are NOT executed
here.

- **Rehearsed:** 2026-06-16
- **Operator:** Christian Labonté (confirm + countersign before the real flip)
- **Method:** Phase-0 verification commands run live (out-of-loop completion of
  gate 2); Phases 1–3 reviewed for readiness, not executed.

> Two FLIP-CHECKLIST bugs were found and fixed during this rehearsal:
> Step 0.4 used `test -x` on `leak_scan.py` (it is invoked via `python3`, not
> executed directly) → changed to `test -f`. Step 0.6's ad-hoc greps flagged
> `INIT-2026-0001`, which is the **kept** orchestrated-ID sample (allowlisted),
> → replaced with the canonical `scrub-history.sh --verify-only` (org-only).

## Phase 0 — Pre-flip verification (run live)

| step | disposition | evidence |
|------|-------------|----------|
| 0.1 Hygiene files | **PASS** | `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` all present + non-empty. |
| 0.2 Templates + dependabot | **PASS** | 3 issue templates + `pull_request_template.md` + `dependabot.yml` all present. |
| 0.3 GitHub label set | **DEFERRED — operator** | `gh label list` queries the remote; verify `bug`/`enhancement`/`question` exist GitHub-side at flip time. No local evidence possible. |
| 0.4 Leak-guard installed + CI gate | **PASS** | `leak_scan.py`, `.specfuse/hooks/pre-commit`, and the `leak-scan` gate in `verification.yml` all present; hook live via `core.hooksPath`; bats 3/3; `leak-scan --all` exits 0; suite 726 OK. |
| 0.5 Edit-history residual risk | **ACCEPTED** | Org-names only, no credentials. GitHub retains issue/PR edit-history; operator-accepted per gate-1 close. |
| 0.6 History rewrite clean | **PASS** | `scrub-history.sh --verify-only` → "history is CLEAN" (all three surfaces). Leaked INIT-F06 folder absent from all history. Tests pass. (`INIT-2026-0001` retained by design.) |
| 0.7 Pre-push backup bundle | **READY — operator** | Create `../loop-PRE-FLIP.bundle` immediately before the force-push (Phase 1). A pre-scrub bundle already exists from this session; make a fresh pre-flip one at flip time. |

## Phases 1–3 — readiness (NOT executed; operator runs at flip)

| step | readiness | notes |
|------|-----------|-------|
| 1.1 Re-attach origin | **READY** | `filter-repo` dropped origin. `git remote add origin git@github.com:specfuse/loop.git` (or HTTPS) at flip. |
| 1.2 Force-push all + tags | **READY** | `git push --no-verify --force --all origin && … --tags`. `--no-verify` required (pre-push-hook + sandbox-off corruption risk). This is the publish mechanism — a normal PR-merge does NOT replace remote's old commits. |
| 1.3 CI green on force-pushed branch | **PENDING (post-push)** | Watch `gh run`; `leak-scan` gate must be green. CI installs gitleaks + bats (added to `ci.yml`). |
| 2.1 Visibility flip → public | **PENDING — maintainer** | GitHub UI, irreversible-ish. Only after Phase 0 all-pass + Phase 1 CI green + 0.5 cleared. Also enable **Settings → Security → Private vulnerability reporting** (SECURITY.md + CODE_OF_CONDUCT.md point reporters there). |
| 3.1–3.4 Post-flip confirm | **PENDING (post-flip)** | Confirm public; `leak-scan` green on `main`; notify collaborators to re-clone (hashes changed); keep backup bundle ≥48h. |

## Go / No-Go

**Readiness verdict: GO for the operator-side flip** — every locally-verifiable
pre-flip gate passes; remaining items are inherently operator/GitHub-side
(label check, force-push, visibility toggle, post-flip confirmation) and are
enumerated with owners + rollbacks in `FLIP-CHECKLIST.md`.

Outstanding operator actions before/at flip: 0.3 (label check), 0.7 (fresh
bundle), Phases 1–3. Token already rotated; history already scrubbed; leak-guard
live.
