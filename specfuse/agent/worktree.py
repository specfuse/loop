# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Give the operator back the branch they started on (#2055).

A `specfuse-agent` run dispatches `/fix-bug` sessions, and those create and
check out branches. When the run ends, the working tree is left on whatever
branch the last dispatched session made. Observed 2026-08-12: a run that
began on `main` ended on `fix/issue-1859-learnings-curate-vendored-promote`,
with nothing in the summary saying so. An operator who reads
`items completed: 0` and starts working is now committing onto an abandoned
feature branch without noticing.

**This lives outside `run_agent` on purpose.** The conductor's invariant --
"there is no code path here that can commit, branch, or merge", enforced by
`tests/test_agent_run.py`, which asserts the loop's runner issues only `gh`
and never a mutating verb -- is a real safety property and worth keeping. The
mutation is not the loop's; it belongs to the dispatched sessions. What the
loop's *caller* owns is the process boundary: `specfuse-agent` is one command
to the operator, and a command that moves your branch and does not move it
back is the surprise. So `main()` brackets the run, and the conductor stays
pure.

Restoring is deliberately conservative. A dirty tree is never forced past --
a checkout there could discard a dispatched session's uncommitted work, which
is strictly worse than the branch being wrong. Both the restore and the
refusal are reported, so a run that could not put things back says so rather
than leaving the operator to discover it.

## Per-item isolation (FEAT-2026-0108/T02)

