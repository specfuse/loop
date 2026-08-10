#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""
Fire-and-forget chat-webhook notifier (FEAT-2026-0047/T01).

`escalation.webhook_env` in `.specfuse/agent-policy.yml` holds an
environment-variable NAME, never a URL — the same convention and rationale
as `lint_monitoring._ENV_VAR_NAME_RE` (see `agent_policy._ENV_VAR_NAME_RE`):
a webhook URL is a bearer credential, and the config a committed file must
never hold one.

The provider is declared via `escalation.provider` (`discord` | `slack` |
`teams` | `none`), never sniffed from the URL — sniffing would mean parsing
a secret.

The GitHub issue `escalation.py` files is the system of record for an
escalation; this module is a best-effort side channel. A failed post logs
and returns `False` — it never raises into the caller and never fails a
gate.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, time
from typing import Callable

from specfuse.monitor.redaction import redact_text

from . import agent_policy

__all__ = (
    "post_notification",
    "resolve_webhook_url",
    "discord_payload",
    "slack_payload",
    "teams_payload",
)

logger = logging.getLogger(__name__)

Poster = Callable[[str, dict], int]

_QUIET_HOURS_RE = re.compile(r"^(\d{2}):(\d{2})-(\d{2}):(\d{2})$")


def resolve_webhook_url(policy_path: str | None = None) -> str | None:
    """Resolve the webhook URL named by `escalation.webhook_env`.

    Returns `None` when the policy file is absent, `webhook_env` is absent
    or empty, or the environment variable it names is unset. The URL never
    lives in the config; only the variable name does.
    """
    try:
        policy = agent_policy.load_policy(policy_path)
    except FileNotFoundError:
        return None

    escalation = policy.get("escalation") if isinstance(policy, dict) else None
    if not isinstance(escalation, dict):
        return None

    env_name = escalation.get("webhook_env")
    if not isinstance(env_name, str) or not env_name:
        return None

    return os.environ.get(env_name) or None


def discord_payload(message: str) -> dict:
    return {"content": redact_text(message)}


def slack_payload(message: str) -> dict:
    return {"text": redact_text(message)}


def teams_payload(message: str) -> dict:
    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "text": redact_text(message),
    }


_PAYLOAD_BUILDERS = {
    "discord": discord_payload,
    "slack": slack_payload,
    "teams": teams_payload,
}


def _in_quiet_hours(quiet_hours: str, now: time) -> bool:
    if not quiet_hours:
        return False
    match = _QUIET_HOURS_RE.match(quiet_hours)
    if not match:
        return False
    start = time(int(match.group(1)), int(match.group(2)))
    end = time(int(match.group(3)), int(match.group(4)))
    if start <= end:
        return start <= now < end
    return now >= start or now < end


def _default_poster(url: str, payload: dict) -> int:
    import json
    import urllib.request

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:  # nosec B310
        return response.status


def post_notification(
    message: str,
    *,
    policy_path: str | None = None,
    poster: Poster | None = None,
    now: time | None = None,
) -> bool:
    """Post *message* to the configured webhook. Never raises.

    Returns `False` (a no-op, not an error) when no webhook is configured,
    the provider is unknown/`none`, or quiet hours cover *now*. Returns
    `False` when the poster raises, times out, or returns a non-2xx status.
    """
    try:
        policy = agent_policy.load_policy(policy_path)
    except FileNotFoundError:
        return False

    escalation = policy.get("escalation") if isinstance(policy, dict) else None
    if not isinstance(escalation, dict):
        return False

    quiet_hours = escalation.get("quiet_hours") or ""
    check_time = now if now is not None else datetime.now().time()
    if _in_quiet_hours(quiet_hours, check_time):
        return False

    url = resolve_webhook_url(policy_path)
    if not url:
        return False

    provider = escalation.get("provider") or "none"
    builder = _PAYLOAD_BUILDERS.get(provider)
    if builder is None:
        return False

    payload = builder(message)
    poster_fn = poster if poster is not None else _default_poster

    try:
        status = poster_fn(url, payload)
    except Exception:  # noqa: BLE001 - a raising poster must never be fatal
        logger.warning("notify: poster raised an exception")
        return False

    if not isinstance(status, int) or not (200 <= status < 300):
        return False

    return True
