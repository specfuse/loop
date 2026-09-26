# LEARNINGS-pending

**What this file is.** This feature runs under `autonomy_default: auto` — a
closing WU here dispatches without a human reading the gate first. Under
`review` or `supervised`, a promoted lesson lands straight in the repo's
`.specfuse/LEARNINGS.md`, because a human already reviewed the gate that
produced it. Under `auto` nobody did, so the lesson stages here instead: in
this feature directory, not in the repo-wide file that every future feature's
planning step loads. A closing WU's own post-pass check refuses to pass if
its diff touches `.specfuse/LEARNINGS.md` while this feature is in `auto`
mode — this file is where those lessons go instead.

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

- [FEAT-2026-0114/G1] **A verbatim example block inserted into a note pushes
  the note's own earlier prose past a capped excerpt window — put the words a
  downstream assertion depends on before the example, not after.** `T02` added
  a two-entry ```result YAML example to the `produces_not_in_diff` repair
  note, appended after the sentence naming `produces_unchanged:` and
  `produces_amended:`. That sentence landed around the note's 300th
  character; `extract_failure_excerpt` keeps only the first ~250 and last
  ~250 characters, so the key names fell into the elided middle, and
  `tests.test_produces_justification`'s excerpt assertion — a test `T02`'s
  own acceptance criteria never named, because it lived in a different
  module than the three T02#3 checked — started failing. The driver's own
  escalation correctly refused to assume this was pre-existing debt ("do NOT
  assume it predates the feature") and named exactly which landed WUs to
  check; the fix (`T02H`) was one added sentence, positioned *before* the
  example instead of after. Authoring rule: when a WU's plan is to append a
  verbatim, multi-line example (a YAML fence, a code block, a full stack
  trace) to prose that must still summarize its point within a capped
  excerpt/head-tail window, name the load-bearing words in a short sentence
  placed *before* the example, and add a red-first test for the excerpt's
  *content* (not just its presence) alongside the change that inserts the
  example — the assertion that would catch this lives in a sibling module a
  narrow `produces:` list will not surface until the broad run finds it.
