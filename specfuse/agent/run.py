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

The loop never touches git. It calls `provider.execute()` and
`provider.reconcile()` and nothing else — the `runner` it holds is used only
to build the T02 snapshot's read-only `gh ... list` calls, and is never
handed to a provider. There is no code path here that can commit, branch, or
merge.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
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

KIND_BUG = "bug"
KIND_FEATURE = "feature"
KIND_TRIAGE = "triage"
KIND_ESCALATION_ANSWER = "escalation-answer"
KIND_FINDING_DIAGNOSE = "finding-diagnose"
KIND_FINDING_AUTOFIX = "finding-autofix"


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


def _default_runner(argv: list, check: bool = False):
    return subprocess.run(argv, check=check, capture_output=True, text=True)


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
) -> RunSummary:
    """Run the select-execute-reconcile loop to completion and return the
    summary. Raises `AgentLockHeldError` if another agent already holds
    `.specfuse/.agent.lock` — never a raw `BlockingIOError`.

    *reporter* receives one progress line per event as the run happens;
    `None` means print them, and passing a collector silences stdout. Tests
    pass a list's `append`."""
    report = reporter if reporter is not None else _default_reporter
    lock_path = Path(specfuse_dir) / DEFAULT_AGENT_LOCK_NAME
    try:
        lock_fd = acquire_agent_lock(Path(specfuse_dir))
    except BlockingIOError as exc:
        raise AgentLockHeldError(lock_path) from exc

    try:
        report(f"run started — repo {repo}")
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

        budget_kwargs = {}
        if pause_marker is not None:
            budget_kwargs["pause_marker"] = pause_marker
        budget = RunBudget(
            clock=clock,
            max_minutes=max_minutes,
            max_tokens=max_tokens,
            max_items=max_items,
            **budget_kwargs,
        )

        items_completed = 0
        escalations = []
        handled_ids = set()
        disabled_providers: set = set()
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

            action, a, b = _select_next(
                providers,
                snapshot,
                bugs_preempt,
                handled_ids,
                disabled=disabled_providers,
                on_advertise_error=_provider_failed_to_advertise,
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

            try:
                outcome = provider.execute(item)
            except Exception as exc:  # noqa: BLE001 - a provider failure parks, never aborts the run
                escalations.append(
                    Escalation(item_id=item.item_id, reason=f"{type(exc).__name__}: {exc}")
                )
                report(
                    f"{item.item_id} failed after {_took(clock, item_started)} — "
                    f"{type(exc).__name__}: {exc}"
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
