---
id: FEAT-2026-0053/T12
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
oracle_env: macos_local
provenance: "G2-PLAN's dispatch brief names migration guidance for existing features and downstream projects as minimum gate-3 scope. The specific breakage list is not invented here — it is RETROSPECTIVE.md's two 'Consumer-visible contract changes' sections (five items for gate 1, ten for gate 2), which flag items 2, 4 and 8 of gate 2 as needing explicit human acknowledgment. The mid-life baseline hazard comes from gate-1 Findings 2 and gate-2 'What the loop did NOT verify' 2, which record it on this feature and predict it for every feature that predates the wiring."
produces:
  - docs/concepts/adopting-auto-mode.md
  - specfuse/loop/data/docs/concepts/adopting-auto-mode.md
  - docs/README.md
  - tests/test_scaffold_data_in_sync.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.7.1
started_at: 2026-07-31T03:41:50.002779+00:00
duration_seconds: 490.502
cost_usd: 0.884682
input_tokens: 46
output_tokens: 8604
---

# What `auto` puts in your repo, and how to opt a feature into it

**Objective.** Ship `docs/concepts/adopting-auto-mode.md`: what appears in any
Specfuse project once a driver at this version runs, what changes for consumers
that already parse the loop's outputs, the mid-life baseline hazard that affects
every feature predating this feature, and the exact procedure for opting a
feature into `auto`.

**Context.** Correlation ID `FEAT-2026-0053/T12`. `depends_on` `T11`: both WUs
add a page under `docs/concepts/` and therefore both edit `docs/README.md`'s
concepts index and the `DOCS_TRACKED` set in
`tests/test_scaffold_data_in_sync.py`. Running second means `T11`'s entries are
already present — add yours beside them and do not restructure either list.
`T10` owns the methodology's §9 and links here; this page owns the operational
detail.

**The source of the breakage list is already written — do not re-derive it.**
`RETROSPECTIVE.md` carries two "Consumer-visible contract changes" sections
(five items from gate 1, ten from gate 2). Read both. Gate 2's section flags
three items as needing explicit human acknowledgment, and those three are the
spine of this page:

- **Item 2 — a changed existing payload.** Every `arm_predicate_evaluated`
  event's `classes` map now carries **eight** keys rather than seven. Anything
  that enumerates that map, asserts its length, or switches exhaustively over
  class names sees a changed shape.
- **Item 4 — repo-visible tags.** `pre-arm/<feature-id>/gate-<N>`, created
  lightweight, unsigned, and with `-f`, so a re-arm of the same gate silently
  moves an existing tag of that name. They accumulate one per armed gate and
  appear in every `git tag` and every `git push --tags`.
- **Item 8 — a changed bookkeeping commit message.** `chore(loop): gate N
  awaiting_review` becomes `chore(loop): gate N auto-armed gate N+1 (tag
  pre-arm/...)` on an auto-armed gate. Dashboards, `/attention`, and ad-hoc
  operator greps keyed on the old string miss auto-armed gates.

The remaining items are additive and belong in the page as an inventory rather
than as warnings: `PLAN.baseline.json`, `FEATURE-REVIEW.md`,
`LEARNINGS-pending.md`, the `LEARNINGS-pending.template.md` that now ships to
every downstream project on the next `init.sh` / upgrade whether or not that
project ever runs `auto`, the two new unregistered event types, the
`learnings_not_staged` outcome value, and the `close-e` /
`close-intermediate-e` closing requirements that change `specfuse-lint
--closing` output.

