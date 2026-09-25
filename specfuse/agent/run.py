# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The conductor loop and `specfuse-agent` entry point (FEAT-2026-0049/T04).

Assembles T01's lock (`specfuse.loop._filelock.acquire_agent_lock`), T02's
snapshot (`specfuse.agent.state.gather_snapshot`), and T03's budget
(`specfuse.agent.budget.RunBudget`) into select-execute-reconcile-repeat.

**No provider ships here.** `ActionProvider` is the protocol a provider
satisfies; the loop runs it against an empty registry, which must drain
cleanly and immediately (criterion 1). Gate 2 supplies the four real
providers.

Selection order is policy, not judgment: `rules.bugs.preempt` (read directly
via `specfuse.loop.agent_policy`, since T02's snapshot does not carry this
dial) decides whether bug-kind items outrank feature-kind items; the
snapshot's `queue:` order settles feature-kind items among themselves. An
item policy cannot place — an unknown `kind`, or a feature `queue_key` absent
from `queue:` — is parked with an escalation rather than guessed into a
position (the "priority is policy, not intelligence" principle this WU's
spec names). A provider whose `execute()` raises is parked the same way; the
run continues rather than ending.

The loop's own `runner` never touches git. It is used only to build the T02
snapshot's read-only `gh ... list` calls, and is never handed to a provider —
`tests/test_agent_run.py` asserts every call it sees is a non-mutating `gh`
one. What the loop calls on a provider is `execute()` and `reconcile()` and
nothing else.

