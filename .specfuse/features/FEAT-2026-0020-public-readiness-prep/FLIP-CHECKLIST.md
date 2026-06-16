<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# FLIP-CHECKLIST — FEAT-2026-0020 (Public-readiness prep)

Correlation ID: `FEAT-2026-0020/T17`

Operator-runnable checklist for flipping this repo from private to public.
Work through phases in order. Each step carries an **Owner** and a **Rollback**.
Do not skip or reorder steps — each phase gate is a dependency of the next.

**Scope boundary (resolved in `GATE-02-REVIEW.md` Open Verification #4):**
This checklist stops at the GitHub visibility flip (+ the history force-push that
makes the scrubbed tree the one published). PyPi packaging and the first release
tag belong to FEAT-2026-0019, which must be sequenced *after* this flip.

---

## PHASE 0 — Pre-flip verification

All Phase 0 checks must pass before entering Phase 1.
Mark each step `[x]` before proceeding.

---

### Step 0.1 — Hygiene files present (gate-2 T10–T12)

Verify the four community-health files are in the repo working tree:

```bash
for f in README.md CONTRIBUTING.md SECURITY.md CODE_OF_CONDUCT.md; do
  test -s "$f" && echo "OK  $f" || echo "MISSING $f"
done
```

Expected: four `OK` lines.
These files were authored in gate-2 WUs T10 (README polish), T11 (CONTRIBUTING),
and T12 (SECURITY + CODE_OF_CONDUCT).

**Owner:** Operator  
**Rollback:** Re-dispatch the relevant gate-2 WU if a file is missing. No state
was changed by this verification step alone — rollback is N/A.

---

### Step 0.2 — GitHub templates and Dependabot config present (gate-2 T13–T14)

```bash
for f in \
  .github/ISSUE_TEMPLATE/bug_report.md \
  .github/ISSUE_TEMPLATE/feature_request.md \
  .github/ISSUE_TEMPLATE/methodology_question.md \
  .github/pull_request_template.md \
  .github/dependabot.yml; do
  test -s "$f" && echo "OK  $f" || echo "MISSING $f"
done
```

Expected: five `OK` lines.

**Owner:** Operator  
**Rollback:** N/A (verification only). If files are missing, re-dispatch T13 or T14.

---

### Step 0.3 — GitHub label set intact

Templates reference `bug`, `enhancement`, and `question` — all GitHub default
labels. Verify they have not been deleted from the repo's label set before the
public flip.

```bash
gh label list --repo <REPO> --json name --jq '.[].name' | sort
```

Expected output includes: `bug`, `enhancement`, `question`.

**Owner:** Operator  
**Rollback:** If any default label is missing, recreate it via GitHub UI
(Labels → New label) or `gh label create <name>`. No state changed by this check.

---

### Step 0.4 — Leak-scan guard installed and CI gate green (gate-2 T15–T16)

Verify the leak-scan detector script exists, the pre-commit hook is wired, and
the CI gate passes. (The detector is invoked via `python3 leak_scan.py`, not run
directly, so it is checked with `test -f`, not `test -x`.)

```bash
# Detector present
test -f .specfuse/scripts/leak_scan.py && echo "OK  leak_scan.py" || echo "MISSING"

# Pre-commit hook target exists
test -f .specfuse/hooks/pre-commit && echo "OK  pre-commit hook" || echo "MISSING"

# CI gate key present in verification.yml
grep -q 'leak-scan' .specfuse/verification.yml && echo "OK  ci-gate" || echo "MISSING"

# Run the smoke tests to confirm the gate passes locally
bash scripts/smoke-test.sh
```

Expected: all `OK`, smoke-test exits 0.

**Owner:** Operator  
**Rollback:** N/A (verification only). If the gate fails, re-dispatch T15 or T16
to restore the guard scripts before proceeding.

---

### Step 0.5 — Accept or resolve GitHub edit-history residual risk

`RETROSPECTIVE.md` §"What the loop did NOT verify" entry 6 records an
operator-accepted residual: GitHub retains prior revisions of issue/PR bodies
in the "edited" dropdown, which becomes visible on the public flip. True expunge
requires delete+recreate or a GitHub Support request.

Current status: **operator-accepted residual risk** (org-names only, no
credentials) per gate-1 close. This step is a confirmation gate, not new work.

Confirm one of:
- `[x]` Residual risk accepted as-is — org-name strings in edit history, no credentials.
- `[ ]` Operator chose to expunge: submitted GitHub Support request and confirmed purge
  before proceeding.

**Owner:** Operator  
**Rollback:** N/A (decision record only).

---

### Step 0.6 — Confirm history rewrite is clean on the local branch

The `git filter-repo` phase-2 rewrite was executed prior to this checklist
(recorded in `GATE-02-REVIEW.md` Open Verification #5). Verify each scrub
surface is clean before force-pushing:

# Canonical check — org-only patterns across all three history surfaces.
# Use the scrub harness, NOT ad-hoc greps: it omits INIT-2026-0001, which is
# the scaffold's KEPT orchestrated-ID sample (allowlisted in leak_scan.py and
# present in correlation-ids.md + tests by design — NOT a leak).
bash .specfuse/features/FEAT-2026-0020-public-readiness-prep/history-scrub/scrub-history.sh --verify-only
# Expect: "RESULT: history is CLEAN." (exit 0)

# (d) leaked folder gone from all history — expect no output before "exit=0"
git log --all --oneline \
  -- '.specfuse/features/INIT-2026-0001-F06-conform-exampleEndpoint-to-validated-spec'
echo "exit=$?"

# (e) working tree still passes tests
python3 -m unittest discover -s tests
```

If any check emits matches: do NOT proceed to Phase 1. Re-run the scrub per
`history-scrub/RUNBOOK.md`, adding the missing string variants to
`replace-text.txt`, then re-run this step from the bundle restore.

**Owner:** Operator  
**Rollback:** Restore from the backup bundle created in Step 0.7 below. If the
backup bundle does not yet exist, create it before running any fix attempt.

---

### Step 0.7 — Create pre-push backup bundle

Filter-repo is irreversible without a backup. Create the bundle *before*
force-pushing, even if you believe a prior bundle exists:

```bash
git bundle create ../loop-PRE-FLIP.bundle --all
git tag pre-flip-backup 2>/dev/null || true   # local marker; dropped by any future rewrite
```

Keep the bundle until the public flip is confirmed good (see Step 3.4).

**Owner:** Operator  
**Rollback:** N/A (this step *is* the rollback mechanism for Phase 1). To restore
from it later: `git clone ../loop-PRE-FLIP.bundle`.

---

## PHASE 1 — History force-push

`git filter-repo` removes the `origin` remote. Re-attach and force-push before
flipping visibility so that the rewritten history is what becomes public.

---

### Step 1.1 — Re-attach origin remote

```bash
git remote -v            # confirm remote is absent (filter-repo removed it)
git remote add origin <ORIGIN_URL>
git remote -v            # confirm origin is present
```

`<ORIGIN_URL>`: the SSH or HTTPS URL for this repo (e.g., `git@github.com:<owner>/<repo>.git`).

**Owner:** Operator  
**Rollback:** `git remote remove origin` — no commits were pushed yet; local
state is unchanged. Restore from the backup bundle if local tree is corrupt.

---

### Step 1.2 — Force-push all branches and tags

```bash
git push --no-verify --force --all  origin
git push --no-verify --force --tags origin
```

`--no-verify` is required: the pre-push hook combined with sandbox-off mode can
corrupt the real repo (see `history-scrub/RUNBOOK.md` §4 note). This is the
documented, intentional exception per that runbook.

**Owner:** Operator  
**Rollback:** **Partially reversible.** GitHub retains force-push reflog for
30 days on private repos, and the backup bundle from Step 0.7 contains the
pre-scrub history. To restore:
1. Confirm the repo is still private (do not flip visibility before restoring).
2. `git clone ../loop-PRE-FLIP.bundle loop-restore && cd loop-restore`
3. `git remote add origin <ORIGIN_URL>`
4. `git push --no-verify --force --all origin && git push --no-verify --force --tags origin`
Once the repo becomes public, prior commits in the edit history may have already
been cached by crawlers — restore is time-critical.

---

### Step 1.3 — Verify CI passes on the force-pushed branch

After force-push, GitHub Actions re-runs CI on the new commits. Confirm the
`leak-scan` gate and all other required gates pass before flipping visibility.

```bash
gh run list --repo <REPO> --branch <BRANCH> --limit 5
# or watch:
gh run watch --repo <REPO>
```

Expected: all required gates green. If `leak-scan` fails: rollback (Step 1.2
rollback), investigate, re-scrub, re-push.

**Owner:** CI (automated) / Operator (monitor)  
**Rollback:** See Step 1.2 rollback. No visibility change has occurred yet; the
repo is still private. Investigate the failing gate before retrying.

---

## PHASE 2 — Visibility flip

One irreversible step. Perform only after all Phase 0 checks pass and CI is green.

---

### Step 2.1 — Flip repo visibility to public

Via GitHub UI:
1. Settings → General → Danger Zone → "Change repository visibility"
2. Select "Make public"
3. Type the repo name to confirm
4. Click "I understand, make this repository public"

**Owner:** Maintainer (requires admin access to the repository)  
**Rollback:** **Reversible (time-sensitive).** GitHub allows flipping back to
private: Settings → General → Danger Zone → "Change repository visibility" →
"Make private". However, any content that was public for any duration may have
been indexed by search engines, GitHub's own crawlers, or third-party mirrors.
Roll back immediately if a leak is detected post-flip. Flipping back does NOT
expunge cached copies.
**Proceed only when:** Phase 0 all steps pass, Phase 1 CI is green, and the
operator has cleared the GitHub edit-history residual (Step 0.5).

---

## PHASE 3 — Post-flip confirmation

---

### Step 3.1 — Confirm repo is publicly visible

```bash
# Must return "public"
gh repo view <REPO> --json visibility --jq '.visibility'

# Or navigate to the repo URL in a browser (logged out / incognito)
# and confirm the repo loads without a 404 or "private" gate.
```

**Owner:** Operator  
**Rollback:** If the repo shows as private or returns 404, verify the flip
completed (Step 2.1). If it did complete and the status is unexpected, contact
GitHub Support. No rollback action is needed for this verification step itself.

---

### Step 3.2 — Confirm leak-scan CI gate passes on the public branch

```bash
gh run list --repo <REPO> --branch main --limit 3
```

All required gates — including `leak-scan` — must be green on the post-flip
commit. A failing `leak-scan` gate after the flip means a residual string
survived and the repo must be flipped back immediately (Step 2.1 rollback).

**Owner:** CI (automated) / Operator (monitor)  
**Rollback:** Flip repo back to private (Step 2.1 rollback), investigate the
`leak-scan` failure, re-scrub, re-push, re-flip.

---

### Step 3.3 — Notify collaborators of invalidated history

Force-pushing rewrote every commit hash. Anyone with an existing clone or fork
must delete it and re-clone — old hashes are gone.

Send a notification to all known contributors with:
- The fact that the history was rewritten (org-name + path redaction)
- The instruction to delete their local clone and re-clone from origin
- The new base commit SHA (optional but helpful)

**Owner:** Maintainer  
**Rollback:** N/A (communication artifact). If notification was premature (flip
rolled back), send a follow-up clarification.

---

### Step 3.4 — Delete backup bundle (deferred cleanup)

After the public flip is confirmed good (Steps 3.1–3.2 green, no immediate
rollback signal within 48 hours), delete the pre-flip backup bundle:

```bash
rm ../loop-PRE-FLIP.bundle
```

Do not delete the bundle before 48 hours post-flip. The bundle is the only
complete restore point if a crawler-indexed leak is discovered in the first
day.

**Owner:** Operator  
**Rollback:** N/A — this is a cleanup step. If the bundle is needed after
deletion, restore from GitHub's 30-day force-push reflog (private repos only;
already public by this point so reflog may not be accessible).

---

## Scope boundary (repeated for clarity)

This checklist ends at Step 3.4. FEAT-2026-0019 handles:
- Building and publishing the first PyPi wheel
- Creating the first release tag

FEAT-2026-0019 must be sequenced *after* this checklist is complete and the
repo is confirmed public. Do not begin 0019's PyPi tag steps until Step 3.2
is green.
