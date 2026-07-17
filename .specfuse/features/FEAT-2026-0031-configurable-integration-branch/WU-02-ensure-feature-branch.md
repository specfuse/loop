---
id: FEAT-2026-0031/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.60
produces_driver_helper: ensure_feature_branch
produces:
  - specfuse/loop/loop.py
  - tests/test_ensure_feature_branch_base.py
generated_surfaces: []
model: sonnet
effort: medium
gate_set: code
driver_version: 0.3.13
started_at: 2026-07-17T12:35:33.147433+00:00
duration_seconds: 368.912
cost_usd: 1.158896
input_tokens: 56
output_tokens: 13922
---

# Cut the feature branch from the resolved base and re-anchor the staleness guard

**Objective.** Wire `resolve_base` / `ensure_base_ref` into `ensure_feature_branch`
so the feature branch is created from the declared base, the staleness guard measures
against that base, and the guard's error text is readable by an operator who does not
know git.

**Context.** Correlation `FEAT-2026-0031/T02`. Depends on `FEAT-2026-0031/T01`, which
added `resolve_base`, `ensure_base_ref`, and `BaseBranchError` to
`specfuse/loop/loop.py` — import and use them; do not re-implement or alter them.
See `PLAN.md` in this folder for the draft-time decisions behind the re-anchor.

Grounding:
- `specfuse/loop/loop.py:1028` — `ensure_feature_branch`, this WU's target.
- `specfuse/loop/loop.py:1104` — the bare `checkout -B <branch>` this WU gives a base.
- `specfuse/loop/loop.py:1070-1085` — the `merge-base --is-ancestor <branch> HEAD`
  guard and the three-option hint this WU re-anchors and rewrites.
- `specfuse/loop/loop.py:1091-1103` — the dirty-tree allowlist. Unchanged by this WU.

Why the re-anchor: on a configured base the current HEAD-anchored check fires
spuriously (the operator standing on the default branch, feature based elsewhere),
and its hint advises `git rebase {current}` — which would rebase the feature onto the
*wrong* base. The hint is more dangerous than the false alarm.

Binding rules apply by reference: `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`. Run gates via
`.specfuse/skills/verification/SKILL.md`.

**Acceptance criteria.**

1. `tests/test_ensure_feature_branch_base.py::test_branch_is_cut_from_declared_base`
   exists and **fails on HEAD before this WU's edits**.
2. `ensure_feature_branch` calls `resolve_base(feat_fm)` and, when a base resolves,
   `ensure_base_ref(base)` before any checkout.
3. Branch creation passes the base explicitly: `git checkout -B <branch> <base>`.
4. A test using **real git** in a tmpdir asserts that with `base: release/2.0`
   declared and HEAD standing on the default branch, the created feature branch's
   `merge-base` with `release/2.0` equals `release/2.0`'s tip — i.e. it was cut from
   the base, not from HEAD.
5. The staleness check is `git merge-base --is-ancestor <branch> <resolved_base>` —
   HEAD is no longer the anchor.
6. A test asserts a feature with **no** `base` key still resolves via
   `_default_branch()` and its branch is cut from the default branch — the
   no-regression path for every existing feature.
7. The `FeatureBranchError` text for a diverged branch names the **resolved base**,
   not `current`.
8. The rebase hint reads `git rebase <resolved_base>` — not `git rebase {current}`.
9. The `git branch -D <branch>` suggestion is **removed** from the error text. A
   work-destroying command must not be offered to an operator who cannot evaluate
   it; assert its absence with a test on the message string.
10. The rewritten error text states, in plain language and without git jargon, what
    happened and the one safe action to take. Assert the message contains the branch
    name, the base name, and no `-D` flag.
11. The dirty-tree allowlist behavior (`_expected_flip_paths` |
    `_scaffold_managed_dirty`) is unchanged — assert with a regression test that
    unexpected tracked edits still raise.
12. `tests/test_ensure_feature_branch_base.py::test_branch_is_cut_from_declared_base`
    passes after this WU's edits.
13. A `BaseBranchError` raised by `ensure_base_ref` propagates out of
    `ensure_feature_branch` without being caught and reshaped into a
    `FeatureBranchError` — the base cause must survive to the operator.

**Do not touch.** `resolve_base` / `ensure_base_ref` / `BaseBranchError` — T01 owns
them; consume, don't edit. `gh_backend.py` and `wrap-feature/SKILL.md` — T03's files.
`_default_branch()`. Generated directories, secrets, `.git/`. The driver owns all git
operations on the repo — you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (tests,
coverage ≥ 90%, zero warnings, lint, security scan). All base-path tests must use
real git in a tmpdir with a local bare repo as `origin` — no network, no mocking git.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
re-anchoring the guard to the base would break an existing test that asserts
HEAD-anchored behavior AND the fix is not obviously a test-intent update — that
would mean the re-anchor has a consequence this plan did not foresee; report it with
the failing test named. Also block if `ensure_feature_branch` cannot reach a base
ref without a network call on the **happy path** (a declared base already present
locally must never trigger a fetch — see PLAN.md), or if `resolve_base` is absent
from `loop.py` (T01 incomplete — do not re-implement it here).
