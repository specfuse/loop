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
from specfuse.agent.state import AgentSnapshot, gather_snapshot
from specfuse.loop import agent_policy
from specfuse.loop._filelock import acquire_agent_lock
from specfuse.loop.escalation import annotate_escalation, emit_escalation

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

    `spend` is whatever unit the provider counts as tokens; it defaults to
    zero so a provider that reports nothing leaves the run's total spend at
    zero. `escalation`, when set on a `STATUS_ESCALATED` outcome, is filed
    as a needs-human issue via `emit_escalation`; left `None`, the item is
    still recorded as escalated but no issue is filed (criterion 9)."""

    status: str
    detail: str = ""
    spend: int = 0
    escalation: Optional[EscalationPayload] = None


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
        suffix = f"(filed as issue {issue_id})"
    return f"{reason} {suffix}" if reason else suffix.strip("()")


def _select_next(
    providers: Sequence[ActionProvider],
    snapshot: AgentSnapshot,
    bugs_preempt: bool,
    handled_ids: set,
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
    """
    candidates = []
    for provider in providers:
        for item in provider.advertise(snapshot):
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
        stop_reason = STOP_DRAINED

        while True:
            if budget.pause_requested():
                stop_reason = STOP_PAUSE
                break
            if not budget.may_start_next_item():
                stop_reason = STOP_CAP
                break

            action, a, b = _select_next(providers, snapshot, bugs_preempt, handled_ids)

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

            provider.reconcile(item, outcome)
            budget.record_tokens(outcome.spend)
            if outcome.status == STATUS_COMPLETED:
                items_completed += 1
                report(
                    f"{item.item_id} completed in {_took(clock, item_started)} — "
                    f"{outcome.detail or 'no detail'}"
                )
            else:
                reason = _record_escalation(
                    item,
                    outcome,
                    repo=repo,
                    runner=runner,
                    policy_path=policy_path,
                )
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
    parser.add_argument("--repo", default=None, help="GitHub repo, OWNER/NAME")
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
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    features_root = Path(args.features_root) if args.features_root else None
    try:
        summary = run_agent(
            repo=args.repo,
            policy_path=args.policy,
            features_root=features_root,
            max_minutes=args.max_minutes,
            max_tokens=args.max_tokens,
            max_items=args.max_items,
            providers=default_providers(
                repo=args.repo,
                policy_path=args.policy,
                features_root=features_root,
                monitoring_config_path=args.monitoring_config,
            ),
        )
    except AgentLockHeldError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(_format_summary(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
