# Adopting `auto`: what appears in your repo, and how to opt in

`auto` (`autonomy_default: auto` in a feature's `PLAN.md` frontmatter) lets a
gate arm its successor without a human reading `GATE-N-REVIEW.md` first — the
arm predicate in `specfuse/loop/arm_eval.py` decides instead, deterministically,
from eight classes (see [`autonomy-stop-classes.md`](autonomy-stop-classes.md)
for the per-class diagnosis; this page does not restate it). This page covers
two things that page does not: what a driver at this version puts in *any*
Specfuse project regardless of whether that project ever runs `auto`, and the
exact procedure for opting one feature into it.

**Merge is never automated by this feature, without exception.** `auto` moves
the gate-arm decision off a human. It does not touch the PR review or the
merge — those stay manual on every feature, `auto` or not.

## Inventory: what a driver at this version adds

Additive, present whether or not any feature in the project uses `auto`:

- **`PLAN.baseline.json`** — a per-feature artifact, written once at a
  feature's first dispatch, byte-immutable after that. The snapshot the drift
  classes (`drift_caps`, `retroactive_edits`, `budget_projection`) measure
  against. See the mid-life hazard below.
- **`FEATURE-REVIEW.md`** — a per-feature artifact, written only under `auto`,
  append-only, one section per auto-armed gate. The read a human gives up
  per-gate becomes the read they owe at PR time instead.
- **`LEARNINGS-pending.md`** — a per-feature artifact, written only under
  `auto`, the staging destination for lessons an unread gate produced (a
  closing WU under `auto` may not touch `.specfuse/LEARNINGS.md` directly).
- **`LEARNINGS-pending.template.md`** — ships into *every* downstream
  project's `.specfuse/templates/` on the next `init.sh` / upgrade, whether or
  not that project ever runs `auto`.
- **`pre-arm/<feature-id>/gate-<N>` tags** — see "what may break" below.
- **`arm_predicate_evaluated`** — new `events.jsonl` event type, payload
  `{gate, would_arm, predicate_version, classes: {<name>: {status, reason}}}`
  or `{gate, would_arm: null, evaluation_error}` on a degraded evaluation.
  Deliberately unregistered (absent from `event.schema.json`'s `event_type`
  enum and from `PER_TYPE_SCHEMA_DIR`), matching the `gate_reached` /
  `attempt_outcome` precedent.
- **`gate_auto_armed`** — new `events.jsonl` event type, payload `{gate, tag,
  armed_wu_ids, predicate_version}`, appended once per auto-arm. Also
  deliberately unregistered.
- **`learnings_not_staged`** — new closing-requirements failure reason
  (`close-e` / `close-intermediate-e`, `closing_requirements.py`), fired when
  a closing WU under `autonomy_default: auto` touches `.specfuse/LEARNINGS.md`
  directly instead of staging to `LEARNINGS-pending.md`. Changes
  `specfuse lint --closing` output accordingly. Inert outside `auto`, but the
  requirement registry is a published surface every project's lint now
  carries.

## What may break

Three items from the gate 2 retrospective need explicit acknowledgment
because they change or repurpose something a consumer may already depend on,
rather than adding beside it.

### The `classes` map grew from seven keys to eight

`arm_predicate_evaluated`'s `classes` map now carries eight entries
(`CLASS_NAMES` went from 7 to 8, `VETO_CLASSES` from 2 to 3 — the eighth class
is `plan_next_lint`). **Affects:** any consumer that enumerates the map,
asserts its length, or switches exhaustively over class names — dashboards
rendering the predicate breakdown, `gate-status`/`learnings-suggest` if they
inspect classes, any project-local `events.jsonl` reader, and anyone diffing
two `arm_predicate_evaluated` events emitted either side of this feature.
**Owner action:** treat the map as open (iterate keys, don't assume a fixed
set or a fixed count) rather than pattern-matching on exactly seven names.

### `pre-arm/<feature-id>/gate-<N>` tags are force-created

Created with `git -c tag.gpgSign=false tag -f` — lightweight, unsigned, and
**`-f`, so a re-arm of the same gate silently moves an existing tag of that
name.** They accumulate one per armed gate and show up in every `git tag`
listing and every `git push --tags` in a project running `auto`. **Affects:**
any tooling or script that walks the tag list expecting only release/version
tags, or that assumes a tag name is stable once created. **Owner action:**
either ignore the `pre-arm/` namespace explicitly in tag-consuming tooling, or
treat a `pre-arm/` tag's target commit as mutable, not pinned. Recovery
procedure for this tag namespace: [`auto-arm-recovery.md`](../dev/auto-arm-recovery.md).

### The bookkeeping commit message changes on an auto-armed gate

`chore(loop): gate N awaiting_review` becomes `chore(loop): gate N auto-armed
gate N+1 (tag pre-arm/...)` when the gate auto-arms. **Affects:** dashboards,
the `/attention` skill, and any ad-hoc operator grep keyed on the old
`awaiting_review` string — those will miss auto-armed gates entirely.
**Owner action:** match on the `chore(loop): gate N` prefix rather than the
full literal string, or additionally grep for `auto-armed`.

## The mid-life baseline hazard

`PLAN.baseline.json` is written once, at a feature's **first dispatch**, and
is byte-immutable after that by construction. A feature whose first dispatch
happened before a driver at this version shipped has no baseline. The next
time that feature's driver runs, it writes one from `PLAN.md` **as it then
reads** — a plan that already contains everything the feature has drifted
into up to that point.

The classes that measure drift against the baseline — `drift_caps`,
`retroactive_edits`, and `budget_projection`'s baseline-total comparison — will
then report clean and mean nothing for that feature, because the yardstick was
cut from the thing it is supposed to measure. **This applies to every feature
whose first dispatch predates this feature, not only to `FEAT-2026-0053`
itself**, and it is not a defect: there is no fix, because it is what
"snapshot the as-activated graph" means when the snapshot is taken mid-life
instead of at activation.

The only honest remedy: drift detection is trustworthy from a feature's first
dispatch onward. For a feature that predates this one, a clean `drift_caps` /
`retroactive_edits` verdict carries no information, and the human's read at
that gate is doing the work those classes cannot. No `PLAN.baseline.json` may
be hand-authored to retroactively fix this for an older feature — there is no
correct value to backfill it with.

## Opting a feature into `auto`

1. **Edit the frontmatter.** In the feature's `PLAN.md`, set
   `autonomy_default: auto` (the field also accepts `review` — the current
   default — and `supervised`; see `PLAN.template.md`'s inline comment).
2. **Know what changes at the gate boundary.** From the next gate close
   onward, if the arm predicate returns `would_arm: True`, the driver flips
   every gate-`N+1` draft WU to `pending` and the closed gate to `passed` in
   one commit, tags `pre-arm/<feature-id>/gate-<N>` at the pre-arm commit
   first, and appends `gate_reached`, `arm_predicate_evaluated`, and
   `gate_auto_armed` to `events.jsonl` — with no `arm-gate` skill invocation
   and no human read in between. If any class fires or is `not_evaluable`
   (including `not_evaluable: no_baseline` on a feature with no baseline —
   see above), the gate parks at `awaiting_review` exactly as it does today,
   and the normal `arm-gate` skill applies.
3. **What the operator gives up:** the per-gate read of `GATE-N-REVIEW.md`
   before the successor gate's work units start.
4. **What the operator keeps:** every escalation (a fired or `not_evaluable`
   class still halts, same as before), the PR review, and the merge — merge
   is never automated, on any feature.
5. **Read two artifacts at PR time**, since the per-gate read no longer
   happens:
   - **`FEATURE-REVIEW.md`** — one section per auto-armed gate, the
     substitute for the reads that were skipped.
   - **`LEARNINGS-pending.md`**, and promote its entries into
     `.specfuse/LEARNINGS.md` by hand. As of this feature's gate 2 close, no
     human has ever performed this promotion step — it is untested by use,
     not just undocumented, so budget extra care the first time.
6. **To back out:**
   - **Frontmatter revert:** set `autonomy_default` back to `review` (or
     `supervised`) in `PLAN.md`. This only affects gates that close after the
     edit — it does not un-arm a gate that already auto-armed.
   - **Undo an already-committed auto-arm:**
     `git reset --hard pre-arm/<feature-id>/gate-<N>`, which returns the
     just-closed gate to `awaiting_review` and every gate-`N+1` WU to `draft`.
     Full recovery procedure, including the crash-mid-arm case (which needs no
     action): [`auto-arm-recovery.md`](../dev/auto-arm-recovery.md).
