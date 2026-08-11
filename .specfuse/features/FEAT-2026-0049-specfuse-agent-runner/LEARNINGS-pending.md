# LEARNINGS-pending

**What this file is.** This feature runs under `autonomy_default: auto` — a
closing WU here dispatches without a human reading the gate first. Under
`review` or `supervised`, a promoted lesson lands straight in the repo's
`.specfuse/LEARNINGS.md`, because a human already reviewed the gate that
produced it. Under `auto` nobody did, so the lesson stages here instead: in
this feature directory, not in the repo-wide file that every future feature's
planning step loads. A closing WU's own post-pass check refuses to pass if its
diff touches `.specfuse/LEARNINGS.md` while this feature is in `auto` mode —
this file is where those lessons go instead.

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

## Format

```
- [FEAT-YYYY-NNNN/G1] Implementation WUs must name the module a new route/handler
  lives in; "add it to the router" cost a blocked attempt when no router existed yet.
```

## Entries

<!-- closing work units append below this line -->

- [FEAT-2026-0049/G3-CLOSE-INTERMEDIATE] **A gate whose deliverables cannot be
  exercised against the repository that ships them must state its ceiling per
  criterion at draft time, not per gate at close time.** Gate 3's review wrote
  an excellent four-row "what cannot be proven here" table before the gate ran.
  Checked against what the gate actually built, that table was *right but
  incomplete*: it missed that `load_monitoring_config` had never parsed an
  operator-authored config, that `--monitoring-config`'s default path had never
  resolved to a file that exists, and that the `diagnose:` dial's first consumer
  had only ever read a fixture value. Ten criteria were fixture-limited; the
  gate-scope table named four. Rule: when a gate's definition of done says "this
  cannot be exercised here", the *close* must walk the criteria one at a time and
  ask "what stood in for the live surface, and what would replace it" — a
  gate-scope paragraph, however well written, systematically undercounts. The
  cost of getting it wrong lands at the terminal verdict, where the list has to
  be re-derived from a diff.

- [FEAT-2026-0049/G3-CLOSE-INTERMEDIATE] **A test whose name asserts an
  invariant its body no longer checks is worse than a missing test, and gates
  that supersede an earlier gate's criterion create them systematically.** T05's
  criterion 7 said "the registry returns `()` in this unit", and its test asserts
  `tuple(default_providers()) == ()`. Five providers later that test is still
  green — because `default_providers()` returns `()` when given no `repo`, not
  because the registry is empty. Nothing is broken; the registration is covered
  by five separate per-provider tests. But `test_default_providers_returns_empty_registry`
  now reads as an emptiness invariant to anyone scanning the file, which is
  exactly how a stale assertion survives. Rule: when a later WU deliberately
  supersedes an earlier WU's acceptance criterion, the superseding WU should say
  so and either rename or delete the test that encoded the old state. "The test
  still passes" is not evidence the criterion still means what it said.

- [FEAT-2026-0049/G3-CLOSE-INTERMEDIATE] **An acceptance criterion of the form
  "test X exists and fails on HEAD before this WU runs" is only half
  re-verifiable, and a close that inherits it should be told which half.** Every
  one of this feature's eleven substantive work units opens with that criterion.
  The green-after half re-runs in seconds; the red-before half depends on a tree
  state that no longer exists, and a closing session runs no `git` command by
  contract, so it can never be re-proven downstream. The same applies to
  "no file under `<dir>` is edited", which is a diff claim four criteria here
  carry. Rule: split the criterion, or mark the historical half explicitly at
  draft time, so a close reconciling deferred verification does not have to
  choose between silently claiming it and looking like it missed something. The
  driver's produces-vs-diff guard already owns the diff half at squash time;
  say so in the WU rather than leaving the close to argue it.

- [FEAT-2026-0049/G3-CLOSE-INTERMEDIATE] **When a plan's own review argues that
  a behaviour "will be visible in the same run", write the fixture-level test
  for it in the same gate — an ordering test does not cover a handoff.** Gate 3
  ranked findings-diagnose ahead of triage on the specific argument that a
  diagnosis posted at iteration 3 becomes visible at iteration 4, because the
  autofix provider reads comments live at `advertise()`. The ranking is tested.
  The handoff is not — no test drives both providers through the run loop
  together, in any environment. The gate review had recorded this as needing a
  live run on a repo with two findings, which made an available fixture test
  look like an impossible live one. Rule: before deferring a behaviour to
  "needs a live run", ask what fraction of it a test double could reach today.
  Deferring the whole claim when only part of it is genuinely environment-bound
  is how a testable gap gets filed as an untestable one.

