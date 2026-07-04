<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0029: One-command Specfuse scaffold upgrade skill

Single gate, terminal `close`. The feature ships the `scaffold-upgrade` Claude Code
skill: a pure-markdown flow wrapping `specfuse upgrade [--dry-run] <target>` in the
git choreography (branch off fresh `origin/main` → upgrade → commit → push → PR →
watch CI → merge-gate), with the one load-bearing decision — "given CI status and
per-feature conformance, is it safe to merge?" — extracted into a unit-tested
helper.

## Per-WU outcome

### T01 — merge-safety gate helper (`.specfuse/scripts/upgrade_merge_gate.py`)

- **What worked.** Final shape is clean: `decide(ci_all_green, feature_reports)`
  returns `("merge", "")` only on green CI + all-`ok` reports, `("halt", reason)`
  otherwise; `decide(True, [])` fail-safes to `halt` (never merge on absence of
  evidence); `collect_reports(repo_root)` shells `lint_plan.py` once per feature
  folder. Table-driven tests + tmp-repo coverage all green.
- **What failed.** The costliest WU by far — **5 attempts across 3 dispatches**.
  (1) First dispatch blocked: the WU's original framing pointed at a `specfuse
  upgrade` "health report" string format that is **not implemented anywhere** in
  the repo (only prose in `feature-conversion/SKILL.md`). The agent correctly
  refused to invent a parser grammar. (2) Re-scoped to a Python data-structure
  contract (`{"feature","ok","detail"}`) instead of a parsed report string;
  next dispatch then spun 3 attempts on a **sandbox** failure — `mktemp -d`
  returned `Operation not permitted`, so the tmp-repo `collect_reports` test could
  not build its fixture. (3) Third dispatch passed in one attempt once the tmp-dir
  strategy worked under the sandbox.
- **Final cost.** ~$3.50 across all attempts (planned $1.75) — a **2× overrun**,
  entirely attributable to the block + spin, not to the final passing work.

### T02 — author the skill (`.specfuse/skills/scaffold-upgrade/SKILL.md`)

- **What worked.** One attempt, clean pass. Pure-markdown skill modeled on
  `wrap-feature`: `## When to invoke`, Dry-run section (states plainly an upgrade
  *would be performed*, no writes), Live flow (dirty-tree/`gh`/CLI refusal →
  fetch + `chore/…` branch off `origin/main` → upgrade → commit → push `--no-verify`
  → `gh pr create` → watch CI → call the T01 helper → merge/halt), Target
  subsection, Hard rules, and `## What this skill does NOT do`. Carried the
  explicit `Red-test exempt:` line — the red→green proof lives in T01 and T03.
- **What failed.** Nothing.
- **Final cost.** ~$0.49 (planned $1.75) — well **under** budget; prose WU with
  no code gate to iterate against.

### T03 — wire and register (`.claude/skills/` symlink + both `docs/skills.md`)

