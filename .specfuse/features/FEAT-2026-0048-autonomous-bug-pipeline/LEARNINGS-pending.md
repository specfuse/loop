# LEARNINGS-pending

**What this file is.** This feature runs under `autonomy_default: auto` — a
closing WU here dispatches without a human reading the gate first. Under
`review` or `supervised`, a promoted lesson lands straight in the repo's
`.specfuse/LEARNINGS.md`, because a human already reviewed the gate that
produced it. Under `auto` nobody did, so the lesson stages here instead: in
this feature directory, not in the repo-wide file that every future feature's
planning step loads. A closing WU's own post-pass check
(`assert_learnings_staged_under_auto`) refuses to pass if its diff touches
`.specfuse/LEARNINGS.md` while this feature is in `auto` mode — this file is
where those lessons go instead.

**How a human promotes an entry from here.** At PR review for this feature:

1. Read each entry below. Judge it the way you would judge any
   `LEARNINGS.md` candidate — does it generalize into a rule that should
   change how a FUTURE work unit, in any feature, is written or executed?
2. For each entry you accept, copy it into `.specfuse/LEARNINGS.md` (below
   the `<!-- lessons work units append below this line -->` marker, in that
   file's existing entry format) in the same commit or a follow-up commit to
   the PR branch.
3. For each entry you reject or narrow, leave it here — do not delete it
   silently; a short note on why it didn't generalize helps the next person
   who drafts a similar feature.
4. This file is not read by planning. Nothing here shapes another feature
   until a human has done step 2.

## Entries

<!-- closing work units append below this line -->

- [FEAT-2026-0048/G1-CLOSE] **A guardrail whose evidence test is a hardcoded
  path prefix is a guardrail about *this* repository, and shipping it in a
  scaffold makes it silently inoperative everywhere else.** This feature's
  test-first guardrail is `any(path.startswith("tests/"))`. That is exactly
  what `PLAN.md`'s assumed decision 5 specified, and the reasoning behind it —
  a semantic judgment of test quality would be a model-authored approval,
  which FEAT-2026-0053's organizing principle forbids — is still right. What
  the decision did not price is that `specfuse` is a scaffold other projects
  install. In a project whose tests live in `spec/`, `src/**/__tests__/`, or
  alongside sources as `*_test.go`, no diff can satisfy the guardrail, so the
  bug lane never merges anything — and it reads in review as "the guardrails
  are working", because a permanently-declining guardrail and a correctly-
  declining one look identical from outside. Rule: when a guardrail's
  predicate contains a repository-shaped literal (a path prefix, a branch
  name, a label, a directory layout), either make it a dial in the policy file
  or state in the WU body that the guardrail is deliberately this-repo-only.
  The failure mode is not a false merge; it is a lane that never runs and
  never says why.

- [FEAT-2026-0048/T04] **A code path that writes a label must be reconciled
  against the label registry in the same work unit, or the failure path is the
  one that fails.** `run_bug_lane`'s declining path calls
  `gh pr edit --add-label <reason>` with `check=True`, where `<reason>` is one
  of six constants the WU introduced. None of the six is in
  `specfuse/loop/labels.py`'s `LABEL_REGISTRY`, so `provision_labels` never
  creates them, and on a repository where they do not exist `gh` exits
  non-zero and the runner raises. The unit's own acceptance criterion — "the
  PR is labeled with the guardrail's reason constant and left open" — passes,
  because the test injects a runner that accepts any label string. The
  asymmetry is what makes this general: the *happy* path here is "merge", which
  is well covered, and the *declining* path is the safe outcome nobody
  stress-tests against real infrastructure. The comparable precedent,
  `autofix_run._apply_failed_label`, is also `check=True` — but it writes a
  registered label, so it works. Rule: a WU that introduces a new label
  literal must either add it to `LABEL_REGISTRY` in the same unit or make the
  write best-effort the way `triage.apply_triage` already does; and a WU whose
  acceptance criteria are all satisfiable against an injected fake should say
  in its body which of them a real backend could still refuse.

- [FEAT-2026-0048/G1-CLOSE] **The solo-drafting cost signature recurred
  exactly, which promotes it from an observation to a rule.** FEAT-2026-0044's
  close recorded that all four of its solo-drafted units came in more than 50%
  under plan (−69%, −55%, −62%, −80%) and diagnosed the cause as accounting
  rather than efficiency: a solo-drafted WU body front-loads every load-bearing
  string, so the unit spends nothing on discovery, and discovery is what an
  interview-drafted estimate implicitly prices. FEAT-2026-0048 was drafted in
  the same unattended session and reproduced the signature: −67.8%, −79.2%,
  −79.3% on the three units whose plan handed them module path, function
  signature, constants, and the file to copy the shape from — and −20.1% on
  `T04`, the one unit that had to build a mechanism (`pr_ci_conclusion`) the
  plan could not hand it. Two features, eight units, one control that behaves
  differently for a nameable reason. Rule: when a plan's WUs quote their
  load-bearing strings verbatim and name the existing file to copy the shape
  from, estimate them as transcription-plus-tests, not as
  design-plus-implementation. This is not harmless bookkeeping — over-planned
  unit costs inflate gate budgets, and the gate budget is the control that is
  supposed to stop a runaway feature. A gate budgeted at $26.00 that reliably
  spends $11 is a brake with slack in the cable.

- [FEAT-2026-0048/G1-CLOSE] **`T01`-as-schema-verifier worked, and the reason
  it worked is worth copying — but so is the near-miss.** This feature was
  drafted before FEAT-2026-0044 shipped the schema it builds on, and its `T01`
  existed purely to verify the shipped schema against the assumed table and
  escalate on divergence rather than adapt. Every row held; T01 did not
  escalate; the pattern is cheap ($0.81) and it is the right mitigation for
  "drafted against a file that does not exist yet". The near-miss: the plan's
  assumed table wrote the dial values as `off | on` unquoted, and the shipped
  schema requires them quoted, because this repo's `_miniyaml` rejects a bare
  `off` rather than coercing it. That divergence cost nothing only because
  every criterion in this feature was expressible against the *parsed* value.
  Had one been written as a grep for the literal `automerge: off`, T01 would
  have escalated on a cosmetic difference or, worse, adapted to it. Rule: when
  a WU verifies an assumed schema, write its assertions against parsed values,
  not against source spellings — and when a plan quotes a config block as an
  interface, run that block through the project's own parser before shipping
  the WU body, because a later feature will be drafted against the literal.
