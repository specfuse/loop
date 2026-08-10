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

- [FEAT-2026-0044/G1-CLOSE] **`autonomy_default: auto` is never "close to a
  no-op", even on a single-gate feature with no next gate to arm.** This
  feature's `PLAN.md` reasoned that `auto` mattered only for gate arming, so on
  a one-gate feature it changed nothing. It changed where the close's lessons
  are allowed to land: under `auto`, a closing WU whose diff touches
  `.specfuse/LEARNINGS.md` fails `assert_learnings_staged_under_auto`, and the
  lessons must stage to a feature-local `LEARNINGS-pending.md` instead. This
  close was the first time that mechanism fired anywhere in the repo, and it
  collided with the close WU's own acceptance criterion, which had been written
  as "`.specfuse/LEARNINGS.md` gains at least one entry, or carries an explicit
  note that nothing generalized" — two branches, neither of them the one `auto`
  requires. Rules. (a) When a plan sets `autonomy_default: auto`, enumerate the
  mechanisms that dial actually reaches, not just the one the feature's shape
  makes salient; gate arming is the visible half and lessons staging is the
  quiet half. (b) A close WU drafted for an `auto` feature must give its
  LEARNINGS criterion a third branch — "or stages entries in
  `LEARNINGS-pending.md`" — or the close is forced to satisfy a criterion whose
  literal wording the driver would refuse.

- [FEAT-2026-0044/G1] **A plan drafted solo, that front-loads every load-bearing
  string, should price its implementation units below the interview-drafted
  norm — not at it.** All four substantive work units here came in more than 50%
  under plan (−69%, −55%, −62%, −80%; $14.00 planned, $4.55 actual), and none of
  the four was thin: the first landed the bulk of a 358-line module plus a
  252-line test file at 31% of its estimate. The cause is not efficiency, it is
  accounting. Each unit
  had its module path, function signature, finding prefixes, dial location and
  shape-to-copy fixed at draft time, so none of them spent anything on
  discovery — and discovery is what an interview-drafted estimate is implicitly
  pricing. Rule: when a plan's WUs quote their load-bearing strings verbatim and
  name the existing file to copy the shape from, estimate them as
  transcription-plus-tests, not as design-plus-implementation. Persistently
  over-planned costs are not harmless: they inflate gate budgets, which is the
  control that is supposed to stop a runaway feature.

- [FEAT-2026-0044/T01] **A schema documented in a WU body must be written in the
  exact spelling the project's own parser accepts, because a downstream feature
  drafted against that body will copy the literal.** T01's schema block wrote
  `automerge: off` unquoted; the repo's `_miniyaml` rejects that outright
  (`only lowercase true/false accepted as booleans (got 'off')`), so the shipped
  example and live file both write `automerge: "off"`. FEAT-2026-0048 had
  already been drafted against T01's block and encodes the unquoted literal in
  two of its own acceptance criteria. The parsed values matched what 0048
  assumed, so nothing broke — but only because 0048's checks happened to be
  expressible against the parsed value. Rule: before a WU body ships a YAML,
  JSON or config block as a schema declaration, run it through the project's
  actual parser. A schema block in a WU body is not illustrative prose; it is
  the interface a later feature will be drafted against.
