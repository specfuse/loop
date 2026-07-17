---
id: FEAT-2026-0031/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.20
produces_driver_helper: resolve_base, ensure_base_ref, BaseBranchError
produces:
  - specfuse/loop/loop.py
  - specfuse/loop/lint_plan.py
  - tests/test_resolve_base.py
generated_surfaces: []
model: sonnet
effort: medium
gate_set: code
driver_version: 0.3.13
started_at: 2026-07-17T12:30:13.743152+00:00
duration_seconds: 319.213
cost_usd: 1.397775
input_tokens: 60
output_tokens: 11924
---

# Add the `base` frontmatter key and the base resolver

**Objective.** Introduce an optional `base:` key in PLAN.md feature frontmatter and
the two driver helpers that turn it into a usable git ref — `resolve_base` (name)
and `ensure_base_ref` (existence) — without wiring either into a caller yet.

**Context.** Correlation `FEAT-2026-0031/T01`. See `PLAN.md` in this folder for the
shape and the draft-time decisions; this WU implements the *resolver* half only.
Callers are `FEAT-2026-0031/T02` (branch creation, staleness guard) and
`FEAT-2026-0031/T03` (PR base) — do not touch their call sites here.

Grounding:
- `specfuse/loop/loop.py:769` — `_default_branch()`, the existing remote-aware
  repo-default detector. It is the resolver's fallback; do not modify it.
- `specfuse/loop/lint_plan.py:38` — `REQUIRED_FEATURE_KEYS`. `base` is **optional**
  and must NOT be added to that set.
- `specfuse/loop/loop.py:1028` — `ensure_feature_branch`, T02's target. Read for
  context; leave unmodified.
- `FeatureBranchError` in `loop.py` — the existing error shape to mirror.

Binding rules apply by reference: `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`. Run gates via
`.specfuse/skills/verification/SKILL.md`.

**Acceptance criteria.**

1. `tests/test_resolve_base.py::test_frontmatter_base_wins_over_default` exists and
   **fails on HEAD before this WU's edits** (the symbol does not yet exist).
2. `resolve_base(feat_fm: dict) -> str | None` is added to `specfuse/loop/loop.py`
   and returns frontmatter `base` when set and non-empty.
3. `resolve_base` returns `_default_branch()` when `base` is absent, empty, or
   whitespace-only.
4. `resolve_base` returns the current branch when `base` is absent AND
   `_default_branch()` returns `None`.
5. `BaseBranchError` is added to `specfuse/loop/loop.py`, mirroring
   `FeatureBranchError`'s shape.
6. `ensure_base_ref(base: str) -> None` is added to `specfuse/loop/loop.py` and
   returns without any network call when `git rev-parse --verify <base>` succeeds.
7. `ensure_base_ref` runs `git ls-remote --exit-code origin <base>` only when the
   local ref is absent.
8. When `ls-remote` reports the base exists on the remote, `ensure_base_ref` runs
   `git fetch origin <base>` and prints one line naming what it fetched and why.
9. When `ls-remote` reports the base does NOT exist on the remote,
   `ensure_base_ref` raises `BaseBranchError` naming the base as a probable typo and
   listing candidate local branch names.
10. When `ls-remote` itself fails (offline / auth), `ensure_base_ref` raises
    `BaseBranchError` whose text distinguishes "remote unreachable" from the typo
    case — the two messages must not be interchangeable.
11. `lint_plan.py` rejects a `base` key present but empty / whitespace-only /
    non-string, with an error naming the feature and the key.
12. `lint_plan.py` still passes on a feature with **no** `base` key — assert against
    an existing feature folder in `.specfuse/features/` as a regression fixture.
13. `base` is NOT added to `REQUIRED_FEATURE_KEYS`.
14. `tests/test_resolve_base.py::test_frontmatter_base_wins_over_default` passes
    after this WU's edits.
15. Every `ensure_base_ref` path above is covered by a test using **real git** in a
    tmpdir, with a local bare repo as `origin`. No network, no mocking of git itself.

**Do not touch.** `_default_branch()` (loop.py:769) and its `_persist_scaffold_sync`
caller (loop.py:829) — this WU adds a consumer, it does not change the detector.
`ensure_feature_branch` (loop.py:1028) and `gh_backend.py` — T02's and T03's files.
Generated directories, secrets, `.git/`. The driver owns all git operations on the
repo — you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (tests,
coverage ≥ 90%, zero warnings, lint, security scan). Plus explicit symbol-existence
checks, since the code gate cannot detect a missing symbol no test names:

```
python3 -c "from specfuse.loop.loop import resolve_base, ensure_base_ref, BaseBranchError"
```

Plus the regression fixture in criterion 12: `python3 -m specfuse.loop.lint_plan
.specfuse/features/FEAT-2026-0030-events-jsonl-sanitize` still exits 0.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`resolve_base`, `ensure_base_ref`, or `BaseBranchError` is absent from the files you
edited — do not claim complete. Also block if `_miniyaml` cannot round-trip the
`base` key without a parser change (that is a separate WU, not a silent widening
here), or if the lint rejection in criterion 11 would also reject any existing
feature folder — a guard that fails on legacy artifacts is the spurious-block
pattern in LEARNINGS FEAT-2026-0015/G2-CLOSE; report it instead of weakening the
regression fixture.
