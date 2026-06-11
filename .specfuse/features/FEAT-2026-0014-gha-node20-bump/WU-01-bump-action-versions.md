---
id: FEAT-2026-0014/T01
type: implementation
model: claude-sonnet-4-6
effort: medium
status: pending
attempts: 0
duration_seconds: 306.332
cost_usd: 0.595073
input_tokens: 25
output_tokens: 12550
---

# Bump GitHub Actions to Node-24 generation in ci.yml

**Objective.** Edit `.github/workflows/ci.yml` so the two pinned actions
(`actions/checkout`, `actions/setup-python`) use the Node-24-native `@v6`
major tags. Post-merge CI-log inspection is performed manually by the
operator — see RETROSPECTIVE.md's verification section.

**Context.** This is `FEAT-2026-0014/T01`. GitHub deprecates Node 20
actions on 2026-06-16. Today's `ci.yml` pins `actions/checkout@v4` (Node
20) and `actions/setup-python@v5` (Node 20). The Node-24-native generation
is `actions/checkout@v6` (latest 6.0.3) and `actions/setup-python@v6`
(latest 6.2.0) — both confirmed by upstream release feeds at WU author
time. Pin style stays major-tag (`@v6`), not exact patch or SHA.

**Authoring note — gh-CLI-from-claude-p surface deferred.** Earlier
revisions of this WU included `gh run view --log` ACs to verify the
post-merge CI run shows no Node-20 deprecation lines. Discovery
2026-06-11: `gh auth status` fails inside the dispatched `claude -p`
subprocess (both sandboxed and `--dangerously-skip-permissions`) even
when the same `GH_TOKEN` succeeds via shell `gh` AND shell `curl
https://api.github.com/user`. Root cause unidentified. Until that
surface is fixed (see LEARNINGS entry
`[FEAT-2026-0014/T01/gh-claudeP-broken]`), this WU does NOT attempt
CI-log inspection from the agent. Verification of "no Node-20
deprecation warning" is performed by the operator at the review-CI
step described in RETROSPECTIVE.md.

This WU edits one file. The driver owns all git.

Reference the binding rules under `.specfuse/rules/`.

**Acceptance criteria.**
1. `grep -c 'actions/checkout@v6' .github/workflows/ci.yml` returns `1`.
2. `grep -c 'actions/setup-python@v6' .github/workflows/ci.yml` returns
   `1`.
3. `grep -cE 'actions/(checkout@v[0-5]|setup-python@v[0-5])' .github/workflows/ci.yml`
   returns `0` (no stale pins remain).
4. **Existence check.** Before declaring complete, run:
   `grep -q 'actions/checkout@v6' .github/workflows/ci.yml && grep -q 'actions/setup-python@v6' .github/workflows/ci.yml`
   — must exit `0`. If not, emit `status: blocked`.

**Do not touch.** Exactly 1 file changes: `.github/workflows/ci.yml`. No
edits to: `scripts/`, `.specfuse/`, `pyproject.toml`, tests, other
workflow files (none exist today; if one appears, leave it alone),
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`
(tests, lint, security, coverage) still passes on the unchanged Python
surface — no Python changed. Plus AC1–AC4 grep checks on the edited
yaml. Post-merge CI-log inspection is the operator's manual step,
out-of-loop.

**Escalation triggers.**
1. **Completeness.** If `.github/workflows/ci.yml` does not show the
   `@v6` pins after your edits, emit `status: blocked` — do not claim
   complete.
2. **Unexpected file edit.** If you find yourself editing any path
   other than `.github/workflows/ci.yml`, emit `status: blocked`. The
   yaml edit is the only change this WU authorizes.
