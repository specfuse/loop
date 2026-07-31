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