Restoring the branch at the *end* of a run is the smallest version of the
problem. The larger one is what happens *during* it: every item shared one
working tree, so item N's session started on whatever branch item N-1's
session left checked out, with item N-1's uncommitted edits still in the
tree. The 2026-09-02 unattended run made that concrete -- one item's
complete, passing fix was left as uncommitted edits on a branch named for a
different issue (#3179), and the only trace of it was a line in the run's
console output.

`item_worktree` gives each item its own `git worktree` on its own
`agent/<item_id>` branch, cut from one base recorded at the start of the run,
and takes it away afterwards. On the way out it makes a decision the old
code never made: work that is committed keeps its branch, and work that is
*not* committed is committed for it, under `wip/<item_id>` -- a ref whose
name says which item produced it. "Uncommitted edits in a shared tree" stops
being a state the lane can end an item in, so it stops being a state that can
be attributed to the wrong issue.

Nothing here runs through the conductor's injected runner. `run_agent`'s
invariant -- no code path in it can commit, branch or merge, enforced by
`tests/test_agent_run.py` asserting that runner only ever issues `gh` -- is
intact: these calls are this module's, made through its own subprocess
runner, in the same way `restore_branch` already worked.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator, List, Optional


def _default_runner(argv: list, check: bool = False):
    return subprocess.run(argv, check=check, capture_output=True, text=True)


def current_branch(runner: Callable = _default_runner) -> Optional[str]:
    """The checked-out branch, or `None` if that cannot be determined.

    `None` covers a detached HEAD and a non-repository alike: in both, there
    is no branch name to put back, and guessing one would be worse than
    leaving the tree alone.
    """
    try:
        result = runner(["git", "branch", "--show-current"], check=False)
    except Exception:  # noqa: BLE001 - never break a run over bookkeeping
        return None
    if getattr(result, "returncode", 1) != 0:
        return None
    name = (getattr(result, "stdout", "") or "").strip()
    return name or None


def is_dirty(runner: Callable = _default_runner) -> Optional[bool]:
    """Whether the tree has uncommitted changes. `None` when unreadable."""
    try:
        result = runner(["git", "status", "--porcelain"], check=False)
    except Exception:  # noqa: BLE001
        return None
    if getattr(result, "returncode", 1) != 0:
        return None
    return bool((getattr(result, "stdout", "") or "").strip())


def restore_branch(
    original: Optional[str],
    *,
    runner: Callable = _default_runner,
    report: Optional[Callable[[str], None]] = None,
) -> bool:
    """Check *original* back out if the run moved off it. Returns success.

    A silent no-op only when the tree never moved, or when *original* is
    `None` because there was no branch to record at the start. Every other
    non-restore -- unreadable branch, dirty tree, failed checkout -- reports
    and returns False, because a restore that did not happen and says nothing
    is the failure mode this whole module exists to remove.
    """
    def _say(message: str) -> None:
        if report is not None:
            report(message)

    if not original:
        return True

    now = current_branch(runner)
    if now == original:
        return True
    if now is None:
        # Unreadable, not "fine". Returning success here would be a silent
        # path: git is broken or the tree is detached, we restored nothing,
        # and the operator hears nothing about either.
        _say(
            f"could not read the current branch, so '{original}' was not "
            f"restored — check where the tree is before continuing"
        )
        return False

    dirty = is_dirty(runner)
    if dirty is None:
        _say(
            f"working tree left on '{now}' (started on '{original}') — could "
            f"not read its status, so it was left alone"
        )
        return False
    if dirty:
        # Refusing loudly beats forcing: a checkout over uncommitted changes
        # can discard a dispatched session's work, and losing work is worse
        # than being on the wrong branch.
        _say(
            f"working tree left on '{now}' (started on '{original}') — NOT "
            f"restored: it has uncommitted changes. Inspect them before "
            f"switching back."
        )
        return False

    try:
        result = runner(["git", "checkout", original], check=False)
    except Exception as exc:  # noqa: BLE001
        _say(f"could not restore branch '{original}' — {type(exc).__name__}: {exc}")
        return False
    if getattr(result, "returncode", 1) != 0:
        stderr = (getattr(result, "stderr", "") or "").strip()
        _say(f"could not restore branch '{original}' — {stderr or 'checkout failed'}")
        return False

    _say(f"working tree restored to '{original}' (the run left it on '{now}')")
    return True


# --------------------------------------------------------------------------- #
# Per-item isolation (FEAT-2026-0108/T02)                                     #
# --------------------------------------------------------------------------- #

#: Where an item's own working tree lives while it runs.
ITEM_BRANCH_PREFIX = "agent/"

#: Where an item's *uncommitted* work is parked when it ends without a commit
#: of its own. The item id is in the name on purpose: the failure this
#: replaces (#3179) was work whose only identification was the branch of a
#: different issue that happened to be checked out at the time.
WIP_BRANCH_PREFIX = "wip/"

_UNSAFE_REF_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


class ItemWorktreeError(RuntimeError):
    """A per-item working tree could not be created.

    Raised by `item_worktree` before it yields, so the caller parks the item
    rather than falling back to the shared tree -- running the item anyway is
    exactly the behaviour this module exists to remove.
    """


def ref_slug(item_id: str) -> str:
    """The item id, reduced to something git will accept as one ref component.

    Every character outside `[A-Za-z0-9._-]` collapses to a single `-`, which
    flattens `/` too. That is deliberate: `agent/a` and `agent/a/b` cannot
    both exist (git stores refs as files, so one would have to be a directory
    and a file at once), and an item id is free-form enough that both shapes
    are reachable. One component per item makes that conflict unreachable.
    """
    slug = _UNSAFE_REF_CHARS.sub("-", str(item_id or "")).strip("-.")
    while ".." in slug:
        slug = slug.replace("..", ".")
    return slug or "item"


def _git(runner: Callable, argv: list):
    """Run one git command and return `(returncode, stdout, stderr)`.

    Never raises: every caller here is either bookkeeping around an item that
    has already run, or a guard whose failure must read as "refuse", not as a
    traceback out of the middle of a run.
    """
    try:
        result = runner(argv, check=False)
    except Exception as exc:  # noqa: BLE001 - see docstring
        return (1, "", f"{type(exc).__name__}: {exc}")
    return (
        getattr(result, "returncode", 1),
        (getattr(result, "stdout", "") or "").strip(),
        (getattr(result, "stderr", "") or "").strip(),
    )


def dirty_paths(runner: Callable = _default_runner) -> Optional[List[str]]:
    """The *tracked* paths with uncommitted changes, `[]` when clean, `None`
    when the status could not be read.

    `is_dirty` answers the same question as a bool and stays for
    `restore_branch`'s use. This returns the paths because the caller refusing
    to dispatch owes the operator the *names*: "the tree is dirty" sends them
    to run `git status` themselves, which is the one thing they were about to
    do anyway.

    Untracked files are excluded deliberately. A new worktree is materialised
    from a commit, so nothing untracked in the main tree follows an item into
    its own -- and the run itself creates untracked files in the checkout it
    runs from, starting with `.specfuse/.agent.lock`. Counting those would
    make every run refuse itself. What the guard is actually looking for is
    committed content the operator has since modified, which is the state that
    makes "branched from HEAD" and "what the operator sees" disagree.
    """
    code, out, _ = _git(
        runner, ["git", "status", "--porcelain", "--untracked-files=no"]
    )
    if code != 0:
        return None
    paths = []
    for line in out.splitlines():
        # `XY PATH`, where XY is the two-column status. Splitting on
        # whitespace rather than slicing a fixed offset survives a leading
        # status column that has already been stripped off the first line.
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        entry = parts[1].strip()
        if " -> " in entry:  # a rename: report where the content ended up
            entry = entry.split(" -> ", 1)[1].strip()
        entry = entry.strip('"')
        if entry:
            paths.append(entry)
    return paths


def head_commit(runner: Callable = _default_runner) -> Optional[str]:
    """The commit every item of a run branches from, or `None` if unreadable.

    Resolved once and reused: items must all be cut from the same base, or
    item N inherits item N-1's commits and the attribution problem comes back
    in a form that looks like history rather than like a dirty tree.
    """
    code, out, _ = _git(runner, ["git", "rev-parse", "HEAD"])
    return out or None if code == 0 else None


@dataclass
class ItemWorktree:
    """One item's working tree, and what became of it.

    `wip_ref` is set only when the item ended with uncommitted edits and they
    were committed under it. `notes` carries anything the run summary should
    say about this tree -- a ref that was created, or a cleanup that could not
    be completed and left something on disk.
    """

    item_id: str
    slug: str
    path: Path
    branch: str
    base: str
    wip_ref: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    @property
    def working_dir(self) -> str:
        return str(self.path)


@contextmanager
def item_worktree(
    item_id: str,
    base: str = "HEAD",
    *,
    runner: Callable = _default_runner,
    report: Optional[Callable[[str], None]] = None,
    parent_dir: Optional[str] = None,
) -> Iterator[ItemWorktree]:
    """Run one item in its own working tree on its own branch.

    Adds `agent/<item_id>` at a fresh temporary directory cut from *base*,
    yields the `ItemWorktree` describing it, and on exit retires it:

    * **Committed work keeps its branch.** An item that committed (and
      pushed, or not) owns `agent/<item_id>`; the branch is left exactly
      where the item put it and no `wip/` ref is invented behind it.
    * **Uncommitted work is committed under `wip/<item_id>`.** Not discarded,
      not left in place for the next item to inherit -- named, so the run
      summary can point at it and an operator can `git show` it.
    * **Empty trees leave nothing.** A branch still at *base* is deleted with
      the worktree; a run that did nothing should look like it.

    Nothing here is allowed to destroy work in order to tidy up. If the
    uncommitted edits cannot be committed, or the worktree cannot be removed,
    the tree is left on disk and a note says where -- a stale directory is
    recoverable and a deleted fix is not.

    Raises `ItemWorktreeError` if the tree could not be created at all.
    """

    def _say(message: str) -> None:
        if report is not None:
            report(message)

    slug = ref_slug(item_id)
    branch = f"{ITEM_BRANCH_PREFIX}{slug}"
    holder = Path(tempfile.mkdtemp(prefix="specfuse-agent-", dir=parent_dir))
    path = holder / slug

    code, _, err = _git(
        runner, ["git", "worktree", "add", "-b", branch, str(path), base]
    )
    if code != 0:
        # Almost always "branch already exists" from an interrupted earlier
        # run. That branch may hold real commits, so it is not reset -- this
        # item takes a distinct name instead and the old one is left for the
        # operator.
        retry_branch = f"{ITEM_BRANCH_PREFIX}{slug}-{uuid.uuid4().hex[:8]}"
        retry_code, _, retry_err = _git(
            runner, ["git", "worktree", "add", "-b", retry_branch, str(path), base]
        )
        if retry_code != 0:
            shutil.rmtree(holder, ignore_errors=True)
            raise ItemWorktreeError(
                f"could not create a working tree for {item_id} at {path} — "
                f"{retry_err or err or 'git worktree add failed'}"
            )
        _say(
            f"{item_id}: '{branch}' already exists — this item is running on "
            f"'{retry_branch}' instead"
        )
        branch = retry_branch

    _, base_sha, _ = _git(runner, ["git", "rev-parse", base])
    handle = ItemWorktree(
        item_id=item_id,
        slug=slug,
        path=path,
        branch=branch,
        base=base_sha or base,
    )
    try:
        yield handle
    finally:
        _retire(handle, holder, runner=runner, say=_say)


def _retire(
    handle: ItemWorktree,
    holder: Path,
    *,
    runner: Callable,
    say: Callable[[str], None],
) -> None:
    """Commit anything left over, remove the tree, and drop a branch that
    holds nothing the repository does not already have."""
    path = str(handle.path)

    status_code, status_out, status_err = _git(
        runner, ["git", "-C", path, "status", "--porcelain"]
    )
    if status_code != 0:
        note = (
            f"{handle.item_id}: could not read its working tree's status "
            f"({status_err or 'git status failed'}) — left in place at {path}"
        )
        handle.notes.append(note)
        say(note)
        return

    if status_out:
        if not _commit_leftovers(handle, path, runner=runner, say=say):
            return  # the work is still on disk; removing the tree would lose it

    if not _remove_worktree(handle, path, holder, runner=runner, say=say):
        return

    _drop_branch_if_redundant(handle, runner=runner, say=say)


def _commit_leftovers(
    handle: ItemWorktree,
    path: str,
    *,
    runner: Callable,
    say: Callable[[str], None],
) -> bool:
    """Commit the tree's uncommitted edits under `wip/<item_id>`. Returns
    whether it is now safe to remove the tree."""
    add_code, _, add_err = _git(runner, ["git", "-C", path, "add", "-A"])
    message = (
        f"wip({handle.item_id}): work an agent run left uncommitted\n\n"
        f"Committed by the agent lane so the item that produced it is "
        f"recoverable by name. See {WIP_BRANCH_PREFIX}{handle.slug}."
    )
    commit_code, _, commit_err = _git(
        runner, ["git", "-C", path, "commit", "-q", "-m", message]
    )
    if add_code != 0 or commit_code != 0:
        note = (
            f"{handle.item_id}: ended with uncommitted edits that could NOT be "
            f"committed ({commit_err or add_err or 'git commit failed'}) — its "
            f"working tree is left at {path}; recover it before the next run"
        )
        handle.notes.append(note)
        say(note)
        return False

    wip_ref = f"{WIP_BRANCH_PREFIX}{handle.slug}"
    ref_code, _, ref_err = _git(
        runner, ["git", "-C", path, "branch", "--force", wip_ref, "HEAD"]
    )
    if ref_code != 0:
        note = (
            f"{handle.item_id}: its uncommitted edits are committed on "
            f"'{handle.branch}' but '{wip_ref}' could not be created "
            f"({ref_err or 'git branch failed'})"
        )
        handle.notes.append(note)
        say(note)
        return True

    handle.wip_ref = wip_ref
    note = (
        f"{handle.item_id}: ended without committing — its edits are committed "
        f"on '{wip_ref}' (git show {wip_ref})"
    )
    handle.notes.append(note)
    say(note)
    return True


def _remove_worktree(
    handle: ItemWorktree,
    path: str,
    holder: Path,
    *,
    runner: Callable,
    say: Callable[[str], None],
) -> bool:
    code, _, err = _git(runner, ["git", "worktree", "remove", "--force", path])
    if code != 0:
        note = (
            f"{handle.item_id}: its working tree at {path} could not be removed "
            f"({err or 'git worktree remove failed'}) — remove it by hand"
        )
        handle.notes.append(note)
        say(note)
        return False
    shutil.rmtree(holder, ignore_errors=True)
    return True


def _drop_branch_if_redundant(
    handle: ItemWorktree,
    *,
    runner: Callable,
    say: Callable[[str], None],
) -> None:
    """Delete `agent/<item_id>` when it holds nothing that would be lost.

    Two cases qualify: the branch never moved off the base, or everything on
    it is already reachable from the `wip/` ref that now names it. Any other
    branch -- one carrying commits the item made and possibly pushed -- is
    left alone, because deleting it is precisely the "finished work with no
    name" failure in reverse.
    """
    code, branch_sha, _ = _git(
        runner, ["git", "rev-parse", "--verify", "-q", f"refs/heads/{handle.branch}"]
    )
    if code != 0 or not branch_sha:
        return  # already gone, or the item moved off it and it never existed

    redundant = branch_sha == handle.base
    if not redundant and handle.wip_ref:
        contained, _, _ = _git(
            runner,
            [
                "git",
                "merge-base",
                "--is-ancestor",
                handle.branch,
                handle.wip_ref,
            ],
        )
        redundant = contained == 0

    if not redundant:
        return

    del_code, _, del_err = _git(runner, ["git", "branch", "-D", handle.branch])
    if del_code != 0:
        say(
            f"{handle.item_id}: left branch '{handle.branch}' behind — "
            f"{del_err or 'git branch -D failed'}"
        )
