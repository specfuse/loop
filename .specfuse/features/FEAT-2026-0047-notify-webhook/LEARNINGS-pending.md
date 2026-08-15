<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Lessons staged for promotion — FEAT-2026-0047

`autonomy_default: auto`, so `FEAT-2026-0047/G1-CLOSE` may not append to
`.specfuse/LEARNINGS.md` directly (`assert_learnings_staged_under_auto`, reason
`learnings_not_staged`). No human read gate 1 before this close dispatched, and
`.specfuse/LEARNINGS.md` is loaded into planning context for every future
feature — so a lesson written there unreviewed compounds. These three are staged
for the operator to **promote, narrow, or reject** at PR review.

Promoting one means appending it to `.specfuse/LEARNINGS.md` in the entry shape
that file already uses. Rejecting one costs nothing; a rejected lesson is just a
retrospective observation that did not generalise.

---

## Candidate 1 — the config holds a name, the environment holds the value

**Proposed entry:**

> - [FEAT-2026-0047/G1-CLOSE/config-holds-a-name-environment-holds-the-value]
>   **When a committed config file needs to reference a credential, the file
>   holds the environment-variable NAME and the environment holds the value —
>   and the validator enforces the *shape* of a name, not the absence of a
>   secret.** FEAT-2026-0044 shipped `escalation.webhook: ""` into a committed
>   file. A webhook URL is a bearer credential, and
>   `lint_monitoring`'s credential-key pattern
>   (`key|token|secret|password|credential|connection_string`) does not match
>   `webhook`, so nothing in the repo would have stopped an operator pasting a
>   live URL into git. FEAT-2026-0047 renamed the key to `webhook_env` and
>   validated it against `^[A-Za-z_][A-Za-z0-9_]*$` — the same structural shape
>   `monitoring.yml` already used for credentials. **The generalisation is the
>   validator's posture, not the naming convention:** a shape check for what a
>   name looks like is decidable and reports zero on a conforming file
>   (including the empty-value case), whereas a secret *detector* is a guess
>   that must be updated for every provider's URL format. Three properties make
>   the convention testable rather than aspirational, and are worth copying
>   together: (a) the empty value is explicitly valid and means "not
>   configured", so the no-op path is the one CI actually covers; (b) the
>   provider is declared by its own key rather than sniffed from the URL, so no
>   code path parses the credential; (c) the failure log is a fixed string with
>   no interpolation, which is why a raising poster cannot leak the target.
>   **Boundary:** this applies to *committed* config. A key already carried by a
>   tagged release needs a reader that accepts both spellings; the no-shim
>   rename here was cheap only because both features sat in the same unreleased
>   section and no consumer outside the repo had ever seen the old key.

**Why it may generalise:** every project that grows an outbound integration
faces this, and the loop's own scaffold ships two config surfaces
(`monitoring.yml`, `agent-policy.yml`) that now share the convention.

**Why the operator might narrow it:** the strongest, most portable part is the
last sentence about the release boundary; the rest may already be adequately
covered by `security-boundaries.md`, in which case the right move is a one-line
addition there rather than a LEARNINGS entry. Consider whether this belongs in
`.specfuse/rules/security-boundaries.md` as a standard instead — it is a
posture, not an incident.

---

## Candidate 2 — a two-part criterion needs its two halves verified separately

**Proposed entry:**

> - [FEAT-2026-0047/G1-CLOSE/two-part-criteria-hide-a-missing-half]
>   **A criterion of the form "X ships AND a test asserts X" passes the whole
>   code gate set with only the first half delivered — verify the halves
>   separately, and make the second half its own numbered criterion.**
>   FEAT-2026-0047's T04 criterion 9 required a `/attention` skill section
>   naming `specfuse.loop.heartbeat.silence_check` **and** a test asserting that
>   literal. The section shipped; the test was never written. The WU reported
>   `done`, the driver's produces-vs-diff guard passed (the skill file really
>   did change), and all sixteen `code` gates went green — because a *missing*
>   test is invisible to every gate: nothing fails, coverage does not drop, and
>   the prose passes lint trivially. Only the close's own fresh sweep caught it,
>   with a one-line grep (`grep -rl '<literal>' tests/`). Three rules. (a) When
>   a criterion contains "and a test asserts", split it into two numbered
>   criteria so the per-criterion state artifact can record one `pass` and one
>   `fail` instead of one ambiguous entry. (b) A close verifying a prose
>   deliverable should grep `tests/` for the guard, not just grep the artifact
>   for the content — the artifact's presence is the easy half. (c) The
>   falsifiability check for any prose criterion is "delete the section; does
>   anything go red?" — if not, the guard is missing regardless of what the WU
>   reported.

**Why it may generalise:** the pattern is not specific to skills. Any criterion
pairing a deliverable with its regression guard has this shape, and prose
deliverables (SKILL.md, rules, docs) are where it bites hardest because they
pass automated gates trivially. `[FEAT-2026-0003/G2-LESSONS]` already records
the underlying observation about prose artifacts; this is the operational
counterpart — what a close should *do* about it.

**Why the operator might narrow it:** rule (a) is a change to how work units are
authored and may belong in `.specfuse/skills/authoring-work-units/SKILL.md`
rather than LEARNINGS; rules (b) and (c) belong to close discipline. Splitting
this candidate across those two homes may serve better than one LEARNINGS entry.

---

## Candidate 3 — price a composition WU against its own statement count

**Proposed entry:**

> - [FEAT-2026-0047/G1-CLOSE/price-composition-wus-against-their-own-size]
>   **A work unit whose entire job is to compose two already-finished modules
>   should be priced against its own statement count, not against its
>   siblings.** FEAT-2026-0047's T02 was planned at $3.00, in line with the
>   feature's other three units, and came in at $0.71 — a −76.4% variance, the
>   largest in the feature. It is 14 statements: a URL formatter, a category
>   guard, a one-line message, and a delegation. Its WU body's own constraints
>   ("import the constants, do not retype them"; "a one-liner and a link,
>   nothing else") had removed essentially all the design latitude that costs
>   turns before dispatch. More generally, all three of this feature's
>   over-50%-under-plan units under-spent for one shared reason: **PLAN.md's
>   existing-mechanism table had already done the searching, and the estimates
>   were written as if it had not.** A plan that pays for the search up front
>   should price the WUs against the post-search work; otherwise the search is
>   paid twice and the remaining budget reads as slack the gate does not have.

**Why it may generalise:** the existing-mechanism table is now standard practice
(`planning-discipline.md` §1), so the double-counting it enables is a standing
estimation bias, not a one-off.

**Why the operator might reject it:** under-spending is a benign failure, and an
estimate that is 2.4× high costs nothing but a wide budget. If gate budgets are
never the binding constraint in this repository, this is an observation rather
than a lesson. It also rests on a single feature's four data points; waiting for
a second feature with an equally thorough plan table would make it much stronger.
