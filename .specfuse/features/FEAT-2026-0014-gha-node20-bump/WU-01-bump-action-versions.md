---
id: FEAT-2026-0014/T01
type: implementation
model: claude-sonnet-4-6
effort: medium
status: blocked_human
attempts: 1
duration_seconds: 38.01
cost_usd: 0.247557
input_tokens: 8
output_tokens: 1509
---

# Bump GitHub Actions to Node-24 generation in ci.yml

**Objective.** Edit `.github/workflows/ci.yml` so the two pinned actions
(`actions/checkout`, `actions/setup-python`) use the Node-24-native `@v6`
major tags, then confirm the resulting CI run on the feature branch fires
zero Node.js 20 deprecation warnings while both jobs still pass.

**Context.** This is `FEAT-2026-0014/T01`. GitHub deprecates Node 20
actions on 2026-06-16. Today's `ci.yml` pins `actions/checkout@v4` (Node
20) and `actions/setup-python@v5` (Node 20). The Node-24-native generation
is `actions/checkout@v6` (latest 6.0.3) and `actions/setup-python@v6`
(latest 6.2.0) — both confirmed by upstream release feeds at WU author
time. Pin style stays major-tag (`@v6`), not exact patch or SHA.

This WU edits one file, then verifies behavior via the CI log. The driver
owns all git (commit + push of the squash); after the squash, GitHub
Actions runs CI on the pushed branch and the agent must read the resulting
log via `gh run view --log`.

Reference the binding rules under `.specfuse/rules/`.

**Acceptance criteria.**
1. `grep -c 'actions/checkout@v6' .github/workflows/ci.yml` returns `1`.
2. `grep -c 'actions/setup-python@v6' .github/workflows/ci.yml` returns
   `1`.
3. `grep -cE 'actions/(checkout@v[0-5]|setup-python@v[0-5])' .github/workflows/ci.yml`
   returns `0` (no stale pins remain).
4. After the WU squash lands on the feature branch and CI completes,
   `gh run view --log --branch feat/FEAT-2026-0014-gha-node20-bump`
   (latest run for this WU's commit) shows zero matches for the regex
   `Node\.js 20|node20.*deprecat|set-output.*deprecated`. Quote the
   matched-zero-times evidence in the RESULT block.
5. The same CI run's `smoke-test` job ends with
   `conclusion: success` (confirm via `gh run view --json conclusion`).
6. **Existence check.** Before declaring complete, run:
   `grep -q 'actions/checkout@v6' .github/workflows/ci.yml && grep -q 'actions/setup-python@v6' .github/workflows/ci.yml`
   — must exit `0`. If not, emit `status: blocked`.

**Do not touch.** Exactly 1 file changes: `.github/workflows/ci.yml`. No
edits to: `scripts/`, `.specfuse/`, `pyproject.toml`, tests, other
workflow files (none exist today; if one appears, leave it alone),
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`
(tests, lint, security, coverage) still passes on the unchanged Python
surface — no Python changed. Plus AC4–AC5 (CI-log + run-conclusion
checks), which are the load-bearing verification for this WU.

**Escalation triggers.**
1. **`gh` CLI unauthenticated.** If `gh auth status` fails, emit
   `status: blocked` with `blocked_reason: "gh CLI not authenticated; AC4/AC5 cannot run"`.
   Do NOT skip AC4/AC5 — they are the point of this WU.
2. **CI run not yet complete.** If the squash-triggered CI run is still
   in progress when verification fires, poll up to 10 minutes via
   `gh run watch`. If it has not completed by then, emit
   `status: blocked` with the run URL.
3. **Deprecation warning still fires.** If AC4's grep matches anything,
   emit `status: blocked` with the matched line(s) verbatim — a
   transitive action may still be Node 20 and needs naming. Do NOT
   silently revert.
4. **CI fails for unrelated reason.** If the `smoke-test` job fails
   with errors unrelated to the action bump (test regression, network,
   etc.), emit `status: blocked` with the failure output and run URL.
   Do not paper over it.
5. **Completeness.** If `.github/workflows/ci.yml` does not show the
   `@v6` pins after your edits, emit `status: blocked` — do not claim
   complete.