- **What worked.** Final dispatch added the forward discovery symlink
  `.claude/skills/scaffold-upgrade → ../../.specfuse/skills/scaffold-upgrade`
  (correct direction — the #56 inversion bug avoided), listed the skill in **both**
  `docs/skills.md` copies, and kept the live source-layout invariant (bats test 3)
  green.
- **What failed.** First dispatch **blocked** correctly: the agent chased AC4 into
  a `scaffold.py` skill-deploy defect (`init()`/`upgrade_specfuse()` don't deploy
  `.specfuse/skills/` for *any* skill) — pre-existing, out of scope, driver-internals
  territory. Rather than weaken the regression, it escalated. The WU was then
  **re-scoped** (commit da81c27) to the plugin skill-delivery model — skills ship via
  the Claude Code plugin, not the pip scaffold — removing the false dependency on the
  scaffold-deploy path. Re-dispatch passed in one attempt.
- **Final cost.** ~$2.10 across both dispatches (planned $1.25) — overrun driven by
  the first-dispatch block on the mis-scoped AC4.

## Gate-level summary

The roadmap goal is met: `scaffold-upgrade` exists, is wired for discovery,
documented in both skill indexes, and its one non-trivial decision is verified by
unit tests rather than trusted to prose. The full repo suite passes (1068 tests,
`OK (skipped=2)`). Two of three WUs required a human re-scope before they could
pass — both re-scopes were **correct** interventions (an invented report format and
a mis-attributed scaffold defect), not busywork. The agents blocked rather than
papering over, which is the intended behavior.

## Surprises

1. **The health-report format was a phantom dependency.** The feature was drafted
   assuming `specfuse upgrade` emits a parseable `FAIL <feature>` health report;
   it does not — the signal that already exists in-repo is `lint_plan.py`'s
   per-feature exit code. T01's block surfaced this on attempt 1 and the WU was
   corrected to a data-structure contract. A pre-dispatch check of "does the
   artifact this parser consumes actually exist?" would have caught it at draft.
2. **Sandbox `mktemp` denial burned a whole 3-attempt spin.** T01's tmp-repo test
   fixture hit `mktemp: Operation not permitted` under the loop sandbox — not a
   logic bug, an environment limit — yet it consumed the full spinning budget
   before the re-arm dispatch found a working tmp-dir strategy.
3. **T03's AC4 pointed at a real but out-of-scope defect.** The scaffold does not
   deploy `.specfuse/skills/` for any skill; the agent was right that this is a
   separate defect, and the fix was to re-scope the WU to the plugin-delivery model
   (which never depended on scaffold-deploy) rather than touch driver internals.

## Cost analysis

Reconciled from `events.jsonl` `attempt_outcome` rows (`cost_usd` field) against
`planned_cost_usd` in PLAN.md and per-WU frontmatter.

| WU  | Planned | Actual | Attempts (dispatches) | Delta |
|-----|--------:|-------:|-----------------------|------:|
| T01 | $1.75 | $3.50 | 5 (3) — 1 blocked, 3 spin-failed, 1 passed | **+$1.75 (+100%)** |
| T02 | $1.75 | $0.49 | 1 (1) — passed | **−$1.26 (−72%)** |
| T03 | $1.25 | $2.10 | 2 (2) — 1 blocked, 1 passed | **+$0.85 (+68%)** |
| **Implementation subtotal** | **$4.75** | **$6.09** | | **+$1.34 (+28%)** |
| G1-CLOSE | $1.25 | (billed by driver post-session) | this WU | — |
| **Feature total (planned)** | **$6.00** | **≥$6.09** before close | | overrun |

Per-attempt `cost_usd`: T01 = 0.7146 + 0.8503 + 0.3291 + 0.3687 + 1.2410; T02 =
0.4867; T03 = 1.7570 + 0.3465. Implementation actual = **$6.0939**.

**Delta named.** The $1.34 (+28%) implementation overrun is fully explained by the
two blocked-then-rescoped WUs: T01's phantom health-report dependency + sandbox
`mktemp` spin ($1.75 over), and T03's mis-scoped AC4 block ($0.85 over). T02's
$1.26 underrun (a clean single-attempt prose WU) offset roughly half of it. The
final *passing* work on every WU was cheap; the overrun is 100% cost-of-discovery
on two draft-time mis-scopes, not cost of the delivered code.

## What the loop did NOT verify

- **The skill's live git choreography against a real target repo.** The
  `scaffold-upgrade` skill's outward-facing steps — `git fetch`/branch off
  `origin/main`, `specfuse upgrade`, commit, `git push`, `gh pr create`, watch CI
  to green, squash-merge — cannot run against a live target repo inside the loop
  sandbox (no network-mutating GitHub access; `gh` auth round-trips are known-broken
  under `claude -p`, see LEARNINGS `gh-claudeP-broken`). **Why deferred:** these are
  irreversible external mutations that must not fire from the driver's subprocess
  loop. **Where verified:** operator-side, on the skill's first real use against an
  actual project. The in-loop proof is limited to (a) T01's helper unit tests — the
  one piece of real decision logic, fully covered — and (b) T03's deploy/discovery
  bats (`init_skills_idempotent.bats` test 3, source-layout invariant).

This list has **1 entry** (≤ 2, and well under 30% of the gate's criteria) — the
single-gate sizing is appropriate; no sizing concern to flag below.

## What I'd change

- **Verify parser inputs exist at draft time.** T01's block came from drafting a
  parser for a report format that isn't implemented. A draft-time check — "grep the
  repo for the artifact this WU consumes; if absent, the contract is a data
  structure, not a parse" — would have saved the first blocked dispatch (~$0.71).
- **Flag sandbox tmp-dir dependence in the WU spec.** T01 spun 3 attempts on
  `mktemp: Operation not permitted`. Any WU whose tests build a tmp git repo should
  note the sandbox tmp-dir constraint up front (use the repo's established
  `TemporaryDirectory`/`$TMPDIR` fixture pattern) so the agent doesn't rediscover
  the limit under the spinning budget.
- **Scope AC4-style claims to the WU's own delivery model.** T03's first block was a
  mis-attributed dependency on `scaffold.py` skill-deploy; the skill actually ships
  via the plugin. Naming the delivery model (plugin vs pip scaffold) in the WU
  Context up front would have avoided the block. The re-scope (commit da81c27) was
  the right fix and is now reflected in the WU body.
- **Single-gate `close` sizing was correct.** One gate, three substantive WUs plus
  a terminal `close` — proportionate to an orchestration-only feature with one
  tested helper. No change warranted here.