With `isolate_items=True` the loop does bracket each item with
`specfuse.agent.worktree.item_worktree`, which adds a worktree, may commit
that worktree's leftovers, and removes it again (FEAT-2026-0108/T02). Those
calls are that module's, through its own subprocess runner, on a tree no
provider shares — the property the invariant above protects, that a provider
cannot be handed a git transport by the conductor, is untouched by it.
"""

from __future__ import annotations

import argparse
import inspect
import re
import subprocess
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, Optional, Protocol, Sequence

from specfuse.agent.budget import (
    STOP_CAP,
    STOP_DRAINED,
    STOP_PAUSE,
    RunBudget,
)
from specfuse.agent import worktree
from specfuse.agent.repo_detect import detect_repo
from specfuse.agent.state import AgentSnapshot, gather_snapshot
from specfuse.loop import agent_policy
from specfuse.loop._filelock import acquire_agent_lock
from specfuse.loop.build_provenance import warn_if_out_of_tree
from specfuse.loop.escalation import (
    CREATED_NUMBER_UNKNOWN,
    annotate_escalation,
    emit_escalation,
)

DEFAULT_SPECFUSE_DIR = Path(".specfuse")
DEFAULT_AGENT_LOCK_NAME = ".agent.lock"

STATUS_COMPLETED = "completed"
STATUS_ESCALATED = "escalated"

#: The run refused to start: per-item isolation was asked for and the tree it
#: would branch every item from already carries someone else's edits
#: (FEAT-2026-0108/T02). Not one of `budget.py`'s stop reasons -- nothing was
#: budgeted, because nothing was dispatched.
STOP_DIRTY_TREE = "dirty_tree"
#: The run could not read the queue it was meant to work through (#3392).
#: Distinct from `STOP_DRAINED`, which means the opposite: a drained run saw
#: everything there was and finished it. Reported identically, they are
#: indistinguishable in the summary — the part an operator reads and the only
#: part automation parses — so a nightly run whose credentials broke looks like
#: a quiet backlog.
STOP_SNAPSHOT_UNREADABLE = "snapshot_unreadable"

KIND_BUG = "bug"
KIND_FEATURE = "feature"
KIND_TRIAGE = "triage"
KIND_ESCALATION_ANSWER = "escalation-answer"
KIND_FINDING_DIAGNOSE = "finding-diagnose"
KIND_FINDING_AUTOFIX = "finding-autofix"

#: The run stopped because the same failure kept recurring — its cause is the
#: run's environment, not any one item (#3343).
STOP_RUN_LEVEL_FAILURE = "run_level_failure"

#: How many consecutive escalations sharing one cause before the run stops.
#:
#: Small on purpose. The measured case is what sets it: a headless command that
#: did not resolve produced 55 `could_not_proceed` escalations — 55 comments,
#: 55 `needs-human` labels, 16 minutes, one defect in the runner's own setup.
#: `needs-human` is in `_HUMAN_OWNED_LABELS`, so the lane then skips every one
#: of those issues, and a single setup defect removes the whole bug queue from
#: automation until a human clears the labels by hand. Three is enough evidence
#: that the cause is not item-specific and cheap enough to be wrong about.
IDENTICAL_FAILURE_LIMIT = 3

#: Digits are what make two instances of one cause look different: the issue
#: number in "issue #1916: Unknown command" changes per item and the cause does
#: not. Replaced wholesale rather than parsed — a signature is for comparison,
#: never for display.
_FAILURE_DIGITS_RE = re.compile(r"#?\d+")


def failure_signature(item: "ActionItem", outcome: "ActionOutcome") -> str:
    """A comparable stand-in for "this failed the same way as that" (#3343).

    Kind plus the escalation detail with per-item numbers flattened, so two
    issues failing on the same missing command match while a genuinely
    different cause does not. Deliberately coarse: the breaker's job is to
    notice a *repeated environmental* failure, and a signature that is too
    precise never fires — which is the state that cost 55 escalations.
    """
    detail = (outcome.detail or "").strip().lower()
    return f"{item.kind}|{_FAILURE_DIGITS_RE.sub('N', detail)}"

#: The item kinds that open a pull request, and so the ones
#: `budgets.max_open_prs` gates (#3340). Both dispatch a headless
#: `/specfuse:fix-bug`, whose `completed` contract is an opened PR.
#: `KIND_FEATURE` is deliberately absent: `FeatureProvider` runs the driver,
#: which runs gates and commits — `/wrap-feature` opens that PR, interactively,
#: outside any agent run. These are the same two kinds `_select_next` already
#: ranks together in its bug tier.
PR_OPENING_KINDS = frozenset({KIND_BUG, KIND_FINDING_AUTOFIX})


class AgentLockHeldError(RuntimeError):
    """Another agent process already holds `.specfuse/.agent.lock`.

    Carries the lock file's path so the caller can name it in a plain
    message instead of surfacing a raw `BlockingIOError` traceback.
    """

    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        super().__init__(
            f"another specfuse-agent run holds the lock at {lock_path} — "
            "wait for it to finish, or confirm it is stale before removing "
            "the lock file yourself."
        )


@dataclass(frozen=True)
class ActionItem:
    """One unit of advertised work.

    `queue_key` is the string a feature-kind item is matched against in
    `AgentSnapshot.queue` — it is meaningless for `kind="bug"` and may be
    `None` there.
    """

    item_id: str
    kind: str
    summary: str = ""
    queue_key: Optional[str] = None


@dataclass(frozen=True)
class EscalationPayload:
    """The six parts `specfuse.loop.escalation.emit_escalation` requires,
    supplied by a provider that knows the situation — the loop never
    composes these itself (see the WU's note on `render_escalation_body`'s
    two-option minimum)."""

    done_so_far: str
    issue_summary: str
    decision_needed: str
    why_not_auto: str
    options: Sequence[tuple]
    recommendation: str
    category: str = "blocked-wu"
    #: The GitHub issue this escalation is *about*. When set, the six parts
    #: are recorded on that issue — comment, `needs-human` + category labels,
    #: assignee — instead of filing a separate tracking issue. A provider
    #: working from an issue should always set it: a new issue saying "issue
    #: #240's PR was declined" costs the reader a correlation step, and a
    #: halt that recurs files one more each time. Left `None` for work that
    #: is about no issue (a gate review, an unplaceable queue entry), which
    #: still files through `emit_escalation`.
    target_issue: Optional[int] = None


@dataclass(frozen=True)
class ActionOutcome:
    """What a provider's `execute()` reports for one item.

    `spend` is real tokens, not a proxy — a provider that dispatches a
    headless `claude` session reports it through
    `specfuse.agent.invoke.usage_spend(invoke_result.usage)`
    (FEAT-2026-0108/T01): input plus output tokens, cache reads excluded, so
    it lines up with the driver's own cost line. It defaults to zero so a
    provider that dispatches nothing, or whose session reported no usage
    envelope, leaves the run's total spend untouched. `escalation`, when set
    on a `STATUS_ESCALATED` outcome, is recorded — on `target_issue` when the
    payload names one, otherwise as a fresh needs-human issue via
    `emit_escalation`."""

    status: str
    detail: str = ""
    spend: int = 0
    escalation: Optional[EscalationPayload] = None
    #: Why this escalation is deliberately recorded nowhere (#1970).
    #:
    #: An escalating outcome with neither a payload nor a waiver leaves no
    #: trace at all: the run summary mentions it and the terminal scrolls.
    #: Nine such paths shipped across three providers, every one of them by
    #: omission rather than by decision.
    #:
    #: Not every escalation deserves a GitHub record, though. An item that
    #: vanished from the snapshot between `advertise` and `execute` is a
    #: benign race with nothing for a human to decide, and filing a
    #: needs-human issue for it is noise rather than a trace. Such a path
    #: sets this field to the reason instead, which `tests/
    #: test_provider_escalation_traces.py` accepts in place of a payload —
    #: so "we thought about it" is distinguishable from "we forgot", the
    #: same shape as `NON_JUDGE_MODULES` and
    #: `DEPENDENCY_MANIFEST_NAMED_UNCOVERED`.
    escalation_waived: str = ""
    #: Whether this escalation could have an environmental cause (#3372).
    #:
    #: Only an outcome reached WITHOUT reading the item can be about the run's
    #: environment: a dispatch that failed, a session that produced no outcome
    #: marker, a crash. An outcome reached BY reading the item is a judgement
    #: about that item — `/fix-bug`'s `refused` says the work is not bug-sized,
    #: `ci_not_green` and `pr_not_found` are facts about that issue's PR — and
    #: three in a row says the queue holds three such issues, not that anything
    #: is broken.
    #:
    #: #3343's breaker counted every escalation and stopped a run that was
    #: working: two fixes merged, one held on red CI, six correctly declined,
    #: 19 items never reached, and an escalation asserting an environment
    #: cause a human then had to disprove.
    #:
    #: **Defaults False so a provider must opt in.** A provider that says
    #: nothing never trips the breaker, rather than tripping it by omission.
    environmental: bool = False


class ActionProvider(Protocol):
    """The protocol a gate-2 action provider satisfies.

    Three verbs, matching the WU's own language: advertise available work,
    execute one item, report an outcome. `advertise` is called once per
    loop iteration against the run's single snapshot — a provider owns
    shrinking its own list as items are handled; the loop additionally
    tracks handled item ids so a provider that keeps re-advertising a
    finished item cannot stall the run.
    """

    def advertise(self, snapshot: AgentSnapshot) -> Sequence[ActionItem]:
        ...

    def execute(self, item: ActionItem) -> ActionOutcome:
        ...

    def reconcile(self, item: ActionItem, outcome: ActionOutcome) -> None:
        ...


@dataclass(frozen=True)
class Escalation:
    item_id: str
    reason: str


@dataclass(frozen=True)
class RunSummary:
    """The run report (criterion 6): counts, the closed-set stop reason,
    and actual elapsed time — never the configured cap."""

    items_attempted: int
    items_completed: int
    items_escalated: int
    stop_reason: str
    elapsed_minutes: float
    tokens_spent: int = 0
    escalations: tuple = ()
    #: `wip/<item_id>` refs holding work an item finished but never committed
    #: (FEAT-2026-0108/T02). Named here because the alternative -- the state
    #: #3179 reported -- is a finished fix whose only trace is a console line
    #: about a branch belonging to a different issue.
    wip_refs: tuple = ()
    #: Issue numbers that gained a `bug` triage marker during this run and
    #: were never dispatched (#3338). The refresh below normally empties this
    #: -- a bug triaged at item 3 is dispatched at item 4 -- so a non-empty
    #: value means the run ended first (a cap, a pause) or the refresh could
    #: not read the listing. Either way the operator needs to be told to
    #: re-run, because a triage-only run otherwise looks like a bug lane that
    #: declined everything.
    newly_triaged_bugs_undispatched: tuple = ()


def _bug_marked_numbers(snapshot: AgentSnapshot) -> set:
    """Issue numbers whose body carries a `bug` triage marker right now."""
    return {issue.number for issue in snapshot.issues if issue.triage_category == "bug"}


def _refresh_snapshot(
    previous: AgentSnapshot,
    *,
    runner: Callable,
    repo: str,
    policy_path: Optional[str],
    features_root: Optional[Path],
    report: Callable[[str], None],
) -> AgentSnapshot:
    """Re-gather the snapshot between items, keeping any section a fresh read
    could not produce (#3338).

    The run used to gather once, before the loop, and hand that one value to
    every provider on every pass. That made a provider's output invisible to
    the next provider within the same run: `TriageProvider.execute` writes a
    `bug` marker into an issue body, `BugsProvider.advertise` reads the marker
    off `snapshot.issues`, and the snapshot between them never moved -- so a
    run triaged 72 issues, marked 55 of them `bug`, and dispatched the bug
    lane against none. The same staleness applies to any provider whose work
    unblocks another's: an answered escalation drops the `needs-human` label
    the bug lane filters on, and a driver run changes the feature folders
    `snapshot.features` was read from.

    The snapshot is still a value the selector reads rather than a set of
    calls it issues -- the refresh happens BETWEEN iterations, so within one
    `_select_next` nothing moves underneath it.

    **A failed section keeps its previous contents rather than blanking.**
    `gather_snapshot` reports an unreadable section as empty with an error
    set, which is the right shape for a run's opening read and exactly the
    wrong one mid-run: a transient `gh` failure would silently retire every
    remaining item in a lane as "drained". So a section that errors here and
    did not error before is carried forward from the previous snapshot and
    the failure is reported.
    """
    try:
        fresh = gather_snapshot(
            runner,
            repo,
            policy_path=policy_path,
            features_root=features_root,
        )
    except Exception as exc:  # noqa: BLE001 - a refresh must never end a run
        report(
            f"snapshot refresh failed — {type(exc).__name__}: {exc} "
            f"(the previous snapshot still stands)"
        )
        return previous

    carried = {}
    for section, error_field, value_field in (
        ("issues", "issues_error", "issues"),
        ("PRs", "prs_error", "prs"),
    ):
        fresh_error = getattr(fresh, error_field)
        if fresh_error and not getattr(previous, error_field):
            report(
                f"snapshot refresh: {section} unreadable — {fresh_error} "
                f"(the previous listing still stands)"
            )
            carried[value_field] = getattr(previous, value_field)
            carried[error_field] = getattr(previous, error_field)
    return replace(fresh, **carried) if carried else fresh


def _resolve_bugs_preempt(policy_path: Optional[str]) -> bool:
    """Resolve `rules.bugs.preempt`. Same safe-default shape as
    `agent_policy.resolve_bug_automerge` / `resolve_triage_auto`: an absent
    policy file, an absent key, or a non-bool value all resolve to `False`
    (bugs do not jump the feature queue) rather than raising."""
    try:
        policy = agent_policy.load_policy(policy_path)
    except FileNotFoundError:
        return False
    rules = policy.get("rules") if isinstance(policy, dict) else None
    if not isinstance(rules, dict):
        return False
    bugs = rules.get("bugs")
    if not isinstance(bugs, dict):
        return False
    return bugs.get("preempt") is True


def _default_runner(argv: list, check: bool = False, timeout: Optional[float] = None):
    """The real subprocess runner. Forwards *timeout* to `subprocess.run`
    (FEAT-2026-0108/T03) so a caller that bounds one call's wall-clock time --
    `BugsProvider.execute`'s headless `/fix-bug` dispatch, the one call this
    exists for -- gets a real `subprocess.TimeoutExpired` when the process
    outruns it, rather than the session's own turn or wall limit being the
    only thing that ever ends it (#3178)."""
    return subprocess.run(
        argv, check=check, capture_output=True, text=True, timeout=timeout
    )


def _default_reporter(message: str) -> None:
    """Print one timestamped progress line, matching `specfuse run`'s log.

    An unattended run that prints nothing until it ends is unreadable while
    it is happening: the first live run took 85 minutes and its first output
    was the summary, so an operator watching had no way to tell a working
    item from a hung one. Same shape as the driver's per-WU line
    (`loop.py:6368`) so one operator reads both the same way.
    """
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def _took(clock: Callable[[], float], started: float) -> str:
    """Render an item's wall-clock cost. The first live run averaged 8.5
    minutes an item and reported no per-item time at all, so which items were
    expensive was unrecoverable from the summary."""
    seconds = max(0.0, clock() - started)
    if seconds < 90:
        return f"{seconds:.0f}s"
    return f"{seconds / 60:.1f}m"


def _record_escalation(
    item: ActionItem,
    outcome: "ActionOutcome",
    *,
    repo: str,
    runner: Callable,
    policy_path: Optional[str],
) -> str:
    """Record an escalating outcome and return the run-summary reason line.

    Two destinations, one owner. A payload naming a `target_issue` is
    recorded on that issue; one without files a tracking issue. A provider
    that reports no payload at all leaves no trace anywhere, and the summary
    line says exactly that rather than guessing.
    """
    reason = outcome.detail
    escalation = outcome.escalation
    if escalation is None:
        # Previously "(summary only, no issue filed)" — which was wrong
        # whenever something further down had in fact filed one, and was
        # printed for exactly that case on four items of the first live run.
        # It is now reachable only when nothing recorded anything.
        if outcome.escalation_waived:
            suffix = f"(not recorded by design — {outcome.escalation_waived})"
        else:
            suffix = "(not recorded on GitHub — this run's console is the only trace)"
        return f"{reason} {suffix}" if reason else f"escalated {suffix}"

    assignee = agent_policy.resolve_escalation_assignee(policy_path)
    if escalation.target_issue is not None:
        annotate_escalation(
            escalation.target_issue,
            item.item_id,
            category=escalation.category,
            repo=repo,
            done_so_far=escalation.done_so_far,
            issue_summary=escalation.issue_summary,
            decision_needed=escalation.decision_needed,
            why_not_auto=escalation.why_not_auto,
            options=escalation.options,
            recommendation=escalation.recommendation,
            assignee=assignee,
            runner=runner,
        )
        suffix = f"(recorded on issue #{escalation.target_issue})"
    else:
        issue_id = emit_escalation(
            item.item_id,
            category=escalation.category,
            repo=repo,
            done_so_far=escalation.done_so_far,
            issue_summary=escalation.issue_summary,
            decision_needed=escalation.decision_needed,
            why_not_auto=escalation.why_not_auto,
            options=escalation.options,
            recommendation=escalation.recommendation,
            assignee=assignee,
            runner=runner,
        )
        if not issue_id:
            suffix = "(escalation could NOT be filed — no GitHub record exists)"
        elif issue_id == CREATED_NUMBER_UNKNOWN:
            suffix = "(escalation filed, but its issue number could not be read)"
        else:
            suffix = f"(filed as issue {issue_id})"
    return f"{reason} {suffix}" if reason else suffix.strip("()")


def _select_next(
    providers: Sequence[ActionProvider],
    snapshot: AgentSnapshot,
    bugs_preempt: bool,
    handled_ids: set,
    disabled: Optional[set] = None,
    on_advertise_error: Optional[Callable[[object, Exception], None]] = None,
    suppressed_kinds: "frozenset | None" = None,
):
    """Return `("execute", provider, item)`, `("escalate", item, reason)`,
    or `("drained", None, None)`.

    Ranks every still-unhandled candidate the registered providers
    advertise. Feature-kind items rank by their position in
    `snapshot.queue`; bug-kind items rank ahead of all features when
    `rules.bugs.preempt` is true, behind all ranked features otherwise.
    Anything policy cannot place (an unresolvable `queue_key`, an unknown
    `kind`) is escalated rather than guessed — one per call, so the caller's
    loop re-evaluates after each escalation instead of guessing an order
    among several unresolvable items too.

    **A provider that raises in `advertise()` loses itself, not the run.**
    This loop was unguarded, so one raising provider ended the whole run and
    took every healthy provider's work with it — observed as #1746, where
    `FeatureProvider.advertise` raised `AttributeError` on the default
    invocation and every shipped behaviour of the command became reachable
    only by passing `--features-root` explicitly. That fix normalised the one
    cause; the structural gap stayed, and there are six providers now.

    *suppressed_kinds* names kinds this pass must not start. It is how
    `budgets.max_open_prs` is enforced (#3340): at the cap, the kinds that
    open a pull request advertise as usual and are simply not selected.

    A provider that raises is added to *disabled* and skipped for the rest of
    the run, with *on_advertise_error* called once for it. Excluding it
    rather than retrying each iteration is deliberate: `advertise` runs every
    loop pass, so a permanently-broken provider would otherwise report on
    every one, and a run whose log is mostly one repeated traceback is no
    more readable than the crash it replaced.
    """
    disabled = disabled if disabled is not None else set()
    candidates = []
    for provider in providers:
        if id(provider) in disabled:
            continue
        try:
            advertised = tuple(provider.advertise(snapshot))
        except Exception as exc:  # noqa: BLE001 - one provider must not end the run
            disabled.add(id(provider))
            if on_advertise_error is not None:
                on_advertise_error(provider, exc)
            continue
        for item in advertised:
            if item.item_id in handled_ids:
                continue
            if suppressed_kinds and item.kind in suppressed_kinds:
                # Not escalated and not marked handled: a suppressed kind is
                # work the run declines to start right now, not work that
                # failed. Leaving it unhandled means a later pass picks it up
                # if the condition lifts -- a PR merged mid-run frees a slot.
                continue
            candidates.append((provider, item))

    if not candidates:
        return ("drained", None, None)

    ranked = []
    unresolved = []
    for provider, item in candidates:
        if item.kind == KIND_ESCALATION_ANSWER:
            ranked.append(((-1, 0), provider, item))
        elif item.kind == KIND_BUG or item.kind == KIND_FINDING_AUTOFIX:
            tier = 0 if bugs_preempt else 2
            ranked.append(((tier, 0), provider, item))
        elif item.kind == KIND_FEATURE:
            if item.queue_key is not None and item.queue_key in snapshot.queue:
                rank = snapshot.queue.index(item.queue_key)
                ranked.append(((1, rank), provider, item))
            else:
                unresolved.append(
                    (provider, item, f"queue_key {item.queue_key!r} is not in policy queue:")
                )
        elif item.kind == KIND_FINDING_DIAGNOSE:
            ranked.append(((3, 0), provider, item))
        elif item.kind == KIND_TRIAGE:
            ranked.append(((3, 1), provider, item))
        else:
            unresolved.append((provider, item, f"unknown item kind {item.kind!r}"))

    if ranked:
        ranked.sort(key=lambda triple: triple[0])
        _, provider, item = ranked[0]
        return ("execute", provider, item)

    _, item, reason = unresolved[0]
    return ("escalate", item, reason)


def _accepts_working_dir(func: Callable) -> bool:
    """Whether *func* will take a `working_dir=` keyword.

    Providers predate per-item isolation and there are six of them, so the
    directory is offered rather than imposed: a provider that declares the
    parameter (or `**kwargs`) is handed its tree, and one that does not keeps
    the signature its own tests already cover.
    """
    try:
        params = inspect.signature(func).parameters
    except (TypeError, ValueError):  # a C callable, or an unreadable signature
        return False
    if "working_dir" in params:
        return True
    return any(
        param.kind is inspect.Parameter.VAR_KEYWORD for param in params.values()
    )


def _call_execute(
    provider: ActionProvider,
    item: ActionItem,
    working_dir: Optional[str],
    report: Callable[[str], None],
    unisolated: set,
):
    """Execute one item, handing the provider its working directory.

    Three ways in, in order of directness: an `execute(item, working_dir=)`
    parameter; the `_working_dir` attribute the four dispatching providers
    already hold and pass down to `build_invocation` (restored afterwards, so
    a provider is never left pointing at a directory that no longer exists);
    or neither, in which case the item runs where the run does and the
    operator is told once per provider rather than once per item.
    """
    if working_dir is None:
        return provider.execute(item)

    if _accepts_working_dir(provider.execute):
        return provider.execute(item, working_dir=working_dir)

    if hasattr(provider, "_working_dir"):
        previous = provider._working_dir
        provider._working_dir = working_dir
        try:
            return provider.execute(item)
        finally:
            provider._working_dir = previous

    name = type(provider).__name__
    if name not in unisolated:
        unisolated.add(name)
        report(
            f"{name} takes no working directory — its items run in the "
            f"repository root, not in a tree of their own"
        )
    return provider.execute(item)


def _execute_item(
    provider: ActionProvider,
    item: ActionItem,
    *,
    base: Optional[str],
    report: Callable[[str], None],
    unisolated: set,
):
    """Run one item and return `(outcome, failure, tree)`.

    Exactly one of *outcome* and *failure* is set; *tree* is the
    `worktree.ItemWorktree` the item ran in, or `None` when isolation is off
    or the tree could not be created. The failure is returned rather than
    raised so the caller's park-and-continue path stays the single place that
    decides what a failed item costs the run.

    **The tree is retired even when `execute` raises.** That is the whole
    point: a session that died half-way is exactly the one whose edits would
    otherwise be inherited by the next item, and it is retired through the
    same path as a clean one, so its work still ends up on a `wip/` ref that
    names it.
    """
    if base is None:
        try:
            return (_call_execute(provider, item, None, report, unisolated), None, None)
        except Exception as exc:  # noqa: BLE001 - parked by the caller
            return (None, exc, None)

    tree = None
    outcome = None
    failure = None
    try:
        with worktree.item_worktree(item.item_id, base, report=report) as tree:
            try:
                outcome = _call_execute(
                    provider, item, tree.working_dir, report, unisolated
                )
            except Exception as exc:  # noqa: BLE001 - parked by the caller
                failure = exc
    except Exception as exc:  # noqa: BLE001 - the tree itself could not be made
        failure = exc
    return (outcome, failure, tree)


def _refuse_dirty_tree(reason: str, report: Callable[[str], None]) -> RunSummary:
    """The summary a run returns when it declines to dispatch anything.

    Zero attempted, zero completed, and the reason where both a human and the
    summary's own reader will find it. Refusing is the conservative direction:
    branching every item off a base that already carries edits is how one
    item's work gets attributed to another (#3179), and the operator can clear
    the tree in a second once they know which paths are in the way.
    """
    report(f"run refused to start — {reason}")
    return RunSummary(
        items_attempted=0,
        items_completed=0,
        items_escalated=1,
        stop_reason=STOP_DIRTY_TREE,
        elapsed_minutes=0.0,
        tokens_spent=0,
        escalations=(Escalation(item_id="run", reason=reason),),
    )


def _refuse_unreadable_snapshot(reason: str, *, report) -> "RunSummary":
    """Refuse a run whose issue listing failed, rather than draining it (#3392).

    Every provider that matters reads `snapshot.issues`, so a run without it
    can do nothing except mislead. Shaped like `_refuse_dirty_tree`: zero
    attempted, zero completed, one escalation carrying the reason, and a
    distinct stop reason so the summary cannot be mistaken for a healthy run
    against an empty queue.

    Refusing is the conservative direction here for the same reason it is
    there. A blind run that dispatches nothing has cost nothing; a blind run
    reported as `drained` costs the operator their belief that the queue is
    empty.
    """
    report(f"run refused to start — {reason}")
    return RunSummary(
        items_attempted=0,
        items_completed=0,
        items_escalated=1,
        stop_reason=STOP_SNAPSHOT_UNREADABLE,
        elapsed_minutes=0.0,
        tokens_spent=0,
        escalations=(Escalation(item_id="run:snapshot", reason=reason),),
    )


def exit_code_for(stop_reason: str) -> int:
    """The process exit code a run ending in *stop_reason* should report.

    Non-zero only for a refusal — a run that did not happen. Every outcome,
    including `drained`, keeps 0: those are runs that ran. Narrow on purpose,
    so a new stop reason does not silently become a failing exit code for
    whatever automation is watching.
    """
    return 1 if stop_reason == STOP_SNAPSHOT_UNREADABLE else 0


def _dirty_tree_reason(paths) -> str:
    shown = ", ".join(paths[:10])
    if len(paths) > 10:
        shown += f", and {len(paths) - 10} more"
    return (
        f"the working tree has uncommitted changes ({shown}), and every item "
        f"would be branched from it. Commit, stash or discard them, then "
        f"re-run."
    )


def run_agent(
    *,
    specfuse_dir: Path = DEFAULT_SPECFUSE_DIR,
    repo: str,
    runner: Callable = _default_runner,
    providers: Sequence[ActionProvider] = (),
    policy_path: Optional[str] = None,
    features_root: Optional[Path] = None,
    clock: Callable[[], float] = time.monotonic,
    max_minutes: Optional[float] = None,
    max_tokens: Optional[int] = None,
    max_items: Optional[int] = None,
    pause_marker: Optional[Path] = None,
    reporter: Optional[Callable[[str], None]] = None,
    isolate_items: bool = False,
) -> RunSummary:
    """Run the select-execute-reconcile loop to completion and return the
    summary. Raises `AgentLockHeldError` if another agent already holds
    `.specfuse/.agent.lock` — never a raw `BlockingIOError`.

    *reporter* receives one progress line per event as the run happens;
    `None` means print them, and passing a collector silences stdout. Tests
    pass a list's `append`.

    *isolate_items* gives every item its own `git worktree` on its own
    `agent/<item_id>` branch, all cut from the commit HEAD names when the run
    starts (FEAT-2026-0108/T02). It is off by default because it is a
    statement about the process's own checkout: a caller that injects
    providers into a tree it does not own — every test here does — must not
    have branches created under it as a side effect of calling this function.
    `main()`, which *is* the operator's process boundary, turns it on. With it
    on, a dirty starting tree refuses to dispatch at all: see
    `_refuse_dirty_tree`."""
    report = reporter if reporter is not None else _default_reporter
    lock_path = Path(specfuse_dir) / DEFAULT_AGENT_LOCK_NAME
    try:
        lock_fd = acquire_agent_lock(Path(specfuse_dir))
    except BlockingIOError as exc:
        raise AgentLockHeldError(lock_path) from exc

    try:
        report(f"run started — repo {repo}")

        base_commit = None
        if isolate_items:
            paths = worktree.dirty_paths()
            if paths is None:
                return _refuse_dirty_tree(
                    "the working tree's status could not be read, so no item "
                    "can be given a tree of its own",
                    report,
                )
            if paths:
                return _refuse_dirty_tree(_dirty_tree_reason(paths), report)
            base_commit = worktree.head_commit()
            if base_commit is None:
                return _refuse_dirty_tree(
                    "HEAD could not be resolved, so there is no commit to "
                    "branch this run's items from",
                    report,
                )
            report(f"per-item worktrees on — every item branches from {base_commit[:12]}")

        snapshot = gather_snapshot(
            runner,
            repo,
            policy_path=policy_path,
            features_root=features_root,
        )
        bugs_preempt = _resolve_bugs_preempt(policy_path)
        report(
            f"snapshot: {len(snapshot.issues)} open issues, "
            f"{len(snapshot.prs)} open PRs, {len(snapshot.features)} features, "
            f"queue={len(snapshot.queue)} — bugs_preempt={bugs_preempt}"
        )
        for section, error in (
            ("issues", snapshot.issues_error),
            ("PRs", snapshot.prs_error),
        ):
            if error:
                report(f"snapshot: {section} unreadable — {error}")

        # #3392: an unreadable issue listing is not an empty queue. Every
        # provider that matters reads `snapshot.issues`, so continuing here
        # finds no candidates and stops with `drained` — "worked through
        # everything there was" reported for "could not see anything". Measured
        # with nine dispatchable bugs in the queue at the time.
        if snapshot.issues_error:
            return _refuse_unreadable_snapshot(
                f"the issue listing failed, so the queue could not be read: "
                f"{snapshot.issues_error}",
                report=report,
            )

        # The PR listing failing is NOT a refusal: `max_open_prs` deliberately
        # reads an unreadable listing as zero rather than firing on a number
        # the run could not measure. But that leaves the cap silently disabled
        # for this run, so the summary says so rather than the operator finding
        # it in the log. Whether it should refuse instead is a live question
        # (#3392 item 3) and not decided here.
        if snapshot.prs_error:
            report(
                "snapshot: max_open_prs is NOT enforced this run — the PR "
                "listing could not be read, so the cap has no number to "
                "measure against"
            )

        budget_kwargs = {}
        if pause_marker is not None:
            budget_kwargs["pause_marker"] = pause_marker
        # #3340: agent-policy.yml declared budgets that nothing read, so a plain
        # run was uncapped while the policy said otherwise. A flag still wins --
        # it is the narrower, more deliberate statement for one run.
        _tokens = agent_policy.resolve_max_tokens(max_tokens, policy_path)
        _items = agent_policy.resolve_max_items(max_items, policy_path)
        # #3340's remaining half: the key was required, proposed and reviewed,
        # and read by nothing that could act on it. No flag counterpart -- this
        # is a property of the repository's state, not of one run's appetite.
        _open_pr_cap = agent_policy.resolve_max_open_prs(policy_path)

        def _source(flag, resolved):
            if flag is not None:
                return "flag"
            return "policy" if resolved is not None else "none"

        budget = RunBudget(
            clock=clock,
            max_minutes=max_minutes,
            max_tokens=_tokens,
            max_items=_items,
            **budget_kwargs,
        )
        report(agent_policy.describe_budget_sources(
            max_minutes=(max_minutes, "flag" if max_minutes is not None else "none"),
            max_tokens=(_tokens, _source(max_tokens, _tokens)),
            max_items=(_items, _source(max_items, _items)),
            max_open_prs=(_open_pr_cap, "policy" if _open_pr_cap is not None else "none"),
        ))

        # #3338: what was already marked `bug` before any item ran. The
        # difference against the final snapshot is what this run's own triage
        # produced, which is what the summary owes the operator when the run
        # ends before dispatching it.
        bugs_marked_at_start = _bug_marked_numbers(snapshot)

        items_completed = 0
        escalations = []
        wip_refs = []
        handled_ids = set()
        snapshot_stale = False
        disabled_providers: set = set()
        #: Whether the open-PR ceiling is currently engaged. Held across passes
        #: only so the report fires on each transition rather than every pass:
        #: `snapshot.prs` is re-read between items (#3338), so a PR merged
        #: mid-run genuinely lifts this and the operator should see both edges.
        open_prs_suppressed = False
        #: (signature, consecutive count) for the run-level failure breaker
        #: (#3343). Reset by an escalation with a different cause and by any
        #: completed item — a run making progress is not in the state this
        #: breaker exists to stop.
        last_failure_signature = None
        consecutive_identical_failures = 0
        unisolated_providers: set = set()
        stop_reason = STOP_DRAINED

        def _provider_failed_to_advertise(provider, exc) -> None:
            """Record a provider dropping out — once, by name, in the summary."""
            name = type(provider).__name__
            reason = (
                f"{type(exc).__name__}: {exc} — provider disabled for the rest "
                f"of this run; its work is not being picked up"
            )
            escalations.append(Escalation(item_id=f"provider:{name}", reason=reason))
            report(f"{name} failed to advertise — {reason}")

        while True:
            if budget.pause_requested():
                stop_reason = STOP_PAUSE
                break
            if not budget.may_start_next_item():
                stop_reason = STOP_CAP
                break

            if snapshot_stale:
                snapshot = _refresh_snapshot(
                    snapshot,
                    runner=runner,
                    repo=repo,
                    policy_path=policy_path,
                    features_root=features_root,
                    report=report,
                )
                snapshot_stale = False

            # A failed PR listing leaves `snapshot.prs` empty with
            # `prs_error` set. That reads as zero here, deliberately: the cap
            # must not fire on a number the run could not measure, and #3338's
            # refresh already carries the previous listing forward when it can.
            suppressed_kinds = frozenset()
            if _open_pr_cap is not None and len(snapshot.prs) >= _open_pr_cap:
                suppressed_kinds = PR_OPENING_KINDS
                if not open_prs_suppressed:
                    report(
                        f"max_open_prs reached — {len(snapshot.prs)} open PR(s) "
                        f"at a cap of {_open_pr_cap}; not starting "
                        f"{', '.join(sorted(PR_OPENING_KINDS))} items until one "
                        f"closes"
                    )
                    open_prs_suppressed = True
            elif open_prs_suppressed:
                report(
                    f"max_open_prs cleared — {len(snapshot.prs)} open PR(s) "
                    f"against a cap of {_open_pr_cap}"
                )
                open_prs_suppressed = False

            action, a, b = _select_next(
                providers,
                snapshot,
                bugs_preempt,
                handled_ids,
                disabled=disabled_providers,
                on_advertise_error=_provider_failed_to_advertise,
                suppressed_kinds=suppressed_kinds,
            )

            if action == "drained":
                stop_reason = STOP_DRAINED
                break

            if action == "escalate":
                item, reason = a, b
                handled_ids.add(item.item_id)
                escalations.append(Escalation(item_id=item.item_id, reason=reason))
                report(f"{item.item_id} parked — {reason}")
                continue

            provider, item = a, b
            budget.record_item_started()
            handled_ids.add(item.item_id)

            report(
                f"item {budget.items_started}: {item.item_id} [{item.kind}] "
                f"via {type(provider).__name__}"
                + (f" — {item.summary}" if item.summary else "")
            )

            item_started = clock()

            outcome, failure, tree = _execute_item(
                provider,
                item,
                base=base_commit,
                report=report,
                unisolated=unisolated_providers,
            )
            # The item ran; whatever it changed in the repo is not in the
            # snapshot the next pass would otherwise select from. Set here
            # rather than on the success path so a failed or escalated item --
            # both of which can still have written labels, comments or an
            # escalation issue before stopping -- refreshes too.
            snapshot_stale = True
            if tree is not None and tree.wip_ref:
                wip_refs.append(tree.wip_ref)
            if failure is not None:
                # A provider failure parks its item; it never aborts the run.
                escalations.append(
                    Escalation(
                        item_id=item.item_id,
                        reason=f"{type(failure).__name__}: {failure}",
                    )
                )
                report(
                    f"{item.item_id} failed after {_took(clock, item_started)} — "
                    f"{type(failure).__name__}: {failure}"
                )
                continue

            try:
                provider.reconcile(item, outcome)
            except Exception as exc:  # noqa: BLE001 - the outcome is already decided
                # `reconcile` is post-hoc bookkeeping. The item ran, the
                # outcome exists, and any escalation it carries still needs
                # recording — losing all of that because a provider's
                # bookkeeping raised would discard real work, so this is
                # reported and stepped over rather than allowed to end the run.
                report(
                    f"{item.item_id}: reconcile raised — {type(exc).__name__}: {exc} "
                    f"(the item's own outcome still stands)"
                )
            budget.record_tokens(outcome.spend)
            if outcome.status == STATUS_COMPLETED:
                last_failure_signature = None
                consecutive_identical_failures = 0
                items_completed += 1
                report(
                    f"{item.item_id} completed in {_took(clock, item_started)} — "
                    f"{outcome.detail or 'no detail'}"
                )
            else:
                try:
                    reason = _record_escalation(
                        item,
                        outcome,
                        repo=repo,
                        runner=runner,
                        policy_path=policy_path,
                    )
                except Exception as exc:  # noqa: BLE001 - see below
                    # Recording an escalation must never destroy the run it is
                    # recording (#2170). A `gh issue create` rejected for an
                    # over-long title raised `CalledProcessError` out of here,
                    # out of `run_agent`, and out of the process -- so a
                    # REPORTING failure killed a run that had already done its
                    # work. The item is still escalated; only its GitHub trace
                    # is lost, and the summary says so.
                    reason = (
                        f"{outcome.detail} (escalation could NOT be recorded — "
                        f"{type(exc).__name__}: {exc})"
                    ).strip()
                escalations.append(Escalation(item_id=item.item_id, reason=reason))
                report(
                    f"{item.item_id} escalated after {_took(clock, item_started)} — "
                    f"{reason}"
                )

                # #3343: an escalation whose cause keeps repeating is not about
                # the item. Counted here rather than in a provider, because only
                # the run can see that the SAME thing failed N times.
                #
                # #3372: but only an outcome the provider marks `environmental`
                # can have an environmental cause. A per-item judgement —
                # `refused`, `ci_not_green`, `pr_not_found` — RESETS the count
                # rather than being ignored: a lane still reaching verdicts on
                # items is not one whose environment is broken.
                if not outcome.environmental:
                    last_failure_signature = None
                    consecutive_identical_failures = 0
                else:
                    signature = failure_signature(item, outcome)
                    if signature == last_failure_signature:
                        consecutive_identical_failures += 1
                    else:
                        last_failure_signature = signature
                        consecutive_identical_failures = 1

                if consecutive_identical_failures >= IDENTICAL_FAILURE_LIMIT:
                    run_reason = (
                        f"{consecutive_identical_failures} consecutive items "
                        f"failed with the same cause, so the cause is this "
                        f"run's environment rather than any one item. Stopped "
                        f"rather than working the rest of the queue: every "
                        f"further item would add an escalation and a "
                        f"human-owned label for a defect that has nothing to "
                        f"do with it. Last item {item.item_id}; shared cause: "
                        f"{reason}"
                    )
                    # Recorded against the run, not an issue: no target_issue
                    # and no per-item label, so this stop removes nothing
                    # further from automation. The items already escalated
                    # above keep their own records.
                    escalations.append(
                        Escalation(item_id="run:identical-failures", reason=run_reason)
                    )
                    report(f"run stopped — {run_reason}")
                    stop_reason = STOP_RUN_LEVEL_FAILURE
                    break

        # A run that stopped on a cap or a pause broke out of the loop before
        # the top-of-iteration refresh, so the snapshot in hand is the one the
        # last item already invalidated. Refresh once here, or the count below
        # is computed against a view that predates this run's own triage and
        # reports nothing outstanding when the whole point is that something
        # is.
        if snapshot_stale:
            snapshot = _refresh_snapshot(
                snapshot,
                runner=runner,
                repo=repo,
                policy_path=policy_path,
                features_root=features_root,
                report=report,
            )
            snapshot_stale = False

        # #3338: a bug this run marked and never dispatched. With the refresh
        # above in place the usual answer is none -- the marker is written at
        # one item and dispatched at the next -- so a non-empty set means the
        # run ran out of budget or the listing went unreadable, and the
        # operator has to be told rather than left reading a triage-only run
        # as a bug lane that declined everything.
        newly_triaged = sorted(
            number
            for number in _bug_marked_numbers(snapshot) - bugs_marked_at_start
            if f"bug-{number}" not in handled_ids
        )
        if newly_triaged:
            report(
                f"{len(newly_triaged)} issue(s) newly triaged as bug and not "
                f"dispatched in this run — re-run to fix them: "
                + ", ".join(f"#{number}" for number in newly_triaged)
            )

        report(
            f"run finished — {stop_reason} after "
            f"{budget.elapsed_minutes:.2f} minutes"
        )
        return RunSummary(
            items_attempted=budget.items_started,
            items_completed=items_completed,
            items_escalated=len(escalations),
            stop_reason=stop_reason,
            elapsed_minutes=budget.elapsed_minutes,
            tokens_spent=budget.tokens_spent,
            escalations=tuple(escalations),
            wip_refs=tuple(wip_refs),
            newly_triaged_bugs_undispatched=tuple(newly_triaged),
        )
    finally:
        lock_fd.close()


def _format_summary(summary: RunSummary) -> str:
    lines = [
        "specfuse-agent run summary:",
        f"  items attempted:  {summary.items_attempted}",
        f"  items completed:  {summary.items_completed}",
        f"  items escalated:  {summary.items_escalated}",
        f"  stop reason:      {summary.stop_reason}",
        f"  elapsed minutes:  {summary.elapsed_minutes:.2f}",
        f"  tokens spent:     {summary.tokens_spent}",
    ]
    for escalation in summary.escalations:
        lines.append(f"    escalated: {escalation.item_id} — {escalation.reason}")
    for ref in summary.wip_refs:
        lines.append(
            f"    uncommitted work committed on: {ref} (git show {ref})"
        )
    if summary.newly_triaged_bugs_undispatched:
        numbers = ", ".join(
            f"#{number}" for number in summary.newly_triaged_bugs_undispatched
        )
        lines.append(
            f"    {len(summary.newly_triaged_bugs_undispatched)} newly triaged "
            f"as bug, not dispatched — re-run to fix them: {numbers}"
        )
    return "\n".join(lines)


def default_providers(
    *,
    repo: Optional[str] = None,
    runner: Callable = _default_runner,
    policy_path: Optional[str] = None,
    features_root: Optional[Path] = None,
    monitoring_config_path: Optional[str] = None,
    reporter: Optional[Callable[[str], None]] = None,
) -> Sequence[ActionProvider]:
    """The registry each gate-2 provider WU (T06-T08) appends itself to.

    Returns `()` when `repo` is not given -- `run_agent`'s own `providers=`
    default stays `()` too, so tests keep injecting doubles rather than
    going through this function. T06 is the first provider to append itself
    here; T07/T08 add theirs the same way."""
    from specfuse.agent.providers.answers import AnsweredEscalationProvider
    from specfuse.agent.providers.bugs import BugsProvider
    from specfuse.agent.providers.feature import FeatureProvider
    from specfuse.agent.providers.findings_autofix import FindingsAutofixProvider
    from specfuse.agent.providers.findings_diagnose import FindingsDiagnoseProvider
    from specfuse.agent.providers.triage import TriageProvider

    if repo is None:
        return ()
    findings_diagnose_kwargs = {}
    findings_autofix_kwargs = {}
    if monitoring_config_path is not None:
        findings_diagnose_kwargs["monitoring_config_path"] = monitoring_config_path
        findings_autofix_kwargs["monitoring_config_path"] = monitoring_config_path
    return (
        AnsweredEscalationProvider(
            repo=repo,
            runner=runner,
        ),
        BugsProvider(
            repo=repo,
            runner=runner,
            policy_path=policy_path,
            # #3339: a severity skip must reach the operator, or a lane that
            # advertises nothing looks broken rather than filtered.
            report=reporter,
        ),
        FeatureProvider(
            repo=repo,
            runner=runner,
            policy_path=policy_path,
            features_root=features_root,
            # The one provider that runs a long child process, so the one that
            # owes the operator its output while it runs rather than after.
            stream_driver_output=True,
            reporter=reporter if reporter is not None else _default_reporter,
        ),
        TriageProvider(
            repo=repo,
            runner=runner,
            policy_path=policy_path,
        ),
        FindingsDiagnoseProvider(
            repo=repo,
            runner=runner,
            policy_path=policy_path,
            **findings_diagnose_kwargs,
        ),
        FindingsAutofixProvider(
            repo=repo,
            runner=runner,
            policy_path=policy_path,
            **findings_autofix_kwargs,
        ),
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="specfuse-agent",
        description="Run the specfuse-agent conductor loop.",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="GitHub repo, OWNER/NAME (default: detected from the checkout)",
    )
    parser.add_argument("--policy", default=None, help="path to agent-policy.yml")
    parser.add_argument("--features-root", default=None, help="path to .specfuse/features")
    parser.add_argument(
        "--monitoring-config",
        default=".specfuse/monitoring.yml",
        help="path to monitoring.yml (default: .specfuse/monitoring.yml)",
    )
    parser.add_argument("--max-minutes", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--max-items", type=int, default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    warn_if_out_of_tree()
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    features_root = Path(args.features_root) if args.features_root else None

    # No repo, no run (#2271). `default_providers` returns `()` on a `None`
    # repo, so continuing here would drain in 0.00 minutes and exit 0 -- a
    # summary indistinguishable from "there was genuinely nothing to do",
    # printed by a run that never asked. Failing before the lock is taken
    # keeps that distinction where the operator can act on it.
    repo = args.repo or detect_repo()
    if not repo:
        print(
            "specfuse-agent: could not work out which GitHub repo to run "
            "against, and a run without one does nothing. Pass --repo "
            "OWNER/NAME, or run from a checkout whose 'origin' remote is on "
            "github.com (gh repo view must succeed).",
            file=sys.stderr,
        )
        return 2

    # Bracket the run at the process boundary (#2055). Dispatched `/fix-bug`
    # sessions create and check out branches, so a run that started on `main`
    # ends wherever the last session left it -- silently. The conductor is not
    # the right place to fix that: `run_agent`'s invariant is that no code path
    # in it can commit, branch or merge, and a test enforces that its runner
    # only ever issues `gh`. `main()` is what the operator invoked, so `main()`
    # is what owes them their branch back.
    started_on = worktree.current_branch()

    try:
        summary = run_agent(
            repo=repo,
            policy_path=args.policy,
            features_root=features_root,
            max_minutes=args.max_minutes,
            max_tokens=args.max_tokens,
            max_items=args.max_items,
            isolate_items=True,
            providers=default_providers(
                repo=repo,
                policy_path=args.policy,
                features_root=features_root,
                monitoring_config_path=args.monitoring_config,
            ),
        )
    except AgentLockHeldError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        # `finally`, not a trailing call: a run that raises part-way has still
        # moved the tree, and that is exactly when the operator is least likely
        # to think to check.
        worktree.restore_branch(started_on, report=_default_reporter)

    print(_format_summary(summary))
    # #3392: a refusal exits non-zero so a scheduled run's exit status is
    # self-describing without its log. Outcomes — `drained` included — keep 0.
    return exit_code_for(summary.stop_reason)


if __name__ == "__main__":
    sys.exit(main())
