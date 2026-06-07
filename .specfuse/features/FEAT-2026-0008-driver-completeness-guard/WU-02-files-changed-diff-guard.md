---
id: FEAT-2026-0008/T02
type: implementation
model: claude-opus-4-7
effort: high
status: done
attempts: 1
duration_seconds: 336.905
cost_usd: 1.746955
input_tokens: 22
output_tokens: 21351
---

# `files_changed` diff guard

**Objective.** When a WU's RESULT block declares
`files_changed: [paths...]`, the driver verifies — **before squashing
the attempt's edits** — that each named path actually differs from
`HEAD`. If any declared path is unchanged from `HEAD`, the attempt is
treated as a failed attempt (re-dispatch).

**Context.** This is `FEAT-2026-0008/T02`. `parse_result_block` at
`loop.py:481` parses the YAML inside the agent's fenced `result` block;
the parsed dict already carries a `files_changed` list when the agent
authored it per `.specfuse/rules/result-contract.md`. `squash_commit`
at `loop.py:400` performs the soft-reset + add-all + commit dance. The
diff check belongs **between** `parse_result_block` and `squash_commit`
— after we know the agent's claim, before we lock it into history.

The retrospective for FEAT-2026-0007 documents T04 and T08 committing
WU frontmatter status flips with **no source-code edits in their
diffs**, while their RESULT blocks declared `files_changed` lists naming
`.specfuse/scripts/loop.py` and new test files. This guard turns that
mismatch into a falsifiable check.

Reference the binding rules under `.specfuse/rules/`. The driver owns
git; edit files only.

**Acceptance criteria.**
1. New helper `verify_files_changed(result: dict, head_before: str) ->
   list[str]` returns a list of paths from `result.get("files_changed",
   [])` that are unchanged between the working tree and `head_before`.
   Empty list means "all claimed files have real diffs"; a non-empty
   list names the offending paths for the failure event.
2. The check uses `git diff --quiet <head_before> -- <path>` per path
   (exit 0 = no diff, exit 1 = diff). Paths declared by the agent that
   do not exist in the working tree are reported as "unchanged" (they
   never existed, so they cannot have diffs to commit).
3. In the attempt loop, after `parse_result_block` returns a parsed
   RESULT and before `squash_commit` is invoked, call
   `verify_files_changed(result, head_before)`. When the returned list is
   non-empty:
   (a) skip `squash_commit` entirely (no agent-work commit lands),
   (b) `git reset --hard <head_before>` to discard any partial edits,
   (c) append an event `attempt_outcome` with
       `outcome: "files_changed_mismatch"` and payload field
       `unchanged_paths: [...]`,
   (d) treat the attempt as a verification failure (increment counter,
       continue to next attempt or spinning escalation).
4. When the RESULT block omits `files_changed` entirely or the value is
   the empty list, the guard does NOT fire — the existing behavior is
   preserved. This is the explicit opt-out, kept because pre-existing
   WUs and the worked-example fixture do not always declare it.
5. New unit tests in `tests/test_loop_files_changed_guard.py`:
   (a) `verify_files_changed` with all claimed paths actually modified
       returns `[]`.
   (b) `verify_files_changed` with one claimed path that the agent
       never touched returns that path.
   (c) `verify_files_changed` with a claimed path that does not exist on
       disk returns that path.
   (d) Integration via a stubbed dispatch + a temp git repo: an agent
       that returns `files_changed: [a.py]` but writes nothing causes the
       WU to fail and re-dispatch; no squash commit lands; the soft-reset
       discards anything else the agent may have done.
   (e) Integration: an agent that omits `files_changed` from the RESULT
       block has the existing pre-T02 behavior (squash runs as today).
6. **Existence check** (per LEARNINGS `[FEAT-2026-0007/G1-LESSONS]`):
   `python3 -c "from loop import verify_files_changed"` must succeed
   before declaring complete.

**Do not touch.** Exactly 2 files change: `.specfuse/scripts/loop.py`
and one new test file `tests/test_loop_files_changed_guard.py`. No edits
to: `.specfuse/rules/result-contract.md` (the contract already documents
`files_changed`; this WU only enforces it), `WU.template.md`,
`.specfuse/verification.yml`, existing WU files, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`,
plus the existence smoke check in AC 6.

**Escalation triggers.**
1. **Completeness.** If `verify_files_changed` is absent from `loop.py`
   after your edits, emit `status: blocked` — do not claim complete.
2. **Pre-existing-WU regression.** If your implementation fires the
   guard on WUs whose RESULT blocks omit `files_changed` (treating
   absence as "empty list of required changes"), stop and emit
   `status: blocked` — absence must opt out of the guard, not into it.
3. **Squash sequencing.** The check MUST run before `squash_commit`'s
   `git add -A`. If the implementation accidentally runs after staging,
   the working-tree diff against `head_before` will include nothing
   (already staged) and the guard becomes a no-op. Test with a sentinel
   path the agent never touched; the integration test must catch this.