**The mid-life baseline hazard — the part an operator cannot infer.**
`PLAN.baseline.json` is written once, at a feature's **first dispatch**, and is
byte-immutable after that by construction. A feature whose first dispatch
happened before this feature shipped has no baseline; the next driver
invocation writes one from `PLAN.md` **as it then reads** — that is, from a plan
that already contains everything the feature has drifted into so far. The
classes that measure drift against the baseline (`drift_caps`,
`retroactive_edits`, and `budget_projection`'s baseline total) will then report
clean and mean nothing for that feature. This is not a defect and there is no
fix: it is what "snapshot the as-activated graph" means when the snapshot starts
mid-life. The page must state it, state that it applies to **every** feature
predating this one, and state the only honest remedy — that drift detection is
trustworthy from a feature's first dispatch onward, and for older features the
human's read is doing the work the class cannot.

**The opt-in procedure must be executable.** An operator following the page
should be able to move a feature to `auto` without reading any source. At
minimum it names: the frontmatter edit (`autonomy_default: auto` in `PLAN.md`),
what changes about the gate boundary from that moment, what the operator gives
up (the per-gate read) and what they keep (every escalation, the PR review, the
merge), the artifacts they must now read at PR time (`FEATURE-REVIEW.md` and the
`LEARNINGS-pending.md` promotion step, which as of gate 2's close no human has
ever performed), and how to back out — both the frontmatter revert and the
`git reset --hard pre-arm/<feature-id>/gate-<N>` path documented in
`docs/dev/auto-arm-recovery.md`.

**Acceptance criteria.**

1. `docs/concepts/adopting-auto-mode.md` exists, is non-empty, and contains an
   inventory section naming every one of: `PLAN.baseline.json`,
   `FEATURE-REVIEW.md`, `LEARNINGS-pending.md`, `LEARNINGS-pending.template.md`,
   `pre-arm/`, `arm_predicate_evaluated`, `gate_auto_armed`, and
   `learnings_not_staged`.
2. The page carries a "what may break" section covering gate 2's three
   acknowledgment items — the eight-key `classes` map, the force-created tag
   namespace, and the changed bookkeeping commit message — each with the
   consumer it affects and what that consumer's owner should do.
3. The page states the mid-life baseline hazard: that a feature predating this
   one gets a post-drift baseline, that `drift_caps` / `retroactive_edits` are
   therefore uninformative for it, and that this applies to every such feature
   rather than being specific to `FEAT-2026-0053`.
4. The page carries a numbered opt-in procedure for moving one feature to
   `auto`, covering the frontmatter edit, what the operator gives up and keeps,
   the two artifacts they must read at PR time, and both back-out paths.
5. The page states that merge is never automated by this feature, without
   exception, and links `docs/concepts/autonomy-stop-classes.md` (T11) for the
   per-class diagnosis rather than restating it.
6. `docs/README.md`'s "Concepts (under `concepts/`)" list gains an entry for the
   new page, alongside T11's entry rather than replacing it.
7. `specfuse/loop/data/docs/concepts/adopting-auto-mode.md` exists,
   `DOCS_TRACKED` in `tests/test_scaffold_data_in_sync.py` names the new path
   **and still names T11's**, and
   `python3 -m unittest tests.test_scaffold_data_in_sync -v` exits `0`.
8. `python3 -m unittest discover -s tests -v` exits `0`.

**Do not touch.** Every `.py` file under `specfuse/` except the mirrored data
copy — this is a documentation WU and a migration claim that needs a code change
to be true is an escalation, not an edit. `docs/methodology.md` (T10).
`docs/concepts/autonomy-stop-classes.md`, and T11's entries in the docs index
and in the drift guard's `DOCS_TRACKED` set — read them, append beside them, do
not rewrite or reorder them. Historical
feature folders: this page tells operators what to do, it does not back-fill
anything into closed features, and no `PLAN.baseline.json` may be hand-authored
for any feature. `.specfuse/rules/`. `RETROSPECTIVE.md` and the other
feature-folder artifacts. Generated directories, secrets, `.git/`. The driver
owns all git — you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` set in `.specfuse/verification.yml`. Scoped
iteration run: `python3 -m unittest tests.test_scaffold_data_in_sync -v`.
Criterion 1's inventory is a literal-string check; grep for each of the eight
names in the produced page before reporting.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if
the opt-in procedure cannot be written as an executable sequence — if opting a
feature into `auto` turns out to require a step that does not exist yet, the
gap belongs in front of a human rather than inside a document that reads as
though the path is complete. Emit `status: blocked` if `T11`'s page or its
`DOCS_TRACKED` entry is absent from the working tree: this WU depends on it, and
writing around a missing dependency produces an index this WU cannot verify.