- [FEAT-2026-0049/G4-CLOSE] **A "every work unit passed first attempt" claim in
  a planning artifact must be recomputed from `events.jsonl` at each close, not
  copied forward from the previous gate's prose.** Three artifacts on this
  feature — `PLAN.md` § "A note on `planned_cost_usd`", `GATE-03-REVIEW.md`, and
  `GATE-04-REVIEW.md` § "On the estimates" — say "eleven substantive work units,
  every one a first-attempt pass." T06 failed its first attempt
  (`attempt_outcome`, `failure_class: tests`, $0.70) and its own frontmatter
  reads `attempts: 2`. The claim was not decorative: it was the evidence for a
  cost-estimating decision ("eleven observations is a distribution, not an
  outlier"). It survived two gates because each `plan-next` quoted the previous
  one instead of re-reading the event log, which is the cheapest possible check
  — one pass over a file the session already has open. Rule: any claim of the
  form "N units, all clean" in a gate review or PLAN note is derived data;
  derive it, and cite the file you derived it from.

- [FEAT-2026-0049/G4-CLOSE] **On a feature whose closing units run `opus`/`high`
  and whose implementation units run `sonnet`/`medium`, the closing units are
  the cost model — and `planning-discipline.md` §5 sizes the padding off the
  wrong end.** Fourteen substantive units planned $86.50 and spent $22.03 (25.5%
  of plan). The four closing units that actually ran planned $22.50 and spent
  $34.30 — **61% of the feature's entire spend** — every one over its estimate,
  by +21%, +38%, +56% and +96%. §5 sizes a gate's headroom off its *largest
  substantive* estimate and explicitly declines to budget for a closing retry,
  on the grounds that a closing retry is a defect to diagnose. That reasoning
  holds for a *retry*; it does not cover a first attempt that is simply twice
  its estimate because it runs a bigger model over four gates of accumulated
  context. Nothing went wrong here — the substantive underrun absorbed it and
  budget was never binding — but the estimates were wrong in the one place the
  padding rule does not look. Rule: estimate a closing WU from the *volume of
  prior gates it must reconcile* and its model tier, not from a flat floor, and
  expect a terminal close to cost more than any implementation unit in the
  feature.

- [FEAT-2026-0049/G4-CLOSE] **A gate-scoped guard that resolves a gate number
  from the correlation ID can only see closing work units — check what a guard
  can observe before trusting its green.** `assert_failure_class_breakdown_when_
  failures_present` (`close-f`) is scoped by gate, and the scoping runs through
  `_gate_number_from_wu_id`, which matches `^G(\d+)-` on the ID's last segment.
  A substantive ID (`FEAT-2026-0049/T06`) has no such prefix, yields `None`, and
  is filtered out of every gate-scoped summary. So the guard that exists to make
  a close account for failed attempts is structurally blind to the failures of
  the units that do the work, and can only ever fire on a closing WU's own
  stumble — which issue #145 then deliberately excludes. Observed here: the
  gate-scoped call returns "(no non-passing attempts in scope)" for all four
  gates while the unscoped call over the same file returns a populated table.
  Rule: when a guard passes, ask what input it actually saw. A guard whose
  filter silently drops the majority of its domain reads as coverage while
  asserting nothing, which is the same failure shape as an ungated test suite.

- [FEAT-2026-0049/G4-CLOSE] **A test suite that injects a fixture value for a
  parameter with a shipped default never exercises the default — and the default
  is the invocation your users actually type.** All 54 of gate 4's tests passed
  `features_root=<a Path under a temp dir>`. `FeatureProvider`'s no-argument
  fallback is the *string* `".specfuse/features"`, and the reader called
  `.is_dir()` on it, so the bare `specfuse-agent run` raised `AttributeError`
  before selecting anything — and because `_select_next` calls every provider's
  `advertise` un-guarded, one provider's type error ended the whole run
  (#1746). The fixture was not wrong; it was *uniform*. Rule: for any parameter
  that has a default the shipped entry point relies on, one test must supply
  **nothing** and drive the entry point's own construction path. A
  fixture-injecting variant of that test re-hides the bug, which is why the
  regression module states in its docstring that it exercises the default
  deliberately. Corollary for reviewers: `grep` the test file for the parameter
  name; if every occurrence is an assignment, the default is untested.

- [FEAT-2026-0049/G4-CLOSE] **A close's evidence is "as of a commit", and
  nothing in the artifact records which commit — so a re-arm re-reads a
  retrospective that silently describes a different tree.** This close ran
  twice. The first pass re-ran every oracle honestly and recorded the results;
  one commit later those results described a tree that no longer existed, and
  `--recheck-verdict` re-reads the verdict field rather than re-verifying
  anything, so nothing in the machinery would have noticed. Two sub-rules, both
  paid for here. (a) A close that re-runs oracles should say which tree state it
  ran against, so a later reader can tell staleness from disagreement. (b) A
  live probe that calls a module's *leaf functions* is not evidence about the
  *entry path* that calls them: the first pass probed five readers and a
  constructor against live state, looked thorough, and was blind to a crash
  sitting between the constructor and the first method call. Probe the path the
  shipped entry point takes, or say explicitly that you probed the leaves.
