#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Azure credential construction, shared by both Azure provider modules (#302).

Lives with the providers rather than in the core on purpose. `cli.py` looks this up
reflectively via `build_credential`, so the dispatcher never learns how any provider
authenticates — the property
`TestProviderRegistry.test_no_provider_identifier_reaches_the_core` enforces, and the
one that caught the first attempt at this fix.
"""

from __future__ import annotations

__all__ = ("build_credential",)


def build_credential():
    """Return the Azure `TokenCredential` the SDKs expect.

    `DefaultAzureCredential` is the strategy, and it is the default because it needs
    **no secret in the config at all** — managed identity in a cluster, developer
    credentials locally. That is a better posture than a connection string for the
    common case, not merely a convenience.

    `ServiceBusClient(credential=...)` and `LogsQueryClient(credential)` both want an
    object with `get_token()`. Before #302 they were handed the environment-resolved
    credentials *mapping*, so every real Azure call would have failed on the first
    request. No test caught it because they all inject a stub transport, and a stub
    accepts any `credential` argument.

    Imported lazily so `azure-identity` is never needed to import this module — the
    package keeps zero runtime dependencies, which `verification.yml` records as a
    property. A missing SDK is reported as a diagnosed error naming the extra rather
    than a raw `ImportError` traceback, because that is the first thing a new
    operator would otherwise hit.

    **Connection-string authentication is deliberately not supported here.** Selecting
    between strategies needs a schema field, which is a consumer-visible contract
    change; #302 records it as out of scope for this fix.
    """
    from specfuse.monitor.cli import MonitorCliError

    try:
        from azure.identity import DefaultAzureCredential
    except ImportError as exc:
        raise MonitorCliError(
            "azure-identity is not installed, so no Azure credential can be built. "
            "Install the provider SDKs with: pip install 'specfuse-loop[azure]'"
        ) from exc
    return DefaultAzureCredential()
