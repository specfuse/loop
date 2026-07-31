# Auto-arm recovery (FEAT-2026-0053/T06)

See `docs/methodology.md` §9 for the one-commit-arm concept; this doc is the
recovery procedure only.

## The guarantee

An `auto`-feature arm is **exactly one commit**. When a gate closes with
`autonomy_default: auto` and the arm predicate returns `would_arm: True`, the
driver's normal-completion flip site does all of the following inside the
single bookkeeping commit that already fires at that site:

1. flips every gate-`N+1` draft work unit's `status` from `draft` to `pending`;
2. flips the just-closed gate `N`'s file from `awaiting_review` to `passed`;
3. appends `gate_reached`, `arm_predicate_evaluated`, and `gate_auto_armed` to
   `events.jsonl`.

Before any of those writes touch the working tree, the driver creates the
revert tag `pre-arm/<feature-id>/gate-<N>` at `HEAD` — the commit immediately
before the arm. Because the whole write set lands in one commit, and the tag
is created before that commit exists, a crash mid-arm leaves the repository in
exactly one of two states. There is no third state.

## State 1 — the arm never committed

If the driver crashes (or is killed) after the tag is created but before the
bookkeeping commit lands, the working tree holds the flipped-status writes
uncommitted. The driver's own pre-run guards discard this on the next
invocation:

- `require_git_ready` / the per-attempt `git reset --hard` path resets the
  working tree to `HEAD`, which is still the pre-arm commit — the tag points
  at the same commit `HEAD` already is, so nothing needs to change.
- The uncommitted draft->pending / awaiting_review->passed writes are
  discarded along with everything else `reset --hard` throws away.

**Nothing to do.** Re-run the driver; it re-evaluates the gate close from
scratch, tags at the same `HEAD` again (tag creation is idempotent: the driver
force-creates the tag at the current `HEAD`, so re-tagging the same commit is
a no-op), and either arms again or takes the non-arm path if circumstances
changed.

## State 2 — the arm committed in full

If the bookkeeping commit lands, the arm is complete: `HEAD` now points at a
commit that contains every one of the write-set paths (the gate file, every
flipped WU file, `events.jsonl`) with nothing else mixed in. To undo exactly
this arm and nothing else:

```
git reset --hard pre-arm/<feature-id>/gate-<N>
```

This moves `HEAD` (and the branch it points at) back to the commit immediately
before the arm — the just-closed gate returns to `awaiting_review`, every
gate-`N+1` WU returns to `draft`, and the `gate_auto_armed` /
`arm_predicate_evaluated` / `gate_reached` events for that close disappear from
the working tree's view of `events.jsonl` (the commit itself is still
reachable via the tag until the tag is deleted, so the events remain
inspectable at `pre-arm/<feature-id>/gate-<N>..<the arm commit>` if needed
before deleting it).

Substitute the real feature ID and gate number, e.g. for `FEAT-2026-0053`'s
gate 1:

```
git reset --hard pre-arm/FEAT-2026-0053/gate-1
```

## Why there is no third state

The three states a partially-written multi-commit operation could leave behind
— "not started," "half-written," "fully written" — collapse to two here
because the entire write set is one commit. "Half-written" would require some
of the arm's file changes to be committed while others are not; that cannot
happen because `git commit` is itself atomic on a single commit, and this arm
performs exactly one. The tag's presence is not itself evidence of a completed
arm — it exists in both states — which is why recovery is keyed on the
commit, not the tag: check whether the just-closed gate's file (or any
gate-`N+1` WU) shows the armed status on disk. If it does, the commit landed
(state 2); if it does not, nothing did (state 1).
