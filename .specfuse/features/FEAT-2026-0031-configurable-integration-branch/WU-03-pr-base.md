---
id: FEAT-2026-0031/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.20
oracle_env: github_actions_ci
produces_driver_helper: GitHubBackend.on_feature_complete
produces:
  - specfuse/loop/gh_backend.py
  - plugins/specfuse/skills/wrap-feature/SKILL.md
  - tests/test_gh_backend.py
generated_surfaces: []
---

# Target the PR at the resolved base instead of a hardcoded `main`

**Objective.** Replace the hardcoded `--base main` in the GitHub backend with the
feature's resolved base, route the PR-existence probe through the injected runner so
the whole call path is testable, and update the `wrap-feature` skill's PR command to
name the base explicitly.

**Context.** Correlation `FEAT-2026-0031/T03`. Depends on `FEAT-2026-0031/T01`, which
added `resolve_base` to `specfuse/loop/loop.py` — import and use it. Independent of
`FEAT-2026-0031/T02`; do not touch `ensure_feature_branch`.

Grounding:
- `specfuse/loop/gh_backend.py:73` — the hardcoded `"--base", "main"`, this WU's
  primary target.
- `specfuse/loop/gh_backend.py:58-61` — the `gh pr view` idempotency probe. It calls
  `subprocess.run` **directly**, bypassing `self._runner`, so a stub cannot intercept
  it. Route it through `self._runner`.
- `specfuse/loop/gh_backend.py:30-38` — the `runner` injection point.
- `tests/test_gh_backend.py:53-56` — the established `runner=stub_runner` pattern.
  Follow it; do not invent a new harness.
- `plugins/specfuse/skills/wrap-feature/SKILL.md:132,134` — `gh pr create --fill`
  with no `--base`, which silently inherits GitHub's repo default.

Scope note: `fix-bug` and `scaffold-upgrade` also hardcode `main`, but they cut
branches with **no feature folder** — no frontmatter to read a base from. They are
explicitly out of scope (see PLAN.md); do not touch them.

Binding rules apply by reference: `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`. Run gates via
`.specfuse/skills/verification/SKILL.md`.

**Acceptance criteria.**

1. `tests/test_gh_backend.py::test_pr_create_targets_resolved_base` exists and
   **fails on HEAD before this WU's edits**.
2. `on_feature_complete` passes the resolved base to `gh pr create --base`; the
   literal string `"main"` no longer appears in `gh_backend.py`. Assert with
   `grep -n '"main"' specfuse/loop/gh_backend.py` returning no match.
3. A stub-runner test asserts the `gh pr create` argv contains `--base` followed by
   the feature's declared base when `base` is set in the stored frontmatter.
4. A stub-runner test asserts that with **no** `base` declared, the `--base` value is
   `_default_branch()`'s result — the no-regression path.
5. The `gh pr view` probe at `gh_backend.py:58-61` goes through `self._runner`, not a
   direct `subprocess.run`.
6. A stub-runner test asserts the `gh pr view` probe is observed by the stub —
   proving the whole call path is now interceptable rather than half-escaping.
7. The probe's existing idempotency behavior is preserved: when a PR already exists
   for the branch, `gh pr create` is not called. Assert with a stub whose probe
   reports success.
8. `wrap-feature/SKILL.md`'s PR command names the base explicitly rather than relying
   on `--fill` to inherit the repo default.
9. `wrap-feature/SKILL.md` states where the base comes from (PLAN.md frontmatter
   `base`, else the repo default) so the agent following the prose can resolve it.
10. `tests/test_gh_backend.py::test_pr_create_targets_resolved_base` passes after
    this WU's edits.

**Do not touch.** `resolve_base` (T01 owns it), `ensure_feature_branch` (T02's file),
`plugins/specfuse/skills/fix-bug/SKILL.md`, and
`plugins/specfuse/skills/scaffold-upgrade/SKILL.md` — explicitly out of scope.
Generated directories, secrets, `.git/`. The driver owns all git operations — you
edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (tests,
coverage ≥ 90%, zero warnings, lint, security scan), plus the `doc` gate set for the
`wrap-feature/SKILL.md` edit.

**Oracle honesty — read before claiming complete.** `gh` is unreachable inside
`claude -p` (auth errors; the documented `gh`↔claude-p bug, LEARNINGS
FEAT-2026-0020/G1-CLOSE-INTERMEDIATE). Do **not** attempt to run `gh` to prove this
WU. The in-loop oracle is the stub-runner argv assertion — it proves the call shape,
not that a real PR targets correctly. Criterion 8/9's skill edit is prose an agent
follows; a grep proves the instruction is written, not that it is obeyed. Both gaps
are known and belong in the close WU's `## What the loop did NOT verify`; record them
there rather than overclaiming here.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
routing the `gh pr view` probe through `self._runner` changes the probe's return-code
semantics in a way the existing tests cannot express (the current direct
`subprocess.run` captures output; `_default_runner` may not) — that is a real
interface question, not a detail to paper over. Also block if `resolve_base` is
absent from `loop.py` (T01 incomplete), or if importing it into `gh_backend.py`
creates a circular import — report the cycle rather than duplicating the resolver.
