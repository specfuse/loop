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
