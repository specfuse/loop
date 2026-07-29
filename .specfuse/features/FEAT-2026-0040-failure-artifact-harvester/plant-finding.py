#!/usr/bin/env python3
"""Path B — plant a finding with a fake transport, file it with the REAL `gh`.

Discharges **D-9** in full and **D-10 partially**, without a live Azure environment.
See `OPERATOR-JOURNAL.md` § "How to run these" for what each of those means and what
this script deliberately does not prove.

WHY THIS EXISTS. `specfuse-monitor run` resolves providers only by importing
`specfuse.monitor.providers.<name>`; there is no plugin path and no override, so the
CLI cannot manufacture a finding without a real Azure backend. `run_cycle()` takes
`transport_resolver` and `gh_runner` separately, so a fake transport can produce the
finding while the real `gh` files it. `main()` does not expose that seam — hence a
script rather than a flag.

WHAT IT WRITES. Real GitHub issues, in the repository resolved from
`git config --get remote.origin.url`. Run it from inside a SCRATCH clone. It is
deliberately loud about which repository it is about to write to and refuses to
proceed without confirmation.

USAGE
    cd /path/to/scratch-clone
    python3 plant-finding.py            # first run  — expect 2 issues created
    python3 plant-finding.py            # second run — expect 0 created, 2 found

The second run is the observation D-9 asks for: the issue count must NOT grow.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from specfuse.monitor.cli import (
    _resolve_repo,
    load_monitoring_config,
    run_cycle,
)

NOW = datetime.now(timezone.utc)


# --- the fake transport ------------------------------------------------------
# Shapes mirror tests/test_monitor_cli.py's stubs — the contract each adapter
# expects of its transport. Keep them in step if an adapter's transport changes.


@dataclass
class _Message:
    dead_letter_reason: str = "MaxDeliveryCountExceeded"
    dead_letter_error_description: str = "planted by plant-finding.py"
    message_id: str = "m1"
    sequence_number: int = 1


class _DlqTransport:
    """Two subscriptions, each with one dead-lettered message.

    Two targets rather than one on purpose: it makes the same run prove
    FEAT-2026-0069's binding constraint — findings from different targets on one
    component must produce DIFFERENT issues, not one collapsed bucket.
    """

    def __init__(self, by_subscription):
        self._by_subscription = by_subscription

    def peek_dead_letter_messages(self, *, subscription, max_message_count):
        return list(self._by_subscription.get(subscription, []))


class _QueueStalledTransport:
    def __init__(self, active, oldest):
        self._active, self._oldest = active, oldest

    def get_active_message_count(self, *, subscription):
        return self._active.get(subscription, 0)

    def get_oldest_message_enqueued_time(self, *, subscription):
        return self._oldest.get(subscription)


class _TelemetryTransport:
    def __init__(self, rows):
        self._rows = rows

    def run_query(self, query):
        return list(self._rows)


_ROWS = {
    "error-logs": [],   # empty: keep this run's blast radius to the dlq targets
    "http-5xx": [],
    "invariant": [],
    "heartbeat": [],
}


def fake_resolver(module, check_type, binding):
    """Stand in for `_default_transport_resolver`. Never touches a cloud SDK."""
    if check_type == "dlq":
        # Subscription names must match the `dlq` targets in your monitoring.yml.
        return _DlqTransport({
            "orders-sub": [_Message(message_id="planted-orders")],
            "inventory-sub": [_Message(
                message_id="planted-inventory",
                dead_letter_error_description="a different planted failure",
            )],
        })
    if check_type == "queue-stalled":
        return _QueueStalledTransport(
            active={"stalled-sub": 5},
            oldest={"stalled-sub": NOW - timedelta(hours=1)},
        )
    return _TelemetryTransport(_ROWS.get(check_type, []))


# --- guard rails -------------------------------------------------------------


def main() -> int:
    try:
        repo = _resolve_repo()
    except Exception as exc:                                    # noqa: BLE001
        print(f"could not resolve a repository: {exc}", file=sys.stderr)
        print("run this from inside the scratch clone.", file=sys.stderr)
        return 1

    print(f"About to file REAL GitHub issues in: {repo}")
    print("This must be a scratch repository, not a real project.")
    if input("Type the repo name to continue: ").strip() != repo:
        print("aborted — no issues filed.")
        return 1

    config = load_monitoring_config(".specfuse/monitoring.yml")
    return run_cycle(
        config,
        repo=repo,
        transport_resolver=fake_resolver,   # fake: plants the finding
        # gh_runner left at its default — the REAL `gh`, which is the point
        now=NOW,
    )


if __name__ == "__main__":
    raise SystemExit(main())
