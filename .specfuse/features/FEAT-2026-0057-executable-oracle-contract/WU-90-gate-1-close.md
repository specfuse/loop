---
id: FEAT-2026-0057/G1-CLOSE
type: close
status: pending
attempts: 0
re_arm_count: 1
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
oracles: [oracles]
verdict: partially_met
produces:
  - .specfuse/features/FEAT-2026-0057-executable-oracle-contract/RETROSPECTIVE.md
  - .specfuse/LEARNINGS.md
duration_seconds: 2005.895
cost_usd: 10.687821
input_tokens: 13472
output_tokens: 103947
---

# Close gate 1 — retrospective, lessons, docs, and terminal verdict

**Objective.** Close the feature: re-run its oracles fresh, judge the definition
of done, record what was learned, and write the terminal verdict.

**Context.** Correlation ID `FEAT-2026-0057/G1-CLOSE`, the terminal close for
this feature's only gate. `FEAT-2026-0057/T01`, `/T02`, `/T03`, and `/T04` are
`done`. Read `PLAN.md` for the framing, the scope boundary, the draft-time
decisions, and the *Off-plan record* section; read `GATE-01.md` for the definition
of done you are judging against.

**This is the second pass.** The first close returned `partially_met` and its
`RETROSPECTIVE.md` is on disk — read it first. It found that T01–T03 built the
mechanism and nothing called it, and it raised four follow-ups. T04 was added to
discharge FU-1 and FU-2. **Your job includes re-running that close's own probes
and reporting whether they now return the opposite result.** Rewrite
`RETROSPECTIVE.md` for the feature as a whole rather than appending to it; the
first pass's findings are history to be reflected, not a document to preserve.

**You have oracle output injected into this prompt.** This work unit declares
`oracles: [oracles]`, so if T04 landed correctly you will find a section headed
`## Captured oracle output (pre-dispatch)` below, carrying `git log --oneline -20`
and `git --no-pager diff --stat main` — run for you, before this session started.
Read it instead of re-deriving that information; your **Do not touch** rule
forbids you from running `git` yourself, and that set exists precisely to serve
you the answer. **If that section is absent, say so in the retrospective** — its
absence is the FU-2 defect surviving, and it is a finding, not an inconvenience.

`auto_close_disabled: true` is deliberate and load-bearing. This feature adds two
frontmatter keys to the scaffold's work-unit template, which is a consumer-visible
contract change for every downstream project. FEAT-2026-0031's lesson is that
auto-close silently voids a close unit's `produces` contract and every acceptance
criterion in its body — a close with `attempts: 0` means this body never ran, and
its criteria should be read as *unfulfilled* rather than as evidence.

Binding rules apply by reference: `.specfuse/rules/close-discipline.md`,
`.specfuse/rules/result-contract.md`, `.specfuse/rules/never-touch.md`,
`.specfuse/rules/correlation-ids.md`.

> Run `specfuse-lint --closing` and confirm it exits 0 before this work unit
> reports `complete` — see `.specfuse/rules/close-discipline.md` §4.

**Close obligations.**

**Acceptance criteria.**

1. **Oracles re-run fresh.** Every oracle this feature's criteria name is re-run
   with its full command and its exit code read directly — never a producing work
   unit's self-report. That includes each scoped red→green test named in T01, T02,
   and T04, the symbol-existence checks in all four units, and the `code` gate set.
1b. **The first close's negative probes are re-run, and their new results
   recorded.** The prior `RETROSPECTIVE.md` proved the defect three ways: the
   `WorkUnit` dataclass field list, a real WU file declaring both keys loaded
   through `load_wu` and passed to `run_pre_dispatch`, and a repo-wide caller grep
   for the five produced symbols. Re-run all three. FU-1 and FU-2 are discharged
   only if the field list now contains `prep` and `oracles`, the probe returns
   non-empty `prep_results` and `oracle_results`, and the grep finds callers in
   `specfuse/loop/loop.py`. Report the actual output of each, not a summary of it.
2. **Cost analysis.** `RETROSPECTIVE.md` contains a `## Cost analysis` heading,
   written with exactly that text. Under it, actual spend is reconciled against
   `planned_cost_usd: 18.50` and against each unit's own estimate (T01 $4.00,
   T02 $3.50, T03 $2.50, T04 $3.50, this close $5.00). Read `events.jsonl` first;
   where it is silent, read the work unit's own frontmatter and say which source
   each figure came from. **The first pass's close cost $10.69 over 2005s** — that
   figure exists in `WU-90`'s frontmatter but was absent from `events.jsonl` when
   the first retrospective was written (FU-3), so state the feature's lifetime
   cost across both passes rather than this pass alone. `re_arm_count: 1` on this
   unit means the driver folded the prior cycle into `cumulative_cost_usd`; use
   the lifetime figure. Name any unit whose actual diverged from plan by more than
   a third, and say why. The heading is checked after dispatch, so omitting it
   costs a full re-attempt.
3. **Deferred-verification list.** Every acceptance criterion not verified
   in-loop is listed with the criterion, the reason it could not be verified
   here, and where it actually gets checked — or the section contains exactly
   `(nothing — every acceptance criterion was verified in-loop)`.
4. **Consumer-visible contract changes.** Enumerate every addition, removal, and
   rename across the three producing units by **grepping the packaging manifests
   and shipped templates** for each changed path, and state the blast radius you
   measured rather than the one the plan predicted. FEAT-2026-0060's lesson cuts
   both ways: the assumption that overstates risk when a file is internal
   understates it when a file really is shipped. The specific paths to check are
   the `prep` / `oracles` keys against `.specfuse/templates/WU.template.md`, and
   the `oracles` set against the shipped `verification.yml.example` and the
   scaffold manifests. Block on human acknowledgment, or write exactly
   `n/a — no consumer-visible contract change`.
5. **Verdict against the definition of done.** Judge GATE-01.md's definition of
   done criterion by criterion and record the verdict. On `met_locally` or
   `partially_met`, write a named record per unmet criterion — the criterion, why
   it is unverifiable here, the exact re-run condition that upgrades it to `met`,
   and a `kind:` line written as `- **kind:** \`<value>\`` with one of
   `acceptance-discharged`, `externally-verifiable-later`, `routed-finding`,
   `inherent`.
6. **Lessons.** Candidate lessons are promoted to `.specfuse/LEARNINGS.md`. The
   existing-mechanism search is the obvious candidate — a roadmap entry whose goal
   was ~70% already shipped, found by three greps — but write what the run
   actually taught, not what this line predicts.
7. `specfuse-lint --closing` exits 0 before this work unit reports `complete`.

Do **not** add a criterion flipping `PLAN.md status` to `done`. The driver owns
the terminal flip: `fire_terminal_flips` writes it, gated on
`verdict_permits_terminal_flips`, on both the dispatched-close and the
agent-less auto-close path (FEAT-2026-0023/T01, closes #49). A manual flip is
redundant, and gating it with the driver is what leaves `PLAN.md` `active` on a
hedged verdict.

**Do not touch.**

- Production source under `specfuse/loop/` and the tests under `tests/`. This is
  a reflective unit: it re-runs oracles and records findings. A defect found here
  is a finding to route, not a fix to make.
- Other features' folders under `.specfuse/features/`.
- Generated directories, secrets (`.env`, `*.pem`, `*.key`, `credentials.json`),
  and `.git/` internals. See `.specfuse/rules/never-touch.md`.
- **The driver owns all git.** You edit files only — never run `git`.

**Verification.**

- The `plannext` gate set as declared in `.specfuse/verification.yml`.
- `specfuse-lint --closing` exits 0 — the registry of required sections lives in
  `specfuse/loop/closing_requirements.py` and the skeleton is pre-created at
  dispatch, so the lint is the check rather than a restated list of headings here.

**Escalation triggers.**

- If a re-run oracle disagrees with a producing unit's self-report, emit
  `status: blocked` with both results. A close that reconciles a disagreement in
  the agent's head is the failure this ceremony exists to prevent.
- If a consumer-visible contract change is found that no work unit declared, block
  for human acknowledgment rather than recording it and proceeding.
- If the definition of done cannot be judged because an oracle cannot run in this
  environment, record it in the deferred-verification list and hedge the verdict —
  do not claim `met` on evidence from the wrong environment. `oracle_env` on the
  producing units names where each oracle was intended to run.
- Blocked is a respectable outcome (`.specfuse/rules/result-contract.md` rule 4).
